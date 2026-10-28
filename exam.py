"""
exam.py — Exam mode for NaijaSensei
Endpoints:
  POST /exam/start      → generate a timed exam (MCQ + theory)
  POST /exam/submit     → submit answers, get score + AI feedback
  GET  /exam/history    → past exam results for a student

Now uses the shared 32-provider fallback chain from ai_providers.py
instead of a standalone Gemini → Groq → Ollama chain.
"""

import asyncio
import os
import json
import time
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from auth import require_user, _get_conn
from ai_providers import call_ai_with_fallback

router = APIRouter(prefix="/exam", tags=["exam"])

# ── Subjects available ────────────────────────────────────────────────────────
from student_profile import ALL_SUBJECTS_BY_DEPARTMENT, TRADE_SUBJECTS

# Union of every subject across all departments + compulsory + trades,
# so exam validation never rejects a subject a student can legitimately
# have on their profile. Single source of truth lives in student_profile.py.
SUBJECTS = sorted(set(
    sum(ALL_SUBJECTS_BY_DEPARTMENT.values(), []) + TRADE_SUBJECTS
))
# ── DB setup ──────────────────────────────────────────────────────────────────
def init_exam_db():
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS exam_sessions (
            id           BIGSERIAL PRIMARY KEY,
            user_id      INTEGER NOT NULL,
            subjects     TEXT NOT NULL,
            questions    TEXT NOT NULL,
            answers      TEXT,
            timings      TEXT,
            coach_mode   INTEGER DEFAULT 0,
            score        REAL,
            max_score    REAL,
            feedback     TEXT,
            started_at   TEXT DEFAULT (now_iso()),
            submitted_at TEXT,
            duration_min INTEGER DEFAULT 45
        )
    """)
    # Add columns for older DBs that don't have them yet.
    # IF NOT EXISTS is idempotent in Postgres — unlike the old SQLite
    # try/except pattern, a failed ALTER here would abort the rest of
    # this transaction, so this can't stay a bare try/except.
    for col, coltype in [("timings", "TEXT"), ("coach_mode", "INTEGER DEFAULT 0")]:
        conn.execute(f"ALTER TABLE exam_sessions ADD COLUMN IF NOT EXISTS {col} {coltype}")
    conn.commit()
    conn.close()

# ── Exam mode presets ────────────────────────────────────────────────────────
EXAM_PRESETS = {
    "waec": {
        "label": "Real WAEC Simulation",
        "num_mcq": 50,
        "num_theory": 6,        # WAEC gives 6, student answers 4 — we generate 6
        "theory_attempt": 4,    # how many theory Qs student must attempt
        "duration_min": 180,    # 3 hours
        "description": "50 MCQ + 6 theory questions (answer any 4) · 3 hours · Full WAEC simulation"
    },
    "quick": {
        "label": "Quick Practice",
        "num_mcq": 15,
        "num_theory": 3,
        "theory_attempt": 3,
        "duration_min": 30,
        "description": "15 MCQ + 3 theory questions · 30 minutes · Fast revision session"
    },
    "custom": {
        "label": "Custom",
        "num_mcq": 10,
        "num_theory": 3,
        "theory_attempt": 3,
        "duration_min": 45,
        "description": "Set your own number of questions and time"
    }
}

class ExamStartRequest(BaseModel):
    subjects: list[str]  # enforced to exactly 1 item in /start — one subject per exam
    mode: str = "quick"          # "waec", "quick", or "custom"
    num_mcq: int = 15            # only used when mode="custom"
    num_theory: int = 3          # only used when mode="custom"
    duration_min: int = 30       # only used when mode="custom"
    coach_mode: bool = False     # AI Exam Coach — tracks per-question speed

class ExamSubmitRequest(BaseModel):
    session_id: int
    answers: dict              # {"q1": "A", "q2": "oxidation is...", ...}
    timings: Optional[dict] = None  # {"q1": 12.4, "q2": 45.0, ...} seconds per question

# ── Helpers ───────────────────────────────────────────────────────────────────
def _get_rag_context(subjects: list[str], top_k: int = 15) -> list[dict]:
    """Pull relevant curriculum passages for the selected subjects."""
    from rag import search
    all_passages = []
    for subject in subjects:
        hits = search(subject + " past exam questions topics", top_k=top_k // len(subjects) + 2)
        for h in hits:
            if h["subject"] in subjects and h not in all_passages:
                all_passages.append(h)
    return all_passages[:top_k]


def _build_marking_prompt(questions: list[dict], answers: dict) -> str:
    qa_pairs = []
    for q in questions:
        student_ans = answers.get(q["id"], "[No answer provided]")
        qa_pairs.append(
            f"Question ({q['subject']} - {q['topic']}, {q['marks']} marks):\n"
            f"{q['question']}\n\n"
            f"Model answer guide: {q['model_answer']}\n\n"
            f"Student's answer: {student_ans}"
        )

    joined = "\n\n---\n\n".join(qa_pairs)
    return f"""You are a WAEC examiner marking theory answers for Nigerian secondary school students.

