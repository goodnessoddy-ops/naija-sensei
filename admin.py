"""
admin.py — Owner/Admin Dashboard for NaijaSensei.

Password-protected with a separate ADMIN_PASSWORD env variable.
Accessible at /admin (a separate HTML page, not part of the student app).

Features:
- All registered users (students, teachers, parents) with stats
- All exams written — scores, subjects, pass rates, trends
- Most popular topics and subjects
- Active users, new signups over time
- Chat activity overview
- User management (change roles, deactivate)
- Real-time site health (provider usage, error rates)
"""

import os
import json
from datetime import datetime, timedelta, date
from collections import Counter
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from auth import _get_conn, get_waec_end_date, set_waec_end_date
from security import require_env_secret, constant_time_equals

router = APIRouter(prefix="/admin", tags=["admin"])

# Validated at import time — this used to silently fall back to the
# hardcoded string "naijasensei-admin-2025", which is now public (it was
# committed to this codebase's source). See security.py's docstring.
ADMIN_PASSWORD = require_env_secret("ADMIN_PASSWORD", min_length=12)


def _require_admin(x_admin_password: str = Header(None)):
    """Header-based admin auth. Set ADMIN_PASSWORD in your .env.
    Uses a constant-time comparison — a plain `!=` here leaks how many
    leading characters of a guess were correct via response-time
    differences, which is a real (if slow) attack against a
    single-shared-password scheme like this one."""
    if not constant_time_equals(x_admin_password or "", ADMIN_PASSWORD):
        raise HTTPException(401, "Invalid admin password.")
    return True


# ── Overview Stats ─────────────────────────────────────────────────────────────

@router.get("/stats")
def get_stats(admin=Depends(_require_admin)):
    """High-level overview: users, exams, activity."""
    conn = _get_conn()

    # User counts by role
    user_counts = {}
    for role in ("student", "teacher", "parent"):
        row = conn.execute(
            "SELECT COUNT(*) as c FROM users WHERE role = ?", (role,)
        ).fetchone()
        user_counts[role] = row["c"] if row else 0
    total_users = sum(user_counts.values())

    # New signups in last 7 and 30 days
    new_7d = conn.execute(
        "SELECT COUNT(*) as c FROM users WHERE created_at::timestamp >= (NOW() - INTERVAL '7 days')"
    ).fetchone()["c"]
    new_30d = conn.execute(
        "SELECT COUNT(*) as c FROM users WHERE created_at::timestamp >= (NOW() - INTERVAL '30 days')"
    ).fetchone()["c"]

    # Exam stats
    total_exams = conn.execute(
        "SELECT COUNT(*) as c FROM exam_sessions WHERE submitted_at IS NOT NULL"
    ).fetchone()["c"]
    exams_7d = conn.execute(
        "SELECT COUNT(*) as c FROM exam_sessions WHERE submitted_at::timestamp >= (NOW() - INTERVAL '7 days')"
    ).fetchone()["c"]

    avg_score_row = conn.execute(
        "SELECT AVG(CAST(score AS FLOAT) / CAST(max_score AS FLOAT) * 100) as avg FROM exam_sessions WHERE submitted_at IS NOT NULL AND max_score > 0"
    ).fetchone()
    avg_score = round(avg_score_row["avg"], 1) if avg_score_row["avg"] else None

    pass_rate_row = conn.execute(
        "SELECT COUNT(*) as c FROM exam_sessions WHERE submitted_at IS NOT NULL AND max_score > 0 AND (CAST(score AS FLOAT) / CAST(max_score AS FLOAT)) >= 0.5"
    ).fetchone()
    pass_rate = round(pass_rate_row["c"] / max(total_exams, 1) * 100, 1)

    # Chat activity
    total_messages = conn.execute(
        "SELECT COUNT(*) as c FROM chat_history"
    ).fetchone()["c"]
    messages_7d = conn.execute(
        "SELECT COUNT(*) as c FROM chat_history WHERE created_at::timestamp >= (NOW() - INTERVAL '7 days')"
    ).fetchone()["c"]

    # Active users (any chat or exam in last 7 days)
    active_7d = conn.execute("""
        SELECT COUNT(DISTINCT user_id) as c FROM (
            SELECT user_id FROM chat_history WHERE created_at::timestamp >= (NOW() - INTERVAL '7 days')
            UNION
            SELECT user_id FROM exam_sessions WHERE started_at::timestamp >= (NOW() - INTERVAL '7 days')
        )
    """).fetchone()["c"]

    # Premium subscribers — "currently premium" means the same thing
    # billing.py's is_premium() checks: an active subscription row whose
    # expires_at hasn't passed yet. Counted directly in SQL rather than
    # looping is_premium() over every user.
    total_premium = conn.execute(
        "SELECT COUNT(*) as c FROM subscriptions WHERE status = 'active' AND expires_at::timestamp > NOW()"
    ).fetchone()["c"]
    premium_by_plan_rows = conn.execute(
        """SELECT plan, COUNT(*) as c FROM subscriptions
           WHERE status = 'active' AND expires_at::timestamp > NOW()
           GROUP BY plan ORDER BY c DESC"""
    ).fetchall()
    premium_by_plan = {r["plan"]: r["c"] for r in premium_by_plan_rows}
    premium_new_7d = conn.execute(
        """SELECT COUNT(*) as c FROM subscriptions
           WHERE status = 'active' AND expires_at::timestamp > NOW()
           AND activated_at::timestamp >= (NOW() - INTERVAL '7 days')"""
    ).fetchone()["c"]

    conn.close()

    return {
        "users": {
            "total": total_users,
            "by_role": user_counts,
            "new_7d": new_7d,
            "new_30d": new_30d,
            "active_7d": active_7d,
        },
        "exams": {
            "total": total_exams,
            "last_7d": exams_7d,
            "avg_score_pct": avg_score,
            "pass_rate_pct": pass_rate,
        },
        "chat": {
            "total_messages": total_messages,
            "messages_7d": messages_7d,
        },
        "premium": {
            "total": total_premium,
            "by_plan": premium_by_plan,
            "new_7d": premium_new_7d,
            "pct_of_users": round(total_premium / max(total_users, 1) * 100, 1),
        },
    }


