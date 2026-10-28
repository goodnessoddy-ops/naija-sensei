"""
billing.py — Premium subscriptions for NaijaSensei.

TWO ACTIVATION PATHS
  1. Direct payment via Paystack — POST /billing/checkout initializes a
     transaction, the payer completes it on Paystack's hosted page, and
     POST /billing/webhook auto-activates premium the moment payment
     clears. A parent or teacher can pay for one of THEIR OWN linked
     children / class students (checked against parent_links /
     class_members — see _can_pay_for) rather than only themselves,
     which is how "pay per added student" works without needing a
     separate bulk/seat-pack flow.
  2. Redemption codes — for bank transfer / agent / school sales where a
     human collects payment outside Paystack (common in Nigeria for
     buyers without card access). An admin generates a batch of codes
     (POST /billing/admin/generate-codes) and hands them out through
     whatever offline channel; the buyer redeems one via
     POST /billing/redeem to activate their own account.

PLANS live in code, not the DB — pricing is a product decision that
should go through a code review/deploy, not a runtime-editable table an
attacker could tamper with if they ever got DB write access.

SECURITY NOTES (this is real-money code, treat it accordingly)
  - Every code is stored as a SHA-256 hash, never plaintext — same
    posture as passwords. The only place a code is ever shown in
    plaintext is the one-time admin-generation response.
  - The Paystack webhook verifies the x-paystack-signature header
    (HMAC-SHA512 over the RAW request body, per Paystack's own docs)
    BEFORE parsing or trusting anything in the payload.
  - Per Paystack's own guidance, the webhook does not trust its own
    payload's status field — it re-verifies via GET
    /transaction/verify/:reference before activating anything, and
    checks the paid amount against the expected plan price to catch
    tampering or a stale client-side price.
  - Webhook processing is idempotent on `reference` — Paystack can and
    does retry webhook delivery, so this must never double-activate or
    double-extend a subscription from the same payment.
  - /billing/redeem and /billing/checkout are both on
    RateLimitMiddleware's strict rule list (see security.py) — code
    guessing and checkout spam both get throttled per IP.
"""

import asyncio
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from auth import _get_conn, require_user, get_current_user
from security import constant_time_equals

router = APIRouter(prefix="/billing", tags=["billing"])

PAYSTACK_SECRET_KEY = os.environ.get("PAYSTACK_SECRET_KEY", "").strip()
PAYSTACK_BASE = "https://api.paystack.co"

if not PAYSTACK_SECRET_KEY:
    print(
        "[billing] PAYSTACK_SECRET_KEY not set — /billing/checkout and the "
        "webhook will return 503 until it's configured. Redemption codes "
        "(/billing/redeem, /billing/admin/generate-codes) work regardless, "
        "since that path doesn't touch Paystack at all."
    )

# ── Plans — see the pricing discussion this was built from for the
# reasoning behind these specific numbers and discount curve. ──────────────
PLANS = {
    "monthly": {"label": "Monthly", "amount_naira": 5000, "duration_days": 30},
    "termly": {"label": "Termly (3 months)", "amount_naira": 12000, "duration_days": 90},
    "annual": {"label": "WAEC Season / Annual (12 months)", "amount_naira": 40000, "duration_days": 365},
}

# A free trial plan — deliberately kept OUT of PLANS above so it can
# never be bought via /billing/checkout (that endpoint only accepts keys
# from PLANS). It can only ever be granted through an admin-generated
# redemption code — see admin_generate_codes(), which validates against
# ALL_PLANS (paid + trial) rather than PLANS (paid only).
TRIAL_PLAN = {"label": "Free Trial (1 month)", "amount_naira": 0, "duration_days": 30}
ALL_PLANS = {**PLANS, "trial": TRIAL_PLAN}

