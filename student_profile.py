"""
student_profile.py — Student department and subject combination system.

Based on WAEC 2026/2027 official subject structure:
- 3 departments: Science, Arts, Commercial
- 3 compulsory subjects for all: English Language, Mathematics, Civic Education
- Department core subjects
- Elective/optional subjects per department
- 35 Trade subjects
"""

import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from auth import require_user, _get_conn

router = APIRouter(prefix="/profile", tags=["profile"])

# ── Full WAEC 2026 Subject Structure ─────────────────────────────────────────

COMPULSORY_SUBJECTS = [
    "English Language",
    "Mathematics",
    "Civic Education",
]

DEPARTMENTS = {
    "science": {
        "label": "Science",
        "emoji": "🔬",
        "description": "Physics, Chemistry, Biology — for Medicine, Engineering, Pharmacy, Computer Science",
        "core_subjects": [
            "Physics",
            "Chemistry",
            "Biology",
        ],
        "optional_subjects": [
            "Further Mathematics",
            "Geography",
            "Agricultural Science",
            "Technical Drawing",
            "Yoruba Language",
            "Igbo Language",
            "Hausa Language",
            "Health Education",
            "Physical Education",
            "Computer Studies",
            "Foods and Nutrition",
            "Animal Husbandry",
        ],
        "career_paths": ["Medicine", "Engineering", "Pharmacy", "Nursing", "Computer Science",
                          "Biochemistry", "Microbiology", "Architecture", "Dentistry"],
    },
    "arts": {
        "label": "Arts / Humanities",
        "emoji": "📚",
        "description": "Literature, Government, Languages — for Law, Mass Comm, Education, Social Sciences",
        "core_subjects": [
            "Literature in English",
            "Government",
            "History",
            "Christian Religious Studies",
            "Islamic Religious Studies",
            "Yoruba Language",
            "Igbo Language",
            "Hausa Language",
            "Edo Language",
            "Efik Language",
            "Ibibio Language",
            "Arabic",
            "French",
            "Music",
        ],
        "optional_subjects": [
            "Geography",
            "Agricultural Science",
            "Biology",
            "Commerce",
            "Fine Art",
            "Physical Education",
        ],
        "note": "Choose at least one Nigerian Language and one of: Government or History. CRS or IRS (not both required).",
        "career_paths": ["Law", "Mass Communication", "English Education", "History",
                          "International Relations", "Linguistics", "Theatre Arts", "Journalism"],
    },
    "commercial": {
        "label": "Commercial / Business",
        "emoji": "💼",
        "description": "Economics, Accounting, Commerce — for Business Admin, Banking, Marketing, Finance",
        "core_subjects": [
            "Economics",
            "Commerce",
            "Financial Accounting",
            "Marketing",
        ],
        "optional_subjects": [
            "Further Mathematics",
            "Agricultural Science",
            "Biology",
            "Yoruba Language",
            "Igbo Language",
            "Hausa Language",
            "Geography",
            "Government",
            "Book Keeping",
            "Office Practice",
            "Store Management",
            "Computer Studies",
        ],
        "career_paths": ["Accounting", "Banking & Finance", "Business Administration",
                          "Marketing", "Economics", "Insurance", "Entrepreneurship"],
    },
}

TRADE_SUBJECTS = [
    "Auto Mechanics", "Basketry", "Batik and Tie-Dye", "Beauty and Cosmetology",
    "Block Laying, Bricklaying and Concreting", "Book Binding", "Business Management",
    "Cabinet Making", "Catering Craft Practice", "Computer Craft Practice",
    "Data Processing", "Dyeing and Bleaching", "Electrical Installation and Maintenance",
    "Electronics", "Fashion Design and Garment Making", "Fishery",
    "Floral Decoration", "Furniture Making", "GSM Maintenance and Repairs",
    "Glass and Ceramics", "Graphic Design", "Home Management",
    "Horticulture", "Iron and Steel Fabrication", "Leather Goods Manufacturing",
    "Painting and Decorating", "Photo Technology", "Plumbing and Pipe Fitting",
    "Printing Craft Practice", "Refrigeration and Air Conditioning",
    "Sculpture", "Shoemaking", "Typewriting", "Upholstery", "Welding and Fabrication",
]

# Subject groups for the UI
ALL_SUBJECTS_BY_DEPARTMENT = {}
for dept_key, dept in DEPARTMENTS.items():
    ALL_SUBJECTS_BY_DEPARTMENT[dept_key] = (
        COMPULSORY_SUBJECTS
        + dept["core_subjects"]
        + dept.get("optional_subjects", [])
    )