# ── User Management ───────────────────────────────────────────────────────────

@router.get("/users")
def get_all_users(admin=Depends(_require_admin)):
    """All registered users with their stats."""
    conn = _get_conn()
    users = conn.execute(
        "SELECT id, username, full_name, email, role, share_code, created_at FROM users ORDER BY created_at DESC"
    ).fetchall()

    result = []
    for u in users:
        uid = u["id"]
        exam_row = conn.execute(
            "SELECT COUNT(*) as c, AVG(CAST(score AS FLOAT)/CAST(max_score AS FLOAT)*100) as avg FROM exam_sessions WHERE user_id=? AND submitted_at IS NOT NULL AND max_score>0",
            (uid,)
        ).fetchone()
        msg_row = conn.execute(
            "SELECT COUNT(*) as c FROM chat_history WHERE user_id=?", (uid,)
        ).fetchone()
        last_active = conn.execute(
            "SELECT MAX(created_at) as la FROM chat_history WHERE user_id=?", (uid,)
        ).fetchone()
        result.append({
            "id": uid,
            "username": u["username"],
            "full_name": u["full_name"],
            "email": u["email"],
            "role": u["role"] or "student",
            "share_code": u["share_code"],
            "registered_at": u["created_at"],
            "exams_taken": exam_row["c"] if exam_row else 0,
            "avg_score": round(exam_row["avg"], 1) if exam_row and exam_row["avg"] else None,
            "messages_sent": msg_row["c"] if msg_row else 0,
            "last_active": last_active["la"] if last_active else None,
        })
    conn.close()
    return {"users": result}


class UpdateUserRequest(BaseModel):
    role: str | None = None
    active: bool | None = None


@router.patch("/users/{user_id}")
def update_user(user_id: int, req: UpdateUserRequest, admin=Depends(_require_admin)):
    """Change a user's role."""
    conn = _get_conn()
    if req.role:
        if req.role not in ("student", "teacher", "parent", "admin"):
            raise HTTPException(400, "Invalid role.")
        conn.execute("UPDATE users SET role=? WHERE id=?", (req.role, user_id))
    conn.commit()
    conn.close()
    return {"message": "User updated."}


@router.delete("/users/{user_id}")
def delete_user(user_id: int, admin=Depends(_require_admin)):
    """Delete a user and all their data."""
    conn = _get_conn()
    conn.execute("DELETE FROM chat_history WHERE user_id=?", (user_id,))
    conn.execute("DELETE FROM exam_sessions WHERE user_id=?", (user_id,))
    conn.execute("DELETE FROM user_activity WHERE user_id=?", (user_id,))
    conn.execute("DELETE FROM class_members WHERE student_id=?", (user_id,))
    conn.execute("DELETE FROM parent_links WHERE parent_id=? OR student_id=?", (user_id, user_id))
    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    return {"message": "User deleted."}


