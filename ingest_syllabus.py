"""
Convert pasted Nigerian syllabus text (WAEC/NECO/JUPEB) into Tutorly curriculum chunks.

How it works
------------
You save raw syllabus text into a file at data/raw/<board>-<subject>-<year>.txt.
You run this script with arguments describing what's in that file. The script
parses the text into fine-grained chunks (one per sub-point), assigns metadata
(board, subject, department, grade), and appends them to data/generated_curriculum.py
in the exact format your existing curriculum.py uses.

Usage
-----
    python scripts/ingest_syllabus.py \
        --file data/raw/waec-chemistry-2026.txt \
        --board WAEC \
        --subject Chemistry \
        --department Sciences \
        --grade SS \
        --year 2026

After running, review the appended entries in data/generated_curriculum.py and,
when satisfied, copy them into curriculum.py (or import them — see notes below).

Design notes
------------
- Fine granularity: each Roman-numeral or letter sub-point becomes its own chunk.
- Topic context: each chunk includes its parent topic name so retrieval has
  enough semantic signal even for very short sub-points.
- Deterministic IDs: ids are stable across runs, so re-ingesting the same file
  produces the same ids (no duplicates if you append carefully).
- Loss-tolerant parser: if the text format varies, we still extract something
  useful rather than crashing. Quality is checked at the end with a count.
"""
from __future__ import annotations

import argparse
import re
import unicodedata
from pathlib import Path
from textwrap import indent


# ---- text cleaning ------------------------------------------------------------

def clean(text: str) -> str:
    """Normalize unicode and collapse spaces. Tabs are preserved (significant)."""
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\u00a0", " ")
    # Collapse runs of spaces but keep tabs - they separate topic from objectives
    text = re.sub(r"[ ]+", " ", text)
    return text.strip()


# Header lines that look like topics but are actually table headers / noise
HEADER_BLACKLIST = {
    "TOPICS OBJECTIVES",
    "TOPICS",
    "OBJECTIVES",
    "WAEC CHEMISTRY SYLLABUS",
    "WAEC CHEMISTRY PRACTICALS",
    "WAEC SYLLABUS",
}


