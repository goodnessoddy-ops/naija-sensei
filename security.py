"""
security.py — Automated security hardening for NaijaSensei.

WHAT THIS COVERS
  1. require_env_secret() — refuses to start the app if JWT_SECRET_KEY /
     ADMIN_PASSWORD / CREDENTIALS_ENCRYPTION_KEY aren't set to a real
     value. All three used to silently fall back to a hardcoded string
     baked into this repo's source (and shared in chat history while
     building this app) — those strings are now public. An app that
     refuses to start is far safer than one that starts up with a known
     secret and lets anyone forge an admin JWT, guess the admin panel
     password, or decrypt stored student credentials on the first try.
  2. RateLimitMiddleware — sliding-window request limiting per IP, with
     stricter limits on auth/admin/AI-calling endpoints.
  3. SecurityHeadersMiddleware — standard hardening headers most small
     apps skip (X-Frame-Options, X-Content-Type-Options, etc).
  4. LoginAttemptTracker — brute-force lockout on repeated failed
     logins, keyed by username.

STATE BACKEND: IN-MEMORY BY DEFAULT, REDIS WHEN CONFIGURED
Both the rate limiter and the login lockout tracker store their sliding
windows through a small pluggable interface (_SlidingWindowStore) with
two implementations:
  - _InMemorySlidingWindowStore — the default. Lives in this one
    process's memory. Fine for a single app replica; once you're running
    more than one (Phase 2 of the scaling plan from earlier in this
    build), an attacker distributing requests across replicas resets
    these limits per-replica, since each replica only sees its own share
    of the traffic.
  - _RedisSlidingWindowStore — used automatically the moment REDIS_URL
    is set in the environment (and the `redis` package is installed —
    it's in requirements.txt). Shared across every replica connected to
    the same Redis instance, so the limit is enforced against total
    traffic, not per-replica traffic. Falls back to in-memory with a
    clear warning if REDIS_URL is set but unreachable, rather than
    crashing the app over what should be a best-effort protection layer.

WHAT THIS DOESN'T COVER (be honest about the limits)
  - This is NOT a WAF. It won't stop DDoS-scale volumetric attacks, and
    it doesn't inspect payloads for SQL injection or XSS (the codebase's
    own parameterized queries via db.py already prevent SQL injection at
    the query layer — see db.py's docstring). For real production
    traffic, put this behind Cloudflare or a similar edge provider —
    that's where DDoS mitigation and WAF rules actually belong, not in
    application code.
  - Prompt-injection defense for the AI tutor already exists in
    server.py's chat handler (_JAILBREAK_RE + gray-zone reinforcement)
    and is out of scope for this file.
  - Redis being reachable is a soft dependency, not a hard one — if it's
    down, rate limiting/lockout silently degrades to per-process state
    rather than taking the whole app down with it. That's a deliberate
    choice (a rate limiter's own outage shouldn't cause a bigger outage
    than the thing it's protecting against), but it does mean a Redis
    outage quietly weakens this protection — worth alerting on.
"""

import os
import secrets
import sys
import threading
import time
import uuid
from collections import defaultdict, deque
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# ─────────────────────────────────────────────────────────────────────────
# Required secrets — fail fast instead of falling back to a public default
# ─────────────────────────────────────────────────────────────────────────

# Every one of these was, at some point, this codebase's own hardcoded
# fallback — now public. Refuse to start on any of them, not just the
# exact-match check on a missing env var, in case someone "fixes" the
# startup failure by literally pasting the old default back in.
_KNOWN_LEAKED_SECRETS = {
    "naija-sensei-change-this-in-production-2025",
    "naijasensei-admin-2025",
}
_WEAK_SECRETS = _KNOWN_LEAKED_SECRETS | {
    "changeme", "change-me", "password", "secret", "admin", "admin123",
    "letmein", "12345678", "password123",
}