# ── Exam Analytics ────────────────────────────────────────────────────────────

@router.get("/exams")
def get_exam_analytics(admin=Depends(_require_admin)):
    """Full exam analytics — scores, subjects, trends, popular topics."""
    conn = _get_conn()

    # All completed exams
    exams = conn.execute("""
        SELECT e.id, e.user_id, u.username, u.full_name, e.subjects,
               e.score, e.max_score, e.started_at, e.submitted_at
        FROM exam_sessions e
        JOIN users u ON u.id = e.user_id
        WHERE e.submitted_at IS NOT NULL
        ORDER BY e.submitted_at DESC
        LIMIT 200
    """).fetchall()

    # Subject frequency — how often each subject is practised
    subject_counter = Counter()
    score_by_subject: dict[str, list] = {}
    daily_exams: dict[str, int] = {}

    for e in exams:
        try:
            subjects = json.loads(e["subjects"])
            for s in subjects:
                subject_counter[s] += 1
                pct = round(e["score"] / e["max_score"] * 100, 1) if e["score"] and e["max_score"] else None
                if pct is not None:
                    score_by_subject.setdefault(s, []).append(pct)
            # Daily trend
            day = e["submitted_at"][:10] if e["submitted_at"] else None
            if day:
                daily_exams[day] = daily_exams.get(day, 0) + 1
        except Exception:
            continue

    subject_stats = []
    for subj, count in subject_counter.most_common():
        scores = score_by_subject.get(subj, [])
        subject_stats.append({
            "subject": subj,
            "exam_count": count,
            "avg_score": round(sum(scores)/len(scores), 1) if scores else None,
            "pass_rate": round(sum(1 for s in scores if s >= 50) / max(len(scores), 1) * 100, 1) if scores else None,
        })

    # Recent exams list
    recent = []
    for e in exams[:50]:
        pct = round(e["score"] / e["max_score"] * 100, 1) if e["score"] and e["max_score"] else None
        recent.append({
            "id": e["id"],
            "student": e["full_name"] or e["username"],
            "subjects": json.loads(e["subjects"]) if e["subjects"] else [],
            "score_pct": pct,
            "submitted_at": e["submitted_at"],
        })

    # Sort daily trend
    daily_sorted = sorted(daily_exams.items())[-30:]

    conn.close()
    return {
        "subject_stats": subject_stats,
        "recent_exams": recent,
        "daily_trend": [{"date": d, "count": c} for d, c in daily_sorted],
    }


# ── Signup Trend ──────────────────────────────────────────────────────────────

@router.get("/signups")
def get_signup_trend(admin=Depends(_require_admin)):
    """Daily signup counts for the last 30 days."""
    conn = _get_conn()
    rows = conn.execute("""
        SELECT DATE(created_at) as day, COUNT(*) as count
        FROM users
        WHERE created_at::timestamp >= (NOW() - INTERVAL '30 days')
        GROUP BY day ORDER BY day
    """).fetchall()
    conn.close()
    return {"signups": [{"date": r["day"], "count": r["count"]} for r in rows]}


# ── Chat Activity ─────────────────────────────────────────────────────────────

@router.get("/chat-activity")
def get_chat_activity(admin=Depends(_require_admin)):
    """Daily message counts and most active users."""
    conn = _get_conn()

    daily = conn.execute("""
        SELECT DATE(created_at) as day, COUNT(*) as count
        FROM chat_history
        WHERE created_at::timestamp >= (NOW() - INTERVAL '30 days')
        GROUP BY day ORDER BY day
    """).fetchall()

    top_users = conn.execute("""
        SELECT u.username, u.full_name, u.role, COUNT(ch.id) as msg_count
        FROM chat_history ch
        JOIN users u ON u.id = ch.user_id
        WHERE ch.role='user'
        GROUP BY ch.user_id
        ORDER BY msg_count DESC
        LIMIT 10
    """).fetchall()

    conn.close()
    return {
        "daily_messages": [{"date": r["day"], "count": r["count"]} for r in daily],
        "top_users": [dict(r) for r in top_users],
    }


# ── Classes Overview ──────────────────────────────────────────────────────────