def slugify(text: str, max_len: int = 40) -> str:
    """Turn 'Acids, Bases & Salts' into 'acids_bases_salts'."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = text.strip("_")
    return text[:max_len]


# ---- syllabus structure parsing ----------------------------------------------

# A "topic header" line is usually all-caps or Title Case, short, no punctuation
# beyond ampersands and commas. Heuristic, not perfect.
TOPIC_HEADER_RE = re.compile(
    r"^[\sA-Z0-9&,\-/()]{4,80}$"  # mostly uppercase, reasonable length
)

# Sub-point markers we want to chunk on:
#   "i.", "ii.", "iii.", "iv." (Roman numerals)
#   "a)", "b)", "c)" (lowercase letter with paren)
#   "1.", "2." (arabic numerals)
SUBPOINT_RE = re.compile(
    r"^\s*(?:"
    r"(?:[ivxlcdm]+\.)"               # roman: i. ii. iii.
    r"|(?:[a-z]\))"                   # letter: a) b) c)
    r"|(?:\d+\.)"                     # arabic: 1. 2.
    r")\s+",
    re.IGNORECASE,
)


def looks_like_topic_header(line: str) -> bool:
    """Heuristic: is this line a major topic heading?

    A topic header is typically ALL-CAPS, 4-80 chars, mostly letters and not
    in our blacklist of false positives.
    """
    line = line.strip()
    if line.upper() in HEADER_BLACKLIST:
        return False
    if len(line) < 4 or len(line) > 80:
        return False
    if not TOPIC_HEADER_RE.match(line):
        return False
    # Must be predominantly uppercase (real topic headers are all-caps)
    upper = sum(c.isupper() for c in line if c.isalpha())
    letters = sum(c.isalpha() for c in line)
    if letters == 0 or upper / letters < 0.8:
        return False
    return True


def split_into_topics(raw_text: str) -> list[tuple[str, list[str]]]:
    """
    Walk through the syllabus text top-to-bottom and group lines under each topic header.

    Handles two formats:
      1. Topic on its own line, followed by sub-points on next lines (multi-line)
      2. Topic and first sub-point on the same line, separated by a tab (table layout)
    """
    topics: list[tuple[str, list[str]]] = []
    current_topic: str | None = None
    current_lines: list[str] = []

    for raw_line in raw_text.splitlines():
        if not raw_line.strip():
            continue

        # Check for tab-separated "TOPIC\tcontent" pattern (WAEC table layout)
        if "\t" in raw_line:
            parts = raw_line.split("\t", 1)
            possible_header = clean(parts[0])
            rest = clean(parts[1]) if len(parts) > 1 else ""
            if looks_like_topic_header(possible_header):
                # New topic detected via tab split
                if current_topic and current_lines:
                    topics.append((current_topic, current_lines))
                current_topic = possible_header
                current_lines = [rest] if rest else []
                continue

        line = clean(raw_line)
        if not line:
            continue

        if looks_like_topic_header(line):
            if current_topic and current_lines:
                topics.append((current_topic, current_lines))
            current_topic = line
            current_lines = []
        else:
            if current_topic:
                current_lines.append(line)

    if current_topic and current_lines:
        topics.append((current_topic, current_lines))

    return topics


def split_topic_into_subpoints(lines: list[str]) -> list[str]:
    """
    Within a topic, split content into discrete sub-points.

    A sub-point starts at a marker (i. / ii. / a) / 1.) and continues until the next marker.
    Lines without a marker get appended to the current sub-point.
    """
    subpoints: list[str] = []
    current: list[str] = []

    for line in lines:
        if SUBPOINT_RE.match(line):
            # Start a new sub-point
            if current:
                subpoints.append(" ".join(current).strip())
            current = [line]
        else:
            # Continuation of current sub-point (or trailing detail)
            if current:
                current.append(line)
            else:
                # Line before any marker - treat as standalone sub-point
                subpoints.append(line)

    if current:
        subpoints.append(" ".join(current).strip())

    # Filter out marker-only lines (e.g. just "i.") and very short fragments
    return [sp for sp in subpoints if len(sp) > 8]


# ---- chunk building ----------------------------------------------------------

def build_chunks(
    raw_text: str,
    *,
    board: str,
    subject: str,
    department: str,
    grade: str,
    year: int,
) -> list[dict]:
    """Top-level: turn raw syllabus text into a list of curriculum chunks."""
    topics = split_into_topics(raw_text)
    chunks: list[dict] = []

    subj_slug = slugify(subject, 12)
    board_slug = slugify(board, 6)

    # Track how many times each topic_slug has appeared.
    # Real syllabi often repeat topic names across sections (e.g. JSS vs SSS),
    # so we suffix occurrences with a section counter to keep IDs unique.
    topic_occurrences: dict[str, int] = {}

    for topic_name, lines in topics:
        topic_slug = slugify(topic_name, 30)
        topic_occurrences[topic_slug] = topic_occurrences.get(topic_slug, 0) + 1
        section_num = topic_occurrences[topic_slug]
        subpoints = split_topic_into_subpoints(lines)

        for idx, sp_text in enumerate(subpoints, start=1):
            # Strip the leading marker from the chunk content (it's noise for the LLM)
            content = SUBPOINT_RE.sub("", sp_text, count=1).strip()
            if len(content) < 15:
                continue  # too short to be useful

            # Prepend the topic name so the chunk has semantic context on its own
            full_content = (
                f"[{subject} - {topic_name.title()}]\n"
                f"{content}"
            )

            # ID format: {board}_{subject}_{topic}_s{section}_{idx}
            # Section number is always present so re-encountering a topic name
            # never collides with earlier chunks.
            chunk_id = f"{board_slug}_{subj_slug}_{topic_slug}_s{section_num}_{idx:02d}"
            chunks.append({
                "id": chunk_id,
                "board": board,
                "subject": subject,
                "department": department,
                "grade": grade,
                "year": year,
                "topic": topic_name.title(),
                "content": full_content,
            })

    return chunks


# ---- output formatting -------------------------------------------------------

def format_python_dict(chunk: dict) -> str:
    """Format a chunk as a Python dict literal that matches curriculum.py style."""
    # Escape any triple-quote sequences in content (paranoid)
    content = chunk["content"].replace('"""', '\\"\\"\\"')
    return (
        "    {\n"
        f"        \"id\": \"{chunk['id']}\",\n"
        f"        \"board\": \"{chunk['board']}\",\n"
        f"        \"subject\": \"{chunk['subject']}\",\n"
        f"        \"department\": \"{chunk['department']}\",\n"
        f"        \"grade\": \"{chunk['grade']}\",\n"
        f"        \"year\": {chunk['year']},\n"
        f"        \"topic\": \"{chunk['topic']}\",\n"
        f"        \"content\": (\n"
        f"            \"\"\"{content}\"\"\"\n"
        f"        ),\n"
        "    },"
    )


