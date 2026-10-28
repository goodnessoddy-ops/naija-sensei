"""
career.py — Career & Scholarship Guidance for NaijaSensei.

Two parts:
1. Nigerian scholarships and career paths database — DB-backed, editable
   via admin CRUD routes below, seeded once from the lists further down
   the first time this runs against an empty database. Previously these
   were hardcoded Python lists with no way to update a stale link or add
   a new scholarship without a full redeploy — now an admin can edit them
   live, and the AI guidance below picks up those edits automatically
   since it reads from the same table.
2. AI guidance personalised to the student's actual performance data
"""

import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from auth import require_user, _get_conn
from ai_providers import call_ai_with_fallback

router = APIRouter(prefix="/career", tags=["career"])

# ── Seed data: loaded into the DB once on first startup (see
# init_career_db below) if the tables are empty. After that, this data
# lives in the scholarships / career_paths tables and these lists are
# never read again — edit via the admin routes below, not by editing
# this file. ─────────────────────────────────────────────────────────────

_SEED_SCHOLARSHIPS = [
    {
        "id": "ptdf",
        "name": "PTDF Scholarship",
        "body": "Petroleum Technology Development Fund",
        "level": "Undergraduate & Postgraduate",
        "subjects": ["Physics", "Chemistry", "Mathematics", "Biology"],
        "description": "Full scholarship for science and engineering students studying in Nigerian and foreign universities. Covers tuition, accommodation, and stipend.",
        "link": "https://ptdf.gov.ng",
        "type": "Federal Government",
    },
    {
        "id": "agbami",
        "name": "Agbami Medical & Engineering Scholarship",
        "body": "Stardeep Petroleum / Chevron",
        "level": "Undergraduate",
        "subjects": ["Physics", "Chemistry", "Mathematics", "Biology"],
        "description": "Covers medicine, pharmacy, nursing, and engineering courses. Requires minimum of 5 credits including English and Mathematics at WAEC.",
        "link": "https://www.agbamischolarship.com",
        "type": "Oil & Gas",
    },
    {
        "id": "nlng",
        "name": "NLNG Scholarship",
        "body": "Nigeria LNG Limited",
        "level": "Undergraduate & Postgraduate",
        "subjects": ["Physics", "Chemistry", "Mathematics"],
        "description": "One of Nigeria's most prestigious scholarships. Covers all science, engineering, and technology courses at Nigerian universities.",
        "link": "https://www.nlng.com",
        "type": "Oil & Gas",
    },
    {
        "id": "tetfund",
        "name": "TETFund Scholarship",
        "body": "Tertiary Education Trust Fund",
        "level": "Postgraduate",
        "subjects": [],
        "description": "For Nigerian academics and postgraduate students. Funds Masters and PhD programmes locally and abroad.",
        "link": "https://tetfund.gov.ng",
        "type": "Federal Government",
    },
    {
        "id": "seplat",
        "name": "Seplat Energy Scholarship",
        "body": "Seplat Energy PLC",
        "level": "Undergraduate",
        "subjects": ["Physics", "Chemistry", "Mathematics"],
        "description": "Supports science and engineering students from Niger Delta communities. Covers tuition and living expenses.",
        "link": "https://www.seplatpetroleum.com",
        "type": "Oil & Gas",
    },
    {
        "id": "edo_state",
        "name": "Edo State Merit Scholarship",
        "body": "Edo State Government",
        "level": "Undergraduate",
        "subjects": [],
        "description": "Merit-based scholarship for Edo State indigenes with outstanding WAEC results. Open to all courses.",
        "link": "https://www.edostate.gov.ng",
        "type": "State Government",
    },
    {
        "id": "commonwealth",
        "name": "Commonwealth Scholarship",
        "body": "Commonwealth Scholarship Commission",
        "level": "Postgraduate",
        "subjects": [],
        "description": "Fully-funded Masters and PhD study in the UK for Nigerian citizens. Competitive but open to all disciplines.",
        "link": "https://cscuk.fcdo.gov.uk",
        "type": "International",
    },
    {
        "id": "mastercard",
        "name": "Mastercard Foundation Scholars Program",
        "body": "Mastercard Foundation",
        "level": "Undergraduate",
        "subjects": [],
        "description": "Full scholarship for economically disadvantaged but academically talented young Africans. Open to all courses at partner universities.",
        "link": "https://mastercardfdn.org/all/scholars",
        "type": "International",
    },
    {
        "id": "oando",
        "name": "Oando Foundation Scholarship",
        "body": "Oando Foundation",
        "level": "Secondary & Undergraduate",
        "subjects": ["Mathematics", "Physics", "Chemistry"],
        "description": "Supports STEM education from secondary school level through to university for talented students.",
        "link": "https://www.oandofoundation.org",
        "type": "Oil & Gas",
    },
]

