"""
dashboard.py — Teacher and Parent Dashboard for NaijaSensei.

Adds role-based access (student / teacher / parent) and class management
without modifying auth.py directly. Uses safe ALTER TABLE migrations so
existing user accounts are unaffected.

Teacher features:
  - Create a class (gets a unique invite code)
  - See all students in their class + their scores/weak areas
  - Monitor class-wide performance trends

Parent features:
  - Link to a student account using the student's share code
  - Read-only view of that student's scores, weak areas, and predictions
  - Export a progress report
"""

import os
import json
import random
import string
import base64
import hashlib
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from cryptography.fernet import Fernet, InvalidToken
from auth import require_user, require_student, _get_conn, get_activity_summary, SECRET_KEY, ALGORITHM

from predictor import pct_to_grade, grade_to_credit

from security import require_env_secret

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


# ── Credential encryption ──────────────────────────────────────────────────
# created_credentials.plain_password historically stored teacher/parent-
# created students' passwords in plain text so they could be shown back to
# the account creator (the whole point of "recoverable credentials"). That's
# a real risk if the DB is ever compromised - it becomes a plaintext
# password dump. This encrypts the value at rest instead; the column name
# is kept as-is for schema compatibility, but it now holds a Fernet token,
# not the raw password. Decryption still happens server-side on demand for
# the /teacher/logins and /parent/logins views, so the feature behaves the
# same from the outside - only what's sitting in the DB file changes.
_CRED_ENC_ENV = "CREDENTIALS_ENCRYPTION_KEY"
# Validated once at import time — this used to warn and silently fall back
# to the same hardcoded string as JWT_SECRET_KEY/ADMIN_PASSWORD, which
# would let anyone who's seen this codebase decrypt every stored student
# credential from a DB dump. See security.py's docstring.
_CRED_ENC_KEY = require_env_secret(_CRED_ENC_ENV, min_length=16)


def _get_fernet() -> Fernet:
    # Fernet requires a 32-byte url-safe base64 key. Deriving it from a
    # plain passphrase via SHA-256 means operators can set a normal secret
    # string in .env (matching the JWT_SECRET_KEY pattern) rather than
    # needing to separately pre-generate a raw Fernet key.
    derived = base64.urlsafe_b64encode(hashlib.sha256(_CRED_ENC_KEY.encode()).digest())
    return Fernet(derived)


def _encrypt_password(plain: str) -> str:
    return _get_fernet().encrypt(plain.encode()).decode()


def _decrypt_password(stored: str) -> str:
    """Best-effort decrypt. Falls back to returning the stored value
    unchanged if it isn't a valid Fernet token - covers the brief window
    right at migration time, or any row that somehow wasn't migrated,
    rather than crashing the /teacher/logins or /parent/logins views."""
    try:
        return _get_fernet().decrypt(stored.encode()).decode()
    except (InvalidToken, Exception):
        return stored


def _get_profile_map(conn, user_ids: list[int]) -> dict:
    """
    {user_id: {"department":..., "class_level":...}} — reads from
    student_profiles if that table exists (created by the profile setup
    flow). Returns {} silently if the table isn't there yet.
    """
    if not user_ids:
        return {}
    try:
        placeholders = ",".join("?" for _ in user_ids)
        rows = conn.execute(
            f"SELECT user_id, department, class_level FROM student_profiles "
            f"WHERE user_id IN ({placeholders})",
            user_ids
        ).fetchall()
        return {r["user_id"]: {"department": r["department"], "class_level": r["class_level"]} for r in rows}
    except Exception:
        return {}


def _predict_student_avg(conn, user_id: int):
    """
    Same weighted-average logic as predictor.py's /predict/prediction —
    most recent exam counts 2x, rest count 1x. Returns
    (avg_pct, grade, credit_likely, exams_taken) or (None, None, None, 0).
    """
    rows = conn.execute(
        """SELECT score, max_score FROM exam_sessions
           WHERE user_id = ? AND submitted_at IS NOT NULL
           ORDER BY started_at DESC LIMIT 10""",
        (user_id,)
    ).fetchall()
    scores = [
        round(r["score"] / r["max_score"] * 100, 1)
        for r in rows if r["score"] is not None and r["max_score"]
    ]
    if not scores:
        return None, None, None, 0
    weighted_sum = sum(s * (2 if i == 0 else 1) for i, s in enumerate(scores))
    weight_total = sum(2 if i == 0 else 1 for i in range(len(scores)))
    avg_pct = round(weighted_sum / weight_total, 1)
    grade = pct_to_grade(avg_pct)
    credit = grade_to_credit(grade)
    return avg_pct, grade, credit, len(scores)


def _get_subject_averages(conn, user_id: int) -> dict:
    """
    {subject: avg_percentage} across this student's submitted exams.
    Mirrors the subject_avgs logic used in get_student_progress, extracted
    here so both the teacher overview and parent progress views can share it.
    """
    exams = conn.execute(
        """SELECT subjects, score, max_score FROM exam_sessions
           WHERE user_id = ? AND submitted_at IS NOT NULL
           ORDER BY started_at DESC LIMIT 20""",
        (user_id,)
    ).fetchall()

    subject_scores: dict[str, list] = {}
    for e in exams:
        try:
            if not e["score"] or not e["max_score"]:
                continue
            pct = round(e["score"] / e["max_score"] * 100, 1)
            subjects = json.loads(e["subjects"])
            for subj in subjects:
                subject_scores.setdefault(subj, []).append(pct)
        except Exception:
            continue

    return {s: round(sum(scs) / len(scs), 1) for s, scs in subject_scores.items()}


# ── DB setup (safe migrations — won't break existing data) ────────────────────

