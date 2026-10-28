"""
api_costs.py — USD cost tracking for paid AI API usage (Mistral text,
ElevenLabs voice), feeding the /admin/api-costs dashboard tab.

PRICING — verified July 2026 directly against official provider pricing
pages, not third-party aggregators (several of which disagreed with each
other and, in places, with the official page):

  - Mistral Small (mistral-small-latest), this app's main text model:
    https://mistral.ai/pricing/api — $0.15 / 1M input tokens,
    $0.60 / 1M output tokens.

  - Pixtral 12B (pixtral-12b-2409), this app's vision model for messages
    with an attached image: NOT on Mistral's current official pricing
    table — Mistral has deprecated it in favour of newer vision models.
    This figure instead comes from third-party trackers (CloudPrice,
    Artificial Analysis, PricePerToken), which independently agree:
    $0.15 / 1M input tokens, $0.15 / 1M output tokens (legacy rate).

  - ElevenLabs (eleven_turbo_v2_5, this app's TTS model):
    https://elevenlabs.io/pricing/api — Turbo/Flash tier = $0.05 per
    1,000 characters. NOT the $0.10 Multilingual v2/v3 rate quoted on
    most ElevenLabs pricing summaries — this app specifically uses the
    cheaper Turbo model (see classroom.py's _text_to_speech).

Every other provider in the AI fallback chain (Gemini, Cohere,
Cloudflare, HuggingFace, and the rest) runs on a free tier in this app's
current config, so their cost is $0 and they're not tracked here. If that
ever changes (a provider moves to paid usage), add its pricing below and
a logging call at its call site, following the same pattern as Mistral.

ACCURACY CAVEAT — read before trusting these numbers to the last cent:
Mistral's streaming calls request exact usage data via
stream_options.include_usage. When that comes back, it's used directly
(real billed token counts, from Mistral itself). When it doesn't — the
flag isn't honoured, or the response shape differs from expected, both
unverified from this environment since there's no live API access here —
this falls back to an ESTIMATE: roughly 4 characters per token, a
standard rule of thumb for English text, not Mistral's actual tokenizer.
Every logged row carries is_estimate so you can always tell which numbers
are exact provider-reported billing data and which are approximations.
ElevenLabs character counts are always exact (it's literally len(text)
sent to the API) and never estimated.
"""

from auth import _get_conn

# USD per 1M tokens
MISTRAL_PRICING = {
    "mistral-small-latest": {"input": 0.15, "output": 0.60},
    "pixtral-12b-2409": {"input": 0.15, "output": 0.15},
}
# USD per 1,000 characters — Turbo/Flash tier (this app uses eleven_turbo_v2_5,
# not the pricier Multilingual v2/v3 tier)
ELEVENLABS_USD_PER_1K_CHARS = 0.05


def init_api_costs_db():
    """Create the api_usage_log table on startup. Safe to call repeatedly."""
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS api_usage_log (
            id            BIGSERIAL PRIMARY KEY,
            provider      TEXT NOT NULL,          -- 'mistral' or 'elevenlabs'
            model         TEXT,                   -- e.g. 'mistral-small-latest'
            kind          TEXT NOT NULL,           -- 'text' or 'tts'
            input_tokens  INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0,
            characters    INTEGER DEFAULT 0,       -- TTS only
            cost_usd      REAL NOT NULL,
            is_estimate   INTEGER DEFAULT 0,       -- 1 if token count is estimated, not exact
            created_at    TEXT DEFAULT (now_iso())
        )
    """)
    conn.commit()
    conn.close()
    print("[api_costs] api_usage_log DB ready.")


def estimate_tokens(text: str) -> int:
    """
    Rough fallback estimate: ~4 characters per token for English text.
    Only used when Mistral doesn't return real usage data for a call -
    see the accuracy caveat in this module's docstring.
    """
    return max(1, len(text or "") // 4)


def log_mistral_usage(model: str, input_tokens: int, output_tokens: int, is_estimate: bool = False):
    """
    Best-effort insert - never raises. A cost-logging failure (e.g. DB
    momentarily locked) must never take down an actual AI call, so any
    error here is swallowed and printed instead, matching the pattern
    used for provider_events logging in ai_providers.py.
    """
    try:
        pricing = MISTRAL_PRICING.get(model, MISTRAL_PRICING["mistral-small-latest"])
        cost = (input_tokens / 1_000_000 * pricing["input"]) + (output_tokens / 1_000_000 * pricing["output"])
        conn = _get_conn()
        conn.execute(
            """INSERT INTO api_usage_log (provider, model, kind, input_tokens, output_tokens, cost_usd, is_estimate)
               VALUES ('mistral', ?, 'text', ?, ?, ?, ?)""",
            (model, input_tokens, output_tokens, round(cost, 8), 1 if is_estimate else 0)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[api_costs] Failed to log Mistral usage: {e}")


def log_elevenlabs_usage(characters: int):
    """
    Best-effort insert for ElevenLabs TTS usage. Character count is
    always exact - it's literally len(text) sent to the API - so this
    is never flagged as an estimate.
    """
    try:
        cost = characters / 1000 * ELEVENLABS_USD_PER_1K_CHARS
        conn = _get_conn()
        conn.execute(
            """INSERT INTO api_usage_log (provider, model, kind, characters, cost_usd, is_estimate)
               VALUES ('elevenlabs', 'eleven_turbo_v2_5', 'tts', ?, ?, 0)""",
            (characters, round(cost, 8))
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[api_costs] Failed to log ElevenLabs usage: {e}")