"""
predictor.py — Pass Predictor for NaijaSensei.

Two-step prediction:
1. Diagnostic exam: a short 10-question test across the student's chosen
   subjects to establish a baseline if they have no exam history yet.
2. Ongoing prediction: once they have exam history, combine diagnostic
   result + past exam scores + weak topic analysis to predict WAEC pass
   likelihood per subject (A1-C6 = credit pass, D7-F9 = fail).
"""

import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from auth import require_user, _get_conn
from ai_providers import call_ai_with_fallback

router = APIRouter(prefix="/predict", tags=["predictor"])

CREDIT_GRADES = {"A1", "B2", "B3", "C4", "C5", "C6"}


def init_predictor_db():
    """Create all tables needed by predictor.py on startup."""
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS diagnostic_results (
            id BIGSERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            subjects TEXT NOT NULL,
            results TEXT NOT NULL,
            taken_at TEXT DEFAULT (now_iso())
        )
    """)
    # A timestamped history of what was predicted, not just the live
    # recomputed number — needed so a later actual result can be compared
    # against what was actually being shown to the student at some point
    # in time, not against today's (possibly different) live prediction.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS predicted_grades (
            id              BIGSERIAL PRIMARY KEY,
            user_id         INTEGER NOT NULL,
            subject         TEXT NOT NULL,
            predicted_grade TEXT NOT NULL,
            predicted_pct   REAL,
            confidence      TEXT,
            recorded_at     TEXT DEFAULT (now_iso())
        )
    """)
    # Student self-reports their real WAEC grade once results are out.
    # This is the only source of ground truth anywhere in this codebase
    # for whether Pass Predictor is actually accurate — see /accuracy
    # below, which is the whole reason these two tables exist.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS actual_waec_results (
            id           BIGSERIAL PRIMARY KEY,
            user_id      INTEGER NOT NULL,
            subject      TEXT NOT NULL,
            actual_grade TEXT NOT NULL,
            exam_year    TEXT NOT NULL,
            reported_at  TEXT DEFAULT (now_iso()),
            UNIQUE(user_id, subject, exam_year)
        )
    """)
    conn.commit()
    conn.close()

WAEC_GRADE_BOUNDARIES = [
    (75, "A1"), (70, "B2"), (65, "B3"),
    (60, "C4"), (55, "C5"), (50, "C6"),
    (45, "D7"), (40, "E8"), (0,  "F9"),
]

def pct_to_grade(pct: float) -> str:
    for boundary, grade in WAEC_GRADE_BOUNDARIES:
        if pct >= boundary:
            return grade
    return "F9"

def grade_to_credit(grade: str) -> bool:
    return grade in CREDIT_GRADES


def _parse_diagnostic_questions(raw: str) -> list[dict]:
    """
    Parses the AI's JSON response into a list of question dicts. Falls back
    to recovering only the *complete* question objects if the response was
    truncated mid-generation (common with tight token limits), rather than
    failing the whole request over one broken trailing object.
    """
    import re

    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)

    # Fast path — well-formed JSON
    try:
        data = json.loads(raw)
        questions = data.get("questions", [])
        if questions:
            return questions
    except Exception:
        pass

    # Recovery path — pull out each {...} object anywhere in the response
    # (questions sit one level inside the outer {"questions": [...]} wrapper,
    # so we track a stack of open-brace positions rather than only objects
    # that return to top-level depth 0, which never happens for a truncated
    # wrapper that's still open). Skip anything that doesn't parse or doesn't
    # look like a real question, instead of letting one broken trailing
    # object invalidate all the good ones before it.
    recovered = []
    stack = []
    for i, ch in enumerate(raw):
        if ch == "{":
            stack.append(i)
        elif ch == "}":
            if stack:
                start_idx = stack.pop()
                candidate = raw[start_idx:i + 1]
                try:
                    obj = json.loads(candidate)
                    # Only keep things that look like a real question object
                    if isinstance(obj, dict) and "question" in obj and "options" in obj:
                        recovered.append(obj)
                except Exception:
                    pass

    return recovered


# ── Diagnostic: generate 10 quick MCQs across chosen subjects ─────────────────

class DiagnosticRequest(BaseModel):
    subjects: list[str]

class DiagnosticSubmitRequest(BaseModel):
    subjects: list[str]
    answers: dict   # {"q1": "A", "q2": "B", ...}
    questions: list[dict]  # the original questions sent from frontend


@router.post("/diagnostic/start")
async def start_diagnostic(req: DiagnosticRequest,
                            current_user: dict = Depends(require_user)):
    """Generate a short 10-question diagnostic MCQ across chosen subjects."""
    if not req.subjects:
        raise HTTPException(400, "Select at least one subject.")

    # Pull curriculum grounding for the chosen subjects, same approach as
    # exam.py's _get_rag_context — previously this prompt had zero RAG
    # grounding at all, unlike exam.py's exam generator.
    import asyncio
    from rag import search

    def _get_diagnostic_rag_context(subjects: list[str], top_k: int = 12) -> list[dict]:
        all_passages = []
        for subject in subjects:
            hits = search(subject + " key topics", top_k=top_k // len(subjects) + 2)
            for h in hits:
                if h["subject"] in subjects and h not in all_passages:
                    all_passages.append(h)
        return all_passages[:top_k]

    passages = await asyncio.to_thread(_get_diagnostic_rag_context, req.subjects)
    context = "\n\n".join(f"[{p['subject']} · {p['topic']}]\n{p['content']}" for p in passages)
    context_block = f"\n\nCURRICULUM CONTEXT — base questions on this real syllabus content where relevant:\n{context}\n" if context else ""

    prompt = f"""You are a WAEC exam question generator for Nigerian secondary school students.

