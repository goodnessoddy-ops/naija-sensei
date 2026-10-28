"""
past_questions.py — WAEC/NECO/UTME Past Questions practice for NaijaSensei,
powered by the free ALOC API (https://questions.aloc.com.ng).

READ BEFORE DEPLOYING — three things that matter:

1. Requires a free ALOC access token. Sign up at
   https://questions.aloc.com.ng, copy the token, and set it as
   ALOC_ACCESS_TOKEN in your .env file. Without it every endpoint here
   returns a clear 503 explaining what's missing, instead of a confusing
   500 crash.

2. WAEC's OWN e-Learning portal (waeconline.org.ng) and eStudy (estudy.ng)
   do NOT expose a public API — they are just websites built for humans to
   browse. There is no supported, documented way to pull data from them
   programmatically. Scraping them would be fragile (breaks the moment
   their HTML changes) and likely against their terms of use, so this
   module deliberately does not attempt it. ALOC is a genuinely public,
   documented, free API — that's the only reason it's used here.

3. ALOC only covers a subset of NaijaSensei's WAEC subjects (see
   SUBJECT_MAP below) — 15 of them, not all 40+. Financial Accounting maps
   to ALOC's "accounting" as the closest match, not an exact one. Most
   trade subjects and Nigerian languages have zero coverage through this
   API and are not listed.

4. The exact JSON field names ALOC returns (option/options, answer,
   examyear, etc.) are based on ALOC's commonly-documented v2 response
   shape, NOT a live-tested call — this environment has no network path to
   test with a real token. _parse_aloc_question() is written defensively
   (tries multiple likely key names, skips a malformed question instead of
   crashing the whole batch) so a schema mismatch degrades gracefully. If
   questions come back visibly wrong once you have a real token, that
   function is the first place to check against an actual response.
"""

import os
import json
import random
import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from auth import require_student, _get_conn

router = APIRouter(prefix="/past-questions", tags=["past-questions"])

ALOC_BASE = "https://questions.aloc.com.ng/api/v2"

# NaijaSensei subject name -> ALOC subject slug. ONLY subjects listed here
# have past-question coverage through this feature — everything else in
# student_profile.py's subject lists has none.
SUBJECT_MAP = {
    "Mathematics": "mathematics",
    "English Language": "english",
    "Biology": "biology",
    "Physics": "physics",
    "Chemistry": "chemistry",
    "Government": "government",
    "Economics": "economics",
    "Geography": "geography",
    "History": "history",
    "Commerce": "commerce",
    "Financial Accounting": "accounting",   # closest available match, not exact
    "Literature in English": "englishlit",
    "Civic Education": "civiledu",
    "Christian Religious Studies": "crk",
    "Islamic Religious Studies": "irk",
}