def require_env_secret(env_var: str, min_length: int = 16) -> str:
    """
    Read a required secret from the environment. Exits the process
    immediately with a clear, actionable message if it's missing, too
    short, or a known-public former default — rather than silently
    falling back to something an attacker could already know.
    """
    value = os.environ.get(env_var, "").strip()

    if not value:
        sys.exit(
            f"\n[SECURITY] STARTUP REFUSED: {env_var} is not set.\n"
            f"  This used to silently fall back to a hardcoded default "
            f"that is now public — anyone who's seen this codebase could "
            f"use it to forge access. Generate a real secret:\n"
            f"      python -c \"import secrets; print(secrets.token_hex(32))\"\n"
            f"  then set {env_var}=<that value> in your .env file "
            f"(see .env.example) and restart.\n"
        )

    if value.lower() in _WEAK_SECRETS:
        sys.exit(
            f"\n[SECURITY] STARTUP REFUSED: {env_var} is set to a known "
            f"weak or leaked default value. Generate a real secret (see "
            f"the command above) and set a new value.\n"
        )

    if len(value) < min_length:
        sys.exit(
            f"\n[SECURITY] STARTUP REFUSED: {env_var} is only "
            f"{len(value)} characters — needs at least {min_length} for "
            f"its risk level. Generate a longer one:\n"
            f"      python -c \"import secrets; print(secrets.token_hex(32))\"\n"
        )

    return value


def constant_time_equals(a: str, b: str) -> bool:
    """Timing-safe string comparison — use for any secret/password
    comparison (e.g. admin.py's X-Admin-Password header check) instead
    of `==`, which leaks how many leading characters matched via
    response-time differences."""
    return secrets.compare_digest(a or "", b or "")


# ─────────────────────────────────────────────────────────────────────────
# Sliding-window storage backend — shared by the rate limiter and the
# login lockout tracker, since both are really the same primitive:
# "how many timestamped events happened for this key in the last N
# seconds, and when was the oldest one?"
# ─────────────────────────────────────────────────────────────────────────

class _SlidingWindowStore:
    """Interface both implementations below satisfy."""

    def count_recent(self, key: str, window: int) -> tuple[int, Optional[float]]:
        """Returns (count of events within the last `window` seconds,
        timestamp of the oldest one still in that window, or None)."""
        raise NotImplementedError

    def add(self, key: str, now: float, window: int):
        raise NotImplementedError

    def clear(self, key: str):
        raise NotImplementedError


class _InMemorySlidingWindowStore(_SlidingWindowStore):
    """Per-process fallback — see this module's docstring for the
    multi-replica caveat."""

    _CLEANUP_EVERY = 2000

    def __init__(self):
        self._data: dict = defaultdict(deque)
        self._lock = threading.Lock()
        self._ops = 0

    def count_recent(self, key, window):
        with self._lock:
            dq = self._data[key]
            cutoff = time.time() - window
            while dq and dq[0] < cutoff:
                dq.popleft()
            return len(dq), (dq[0] if dq else None)

    def add(self, key, now, window):
        with self._lock:
            self._data[key].append(now)
            self._ops += 1
            # Prevents unbounded memory growth from one-off keys (e.g.
            # scanners probing random IPs/paths) that will never recur.
            if self._ops % self._CLEANUP_EVERY == 0:
                stale = [k for k, dq in self._data.items() if not dq]
                for k in stale:
                    del self._data[k]

    def clear(self, key):
        with self._lock:
            self._data.pop(key, None)