@router.get("/classes")
def get_classes_overview(admin=Depends(_require_admin)):
    """All classes with teacher and student count."""
    conn = _get_conn()
    classes = conn.execute("""
        SELECT c.id, c.name, c.invite_code, c.created_at,
               u.username as teacher, u.full_name as teacher_name,
               COUNT(cm.student_id) as student_count
        FROM classes c
        JOIN users u ON u.id = c.teacher_id
        LEFT JOIN class_members cm ON cm.class_id = c.id
        GROUP BY c.id ORDER BY c.created_at DESC
    """).fetchall()
    conn.close()
    return {"classes": [dict(c) for c in classes]}


# ── Broadcast Messages ────────────────────────────────────────────────────────

class BroadcastRequest(BaseModel):
    message: str
    target: str = "all"          # "all", "students", "teachers", "parents", or "user:{id}"
    sender_label: str = "NaijaSensei Admin"


def _init_broadcast_table():
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS broadcasts (
            id          BIGSERIAL PRIMARY KEY,
            sender_type TEXT NOT NULL DEFAULT 'admin',  -- 'admin' or 'teacher'
            sender_id   INTEGER,                         -- NULL for admin
            sender_label TEXT NOT NULL,
            message     TEXT NOT NULL,
            target      TEXT NOT NULL,
            sent_at     TEXT DEFAULT (now_iso())
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS broadcast_reads (
            broadcast_id INTEGER NOT NULL,
            user_id      INTEGER NOT NULL,
            read_at      TEXT DEFAULT (now_iso()),
            PRIMARY KEY (broadcast_id, user_id)
        )
    """)
    conn.commit()
    conn.close()

_init_broadcast_table()
def init_broadcasts_db():
    """Public wrapper so server.py's import works, matching the
    init_*_db() naming convention used by every other module."""
    _init_broadcast_table()

@router.post("/broadcast")
def send_broadcast(req: BroadcastRequest, admin=Depends(_require_admin)):
    """Admin sends a broadcast to all users or a specific group."""
    if not req.message.strip():
        raise HTTPException(400, "Message cannot be empty.")
    conn = _get_conn()
    conn.execute(
        "INSERT INTO broadcasts (sender_type, sender_label, message, target) VALUES ('admin', ?, ?, ?)",
        (req.sender_label or "NaijaSensei Admin", req.message.strip(), req.target)
    )
    conn.commit()
    conn.close()
    return {"message": "Broadcast sent."}


@router.get("/broadcasts")
def get_broadcasts(admin=Depends(_require_admin)):
    """List all past broadcasts with read counts."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM broadcasts ORDER BY sent_at DESC LIMIT 50"
    ).fetchall()
    result = []
    for r in rows:
        read_count = conn.execute(
            "SELECT COUNT(*) as c FROM broadcast_reads WHERE broadcast_id=?", (r["id"],)
        ).fetchone()["c"]
        result.append({**dict(r), "read_count": read_count})
    conn.close()
    return {"broadcasts": result}


class WaecResultsAnnouncementRequest(BaseModel):
    exam_year: str


@router.post("/waec-results-announcement")
def announce_waec_results(req: WaecResultsAnnouncementRequest, admin=Depends(_require_admin)):
    """
    One-click preset on top of send_broadcast() above, specifically for
    'WAEC results are out' — auto-composes the message and always targets
    students (the only ones with a Pass Predictor prediction to check
    against a real result), so admin can't accidentally send it to the
    wrong audience or with inconsistent wording. This exists because
    predictor.py's /predict/actual-result endpoint has no organic reason
    for a student to visit it on their own — once they've sat WAEC they
    have little reason to open the app again — so this is the proactive
    nudge that makes that endpoint (and therefore predictor.py's
    /predict/accuracy) actually collect data over time. Writes to the
    same broadcasts table send_broadcast() does — same history, same
    /broadcasts/me delivery to students, not a separate pipeline.
    """
    year = req.exam_year.strip()
    if not year:
        raise HTTPException(400, "exam_year is required.")

    message = (
        f"🎉 {year} WAEC results are out! Help make Pass Predictor more "
        f"accurate for the next set of students — open Pass Predictor and "
        f"tell us your real grade for each subject you sat. Takes under a "
        f"minute, and it's the only way we can ever know how well it's "
        f"actually working."
    )
    conn = _get_conn()
    conn.execute(
        "INSERT INTO broadcasts (sender_type, sender_label, message, target) VALUES ('admin', ?, ?, 'students')",
        ("NaijaSensei Admin", message)
    )
    conn.commit()
    conn.close()
    return {"message": f"{year} results announcement sent to all students.", "exam_year": year}


