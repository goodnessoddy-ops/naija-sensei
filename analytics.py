"""
analytics.py — Performance Analytics + Study Plan Generator for NaijaSensei

Endpoints:
  GET  /analytics/performance   -> subject breakdown, strengths, weak areas
  POST /analytics/study-plan    -> AI-generated personalised study plan

Now uses the shared 32-provider fallback chain from ai_providers.py
instead of a standalone Groq -> Gemini chain.
"""

import os
import json
from datetime import datetime, date
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from auth import require_user, _get_conn
from ai_providers import stream_simple_with_fallback

router = APIRouter(prefix="/analytics", tags=["analytics"])


def compute_topic_mastery(user_id: int) -> dict:
    """
    Returns {subject: {topic: {"correct": n, "total": n, "pct": float}}}
    computed from every completed exam_sessions row for this student.
    Shared by: the /chat system prompt (so Mr. Sensei knows what a student
    is weak on), the topic-mastery page endpoint, and get_performance()
    below (which aggregates this further to subject level).
    """
    conn = _get_conn()
    rows = conn.execute(
        """SELECT questions, answers FROM exam_sessions
           WHERE user_id = ? AND submitted_at IS NOT NULL""",
        (user_id,)
    ).fetchall()
    conn.close()

    mastery: dict = {}
    for row in rows:
        try:
            questions = json.loads(row["questions"])
            answers = json.loads(row["answers"]) if row["answers"] else {}
        except Exception:
            continue
        for q in questions.get("mcq", []):
            subj = q.get("subject", "Unknown")
            topic = q.get("topic", "Unknown")
            entry = mastery.setdefault(subj, {}).setdefault(topic, {"correct": 0, "total": 0})
            entry["total"] += 1
            student_ans = answers.get(q["id"], "").strip().upper()
            correct_ans = q.get("answer", "").strip().upper()
            if student_ans == correct_ans:
                entry["correct"] += 1

    for subj in mastery:
        for topic in mastery[subj]:
            t = mastery[subj][topic]
            t["pct"] = round(t["correct"] / t["total"] * 100, 1) if t["total"] else 0.0
    return mastery


def summarize_mastery_for_prompt(mastery: dict, max_topics: int = 5) -> str:
    """
    Compresses compute_topic_mastery()'s output into a short block of text
    for injection into the /chat system prompt - just the weakest topics
    (below 60%, with at least 2 questions attempted so one lucky/unlucky
    guess doesn't skew it), sorted worst-first, capped at max_topics.
    Returns "" if there's nothing weak enough to be worth mentioning.
    """
    weak = []
    for subj, topics in mastery.items():
        for topic, stats in topics.items():
            if stats["total"] >= 2 and stats["pct"] < 60:
                weak.append((stats["pct"], subj, topic, stats["correct"], stats["total"]))
    if not weak:
        return ""
    weak.sort(key=lambda x: x[0])
    lines = [f"- {subj} / {topic}: {correct}/{total} correct ({pct}%)"
             for pct, subj, topic, correct, total in weak[:max_topics]]
    return "\n".join(lines)