# ── Free-tier soft quotas. Enforced from server.py (/chat), exam.py
# (/exam/start), career.py (/career/guidance), and classroom.py (voice) —
# see check_chat_quota() / check_exam_quota() / check_feature_locked()
# below, which those files call directly. ──────────────────────────────────
FREE_CHAT_MESSAGES_PER_DAY = 20
FREE_EXAMS_PER_MONTH = 2


def init_billing_db():
    """Create billing tables on startup. Safe to call repeatedly."""
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            user_id      BIGINT PRIMARY KEY,
            plan         TEXT NOT NULL,
            status       TEXT NOT NULL DEFAULT 'active',
            source       TEXT NOT NULL,          -- 'paystack' or 'code'
            activated_at TEXT NOT NULL DEFAULT now_iso(),
            expires_at   TEXT NOT NULL,
            updated_at   TEXT NOT NULL DEFAULT now_iso()
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS payment_transactions (
            id                   BIGSERIAL PRIMARY KEY,
            payer_user_id        BIGINT NOT NULL,
            target_user_id       BIGINT NOT NULL,   -- who premium activates for (usually = payer)
            reference            TEXT NOT NULL UNIQUE,
            plan                 TEXT NOT NULL,
            amount_naira         INTEGER NOT NULL,
            status               TEXT NOT NULL DEFAULT 'pending',  -- pending, success, failed, amount_mismatch
            raw_gateway_response TEXT,
            created_at           TEXT NOT NULL DEFAULT now_iso(),
            completed_at         TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS redemption_codes (
            id                BIGSERIAL PRIMARY KEY,
            code_hash         TEXT NOT NULL UNIQUE,
            plan              TEXT NOT NULL,
            batch_note        TEXT,
            issued_by_user_id BIGINT,
            issued_by_role    TEXT NOT NULL,        -- 'admin'
            used_by_user_id   BIGINT,
            used_at           TEXT,
            created_at        TEXT NOT NULL DEFAULT now_iso(),
            expires_at        TEXT NOT NULL         -- unredeemed codes expire too
        )
    """)
    conn.commit()
    conn.close()
    print("[billing] subscriptions / payment_transactions / redemption_codes tables ready.")


# ── Code generation ──────────────────────────────────────────────────────

# Excludes visually ambiguous characters (0/O, 1/I/L) since these are
# meant to be read off a printout or a WhatsApp message and typed back in.
_CODE_ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"


def _generate_code() -> str:
    part = lambda n: "".join(secrets.choice(_CODE_ALPHABET) for _ in range(n))
    return f"NSAI-{part(4)}-{part(4)}"


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.strip().upper().encode()).hexdigest()


# ── Subscription helpers ─────────────────────────────────────────────────

def get_subscription(user_id: int) -> Optional[dict]:
    conn = _get_conn()
    row = conn.execute("SELECT * FROM subscriptions WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def is_premium(user_id: int) -> bool:
    sub = get_subscription(user_id)
    if not sub or sub["status"] != "active":
        return False
    try:
        expires = datetime.fromisoformat(sub["expires_at"])
    except Exception:
        return False
    return expires > datetime.utcnow()


def _activate_subscription(conn, user_id: int, plan: str, source: str) -> datetime:
    """Activates or extends a subscription. If the user is already
    premium and not yet expired, extends from their CURRENT expiry
    rather than from now — buying more time while still premium
    shouldn't waste the remaining balance. Caller owns commit/close."""
    plan_info = ALL_PLANS[plan]
    now = datetime.utcnow()

    row = conn.execute("SELECT expires_at FROM subscriptions WHERE user_id = ?", (user_id,)).fetchone()
    base = now
    if row and row["expires_at"]:
        try:
            current_expiry = datetime.fromisoformat(row["expires_at"])
            base = max(now, current_expiry)
        except Exception:
            pass

    new_expiry = base + timedelta(days=plan_info["duration_days"])
    conn.execute("""
        INSERT INTO subscriptions (user_id, plan, status, source, activated_at, expires_at, updated_at)
        VALUES (?, ?, 'active', ?, ?, ?, ?)
        ON CONFLICT (user_id) DO UPDATE SET
            plan = EXCLUDED.plan,
            status = 'active',
            source = EXCLUDED.source,
            expires_at = EXCLUDED.expires_at,
            updated_at = EXCLUDED.updated_at
    """, (user_id, plan, source, now.isoformat(), new_expiry.isoformat(), now.isoformat()))
    conn.commit()
    return new_expiry


def _can_pay_for(payer: dict, target_user_id: int) -> bool:
    """Can `payer` buy premium for `target_user_id`? Only true if
    target_user_id is payer's own linked child (parent_links, approved)
    or a student in one of payer's classes (class_members/classes)."""
    conn = _get_conn()
    try:
        if payer.get("role") == "parent":
            row = conn.execute(
                "SELECT 1 FROM parent_links WHERE parent_id = ? AND student_id = ? AND status = 'approved'",
                (payer["id"], target_user_id)
            ).fetchone()
            return bool(row)
        if payer.get("role") == "teacher":
            row = conn.execute(
                """SELECT 1 FROM class_members cm
                   JOIN classes c ON cm.class_id = c.id
                   WHERE c.teacher_id = ? AND cm.student_id = ?""",
                (payer["id"], target_user_id)
            ).fetchone()
            return bool(row)
        return False
    finally:
        conn.close()


# ── Free-tier quota checks — called from server.py/exam.py/career.py/
# classroom.py before spending an AI call. ──────────────────────────────

def check_chat_quota(user_id: int) -> tuple[bool, str]:
    """Returns (allowed, message_if_blocked).

    Counts from chat_quota_log, NOT chat_history — chat_history is what the
    'Clear chat' button deletes, and this quota must survive that. See the
    chat_quota_log table comment in auth.py's init_db() for the full reason."""
    if is_premium(user_id):
        return True, ""
    today_prefix = datetime.utcnow().strftime("%Y-%m-%d")
    conn = _get_conn()
    count = conn.execute(
        "SELECT COUNT(*) AS c FROM chat_quota_log WHERE user_id = ? AND created_at LIKE ?",
        (user_id, today_prefix + "%")
    ).fetchone()["c"]
    conn.close()
    if count >= FREE_CHAT_MESSAGES_PER_DAY:
        return False, (
            f"You've used today's {FREE_CHAT_MESSAGES_PER_DAY} free messages with Mr. Sensei. "
            f"Upgrade to Premium for unlimited chat, or come back tomorrow!"
        )
    return True, ""


def check_exam_quota(user_id: int) -> tuple[bool, str]:
    if is_premium(user_id):
        return True, ""
    month_prefix = datetime.utcnow().strftime("%Y-%m")
    conn = _get_conn()
    count = conn.execute(
        "SELECT COUNT(*) AS c FROM exam_sessions WHERE user_id = ? AND started_at LIKE ?",
        (user_id, month_prefix + "%")
    ).fetchone()["c"]
    conn.close()
    if count >= FREE_EXAMS_PER_MONTH:
        return False, (
            f"You've used this month's {FREE_EXAMS_PER_MONTH} free practice exams. "
            f"Upgrade to Premium for unlimited exams!"
        )
    return True, ""


def check_feature_locked(user_id: int, feature_label: str) -> tuple[bool, str]:
    """For fully-locked-behind-premium features (career guidance, voice)
    rather than daily/monthly quotas."""
    if is_premium(user_id):
        return True, ""
    return False, f"{feature_label} is a Premium feature. Upgrade to unlock it!"


# ── Schemas ───────────────────────────────────────────────────────────────

class CheckoutRequest(BaseModel):
    plan: str
    target_user_id: Optional[int] = None  # None = buying for self
    callback_url: Optional[str] = None     # where Paystack redirects the browser after payment


class RedeemRequest(BaseModel):
    code: str


class GenerateCodesRequest(BaseModel):
    plan: str
    count: int = 1
    note: str = ""
    validity_days: int = 180  # how long an UNREDEEMED code stays valid


# ── Routes: plans / status ──────────────────────────────────────────────

@router.get("/plans")
def list_plans():
    return {
        "plans": PLANS,
        "free_quotas": {
            "chat_messages_per_day": FREE_CHAT_MESSAGES_PER_DAY,
            "exams_per_month": FREE_EXAMS_PER_MONTH,
        },
    }


@router.get("/status")
def billing_status(current_user: dict = Depends(require_user)):
    sub = get_subscription(current_user["id"])
    return {
        "is_premium": is_premium(current_user["id"]),
        "plan": sub["plan"] if sub else None,
        "expires_at": sub["expires_at"] if sub else None,
        "source": sub["source"] if sub else None,
    }


# ── Routes: Paystack checkout ────────────────────────────────────────────

@router.post("/checkout")
async def checkout(req: CheckoutRequest, current_user: dict = Depends(require_user)):
    if req.plan not in PLANS:
        raise HTTPException(400, f"Unknown plan. Choose from: {', '.join(PLANS.keys())}")
    if not PAYSTACK_SECRET_KEY:
        raise HTTPException(503, "Payments aren't configured yet. Set PAYSTACK_SECRET_KEY.")

    target_id = req.target_user_id or current_user["id"]
    if target_id != current_user["id"]:
        allowed = await asyncio.to_thread(_can_pay_for, current_user, target_id)
        if not allowed:
            raise HTTPException(
                403,
                "You can only buy Premium for your own linked children (parent) "
                "or students in your class (teacher)."
            )

    plan_info = PLANS[req.plan]
    reference = f"ns_{secrets.token_hex(12)}"
    amount_kobo = plan_info["amount_naira"] * 100

    def _log_pending():
        conn = _get_conn()
        conn.execute(
            """INSERT INTO payment_transactions
               (payer_user_id, target_user_id, reference, plan, amount_naira, status)
               VALUES (?, ?, ?, ?, ?, 'pending')""",
            (current_user["id"], target_id, reference, req.plan, plan_info["amount_naira"])
        )
        conn.commit()
        conn.close()

    await asyncio.to_thread(_log_pending)

    paystack_payload = {
        "email": current_user["email"],
        "amount": amount_kobo,
        "reference": reference,
        "metadata": {
            "target_user_id": target_id,
            "payer_user_id": current_user["id"],
            "plan": req.plan,
        },
    }
    # Only accept a plain http(s) URL — this only ever redirects the
    # payer's own browser back to wherever they came from, but there's
    # no reason to accept a javascript:/data: URI here either.
    if req.callback_url and req.callback_url.startswith(("http://", "https://")):
        paystack_payload["callback_url"] = req.callback_url

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(
            f"{PAYSTACK_BASE}/transaction/initialize",
            headers={"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"},
            json=paystack_payload,
        )
    try:
        data = resp.json()
    except Exception:
        raise HTTPException(502, "Paystack returned an unexpected response. Try again shortly.")

    if not data.get("status"):
        raise HTTPException(502, f"Could not start payment: {data.get('message', 'unknown error')}")

    return {
        "authorization_url": data["data"]["authorization_url"],
        "reference": reference,
        "amount_naira": plan_info["amount_naira"],
    }


@router.post("/webhook")
async def paystack_webhook(request: Request):
    """Paystack calls this server-to-server on charge.success. See this
    file's module docstring for the security reasoning — signature
    verification on the RAW body, re-verification against Paystack's own
    API (not just trusting the payload), amount checking, and
    idempotency on `reference` all happen here, in that order."""
    raw_body = await request.body()
    signature = request.headers.get("x-paystack-signature", "")

    if not PAYSTACK_SECRET_KEY:
        raise HTTPException(503, "Payments not configured.")

    computed = hmac.new(PAYSTACK_SECRET_KEY.encode(), raw_body, hashlib.sha512).hexdigest()
    if not constant_time_equals(computed, signature):
        raise HTTPException(401, "Invalid webhook signature.")

    try:
        event = json.loads(raw_body)
    except Exception:
        raise HTTPException(400, "Invalid payload.")

    if event.get("event") != "charge.success":
        return {"status": "ignored"}

    reference = event.get("data", {}).get("reference")
    if not reference:
        return {"status": "missing_reference"}

    # Re-verify against Paystack's own API rather than trusting the
    # webhook payload's status field alone — this is Paystack's own
    # documented recommendation, not just extra caution on my part.
    async with httpx.AsyncClient(timeout=20) as client:
        verify_resp = await client.get(
            f"{PAYSTACK_BASE}/transaction/verify/{reference}",
            headers={"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"},
        )
    try:
        verify_data = verify_resp.json()
    except Exception:
        return {"status": "verify_failed"}

    if not (verify_data.get("status") and verify_data.get("data", {}).get("status") == "success"):
        return {"status": "not_verified"}

    verified = verify_data["data"]
    amount_kobo = verified["amount"]
    metadata = verified.get("metadata") or {}
    target_user_id = metadata.get("target_user_id")
    plan = metadata.get("plan")

    if not (target_user_id and plan and plan in PLANS):
        return {"status": "missing_metadata"}

    expected_amount_kobo = PLANS[plan]["amount_naira"] * 100
    if amount_kobo != expected_amount_kobo:
        # Don't activate on a price mismatch — either tampering or a
        # stale client-side price. Log loudly for manual review.
        print(f"[billing] WEBHOOK AMOUNT MISMATCH: ref={reference} expected={expected_amount_kobo} got={amount_kobo}")

        def _mark_mismatch():
            conn = _get_conn()
            conn.execute(
                "UPDATE payment_transactions SET status = 'amount_mismatch', completed_at = ? WHERE reference = ?",
                (datetime.utcnow().isoformat(), reference)
            )
            conn.commit()
            conn.close()
        await asyncio.to_thread(_mark_mismatch)
        return {"status": "amount_mismatch"}

    def _finalize():
        conn = _get_conn()
        # Idempotency — Paystack can and does retry webhook delivery.
        existing = conn.execute(
            "SELECT status FROM payment_transactions WHERE reference = ?", (reference,)
        ).fetchone()
        if existing and existing["status"] == "success":
            conn.close()
            return
        conn.execute(
            "UPDATE payment_transactions SET status = 'success', completed_at = ?, raw_gateway_response = ? WHERE reference = ?",
            (datetime.utcnow().isoformat(), json.dumps(verified)[:5000], reference)
        )
        conn.commit()
        _activate_subscription(conn, int(target_user_id), plan, "paystack")
        conn.close()

    await asyncio.to_thread(_finalize)
    return {"status": "ok"}


# ── Routes: redemption codes ─────────────────────────────────────────────

@router.post("/redeem")
async def redeem_code(req: RedeemRequest, current_user: dict = Depends(require_user)):
    code_hash = _hash_code(req.code)

    def _redeem():
        conn = _get_conn()
        row = conn.execute("SELECT * FROM redemption_codes WHERE code_hash = ?", (code_hash,)).fetchone()
        if not row:
            conn.close()
            return None, None, "That code isn't valid. Double-check it and try again."
        if row["used_by_user_id"]:
            conn.close()
            return None, None, "That code has already been used."
        try:
            expires = datetime.fromisoformat(row["expires_at"])
        except Exception:
            expires = datetime.utcnow() - timedelta(days=1)
        if expires < datetime.utcnow():
            conn.close()
            return None, None, "That code has expired."

        # Atomic claim: the WHERE clause re-checks used_by_user_id IS NULL
        # at UPDATE time, not just at the SELECT above — two concurrent
        # redemptions of the same code could otherwise both pass the
        # "not yet used" check before either commits, letting one code
        # activate premium for two different people. rowcount tells us
        # whether OUR update actually won that race.
        cursor = conn.execute(
            "UPDATE redemption_codes SET used_by_user_id = ?, used_at = ? WHERE code_hash = ? AND used_by_user_id IS NULL",
            (current_user["id"], datetime.utcnow().isoformat(), code_hash)
        )
        if cursor.rowcount != 1:
            conn.close()
            return None, None, "That code has already been used."
        conn.commit()
        plan = row["plan"]
        new_expiry = _activate_subscription(conn, current_user["id"], plan, "code")
        conn.close()
        return plan, new_expiry, None

    plan, new_expiry, error = await asyncio.to_thread(_redeem)
    if error:
        raise HTTPException(400, error)
    return {
        "message": f"Activated! You're now Premium ({ALL_PLANS[plan]['label']}) until {new_expiry.date().isoformat()}.",
        "plan": plan,
        "expires_at": new_expiry.isoformat(),
    }


# ── Routes: admin ─────────────────────────────────────────────────────────
# Reuses admin.py's existing header-password auth rather than inventing a
# second admin scheme.

from admin import _require_admin  # noqa: E402 — after router/helpers defined above, avoids any import-order ambiguity


@router.post("/admin/generate-codes")
def admin_generate_codes(req: GenerateCodesRequest, admin=Depends(_require_admin)):
    if req.plan not in ALL_PLANS:
        raise HTTPException(400, f"Unknown plan. Choose from: {', '.join(ALL_PLANS.keys())}")
    if not (1 <= req.count <= 500):
        raise HTTPException(400, "count must be between 1 and 500.")

    expires_at = (datetime.utcnow() + timedelta(days=req.validity_days)).isoformat()
    conn = _get_conn()
    plaintext_codes = []
    for _ in range(req.count):
        # Collision odds are astronomically low (8 chars from a 32-char
        # alphabet ≈ 1.1 trillion combinations) but the UNIQUE constraint
        # on code_hash is the real backstop — this retry loop just means
        # a batch request never fails outright over one in-a-trillion hit.
        for attempt in range(5):
            code = _generate_code()
            code_hash = _hash_code(code)
            exists = conn.execute(
                "SELECT 1 FROM redemption_codes WHERE code_hash = ?", (code_hash,)
            ).fetchone()
            if not exists:
                break
        else:
            conn.close()
            raise HTTPException(500, "Could not generate a unique code after several attempts — try again.")

        conn.execute(
            """INSERT INTO redemption_codes (code_hash, plan, batch_note, issued_by_role, expires_at)
               VALUES (?, ?, ?, 'admin', ?)""",
            (code_hash, req.plan, req.note, expires_at)
        )
        plaintext_codes.append(code)
    conn.commit()
    conn.close()

    return {
        "plan": req.plan,
        "count": req.count,
        "codes": plaintext_codes,
        "expires_at": expires_at,
        "warning": "Save these now — codes are hashed at rest and this is the only time they're shown in plaintext.",
    }


@router.get("/admin/transactions")
def admin_list_transactions(limit: int = 100, admin=Depends(_require_admin)):
    limit = max(1, min(limit, 500))
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM payment_transactions ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return {"transactions": [dict(r) for r in rows]}


@router.get("/admin/codes")
def admin_list_codes(limit: int = 200, admin=Depends(_require_admin)):
    """Never returns plaintext codes — only metadata (plan, used/unused,
    who used it, when). Plaintext is shown exactly once, at generation."""
    limit = max(1, min(limit, 1000))
    conn = _get_conn()
    rows = conn.execute(
        """SELECT id, plan, batch_note, issued_by_role, used_by_user_id, used_at, created_at, expires_at
           FROM redemption_codes ORDER BY created_at DESC LIMIT ?""",
        (limit,)
    ).fetchall()
    conn.close()
    return {"codes": [dict(r) for r in rows]}