"""
test_languages.py — One-off script to test which of your active AI providers
handles Yoruba, Hausa, and Igbo best WITHOUT switching to English.

Usage:
  python test_languages.py

Reads API keys from your .env file (same one server.py uses).
Prints each provider's raw response side by side so you can compare quality.
"""

import os
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv()

TEST_MESSAGES = {
    "Yoruba":  "Bawo ni mo se le yanju percentage?",
    "Hausa":   "Yaya zan iya warware lissafin percentage?",
    "Igbo":    "Biko kowaa m otu esi edozi nsogbu percentage",
}

SYSTEM_PROMPT = (
    "You are a tutor for Nigerian secondary school students. "
    "CRITICAL: reply ONLY in the exact same language the student used. "
    "Do not switch to English. Do not mix languages. If the student wrote "
    "in Yoruba, your entire reply must be in Yoruba. If Hausa, entire reply "
    "in Hausa. If Igbo, entire reply in Igbo. Explain the math topic simply "
    "in 3-4 sentences in that language only."
)


def call_openai_compat(name, base_url, api_key, model, message, extra_headers=None):
    if not api_key:
        return f"[{name}] SKIPPED — no API key set"
    try:
        payload = json.dumps({
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
            "max_tokens": 300,
        }).encode()
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        if extra_headers:
            headers.update(extra_headers)
        req = urllib.request.Request(f"{base_url.rstrip('/')}/chat/completions", data=payload, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[{name}] FAILED — {str(e)[:150]}"


def call_cohere(api_key, message):
    if not api_key:
        return "[Cohere] SKIPPED — no API key set"
    try:
        payload = json.dumps({
            "model": "command-r",
            "message": message,
            "preamble": SYSTEM_PROMPT,
            "max_tokens": 300,
        }).encode()
        req = urllib.request.Request(
            "https://api.cohere.com/v1/chat", data=payload,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        return data.get("text", "").strip()
    except Exception as e:
        return f"[Cohere] FAILED — {str(e)[:150]}"


def main():
    providers = [
        ("Cerebras",   lambda msg: call_openai_compat("Cerebras", "https://api.cerebras.ai/v1",
                        os.environ.get("CEREBRAS_API_KEY", ""), "llama-4-scout", msg)),
        ("OpenRouter", lambda msg: call_openai_compat("OpenRouter", "https://openrouter.ai/api/v1",
                        os.environ.get("OPENROUTER_API_KEY", ""), "meta-llama/llama-3.3-70b-instruct:free", msg,
                        extra_headers={"HTTP-Referer": "https://naijasensei.app", "X-Title": "NaijaSensei"})),
        ("Mistral",    lambda msg: call_openai_compat("Mistral", "https://api.mistral.ai/v1",
                        os.environ.get("MISTRAL_API_KEY", ""), "mistral-small-latest", msg)),
        ("Cohere",     lambda msg: call_cohere(os.environ.get("COHERE_API_KEY", ""), msg)),
        ("AIML API",   lambda msg: call_openai_compat("AIML API", "https://api.aimlapi.com/v1",
                        os.environ.get("AIML_API_KEY", ""), "meta-llama/Llama-3.3-70B-Instruct-Turbo", msg)),
    ]

    for lang, message in TEST_MESSAGES.items():
        print("\n" + "=" * 70)
        print(f"LANGUAGE: {lang}   |   Sent: {message}")
        print("=" * 70)
        for name, fn in providers:
            print(f"\n--- {name} ---")
            result = fn(message)
            print(result)

    print("\n" + "=" * 70)
    print("DONE. Read each block above and judge:")
    print("  1. Did it reply in the correct language the whole way through?")
    print("  2. Did the sentences make actual sense (not repeated fragments)?")
    print("  3. Did it explain the math correctly?")
    print("Pick whichever provider did best per language.")
    print("=" * 70)


if __name__ == "__main__":
    main()