def init_dashboard_db():
    conn = _get_conn()

    # Add role column to users table (student / teacher / parent)
    conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'student'")

    # Recoverable credentials for accounts created ON BEHALF of a student
    # (by a teacher or parent). Kept separate from hashed_pw — this is the
    # only place a plaintext password is stored, and only for these accounts.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS created_credentials (
            id              BIGSERIAL PRIMARY KEY,
            user_id         INTEGER NOT NULL UNIQUE,
            plain_password  TEXT NOT NULL,
            created_by_id   INTEGER NOT NULL,
            created_by_role TEXT NOT NULL,
            created_at      TEXT DEFAULT (now_iso())
        )
    """)

    # One-time migration: encrypt any pre-existing plaintext rows in
    # created_credentials in place. Safe to run on every startup - rows that
    # already decrypt cleanly (already migrated) are left untouched.
    try:
        rows = conn.execute("SELECT id, plain_password FROM created_credentials").fetchall()
        migrated = 0
        for row in rows:
            stored = row["plain_password"]
            try:
                _get_fernet().decrypt(stored.encode())
                continue  # already a valid Fernet token - already migrated
            except Exception:
                pass
            conn.execute(
                "UPDATE created_credentials SET plain_password = ? WHERE id = ?",
                (_encrypt_password(stored), row["id"])
            )
            migrated += 1
        if migrated:
            print(f"[dashboard] Encrypted {migrated} previously-plaintext stored credential(s).")
    except Exception as e:
        print(f"[dashboard] Credential encryption migration skipped (non-fatal): {e}")

    # Add share_code column — students get a unique code parents can use to link
    conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS share_code TEXT")

    # Generate share codes for existing students who don't have one
    rows = conn.execute(
        "SELECT id FROM users WHERE share_code IS NULL OR share_code = ''"
    ).fetchall()
    for row in rows:
        code = "NS" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        conn.execute("UPDATE users SET share_code = ? WHERE id = ?", (code, row["id"]))

    # Classes table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS classes (
            id          BIGSERIAL PRIMARY KEY,
            teacher_id  INTEGER NOT NULL,
            name        TEXT NOT NULL,
            invite_code TEXT NOT NULL UNIQUE,
            created_at  TEXT DEFAULT (now_iso())
        )
    """)

    # Class membership
    conn.execute("""
        CREATE TABLE IF NOT EXISTS class_members (
            id         BIGSERIAL PRIMARY KEY,
            class_id   INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            joined_at  TEXT DEFAULT (now_iso()),
            UNIQUE(class_id, student_id)
        )
    """)

    # Parent-student links. status default 'approved' so this ALTER is safe
    # for existing rows (already-linked parents keep working unchanged) -
    # new link requests explicitly insert status='pending' instead, so a
    # parent's access only becomes real once the student approves it.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS parent_links (
            id         BIGSERIAL PRIMARY KEY,
            parent_id  INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            linked_at  TEXT DEFAULT (now_iso()),
            UNIQUE(parent_id, student_id)
        )
    """)
    conn.execute("ALTER TABLE parent_links ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'approved'")

    conn.commit()
    conn.close()


# ── Register with role (extends auth.py's register to include role) ───────────

class RegisterWithRoleRequest(BaseModel):
    username: str
    email: str
    full_name: str | None = None
    password: str
    role: str = "student"   # "student", "teacher", or "parent"


@router.post("/register-with-role")
def register_with_role(body: RegisterWithRoleRequest):
    """
    Extended registration that saves the user's role (student/teacher/parent)
    at sign-up time. Works alongside auth.py's existing /auth/register endpoint.
    Returns same token format so frontend can use it directly.
    """
    from passlib.context import CryptContext
    from jose import jwt
    from datetime import datetime, timedelta

    if body.role not in ("student", "teacher", "parent"):
        raise HTTPException(400, "Role must be student, teacher, or parent.")

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    conn = _get_conn()
    existing = conn.execute(
        "SELECT id FROM users WHERE username = ? OR email = ?",
        (body.username, body.email)
    ).fetchone()
    if existing:
        conn.close()
        raise HTTPException(400, "Username or email already taken.")

    hashed = pwd_context.hash(body.password)
    cursor = conn.execute(
        "INSERT INTO users (username, email, full_name, role, hashed_pw) VALUES (?, ?, ?, ?, ?) RETURNING id",
        (body.username, body.email, body.full_name, body.role, hashed)
    )
    student_id = cursor.lastrowid

    # Give every user a share code (useful for students linking with parents)
    code = "NS" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    conn.execute("UPDATE users SET share_code = ? WHERE id = ?", (code, student_id))
    conn.commit()

    row = conn.execute("SELECT * FROM users WHERE id = ?", (student_id,)).fetchone()
    conn.close()
    user = dict(row)

    expire = datetime.utcnow() + timedelta(hours=24)
    token = jwt.encode({"sub": user["username"], "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer", "user": user}


# ── Role management ───────────────────────────────────────────────────────────

class SetRoleRequest(BaseModel):
    role: str  # "student", "teacher", or "parent"


@router.post("/set-role")
def set_role(req: SetRoleRequest, current_user: dict = Depends(require_user)):
    """Let a user change their own role (teacher or parent)."""
    if req.role not in ("student", "teacher", "parent"):
        raise HTTPException(400, "Role must be student, teacher, or parent.")
    conn = _get_conn()
    conn.execute("UPDATE users SET role = ? WHERE id = ?", (req.role, current_user["id"]))
    conn.commit()
    conn.close()
    return {"role": req.role}


@router.get("/me")
def get_my_role(current_user: dict = Depends(require_user)):
    """Return current user's role and share code."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT role, share_code FROM users WHERE id = ?", (current_user["id"],)
    ).fetchone()
    conn.close()
    return {
        "role": row["role"] if row and row["role"] else "student",
        "share_code": row["share_code"] if row else None,
        "username": current_user.get("username"),
        "full_name": current_user.get("full_name"),
    }


# ── Teacher: Class Management ─────────────────────────────────────────────────

class CreateClassRequest(BaseModel):
    name: str


def _require_teacher(current_user: dict = Depends(require_user)):
    conn = _get_conn()
    row = conn.execute("SELECT role FROM users WHERE id = ?", (current_user["id"],)).fetchone()
    conn.close()
    if not row or row["role"] != "teacher":
        raise HTTPException(403, "Only teachers can access this.")
    return current_user


@router.post("/teacher/class")
def create_class(req: CreateClassRequest,
                  current_user: dict = Depends(_require_teacher)):
    """Create a new class and get an invite code students can use to join."""
    if not req.name.strip():
        raise HTTPException(400, "Class name cannot be empty.")
    invite_code = "CLS" + "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
    conn = _get_conn()
    conn.execute(
        "INSERT INTO classes (teacher_id, name, invite_code) VALUES (?, ?, ?)",
        (current_user["id"], req.name.strip(), invite_code)
    )
    conn.commit()
    conn.close()
    return {"name": req.name, "invite_code": invite_code}
class AssignClassRequest(BaseModel):
    student_id: int
    class_id: int | None = None  # None = unassign