_SEED_CAREERS = [
    {
        "id": "medical_doctor",
        "career": "Medical Doctor / Surgeon",
        "required_subjects": ["Biology", "Chemistry", "Physics", "Mathematics", "English Language"],
        "min_credits": 5,
        "university_course": "Medicine and Surgery (MBBS)",
        "description": "One of Nigeria's most respected professions. Requires strong sciences at WAEC and JAMB. Training takes 6 years.",
        "avg_salary_range": "₦500,000 – ₦2,000,000/month (senior specialist)",
        "job_market": "Strong demand in Nigeria and abroad",
    },
    {
        "id": "software_engineer",
        "career": "Software Engineer / Developer",
        "required_subjects": ["Mathematics", "Physics", "English Language"],
        "min_credits": 3,
        "university_course": "Computer Science, Software Engineering, or related",
        "description": "Nigeria's tech sector is booming. Strong Mathematics and logical thinking are key. Many self-taught routes also exist.",
        "avg_salary_range": "₦200,000 – ₦2,000,000+/month (tech companies)",
        "job_market": "Very high demand locally and internationally (remote work opportunities)",
    },
    {
        "id": "civil_engineer",
        "career": "Civil / Structural Engineer",
        "required_subjects": ["Mathematics", "Physics", "Chemistry", "English Language"],
        "min_credits": 4,
        "university_course": "Civil Engineering",
        "description": "Nigeria's infrastructure boom means strong demand for civil engineers in construction, roads, and bridges.",
        "avg_salary_range": "₦150,000 – ₦800,000/month",
        "job_market": "High demand, especially in construction and government projects",
    },
    {
        "id": "lawyer",
        "career": "Lawyer / Legal Practitioner",
        "required_subjects": ["English Language", "Literature in English", "Government", "Economics"],
        "min_credits": 5,
        "university_course": "Law (LLB)",
        "description": "Requires strong English and humanities at WAEC. Law school follows after a 5-year LLB programme.",
        "avg_salary_range": "₦100,000 – ₦5,000,000/month (senior counsel)",
        "job_market": "Competitive but strong demand in corporate, oil & gas, and human rights sectors",
    },
    {
        "id": "accountant",
        "career": "Accountant / Financial Analyst",
        "required_subjects": ["Mathematics", "Economics", "Commerce", "English Language"],
        "min_credits": 4,
        "university_course": "Accounting, Finance, or Economics",
        "description": "ICAN and ACCA professional qualifications open doors to top financial roles. Mathematics is essential.",
        "avg_salary_range": "₦100,000 – ₦1,000,000/month",
        "job_market": "Consistent demand across all sectors",
    },
    {
        "id": "pharmacist",
        "career": "Pharmacist",
        "required_subjects": ["Chemistry", "Biology", "Mathematics", "Physics", "English Language"],
        "min_credits": 5,
        "university_course": "Pharmacy (B.Pharm)",
        "description": "5-year programme with strong sciences needed. Nigeria's pharmaceutical sector is growing rapidly.",
        "avg_salary_range": "₦150,000 – ₦600,000/month",
        "job_market": "Good demand, especially in private practice and pharmaceutical companies",
    },
    {
        "id": "agricultural_scientist",
        "career": "Agricultural Scientist / Agronomist",
        "required_subjects": ["Agricultural Science", "Biology", "Chemistry", "Mathematics"],
        "min_credits": 4,
        "university_course": "Agriculture, Agronomy, or Agricultural Economics",
        "description": "With Nigeria's focus on food security, this sector has strong government backing and growing private investment.",
        "avg_salary_range": "₦80,000 – ₦400,000/month",
        "job_market": "Growing, especially with agritech startups",
    },
    {
        "id": "teacher",
        "career": "Teacher / Educator",
        "required_subjects": ["English Language"],
        "min_credits": 5,
        "university_course": "Education (B.Ed) in any subject",
        "description": "The backbone of Nigeria's future. Teaching offers job security and the chance to shape the next generation.",
        "avg_salary_range": "₦60,000 – ₦300,000/month (higher in private schools)",
        "job_market": "Always in demand",
    },
    {
        "id": "economist",
        "career": "Economist / Policy Analyst",
        "required_subjects": ["Economics", "Mathematics", "Government", "English Language"],
        "min_credits": 4,
        "university_course": "Economics or Economic Policy",
        "description": "Works in banks, government, international organisations (World Bank, IMF, UN). Strong analytical and communication skills needed.",
        "avg_salary_range": "₦150,000 – ₦1,500,000/month",
        "job_market": "Strong in financial institutions and NGOs",
    },
    {
        "id": "electrical_engineer",
        "career": "Electrical / Electronic Engineer",
        "required_subjects": ["Physics", "Mathematics", "Chemistry", "English Language"],
        "min_credits": 4,
        "university_course": "Electrical Engineering or Electronic Engineering",
        "description": "Powers Nigeria's infrastructure, telecoms, and renewable energy sectors. Very strong future demand.",
        "avg_salary_range": "₦120,000 – ₦700,000/month",
        "job_market": "High demand, especially in telecoms and energy",
    },
]


