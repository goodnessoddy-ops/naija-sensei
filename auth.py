"""
auth.py — JWT authentication for NaijaSensei
Drop this file next to server.py

Install:
  pip install "python-jose[cryptography]" "passlib[bcrypt]" python-multipart
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import Optional

from db import _get_conn  # noqa: F401 — re-exported for every other
# module's `from auth import _get_conn`. See db.py for why the DB layer
# moved off SQLite (concurrency ceiling + can't be shared across replicas).

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from security import require_env_secret, login_attempts

# ── Config ────────────────────────────────────────────────────────────────────
SECRET_KEY = require_env_secret("JWT_SECRET_KEY", min_length=32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

router = APIRouter(prefix="/auth", tags=["auth"])

# ── PostgreSQL DB ─────────────────────────────────────────────────────────────
# _get_conn is imported from db.py above — a pooled Postgres connection,
# not a fresh file handle per call. See db.py's module docstring for the
# full rationale and the connection-pool sizing note.

def init_db():
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         BIGSERIAL PRIMARY KEY,
            username   TEXT UNIQUE NOT NULL,
            email      TEXT UNIQUE NOT NULL,
            full_name  TEXT,
            role       TEXT DEFAULT 'student',
            hashed_pw  TEXT NOT NULL,
            created_at TEXT DEFAULT (now_iso())
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id         BIGSERIAL PRIMARY KEY,
            user_id    INTEGER NOT NULL,
            role       TEXT NOT NULL,
            content    TEXT NOT NULL,
            created_at TEXT DEFAULT (now_iso()),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_activity (
            user_id       INTEGER PRIMARY KEY,
            last_active   TEXT DEFAULT (now_iso()),
            warned        INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Suspension flag — safe migration, won't break existing accounts.
    # ADD COLUMN IF NOT EXISTS is idempotent in Postgres (unlike SQLite,
    # a failed ALTER here would abort the rest of this transaction, so
    # this replaces the old try/except-swallow pattern rather than just
    # wrapping the same statement).
    conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_suspended INTEGER DEFAULT 0")

    # Per-subject chat threads — NULL subject = the general/main chat.
    # Existing rows are untouched (they default to NULL = still the main chat).
    conn.execute("ALTER TABLE chat_history ADD COLUMN IF NOT EXISTS subject TEXT DEFAULT NULL")
    conn.execute("ALTER TABLE chat_history ADD COLUMN IF NOT EXISTS topic TEXT DEFAULT NULL")

    # Per-day time-on-app tracking, incremented by /auth/heartbeat
    conn.execute("""
        CREATE TABLE IF NOT EXISTS activity_minutes (
            id         BIGSERIAL PRIMARY KEY,
            user_id    INTEGER NOT NULL,
            date       TEXT NOT NULL,
            minutes    INTEGER DEFAULT 0,
            UNIQUE(user_id, date),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Insert-only log of every free-tier chat message sent, used solely to
    # enforce the daily FREE_CHAT_MESSAGES_PER_DAY quota in billing.py.
    # Deliberately a SEPARATE table from chat_history: chat_history is what
    # "Clear chat" deletes so a student can start a fresh conversation, but
    # if the quota were counted from chat_history itself, clearing the chat
    # would also wipe today's message count and let a free-tier student
    # bypass the daily limit just by clearing the chat and continuing.
    # Nothing ever deletes rows from this table except the same 5-month
    # inactivity expiry that wipes chat_history (see clear_all_history()).
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_quota_log (
            id         BIGSERIAL PRIMARY KEY,
            user_id    INTEGER NOT NULL,
            created_at TEXT DEFAULT (now_iso()),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Generic admin-configurable settings store. Currently holds exactly
    # one key ("waec_end_date") — see set_waec_end_date()/get_waec_end_date()
    # below — but kept generic (key/value) rather than a single dedicated
    # column somewhere, so future admin-settable app-wide settings can
    # reuse this same table instead of each needing their own migration.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    # Marks that a given user's history has already been cleared for a
    # given WAEC end date, so check_and_expire_history() fires the
    # clearing + farewell message exactly ONCE per student per WAEC
    # cycle, not on every single /history call made after the expiry
    # date has passed. When the admin sets a NEW waec_end_date next year
    # (a different string), every student is naturally eligible again,
    # since the uniqueness is keyed on the (user_id, waec_end_date) pair.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS waec_expiry_log (
            id            BIGSERIAL PRIMARY KEY,
            user_id       INTEGER NOT NULL,
            waec_end_date TEXT NOT NULL,
            cleared_at    TEXT DEFAULT (now_iso()),
            UNIQUE(user_id, waec_end_date),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()
    print("[NaijaSensei] Auth DB ready.")


# ── Admin-configured WAEC end date ──────────────────────────────────────────
def get_waec_end_date() -> Optional[str]:
    """
    The date WAEC officially ended this year, as an ISO 'YYYY-MM-DD'
    string, set by an admin (see set_waec_end_date()). Returns None if no
    admin has set one yet — in that case check_and_expire_history() falls
    back to its old 5-months-of-inactivity rule rather than doing nothing,
    so history expiry still works sensibly before the admin panel piece
    of this feature exists.
    """
    conn = _get_conn()
    row = conn.execute("SELECT value FROM app_settings WHERE key = 'waec_end_date'").fetchone()
    conn.close()
    return row["value"] if row else None


def set_waec_end_date(end_date_iso: str):
    """
    Admin-only — record the date WAEC officially ended this year.
    check_and_expire_history() clears every student's chat history
    HISTORY_EXPIRY_MONTHS_AFTER_WAEC months after this date, once per
    student per exact date value (see waec_expiry_log). Calling this
    again next year with a new date automatically makes every student
    eligible for a fresh clearing cycle, since the uniqueness constraint
    in waec_expiry_log is keyed on (user_id, waec_end_date) together —
    a different date string is, by definition, a new cycle.

    NOTE: this function does no authorization check itself — the caller
    (the HTTP endpoint that calls this) is responsible for confirming the
    requester is actually an admin before calling it. This lives in
    auth.py purely because it touches the same connection/table
    conventions as the rest of this file, not because it's meant to be
    reachable directly.
    """
    conn = _get_conn()
    conn.execute("""
        INSERT INTO app_settings (key, value) VALUES ('waec_end_date', ?)
        ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
    """, (end_date_iso,))
    conn.commit()
    conn.close()


def get_activity_summary(user_id: int) -> dict:
    """{today_minutes, week_minutes, total_minutes} for a given user."""

    conn = _get_conn()
    today = datetime.utcnow().date().isoformat()
    week_ago = (datetime.utcnow().date() - timedelta(days=7)).isoformat()
    today_row = conn.execute(
        "SELECT minutes FROM activity_minutes WHERE user_id=? AND date=?", (user_id, today)
    ).fetchone()
    week_row = conn.execute(
        "SELECT SUM(minutes) as total FROM activity_minutes WHERE user_id=? AND date>=?",
        (user_id, week_ago)
    ).fetchone()
    total_row = conn.execute(
        "SELECT SUM(minutes) as total FROM activity_minutes WHERE user_id=?", (user_id,)
    ).fetchone()
    conn.close()
    return {
        "today_minutes": today_row["minutes"] if today_row else 0,
        "week_minutes": (week_row["total"] or 0) if week_row else 0,
        "total_minutes": (total_row["total"] or 0) if total_row else 0,
    }


# ── Chat memory functions ─────────────────────────────────────────────────────
import json
from datetime import datetime, timedelta

HISTORY_EXPIRY_MONTHS = 5
WARN_MESSAGE = (
    "Omo, it's been a while since you last used NaijaSensei. "
    "I'm going to clear our chat history now to free up space. "
    "Come back anytime you need help — welcome back whenever you're ready!"
)

# How long after the admin-set WAEC end date (see set_waec_end_date()) a
# student's chat history gets cleared. Only takes effect once an admin has
# actually set a waec_end_date — until then, check_and_expire_history()
# falls back to the plain inactivity rule above.
HISTORY_EXPIRY_MONTHS_AFTER_WAEC = 3
WAEC_WARN_MESSAGE = (
    "Omo, I just realised it's been {months} months since your WAEC. "
    "You don finish the exam — well done! "
    "I'm going to clear our chat history now to free up space. "
    "Come back anytime you need help with your next exams. All the best!"
)

def _normalize_thread_filters(subject: str = None, topic: str = None) -> tuple:
    """
    get_history()'s branching only understands three combinations:
    (subject+topic), (subject only), (neither). A topic given WITHOUT a
    subject isn't one of those — save_message() would happily write a row
    tagged topic-but-no-subject, but get_history() has no branch that ever
    reads it back, so the message becomes permanently unreachable. This
    should never happen if callers always pass subject alongside topic (as
    server.py's /chat does), but nothing enforces that at the type level,
    so guard against it here too, at the storage layer, rather than trusting
    every call site to get it right.
    """
    if topic and not subject:
        print(f"[auth] Warning: topic '{topic}' given without a subject — "
              f"dropping the topic so this doesn't land in an unreachable bucket.")
        topic = None
    return subject, topic


def save_message(user_id: int, role: str, content: str, subject: str = None, topic: str = None):
    """Save a single chat message to the DB. subject=None means the
    general/main chat; a subject value scopes it to that subject's thread."""
    subject, topic = _normalize_thread_filters(subject, topic)
    conn = _get_conn()
    conn.execute(
        "INSERT INTO chat_history (user_id, role, content, subject, topic) VALUES (?, ?, ?, ?, ?)",
        (user_id, role, content, subject or None, topic or None)
    )
    # Update last_active
    conn.execute("""
        INSERT INTO user_activity (user_id, last_active, warned)
        VALUES (?, now_iso(), 0)
        ON CONFLICT(user_id) DO UPDATE SET last_active=now_iso()
    """, (user_id,))
    conn.commit()
    conn.close()


def log_chat_message_for_quota(user_id: int):
    """Record one free-tier chat message toward the daily quota. Insert-only
    and written to chat_quota_log (NOT chat_history) so that clearing the
    chat via clear_history() can never reduce today's count — see the
    chat_quota_log table comment in init_db() for why this has to be a
    separate table. Call this once per student-sent message, alongside
    save_message(), before quota-gated content is generated."""
    conn = _get_conn()
    conn.execute(
        "INSERT INTO chat_quota_log (user_id) VALUES (?)", (user_id,)
    )
    conn.commit()
    conn.close()

def get_history(user_id: int, subject: str = None, topic: str = None) -> list[dict]:
    """Load chat history for a user.
    subject=None, topic=None -> the general/main chat (subject IS NULL).
    subject=X, topic=None -> that subject's whole thread, all topics mixed (unchanged existing behavior).
    subject=X, topic=Y -> ONLY that exact (subject, topic) thread, isolated from the rest of the subject."""
    subject, topic = _normalize_thread_filters(subject, topic)
    conn = _get_conn()
    if subject and topic:
        rows = conn.execute(
            "SELECT role, content FROM chat_history WHERE user_id = ? AND subject = ? AND topic = ? ORDER BY id ASC",
            (user_id, subject, topic)
        ).fetchall()
    elif subject:
        rows = conn.execute(
            "SELECT role, content FROM chat_history WHERE user_id = ? AND subject = ? ORDER BY id ASC",
            (user_id, subject)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT role, content FROM chat_history WHERE user_id = ? AND subject IS NULL ORDER BY id ASC",
            (user_id,)
        ).fetchall()
    conn.close()
    return [{"role": r["role"], "content": r["content"]} for r in rows]

def clear_history(user_id: int, subject: str = None, topic: str = None):
    """Wipe one chat thread for a user. subject=None clears the general
    chat only (existing 'Clear chat' button behaviour, unchanged) — a
    subject value clears only that subject's thread — subject+topic
    together clears only that isolated topic thread, leaving the rest of
    the subject's messages (and other topics under it) untouched."""
    subject, topic = _normalize_thread_filters(subject, topic)
    conn = _get_conn()
    if subject and topic:
        conn.execute(
            "DELETE FROM chat_history WHERE user_id = ? AND subject = ? AND topic = ?",
            (user_id, subject, topic)
        )
    elif subject:
        conn.execute(
            "DELETE FROM chat_history WHERE user_id = ? AND subject = ?", (user_id, subject)
        )
    else:
        conn.execute("DELETE FROM chat_history WHERE user_id = ? AND subject IS NULL", (user_id,))
        conn.execute("DELETE FROM user_activity WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def clear_all_history(user_id: int):
    """Wipe EVERY chat thread for a user — the general chat and every
    subject thread — plus their quota log. Used only by the 5-month
    inactivity expiry job, not by the regular 'Clear chat' button."""
    conn = _get_conn()
    conn.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM user_activity WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM chat_quota_log WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def check_and_expire_history(user_id: int) -> Optional[str]:
    """
    Two rules, tried in this order:

    1. WAEC-date rule (primary, once an admin has set one): if
       get_waec_end_date() returns a date, and we're now
       HISTORY_EXPIRY_MONTHS_AFTER_WAEC months past it, clear this
       student's history — but only once per student per that exact
       date value (waec_expiry_log), so this doesn't re-fire on every
       single /history call made after the date has passed. Setting a
       new waec_end_date next year naturally makes every student
       eligible again, since eligibility is keyed on (user_id,
       waec_end_date) together.

    2. Inactivity rule (fallback, only when no admin has set a WAEC end
       date yet): the original behavior — clear after
       HISTORY_EXPIRY_MONTHS of no activity at all. This exists so
       history expiry still works sensibly before the admin panel's WAEC
       end date has ever been set, rather than simply never expiring
       anything in that gap.

    Returns a farewell message string if history was cleared, else None.
    Clears ALL threads (general + every subject) either way.
    """
    waec_end_date = get_waec_end_date()

    if waec_end_date:
        expiry = datetime.fromisoformat(waec_end_date) + timedelta(days=30 * HISTORY_EXPIRY_MONTHS_AFTER_WAEC)
        if datetime.utcnow() < expiry:
            return None

        conn = _get_conn()
        already_done = conn.execute(
            "SELECT 1 FROM waec_expiry_log WHERE user_id = ? AND waec_end_date = ?",
            (user_id, waec_end_date)
        ).fetchone()
        if already_done:
            conn.close()
            return None

        conn.close()
        clear_all_history(user_id)

        conn = _get_conn()
        conn.execute(
            "INSERT INTO waec_expiry_log (user_id, waec_end_date) VALUES (?, ?) ON CONFLICT (user_id, waec_end_date) DO NOTHING",
            (user_id, waec_end_date)
        )
        conn.commit()
        conn.close()

        return WAEC_WARN_MESSAGE.format(months=HISTORY_EXPIRY_MONTHS_AFTER_WAEC)

    # No WAEC end date set by an admin yet — fall back to the inactivity rule.
    conn = _get_conn()
    row = conn.execute(
        "SELECT last_active, warned FROM user_activity WHERE user_id = ?",
        (user_id,)
    ).fetchone()
    conn.close()

    if not row:
        return None

    last_active = datetime.fromisoformat(row["last_active"])
    expiry = last_active + timedelta(days=30 * HISTORY_EXPIRY_MONTHS)

    if datetime.utcnow() >= expiry:
        clear_all_history(user_id)
        return WARN_MESSAGE

    return None


# ── Schemas ───────────────────────────────────────────────────────────────────
class UserCreate(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    role: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut

# ── Helpers ───────────────────────────────────────────────────────────────────
def _hash(pw: str) -> str:
    return pwd_context.hash(pw)

def _verify(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def _create_token(username: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    return jwt.encode({"sub": username, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)

def _get_user(username: str) -> Optional[dict]:
    conn = _get_conn()
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return dict(row) if row else None

# ── Dependency ────────────────────────────────────────────────────────────────
async def get_current_user(token: str = Depends(oauth2_scheme)) -> Optional[dict]:
    """Returns the current user, or None if no/invalid token/suspended account."""
    if token is None:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            return None
    except JWTError:
        return None
    # This dependency runs on nearly every authenticated request, so the
    # DB lookup is pushed to a worker thread rather than blocking the
    # event loop directly — with a pooled Postgres connection under
    # real concurrent load, blocking here would stall every other
    # in-flight request on this process, not just this one.
    user = await asyncio.to_thread(_get_user, username)
    if user and user.get("is_suspended"):
        return None  # suspended mid-session — treated as logged out
    return user

async def require_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Hard-require auth — raises 401 if not logged in."""
    user = await get_current_user(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please log in to continue.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def require_student(token: str = Depends(oauth2_scheme)) -> dict:
    """Hard-require auth AND that the account's role is 'student'.
    Use for student-only features (classroom, exams, homework, etc.) so a
    teacher/parent's own login can't hit those endpoints directly even
    though the UI already hides the buttons for them."""
    user = await require_user(token)
    if (user.get("role") or "student") != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This feature is only available to student accounts.",
        )
    return user

# ── Routes ────────────────────────────────────────────────────────────────────
@router.post("/register", response_model=Token, status_code=201)
def register(body: UserCreate):
    conn = _get_conn()
    existing = conn.execute(
        "SELECT id FROM users WHERE username = ? OR email = ?",
        (body.username, body.email)
    ).fetchone()
    if existing:
        conn.close()
        raise HTTPException(status_code=400, detail="Username or email already taken.")

    cursor = conn.execute(
        "INSERT INTO users (username, email, full_name, hashed_pw) VALUES (?, ?, ?, ?) RETURNING id",
        (body.username, body.email, body.full_name, _hash(body.password))
    )
    conn.commit()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()
    conn.close()
    user = dict(row)
    return {"access_token": _create_token(user["username"]), "token_type": "bearer", "user": user}

@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends()):
    locked, retry_after = login_attempts.is_locked(form.username)
    if locked:
        raise HTTPException(
            status_code=429,
            detail=f"Too many failed login attempts for this account. Try again in {retry_after} seconds."
        )
    user = _get_user(form.username)
    if not user or not _verify(form.password, user["hashed_pw"]):
        login_attempts.record_failure(form.username)
        raise HTTPException(status_code=401, detail="Incorrect username or password.")
    if user.get("is_suspended"):
        raise HTTPException(status_code=403, detail="This account has been suspended. Please contact your teacher or parent.")
    login_attempts.record_success(form.username)
    return {"access_token": _create_token(user["username"]), "token_type": "bearer", "user": user}


@router.post("/heartbeat")
def heartbeat(current_user: dict = Depends(require_user)):
    """Called every ~60s by the frontend while the tab is open and focused."""
    conn = _get_conn()
    today = datetime.utcnow().date().isoformat()
    conn.execute("""
        INSERT INTO activity_minutes (user_id, date, minutes) VALUES (?, ?, 1)
        ON CONFLICT(user_id, date) DO UPDATE SET minutes = activity_minutes.minutes + 1
    """, (current_user["id"], today))
    conn.commit()
    conn.close()
    return {"ok": True}


@router.get("/me", response_model=UserOut)
def me(current_user: dict = Depends(require_user)):
    return current_user