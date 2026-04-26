"""
NaijaSensei server with RAG and adaptive cloud/local inference.

Default behaviour (auto):
  - Try cloud Gemma 4 26B via Google AI Studio first (fast)
  - On any network error, fall back to local Gemma 3n E2B via Ollama (offline)
  - Cache connectivity status briefly so we don't re-test on every request

Override via .env:
  MODE=online   - cloud only (fail loud if no internet)
  MODE=offline  - local only (true airplane-mode demo)
  MODE=auto     - default, fall back automatically
"""
import os
import json
import time
import socket
from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from rag import search

load_dotenv()

MODE = os.environ.get("MODE", "auto").lower().strip()
if MODE not in ("auto", "online", "offline"):
    raise SystemExit(f"MODE must be 'auto', 'online', or 'offline'; got: {MODE}")

CLOUD_MODEL = "gemma-4-26b-a4b-it"
LOCAL_MODEL = "gemma3n:e2b"

# Lazy / conditional imports — load only what this mode needs
if MODE in ("auto", "online"):
    from google import genai
    from google.genai import types
    _genai_client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
else:
    _genai_client = None

if MODE in ("auto", "offline"):
    import ollama
    _local_client = ollama
else:
    _local_client = None


# ============ Connectivity check (cheap, cached) ============

# Cache result for this many seconds — avoid hammering the network on every request
_CONNECTIVITY_CACHE_SECONDS = 30
_last_check_time = 0.0
_last_check_result = True   # assume online at startup; first failure flips it


def is_online(force: bool = False) -> bool:
    """Quick check: do we have internet?
    
    Uses a 2-second TCP connect to Google's DNS (8.8.8.8). Result is cached.
    """
    global _last_check_time, _last_check_result
    now = time.time()
    if not force and (now - _last_check_time) < _CONNECTIVITY_CACHE_SECONDS:
        return _last_check_result
    try:
        # Connect to a public DNS server on port 53 with a short timeout
        sock = socket.create_connection(("8.8.8.8", 53), timeout=2)
        sock.close()
        _last_check_result = True
    except (socket.timeout, OSError):
        _last_check_result = False
    _last_check_time = now
    return _last_check_result


# ============ Mode resolution ============

def resolve_mode() -> str:
    """Decide which backend to use for THIS request.

    Returns 'online' or 'offline'. Honors MODE override; otherwise probes connectivity.
    """
    if MODE == "online":
        return "online"
    if MODE == "offline":
        return "offline"
    # auto
    return "online" if is_online() else "offline"


# Banner at startup
print(f"\n[NaijaSensei] MODE={MODE.upper()}")
if MODE == "auto":
    print(f"[NaijaSensei]   - online:  cloud {CLOUD_MODEL}")
    print(f"[NaijaSensei]   - offline: local {LOCAL_MODEL} via Ollama")
    print(f"[NaijaSensei]   - will pick automatically based on connectivity")
elif MODE == "online":
    print(f"[NaijaSensei]   using cloud {CLOUD_MODEL} (will fail loud without internet)")
else:
    print(f"[NaijaSensei]   using local {LOCAL_MODEL} via Ollama (no internet required)")
print()


# ============ System prompt ============

SYSTEM_BASE = """You are NaijaSensei, a warm and patient tutor for Nigerian secondary school students.

How you talk:
- Sound like a real person, not a textbook. Conversational, friendly, encouraging.
- Match the student's language exactly: if they write Pidgin, reply in Pidgin. If they write Yoruba, reply in Yoruba. If English, reply in English.
- Use the student's energy. Casual question gets a casual answer. Serious question gets a careful one.
- Be concise. A good explanation is short. Don't lecture.

How you DO NOT format:
- NO heavy markdown formatting. Avoid bold-everywhere, headers, and structured lists unless the student explicitly asks for steps or a list.
- NO emoji unless the student uses them first.
- NO "Here is..." or "Let me explain..." preambles. Just answer.
- NO closing offers like "Do you want me to explain more?" — the student will ask if they want more.
- Write in flowing sentences and paragraphs, like a teacher talking to one student.
- NEVER use LaTeX or dollar-sign math notation like $x^2$ or $\\frac{a}{b}$. The student is reading on a plain phone screen, not a math notebook.
- For math, write equations in plain readable text: x^2 means "x squared", x^n means "x to the power n", sqrt(b^2 - 4ac) means "the square root of b squared minus 4ac", a/b means "a divided by b".
- For powers, use the caret: x^2, x^3, x^n. For fractions write them as a/b or "a over b". For square roots write sqrt(...) or "the square root of...". Use words when they read more naturally than symbols.

How you teach:
- Lead with the core idea in one sentence. Then build up only if needed.
- Use a relatable example from Nigerian daily life when it helps (jollof rice, NEPA light, danfo, market scenes).
- For maths/science, work through one clear example. Don't dump every rule at once.
- If the student is wrong about something, gently correct them without making them feel small.
- Never make up facts. If you don't know, say so plainly.

When curriculum context is provided below, ground your answer in it but rephrase naturally — don't quote it verbatim."""