Generate exactly 10 multiple choice diagnostic questions to assess a student's
current level across these subjects: {", ".join(req.subjects)}.

Mix easy, medium, and hard questions. Spread evenly across subjects.
{context_block}
Return ONLY valid JSON, no other text, no markdown:
{{
  "questions": [
    {{
      "id": "q1",
      "question": "question text",
      "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
      "answer": "A",
      "subject": "Mathematics",
      "difficulty": "medium"
    }}
  ]
}}"""

    try:
        raw = await call_ai_with_fallback(prompt, max_tokens=4500)
        questions = _parse_diagnostic_questions(raw)
        if not questions:
            raise ValueError("No valid questions could be parsed from the AI response")
        return {"questions": questions[:10]}
    except Exception as e:
        raise HTTPException(500, f"Could not generate diagnostic questions: {e}")


@router.post("/diagnostic/submit")
async def submit_diagnostic(req: DiagnosticSubmitRequest,
                             current_user: dict = Depends(require_user)):
    """
    Mark the diagnostic, save results, and generate an initial prediction.
    """
    # Mark MCQs
    subject_scores: dict[str, dict] = {}
    for q in req.questions:
        subj = q.get("subject", "General")
        if subj not in subject_scores:
            subject_scores[subj] = {"correct": 0, "total": 0}
        student_ans = req.answers.get(q["id"], "").strip().upper()
        correct_ans = q.get("answer", "").strip().upper()
        subject_scores[subj]["total"] += 1
        if student_ans == correct_ans:
            subject_scores[subj]["correct"] += 1

    # Calculate per-subject percentage and grade
    results = {}
    for subj, sc in subject_scores.items():
        pct = round(sc["correct"] / max(sc["total"], 1) * 100, 1)
        results[subj] = {
            "score": sc["correct"],
            "total": sc["total"],
            "percentage": pct,
            "grade": pct_to_grade(pct),
            "credit": grade_to_credit(pct_to_grade(pct)),
        }

    # Save diagnostic to DB. Blocking DB call pushed to a worker thread —
    # this is an async def route, so calling the DB directly here would
    # stall the event loop for every other in-flight request too.
    def _save():
        conn = _get_conn()
        conn.execute(
            "INSERT INTO diagnostic_results (user_id, subjects, results) VALUES (?, ?, ?)",
            (current_user["id"], json.dumps(req.subjects), json.dumps(results))
        )
        conn.commit()
        conn.close()

    await asyncio.to_thread(_save)

    return {
        "results": results,
        "message": "Diagnostic complete! Check your Pass Predictor for a full analysis."
    }


# ── Pass Prediction ───────────────────────────────────────────────────────────

@router.get("/prediction")
async def get_prediction(current_user: dict = Depends(require_user)):
    """
    Combine diagnostic results + exam history to predict WAEC pass likelihood
    per subject. Returns per-subject prediction, confidence level, and
    AI-generated advice.
    """
    user_id = current_user["id"]

    def _fetch():
        conn = _get_conn()
        rows = conn.execute(
            """SELECT subjects, score, max_score, feedback, submitted_at
               FROM exam_sessions
               WHERE user_id = ? AND submitted_at IS NOT NULL
               ORDER BY submitted_at DESC LIMIT 20""",
            (user_id,)
        ).fetchall()
        diag = conn.execute(
            """SELECT results, taken_at FROM diagnostic_results
               WHERE user_id = ? ORDER BY taken_at DESC LIMIT 1""",
            (user_id,)
        ).fetchone()
        conn.close()
        return rows, diag

    # Blocking DB calls pushed to a worker thread — see the note in
    # submit_diagnostic() above for why this matters in an async def route.
    exam_rows, diag_row = await asyncio.to_thread(_fetch)

    if not exam_rows and not diag_row:
        return {
            "has_data": False,
            "message": "Take the diagnostic test or complete at least one practice exam to see your Pass Predictor results."
        }

    # Build per-subject score history from exams
    subject_history: dict[str, list[float]] = {}
    for row in exam_rows:
        try:
            subjects = json.loads(row["subjects"])
            pct = round(row["score"] / row["max_score"] * 100, 1) if row["score"] and row["max_score"] else None
            if pct is None:
                continue
            for subj in subjects:
                if subj not in subject_history:
                    subject_history[subj] = []
                subject_history[subj].append(pct)
        except Exception:
            continue

    # Pull diagnostic results
    diag_results = {}
    if diag_row:
        try:
            diag_results = json.loads(diag_row["results"])
        except Exception:
            pass

    # Combine: weighted average (recent exams count more than diagnostic)
    predictions = {}
    all_subjects = set(list(subject_history.keys()) + list(diag_results.keys()))

    for subj in all_subjects:
        scores = subject_history.get(subj, [])
        diag = diag_results.get(subj, {})
        diag_pct = diag.get("percentage") if diag else None

        if scores:
            # Weight: most recent exam = 2x, older = 1x, diagnostic = 0.5x
            weighted_sum = sum(s * (2 if i == 0 else 1) for i, s in enumerate(scores))
            weight_total = sum(2 if i == 0 else 1 for i in range(len(scores)))
            if diag_pct is not None:
                weighted_sum += diag_pct * 0.5
                weight_total += 0.5
            avg_pct = round(weighted_sum / weight_total, 1)
            confidence = "High" if len(scores) >= 3 else ("Medium" if len(scores) >= 1 else "Low")
        elif diag_pct is not None:
            avg_pct = diag_pct
            confidence = "Low"
        else:
            continue

        grade = pct_to_grade(avg_pct)
        credit = grade_to_credit(grade)

        # Trend: compare last 2 exams if available
        trend = "stable"
        if len(scores) >= 2:
            if scores[0] > scores[1] + 5:
                trend = "improving"
            elif scores[0] < scores[1] - 5:
                trend = "declining"

        predictions[subj] = {
            "predicted_grade": grade,
            "predicted_pct": avg_pct,
            "credit_likely": credit,
            "confidence": confidence,
            "trend": trend,
            "exams_taken": len(scores),
            "has_diagnostic": diag_pct is not None,
        }

    if not predictions:
        return {
            "has_data": False,
            "message": "Complete at least one exam or diagnostic test to see predictions."
        }

    # Snapshot this prediction run so there's a real timestamped history to
    # eventually compare against actual WAEC results (see /accuracy below).
    # Only inserts a new row when the grade actually changed since the last
    # snapshot for that subject — otherwise a student just reopening this
    # tab repeatedly would flood the table with identical rows.
    def _snapshot():
        conn = _get_conn()
        for subj, p in predictions.items():
            last = conn.execute(
                """SELECT predicted_grade FROM predicted_grades
                   WHERE user_id = ? AND subject = ?
                   ORDER BY recorded_at DESC LIMIT 1""",
                (user_id, subj)
            ).fetchone()
            if not last or last["predicted_grade"] != p["predicted_grade"]:
                conn.execute(
                    """INSERT INTO predicted_grades (user_id, subject, predicted_grade, predicted_pct, confidence)
                       VALUES (?, ?, ?, ?, ?)""",
                    (user_id, subj, p["predicted_grade"], p["predicted_pct"], p["confidence"])
                )
        conn.commit()
        conn.close()

    await asyncio.to_thread(_snapshot)

    # AI advice based on predictions
    weak_subjects = [s for s, p in predictions.items() if not p["credit_likely"]]
    strong_subjects = [s for s, p in predictions.items() if p["credit_likely"]]

    advice_prompt = f"""You are NaijaSensei, a warm Nigerian secondary school tutor giving honest, motivating WAEC pass prediction feedback.