Mark each theory answer below. Be fair but strict, like a real WAEC examiner.

{joined}

Return ONLY a JSON object, no other text:
{{
  "results": [
    {{
      "id": "th_1",
      "score": 7,
      "max": 10,
      "feedback": "brief encouraging feedback explaining what was good and what was missing"
    }}
  ]
}}

Rules:
- Award marks proportionally based on how much of the model answer was covered
- Feedback must be in simple English a Nigerian SS3 student understands
- Be encouraging but honest"""


# ── Routes ────────────────────────────────────────────────────────────────────
@router.get("/subjects")
def get_subjects():
    """Return list of available subjects."""
    return {"subjects": SUBJECTS}


# ── Question cache (in-memory, keyed by subjects+mode) ────────────────────────
import hashlib
import random
_question_cache: dict = {}   # key -> {"mcq": [...], "theory": [...]}

def _cache_key(subjects: list, mode: str) -> str:
    key = mode + "|" + "|".join(sorted(subjects))
    return hashlib.md5(key.encode()).hexdigest()


async def _call_ai(prompt: str, max_tokens: int = 3000) -> str:
    """
    Call the shared 32-provider fallback chain (non-streaming, async).
    Replaces the old standalone Gemini -> Groq -> Ollama chain.
    """
    print(f"[EXAM] Calling AI fallback chain (prompt: {len(prompt)} chars)...")
    try:
        result = await call_ai_with_fallback(prompt, max_tokens=max_tokens)
        print(f"[EXAM] Got {len(result)} chars back")
        return result
    except Exception as e:
        raise RuntimeError(
            f"All AI providers failed while generating exam content.\n"
            f"Add more API keys to your .env file, or make sure Ollama is running for offline mode.\n"
            f"Error: {e}"
        )


def _parse_json(raw: str) -> dict:
    """Robustly parse JSON from AI response, with repair for truncated output."""
    # Remove Ollama special tokens (▁ word-piece markers appear in some models)
    clean = raw.strip().replace("▁", " ").replace("\u2581", " ")

    # Strip markdown code fences - handles ```json ... ``` and ``` ... ```
    if "```" in clean:
        import re as _re2
        # Try to extract the JSON block
        fence_match = _re2.search(r'```(?:json)?\s*(\{.*?)```', clean, _re2.DOTALL)
        if fence_match:
            try:
                return json.loads(fence_match.group(1).strip())
            except Exception:
                pass
        # Fallback: split on fences
        parts = clean.split("```")
        for p in parts:
            p = p.strip()
            if p.startswith("json"):
                p = p[4:].strip()
            if p.startswith("{"):
                try:
                    return json.loads(p)
                except Exception:
                    repaired = _repair_truncated_json(p)
                    if repaired is not None:
                        return repaired

    # Try direct parse
    try:
        return json.loads(clean)
    except Exception:
        pass

    # Find first { ... } block
    start = clean.find("{")
    if start != -1:
        candidate = clean[start:]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            repaired = _repair_truncated_json(candidate)
            if repaired is not None:
                return repaired

    raise ValueError(f"Could not parse JSON from: {clean[:200]}")


def _repair_truncated_json(text: str) -> Optional[dict]:
    """
    Attempt to salvage a truncated JSON response by finding the last
    complete object inside the top-level array and closing brackets.
    Returns a dict with whatever complete items were recovered, or None.
    """
    # Find the key (e.g. "mcq" or "theory") and the array start
    for key in ("mcq", "theory"):
        marker = f'"{key}"'
        idx = text.find(marker)
        if idx == -1:
            continue
        arr_start = text.find("[", idx)
        if arr_start == -1:
            continue

        # Walk through and find complete top-level objects inside the array
        depth = 0
        obj_start = None
        items = []
        i = arr_start + 1
        in_string = False
        escape = False
        while i < len(text):
            ch = text[i]
            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
            else:
                if ch == '"':
                    in_string = True
                elif ch == "{":
                    if depth == 0:
                        obj_start = i
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0 and obj_start is not None:
                        chunk = text[obj_start:i+1]
                        try:
                            items.append(json.loads(chunk))
                        except Exception:
                            pass
                        obj_start = None
            i += 1

        if items:
            print(f"[EXAM] Recovered {len(items)} complete '{key}' items from truncated response")
            return {key: items}

    return None

def _build_mcq_prompt(subjects: list, passages: list, count: int, avoid_questions: list = None) -> str:
    context = "\n\n".join(
        f"[{p['subject']} · {p['topic']}]\n{p['content']}" for p in passages
    )

    avoid_block = ""
    if avoid_questions:
        avoid_list = "\n".join(f"- {q}" for q in avoid_questions[:30] if q)
        avoid_block = f"""