# ── WAEC end date (chat-history expiry trigger) ─────────────────────────────
# NOT the same thing as the "announce results are out" endpoint above — that
# fires when WAEC releases RESULTS (months later, to nudge students to report
# their grade for Pass Predictor accuracy). This is the date the EXAM ITSELF
# ended, which auth.py's check_and_expire_history() uses to know when to
# start counting HISTORY_EXPIRY_MONTHS_AFTER_WAEC (3 months) before wiping
# every student's chat history. See auth.py's docstrings for the full rule,
# including the inactivity-based fallback used before any admin sets a date
# here.

class SetWaecEndDateRequest(BaseModel):
    waec_end_date: str  # "YYYY-MM-DD"


@router.get("/waec-end-date")
def get_waec_end_date_endpoint(admin=Depends(_require_admin)):
    """Currently-configured WAEC end date, or None if no admin has set one
    yet (in which case chat history is still expiring on the old
    inactivity-only rule)."""
    return {"waec_end_date": get_waec_end_date()}


@router.post("/waec-end-date")
def set_waec_end_date_endpoint(req: SetWaecEndDateRequest, admin=Depends(_require_admin)):
    """
    Set (or update) the date WAEC officially ended this year. Every
    student's chat history will be cleared HISTORY_EXPIRY_MONTHS_AFTER_WAEC
    months after this date (see auth.py), once per student per exact date
    value — so setting a NEW date here next year automatically makes every
    student eligible for a fresh clearing cycle.
    """
    raw = req.waec_end_date.strip()
    try:
        parsed = date.fromisoformat(raw)
    except ValueError:
        raise HTTPException(400, "waec_end_date must be in YYYY-MM-DD format.")

    set_waec_end_date(parsed.isoformat())
    return {"message": f"WAEC end date set to {parsed.isoformat()}.", "waec_end_date": parsed.isoformat()}


# ── Provider Health ────────────────────────────────────────────────────────────
# Backed by provider_events, populated by ai_providers.py (Gemini/Mistral/etc.
# text fallback chain) and classroom.py (ElevenLabs TTS + Mistral vision).

@router.get("/provider-health")
def get_provider_health(admin=Depends(_require_admin)):
    """
    Per-provider success/empty/error counts (last 24h and last 7d), plus the
    most recent errors — meant to answer "why did classroom/chat/exam just
    fail?" at a glance instead of grepping terminal logs.
    """
    conn = _get_conn()

    try:
        rows_24h = conn.execute("""
            SELECT provider, event, COUNT(*) as c
            FROM provider_events
            WHERE created_at::timestamp >= (NOW() - INTERVAL '1 day')
            GROUP BY provider, event
        """).fetchall()
        rows_7d = conn.execute("""
            SELECT provider, event, COUNT(*) as c
            FROM provider_events
            WHERE created_at::timestamp >= (NOW() - INTERVAL '7 days')
            GROUP BY provider, event
        """).fetchall()
        recent_errors = conn.execute("""
            SELECT provider, detail, created_at
            FROM provider_events
            WHERE event = 'error'
            ORDER BY created_at DESC
            LIMIT 30
        """).fetchall()
    except Exception:
        # Table doesn't exist yet (server hasn't been restarted since this
        # feature was added) — degrade gracefully instead of 500ing.
        conn.close()
        return {
            "providers_24h": {}, "providers_7d": {},
            "recent_errors": [],
            "note": "No provider_events yet — restart the server so init_provider_events_db() runs.",
        }

    conn.close()

    def _shape(rows):
        by_provider: dict[str, dict] = {}
        for r in rows:
            p = by_provider.setdefault(r["provider"], {"success": 0, "empty": 0, "error": 0})
            p[r["event"]] = r["c"]
        for p, counts in by_provider.items():
            total = counts["success"] + counts["empty"] + counts["error"]
            counts["total"] = total
            counts["success_rate_pct"] = round(counts["success"] / total * 100, 1) if total else None
        return by_provider

    return {
        "providers_24h": _shape(rows_24h),
        "providers_7d": _shape(rows_7d),
        "recent_errors": [dict(r) for r in recent_errors],
    }


# ── API Costs (USD) ──────────────────────────────────────────────────────────
# Backed by api_usage_log, populated by ai_providers.py + server.py (Mistral
# text/vision calls) and classroom.py (ElevenLabs TTS). See api_costs.py's
# docstring for exact pricing sources and the estimate-vs-exact caveat.