# ---- CLI ---------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest a Nigerian syllabus text file into Tutorly curriculum chunks.")
    parser.add_argument("--file", required=True, help="Path to raw syllabus .txt file")
    parser.add_argument("--board", required=True, choices=["WAEC", "NECO", "JUPEB", "JAMB"])
    parser.add_argument("--subject", required=True, help='e.g. "Chemistry", "Mathematics", "Government"')
    parser.add_argument("--department", required=True, choices=["Sciences", "Arts", "Commercial", "Compulsory"])
    parser.add_argument("--grade", default="SS", help="Grade level, e.g. SS, JSS3, SS2")
    parser.add_argument("--year", type=int, default=2026)
    parser.add_argument(
        "--out",
        default="data/generated_curriculum.py",
        help="Output Python file. Chunks will be APPENDED if it exists.",
    )

    args = parser.parse_args()

    src = Path(args.file)
    if not src.exists():
        raise SystemExit(f"Source file not found: {src}")

    raw = src.read_text(encoding="utf-8")
    chunks = build_chunks(
        raw,
        board=args.board,
        subject=args.subject,
        department=args.department,
        grade=args.grade,
        year=args.year,
    )

    if not chunks:
        raise SystemExit("No chunks extracted. Check the source file format.")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    if not out.exists():
        # First write: create the file with a header and an empty list
        out.write_text(
            '"""Auto-generated curriculum chunks from official Nigerian syllabi."""\n\n'
            "GENERATED_CURRICULUM = [\n"
            "]\n",
            encoding="utf-8",
        )

    # Insert new chunks before the closing ']'
    existing = out.read_text(encoding="utf-8")
    if not existing.rstrip().endswith("]"):
        raise SystemExit(f"Cannot append: {out} does not end with a list literal.")

    insertion = "\n".join(format_python_dict(c) for c in chunks) + "\n"
    new_content = existing.rstrip()
    if new_content.endswith("[\n]") or new_content.endswith("[]"):
        # Empty list — insert without leading comma
        new_content = new_content[: new_content.rfind("]")] + insertion + "]\n"
    else:
        # Non-empty list — splice before final ]
        idx = new_content.rfind("]")
        new_content = new_content[:idx] + insertion + "]\n"

    out.write_text(new_content, encoding="utf-8")

    print(f"\n✓ Ingested {len(chunks)} chunks from {src.name}")
    print(f"✓ Appended to {out}")
    print(f"\nSample of first 3 chunks:")
    for c in chunks[:3]:
        preview = c["content"][:120].replace("\n", " ")
        print(f"  [{c['id']}] {c['topic']}: {preview}...")
    print(f"\nNext: review {out}, then merge into curriculum.py")


if __name__ == "__main__":
    main()