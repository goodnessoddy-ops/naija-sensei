"""
Batch-ingest all WAEC subject syllabi into Tutorly's curriculum index.

Reuses the parser logic from scripts/ingest_syllabus.py. For each subject,
it looks for the corresponding .txt file in data/raw/. If the file exists,
it parses and appends to data/generated_curriculum.py. If not, it skips
gracefully and reports at the end what's still missing.

Usage:
    1. Delete data/generated_curriculum.py first (clean slate)
    2. Save .txt files for as many subjects as you have, in data/raw/
    3. Run from project root:    python scripts/ingest_all.py
    4. Restart the server to pick up new chunks

Idempotent: re-running with the same .txt files produces the same result.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make the sibling ingest_syllabus module importable
sys.path.insert(0, str(Path(__file__).parent))
from ingest_syllabus import build_chunks, format_python_dict


# Single source of truth: every WAEC subject Tutorly aims to cover.
# Add or remove rows here. The script auto-handles whichever .txt files exist.
SUBJECTS = [
    # ---- Compulsory ----
    {"file": "waec-english-2026.txt",       "subject": "English Language",        "dept": "Compulsory"},
    {"file": "waec-mathematics-2026.txt",   "subject": "Mathematics",             "dept": "Compulsory"},

    # ---- Sciences ----
    {"file": "waec-physics-2026.txt",       "subject": "Physics",                 "dept": "Sciences"},
    {"file": "waec-chemistry-2026.txt",     "subject": "Chemistry",               "dept": "Sciences"},
    {"file": "waec-biology-2026.txt",       "subject": "Biology",                 "dept": "Sciences"},
    {"file": "waec-further-maths-2026.txt", "subject": "Further Mathematics",     "dept": "Sciences"},
    {"file": "waec-agric-2026.txt",         "subject": "Agricultural Science",    "dept": "Sciences"},

    # ---- Arts ----
    {"file": "waec-literature-2026.txt",    "subject": "Literature in English",   "dept": "Arts"},
    {"file": "waec-government-2026.txt",    "subject": "Government",              "dept": "Arts"},
    {"file": "waec-history-2026.txt",       "subject": "History",                 "dept": "Arts"},
    {"file": "waec-crs-2026.txt",           "subject": "Christian Religious Studies", "dept": "Arts"},
    {"file": "waec-irs-2026.txt",           "subject": "Islamic Religious Studies",   "dept": "Arts"},

    # ---- Commercial ----
    {"file": "waec-economics-2026.txt",     "subject": "Economics",               "dept": "Commercial"},
    {"file": "waec-commerce-2026.txt",      "subject": "Commerce",                "dept": "Commercial"},
    {"file": "waec-accounting-2026.txt",    "subject": "Financial Accounting",    "dept": "Commercial"},
]


RAW_DIR = Path("data/raw")
OUT_FILE = Path("data/generated_curriculum.py")
BOARD = "WAEC"
GRADE = "SS"
YEAR = 2026


def init_output_file(path: Path) -> None:
    """Reset the output file to an empty list so we don't accumulate duplicates."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        '"""Auto-generated curriculum chunks from official Nigerian syllabi."""\n\n'
        "GENERATED_CURRICULUM = [\n]\n",
        encoding="utf-8",
    )


def append_chunks(path: Path, chunks: list[dict]) -> None:
    """Splice formatted chunks into the existing list literal."""
    existing = path.read_text(encoding="utf-8").rstrip()
    insertion = "\n".join(format_python_dict(c) for c in chunks) + "\n"
    if existing.endswith("[\n]") or existing.endswith("[]"):
        new_content = existing[: existing.rfind("]")] + insertion + "]\n"
    else:
        idx = existing.rfind("]")
        new_content = existing[:idx] + insertion + "]\n"
    path.write_text(new_content, encoding="utf-8")


def main() -> None:
    # Confirm we're running from the project root
    if not Path("scripts").is_dir():
        sys.exit("Run this from the project root (the folder containing 'scripts/'), not from inside scripts/.")

    print("=" * 70)
    print(f"Tutorly batch syllabus ingest")
    print(f"Source dir: {RAW_DIR}/")
    print(f"Output:     {OUT_FILE}")
    print("=" * 70)

    init_output_file(OUT_FILE)

    ingested = []
    missing = []
    failed = []
    total_chunks = 0

    for entry in SUBJECTS:
        src = RAW_DIR / entry["file"]
        subject = entry["subject"]
        dept = entry["dept"]

        if not src.exists():
            missing.append(f"  · {subject:<30} (need: {src})")
            continue

        try:
            raw = src.read_text(encoding="utf-8")
            chunks = build_chunks(
                raw,
                board=BOARD,
                subject=subject,
                department=dept,
                grade=GRADE,
                year=YEAR,
            )
            if not chunks:
                failed.append(f"  · {subject:<30} (parser returned 0 chunks — check file format)")
                continue
            append_chunks(OUT_FILE, chunks)
            ingested.append(f"  ✓ {subject:<30} {len(chunks):>4} chunks  ({src.name})")
            total_chunks += len(chunks)
        except Exception as e:
            failed.append(f"  · {subject:<30} ERROR: {e}")

    # Summary
    print()
    if ingested:
        print(f"Ingested ({len(ingested)} subjects, {total_chunks} chunks total):")
        for line in ingested:
            print(line)
    if missing:
        print(f"\nMissing source files ({len(missing)} subjects — save these to {RAW_DIR}/ to include them):")
        for line in missing:
            print(line)
    if failed:
        print(f"\nFailed to parse ({len(failed)} subjects):")
        for line in failed:
            print(line)

    print()
    print("=" * 70)
    if total_chunks > 0:
        print(f"Done. {total_chunks} chunks written to {OUT_FILE}")
        print("Next: restart the server to load the new chunks.")
        print("    python -m uvicorn server:app --reload --port 8000")
    else:
        print("No chunks ingested. Save syllabus .txt files to data/raw/ first.")
    print("=" * 70)


if __name__ == "__main__":
    main()