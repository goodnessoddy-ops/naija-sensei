"""
db.py — PostgreSQL connection layer for NaijaSensei.

WHY THIS EXISTS
Every route file used to do `sqlite3.connect("naija_sensei.db")` per
request via auth.py's `_get_conn()`. SQLite serializes all writes through
one file lock and lives on one disk, on one process — it cannot be shared
across multiple app server replicas, and it starts throwing
"database is locked" under real concurrent load. Past a few thousand
students this is a hard ceiling, not a tuning problem. This module swaps
the storage engine for pooled PostgreSQL connections that many replicas
can share, without changing the data model or the call-site shape the
rest of the codebase already uses.

DESIGN GOAL: change the engine, not the code above it.
Every file in this codebase does:
    conn = _get_conn()
    conn.execute("... WHERE id = ? ...", (some_id,))   # sqlite-style '?'
    row = conn.execute(...).fetchone()                  # dict-like row
    cursor = conn.execute("INSERT ...")
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
This module's `_get_conn()` returns a thin wrapper that supports exactly
that surface — '?' placeholders, dict-like rows, `.lastrowid`, `.commit()`,
`.close()` — backed by a pooled psycopg2 connection instead of a fresh
sqlite3.connect(). That means every plain SELECT/INSERT/UPDATE/DELETE
across admin.py, dashboard.py, exam.py, etc. keeps working completely
unchanged. Only two categories of SQL needed hand-editing in each file:
  1. CREATE TABLE / ALTER TABLE statements — DDL syntax genuinely differs
     (INTEGER PRIMARY KEY AUTOINCREMENT -> BIGSERIAL PRIMARY KEY, etc).
  2. The handful of INSERTs that read back `cursor.lastrowid` — Postgres
     doesn't hand back a rowid for free like SQLite does, so those specific
     INSERTs were given an explicit `RETURNING id`, which this wrapper
     captures into `.lastrowid` automatically.

TIMESTAMPS STAY TEXT, NOT NATIVE TIMESTAMP
admin.py, analytics.py, dashboard.py, exam.py and auth.py all read
timestamp columns back as plain ISO-8601 strings — string-sliced
(`row["started_at"][:10]`) or parsed with `datetime.fromisoformat(...)`.
To avoid touching every one of those call sites (and risking a format
mismatch), every timestamp column stays a TEXT column, and every SQL-level
`datetime('now')` default was mechanically replaced with `now_iso()`, a
Postgres function (defined below) that returns a string in exactly the
shape `datetime.utcnow().isoformat()` produces — same separator, same
microsecond precision. Nothing downstream can tell the difference.

DEPLOYMENT
Set DATABASE_URL, e.g.:
  postgresql://naijasensei:PASSWORD@your-db-host:5432/naijasensei
Tune DB_POOL_MIN / DB_POOL_MAX per replica — see the note at the bottom
of this file on sizing pools across multiple app server processes.
"""

import os
import re
import threading
from datetime import datetime

import psycopg2
import psycopg2.extras
import psycopg2.pool

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://naijasensei:naijasensei@localhost:5432/naijasensei",
)
# Keep these modest per-replica — see sizing note at the bottom of this
# file. Total connections across all replicas must stay under Postgres's
# max_connections (or, better, sit behind PgBouncer in transaction mode).
POOL_MIN = int(os.environ.get("DB_POOL_MIN", "5"))
POOL_MAX = int(os.environ.get("DB_POOL_MAX", "20"))

_pool = None
_pool_lock = threading.Lock()
_helpers_ready = False


def _now_iso() -> str:
    """Python-side equivalent of the now_iso() SQL function below — for
    call sites that need to pass a timestamp explicitly rather than
    relying on a column DEFAULT (e.g. re-stamping a row on update)."""
    return datetime.utcnow().isoformat()


def _init_pool():
    global _pool
    if _pool is not None:
        return
    with _pool_lock:
        if _pool is None:
            _pool = psycopg2.pool.ThreadedConnectionPool(
                POOL_MIN,
                POOL_MAX,
                dsn=DATABASE_URL,
                cursor_factory=psycopg2.extras.RealDictCursor,
            )
            print(f"[db] Postgres pool ready (min={POOL_MIN}, max={POOL_MAX}).")
    _ensure_helpers()