@router.post("/teacher/assign-class")
def assign_student_to_class(req: AssignClassRequest,
                              current_user: dict = Depends(_require_teacher)):
    """Assign or move a student to one of this teacher's classes."""
    conn = _get_conn()

    student = conn.execute(
        "SELECT id, role FROM users WHERE id = ?", (req.student_id,)
    ).fetchone()
    if not student:
        conn.close()
        raise HTTPException(404, "Student not found.")
    if (student["role"] or "student") != "student":
        conn.close()
        raise HTTPException(400, "Can only assign student accounts to a class.")

    if req.class_id:
        cls = conn.execute(
            "SELECT id FROM classes WHERE id = ? AND teacher_id = ?",
            (req.class_id, current_user["id"])
        ).fetchone()
        if not cls:
            conn.close()
            raise HTTPException(404, "Class not found.")

    teacher_class_ids = [r["id"] for r in conn.execute(
        "SELECT id FROM classes WHERE teacher_id = ?", (current_user["id"],)
    ).fetchall()]
    if teacher_class_ids:
        placeholders = ",".join("?" for _ in teacher_class_ids)
        conn.execute(
            f"DELETE FROM class_members WHERE student_id = ? AND class_id IN ({placeholders})",
            [req.student_id] + teacher_class_ids
        )

    if req.class_id:
        conn.execute(
            "INSERT INTO class_members (class_id, student_id) VALUES (?, ?)",
            (req.class_id, req.student_id)
        )

    conn.commit()
    conn.close()
    return {"message": "Class assignment updated."}

@router.get("/teacher/classes")
def get_my_classes(current_user: dict = Depends(_require_teacher)):
    """List all classes this teacher has created."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT id, name, invite_code, created_at FROM classes WHERE teacher_id = ?",
        (current_user["id"],)
    ).fetchall()
    conn.close()
    return {"classes": [dict(r) for r in rows]}


class CreateStudentRequest(BaseModel):
    username: str
    full_name: str
    password: str
    class_id: int | None = None   # optionally auto-add to one of teacher's classes
    department: str | None = None       # "science", "arts", or "commercial" (optional)
    class_level: str | None = "SS2"     # "SS1", "SS2", "SS3"
    subjects: list[str] | None = None   # 7-9 subjects, required if department is set


def _save_student_profile(conn, user_id: int, department: str | None,
                           class_level: str | None, subjects: list[str] | None):
    """
    Shared helper: saves a department/class_level/subject combination for a
    student created by a teacher or parent. No-op if department wasn't set
    (account creator skipped the subject picker).
    """
    if not department:
        return
    if not subjects or len(subjects) < 7 or len(subjects) > 9:
        raise HTTPException(400, "Select between 7 and 9 subjects for the student.")
    conn.execute("""
        INSERT INTO student_profiles (user_id, department, class_level, subjects, target_score, waec_year)
        VALUES (?, ?, ?, ?, 70, NULL)
        ON CONFLICT(user_id) DO UPDATE SET
            department=excluded.department,
            class_level=excluded.class_level,
            subjects=excluded.subjects,
            updated_at=now_iso()
    """, (user_id, department, class_level or "SS2", json.dumps(subjects)))


@router.post("/teacher/create-student")
def teacher_create_student(req: CreateStudentRequest,
                             current_user: dict = Depends(_require_teacher)):
    """
    Teacher creates a student account directly — no self-registration needed.
    Optionally adds the student to one of the teacher's classes immediately.
    """
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    if not req.username.strip() or not req.password.strip():
        raise HTTPException(400, "Username and password are required.")

    conn = _get_conn()
    try:
        # Check username not already taken
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ?", (req.username.strip(),)
        ).fetchone()
        if existing:
            raise HTTPException(400, f"Username '{req.username}' is already taken. Choose a different one.")

        # Validate BEFORE writing anything, so a bad subjects list can't leave
        # a half-finished, uncommitted transaction open on the connection.
        if req.department and (not req.subjects or not (7 <= len(req.subjects) <= 9)):
            raise HTTPException(400, "Select between 7 and 9 subjects for the student.")

        hashed = pwd_context.hash(req.password)
        # Use a placeholder email since teacher-created accounts don't need one
        placeholder_email = f"{req.username.strip().lower()}@teacher.naijasensei.local"
        cursor = conn.execute(
            "INSERT INTO users (username, email, full_name, role, hashed_pw) VALUES (?, ?, ?, 'student', ?) RETURNING id",
            (req.username.strip(), placeholder_email, req.full_name.strip(), hashed)
        )
        student_id = cursor.lastrowid

        # Generate share code for the new student
        import random, string
        code = "NS" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        conn.execute("UPDATE users SET share_code = ? WHERE id = ?", (code, student_id))

        # Save the (encrypted) password so the teacher can retrieve it later
        conn.execute(
            """INSERT INTO created_credentials
               (user_id, plain_password, created_by_id, created_by_role)
               VALUES (?, ?, ?, 'teacher')
               ON CONFLICT (user_id) DO UPDATE SET
                   plain_password = EXCLUDED.plain_password,
                   created_by_id = EXCLUDED.created_by_id,
                   created_by_role = EXCLUDED.created_by_role""",
            (student_id, _encrypt_password(req.password), current_user["id"])
        )

        # Optionally save the department/subject combination the teacher picked
        _save_student_profile(conn, student_id, req.department, req.class_level, req.subjects)

        # Optionally add to class
        if req.class_id:
            cls = conn.execute(
                "SELECT id FROM classes WHERE id = ? AND teacher_id = ?",
                (req.class_id, current_user["id"])
            ).fetchone()
            if cls:
                try:
                    conn.execute(
                        "INSERT INTO class_members (class_id, student_id) VALUES (?, ?)",
                        (req.class_id, student_id)
                    )
                except Exception:
                    pass

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return {
        "message": f"Student account created for {req.full_name}.",
        "username": req.username,
        "student_id": student_id,
        "share_code": code,
    }


@router.get("/teacher/overview")
def teacher_overview(current_user: dict = Depends(_require_teacher)):
    """All students grouped by class, with per-subject performance."""
    conn = _get_conn()
    classes = conn.execute(
        "SELECT id, name FROM classes WHERE teacher_id = ?",
        (current_user["id"],)
    ).fetchall()
    class_map = {c["id"]: c["name"] for c in classes}

    members = []
    if class_map:
        class_ids = list(class_map.keys())
        placeholders = ",".join("?" for _ in class_ids)
        members = conn.execute(
            f"""SELECT cm.class_id, u.id, u.username, u.full_name
                FROM class_members cm
                JOIN users u ON u.id = cm.student_id
                WHERE cm.class_id IN ({placeholders})""",
            class_ids
        ).fetchall()

    unassigned = conn.execute(
        """SELECT u.id, u.username, u.full_name
           FROM created_credentials cc
           JOIN users u ON u.id = cc.user_id
           WHERE cc.created_by_id = ? AND cc.created_by_role = 'teacher'
             AND u.id NOT IN (SELECT student_id FROM class_members)""",
        (current_user["id"],)
    ).fetchall()

    all_rows = [dict(m) for m in members] + [
        {"class_id": None, "id": r["id"], "username": r["username"], "full_name": r["full_name"]}
        for r in unassigned
    ]

    students = []
    for m in all_rows:
        avg_pct, grade, credit, exams_taken = _predict_student_avg(conn, m["id"])
        students.append({
            "id": m["id"],
            "username": m["username"],
            "full_name": m["full_name"],
            "class_id": m["class_id"],
            "class_name": class_map.get(m["class_id"], "Unassigned"),
            "predicted_avg": avg_pct,
            "predicted_grade": grade,
            "credit_likely": credit,
            "exams_taken": exams_taken,
            "subject_averages": _get_subject_averages(conn, m["id"]),
        })

    conn.close()
    return {"students": students, "classes": [{"id": cid, "name": n} for cid, n in class_map.items()]}
def _teacher_owns_student(conn, teacher_id: int, student_id: int) -> bool:
    row = conn.execute(
        """SELECT 1 FROM created_credentials WHERE user_id=? AND created_by_id=? AND created_by_role='teacher'
           UNION
           SELECT 1 FROM class_members cm JOIN classes c ON c.id=cm.class_id
           WHERE cm.student_id=? AND c.teacher_id=?""",
        (student_id, teacher_id, student_id, teacher_id)
    ).fetchone()
    return row is not None


def _parent_owns_student(conn, parent_id: int, student_id: int) -> bool:
    """True only for an APPROVED link. A pending link (student hasn't
    approved yet) must grant zero access - this is the enforcement point
    for that, since every parent-facing endpoint in this file gates through
    this check before touching a student's data."""
    row = conn.execute(
        "SELECT 1 FROM parent_links WHERE parent_id=? AND student_id=? AND status='approved'",
        (parent_id, student_id)
    ).fetchone()
    return row is not None