class _RedisSlidingWindowStore(_SlidingWindowStore):
    """Sorted-set sliding window in Redis — one key per rate-limit
    bucket, members are unique per-event tokens scored by timestamp.
    Shared across every app replica connected to the same Redis
    instance, which is the whole point: an attacker distributing
    requests across replicas no longer resets the count per-replica."""

    def __init__(self, redis_client, prefix="ns_sw:"):
        self._r = redis_client
        self._prefix = prefix

    def _k(self, key: str) -> str:
        return f"{self._prefix}{key}"

    def count_recent(self, key, window):
        k = self._k(key)
        now = time.time()
        cutoff = now - window
        pipe = self._r.pipeline()
        pipe.zremrangebyscore(k, 0, cutoff)   # prune expired entries
        pipe.zrange(k, 0, 0, withscores=True)  # oldest remaining entry
        pipe.zcard(k)                          # current count
        _removed, oldest_result, count = pipe.execute()
        oldest = oldest_result[0][1] if oldest_result else None
        return count, oldest

    def add(self, key, now, window):
        k = self._k(key)
        member = f"{now}:{uuid.uuid4().hex[:8]}"  # unique even for same-millisecond hits
        pipe = self._r.pipeline()
        pipe.zadd(k, {member: now})
        pipe.expire(k, window + 5)  # a little slack past the window so a
        pipe.execute()               # quiet key doesn't linger forever

    def clear(self, key):
        self._r.delete(self._k(key))


def _build_sliding_window_store(label: str) -> _SlidingWindowStore:
    """Picks Redis if REDIS_URL is set and reachable, otherwise falls
    back to in-memory with a clear explanation of what that means. Never
    raises — a rate limiter failing to start shouldn't take the whole
    app down with it."""
    redis_url = os.environ.get("REDIS_URL", "").strip()
    if not redis_url:
        print(
            f"[security] REDIS_URL not set — {label} state is per-process "
            f"only. Fine for a single app replica; set REDIS_URL before "
            f"running multiple replicas, or an attacker distributing "
            f"requests across them resets this limit per-replica."
        )
        return _InMemorySlidingWindowStore()

    try:
        import redis as redis_pkg
    except ImportError:
        print(
            f"[security] REDIS_URL is set but the 'redis' package isn't "
            f"installed (pip install redis) — falling back to "
            f"per-process state for {label} in the meantime."
        )
        return _InMemorySlidingWindowStore()

    try:
        client = redis_pkg.from_url(redis_url, decode_responses=True, socket_timeout=2)
        client.ping()
        safe_target = redis_url.split("@")[-1]  # don't log embedded credentials
        print(f"[security] {label} backed by Redis at {safe_target} — shared across all app replicas.")
        return _RedisSlidingWindowStore(client)
    except Exception as e:
        print(
            f"[security] Could not connect to REDIS_URL for {label} "
            f"({e}) — falling back to per-process state. This will "
            f"silently weaken protection under multi-replica traffic "
            f"until Redis is reachable again — worth alerting on."
        )
        return _InMemorySlidingWindowStore()