Student's predicted performance:
{json.dumps({s: {'grade': p['predicted_grade'], 'credit': p['credit_likely'], 'trend': p['trend']} for s, p in predictions.items()}, indent=2)}

Strong subjects (likely credit): {", ".join(strong_subjects) if strong_subjects else "None yet"}
Weak subjects (at risk): {", ".join(weak_subjects) if weak_subjects else "None — keep it up!"}

Give honest, warm, specific advice in 3-4 sentences. No markdown, no bullet points, plain flowing prose.
Focus on what the student should do RIGHT NOW to improve their weak subjects before WAEC.
Be encouraging but realistic."""

    try:
        advice = await call_ai_with_fallback(advice_prompt, max_tokens=300)
    except Exception:
        advice = "Keep practising regularly and focus extra time on your weaker subjects. Consistency is key to improving your WAEC predictions."

    return {
        "has_data": True,
        "predictions": predictions,
        "strong_subjects": strong_subjects,
        "weak_subjects": weak_subjects,
        "ai_advice": advice.strip(),
    }

# ── Closing the loop: real WAEC outcomes vs what was predicted ─────────────
# Nothing above this point ever checks whether a prediction was actually
# right. These two routes are how that starts getting measured: a student
# reports their real grade once WAEC results are out, and /accuracy
# compares it against whatever was predicted for them at the time.

class ActualResultRequest(BaseModel):
    subject: str
    actual_grade: str   # WAEC grade, e.g. "B3", "C6", "F9"
    exam_year: str       # e.g. "2026"


_VALID_GRADES = CREDIT_GRADES | {"D7", "E8", "F9"}


@router.post("/actual-result")
async def submit_actual_result(req: ActualResultRequest,
                                current_user: dict = Depends(require_user)):
    """
    Student self-reports their real WAEC grade for a subject once results
    are released. Self-reported, not verified against WAEC directly — so
    treat aggregate accuracy numbers below as directional, not audited.
    Resubmitting the same user/subject/year updates the existing record
    rather than creating a duplicate.
    """
    grade = req.actual_grade.strip().upper()
    if grade not in _VALID_GRADES:
        raise HTTPException(400, f"'{req.actual_grade}' isn't a recognised WAEC grade (A1-F9).")
    if not req.exam_year.strip():
        raise HTTPException(400, "exam_year is required.")

    def _save():
        conn = _get_conn()
        conn.execute(
            """INSERT INTO actual_waec_results (user_id, subject, actual_grade, exam_year)
               VALUES (?, ?, ?, ?)
               ON CONFLICT (user_id, subject, exam_year) DO UPDATE SET
                   actual_grade = EXCLUDED.actual_grade, reported_at = now_iso()""",
            (current_user["id"], req.subject, grade, req.exam_year.strip())
        )
        conn.commit()
        conn.close()

    # Blocking DB call pushed to a worker thread — same reasoning as every
    # other async route in this file.
    await asyncio.to_thread(_save)
    return {"status": "recorded", "subject": req.subject, "actual_grade": grade}


@router.get("/accuracy")
async def prediction_accuracy():
    """
    Aggregate accuracy of Pass Predictor across every student who has
    self-reported a real result: for each (user, subject), compares the
    most recent prediction snapshot recorded BEFORE that result was
    reported against what they actually got. No auth — this is a
    product-quality metric, not personal data (no user_id in the
    response). Returns has_data:false until at least one predicted/actual
    pair exists — that means "not enough data yet", not "0% accurate".
    """
    def _fetch():
        conn = _get_conn()
        rows = conn.execute("""
            SELECT a.user_id, a.subject, a.actual_grade,
                   (SELECT p.predicted_grade FROM predicted_grades p
                    WHERE p.user_id = a.user_id AND p.subject = a.subject
                      AND p.recorded_at <= a.reported_at
                    ORDER BY p.recorded_at DESC LIMIT 1) AS predicted_grade
            FROM actual_waec_results a
        """).fetchall()
        conn.close()
        return rows

    rows = await asyncio.to_thread(_fetch)
    pairs = [r for r in rows if r["predicted_grade"]]

    if not pairs:
        return {
            "has_data": False,
            "message": "No predicted-vs-actual pairs recorded yet — needs students to have both a prediction on record and a self-reported real result."
        }

    n = len(pairs)
    exact_matches = sum(1 for r in pairs if r["predicted_grade"] == r["actual_grade"])
    credit_agreement = sum(
        1 for r in pairs
        if grade_to_credit(r["predicted_grade"]) == grade_to_credit(r["actual_grade"])
    )
    return {
        "has_data": True,
        "sample_size": n,
        "exact_grade_match_pct": round(exact_matches / n * 100, 1),
        "credit_vs_no_credit_agreement_pct": round(credit_agreement / n * 100, 1),
    }