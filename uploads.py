"""
uploads.py — Image & document upload handler for NaijaSensei
Supports: JPG, PNG, WEBP (sent directly to vision AI), PDF, TXT, DOCX (text extracted)

Install deps:
  pip install python-multipart aiofiles pdfminer.six python-docx
"""

import uuid
import base64
import aiofiles
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from auth import require_user

router = APIRouter(prefix="/upload", tags=["uploads"])

# ── Config ────────────────────────────────────────────────────────────────────
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
MAX_MB = 10

ALLOWED = {
    "image/jpeg", "image/png", "image/webp",
    "application/pdf", "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}

# The extension a file is actually SAVED with — derived from the verified
# type below, never from the client-supplied filename. Previously
# `Path(file.filename).suffix` was used directly, so a request declaring
# Content-Type: image/jpeg (passing the ALLOWED check) with filename
# "x.php" would save arbitrary bytes to disk as "<uuid>.php".
_EXT_BY_TYPE = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "application/pdf": ".pdf",
    "text/plain": ".txt",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}

# Leading-byte signatures for each allowed type, checked against the
# ACTUAL uploaded content — Content-Type is just an HTTP header the
# client sets and can be anything regardless of what's really in the
# file, so the allowlist check above cannot be trusted on its own.
_MAGIC_BYTES = {
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
    "application/pdf": (b"%PDF",),
    # DOCX is a zip archive under the hood
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": (b"PK\x03\x04",),
    # text/plain has no reliable magic bytes and can't execute as anything
    # dangerous either way, so the declared Content-Type is accepted as-is
}


def _content_matches_declared_type(contents: bytes, content_type: str) -> bool:
    """True if the file's actual leading bytes are consistent with what it
    claims to be. WEBP gets its own check since its signature isn't a
    simple fixed prefix (RIFF container with a WEBP marker at offset 8)."""
    if content_type == "image/webp":
        return contents[:4] == b"RIFF" and contents[8:12] == b"WEBP"
    sigs = _MAGIC_BYTES.get(content_type)
    if not sigs:
        return True
    return any(contents.startswith(sig) for sig in sigs)

# ── Extractors (for documents only — images go to vision AI directly) ─────────
def _pdf(path: Path) -> str:
    try:
        from pdfminer.high_level import extract_text
        return extract_text(str(path)).strip()
    except ImportError:
        return "[Install pdfminer.six for PDF reading]"
    except Exception as e:
        return f"[PDF extraction failed: {e}]"

def _docx(path: Path) -> str:
    try:
        from docx import Document
        return "\n".join(p.text for p in Document(str(path)).paragraphs if p.text.strip())
    except ImportError:
        return "[Install python-docx for Word file reading]"
    except Exception as e:
        return f"[DOCX extraction failed: {e}]"

def _txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace").strip()

def extract_text(path: Path, ctype: str) -> str:
    """Only used for documents. Images are handled via vision in server.py."""
    if ctype == "application/pdf":    return _pdf(path)
    if "wordprocessingml" in ctype:   return _docx(path)
    if ctype == "text/plain":         return _txt(path)
    return ""

def image_to_base64(path: Path) -> str:
    """Convert image to base64 string for passing to vision AI."""
    return base64.b64encode(path.read_bytes()).decode("utf-8")

# ── Routes ────────────────────────────────────────────────────────────────────
@router.post("/")
async def upload(
    file: UploadFile = File(...),
    question: Optional[str] = Form(None),
    current_user: dict = Depends(require_user),
):
    if file.content_type not in ALLOWED:
        raise HTTPException(415, f"File type not supported: {file.content_type}")

    contents = await file.read()
    mb = len(contents) / (1024 * 1024)
    if mb > MAX_MB:
        raise HTTPException(413, f"File too large ({mb:.1f} MB). Max is {MAX_MB} MB.")

    if not _content_matches_declared_type(contents, file.content_type):
        raise HTTPException(415, "File content doesn't match its declared type.")

    user_dir = UPLOAD_DIR / str(current_user["id"])
    user_dir.mkdir(exist_ok=True)
    ext = _EXT_BY_TYPE[file.content_type]
    saved = f"{uuid.uuid4().hex}{ext}"
    fpath = user_dir / saved

    async with aiofiles.open(fpath, "wb") as f:
        await f.write(contents)

    is_image = file.content_type in IMAGE_TYPES

    if is_image:
        # For images: return base64 + mime type so server.py can send to vision AI
        b64 = image_to_base64(fpath)
        return {
            "ok": True,
            "file_type": "image",
            "original_name": file.filename,
            "size_mb": round(mb, 2),
            "extracted_text": "",        # not used for images
            "image_b64": b64,
            "image_mime": file.content_type,
            "char_count": 0,
            "question": question,
        }
    else:
        text = extract_text(fpath, file.content_type)
        return {
            "ok": True,
            "file_type": "document",
            "original_name": file.filename,
            "size_mb": round(mb, 2),
            "extracted_text": text,
            "image_b64": "",
            "image_mime": "",
            "char_count": len(text),
            "question": question,
        }


@router.get("/my-files")
def my_files(current_user: dict = Depends(require_user)):
    user_dir = UPLOAD_DIR / str(current_user["id"])
    if not user_dir.exists():
        return {"files": []}
    return {
        "files": [
            {"name": f.name, "size_mb": round(f.stat().st_size / (1024 * 1024), 2)}
            for f in user_dir.iterdir() if f.is_file()
        ]
    }