INACTIVE_ALERT_DAYS = 7

def _get_last_active(conn, user_id: int):
    """Most recent activity of ANY kind — chat, exam, or classroom session.
    Returns an ISO timestamp string, or None if the account has never been
    used at all."""
    dates = []
    row = conn.execute("SELECT last_active FROM user_activity WHERE user_id=?", (user_id,)).fetchone()
    if row and row["last_active"]:
        dates.append(row["last_active"])
    row = conn.execute("SELECT MAX(started_at) as m FROM exam_sessions WHERE user_id=?", (user_id,)).fetchone()
    if row and row["m"]:
        dates.append(row["m"])
    try:
        row = conn.execute("SELECT MAX(started_at) as m FROM classroom_sessions WHERE user_id=?", (user_id,)).fetchone()
        if row and row["m"]:
            dates.append(row["m"])
    except Exception:
        pass  # classroom_sessions may not exist yet on a fresh install
    return max(dates) if dates else None


def _is_inactive(last_active) -> bool:
    """True only if there IS a last-active date and it's stale — a brand
    new account with no activity yet is not 'gone quiet', it just hasn't
    started, so that case does not get flagged."""
    if not last_active:
        return False
    try:
        last_dt = datetime.fromisoformat(last_active)
    except Exception:
        return False
    return (datetime.utcnow() - last_dt) > timedelta(days=INACTIVE_ALERT_DAYS)


def _delete_student_fully(conn, student_id: int):
    """Removes a student and every row tied to them across all tables."""
    conn.execute("DELETE FROM class_members WHERE student_id=?", (student_id,))
    conn.execute("DELETE FROM parent_links WHERE student_id=?", (student_id,))
    conn.execute("DELETE FROM created_credentials WHERE user_id=?", (student_id,))
    conn.execute("DELETE FROM chat_history WHERE user_id=?", (student_id,))
    conn.execute("DELETE FROM user_activity WHERE user_id=?", (student_id,))
    conn.execute("DELETE FROM activity_minutes WHERE user_id=?", (student_id,))
    try:
        conn.execute("DELETE FROM exam_sessions WHERE user_id=?", (student_id,))
    except Exception:
        pass
    try:
        conn.execute("DELETE FROM student_profiles WHERE user_id=?", (student_id,))
    except Exception:
        pass
    conn.execute("DELETE FROM users WHERE id=?", (student_id,))


class StudentActionRequest(BaseModel):
    student_id: int


@router.get("/teacher/logins")
def teacher_logins(current_user: dict = Depends(_require_teacher)):
    """Username + recoverable password + activity for every student this teacher created."""
    conn = _get_conn()
    rows = conn.execute(
        """SELECT u.id, u.username, u.full_name, u.is_suspended, cc.plain_password
           FROM created_credentials cc
           JOIN users u ON u.id = cc.user_id
           WHERE cc.created_by_id = ? AND cc.created_by_role = 'teacher'""",
        (current_user["id"],)
    ).fetchall()
    conn.close()
    students = []
    for r in rows:
        d = dict(r)
        d["plain_password"] = _decrypt_password(d["plain_password"])
        d.update(get_activity_summary(d["id"]))
        students.append(d)
    return {"students": students}


@router.post("/teacher/suspend-student")
def teacher_suspend_student(req: StudentActionRequest, current_user: dict = Depends(_require_teacher)):
    conn = _get_conn()
    if not _teacher_owns_student(conn, current_user["id"], req.student_id):
        conn.close()
        raise HTTPException(403, "This student is not linked to you.")
    conn.execute("UPDATE users SET is_suspended=1 WHERE id=?", (req.student_id,))
    conn.commit()
    conn.close()
    return {"message": "Student account suspended."}


@router.post("/teacher/unsuspend-student")
def teacher_unsuspend_student(req: StudentActionRequest, current_user: dict = Depends(_require_teacher)):
    conn = _get_conn()
    if not _teacher_owns_student(conn, current_user["id"], req.student_id):
        conn.close()
        raise HTTPException(403, "This student is not linked to you.")
    conn.execute("UPDATE users SET is_suspended=0 WHERE id=?", (req.student_id,))
    conn.commit()
    conn.close()
    return {"message": "Student account reactivated."}


@router.delete("/teacher/student/{student_id}")
def teacher_delete_student(student_id: int, current_user: dict = Depends(_require_teacher)):
    conn = _get_conn()
    if not _teacher_owns_student(conn, current_user["id"], student_id):
        conn.close()
        raise HTTPException(403, "This student is not linked to you.")
    _delete_student_fully(conn, student_id)
    conn.commit()
    conn.close()
    return {"message": "Student account deleted permanently."}


# ── Teacher: Class Insights (weak topics + classroom activity) ────────────────

