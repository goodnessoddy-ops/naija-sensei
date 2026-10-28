"""
ai_providers.py - Shared 32-provider AI fallback chain for NaijaSensei.

ASYNC VERSION: uses httpx.AsyncClient instead of urllib.request, so multiple
students' requests can be served concurrently without one blocking another.
Previously, every provider call used blocking urllib calls inside sync route
handlers - with several students chatting/taking exams at once, FastAPI's
limited sync worker thread pool meant requests queued up behind each other,
especially during Exam Mode (which makes many sequential AI calls per exam).

Requires: pip install httpx --break-system-packages

Used by:
  server.py     -> /chat endpoint (streaming, with chat history + images)
  exam.py       -> exam question generation + theory marking (non-streaming)
  analytics.py  -> study plan generation (streaming)

Exposes three main async functions:

  async for tag, chunk in stream_with_fallback(system_prompt, history, user_message, image_b64="", image_mime=""):
      ...  # Used for /chat.

  text = await call_ai_with_fallback(prompt, max_tokens=2000)
      # Used for exam generation & marking.

  async for tag, chunk in stream_simple_with_fallback(prompt, max_tokens=2000):
      ...  # Used for study plan generation.

Add provider keys to your .env file. Any key left unset is automatically skipped.
"""

import os
import json
import time
import socket
import asyncio
import httpx
import base64
import inspect

from auth import _get_conn

MODE = os.environ.get("MODE", "auto").lower().strip()

# ── MOCK_AI: short-circuit every provider for load/throughput testing ──────
# Set MOCK_AI=true to skip every real AI provider entirely and return a
# canned response instead. Use this to load-test app-level throughput
# (DB pool, event loop, request handling) without generating real
# provider spend or risking rate limits from a burst of simulated users —
# see locustfile.py. This short-circuits BEFORE resolve_mode()/is_online()
# even run, so no network calls happen at all in mock mode, not even a
# connectivity check.
MOCK_AI = os.environ.get("MOCK_AI", "false").strip().lower() == "true"
if MOCK_AI:
    print("[ai_providers] MOCK_AI=true — all AI calls will return a canned "
          "response instead of calling a real provider. Do not use this "
          "mode to evaluate answer quality or latency, only app throughput.")

_MOCK_REPLY = (
    "[MOCK_AI] This is a canned response for load testing — no real AI "
    "provider was called, so this doesn't reflect real answer quality or "
    "latency."
)