@router.get("/api-costs")
def get_api_costs(admin=Depends(_require_admin)):
    """
    Real USD spend on paid AI APIs (Mistral text/vision, ElevenLabs TTS).
    Every other provider in the fallback chain is free-tier in this app's
    current config, so it isn't tracked here — see api_costs.py if that
    ever changes.
    """
    conn = _get_conn()

    try:
        totals = conn.execute("""
            SELECT
                (SELECT COALESCE(SUM(cost_usd), 0) FROM api_usage_log) as all_time,
                (SELECT COALESCE(SUM(cost_usd), 0) FROM api_usage_log WHERE created_at::timestamp >= (NOW() - INTERVAL '30 days')) as last_30d,
                (SELECT COALESCE(SUM(cost_usd), 0) FROM api_usage_log WHERE created_at::timestamp >= (NOW() - INTERVAL '7 days')) as last_7d,
                (SELECT COALESCE(SUM(cost_usd), 0) FROM api_usage_log WHERE created_at::timestamp >= (NOW() - INTERVAL '1 day')) as last_24h
        """).fetchone()

        by_provider = conn.execute("""
            SELECT provider,
                   COUNT(*) as calls,
                   SUM(cost_usd) as cost_usd,
                   SUM(input_tokens) as input_tokens,
                   SUM(output_tokens) as output_tokens,
                   SUM(characters) as characters,
                   SUM(is_estimate) as estimated_calls
            FROM api_usage_log
            GROUP BY provider
        """).fetchall()

        daily_trend = conn.execute("""
            SELECT date(created_at) as date, provider, SUM(cost_usd) as cost_usd
            FROM api_usage_log
            WHERE created_at::timestamp >= (NOW() - INTERVAL '30 days')
            GROUP BY date(created_at), provider
            ORDER BY date ASC
        """).fetchall()
    except Exception:
        conn.close()
        return {
            "total_all_time_usd": 0, "total_30d_usd": 0, "total_7d_usd": 0, "total_24h_usd": 0,
            "by_provider": {}, "daily_trend": [],
            "note": "No api_usage_log yet — restart the server so init_api_costs_db() runs, "
                    "then use the app (chat or classroom) to generate some usage.",
        }

    conn.close()

    provider_shape = {}
    for r in by_provider:
        provider_shape[r["provider"]] = {
            "calls": r["calls"],
            "cost_usd": round(r["cost_usd"] or 0, 4),
            "input_tokens": r["input_tokens"] or 0,
            "output_tokens": r["output_tokens"] or 0,
            "characters": r["characters"] or 0,
            "estimated_calls": r["estimated_calls"] or 0,
        }

    trend_by_date: dict[str, dict] = {}
    for r in daily_trend:
        d = trend_by_date.setdefault(r["date"], {"date": r["date"], "mistral": 0, "elevenlabs": 0})
        d[r["provider"]] = round(r["cost_usd"] or 0, 4)

    return {
        "total_all_time_usd": round(totals["all_time"] or 0, 4),
        "total_30d_usd": round(totals["last_30d"] or 0, 4),
        "total_7d_usd": round(totals["last_7d"] or 0, 4),
        "total_24h_usd": round(totals["last_24h"] or 0, 4),
        "by_provider": provider_shape,
        "daily_trend": sorted(trend_by_date.values(), key=lambda x: x["date"]),
    }


# ── Classroom Usage ────────────────────────────────────────────────────────────