# -- Performance analytics ------------------------------------------------------
@router.get("/performance")
def get_performance(current_user: dict = Depends(require_user)):
    """
    Analyse all exam results for a student.
    Returns per-subject scores, strengths, weak areas, and trend over time.
    """
    conn = _get_conn()
    rows = conn.execute(
        """SELECT questions, answers, score, max_score, subjects, started_at, submitted_at
           FROM exam_sessions
           WHERE user_id = ? AND submitted_at IS NOT NULL
           ORDER BY started_at ASC""",
        (current_user["id"],)
    ).fetchall()
    conn.close()

    if not rows:
        return {"has_data": False, "message": "No completed exams yet. Take some exams to see your analytics!"}

    # -- Per-subject breakdown ---------------------------------------------------
    subject_stats = {}   # subject -> {correct, total, topics_wrong}

    for row in rows:
        try:
            questions = json.loads(row["questions"])
            answers   = json.loads(row["answers"]) if row["answers"] else {}
        except:
            continue

        for q in questions.get("mcq", []):
            subj  = q.get("subject", "Unknown")
            topic = q.get("topic", "Unknown")
            if subj not in subject_stats:
                subject_stats[subj] = {"correct": 0, "total": 0, "wrong_topics": {}}
            subject_stats[subj]["total"] += 1
            student_ans = answers.get(q["id"], "").strip().upper()
            correct_ans = q.get("answer", "").strip().upper()
            if student_ans == correct_ans:
                subject_stats[subj]["correct"] += 1
            else:
                subject_stats[subj]["wrong_topics"][topic] = \
                    subject_stats[subj]["wrong_topics"].get(topic, 0) + 1

    # -- Score trend ---------------------------------------------------------------
    trend = []
    for row in rows:
        if row["score"] is not None and row["max_score"]:
            pct = round(row["score"] / row["max_score"] * 100, 1)
            trend.append({
                "date": row["started_at"][:10] if row["started_at"] else "",
                "percentage": pct,
                "subjects": json.loads(row["subjects"]) if row["subjects"] else []
            })

    # -- Build per-subject summary --------------------------------------------------
    subjects_summary = []
    for subj, stats in subject_stats.items():
        if stats["total"] == 0:
            continue
        pct = round(stats["correct"] / stats["total"] * 100, 1)
        top_wrong = sorted(stats["wrong_topics"].items(), key=lambda x: x[1], reverse=True)[:3]
        subjects_summary.append({
            "subject": subj,
            "percentage": pct,
            "correct": stats["correct"],
            "total": stats["total"],
            "weak_topics": [t for t, _ in top_wrong],
            "status": "strong" if pct >= 65 else "needs_work" if pct >= 45 else "weak"
        })

    subjects_summary.sort(key=lambda x: x["percentage"], reverse=True)

    strong = [s for s in subjects_summary if s["status"] == "strong"]
    weak   = [s for s in subjects_summary if s["status"] in ("needs_work", "weak")]

    # -- Overall stats ---------------------------------------------------------------
    total_exams = len(rows)
    if trend:
        avg_score    = round(sum(t["percentage"] for t in trend) / len(trend), 1)
        best_score   = max(t["percentage"] for t in trend)
        latest_score = trend[-1]["percentage"]
        improving    = len(trend) >= 2 and trend[-1]["percentage"] > trend[-2]["percentage"]
    else:
        avg_score = best_score = latest_score = 0
        improving = False

    # -- Weekly improvement: this week's avg vs the week before ---------------------
    now = datetime.utcnow()
    this_week, last_week = [], []
    for t in trend:
        if not t["date"]:
            continue
        try:
            days_ago = (now - datetime.fromisoformat(t["date"])).days
        except Exception:
            continue
        if 0 <= days_ago <= 7:
            this_week.append(t["percentage"])
        elif 7 < days_ago <= 14:
            last_week.append(t["percentage"])
    this_week_avg = round(sum(this_week) / len(this_week), 1) if this_week else None
    last_week_avg = round(sum(last_week) / len(last_week), 1) if last_week else None
    weekly_improvement = (
        round(this_week_avg - last_week_avg, 1)
        if (this_week_avg is not None and last_week_avg is not None) else None
    )

    # -- Average response time per question, derived from existing exam ------------
    # timestamps (started_at/submitted_at) - no new instrumentation needed,
    # since this app doesn't track true per-question timing, this is total
    # exam duration divided by question count, averaged across exams.
    response_times = []
    for row in rows:
        try:
            if not (row["started_at"] and row["submitted_at"]):
                continue
            start = datetime.fromisoformat(row["started_at"])
            end = datetime.fromisoformat(row["submitted_at"])
            duration_sec = (end - start).total_seconds()
            q_count = len(json.loads(row["questions"]).get("mcq", []))
            if q_count > 0 and 0 < duration_sec < 6 * 3600:  # sanity cap: ignore exams left open >6h
                response_times.append(duration_sec / q_count)
        except Exception:
            continue
    avg_response_time_seconds = round(sum(response_times) / len(response_times), 1) if response_times else None

    # -- Anonymized rank percentile among other students ----------------------------
    rank_info = _compute_rank_percentile(current_user["id"], avg_score if trend else None)

    return {
        "has_data": True,
        "overall": {
            "total_exams": total_exams,
            "avg_score": avg_score,
            "best_score": best_score,
            "latest_score": latest_score,
            "improving": improving,
            "weekly_improvement": weekly_improvement,
            "avg_response_time_seconds": avg_response_time_seconds,
            "rank_percentile": rank_info["percentile"],
            "total_students_compared": rank_info["total_students_compared"],
        },
        "subjects": subjects_summary,
        "strong_subjects": [s["subject"] for s in strong],
        "weak_subjects":   [s["subject"] for s in weak],
        "weak_topics":     {s["subject"]: s["weak_topics"] for s in weak if s["weak_topics"]},
        "trend": trend[-10:],
    }


def _compute_rank_percentile(user_id: int, my_avg_score) -> dict:
    """
    This student's percentile position among all OTHER students who have
    exam data, fully anonymized - no other student's identity or score is
    ever exposed, only this student's own relative position. Requires at
    least 3 other students with data; with fewer than that, a percentile
    would be misleading (e.g. "100th percentile" out of one other student
    means nothing), so it returns None instead of a fake-precise number.
    """
    if my_avg_score is None:
        return {"percentile": None, "total_students_compared": 0}
    conn = _get_conn()
    all_rows = conn.execute(
        """SELECT user_id, score, max_score FROM exam_sessions
           WHERE submitted_at IS NOT NULL AND score IS NOT NULL AND max_score > 0"""
    ).fetchall()
    conn.close()

    from collections import defaultdict
    student_scores = defaultdict(list)
    for r in all_rows:
        student_scores[r["user_id"]].append(r["score"] / r["max_score"] * 100)
    student_avgs = {uid: sum(scores) / len(scores) for uid, scores in student_scores.items() if scores}

    others = {uid: avg for uid, avg in student_avgs.items() if uid != user_id}
    if len(others) < 3:
        return {"percentile": None, "total_students_compared": len(student_avgs)}

    better_or_equal = sum(1 for avg in others.values() if avg <= my_avg_score)
    percentile = round(better_or_equal / len(others) * 100)
    return {"percentile": percentile, "total_students_compared": len(student_avgs)}