# ─────────────────────────────────────────────────────────────────────────
# Rate limiting
# ─────────────────────────────────────────────────────────────────────────

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Per-IP sliding-window rate limiting. Stricter limits on
    login/register (brute-force + fake-account spam), the admin panel
    (password-guessing), and AI-calling endpoints (cost abuse) than on
    everything else. Backed by Redis when REDIS_URL is set — see this
    module's docstring.
    """

    # (path matcher, window in seconds, max requests in that window)
    RULES = [
        (lambda p: p in ("/auth/login", "/auth/register", "/dashboard/register-with-role"), 300, 10),
        (lambda p: p.startswith("/admin") or p.startswith("/billing/admin"), 300, 30),
        (lambda p: p in ("/chat", "/exam/start", "/exam/submit", "/career/guidance", "/predict/diagnostic/start"), 300, 40),
        # /billing/checkout and /billing/redeem are user-facing and
        # abuse-prone (checkout spam hits Paystack's API for no reason;
        # redeem is a code-guessing surface, even though the code space
        # is huge). /billing/webhook is deliberately NOT in this strict
        # group — it's Paystack calling US, already protected by HMAC
        # signature verification (see billing.py), and rate-limiting it
        # too aggressively risks dropping genuine payment notifications
        # during a legitimate burst (e.g. many students paying around
        # exam season). It falls through to the generous DEFAULT limit
        # below instead.
        (lambda p: p in ("/billing/checkout", "/billing/redeem"), 300, 15),
    ]
    DEFAULT_WINDOW = 300
    DEFAULT_MAX = 600

    def __init__(self, app, store: Optional[_SlidingWindowStore] = None):
        super().__init__(app)
        self._store = store or _build_sliding_window_store("rate limiting")

    @staticmethod
    def _client_ip(request) -> str:
        # X-Forwarded-For is only trustworthy if you're actually behind a
        # proxy/load balancer that sets it (Cloudflare, nginx, etc) — if
        # you're not, an attacker can spoof this header to evade the
        # per-IP limit entirely. Only trust it once you've confirmed your
        # deployment sits behind something that sets it correctly.
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _limit_for(self, path: str):
        for matcher, window, limit in self.RULES:
            if matcher(path):
                return window, limit
        return self.DEFAULT_WINDOW, self.DEFAULT_MAX

    async def dispatch(self, request, call_next):
        path = request.url.path
        window, limit = self._limit_for(path)
        ip = self._client_ip(request)
        key = f"{ip}:{path}"
        now = time.time()

        count, oldest = self._store.count_recent(key, window)
        if count >= limit:
            retry_after = max(1, int((oldest if oldest is not None else now) + window - now) + 1)
            return JSONResponse(
                {"detail": "Too many requests. Please slow down and try again shortly."},
                status_code=429,
                headers={"Retry-After": str(retry_after)},
            )

        self._store.add(key, now, window)
        return await call_next(request)


# ─────────────────────────────────────────────────────────────────────────
# Security headers
# ─────────────────────────────────────────────────────────────────────────

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Standard hardening headers. Deliberately does NOT set a
    Content-Security-Policy — a wrong CSP silently breaks frontend
    assets (inline scripts, third-party CDNs, etc), and this file
    doesn't have visibility into what the frontend actually loads.
    Add one once you've audited the frontend's script/style/image
    sources."""

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(self), camera=(self)")
        # HSTS only makes sense once you're actually serving over HTTPS —
        # setting it on a plain-HTTP deployment does nothing useful and
        # can cause problems if you ever need to fall back to HTTP.
        if request.url.scheme == "https":
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=63072000; includeSubDomains"
            )
        return response


# ─────────────────────────────────────────────────────────────────────────
# Login brute-force lockout
# ─────────────────────────────────────────────────────────────────────────

class LoginAttemptTracker:
    """
    Tracks failed login attempts per username and locks further attempts
    out for a cooldown window after too many failures. Complements
    RateLimitMiddleware's per-IP limit on /auth/login — this one blocks
    a distributed brute force against a SINGLE account from many
    different IPs, which the IP-based limiter alone can't catch. Backed
    by Redis when REDIS_URL is set — see this module's docstring.
    """

    MAX_ATTEMPTS = 6
    LOCKOUT_SECONDS = 15 * 60

    def __init__(self, store: Optional[_SlidingWindowStore] = None):
        self._store = store or _build_sliding_window_store("login lockout")

    @staticmethod
    def _key(username: str) -> str:
        return f"login:{(username or '').strip().lower()}"

    def is_locked(self, username: str) -> tuple[bool, int]:
        key = self._key(username)
        now = time.time()
        count, oldest = self._store.count_recent(key, self.LOCKOUT_SECONDS)
        if count >= self.MAX_ATTEMPTS:
            retry_after = max(1, int((oldest if oldest is not None else now) + self.LOCKOUT_SECONDS - now))
            return True, retry_after
        return False, 0

    def record_failure(self, username: str):
        key = self._key(username)
        self._store.add(key, time.time(), self.LOCKOUT_SECONDS)

    def record_success(self, username: str):
        self._store.clear(self._key(username))


# Module-level singleton — imported directly by auth.py's /login route.
# Both this and RateLimitMiddleware call _build_sliding_window_store()
# independently, so each gets its own Redis connection / in-memory store
# — they don't share state with each other, which is correct: a rate
# limit hit and a failed login are different kinds of events.
login_attempts = LoginAttemptTracker()