@router.get("/teacher/class/{class_id}/weak-topics")
def get_class_weak_topics(class_id: int, current_user: dict = Depends(_require_teacher)):
    """
    Aggregate weak topics across every student in one of this teacher's
    classes — same topic-extraction logic as analytics.py's per-student
    breakdown (questions/answers JSON on exam_sessions), just summed across
    the whole class so a teacher can see what to re-teach without opening
    each student individually.
    """
    conn = _get_conn()
    cls = conn.execute(
        "SELECT id, name FROM classes WHERE id = ? AND teacher_id = ?",
        (class_id, current_user["id"])
    ).fetchone()
    if not cls:
        conn.close()
        raise HTTPException(404, "Class not found.")

    student_ids = [r["student_id"] for r in conn.execute(
        "SELECT student_id FROM class_members WHERE class_id = ?", (class_id,)
    ).fetchall()]

    if not student_ids:
        conn.close()
        return {"class_name": cls["name"], "has_data": False, "subjects": [],
                "message": "No students in this class yet."}

    placeholders = ",".join("?" for _ in student_ids)
    rows = conn.execute(
        f"""SELECT questions, answers FROM exam_sessions
            WHERE user_id IN ({placeholders}) AND submitted_at IS NOT NULL""",
        student_ids
    ).fetchall()
    conn.close()

    subject_topic_wrong: dict[str, dict[str, int]] = {}
    for row in rows:
        try:
            questions = json.loads(row["questions"])
            answers = json.loads(row["answers"]) if row["answers"] else {}
        except Exception:
            continue
        for q in questions.get("mcq", []):
            subj = q.get("subject", "Unknown")
            topic = q.get("topic", "Unknown")
            student_ans = answers.get(q["id"], "").strip().upper()
            correct_ans = q.get("answer", "").strip().upper()
            if student_ans != correct_ans:
                subject_topic_wrong.setdefault(subj, {})
                subject_topic_wrong[subj][topic] = subject_topic_wrong[subj].get(topic, 0) + 1

    subjects = []
    for subj, topics in subject_topic_wrong.items():
        top_wrong = sorted(topics.items(), key=lambda x: x[1], reverse=True)[:5]
        subjects.append({
            "subject": subj,
            "weak_topics": [{"topic": t, "wrong_count": c} for t, c in top_wrong],
        })
    subjects.sort(key=lambda s: sum(t["wrong_count"] for t in s["weak_topics"]), reverse=True)

    return {"class_name": cls["name"], "has_data": bool(subjects), "subjects": subjects}


@router.get("/teacher/classroom-activity")
def get_teacher_classroom_activity(current_user: dict = Depends(_require_teacher)):
    """
    Recent AI Classroom sessions across every student this teacher owns
    (class members + directly-created students) — the teacher-scoped
    equivalent of admin.py's /admin/classroom, so a teacher can see who's
    actually using the classroom without needing admin access.
    """
    conn = _get_conn()

    class_ids = [r["id"] for r in conn.execute(
        "SELECT id FROM classes WHERE teacher_id = ?", (current_user["id"],)
    ).fetchall()]

    student_ids = set()
    if class_ids:
        placeholders = ",".join("?" for _ in class_ids)
        for r in conn.execute(
            f"SELECT student_id FROM class_members WHERE class_id IN ({placeholders})", class_ids
        ).fetchall():
            student_ids.add(r["student_id"])
    for r in conn.execute(
        "SELECT user_id FROM created_credentials WHERE created_by_id = ? AND created_by_role = 'teacher'",
        (current_user["id"],)
    ).fetchall():
        student_ids.add(r["user_id"])

    if not student_ids:
        conn.close()
        return {"sessions": [], "message": "No students yet."}

    try:
        placeholders = ",".join("?" for _ in student_ids)
        rows = conn.execute(
            f"""SELECT cs.id, u.username, u.full_name, cs.started_at, cs.ended_at,
                       cs.exchange_count, cs.subjects
                FROM classroom_sessions cs
                JOIN users u ON u.id = cs.user_id
                WHERE cs.user_id IN ({placeholders})
                ORDER BY cs.started_at DESC LIMIT 30""",
            list(student_ids)
        ).fetchall()
    except Exception:
        conn.close()
        return {"sessions": [], "note": "No classroom sessions yet — restart the server so init_classroom_db() runs."}
    conn.close()

    sessions = []
    for r in rows:
        try:
            subjects = json.loads(r["subjects"]) if r["subjects"] else []
        except Exception:
            subjects = []
        sessions.append({
            "id": r["id"],
            "student": r["full_name"] or r["username"],
            "started_at": r["started_at"],
            "ended_at": r["ended_at"],
            "in_progress": r["ended_at"] is None,
            "exchange_count": r["exchange_count"],
            "subjects": subjects,
        })
    return {"sessions": sessions}


class ResetPasswordRequest(BaseModel):
    student_id: int
    new_password: str | None = None  # omit to auto-generate one


@router.post("/teacher/reset-password")
def teacher_reset_password(req: ResetPasswordRequest, current_user: dict = Depends(_require_teacher)):
    """
    Reset a student's password. Works for any student this teacher owns
    (directly created, or a class member who self-registered) — same
    ownership check as suspend/delete. Recorded in created_credentials so
    it shows up (or starts showing up) in /teacher/logins going forward.
    Note: if this student was originally created by a *parent* and later
    joined this teacher's class, resetting here will reassign that
    recoverable-password record to the teacher and it will stop appearing
    in the parent's /parent/logins list.
    """
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    conn = _get_conn()
    if not _teacher_owns_student(conn, current_user["id"], req.student_id):
        conn.close()
        raise HTTPException(403, "This student is not linked to you.")

    new_password = (req.new_password or "").strip()
    if not new_password:
        new_password = "".join(random.choices(string.ascii_letters + string.digits, k=10))
    elif len(new_password) < 6:
        conn.close()
        raise HTTPException(400, "Password must be at least 6 characters.")

    hashed = pwd_context.hash(new_password)
    conn.execute("UPDATE users SET hashed_pw = ? WHERE id = ?", (hashed, req.student_id))
    conn.execute(
        """INSERT INTO created_credentials
           (user_id, plain_password, created_by_id, created_by_role)
           VALUES (?, ?, ?, 'teacher')
           ON CONFLICT (user_id) DO UPDATE SET
               plain_password = EXCLUDED.plain_password,
               created_by_id = EXCLUDED.created_by_id,
               created_by_role = EXCLUDED.created_by_role""",
        (req.student_id, _encrypt_password(new_password), current_user["id"])
    )
    conn.commit()
    conn.close()
    return {"message": "Password reset.", "new_password": new_password}


# ── Student: Join a class ─────────────────────────────────────────────────────