AVOID REPEATING THESE — the student has already seen questions like these
recently (in this exam or past exams). Write genuinely DIFFERENT questions:
different numbers, different scenarios, different specific wording. Some
topic overlap is fine since the curriculum is fixed, but do not reuse the
same question almost word-for-word:
{avoid_list}"""

    english_instructions = ""
    if "English Language" in subjects:
        english_instructions = """

SPECIAL INSTRUCTIONS FOR ENGLISH LANGUAGE QUESTIONS:
Real WAEC English Language objective papers do NOT use generic vocabulary or
grammar questions. They are built from these specific question types — mix
across them instead of writing plain "choose the correct word" questions:

1. LEXIS AND STRUCTURE — a sentence with one underlined word/phrase. Options
   are near-synonyms or alternative structures; the student picks which one
   means the same thing or fits the sentence correctly.
   Example style: "The boy was reprimanded by his teacher. The underlined
   word means: (A) praised (B) scolded (C) ignored (D) promoted"

2. CLOZE TEST (gapped passage) — write ONE short passage (4-6 sentences)
   with 5 numbered blanks like ___(1)___, ___(2)___ etc, then ask one MCQ
   question per blank, each with 4 word/phrase options that could fill that
   specific blank. Put the full passage text in EVERY question's "question"
   field so each question is self-contained (repeat the passage each time),
   clearly marking which blank number that question is testing.

3. ORAL ENGLISH (phonetics/stress) — test which word has a different vowel
   or consonant sound from the other three, or which syllable carries the
   stress in a given word.
   Example style: "Which of the following words has the same vowel sound as
   the one represented in 'seat'? (A) sit (B) set (C) seed (D) said"

4. COMPREHENSION — write ONE short passage (5-8 sentences) about a Nigerian-
   relevant topic, then ask 3-4 MCQ questions about it (main idea, inference,
   vocabulary-in-context, detail). Put the full passage text in EVERY
   question's "question" field so each question is self-contained.

Spread English Language questions across these four types rather than
generating only one type repeatedly."""

    return f"""You are a WAEC exam question generator for Nigerian secondary school students.

Generate exactly {count} multiple choice questions for: {", ".join(subjects)}.

Curriculum reference:
---
{context}
---
{english_instructions}
{avoid_block}

Return ONLY valid JSON, no other text, no markdown:
{{
  "mcq": [
    {{
      "id": "mcq_1",
      "question": "question text",
      "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
      "answer": "A",
      "explanation": "one or two sentences explaining why that option is correct",
      "subject": "Mathematics",
      "topic": "topic name"
    }}
  ]
}}

Rules:
- Exactly 4 options per question (A, B, C, D)
- Always include a short "explanation" (1-2 plain sentences) saying why the correct option is right
- One correct answer only
- Realistic WAEC difficulty
- Spread across subjects evenly
- Do NOT include the answer in the question text"""

def _build_theory_prompt(subjects: list, passages: list, count: int, avoid_questions: list = None) -> str:
    context = "\n\n".join(
        f"[{p['subject']} · {p['topic']}]\n{p['content']}" for p in passages
    )

    avoid_block = ""
    if avoid_questions:
        avoid_list = "\n".join(f"- {q}" for q in avoid_questions[:30] if q)
        avoid_block = f"""

AVOID REPEATING THESE — the student has already seen questions like these
recently (in this exam or past exams). Write genuinely DIFFERENT questions:
{avoid_list}"""

    english_instructions = ""
    if "English Language" in subjects:
        english_instructions = """

SPECIAL INSTRUCTIONS FOR ENGLISH LANGUAGE THEORY QUESTIONS:
Real WAEC English Language essay paper does NOT ask generic "explain this
topic" questions. Use these real WAEC question types instead:
- ESSAY WRITING: a full essay prompt (narrative, descriptive, expository,
  or argumentative), e.g. "Write a story that ends with: ...peace finally
  returned to the village."
- LETTER WRITING: formal or informal letter prompt, e.g. "Write a letter to
  your local government chairman about the poor state of roads in your area."
- SUMMARY: ask the student to summarise a short passage (write the passage
  inside the question text) in a given number of sentences/words.