@router.get("/classroom")
def get_classroom_admin_stats(admin=Depends(_require_admin)):
    """
    Classroom feature usage — session counts, average length, and which
    subjects are actually being taught in live sessions.
    """
    conn = _get_conn()
    try:
        total_sessions = conn.execute(
            "SELECT COUNT(*) as c FROM classroom_sessions"
        ).fetchone()["c"]
        sessions_7d = conn.execute(
            "SELECT COUNT(*) as c FROM classroom_sessions WHERE started_at::timestamp >= (NOW() - INTERVAL '7 days')"
        ).fetchone()["c"]
        in_progress = conn.execute(
            "SELECT COUNT(*) as c FROM classroom_sessions WHERE ended_at IS NULL"
        ).fetchone()["c"]
        avg_exchanges_row = conn.execute(
            "SELECT AVG(exchange_count) as avg FROM classroom_sessions WHERE ended_at IS NOT NULL"
        ).fetchone()
        avg_exchanges = round(avg_exchanges_row["avg"], 1) if avg_exchanges_row["avg"] else None

        subject_rows = conn.execute(
            "SELECT subjects FROM classroom_sessions WHERE subjects IS NOT NULL AND subjects != '[]'"
        ).fetchall()
        recent = conn.execute("""
            SELECT cs.id, u.username, u.full_name, cs.started_at, cs.ended_at,
                   cs.exchange_count, cs.subjects
            FROM classroom_sessions cs
            JOIN users u ON u.id = cs.user_id
            ORDER BY cs.started_at DESC
            LIMIT 30
        """).fetchall()
    except Exception:
        conn.close()
        return {
            "total_sessions": 0, "sessions_7d": 0, "in_progress": 0,
            "avg_exchanges": None, "top_subjects": [], "recent_sessions": [],
            "note": "No classroom_sessions yet — restart the server so init_classroom_db() runs.",
        }
    conn.close()

    subject_counter = Counter()
    for r in subject_rows:
        try:
            for s in json.loads(r["subjects"]):
                subject_counter[s] += 1
        except Exception:
            continue

    recent_sessions = []
    for r in recent:
        try:
            subjects = json.loads(r["subjects"]) if r["subjects"] else []
        except Exception:
            subjects = []
        recent_sessions.append({
            "id": r["id"],
            "student": r["full_name"] or r["username"],
            "started_at": r["started_at"],
            "ended_at": r["ended_at"],
            "in_progress": r["ended_at"] is None,
            "exchange_count": r["exchange_count"],
            "subjects": subjects,
        })

    return {
        "total_sessions": total_sessions,
        "sessions_7d": sessions_7d,
        "in_progress": in_progress,
        "avg_exchanges": avg_exchanges,
        "top_subjects": [{"subject": s, "count": c} for s, c in subject_counter.most_common(10)],
        "recent_sessions": recent_sessions,
    }


# ── Subject Topics ──────────────────────────────────────────────────────────────
# Admin-managed topic lists shown to students inside a subject's chat, and used
# to scope rag.py's retrieval so answers stay tied to what's actually being
# studied. Cross-checked against curriculum.py so admins get a heads-up if
# they're adding a topic for a subject the curriculum index doesn't cover yet.