class JoinClassRequest(BaseModel):
    invite_code: str


@router.post("/student/join-class")
def join_class(req: JoinClassRequest,
                current_user: dict = Depends(require_user)):
    """Student joins a class using the teacher's invite code."""
    conn = _get_conn()
    cls = conn.execute(
        "SELECT id, name FROM classes WHERE invite_code = ?",
        (req.invite_code.strip().upper(),)
    ).fetchone()
    if not cls:
        conn.close()
        raise HTTPException(404, "Invalid invite code. Ask your teacher to check it.")
    try:
        conn.execute(
            "INSERT INTO class_members (class_id, student_id) VALUES (?, ?)",
            (cls["id"], current_user["id"])
        )
        conn.commit()
    except Exception:
        pass  # already a member
    conn.close()
    return {"message": f"You joined {cls['name']} successfully!"}


# ── Parent: Link to student ───────────────────────────────────────────────────

class LinkStudentRequest(BaseModel):
    share_code: str


def _require_parent(current_user: dict = Depends(require_user)):
    conn = _get_conn()
    row = conn.execute("SELECT role FROM users WHERE id = ?", (current_user["id"],)).fetchone()
    conn.close()
    if not row or row["role"] != "parent":
        raise HTTPException(403, "Only parents can access this.")
    return current_user


@router.post("/parent/link-student")
def link_student(req: LinkStudentRequest,
                  current_user: dict = Depends(_require_parent)):
    """Parent requests a link to a student using the student's share code.
    This no longer grants access immediately - it creates a PENDING request
    that the student must approve (see /student/pending-parent-requests and
    /student/respond-parent-link below) before the parent can see any of
    their data. Previously this was instant and one-sided: anyone who had
    or guessed a share code got standing access with no visibility or
    consent from the student at all."""
    conn = _get_conn()
    student = conn.execute(
        "SELECT id, full_name, username FROM users WHERE share_code = ?",
        (req.share_code.strip().upper(),)
    ).fetchone()
    if not student:
        conn.close()
        raise HTTPException(404, "Invalid share code. Ask your child to share their code from Settings.")

    existing = conn.execute(
        "SELECT status FROM parent_links WHERE parent_id=? AND student_id=?",
        (current_user["id"], student["id"])
    ).fetchone()

    if existing and existing["status"] == "approved":
        conn.close()
        return {
            "message": f"You're already linked to {student['full_name'] or student['username']}.",
            "student_name": student["full_name"] or student["username"],
            "student_id": student["id"],
            "status": "approved",
        }
    elif existing and existing["status"] == "pending":
        conn.close()
        return {
            "message": f"A link request to {student['full_name'] or student['username']} is "
                       f"already pending their approval.",
            "student_name": student["full_name"] or student["username"],
            "student_id": student["id"],
            "status": "pending",
        }
    else:
        conn.execute(
            "INSERT INTO parent_links (parent_id, student_id, status) VALUES (?, ?, 'pending')",
            (current_user["id"], student["id"])
        )
        conn.commit()
    conn.close()
    return {
        "message": f"Link request sent to {student['full_name'] or student['username']}. "
                   f"They'll need to approve it before you can see their progress.",
        "student_name": student["full_name"] or student["username"],
        "student_id": student["id"],
        "status": "pending",
    }


class CreateChildRequest(BaseModel):
    username: str
    full_name: str
    password: str
    department: str | None = None       # "science", "arts", or "commercial" (optional)
    class_level: str | None = "SS2"     # "SS1", "SS2", "SS3"
    subjects: list[str] | None = None   # 7-9 subjects, required if department is set