# ── DB-backed storage ────────────────────────────────────────────────────────

def init_career_db():
    """Create the scholarships / career_paths tables on startup, and seed
    them from the lists above ONLY if empty — so this is safe to call on
    every restart without duplicating rows or clobbering anything an admin
    has since edited via the CRUD routes below."""
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scholarships (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            body        TEXT,
            level       TEXT,
            subjects    TEXT,
            description TEXT,
            link        TEXT,
            type        TEXT,
            updated_at  TEXT DEFAULT (now_iso())
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS career_paths (
            id                TEXT PRIMARY KEY,
            career            TEXT NOT NULL,
            required_subjects TEXT,
            min_credits       INTEGER,
            university_course TEXT,
            description       TEXT,
            avg_salary_range  TEXT,
            job_market        TEXT,
            updated_at        TEXT DEFAULT (now_iso())
        )
    """)
    conn.commit()

    if conn.execute("SELECT COUNT(*) AS c FROM scholarships").fetchone()["c"] == 0:
        for s in _SEED_SCHOLARSHIPS:
            conn.execute(
                """INSERT INTO scholarships (id, name, body, level, subjects, description, link, type)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (s["id"], s["name"], s["body"], s["level"], json.dumps(s["subjects"]),
                 s["description"], s["link"], s["type"])
            )
        print(f"[career] Seeded {len(_SEED_SCHOLARSHIPS)} scholarships.")

    if conn.execute("SELECT COUNT(*) AS c FROM career_paths").fetchone()["c"] == 0:
        for c in _SEED_CAREERS:
            conn.execute(
                """INSERT INTO career_paths (id, career, required_subjects, min_credits, university_course, description, avg_salary_range, job_market)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (c["id"], c["career"], json.dumps(c["required_subjects"]), c["min_credits"],
                 c["university_course"], c["description"], c["avg_salary_range"], c["job_market"])
            )
        print(f"[career] Seeded {len(_SEED_CAREERS)} career paths.")

    conn.commit()
    conn.close()


def _scholarship_row_to_dict(r) -> dict:
    return {
        "id": r["id"], "name": r["name"], "body": r["body"], "level": r["level"],
        "subjects": json.loads(r["subjects"] or "[]"), "description": r["description"],
        "link": r["link"], "type": r["type"],
    }


def _career_row_to_dict(r) -> dict:
    return {
        "id": r["id"], "career": r["career"],
        "required_subjects": json.loads(r["required_subjects"] or "[]"),
        "min_credits": r["min_credits"], "university_course": r["university_course"],
        "description": r["description"], "avg_salary_range": r["avg_salary_range"],
        "job_market": r["job_market"],
    }


def _fetch_scholarships() -> list[dict]:
    conn = _get_conn()
    rows = conn.execute("SELECT * FROM scholarships ORDER BY name").fetchall()
    conn.close()
    return [_scholarship_row_to_dict(r) for r in rows]


def _fetch_careers() -> list[dict]:
    conn = _get_conn()
    rows = conn.execute("SELECT * FROM career_paths ORDER BY career").fetchall()
    conn.close()
    return [_career_row_to_dict(r) for r in rows]


@router.get("/scholarships")
def get_scholarships():
    """Return the current scholarship list from the DB — live, editable
    via the admin routes below, not a fixed list baked into this file."""
    return {"scholarships": _fetch_scholarships()}


@router.get("/careers")
def get_careers():
    """Return the current career paths list from the DB — live, editable
    via the admin routes below, not a fixed list baked into this file."""
    return {"careers": _fetch_careers()}


# ── Admin CRUD — add/edit/remove scholarships and career paths without a
# redeploy. Same admin-auth dependency billing.py's admin routes already
# use; imported down here (not at the top) to match that file's existing
# pattern. ────────────────────────────────────────────────────────────────

from admin import _require_admin  # noqa: E402 — after router/helpers defined above, avoids any import-order ambiguity


class ScholarshipIn(BaseModel):
    id: str
    name: str
    body: str = ""
    level: str = ""
    subjects: list[str] = []
    description: str = ""
    link: str = ""
    type: str = ""


class CareerIn(BaseModel):
    id: str
    career: str
    required_subjects: list[str] = []
    min_credits: int = 0
    university_course: str = ""
    description: str = ""
    avg_salary_range: str = ""
    job_market: str = ""


@router.post("/admin/scholarships")
def upsert_scholarship(s: ScholarshipIn, admin=Depends(_require_admin)):
    """Create a new scholarship, or update an existing one if the id
    already exists — same endpoint handles both, matching how the app's
    other admin CRUD (billing's redemption codes) is structured."""
    conn = _get_conn()
    conn.execute(
        """INSERT INTO scholarships (id, name, body, level, subjects, description, link, type, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, now_iso())
           ON CONFLICT (id) DO UPDATE SET
               name = EXCLUDED.name, body = EXCLUDED.body, level = EXCLUDED.level,
               subjects = EXCLUDED.subjects, description = EXCLUDED.description,
               link = EXCLUDED.link, type = EXCLUDED.type, updated_at = EXCLUDED.updated_at""",
        (s.id, s.name, s.body, s.level, json.dumps(s.subjects), s.description, s.link, s.type)
    )
    conn.commit()
    conn.close()
    return {"status": "ok", "id": s.id}


@router.delete("/admin/scholarships/{scholarship_id}")
def delete_scholarship(scholarship_id: str, admin=Depends(_require_admin)):
    conn = _get_conn()
    conn.execute("DELETE FROM scholarships WHERE id = ?", (scholarship_id,))
    conn.commit()
    conn.close()
    return {"status": "deleted", "id": scholarship_id}


@router.post("/admin/careers")
def upsert_career(c: CareerIn, admin=Depends(_require_admin)):
    conn = _get_conn()
    conn.execute(
        """INSERT INTO career_paths (id, career, required_subjects, min_credits, university_course, description, avg_salary_range, job_market, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, now_iso())
           ON CONFLICT (id) DO UPDATE SET
               career = EXCLUDED.career, required_subjects = EXCLUDED.required_subjects,
               min_credits = EXCLUDED.min_credits, university_course = EXCLUDED.university_course,
               description = EXCLUDED.description, avg_salary_range = EXCLUDED.avg_salary_range,
               job_market = EXCLUDED.job_market, updated_at = EXCLUDED.updated_at""",
        (c.id, c.career, json.dumps(c.required_subjects), c.min_credits,
         c.university_course, c.description, c.avg_salary_range, c.job_market)
    )
    conn.commit()
    conn.close()
    return {"status": "ok", "id": c.id}


@router.delete("/admin/careers/{career_id}")
def delete_career(career_id: str, admin=Depends(_require_admin)):
    conn = _get_conn()
    conn.execute("DELETE FROM career_paths WHERE id = ?", (career_id,))
    conn.commit()
    conn.close()
    return {"status": "deleted", "id": career_id}


# ── AI-personalised guidance ───────────────────────────────────────────────────

class GuidanceRequest(BaseModel):
    message: str
    history: list[dict] = []


@router.post("/guidance")
async def get_guidance(req: GuidanceRequest,
                        current_user: dict = Depends(require_user)):
    """
    AI career/scholarship guidance personalised to the student's actual
    WAEC exam performance, strong subjects, and interests.
    """
    from billing import check_feature_locked
    allowed, lock_message = await asyncio.to_thread(check_feature_locked, current_user["id"], "AI Career Guidance")
    if not allowed:
        raise HTTPException(402, lock_message)
    user_id = current_user["id"]

    def _fetch_exam_rows():
        conn = _get_conn()
        rows = conn.execute(
            """SELECT subjects, score, max_score FROM exam_sessions
               WHERE user_id = ? AND submitted_at IS NOT NULL
               ORDER BY started_at DESC LIMIT 10""",
            (user_id,)
        ).fetchall()
        conn.close()
        return rows

    # Blocking DB call pushed to a worker thread — this is an async def
    # route, so calling the DB directly here would stall the event loop
    # (and every other in-flight request) for the duration of the query.
    exam_rows = await asyncio.to_thread(_fetch_exam_rows)

    # Build subject performance summary
    subject_scores: dict[str, list[float]] = {}
    for row in exam_rows:
        try:
            subjects = json.loads(row["subjects"])
            pct = round(row["score"] / row["max_score"] * 100, 1) if row["score"] and row["max_score"] else None
            if pct is None:
                continue
            for subj in subjects:
                subject_scores.setdefault(subj, []).append(pct)
        except Exception:
            continue

    perf_summary = ""
    if subject_scores:
        lines = []
        for subj, scores in subject_scores.items():
            avg = round(sum(scores) / len(scores), 1)
            lines.append(f"- {subj}: {avg}% average ({len(scores)} exam(s))")
        perf_summary = "Student's performance data:\n" + "\n".join(lines)
    else:
        perf_summary = "Student has no exam history yet on NaijaSensei."

    # Build scholarship and career context — now real DB queries (previously
    # an in-memory list, which was fine synchronously). Same reasoning as
    # exam_rows above: pushed to a worker thread so this doesn't block the
    # event loop.
    def _fetch_career_context():
        return _fetch_scholarships(), _fetch_careers()

    scholarships, careers = await asyncio.to_thread(_fetch_career_context)
    scholarship_summary = "\n".join(
        f"- {s['name']} ({s['body']}): {s['level']}, subjects: {', '.join(s['subjects']) or 'All'}"
        for s in scholarships
    )
    career_summary = "\n".join(
        f"- {c['career']}: needs {', '.join(c['required_subjects'][:3])}"
        for c in careers
    )

    system_prompt = f"""You are NaijaSensei's Career Advisor — a warm, knowledgeable guide helping
Nigerian secondary school students make informed decisions about their future.

{perf_summary}

Available Nigerian scholarships:
{scholarship_summary}

Career paths to consider:
{career_summary}

Based on the student's performance above, give personalised advice. Be specific about
which scholarships they're likely eligible for and which careers align with their strong
subjects. Mention concrete steps (e.g. "focus on Chemistry since you'll need a credit pass
for NLNG Scholarship"). Plain flowing prose, no markdown, no bullet points. Warm and honest."""

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(req.history[-10:])
    messages.append({"role": "user", "content": req.message})

    # Non-streaming AI call (single response)
    full_prompt = f"{system_prompt}\n\nStudent says: {req.message}"
    try:
        reply = await call_ai_with_fallback(full_prompt, max_tokens=500)
        return {"reply": reply.strip()}
    except Exception as e:
        raise HTTPException(500, f"Could not generate guidance: {e}")