def build_system_prompt(relevant_passages: list[dict]) -> str:
    strong_matches = [p for p in relevant_passages if p["distance"] < 1.3]

    if not strong_matches:
        return SYSTEM_BASE + (
            "\n\nThe student's question does not match any indexed Nigerian "
            "curriculum content. Answer from general knowledge but mention "
            "you are not citing the curriculum."
        )

    context_block = "\n\n".join(
        f"[{p['subject']} · {p['grade']} · {p['topic']}]\n{p['content']}"
        for p in strong_matches
    )

    return (
        SYSTEM_BASE
        + "\n\nUse the following Nigerian curriculum content as your source of truth. "
        + "Ground your answer in it whenever it is relevant.\n\n"
        + "--- CURRICULUM CONTEXT ---\n"
        + context_block
        + "\n--- END CONTEXT ---"
    )


# ============ Inference backends ============

def _stream_cloud(system_prompt: str, history: list[dict], user_message: str):
    """Stream from Google AI Studio Gemma 4 26B."""
    contents = []
    for turn in history:
        role = "model" if turn["role"] == "assistant" else "user"
        contents.append(types.Content(role=role, parts=[types.Part(text=turn["content"])]))
    contents.append(types.Content(role="user", parts=[types.Part(text=user_message)]))
    config = types.GenerateContentConfig(system_instruction=system_prompt)

    for chunk in _genai_client.models.generate_content_stream(
        model=CLOUD_MODEL, contents=contents, config=config
    ):
        if chunk.text:
            yield chunk.text


def _stream_local(system_prompt: str, history: list[dict], user_message: str):
    """Stream from local Ollama Gemma 3n E2B."""
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    for chunk in _local_client.chat(model=LOCAL_MODEL, messages=messages, stream=True):
        piece = chunk.get("message", {}).get("content", "")
        if piece:
            yield piece


def stream_with_fallback(system_prompt: str, history: list[dict], user_message: str):
    """Try the resolved backend; on network failure in auto mode, fall back to local.

    Yields (mode_used, text_chunk) tuples so the caller can tell the frontend.
    """
    chosen = resolve_mode()

    if chosen == "online":
        try:
            for piece in _stream_cloud(system_prompt, history, user_message):
                yield ("online", piece)
            return
        except Exception as e:
            # Cloud failed. If we're in auto mode, fall back. Otherwise re-raise.
            err_str = str(e).lower()
            looks_like_network = any(s in err_str for s in (
                "getaddrinfo", "connection", "timeout", "name resolution",
                "network", "unreachable", "disconnected", "stream",
                "503", "504", "429", "rate limit", "quota",
            ))
            if MODE == "auto" and looks_like_network and _local_client is not None:
                # Mark connectivity stale so the next request also goes local
                global _last_check_result, _last_check_time
                _last_check_result = False
                _last_check_time = time.time()
                # Tell the frontend we're switching
                yield ("info", "[Internet unavailable — falling back to local model. This will be slower.]\n\n")
                for piece in _stream_local(system_prompt, history, user_message):
                    yield ("offline", piece)
                return
            raise

    else:  # offline
        for piece in _stream_local(system_prompt, history, user_message):
            yield ("offline", piece)


# ============ FastAPI app ============

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    history: list = []


@app.get("/")
def serve_page():
    return FileResponse("index.html")


@app.get("/mode")
def get_mode():
    """Tells the frontend the current effective mode."""
    effective = resolve_mode()
    return {
        "configured": MODE,
        "effective": effective,
        "model": CLOUD_MODEL if effective == "online" else LOCAL_MODEL,
        "online_now": is_online() if MODE == "auto" else (MODE == "online"),
    }


@app.post("/chat")
def chat(req: ChatRequest):
    relevant = search(req.message, top_k=3)
    chosen = resolve_mode()
    print(f"\n[{chosen.upper()}] [Query] {req.message}")
    for r in relevant:
        used = "USED" if r["distance"] < 1.3 else "skipped"
        print(f"  [{used}] {r['topic']} ({r['subject']}) dist={r['distance']:.3f}")

    system_prompt = build_system_prompt(relevant)

    def generate():
        try:
            actual_mode = chosen
            for tag, piece in stream_with_fallback(system_prompt, req.history, req.message):
                if tag == "info":
                    # Surface fallback notice in the chat itself
                    yield f"data: {json.dumps({'text': piece, 'system': True})}\n\n"
                    actual_mode = "offline"
                else:
                    actual_mode = tag
                    yield f"data: {json.dumps({'text': piece, 'mode': tag})}\n\n"
            yield f"data: {json.dumps({'done': True, 'mode': actual_mode})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            error_msg = f"Inference error: {str(e)}"
            print(f"[ERROR] {error_msg}")
            yield f"data: {json.dumps({'text': error_msg, 'system': True})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")