# ── DB setup ──────────────────────────────────────────────────────────────────

def init_profile_db():
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS student_profiles (
            user_id     INTEGER PRIMARY KEY,
            department  TEXT,
            class_level TEXT DEFAULT 'SS2',
            subjects    TEXT,
            target_score INTEGER DEFAULT 70,
            waec_year   INTEGER,
            updated_at  TEXT DEFAULT (now_iso())
        )
    """)
    conn.commit()
    conn.close()


# ── Schemas ───────────────────────────────────────────────────────────────────

class ProfileRequest(BaseModel):
    department: str            # "science", "arts", or "commercial"
    class_level: str = "SS2"   # "SS1", "SS2", "SS3"
    subjects: list[str]        # selected subjects (7-9 total)
    target_score: int = 70     # target WAEC score %
    waec_year: Optional[int] = None


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/departments")
def get_departments():
    """Return all departments with their subject lists."""
    return {
        "departments": {
            k: {
                "label": v["label"],
                "emoji": v["emoji"],
                "description": v["description"],
                "compulsory": COMPULSORY_SUBJECTS,
                "core_subjects": v["core_subjects"],
                "optional_subjects": v.get("optional_subjects", []),
                "trade_subjects": TRADE_SUBJECTS,
                "career_paths": v.get("career_paths", []),
                "note": v.get("note", ""),
            }
            for k, v in DEPARTMENTS.items()
        }
    }


@router.post("/save")
def save_profile(req: ProfileRequest,
                  current_user: dict = Depends(require_user)):
    """Save student's department and subject combination."""
    if req.department not in DEPARTMENTS:
        raise HTTPException(400, "Department must be: science, arts, or commercial.")
    if len(req.subjects) < 7 or len(req.subjects) > 9:
        raise HTTPException(400, "Select between 7 and 9 subjects.")

    # Validate compulsory subjects are included
    missing = [s for s in COMPULSORY_SUBJECTS if s not in req.subjects]
    if missing:
        raise HTTPException(400, f"Missing compulsory subjects: {', '.join(missing)}")

    # Every submitted subject must actually be valid for this department
    # (or a trade subject) — without this, a profile could be saved with
    # a subject exam.py's own SUBJECTS list (built from these same
    # constants) doesn't recognise, so the student would never be able to
    # start an exam in a "subject" they successfully registered for.
    valid_for_department = set(ALL_SUBJECTS_BY_DEPARTMENT[req.department]) | set(TRADE_SUBJECTS)
    invalid = [s for s in req.subjects if s not in valid_for_department]
    if invalid:
        raise HTTPException(
            400,
            f"Not valid for the {DEPARTMENTS[req.department]['label']} department: {', '.join(invalid)}"
        )

    conn = _get_conn()
    conn.execute("""
        INSERT INTO student_profiles (user_id, department, class_level, subjects, target_score, waec_year)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            department=excluded.department,
            class_level=excluded.class_level,
            subjects=excluded.subjects,
            target_score=excluded.target_score,
            waec_year=excluded.waec_year,
            updated_at=now_iso()
    """, (current_user["id"], req.department, req.class_level,
          json.dumps(req.subjects), req.target_score, req.waec_year))
    conn.commit()
    conn.close()
    return {"message": "Profile saved.", "department": req.department, "subjects": req.subjects}


@router.get("/me")
def get_my_profile(current_user: dict = Depends(require_user)):
    """Get the current student's saved profile."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT * FROM student_profiles WHERE user_id=?", (current_user["id"],)
    ).fetchone()
    conn.close()
    if not row:
        return {"has_profile": False}
    return {
        "has_profile": True,
        "department": row["department"],
        "class_level": row["class_level"],
        "subjects": json.loads(row["subjects"]),
        "target_score": row["target_score"],
        "waec_year": row["waec_year"],
        "department_info": DEPARTMENTS.get(row["department"], {}),
    }


@router.get("/topics")
def get_topics_for_subject(subject: str, current_user: dict = Depends(require_user)):
    """
    Admin-managed topics for a subject — shown in the subject-chat sidebar
    so a student can pick one to narrow the AI's answer/RAG retrieval.
    Read-only for students; managed via /admin/topics.
    """
    conn = _get_conn()
    rows = conn.execute(
        "SELECT topic FROM subject_topics WHERE subject = ? ORDER BY topic ASC",
        (subject,)
    ).fetchall()
    conn.close()
    return {"subject": subject, "topics": [r["topic"] for r in rows]}