For these, "model_answer" should describe what a strong response covers
(structure, key points, tone) rather than a fixed factual answer."""

    return f"""You are a WAEC exam question generator for Nigerian secondary school students.

Generate exactly {count} theory/essay questions for: {", ".join(subjects)}.

Curriculum reference:
---
{context}
---
{english_instructions}
{avoid_block}

Return ONLY valid JSON, no other text, no markdown:
{{
  "theory": [
    {{
      "id": "th_1",
      "question": "theory question text",
      "model_answer": "what a complete answer should include",
      "subject": "Biology",
      "topic": "topic name",
      "marks": 10
    }}
  ]
}}

Rules:
- Each question should require a 5-10 sentence answer (except essay/letter
  writing for English, which should be longer per real WAEC expectations)
- Realistic WAEC essay style
- Spread across subjects"""


def _is_near_duplicate_question(new_q_text: str, existing_texts: list[str], threshold: float = 0.82) -> bool:
    """
    Checks whether new_q_text is substantially similar to any text already
    in existing_texts. Used both within a single exam (strict) and softly
    against the student's recent past exam questions (soft avoidance).
    """
    from difflib import SequenceMatcher
    import re
    normalized_new = re.sub(r'[^a-z0-9 ]+', '', new_q_text.lower()).strip()
    if not normalized_new:
        return False
    for existing in existing_texts:
        normalized_existing = re.sub(r'[^a-z0-9 ]+', '', existing.lower()).strip()
        if not normalized_existing:
            continue
        if SequenceMatcher(None, normalized_new, normalized_existing).ratio() >= threshold:
            return True
    return False


def _get_recent_question_texts(user_id: int, subjects: list[str], limit: int = 25) -> list[str]:
    """
    Pulls question text from the student's recent past exams (same subjects)
    so new generation can be steered away from repeating them too closely.
    This is a SOFT avoidance signal passed into the AI prompt, not a hard
    filter — some natural overlap/similarity across different exam sittings
    is expected and fine.
    """
    conn = _get_conn()
    rows = conn.execute(
        """SELECT questions, subjects FROM exam_sessions
           WHERE user_id = ? ORDER BY started_at DESC LIMIT 15""",
        (user_id,)
    ).fetchall()
    conn.close()

    texts = []
    for row in rows:
        try:
            row_subjects = json.loads(row["subjects"])
            if not (set(row_subjects) & set(subjects)):
                continue
            qs = json.loads(row["questions"])
            for q in qs.get("mcq", []):
                texts.append(q.get("question", ""))
            for q in qs.get("theory", []):
                texts.append(q.get("question", ""))
        except Exception:
            continue
        if len(texts) >= limit:
            break
    return texts[:limit]


@router.post("/start")
async def start_exam(req: ExamStartRequest, current_user: dict = Depends(require_user)):
    """Generate a new exam session with caching and batched generation."""

    if not req.subjects:
        raise HTTPException(400, "Select a subject.")
    if len(req.subjects) > 1:
        raise HTTPException(
            400,
            "You can only write one subject at a time. Please start a separate "
            "exam for each subject you want to practice."
        )
    invalid = [s for s in req.subjects if s not in SUBJECTS]
    if invalid:
        raise HTTPException(400, f"Unknown subjects: {invalid}")

    if req.mode not in EXAM_PRESETS:
        raise HTTPException(400, "mode must be one of: waec, quick, custom")

    # ── Free-tier monthly quota (premium users always pass) ───────────────────
    from billing import check_exam_quota
    allowed, quota_message = await asyncio.to_thread(check_exam_quota, current_user["id"])
    if not allowed:
        raise HTTPException(402, quota_message)

    preset = EXAM_PRESETS[req.mode]
    num_mcq        = req.num_mcq      if req.mode == "custom" else preset["num_mcq"]
    num_theory     = req.num_theory   if req.mode == "custom" else preset["num_theory"]
    duration       = req.duration_min if req.mode == "custom" else preset["duration_min"]
    theory_attempt = preset.get("theory_attempt", num_theory)

    if num_mcq <= 0 and num_theory <= 0:
        raise HTTPException(400, "An exam needs at least one MCQ or theory question.")

    # ── Check cache ────────────────────────────────────────────────────────────
    ckey = _cache_key(req.subjects, req.mode)
    cached = _question_cache.get(ckey)

    if cached and len(cached.get("mcq",[])) >= num_mcq and len(cached.get("theory",[])) >= num_theory:
        print(f"[EXAM] Cache hit for {ckey[:8]}... — shuffling")
        mcq_pool    = cached["mcq"].copy()
        theory_pool = cached["theory"].copy()
        random.shuffle(mcq_pool)
        random.shuffle(theory_pool)
        questions = {
            "mcq":    mcq_pool[:num_mcq],
            "theory": theory_pool[:num_theory]
        }
    else:
        # ── Batch generation: MCQ and theory separately ────────────────────────
        print(f"[EXAM] Generating {num_mcq} MCQ + {num_theory} theory for {req.subjects}")
        # Run the embedding search in a worker thread — it's CPU-bound and
        # would otherwise block other students' requests while it runs.
        passages = await asyncio.to_thread(_get_rag_context, req.subjects, min(30, num_mcq // 2 + 10))

        # Soft avoidance: pull recent past question texts for this student so
        # the prompt can steer the AI away from generating near-identical
        # questions to ones they've already seen in previous exams.
        recent_texts = await asyncio.to_thread(_get_recent_question_texts, current_user["id"], req.subjects)

        # Generate MCQ with retry + fill (batched in groups of 8 to avoid truncation)
        mcq_list = []
        mcq_texts_seen = []  # strict within-session dedup tracking
        max_mcq_attempts = max(6, (num_mcq // 8 + 1) * 3)  # extra headroom for dedup retries
        for attempt in range(max_mcq_attempts):
            needed = num_mcq - len(mcq_list)
            if needed <= 0:
                break
            # Cap batch size — generating too many MCQs in one call risks
            # truncation (hitting max_tokens) which produces invalid JSON.
            batch_size = min(needed, 8)
            try:
                avoid_list = (mcq_texts_seen + recent_texts)[:30]
                raw = await _call_ai(
                    _build_mcq_prompt(req.subjects, passages, batch_size, avoid_questions=avoid_list),
                    max_tokens=4000
                )
                data = _parse_json(raw)
                batch = data.get("mcq", [])

                accepted = 0
                for q in batch:
                    q_text = q.get("question", "")
                    # Strict within-session check — never allow a duplicate
                    # in the SAME exam set, regardless of similarity to past exams.
                    if _is_near_duplicate_question(q_text, mcq_texts_seen):
                        continue
                    q["id"] = f"mcq_{len(mcq_list) + 1}"
                    mcq_list.append(q)
                    mcq_texts_seen.append(q_text)
                    accepted += 1

                print(f"[EXAM] MCQ attempt {attempt+1}: got {len(batch)}, accepted {accepted} (deduped {len(batch)-accepted}), total {len(mcq_list)}/{num_mcq}")
            except Exception as e:
                print(f"[EXAM] MCQ attempt {attempt+1} failed: {e}")
        if num_mcq > 0 and not mcq_list:
            raise HTTPException(500, "Could not generate MCQ questions after multiple attempts. Try again.")

        # Generate theory with retry
        theory_list = []
        theory_texts_seen = []
        max_theory_attempts = max(5, num_theory + 3)
        for attempt in range(max_theory_attempts):
            needed = num_theory - len(theory_list)
            if needed <= 0:
                break
            try:
                avoid_list = (theory_texts_seen + recent_texts)[:30]
                raw = await _call_ai(
                    _build_theory_prompt(req.subjects, passages, needed, avoid_questions=avoid_list),
                    max_tokens=2500
                )
                data = _parse_json(raw)
                batch = data.get("theory", [])

                accepted = 0
                for q in batch:
                    q_text = q.get("question", "")
                    if _is_near_duplicate_question(q_text, theory_texts_seen):
                        continue
                    q["id"] = f"th_{len(theory_list) + 1}"
                    theory_list.append(q)
                    theory_texts_seen.append(q_text)
                    accepted += 1

                print(f"[EXAM] Theory attempt {attempt+1}: got {len(batch)}, accepted {accepted} (deduped {len(batch)-accepted}), total {len(theory_list)}/{num_theory}")
            except Exception as e:
                print(f"[EXAM] Theory attempt {attempt+1} failed: {e}")
        if num_theory > 0 and not theory_list:
            raise HTTPException(500, "Could not generate theory questions after multiple attempts. Try again.")

        questions = {"mcq": mcq_list, "theory": theory_list}

        # Cache for next time (store a bigger pool for WAEC mode)
        _question_cache[ckey] = questions.copy()
        print(f"[EXAM] Cached {len(mcq_list)} MCQ + {len(theory_list)} theory")

    # ── Save session ───────────────────────────────────────────────────────────
    def _save():
        conn = _get_conn()
        cursor = conn.execute(
            "INSERT INTO exam_sessions (user_id, subjects, questions, duration_min, coach_mode) VALUES (?, ?, ?, ?, ?) RETURNING id",
            (current_user["id"], json.dumps(req.subjects), json.dumps(questions), duration, int(req.coach_mode))
        )
        sid = cursor.lastrowid
        conn.commit()
        conn.close()
        return sid

    session_id = await asyncio.to_thread(_save)

    return {
        "session_id":    session_id,
        "mode":          req.mode,
        "mode_label":    preset["label"],
        "duration_min":  duration,
        "theory_attempt": theory_attempt,
        "questions":     questions,
        "coach_mode":    req.coach_mode,
        "started_at":    datetime.utcnow().isoformat(),
        "from_cache":    bool(cached),
    }


@router.get("/presets")
def get_presets():
    return {"presets": EXAM_PRESETS}


@router.post("/submit")
async def submit_exam(req: ExamSubmitRequest, current_user: dict = Depends(require_user)):
    """Submit answers, auto-mark MCQ, AI-mark theory, return full results."""

    def _fetch_session():
        conn = _get_conn()
        r = conn.execute(
            "SELECT * FROM exam_sessions WHERE id = ? AND user_id = ?",
            (req.session_id, current_user["id"])
        ).fetchone()
        conn.close()
        return r

    # Blocking DB call pushed to a worker thread — async def route, real
    # concurrent load would otherwise stall every other in-flight request.
    row = await asyncio.to_thread(_fetch_session)

    if not row:
        raise HTTPException(404, "Exam session not found.")
    if row["submitted_at"]:
        raise HTTPException(400, "This exam has already been submitted.")

    questions = json.loads(row["questions"])

    # ── Auto-mark MCQ ──────────────────────────────────────────────────────────
    mcq_results = []
    mcq_score = 0
    mcq_max = len(questions.get("mcq", []))

    timings = req.timings or {}
    for q in questions.get("mcq", []):
        student_ans = req.answers.get(q["id"], "").strip().upper()
        correct = q["answer"].strip().upper()
        is_correct = student_ans == correct
        if is_correct:
            mcq_score += 1
        mcq_results.append({
            "id": q["id"],
            "question": q["question"],
            "options": q.get("options", {}),
            "your_answer": student_ans,
            "correct_answer": correct,
            "correct": is_correct,
            "explanation": q.get("explanation", ""),
            "subject": q["subject"],
            "topic": q["topic"],
            "time_seconds": timings.get(q["id"]),
        })

    # ── AI-mark theory ─────────────────────────────────────────────────────────
    theory_results = []
    theory_score = 0
    theory_max = sum(q.get("marks", 10) for q in questions.get("theory", []))
    theory_marking_failed = False

    if questions.get("theory"):
        marking_prompt = _build_marking_prompt(questions["theory"], req.answers)
        marking = None

        # Try twice before giving up - a single malformed JSON response
        # (truncated output, a stray comment, etc.) shouldn't be enough to
        # cost a student their entire theory score.
        for attempt in range(2):
            raw = ""
            try:
                raw = await _call_ai(marking_prompt, max_tokens=2000)
                clean = raw.strip()
                if clean.startswith("```"):
                    clean = clean.split("```")[1]
                    if clean.startswith("json"):
                        clean = clean[4:]
                marking = json.loads(clean)
                break
            except Exception as e:
                print(f"[EXAM] Theory marking attempt {attempt + 1} failed: {e}")
                marking = None

        theory_map = {q["id"]: q for q in questions["theory"]}
        if marking is not None:
            for r in marking.get("results", []):
                theory_score += r.get("score", 0)
                theory_results.append({
                    "id": r["id"],
                    "question": theory_map.get(r["id"], {}).get("question", ""),
                    "your_answer": req.answers.get(r["id"], "[No answer]"),
                    "score": r.get("score", 0),
                    "max": r.get("max", 10),
                    "feedback": r.get("feedback", ""),
                    "model_answer": theory_map.get(r["id"], {}).get("model_answer", ""),
                    "subject": theory_map.get(r["id"], {}).get("subject", ""),
                })
        else:
            # Both attempts failed to produce parseable marking. Do NOT
            # silently score this as 0 - a marking failure is not the same
            # thing as a wrong answer, and folding it into total_score as a
            # 0 would unfairly tank the student's grade for something that
            # was never actually assessed. Instead: score=None per question,
            # exclude theory entirely from total_max below, and say plainly
            # that this needs a manual look.
            theory_marking_failed = True
            for q in questions["theory"]:
                theory_results.append({
                    "id": q["id"],
                    "question": q.get("question", ""),
                    "your_answer": req.answers.get(q["id"], "[No answer]"),
                    "score": None,
                    "max": q.get("marks", 10),
                    "feedback": "Could not be auto-marked right now. This won't "
                                "count against your score - it will need a manual "
                                "review.",
                    "model_answer": q.get("model_answer", ""),
                    "subject": q.get("subject", ""),
                })

    # ── Final score ────────────────────────────────────────────────────────────
    # If theory marking failed, exclude it from both sides of the percentage
    # so an infrastructure hiccup can't drag down the student's grade - the
    # percentage below reflects MCQ only in that case (see theory_marking_failed).
    if theory_marking_failed:
        total_score = mcq_score
        total_max = mcq_max
    else:
        total_score = mcq_score + theory_score
        total_max = mcq_max + theory_max
    percentage = round((total_score / total_max * 100) if total_max else 0, 1)

    # Official WAEC grading scale
    WAEC_GRADES = [
        (75, "A1", "Excellent",   True,  "You are sharp! A1 is the highest grade in WAEC. Universities and scholarships will be chasing you."),
        (70, "B2", "Very Good",   True,  "Very good performance! B2 is highly respected and opens doors to competitive courses."),
        (65, "B3", "Good",        True,  "Good result! B3 is a solid credit pass — you clearly understand the material."),
        (60, "C4", "Credit",      True,  "Credit pass! C4 meets university admission requirements. Keep pushing for better."),
        (55, "C5", "Credit",      True,  "Credit pass. C5 qualifies you for most university programmes — well done."),
        (50, "C6", "Credit",      True,  "C6 is the minimum credit pass for WAEC. You made it, but you can do better with more practice."),
        (45, "D7", "Pass",        False, "D7 is a pass but NOT a credit. Most universities won't accept this — you need to aim for C6 or above."),
        (40, "E8", "Pass",        False, "E8 is a pass but NOT a credit. Please study harder — especially if this is Maths or English."),
        (0,  "F9", "Fail",        False, "F9 means you need to retake this subject. Don't be discouraged — identify your weak areas and try again."),
    ]

    grade = "F9"
    grade_label = "Fail"
    is_credit = False
    grade_feedback = ""
    for (min_pct, g, label, credit, msg) in WAEC_GRADES:
        if percentage >= min_pct:
            grade = g
            grade_label = label
            is_credit = credit
            grade_feedback = msg
            break

    credit_status = "CREDIT PASS ✓" if is_credit else "NOT A CREDIT — retake recommended"

    feedback_summary = (
        f"You scored {total_score:.1f}/{total_max} ({percentage}%) — "
        f"{grade} ({grade_label}) · {credit_status}. {grade_feedback}"
    )
    if theory_marking_failed:
        feedback_summary += (
            " (Note: your theory answers couldn't be auto-marked this time, so "
            "this grade reflects the MCQ section only. Your theory answers are "
            "saved and will need manual review.)"
        )

    # Save results to DB
    def _save_results():
        conn = _get_conn()
        conn.execute(
            """UPDATE exam_sessions
               SET answers=?, timings=?, score=?, max_score=?, feedback=?, submitted_at=now_iso()
               WHERE id=?""",
            (json.dumps(req.answers), json.dumps(timings), total_score, total_max, feedback_summary, req.session_id)
        )
        conn.commit()
        conn.close()

    await asyncio.to_thread(_save_results)

    # ── AI Exam Coach stats — speed + accuracy per question, only if timing data given ──
    coach_stats = None
    if timings:
        times = [t for t in timings.values() if isinstance(t, (int, float)) and t > 0]
        if times:
            avg_time = round(sum(times) / len(times), 1)
            fastest  = round(min(times), 1)
            slowest  = round(max(times), 1)
            # Flag questions answered too fast (likely guessed) or too slow (struggled)
            rushed_ids   = [qid for qid, t in timings.items() if t and t < avg_time * 0.4]
            slow_ids     = [qid for qid, t in timings.items() if t and t > avg_time * 2]
            coach_stats = {
                "avg_seconds_per_question": avg_time,
                "fastest_seconds": fastest,
                "slowest_seconds": slowest,
                "total_time_seconds": round(sum(times), 1),
                "rushed_question_ids": rushed_ids,
                "slow_question_ids": slow_ids,
            }

    return {
        "session_id": req.session_id,
        "total_score": total_score,
        "total_max": total_max,
        "percentage": percentage,
        "grade": grade,
        "summary": feedback_summary,
        "theory_marking_failed": theory_marking_failed,
        "mcq": {"score": mcq_score, "max": mcq_max, "results": mcq_results},
        "theory": {
            "score": None if theory_marking_failed else theory_score,
            "max": theory_max,
            "results": theory_results,
        },
        "coach_stats": coach_stats,
    }


@router.get("/history")
def exam_history(current_user: dict = Depends(require_user)):
    """Return past exam sessions for the student."""
    conn = _get_conn()
    rows = conn.execute(
        """SELECT id, subjects, score, max_score, started_at, submitted_at, duration_min
           FROM exam_sessions WHERE user_id = ? ORDER BY started_at DESC LIMIT 20""",
        (current_user["id"],)
    ).fetchall()
    conn.close()

    results = []
    for r in rows:
        pct = round(r["score"] / r["max_score"] * 100, 1) if r["score"] and r["max_score"] else None
        results.append({
            "id": r["id"],
            "subjects": json.loads(r["subjects"]),
            "score": r["score"],
            "max_score": r["max_score"],
            "percentage": pct,
            "started_at": r["started_at"],
            "submitted_at": r["submitted_at"],
            "duration_min": r["duration_min"],
        })
    return {"exams": results}


@router.get("/review/{session_id}")
def review_exam(session_id: int, current_user: dict = Depends(require_user)):
    """
    Return the full saved questions + answers + timing for a past exam,
    so the student can go over it again without regenerating anything.
    """
    conn = _get_conn()
    row = conn.execute(
        "SELECT * FROM exam_sessions WHERE id = ? AND user_id = ?",
        (session_id, current_user["id"])
    ).fetchone()
    conn.close()

    if not row:
        raise HTTPException(404, "Exam not found.")

    questions = json.loads(row["questions"])
    answers   = json.loads(row["answers"]) if row["answers"] else {}
    timings   = json.loads(row["timings"]) if row["timings"] else {}

    # Re-mark MCQ for display (cheap, no AI call needed)
    mcq_results = []
    for q in questions.get("mcq", []):
        student_ans = answers.get(q["id"], "").strip().upper()
        correct = q["answer"].strip().upper()
        mcq_results.append({
            "id": q["id"],
            "question": q["question"],
            "options": q.get("options", {}),
            "your_answer": student_ans,
            "correct_answer": correct,
            "correct": student_ans == correct,
            "explanation": q.get("explanation", ""),
            "subject": q["subject"],
            "topic": q["topic"],
            "time_seconds": timings.get(q["id"]),
        })

    theory_results = []
    for q in questions.get("theory", []):
        theory_results.append({
            "id": q["id"],
            "question": q["question"],
            "your_answer": answers.get(q["id"], "[No answer]"),
            "model_answer": q.get("model_answer", ""),
            "subject": q["subject"],
            "marks": q.get("marks", 10),
        })

    pct = round(row["score"] / row["max_score"] * 100, 1) if row["score"] and row["max_score"] else None

    return {
        "session_id": row["id"],
        "subjects": json.loads(row["subjects"]),
        "score": row["score"],
        "max_score": row["max_score"],
        "percentage": pct,
        "started_at": row["started_at"],
        "submitted_at": row["submitted_at"],
        "mcq_results": mcq_results,
        "theory_results": theory_results,
        "coach_mode": bool(row["coach_mode"]) if row["coach_mode"] is not None else False,
    }


# ══════════════════════════════════════════════════════════════════════════
# ON-PAGE EXPLANATION (for "Explain this" button on results page)
# ══════════════════════════════════════════════════════════════════════════

class ExplainRequest(BaseModel):
    question: str
    options: Optional[dict] = None     # {"A": "...", "B": "...", ...} for MCQ
    correct_answer: str
    your_answer: Optional[str] = ""
    subject: str = ""


@router.post("/explain")
async def explain_question(req: ExplainRequest, current_user: dict = Depends(require_user)):
    """
    Explain why an answer is correct, returned directly (not via /chat),
    so the results page can show it inline without redirecting the student.
    """
    options_block = ""
    if req.options:
        options_block = "\n".join(f"{k}. {v}" for k, v in req.options.items())

    prompt = f"""You are NaijaSensei, a warm Nigerian secondary school tutor.

A student got this {req.subject} question wrong in a practice exam. Explain
clearly why the correct answer is right, and briefly why their answer (if
given) was wrong. Keep it to 3-5 sentences, plain flowing English, no
markdown, no bullet points, no headers — just a teacher explaining out loud.

Question: {req.question}
{options_block}

Correct answer: {req.correct_answer}
Student's answer: {req.your_answer or "[No answer given]"}
"""

    try:
        explanation = await call_ai_with_fallback(prompt, max_tokens=400)
        return {"explanation": explanation.strip()}
    except Exception as e:
        print(f"[EXAM] Explain failed: {e}")
        raise HTTPException(500, "Could not generate explanation right now. Please try again.")