@router.get("/topic-mastery")
def get_topic_mastery(subject: str, topic: str, current_user: dict = Depends(require_user)):
    """
    For one specific (subject, topic): this student's own performance on
    it (from their exam history) plus the actual curriculum content for
    it - pulled via the same fuzzy topic-match retrieval rag.py's chat
    uses, so what's shown here genuinely reflects what the AI would
    ground an answer in for this topic, not a separate/different lookup.
    """
    from rag import search, _topic_match_score

    mastery = compute_topic_mastery(current_user["id"])
    stats = mastery.get(subject, {}).get(topic, {"correct": 0, "total": 0, "pct": 0.0})

    # Exam question topic tags don't always exactly match the topic string
    # a student clicked (e.g. admin topic "Quadratic Equations" vs an exam
    # tag of "Quadratics") - fall back to the closest fuzzy match within
    # the same subject before concluding there's no exam data at all.
    matched_topic_label = topic
    if stats["total"] == 0 and subject in mastery:
        best_variant, best_score = None, 0.0
        for t, s in mastery[subject].items():
            score = _topic_match_score(topic, t)
            if score > best_score:
                best_score, best_variant = score, t
        if best_variant and best_score >= 0.5:
            stats = mastery[subject][best_variant]
            matched_topic_label = best_variant

    passages = search(topic, top_k=5, subject=subject, topic=topic)
    content = [
        {"topic": p["topic"], "grade": p["grade"], "content": p["content"]}
        for p in passages
    ]

    return {
        "subject": subject,
        "topic": topic,
        "mastery": stats,
        "has_exam_data": stats["total"] > 0,
        "matched_topic_label": matched_topic_label if stats["total"] > 0 else None,
        "content": content,
    }


# -- Study plan generator ---------------------------------------------------------
class StudyPlanRequest(BaseModel):
    exam_date:        str
    target_subjects:  list[str]
    hours_per_day:    int = 3


@router.post("/study-plan")
def generate_study_plan(req: StudyPlanRequest, current_user: dict = Depends(require_user)):
    """Generate a personalised WAEC study plan based on performance data."""

    perf = get_performance(current_user)

    try:
        exam_dt   = date.fromisoformat(req.exam_date)
        days_left = (exam_dt - date.today()).days
        if days_left < 1:
            days_left = 90
    except:
        days_left = 90

    weak_topics = perf.get("weak_topics", {}) if perf.get("has_data") else {}
    strong_subj = perf.get("strong_subjects", []) if perf.get("has_data") else []
    weak_subj   = perf.get("weak_subjects", [])   if perf.get("has_data") else req.target_subjects

    # weak_subj is always list[str] here: it's either perf["weak_subjects"]
    # (built as [s["subject"] for s in weak] in get_performance, so already
    # flattened to plain strings) or req.target_subjects (also list[str]).
    weak_subj_str = ", ".join(str(s) for s in weak_subj) if weak_subj else "None identified yet"

    prompt = f"""You are a WAEC study coach for a Nigerian secondary school student.

Generate a detailed personalised study plan based on this data:

Student profile:
- Days until WAEC exam: {days_left} days
- Study hours available per day: {req.hours_per_day} hours
- Target subjects: {", ".join(req.target_subjects) if req.target_subjects else "All WAEC subjects"}
- Strong subjects (less time needed): {", ".join(strong_subj) if strong_subj else "None identified yet"}
- Weak subjects (needs most attention): {weak_subj_str}
- Specific weak topics: {json.dumps(weak_topics) if weak_topics else "Not enough data yet"}

Create a week-by-week study plan. For each week:
1. List which subjects to focus on
2. Specific topics to cover
3. Daily time allocation
4. What to do on weekends (revision or rest)
5. One motivational tip for that week

Format it clearly with week headers. Use simple English a Nigerian SS3 student understands.
Be specific - mention actual WAEC topics like "Quadratic equations", "Organic Chemistry nomenclature", etc.
Keep it realistic for {req.hours_per_day} hours/day.
End with 3 WAEC exam day tips.

Do NOT use markdown headers like ## or **. Use plain text with clear sections.
"""

    async def generate():
        try:
            async for tag, piece in stream_simple_with_fallback(prompt, max_tokens=2000):
                yield f"data: {json.dumps({'text': piece, 'mode': tag})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            print(f"[STUDY-PLAN] All providers failed: {e}")
            yield f"data: {json.dumps({'text': 'Our AI tutor is resting right now. Please come back in 5 minutes and try again! \U0001F60A', 'error': True})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")