@router.post("/parent/create-child")
def parent_create_child(req: CreateChildRequest,
                         current_user: dict = Depends(_require_parent)):
    """
    Parent creates a child's student account directly — no self-registration needed.
    The child is automatically linked to this parent account.
    """
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    if not req.username.strip() or not req.password.strip():
        raise HTTPException(400, "Username and password are required.")

    conn = _get_conn()
    try:
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ?", (req.username.strip(),)
        ).fetchone()
        if existing:
            raise HTTPException(400, f"Username '{req.username}' is already taken.")

        # Validate BEFORE writing anything, so a bad subjects list can't leave
        # a half-finished, uncommitted transaction open on the connection.
        if req.department and (not req.subjects or not (7 <= len(req.subjects) <= 9)):
            raise HTTPException(400, "Select between 7 and 9 subjects for the student.")

        hashed = pwd_context.hash(req.password)
        placeholder_email = f"{req.username.strip().lower()}@parent.naijasensei.local"
        cursor = conn.execute(
            "INSERT INTO users (username, email, full_name, role, hashed_pw) VALUES (?, ?, ?, 'student', ?) RETURNING id",
            (req.username.strip(), placeholder_email, req.full_name.strip(), hashed)
        )
        child_id = cursor.lastrowid

        import random, string
        code = "NS" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        conn.execute("UPDATE users SET share_code = ? WHERE id = ?", (code, child_id))

        # Save the (encrypted) password so the parent can retrieve it later
        conn.execute(
            """INSERT INTO created_credentials
               (user_id, plain_password, created_by_id, created_by_role)
               VALUES (?, ?, ?, 'parent')
               ON CONFLICT (user_id) DO UPDATE SET
                   plain_password = EXCLUDED.plain_password,
                   created_by_id = EXCLUDED.created_by_id,
                   created_by_role = EXCLUDED.created_by_role""",
            (child_id, _encrypt_password(req.password), current_user["id"])
        )

        # Optionally save the department/subject combination the parent picked
        _save_student_profile(conn, child_id, req.department, req.class_level, req.subjects)

        # Auto-link to this parent
        try:
            conn.execute(
                "INSERT INTO parent_links (parent_id, student_id) VALUES (?, ?)",
                (current_user["id"], child_id)
            )
        except Exception:
            pass

        conn.commit()
        return {
            "message": f"Account created for {req.full_name}. They can now log in with username '{req.username}'.",
            "username": req.username,
            "child_id": child_id,
            "share_code": code,
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@router.get("/parent/students")
def get_linked_students(current_user: dict = Depends(_require_parent)):
    """Get all APPROVED students linked to this parent account. Pending
    (not-yet-approved) requests are intentionally excluded here - see
    /parent/pending-requests for those - so a parent can't mistake a
    pending request for actual access."""
    conn = _get_conn()
    rows = conn.execute(
        """SELECT u.id, u.full_name, u.username
           FROM parent_links pl
           JOIN users u ON u.id = pl.student_id
           WHERE pl.parent_id = ? AND pl.status = 'approved'""",
        (current_user["id"],)
    ).fetchall()
    students = []
    for r in rows:
        d = dict(r)
        last_active = _get_last_active(conn, d["id"])
        d["last_active"] = last_active
        d["inactive_alert"] = _is_inactive(last_active)
        students.append(d)
    conn.close()
    return {"students": students}


@router.get("/parent/pending-requests")
def get_parent_pending_requests(current_user: dict = Depends(_require_parent)):
    """Link requests this parent has sent that the student hasn't
    approved or denied yet."""
    conn = _get_conn()
    rows = conn.execute(
        """SELECT u.id, u.full_name, u.username, pl.linked_at
           FROM parent_links pl
           JOIN users u ON u.id = pl.student_id
           WHERE pl.parent_id = ? AND pl.status = 'pending'""",
        (current_user["id"],)
    ).fetchall()
    conn.close()
    return {"pending_requests": [dict(r) for r in rows]}


class UnlinkStudentRequest(BaseModel):
    student_id: int


@router.post("/parent/unlink-student")
def parent_unlink_student(req: UnlinkStudentRequest,
                           current_user: dict = Depends(_require_parent)):
    """Parent-side self-service removal of a link (approved or still-pending) -
    no student approval needed to walk away from a link, only to create one."""
    conn = _get_conn()
    conn.execute(
        "DELETE FROM parent_links WHERE parent_id = ? AND student_id = ?",
        (current_user["id"], req.student_id)
    )
    conn.commit()
    conn.close()
    return {"message": "Link removed."}


class RespondParentLinkRequest(BaseModel):
    parent_id: int
    approve: bool


@router.get("/student/pending-parent-requests")
def get_student_pending_requests(current_user: dict = Depends(require_student)):
    """Parent link requests awaiting THIS student's approval or denial."""
    conn = _get_conn()
    rows = conn.execute(
        """SELECT u.id AS parent_id, u.full_name, u.username, pl.linked_at
           FROM parent_links pl
           JOIN users u ON u.id = pl.parent_id
           WHERE pl.student_id = ? AND pl.status = 'pending'""",
        (current_user["id"],)
    ).fetchall()
    conn.close()
    return {"pending_requests": [dict(r) for r in rows]}


@router.post("/student/respond-parent-link")
def respond_parent_link(req: RespondParentLinkRequest,
                         current_user: dict = Depends(require_student)):
    """Student approves or denies a pending parent link request. Approving
    is the ONLY way a parent-role account gets any read access to this
    student's data - see _parent_owns_student, which requires status='approved'."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT id FROM parent_links WHERE parent_id = ? AND student_id = ? AND status = 'pending'",
        (req.parent_id, current_user["id"])
    ).fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, "No pending request from that parent.")

    if req.approve:
        conn.execute(
            "UPDATE parent_links SET status = 'approved' WHERE id = ?", (row["id"],)
        )
        message = "Parent link approved. They can now see your progress."
    else:
        conn.execute("DELETE FROM parent_links WHERE id = ?", (row["id"],))
        message = "Parent link request denied."
    conn.commit()
    conn.close()
    return {"message": message}


@router.get("/student/linked-parents")
def get_student_linked_parents(current_user: dict = Depends(require_student)):
    """Transparency view: which parent accounts currently have approved
    access to this student's data. Previously there was no way for a
    student to even see this, let alone act on it."""
    conn = _get_conn()
    rows = conn.execute(
        """SELECT u.id AS parent_id, u.full_name, u.username, pl.linked_at
           FROM parent_links pl
           JOIN users u ON u.id = pl.parent_id
           WHERE pl.student_id = ? AND pl.status = 'approved'""",
        (current_user["id"],)
    ).fetchall()
    conn.close()
    return {"linked_parents": [dict(r) for r in rows]}


class UnlinkParentRequest(BaseModel):
    parent_id: int


@router.post("/student/unlink-parent")
def student_unlink_parent(req: UnlinkParentRequest,
                           current_user: dict = Depends(require_student)):
    """Student revokes a parent's access at any time, for any reason -
    no parent-side confirmation needed. This is the piece that was missing
    entirely before: once linked, there was previously no way to undo it."""
    conn = _get_conn()
    conn.execute(
        "DELETE FROM parent_links WHERE parent_id = ? AND student_id = ?",
        (req.parent_id, current_user["id"])
    )
    conn.commit()
    conn.close()
    return {"message": "Parent access removed."}


@router.get("/parent/student/{student_id}")
def get_student_progress(student_id: int,
                          current_user: dict = Depends(_require_parent)):
    """
    Read-only view of a linked student's progress.
    Returns scores, weak areas, exam history, and a shareable report summary.
    """
    conn = _get_conn()

    # Verify this parent has an APPROVED link to this student — same check
    # every other parent route in this file uses. This route previously
    # checked only that a parent_links row existed for this pair, with no
    # status filter, which meant a parent could pull a student's full
    # grades/scores/exam-history the instant they sent a link request,
    # before the student had approved (or even seen) it — bypassing the
    # consent flow entirely for this one endpoint.
    if not _parent_owns_student(conn, current_user["id"], student_id):
        conn.close()
        raise HTTPException(403, "You are not linked to this student.")

    student = conn.execute(
        "SELECT full_name, username FROM users WHERE id = ?", (student_id,)
    ).fetchone()

    exams = conn.execute(
        """SELECT subjects, score, max_score, started_at, submitted_at
           FROM exam_sessions
           WHERE user_id = ? AND submitted_at IS NOT NULL
           ORDER BY started_at DESC LIMIT 20""",
        (student_id,)
    ).fetchall()
    conn.close()

    scores = []
    subject_avgs: dict[str, list] = {}
    exam_history = []
    for e in exams:
        try:
            pct = round(e["score"] / e["max_score"] * 100, 1) if e["score"] and e["max_score"] else None
            if pct is None:
                continue
            subjects = json.loads(e["subjects"])
            scores.append(pct)
            for subj in subjects:
                subject_avgs.setdefault(subj, []).append(pct)
            exam_history.append({
                "subjects": subjects,
                "percentage": pct,
                "date": e["started_at"],
            })
        except Exception:
            continue

    avg_score = round(sum(scores) / len(scores), 1) if scores else None
    weak_subjects = [s for s, sc in subject_avgs.items() if (sum(sc)/len(sc)) < 50]
    strong_subjects = [s for s, sc in subject_avgs.items() if (sum(sc)/len(sc)) >= 65]

    conn2 = _get_conn()
    pred_avg, pred_grade, pred_credit, _ = _predict_student_avg(conn2, student_id)
    last_active = _get_last_active(conn2, student_id)
    conn2.close()

    return {
        "student_name": student["full_name"] or student["username"],
        "exams_taken": len(scores),
        "avg_score": avg_score,
        "predicted_grade": pred_grade,
        "predicted_avg": pred_avg,
        "credit_likely": pred_credit,
        "weak_subjects": weak_subjects,
        "strong_subjects": strong_subjects,
        "subject_averages": {s: round(sum(sc)/len(sc), 1) for s, sc in subject_avgs.items()},
        "exam_history": exam_history[:10],
        "last_active": last_active,
        "inactive_alert": _is_inactive(last_active),
        "report_summary": (
            f"{student['full_name'] or student['username']} has completed {len(scores)} exam(s) on NaijaSensei "
            f"with an average score of {avg_score}%. "
            f"Strong in: {', '.join(strong_subjects) or 'Still building up'}. "
            f"Needs attention in: {', '.join(weak_subjects) or 'None — doing well across all subjects'}."
        )
    }


@router.get("/parent/student/{student_id}/classroom-sessions")
def get_child_classroom_sessions(student_id: int, current_user: dict = Depends(_require_parent)):
    """List a linked child's AI Classroom session history — same data as the
    student's own Recap tab, viewed read-only through the parent's link."""
    conn = _get_conn()
    if not _parent_owns_student(conn, current_user["id"], student_id):
        conn.close()
        raise HTTPException(403, "You are not linked to this student.")
    try:
        rows = conn.execute(
            """SELECT id, started_at, ended_at, exchange_count, subjects, summary
               FROM classroom_sessions WHERE user_id = ?
               ORDER BY started_at DESC LIMIT 20""",
            (student_id,)
        ).fetchall()
    except Exception:
        conn.close()
        return {"sessions": [], "note": "No classroom sessions yet — restart the server so init_classroom_db() runs."}
    conn.close()

    sessions = []
    for r in rows:
        try:
            subjects = json.loads(r["subjects"]) if r["subjects"] else []
        except Exception:
            subjects = []
        sessions.append({
            "id": r["id"],
            "started_at": r["started_at"],
            "ended_at": r["ended_at"],
            "in_progress": r["ended_at"] is None,
            "exchange_count": r["exchange_count"],
            "subjects": subjects,
            "summary": r["summary"],
        })
    return {"sessions": sessions}
@router.get("/parent/logins")
def parent_logins(current_user: dict = Depends(_require_parent)):
    """Username + recoverable password + activity for every child this parent created."""
    conn = _get_conn()
    rows = conn.execute(
        """SELECT u.id, u.username, u.full_name, u.is_suspended, cc.plain_password
           FROM created_credentials cc
           JOIN users u ON u.id = cc.user_id
           WHERE cc.created_by_id = ? AND cc.created_by_role = 'parent'""",
        (current_user["id"],)
    ).fetchall()
    conn.close()
    students = []
    for r in rows:
        d = dict(r)
        d["plain_password"] = _decrypt_password(d["plain_password"])
        d.update(get_activity_summary(d["id"]))
        students.append(d)
    return {"students": students}


@router.post("/parent/suspend-child")
def parent_suspend_child(req: StudentActionRequest, current_user: dict = Depends(_require_parent)):
    conn = _get_conn()
    if not _parent_owns_student(conn, current_user["id"], req.student_id):
        conn.close()
        raise HTTPException(403, "This child is not linked to you.")
    conn.execute("UPDATE users SET is_suspended=1 WHERE id=?", (req.student_id,))
    conn.commit()
    conn.close()
    return {"message": "Child account suspended."}


@router.post("/parent/unsuspend-child")
def parent_unsuspend_child(req: StudentActionRequest, current_user: dict = Depends(_require_parent)):
    conn = _get_conn()
    if not _parent_owns_student(conn, current_user["id"], req.student_id):
        conn.close()
        raise HTTPException(403, "This child is not linked to you.")
    conn.execute("UPDATE users SET is_suspended=0 WHERE id=?", (req.student_id,))
    conn.commit()
    conn.close()
    return {"message": "Child account reactivated."}


@router.delete("/parent/child/{student_id}")
def parent_delete_child(student_id: int, current_user: dict = Depends(_require_parent)):
    conn = _get_conn()
    if not _parent_owns_student(conn, current_user["id"], student_id):
        conn.close()
        raise HTTPException(403, "This child is not linked to you.")
    _delete_student_fully(conn, student_id)
    conn.commit()
    conn.close()
    return {"message": "Child account deleted permanently."}

# ── Teacher Broadcast ─────────────────────────────────────────────────────────

class TeacherBroadcastRequest(BaseModel):
    message: str
    class_id: int | None = None   # None = send to ALL students in ALL teacher's classes


@router.post("/teacher/broadcast")
def teacher_broadcast(req: TeacherBroadcastRequest,
                       current_user: dict = Depends(_require_teacher)):
    """
    Teacher sends a broadcast to their students only.
    Stored with sender_type='teacher' so UI can visually distinguish it
    from admin broadcasts.
    """
    if not req.message.strip():
        raise HTTPException(400, "Message cannot be empty.")

    conn = _get_conn()

    # Verify class belongs to this teacher if specified
    if req.class_id:
        cls = conn.execute(
            "SELECT id, name FROM classes WHERE id=? AND teacher_id=?",
            (req.class_id, current_user["id"])
        ).fetchone()
        if not cls:
            conn.close()
            raise HTTPException(404, "Class not found.")
        target = f"class:{req.class_id}"
    else:
        # All classes belonging to this teacher
        target = f"teacher:{current_user['id']}"

    teacher_name = current_user.get("full_name") or current_user.get("username", "Teacher")

    conn.execute(
        """INSERT INTO broadcasts (sender_type, sender_id, sender_label, message, target)
           VALUES ('teacher', ?, ?, ?, ?)""",
        (current_user["id"], teacher_name, req.message.strip(), target)
    )
    conn.commit()
    conn.close()
    return {"message": "Broadcast sent to your students."}


@router.get("/teacher/broadcasts")
def get_teacher_broadcasts(current_user: dict = Depends(_require_teacher)):
    """List this teacher's own past broadcasts."""
    conn = _get_conn()
    rows = conn.execute(
        """SELECT b.*, COUNT(br.user_id) as read_count
           FROM broadcasts b
           LEFT JOIN broadcast_reads br ON br.broadcast_id = b.id
           WHERE b.sender_id = ? AND b.sender_type = 'teacher'
           GROUP BY b.id ORDER BY b.sent_at DESC LIMIT 20""",
        (current_user["id"],)
    ).fetchall()
    conn.close()
    return {"broadcasts": [dict(r) for r in rows]}