def _ensure_helpers():
    """Create the now_iso() SQL helper function once. Safe to call
    repeatedly (CREATE OR REPLACE). Every CREATE TABLE's
    `DEFAULT now_iso()` and every inline `now_iso()` call in an
    INSERT/UPDATE across the codebase depends on this existing first,
    so it must run before any of the per-module init_*_db() functions."""
    global _helpers_ready
    if _helpers_ready:
        return
    conn = _pool.getconn()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE OR REPLACE FUNCTION now_iso() RETURNS TEXT AS $$
                SELECT replace((NOW() AT TIME ZONE 'UTC')::timestamp::text, ' ', 'T');
            $$ LANGUAGE SQL STABLE;
        """)
        conn.commit()
        _helpers_ready = True
    finally:
        _pool.putconn(conn)


_QMARK_RE = re.compile(r"\?")


def _translate(sql: str) -> str:
    """SQLite '?' placeholders -> Postgres '%s'. This codebase never uses
    a literal '?' character outside of parameter placeholders in its SQL
    strings, so a blind substitution is safe."""
    return _QMARK_RE.sub("%s", sql)


class _CursorResult:
    """Wraps a psycopg2 cursor to keep the sqlite3.Cursor surface the
    rest of the codebase already calls: .fetchone(), .fetchall(),
    .lastrowid. `.lastrowid` is populated only when the executed SQL
    contains RETURNING (added explicitly at the ~7 INSERT call sites
    that read `cursor.lastrowid`) — none of those call sites also fetch
    from the same cursor afterward, so eagerly consuming that one row
    here is safe."""

    __slots__ = ("_cur", "lastrowid")

    def __init__(self, cur, has_returning: bool):
        self._cur = cur
        self.lastrowid = None
        if has_returning:
            row = cur.fetchone()
            if row and "id" in row:
                self.lastrowid = row["id"]

    def fetchone(self):
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()

    def __getattr__(self, name):
        return getattr(self._cur, name)


class _Connection:
    """Wraps a pooled psycopg2 connection to keep the sqlite3.Connection
    surface (`conn.execute(sql, params)`, `.commit()`, `.close()`) the
    rest of the codebase already calls."""

    __slots__ = ("_conn",)

    def __init__(self, pg_conn):
        self._conn = pg_conn

    def execute(self, sql, params=()):
        translated = _translate(sql)
        cur = self._conn.cursor()
        cur.execute(translated, tuple(params) if params else None)
        has_returning = "RETURNING" in translated.upper()
        return _CursorResult(cur, has_returning)

    def executescript(self, sql):
        cur = self._conn.cursor()
        cur.execute(_translate(sql))

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        """Return the connection to the pool rather than actually
        closing the socket. Roll back any leftover open transaction
        first (e.g. a read-only path that never called .commit()) so it
        never leaks into whichever caller borrows this connection next."""
        try:
            self._conn.rollback()
        except Exception:
            pass
        try:
            _pool.putconn(self._conn)
        except Exception:
            try:
                self._conn.close()
            except Exception:
                pass


def _get_conn() -> _Connection:
    """Drop-in replacement for the old sqlite3-backed _get_conn() in
    auth.py. Borrows a connection from the pool instead of opening a new
    OS-level connection every call."""
    _init_pool()
    pg_conn = _pool.getconn()
    return _Connection(pg_conn)


# ─────────────────────────────────────────────────────────────────────────
# SIZING NOTE, for whoever deploys this:
#
# POOL_MIN/POOL_MAX here are PER REPLICA. If you run N app server
# processes (Gunicorn/uvicorn workers or separate containers), total
# Postgres connections can reach N * POOL_MAX. Postgres's default
# max_connections is 100 — that's exhausted fast once you're running
# enough replicas to serve 1M+ students. Two ways to fix this, and you
# likely want both eventually:
#   1. Put PgBouncer (transaction pooling mode) between the app and
#      Postgres, and point DATABASE_URL at PgBouncer instead of Postgres
#      directly. Then this pool's job is just to avoid re-handshaking
#      PgBouncer on every request; PgBouncer is what actually keeps the
#      real Postgres-side connection count bounded regardless of how many
#      app replicas you run.
#   2. Raise Postgres's max_connections and size POOL_MAX so
#      N * POOL_MAX stays comfortably under it, with headroom for
#      migrations/admin tools.
# ─────────────────────────────────────────────────────────────────────────