def init_past_questions_db():
    """Create the pq_sessions table on startup. Safe to call repeatedly."""
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pq_sessions (
            id           BIGSERIAL PRIMARY KEY,
            user_id      INTEGER NOT NULL,
            subject      TEXT NOT NULL,
            exam_type    TEXT,
            year         TEXT,
            questions    TEXT NOT NULL,
            score        INTEGER,
            total        INTEGER,
            started_at   TEXT DEFAULT (now_iso()),
            submitted_at TEXT
        )
    """)
    conn.commit()
    conn.close()
    print("[past_questions] pq_sessions DB ready.")


def _get_token() -> str:
    token = os.environ.get("ALOC_ACCESS_TOKEN", "").strip()
    if not token:
        raise HTTPException(
            503,
            "Past Questions isn't set up yet. Sign up for a free access token at "
            "https://questions.aloc.com.ng, then set ALOC_ACCESS_TOKEN in the .env "
            "file and restart the server."
        )
    return token


def _parse_aloc_question(raw: dict) -> Optional[dict]:
    """
    Best-effort normaliser: one ALOC question object -> the shape the
    frontend expects ({id, question, options:{A,B,...}, answer, year,
    comment}). Returns None (caller skips it) instead of raising, so one
    malformed question doesn't take down the whole practice set. See the
    module docstring point 4 before assuming this is exactly right.
    """
    try:
        qid = raw.get("id") or raw.get("_id") or raw.get("qid")
        question_text = raw.get("question") or raw.get("q")
        opts_raw = raw.get("option") or raw.get("options") or {}
        if isinstance(opts_raw, list):
            letters = ["A", "B", "C", "D", "E"]
            opts = {letters[i]: v for i, v in enumerate(opts_raw) if i < len(letters) and v}
        elif isinstance(opts_raw, dict):
            opts = {str(k).upper(): v for k, v in opts_raw.items() if v}
        else:
            opts = {}
        answer = str(raw.get("answer", "")).strip().upper()
        if not (qid and question_text and opts and answer):
            return None
        return {
            "id": str(qid),
            "question": question_text,
            "options": opts,
            "answer": answer,
            "year": raw.get("examyear") or raw.get("year"),
            "comment": raw.get("comment") or raw.get("solution") or None,
        }
    except Exception:
        return None


# ── Schemas ───────────────────────────────────────────────────────────────

class StartRequest(BaseModel):
    subject: str                    # NaijaSensei subject name, e.g. "Mathematics"
    year: Optional[str] = None      # e.g. "2015" - omit for a random mix of years
    count: int = 10


class SubmitRequest(BaseModel):
    session_id: int
    answers: dict                   # {question_id: "A"}


# ── Routes ────────────────────────────────────────────────────────────────

@router.get("/subjects")
def get_supported_subjects(current_user: dict = Depends(require_student)):
    """Only the subjects ALOC actually has - NOT all WAEC subjects."""
    return {"subjects": sorted(SUBJECT_MAP.keys())}


@router.post("/start")
async def start_practice(req: StartRequest, current_user: dict = Depends(require_student)):
    """Fetch a fresh batch of past questions and start a practice session.
    Correct answers are stored server-side only and stripped before the
    question list is sent to the frontend, so they can't be read from the
    browser network tab mid-practice."""
    token = _get_token()

    slug = SUBJECT_MAP.get(req.subject)
    if not slug:
        raise HTTPException(
            400,
            f"'{req.subject}' isn't available in Past Questions yet. "
            f"Available subjects: {', '.join(sorted(SUBJECT_MAP.keys()))}"
        )
    count = max(1, min(req.count, 20))

    params = {"subject": slug, "type": "wassce"}
    if req.year:
        params["year"] = req.year

    url = f"{ALOC_BASE}/q/{count}"
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(url, params=params, headers={"AccessToken": token})
        if resp.status_code == 401:
            raise HTTPException(502, "ALOC rejected the access token - check ALOC_ACCESS_TOKEN is correct and still active.")
        resp.raise_for_status()
        data = resp.json()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, f"Could not reach the past-questions service: {e}")

    raw_questions = data.get("data") if isinstance(data, dict) else data
    if not isinstance(raw_questions, list):
        raw_questions = [raw_questions] if raw_questions else []

    questions = [q for q in (_parse_aloc_question(r) for r in raw_questions) if q]
    if not questions:
        raise HTTPException(
            502,
            "No usable questions came back for that subject/year combination. "
            "Try a different year, or leave year blank for a random mix."
        )

    random.shuffle(questions)

    conn = _get_conn()
    cursor = conn.execute(
        "INSERT INTO pq_sessions (user_id, subject, exam_type, year, questions, total) VALUES (?, ?, ?, ?, ?, ?)",
        (current_user["id"], req.subject, "wassce", req.year, json.dumps(questions), len(questions))
    )
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()

    safe_questions = [
        {k: v for k, v in q.items() if k not in ("answer", "comment")}
        for q in questions
    ]
    return {"session_id": session_id, "subject": req.subject, "questions": safe_questions}


@router.post("/submit")
def submit_practice(req: SubmitRequest, current_user: dict = Depends(require_student)):
    """Grade a practice session against the answers stored server-side."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT * FROM pq_sessions WHERE id = ? AND user_id = ?",
        (req.session_id, current_user["id"])
    ).fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, "Practice session not found.")

    questions = json.loads(row["questions"])
    results = []
    score = 0
    for q in questions:
        student_ans = (req.answers.get(q["id"]) or "").strip().upper()
        correct = student_ans == q["answer"]
        if correct:
            score += 1
        results.append({
            "id": q["id"],
            "question": q["question"],
            "options": q["options"],
            "your_answer": student_ans or None,
            "correct_answer": q["answer"],
            "correct": correct,
            "comment": q.get("comment"),
        })

    conn.execute(
        "UPDATE pq_sessions SET score = ?, submitted_at = now_iso() WHERE id = ?",
        (score, row["id"])
    )
    conn.commit()
    conn.close()

    total = len(questions)
    return {
        "score": score,
        "total": total,
        "percentage": round(score / total * 100, 1) if total else 0,
        "results": results,
    }


@router.get("/history")
def get_practice_history(current_user: dict = Depends(require_student)):
    """A student's own past practice sessions, most recent first."""
    conn = _get_conn()
    rows = conn.execute(
        """SELECT id, subject, year, score, total, started_at, submitted_at
           FROM pq_sessions WHERE user_id = ? AND submitted_at IS NOT NULL
           ORDER BY submitted_at DESC LIMIT 20""",
        (current_user["id"],)
    ).fetchall()
    conn.close()
    return {"history": [dict(r) for r in rows]}