def init_topics_db():
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS subject_topics (
            id         BIGSERIAL PRIMARY KEY,
            subject    TEXT NOT NULL,
            topic      TEXT NOT NULL,
            created_at TEXT DEFAULT (now_iso()),
            UNIQUE(subject, topic)
        )
    """)
    conn.commit()
    conn.close()
    print("[NaijaSensei] Subject topics DB ready.")


def _known_curriculum_subjects() -> set:
    """Every subject name that actually has passages in the curriculum
    index (curriculum.py + the generated syllabus chunks rag.py also
    loads). Best-effort: if either import fails, just returns what it has."""
    subjects = set()
    try:
        from curriculum import CURRICULUM
        subjects.update(p["subject"] for p in CURRICULUM)
    except Exception as e:
        print(f"[admin] Could not load curriculum.py subjects: {e}")
    try:
        from data.generated_curriculum import GENERATED_CURRICULUM
        subjects.update(p["subject"] for p in GENERATED_CURRICULUM)
    except Exception as e:
        print(f"[admin] Could not load generated_curriculum subjects: {e}")
    return subjects


class TopicRequest(BaseModel):
    subject: str
    topic: str


@router.get("/topics")
def list_topics(subject: str | None = None, admin=Depends(_require_admin)):
    """List all admin-managed topics, optionally filtered to one subject."""
    conn = _get_conn()
    if subject:
        rows = conn.execute(
            "SELECT * FROM subject_topics WHERE subject = ? ORDER BY topic ASC", (subject,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM subject_topics ORDER BY subject ASC, topic ASC"
        ).fetchall()
    conn.close()
    return {"topics": [dict(r) for r in rows]}


@router.post("/topics")
def add_topic(req: TopicRequest, admin=Depends(_require_admin)):
    """
    Add a topic under a subject. If that subject has no passages in the
    curriculum index yet, this still succeeds but returns a `warning` —
    a nudge to add the subject to curriculum.py so RAG grounding for
    this topic actually has something to retrieve, not a hard block.
    """
    subject = req.subject.strip()
    topic = req.topic.strip()
    if not subject or not topic:
        raise HTTPException(400, "Subject and topic are both required.")

    conn = _get_conn()
    try:
        conn.execute(
            "INSERT INTO subject_topics (subject, topic) VALUES (?, ?)",
            (subject, topic)
        )
        conn.commit()
    except Exception:
        conn.close()
        raise HTTPException(400, "This subject/topic pair already exists.")
    conn.close()

    warning = None
    known_subjects = _known_curriculum_subjects()
    if known_subjects and subject not in known_subjects:
        warning = (
            f"Heads up: '{subject}' has no passages in the curriculum index yet "
            f"(curriculum.py). The topic was saved, but until '{subject}' is added "
            f"there, RAG answers for it won't be grounded in real curriculum content."
        )

    return {"message": "Topic added.", "subject": subject, "topic": topic, "warning": warning}


@router.delete("/topics/{topic_id}")
def delete_topic(topic_id: int, admin=Depends(_require_admin)):
    conn = _get_conn()
    conn.execute("DELETE FROM subject_topics WHERE id = ?", (topic_id,))
    conn.commit()
    conn.close()
    return {"message": "Topic deleted."}


@router.get("/topic-coverage")
def get_topic_coverage(admin=Depends(_require_admin)):
    """
    For every topic added via /admin/topics, checks whether the RAG corpus
    (curriculum.py + data/generated_curriculum.py, merged - same combined
    pool rag.py's search() draws from) has any passage whose own topic
    label reasonably matches it, using the identical fuzzy-match scoring
    search() uses at actual retrieval time.

    A "weak"/"none" result here doesn't mean the AI can't answer the
    topic at all - broad subject-level content and the AI's own knowledge
    still ground an answer. It means the topic-specific narrowing rag.py
    is designed to do won't actually surface anything targeted for that
    topic - the exact gap this endpoint exists to surface.
    """
    conn = _get_conn()
    admin_topics = conn.execute(
        "SELECT id, subject, topic FROM subject_topics ORDER BY subject, topic"
    ).fetchall()
    conn.close()

    from rag import _topic_match_score
    from curriculum import CURRICULUM
    from data.generated_curriculum import GENERATED_CURRICULUM
    all_passages = list(CURRICULUM) + list(GENERATED_CURRICULUM)

    results = []
    for row in admin_topics:
        subj, topic = row["subject"], row["topic"]
        subj_passages = [p for p in all_passages if p["subject"] == subj]
        best_score = 0.0
        best_match_topic = None
        for p in subj_passages:
            score = _topic_match_score(topic, p["topic"])
            if score > best_score:
                best_score = score
                best_match_topic = p["topic"]
        coverage = "strong" if best_score >= 0.85 else "weak" if best_score >= 0.4 else "none"
        results.append({
            "id": row["id"],
            "subject": subj,
            "topic": topic,
            "best_match_score": round(best_score, 2),
            "best_match_passage_topic": best_match_topic,
            "coverage": coverage,
            "subject_has_any_passages": len(subj_passages) > 0,
        })

    summary = {
        "strong": sum(1 for r in results if r["coverage"] == "strong"),
        "weak": sum(1 for r in results if r["coverage"] == "weak"),
        "none": sum(1 for r in results if r["coverage"] == "none"),
        "total": len(results),
    }
    return {"summary": summary, "topics": results}


@router.post("/topics/sync-from-curriculum")
def sync_topics_from_curriculum(admin=Depends(_require_admin)):
    """
    Bulk-adds every unique (subject, topic) pair already present in the
    curriculum corpus (curriculum.py + data/generated_curriculum.py)
    straight into subject_topics. Existing topics are left untouched
    (INSERT OR IGNORE against the UNIQUE(subject, topic) constraint), so
    this is safe to re-run any time the curriculum files change.

    Since a synced topic IS the curriculum's own topic label verbatim,
    every topic added this way is guaranteed a "strong" result on the
    /admin/topic-coverage check - this is the most reliable way to
    populate topics with zero fuzzy-match risk, as opposed to an admin
    hand-typing a topic name that might not closely match anything.
    """
    from curriculum import CURRICULUM
    from data.generated_curriculum import GENERATED_CURRICULUM
    all_passages = list(CURRICULUM) + list(GENERATED_CURRICULUM)

    unique_pairs = sorted({(p["subject"], p["topic"]) for p in all_passages})

    conn = _get_conn()
    added = 0
    for subject, topic in unique_pairs:
        cur = conn.execute(
            "INSERT INTO subject_topics (subject, topic) VALUES (?, ?) "
            "ON CONFLICT (subject, topic) DO NOTHING",
            (subject, topic)
        )
        if cur.rowcount > 0:
            added += 1
    conn.commit()
    conn.close()

    return {
        "message": f"Synced {added} new topic(s) from the curriculum corpus.",
        "added": added,
        "already_existed": len(unique_pairs) - added,
        "total_unique_topics_in_curriculum": len(unique_pairs),
    }