def _mock_mcq_json(count: int = 4) -> str:
    """A small, always-valid batch of mock MCQs matching exam.py's
    `_build_mcq_prompt` response schema (`{"mcq": [...]}`) — exam.py's
    JSON parser would fail on plain prose, so the exam-generation path
    needs a schema-matching mock rather than the generic one below."""
    mcqs = [
        {
            "id": f"mcq_{i + 1}",
            "question": f"[MOCK] Sample question {i + 1}?",
            "options": {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
            "answer": "A",
            "subject": "General",
            "topic": "Mock Topic",
        }
        for i in range(max(1, count))
    ]
    return json.dumps({"mcq": mcqs})


def _mock_response_for(prompt: str) -> str:
    """Prompt-aware mock — most callers (chat, career guidance, study
    plans) just want plain prose back, but exam.py's MCQ generator
    requires a specific JSON shape to parse successfully, so detect that
    case from the prompt's own `Return ONLY valid JSON` schema block."""
    if '"mcq": [' in prompt:
        return _mock_mcq_json()
    return _MOCK_REPLY


async def _mock_stream(prompt: str):
    """Mimics real streaming — yields the mock text in a few chunks with
    a small delay, so load-test timing isn't unrealistically instant
    compared to a real provider call."""
    text = _mock_response_for(prompt)
    chunk_size = max(1, len(text) // 4)
    for i in range(0, len(text), chunk_size):
        await asyncio.sleep(0.05)
        yield ("mock", text[i:i + chunk_size])

# -- Model names --------------------------------------------------------------
CLOUD_MODEL       = "gemini-flash-lite-latest"   # 2.0-flash-lite was sunset
LOCAL_MODEL       = "gemma3n:e2b"
CEREBRAS_MODEL    = "gpt-oss-120b"
OPENROUTER_MODEL  = "meta-llama/llama-3.3-70b-instruct:free"
TOGETHER_MODEL    = "meta-llama/Llama-3.3-70B-Instruct-Turbo"
MISTRAL_MODEL        = "mistral-small-latest"
MISTRAL_VISION_MODEL = "pixtral-12b-2409"
COHERE_MODEL      = "command-a-03-2025"   # Cohere v2 API
DEEPSEEK_MODEL    = "deepseek-chat"
DEEPINFRA_MODEL   = "meta-llama/Llama-3.3-70B-Instruct-Turbo"
HUGGINGFACE_MODEL = "meta-llama/Llama-3.3-70B-Instruct"
NOVITA_MODEL      = "meta-llama/llama-3.3-70b-instruct"
SCALEWAY_MODEL    = "llama-3.1-8b-instruct"
FIREWORKS_MODEL   = "accounts/fireworks/models/llama-v3p3-70b-instruct"
AIML_MODEL        = "meta-llama/Llama-3.3-70B-Instruct-Turbo"
KLUSTER_MODEL     = "klusterai/Meta-Llama-3.3-70B-Instruct-Turbo"
GITHUB_MODEL      = "meta-llama-3.3-70b-instruct"
NVIDIA_MODEL      = os.environ.get("NVIDIA_MODEL", "nvidia/nemotron-3-super-120b-a12b")   # set NVIDIA_MODEL in .env to override; make_nvidia_streamer falls back automatically if it returns 410/404
SAMBANOVA_MODEL   = "Meta-Llama-3.3-70B-Instruct"
HYPERBOLIC_MODEL  = "meta-llama/Llama-3.3-70B-Instruct"
LEPTON_MODEL      = "llama3-3-70b"
UPSTAGE_MODEL     = "solar-mini"
INFERENET_MODEL   = "meta-llama/llama-3.3-70b-instruct"
ANYSCALE_MODEL    = "meta-llama/Llama-3.3-70b-Instruct"

_genai_client = None
_local_client = None

if MODE in ("auto", "online") and os.environ.get("GOOGLE_API_KEY"):
    try:
        from google import genai
        _genai_client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    except Exception as e:
        print(f"[ai_providers] Gemini client init failed: {e}")

if MODE in ("auto", "offline"):
    try:
        import ollama
        _local_client = ollama
    except Exception:
        _local_client = None

# Shared async HTTP client - reused across requests instead of opening a new
# connection per call, which is both faster and friendlier to concurrency.
_http_client = None

def _get_http_client():
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(timeout=httpx.Timeout(45.0, connect=10.0, read=30.0))
    return _http_client

async def aclose_http_client():
    """Call on app shutdown to cleanly close the shared client."""
    global _http_client
    if _http_client is not None and not _http_client.is_closed:
        await _http_client.aclose()


# ============ Provider event logging (feeds admin.py /admin/provider-health) ============

def init_provider_events_db():
    """
    Create the provider_events table on startup. Records every provider
    call's outcome (success / empty / error) so the admin Provider Health
    dashboard can show real success/failure rates instead of just terminal
    logs. Called once from server.py at startup - safe to call repeatedly.
    """
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS provider_events (
            id         BIGSERIAL PRIMARY KEY,
            provider   TEXT NOT NULL,
            event      TEXT NOT NULL,
            detail     TEXT,
            created_at TEXT DEFAULT (now_iso())
        )
    """)
    conn.commit()
    conn.close()
    print("[ai_providers] provider_events DB ready.")


def _log_provider_event(provider: str, event: str, detail: str = ""):
    """
    Best-effort insert into provider_events. Never raises - a logging
    failure (e.g. DB momentarily locked) must never take down an actual
    AI call, so any error here is swallowed and printed instead.
    """
    try:
        conn = _get_conn()
        conn.execute(
            "INSERT INTO provider_events (provider, event, detail) VALUES (?, ?, ?)",
            (provider, event, (detail or "")[:500])
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[ai_providers] provider_events logging failed: {e}")


def _strip_asterisks(text: str) -> str:
    """
    Every provider prompt already says 'no markdown', but models still
    leak **bold** / *emphasis* asterisks sometimes. Rather than trying to
    parse markdown pairs (which breaks across stream chunk boundaries -
    a '**' can easily land split across two pieces), this just removes the
    asterisk character outright. Safe because legitimate WAEC tutoring
    content essentially never needs a literal '*' (multiplication is
    written as '×' or 'x' throughout the app's prompts).
    """
    return text.replace("*", "") if text else text


# ============ Connectivity check ============

_CONNECTIVITY_CACHE_SECONDS = 30
_last_check_time   = 0.0
_last_check_result = True

def is_online(force: bool = False) -> bool:
    """
    Still uses a quick blocking socket check - this is a ~1-2ms local
    operation (not a network round trip to an AI provider), so it does not
    meaningfully block other requests. Cached for 30s either way.
    """
    global _last_check_time, _last_check_result
    now = time.time()
    if not force and (now - _last_check_time) < _CONNECTIVITY_CACHE_SECONDS:
        return _last_check_result
    try:
        sock = socket.create_connection(("8.8.8.8", 53), timeout=2)
        sock.close()
        _last_check_result = True
    except (socket.timeout, OSError):
        _last_check_result = False
    _last_check_time = now
    return _last_check_result

def resolve_mode() -> str:
    if MODE == "online":  return "online"
    if MODE == "offline": return "offline"
    return "online" if is_online() else "offline"



# ============ NVIDIA: survive model retirements ============
# NVIDIA retires hosted models often and answers with HTTP 410 Gone (nemotron-3-super
# was retired on 2026-10-03, llama-3.3-70b before it). Instead of editing the model
# name by hand each time, this asks NVIDIA which models THIS key can use (GET /v1/models),
# tries the best candidate, remembers the one that works, and only does the
# lookup again if that one is retired too.
_NVIDIA_BASE = "https://integrate.api.nvidia.com/v1"
_nvidia_state = {"model": None, "retry_default_at": 0.0}
# Fallback order. Confirmed working on the owner's key: super, lightning and nano-omni.
# (ultra answered 503 and nano-3-30b answered 404 "not found for account" when tested.)
_NVIDIA_PREFERRED = [
    "nvidia/nemotron-3-super-120b-a12b",
    "nvidia/nemotron-3.5-lightning-30b-a3b",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
    "nvidia/nemotron-3-ultra-550b-a55b",
]
_NVIDIA_SKIP = ("embed", "safety", "guard", "reward", "retriev", "rerank", "parse", "clip", "ocr",
                "audio", "speech", "asr", "tts", "image", "-vl", "vision")

async def _nvidia_discover(api_key: str, avoid=()) -> list:
    """Chat-capable Nemotron model ids this key can see, best first, minus `avoid`."""
    client = _get_http_client()
    resp = await client.get(f"{_NVIDIA_BASE}/models", headers={"Authorization": f"Bearer {api_key}"}, timeout=15.0)
    resp.raise_for_status()
    ids = [m.get("id", "") for m in resp.json().get("data", [])]
    usable = [i for i in ids if i and i not in avoid and "nemotron" in i.lower()
              and not any(x in i.lower() for x in _NVIDIA_SKIP)]
    ranked = [p for p in _NVIDIA_PREFERRED if p in usable]
    return ranked + sorted(i for i in usable if i not in ranked)

def make_nvidia_streamer(api_key: str, default_model: str):
    async def _stream(system_prompt: str, history: list, user_message: str):
        if not api_key:
            raise RuntimeError("NVIDIA_API_KEY not set")
        tried = set()
        # Use the model that last worked, but give the configured model another chance
        # every 30 minutes (a 410 can be temporary or rolled out unevenly).
        if _nvidia_state["model"] and time.time() < _nvidia_state["retry_default_at"]:
            model = _nvidia_state["model"]
        else:
            model = default_model
        use_extra = True
        queue = []
        for _ in range(5):
            tried.add(model)
            # Nemotron 3 thinks by default and thinking tokens eat max_tokens, so turn it
            # off. If a model rejects these options (HTTP 400), retry once without them.
            extra = ({"chat_template_kwargs": {"enable_thinking": False, "force_nonempty_content": True}}
                     if use_extra and "nemotron-3" in model else None)
            inner = _make_compat_streamer(_NVIDIA_BASE, api_key, model, extra_body=extra)
            yielded = False
            try:
                async for piece in inner(system_prompt, history, user_message):
                    yielded = True
                    yield piece
                if yielded:
                    if _nvidia_state["model"] != model:
                        print(f"[ai_providers] NVIDIA is now using model: {model}")
                    _nvidia_state["model"] = model
                    if model == default_model:
                        _nvidia_state["retry_default_at"] = 0.0
                return
            except httpx.HTTPStatusError as e:
                code = e.response.status_code
                if yielded:
                    raise
                if code == 400 and extra is not None:
                    use_extra = False
                    continue
                if code in (404, 410, 502, 503):
                    # 404/410: retired or not enabled for this account. 502/503: overloaded right now.
                    # Either way, try another model instead of failing the whole request.
                    print(f"[ai_providers] NVIDIA model {model} returned HTTP {code}; trying another model...")
                    _nvidia_state["model"] = None
                    _nvidia_state["retry_default_at"] = time.time() + (1800 if code in (404, 410) else 120)
                    if not queue:
                        queue = await _nvidia_discover(api_key, avoid=tried)
                    queue = [m for m in queue if m not in tried]
                    if not queue:
                        raise
                    model, use_extra = queue.pop(0), True
                    continue
                raise
        raise RuntimeError("NVIDIA: no working model found on this key")
    return _stream

# ============ Provider order ============
# Which provider answers first. Set PROVIDER_ORDER in .env to a comma-separated list of
# provider names, best first, for example:   PROVIDER_ORDER=gemini,nvidia,cohere
# Providers you list are tried in that order, any others follow in their usual order,
# and the offline model always stays last. Unset = the built-in order.
def _apply_provider_order(providers):
    wanted = [x.strip().lower() for x in os.environ.get("PROVIDER_ORDER", "").split(",") if x.strip()]
    if not wanted:
        return providers
    rank = {tag: i for i, tag in enumerate(wanted)}
    cloud = [p for p in providers if p[0] != "offline"]
    tail = [p for p in providers if p[0] == "offline"]
    cloud.sort(key=lambda p: rank.get(p[0], len(wanted)))   # stable: unlisted keep their order
    return cloud + tail


# ============ Provider cooldowns ============
# A provider that just failed with "bad key / no credit / model gone" will fail
# again on the very next call. Without this, every exam question batch retried
# ~11 dead providers before reaching a working one (or the slow local model).
# Failing providers are skipped for a while, then retried automatically.
_cooldown_until: dict = {}

def _err_text(e: Exception) -> str:
    # str(e) is empty for timeouts, so always include the exception type.
    return f"{type(e).__name__}: {e}"

def _note_failure(tag: str, e: Exception) -> None:
    if tag == "offline":
        return
    status = getattr(getattr(e, "response", None), "status_code", None)
    if status in (401, 402, 403, 404, 410):
        secs = 1800          # key / credit / model problem: unlikely to fix itself soon
    elif status == 429 or isinstance(e, httpx.TimeoutException):
        secs = 90            # rate limit or slow: try again shortly
    else:
        secs = 30
    _cooldown_until[tag] = time.time() + secs

def _note_success(tag: str) -> None:
    _cooldown_until.pop(tag, None)

def _filter_cooldown(providers):
    now = time.time()
    live = [(t, f) for t, f in providers if t == "offline" or _cooldown_until.get(t, 0) <= now]
    # If every cloud provider is cooling down, try them all again rather than
    # dropping straight to the local model.
    return live if any(t != "offline" for t, _ in live) else providers


ALL_PROVIDER_KEYS = [
    "MISTRAL_API_KEY", "GOOGLE_API_KEY", "CEREBRAS_API_KEY", "OPENROUTER_API_KEY",
    "TOGETHER_API_KEY", "COHERE_API_KEY", "DEEPSEEK_API_KEY", "DEEPINFRA_API_KEY",
    "HUGGINGFACE_API_KEY", "NOVITA_API_KEY", "SCALEWAY_API_KEY", "FIREWORKS_API_KEY",
    "AIML_API_KEY", "KLUSTER_API_KEY", "GITHUB_TOKEN", "NVIDIA_API_KEY",
    "SAMBANOVA_API_KEY", "HYPERBOLIC_API_KEY", "LEPTON_API_KEY",
    "UPSTAGE_API_KEY", "INFERENCE_NET_API_KEY", "ANYSCALE_API_KEY",
    "ZEROONE_API_KEY", "MOONSHOT_API_KEY", "ZHIPU_API_KEY", "CF_API_TOKEN",
]


# ============ Inference backends (all async generators) ============

async def _stream_cloud(system_prompt: str, history: list, user_message: str,
                         image_b64: str = "", image_mime: str = ""):
    """Gemini via the SDK's async client (real streaming)."""
    from google.genai import types

    contents = []
    for turn in history:
        role = "model" if turn["role"] == "assistant" else "user"
        contents.append(types.Content(role=role, parts=[types.Part(text=turn["content"])]))
    user_parts = []
    if image_b64 and image_mime:
        raw = image_b64.split(",", 1)[-1]
        user_parts.append(types.Part.from_bytes(data=base64.b64decode(raw), mime_type=image_mime))
    user_parts.append(types.Part(text=user_message))
    contents.append(types.Content(role="user", parts=user_parts))
    # An EMPTY system_instruction makes the SDK raise "content is required"
    # (exam/analytics calls pass system_prompt=""), so only send it when set.
    config = types.GenerateContentConfig(system_instruction=system_prompt or None)

    stream = _genai_client.aio.models.generate_content_stream(
        model=CLOUD_MODEL, contents=contents, config=config
    )
    if inspect.isawaitable(stream):   # SDK versions differ
        stream = await stream
    async for chunk in stream:
        if chunk.text:
            yield chunk.text


async def _stream_local(system_prompt: str, history: list, user_message: str):
    """
    Ollama's client is also sync/blocking. Same thread-bridging approach -
    collect all chunks in a worker thread, then yield them async.
    """
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    def _sync_collect():
        chunks = []
        for chunk in _local_client.chat(model=LOCAL_MODEL, messages=messages, stream=True):
            piece = chunk.get("message", {}).get("content", "")
            if piece:
                chunks.append(piece)
        return chunks

    chunks = await asyncio.to_thread(_sync_collect)
    for piece in chunks:
        yield piece


async def _stream_mistral(system_prompt: str, history: list, user_message: str,
                           image_b64: str = "", image_mime: str = ""):
    """
    Mistral text + vision in one streamer. Uses Pixtral only when an image
    is actually attached (costs more / not needed for plain text turns),
    otherwise uses the regular fast text model.
    """
    api_key = os.environ.get("MISTRAL_API_KEY", "")
    if not api_key:
        raise RuntimeError("MISTRAL_API_KEY not set")

    messages = [{"role": "system", "content": system_prompt}]
    for turn in history[-20:]:
        messages.append({"role": turn["role"], "content": turn["content"]})

    if image_b64:
        mime = image_mime or "image/jpeg"
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": user_message},
                {"type": "image_url", "image_url": f"data:{mime};base64,{image_b64}"},
            ]
        })
        model = MISTRAL_VISION_MODEL
    else:
        messages.append({"role": "user", "content": user_message})
        model = MISTRAL_MODEL

    payload = {
        "model": model, "messages": messages, "stream": True, "max_tokens": 1024,
        "stream_options": {"include_usage": True},  # ask for real token counts in the final chunk
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    # For the cost-tracking fallback estimate, in case Mistral doesn't
    # honour stream_options above (unverified from this environment - see
    # api_costs.py's accuracy caveat).
    input_text_for_estimate = system_prompt + user_message + "".join(t["content"] for t in history[-20:])
    output_chars = 0
    real_usage = None

    client = _get_http_client()
    try:
        async with client.stream("POST", "https://api.mistral.ai/v1/chat/completions",
                                  json=payload, headers=headers) as resp:
            resp.raise_for_status()
            async for raw_line in resp.aiter_lines():
                line = raw_line.strip()
                if not line.startswith("data: "):
                    continue
                ps = line[6:]
                if ps == "[DONE]":
                    break
                try:
                    chunk = json.loads(ps)
                    if chunk.get("usage"):
                        real_usage = chunk["usage"]
                    delta = chunk["choices"][0]["delta"].get("content", "") if chunk.get("choices") else ""
                    if delta:
                        output_chars += len(delta)
                        yield delta
                except Exception:
                    continue
    finally:
        from api_costs import log_mistral_usage, estimate_tokens
        if real_usage:
            log_mistral_usage(model, real_usage.get("prompt_tokens", 0),
                               real_usage.get("completion_tokens", 0), is_estimate=False)
        else:
            log_mistral_usage(model, estimate_tokens(input_text_for_estimate),
                               max(1, output_chars // 4), is_estimate=True)


def _make_compat_streamer(base_url: str, api_key: str, model: str,
                           extra_headers: dict = None, extra_body: dict = None):
    """Returns an async generator function for any OpenAI-compatible endpoint."""

    async def _stream(system_prompt: str, history: list, user_message: str):
        if not api_key:
            raise RuntimeError(f"API key not set for {base_url}")
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        for turn in history[-20:]:
            messages.append({"role": turn["role"], "content": turn["content"]})
        messages.append({"role": "user", "content": user_message})
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "max_tokens": 1024,
        }
        if extra_body:
            payload.update(extra_body)
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        if extra_headers:
            headers.update(extra_headers)

        client = _get_http_client()
        url = f"{base_url.rstrip('/')}/chat/completions"

        async with client.stream("POST", url, json=payload, headers=headers) as resp:
            resp.raise_for_status()
            async for raw_line in resp.aiter_lines():
                line = raw_line.strip()
                if not line.startswith("data: "):
                    continue
                ps = line[6:]
                if ps == "[DONE]":
                    break
                try:
                    choices = json.loads(ps).get("choices") or []
                    delta = choices[0]["delta"].get("content") if choices else None
                    if delta:
                        yield delta
                except Exception:
                    continue

    return _stream


async def _stream_cohere(system_prompt: str, history: list, user_message: str):
    """Cohere v2 chat API (the v1 /chat endpoint now returns 404)."""
    key = os.environ.get("COHERE_API_KEY", "")
    if not key:
        raise RuntimeError("COHERE_API_KEY not set")
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    for turn in history[-20:]:
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": user_message})
    payload = {"model": COHERE_MODEL, "messages": messages, "stream": True, "max_tokens": 1024}
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    client = _get_http_client()
    async with client.stream("POST", "https://api.cohere.com/v2/chat",
                              json=payload, headers=headers) as resp:
        resp.raise_for_status()
        async for raw_line in resp.aiter_lines():
            line = raw_line.strip()
            if line.startswith("data:"):
                line = line[5:].strip()
            if not line.startswith("{"):
                continue
            try:
                obj = json.loads(line)
                if obj.get("type") == "content-delta":
                    text = (obj.get("delta", {}).get("message", {})
                               .get("content", {}).get("text", ""))
                    if text:
                        yield text
            except Exception:
                continue


async def _stream_cloudflare(system_prompt: str, history: list, user_message: str):
    token      = os.environ.get("CF_API_TOKEN", "")
    account_id = os.environ.get("CF_ACCOUNT_ID", "")
    if not token or not account_id:
        raise RuntimeError("CF_API_TOKEN or CF_ACCOUNT_ID not set")
    messages = [{"role": "system", "content": system_prompt}]
    for turn in history[-20:]:
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": user_message})
    payload = {"messages": messages, "stream": True, "max_tokens": 1024}
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/meta/llama-3.3-70b-instruct-fp8-fast"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    client = _get_http_client()
    async with client.stream("POST", url, json=payload, headers=headers) as resp:
        resp.raise_for_status()
        async for raw_line in resp.aiter_lines():
            line = raw_line.strip()
            if not line.startswith("data: "):
                continue
            ps = line[6:]
            if ps == "[DONE]":
                break
            try:
                delta = json.loads(ps).get("response", "")
                if delta:
                    yield delta
            except Exception:
                continue


# ============ Build the provider list ============

def _build_providers(system_prompt: str, history: list, user_message: str,
                      image_b64: str = "", image_mime: str = ""):
    """Returns list of (tag, no-arg ASYNC generator fn) in priority order."""
    env = os.environ.get
    providers = []

    def _wrap(streamer_fn):
        # Compat providers (~20 of them below, everything except Mistral
        # and Gemini above) are text-only — none accept image input. If
        # the chain falls through to one of these with an image attached
        # (Mistral AND Gemini both failed), the image was previously
        # dropped with zero acknowledgment: the provider would just
        # answer the text portion with no idea an image existed, which
        # reads strangely for a question like "what's wrong with this
        # equation in the photo?" with no photo. Matches the same
        # clarifying-note pattern already used for offline/Ollama mode in
        # stream_with_fallback below.
        msg = user_message
        if image_b64:
            msg = user_message + ("\n[Student attached an image, but this AI provider cannot view images. "
                                   "Answer based on the text only, and gently ask the student to describe "
                                   "what's in the image if it seems relevant.]")
        return lambda: streamer_fn(system_prompt, history, msg)

    if env("MISTRAL_API_KEY"):
        providers.append((
            "mistral",
            lambda: _stream_mistral(system_prompt, history, user_message, image_b64, image_mime)
        ))

    if _genai_client:
        providers.append((
            "gemini",
            lambda: _stream_cloud(system_prompt, history, user_message, image_b64, image_mime)
        ))

    if env("NVIDIA_API_KEY"):
        providers.append(("nvidia", _wrap(make_nvidia_streamer(env("NVIDIA_API_KEY"), NVIDIA_MODEL))))

    if env("CEREBRAS_API_KEY"):
        providers.append(("cerebras", _wrap(_make_compat_streamer(
            "https://api.cerebras.ai/v1", env("CEREBRAS_API_KEY"), CEREBRAS_MODEL
        ))))

    if env("OPENROUTER_API_KEY"):
        providers.append(("openrouter", _wrap(_make_compat_streamer(
            "https://openrouter.ai/api/v1", env("OPENROUTER_API_KEY"), OPENROUTER_MODEL,
            extra_headers={"HTTP-Referer": "https://naijasensei.app", "X-Title": "NaijaSensei"}
        ))))

    if env("TOGETHER_API_KEY"):
        providers.append(("together", _wrap(_make_compat_streamer(
            "https://api.together.xyz/v1", env("TOGETHER_API_KEY"), TOGETHER_MODEL
        ))))

    if env("COHERE_API_KEY"):
        providers.append(("cohere", lambda: _stream_cohere(system_prompt, history, user_message)))

    if env("DEEPSEEK_API_KEY"):
        providers.append(("deepseek", _wrap(_make_compat_streamer(
            "https://api.deepseek.com/v1", env("DEEPSEEK_API_KEY"), DEEPSEEK_MODEL
        ))))

    if env("DEEPINFRA_API_KEY"):
        providers.append(("deepinfra", _wrap(_make_compat_streamer(
            "https://api.deepinfra.com/v1/openai", env("DEEPINFRA_API_KEY"), DEEPINFRA_MODEL
        ))))

    if env("HUGGINGFACE_API_KEY"):
        providers.append(("huggingface", _wrap(_make_compat_streamer(
            "https://router.huggingface.co/v1", env("HUGGINGFACE_API_KEY"), HUGGINGFACE_MODEL
        ))))

    if env("NOVITA_API_KEY"):
        providers.append(("novita", _wrap(_make_compat_streamer(
            "https://api.novita.ai/v3/openai", env("NOVITA_API_KEY"), NOVITA_MODEL
        ))))

    if env("SCALEWAY_API_KEY"):
        providers.append(("scaleway", _wrap(_make_compat_streamer(
            "https://api.scaleway.ai/v1", env("SCALEWAY_API_KEY"), SCALEWAY_MODEL
        ))))

    if env("FIREWORKS_API_KEY"):
        providers.append(("fireworks", _wrap(_make_compat_streamer(
            "https://api.fireworks.ai/inference/v1", env("FIREWORKS_API_KEY"), FIREWORKS_MODEL
        ))))

    if env("AIML_API_KEY"):
        providers.append(("aimlapi", _wrap(_make_compat_streamer(
            "https://api.aimlapi.com/v1", env("AIML_API_KEY"), AIML_MODEL
        ))))

    if env("KLUSTER_API_KEY"):
        providers.append(("kluster", _wrap(_make_compat_streamer(
            "https://api.kluster.ai/v1", env("KLUSTER_API_KEY"), KLUSTER_MODEL
        ))))

    if env("GITHUB_TOKEN"):
        providers.append(("github", _wrap(_make_compat_streamer(
            "https://models.inference.ai.azure.com", env("GITHUB_TOKEN"), GITHUB_MODEL
        ))))

    if env("SAMBANOVA_API_KEY"):
        providers.append(("sambanova", _wrap(_make_compat_streamer(
            "https://api.sambanova.ai/v1", env("SAMBANOVA_API_KEY"), SAMBANOVA_MODEL
        ))))

    if env("HYPERBOLIC_API_KEY"):
        providers.append(("hyperbolic", _wrap(_make_compat_streamer(
            "https://api.hyperbolic.xyz/v1", env("HYPERBOLIC_API_KEY"), HYPERBOLIC_MODEL
        ))))

    if env("LEPTON_API_KEY"):
        providers.append(("lepton", _wrap(_make_compat_streamer(
            "https://llama3-3-70b.lepton.run/api/v1", env("LEPTON_API_KEY"), LEPTON_MODEL
        ))))

    if env("UPSTAGE_API_KEY"):
        providers.append(("upstage", _wrap(_make_compat_streamer(
            "https://api.upstage.ai/v1/solar", env("UPSTAGE_API_KEY"), UPSTAGE_MODEL
        ))))

    if env("INFERENCE_NET_API_KEY"):
        providers.append(("inference_net", _wrap(_make_compat_streamer(
            "https://api.inference.net/v1", env("INFERENCE_NET_API_KEY"), INFERENET_MODEL
        ))))

    if env("ANYSCALE_API_KEY"):
        providers.append(("anyscale", _wrap(_make_compat_streamer(
            "https://api.endpoints.anyscale.com/v1", env("ANYSCALE_API_KEY"), ANYSCALE_MODEL
        ))))

    if env("ZEROONE_API_KEY"):
        providers.append(("zeroone", _wrap(_make_compat_streamer(
            "https://api.01.ai/v1", env("ZEROONE_API_KEY"), "yi-large"
        ))))

    if env("MOONSHOT_API_KEY"):
        providers.append(("moonshot", _wrap(_make_compat_streamer(
            "https://api.moonshot.cn/v1", env("MOONSHOT_API_KEY"), "moonshot-v1-8k"
        ))))

    if env("ZHIPU_API_KEY"):
        providers.append(("zhipu", _wrap(_make_compat_streamer(
            "https://open.bigmodel.cn/api/paas/v4", env("ZHIPU_API_KEY"), "glm-4-flash"
        ))))

    if env("LM_STUDIO_ENABLED"):
        providers.append(("lmstudio", _wrap(_make_compat_streamer(
            "http://localhost:1234/v1", "lm-studio", "local-model"
        ))))

    if env("CF_API_TOKEN") and env("CF_ACCOUNT_ID"):
        providers.append(("cloudflare", lambda: _stream_cloudflare(system_prompt, history, user_message)))

    if _local_client is not None:
        providers.append(("offline", lambda: _stream_local(system_prompt, history, user_message)))

    return _apply_provider_order(providers)


# ============ Main fallback orchestrators (all async) ============

async def stream_with_fallback(system_prompt: str, history: list, user_message: str,
                                image_b64: str = "", image_mime: str = ""):
    """
    Used by /chat. Async-yields (provider_tag, text_chunk) tuples.
    Tries all configured providers in priority order until one succeeds.
    """
    if MOCK_AI:
        async for tag, chunk in _mock_stream(user_message):
            yield (tag, chunk)
        return

    chosen = resolve_mode()

    if chosen == "offline":
        if _local_client is None:
            raise RuntimeError("Offline mode but Ollama is not installed.")
        if image_b64:
            async for piece in _stream_local(system_prompt, history,
                user_message + "\n[Student uploaded image but offline model cannot view it. Ask them to describe it.]"):
                yield ("offline", _strip_asterisks(piece))
        else:
            async for piece in _stream_local(system_prompt, history, user_message):
                yield ("offline", _strip_asterisks(piece))
        return

    providers = _build_providers(system_prompt, history, user_message, image_b64, image_mime)
    if not providers:
        raise RuntimeError("No providers available. Add at least one API key to .env or install Ollama.")
    providers = _filter_cooldown(providers)

    last_error = None
    for tag, fn in providers:
        chunks_sent = 0
        try:
            print(f"[ai_providers] Trying: {tag.upper()}...")
            async for piece in fn():
                chunks_sent += 1
                yield (tag, _strip_asterisks(piece))
            if chunks_sent > 0:
                print(f"[ai_providers] OK {tag.upper()} succeeded ({chunks_sent} chunks)")
                _log_provider_event(tag, "success")
                _note_success(tag)
                return
            print(f"[ai_providers] {tag.upper()} returned empty - trying next...")
            _log_provider_event(tag, "empty")
        except Exception as e:
            last_error = e
            print(f"[ai_providers] {tag.upper()} failed: {_err_text(e)[:120]}")
            _log_provider_event(tag, "error", _err_text(e))
            _note_failure(tag, e)
            if chunks_sent > 0:
                # This provider already streamed part of an answer to the
                # caller before dying mid-stream. Falling through to the next
                # provider here would silently glue a second, independently-
                # generated full answer onto the end of that partial one -
                # the student would see something like "Newton's first law
                # sta[provider switch]Newton's first law states that...".
                # A cut-off answer with a clear notice is far less confusing
                # than a garbled, duplicated one, so stop here instead of
                # trying the next provider.
                print(f"[ai_providers] {tag.upper()} died mid-stream after "
                      f"{chunks_sent} chunk(s) - stopping instead of switching "
                      f"providers, to avoid a garbled/duplicated reply.")
                yield (tag, "\n\n[Connection interrupted - the answer above may "
                             "be cut off. Please ask again if it looks incomplete.]")
                return
            continue

    raise RuntimeError(f"All {len(providers)} providers failed. Last error: {last_error}")


async def call_ai_with_fallback(prompt: str, max_tokens: int = 2000) -> str:
    """
    Non-streaming single-prompt call with full fallback chain.
    Used by exam.py for question generation and theory marking.
    Returns the full text response as a string.
    """
    if MOCK_AI:
        await asyncio.sleep(0.05)
        return _mock_response_for(prompt)

    chosen = resolve_mode()

    if chosen == "offline":
        if _local_client is None:
            raise RuntimeError("Offline mode but Ollama is not installed.")

        def _sync_call():
            response = _local_client.chat(
                model=LOCAL_MODEL,
                messages=[{"role": "user", "content": prompt}],
                options={"num_predict": max_tokens}
            )
            return response.get("message", {}).get("content", "")

        return await asyncio.to_thread(_sync_call)

    providers = _build_providers(system_prompt="", history=[], user_message=prompt)
    if not providers:
        raise RuntimeError("No providers available. Add at least one API key to .env or install Ollama.")
    providers = _filter_cooldown(providers)

    last_error = None
    for tag, fn in providers:
        try:
            print(f"[ai_providers] (non-stream) Trying: {tag.upper()}...")
            full_text = ""
            async for piece in fn():
                full_text += _strip_asterisks(piece)
            if full_text.strip():
                print(f"[ai_providers] OK {tag.upper()} succeeded ({len(full_text)} chars)")
                _log_provider_event(tag, "success")
                _note_success(tag)
                return full_text
            print(f"[ai_providers] {tag.upper()} returned empty - trying next...")
            _log_provider_event(tag, "empty")
        except Exception as e:
            last_error = e
            print(f"[ai_providers] {tag.upper()} failed: {_err_text(e)[:120]}")
            _log_provider_event(tag, "error", _err_text(e))
            _note_failure(tag, e)
            continue

    raise RuntimeError(f"All {len(providers)} providers failed. Last error: {last_error}")


async def stream_simple_with_fallback(prompt: str, max_tokens: int = 2000):
    """
    Streaming single-prompt call with full fallback chain (no chat history).
    Used by analytics.py for study plan generation.
    Async-yields (provider_tag, text_chunk) tuples.
    """
    if MOCK_AI:
        async for tag, chunk in _mock_stream(prompt):
            yield (tag, chunk)
        return

    chosen = resolve_mode()

    if chosen == "offline":
        if _local_client is None:
            raise RuntimeError("Offline mode but Ollama is not installed.")
        async for piece in _stream_local("", [], prompt):
            yield ("offline", _strip_asterisks(piece))
        return

    providers = _build_providers(system_prompt="", history=[], user_message=prompt)
    if not providers:
        raise RuntimeError("No providers available. Add at least one API key to .env or install Ollama.")
    providers = _filter_cooldown(providers)

    last_error = None
    for tag, fn in providers:
        chunks_sent = 0
        try:
            print(f"[ai_providers] (stream-simple) Trying: {tag.upper()}...")
            async for piece in fn():
                chunks_sent += 1
                yield (tag, _strip_asterisks(piece))
            if chunks_sent > 0:
                print(f"[ai_providers] OK {tag.upper()} succeeded ({chunks_sent} chunks)")
                _log_provider_event(tag, "success")
                _note_success(tag)
                return
            print(f"[ai_providers] {tag.upper()} returned empty - trying next...")
            _log_provider_event(tag, "empty")
        except Exception as e:
            last_error = e
            print(f"[ai_providers] {tag.upper()} failed: {_err_text(e)[:120]}")
            _log_provider_event(tag, "error", _err_text(e))
            _note_failure(tag, e)
            if chunks_sent > 0:
                # Same reasoning as stream_with_fallback: don't glue a fresh
                # answer from a different provider onto a partial one.
                print(f"[ai_providers] {tag.upper()} died mid-stream after "
                      f"{chunks_sent} chunk(s) - stopping instead of switching "
                      f"providers, to avoid a garbled/duplicated reply.")
                yield (tag, "\n\n[Connection interrupted - the text above may "
                             "be cut off. Please try generating again.]")
                return
            continue

    raise RuntimeError(f"All {len(providers)} providers failed. Last error: {last_error}")