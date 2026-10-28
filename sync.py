"""
sync.py — Offline-queue sync endpoint for NaijaSensei's on-device AI path.

WHY THIS EXISTS
When a student uses the on-device model (running locally in-browser via
WebGPU/WebLLM, with no server involved) while genuinely offline, the
resulting conversation still needs to reach the server eventually — for
teacher/parent visibility (dashboard.py's activity views), the student's
own chat history, and analytics (analytics.py's topic mastery). Since
those messages were generated with no network connection, they get queued
client-side (see static/offline-queue.js) and flushed here in a batch the
next time the device actually has a connection.

WHY THIS NEEDS ITS OWN ENDPOINT INSTEAD OF REUSING auth.py's save_message()
A normal /chat request happens once, in real time, with the server
generating the AI reply itself — save_message() there never needs to worry
about being called twice for the same message. A queued offline message is
different: the client might successfully POST it here, then lose
connection again before it gets the 200 response, and retry the same
message on the next sync attempt. Without idempotency, that message would
be saved twice, corrupting chat history and (more importantly) analytics
and quota counts that assume one row per real message. Every row inserted
here is keyed by a client-generated `client_id` (a UUID minted on-device at
the moment the message was created), with a unique constraint enforced at
the database level via `ON CONFLICT DO NOTHING` (see the note in the insert below
for why no conflict target is given) — so retrying
the exact same batch any number of times has the same effect as sending it
once.

WHAT THIS DOES NOT DO
- Does not run the AI itself — these are messages the on-device model
  already generated locally. This endpoint only persists them.
- Does not affect the free-tier daily quota (log_chat_message_for_quota in
  auth.py) — quota is deliberately NOT charged retroactively for messages
  that were generated for free, on-device, while offline. Charging it
  after the fact would be confusing (a student could see a message appear
  in history that silently used up quota they didn't know was being
  spent) and defeats a real purpose of the offline mode: unmetered use
  when there's no connection anyway.
- Does not attempt real-time analytics recomputation per message — mastery
  scores etc. are computed on read (see analytics.py), not on write, so a
  batch insert here doesn't need special-case handling.
"""

import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

from auth import require_user, _get_conn

router = APIRouter(prefix="/sync", tags=["sync"])

# Defensive cap — a single sync batch should be a phone's worth of offline
# conversation, not an unbounded upload. Client should chunk larger queues
# into multiple calls if this is ever hit (see static/offline-queue.js).
MAX_BATCH_SIZE = 200


def init_sync_db():
    """
    Adds the columns/index this module needs onto chat_history, which
    already exists (created by auth.py's init_db()). Safe to call
    repeatedly — every statement here is idempotent. Must run AFTER
    auth.init_db() — see server.py's startup sequence.
    """
    conn = _get_conn()
    # client_id is nullable: normal online /chat messages (auth.py's
    # save_message) never set it and don't need to — idempotency only
    # matters for retried offline syncs, not for a single realtime insert.
    conn.execute("ALTER TABLE chat_history ADD COLUMN IF NOT EXISTS client_id TEXT")
    conn.execute("ALTER TABLE chat_history ADD COLUMN IF NOT EXISTS synced_from_offline INTEGER DEFAULT 0")
    # Partial unique index: only enforced where client_id is actually set,
    # so it doesn't collide with (or slow down) the many plain online rows
    # that leave it NULL.
    conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS chat_history_client_id_uidx
        ON chat_history (client_id) WHERE client_id IS NOT NULL
    """)
    conn.commit()
    conn.close()
    print("[sync] chat_history ready for offline sync (client_id column + unique index).")


# ── Schemas ───────────────────────────────────────────────────────────────

class QueuedMessage(BaseModel):
    client_id: str = Field(..., min_length=8, max_length=100)
    role: str                      # "user" or "assistant"
    content: str = Field(..., max_length=20000)
    subject: Optional[str] = None
    topic: Optional[str] = None
    # When the on-device model produced this, per the student's own clock.
    # Accepted for forwards-compatibility but NOT stored yet: rows get the
    # server's insert time, and the client sends each batch oldest-first so
    # the conversation keeps its order.
    created_at_device: Optional[str] = None
    on_device: bool = True          # always true today; reserved for a
                                     # future queued-write type sharing
                                     # this same sync path


class SyncBatchRequest(BaseModel):
    messages: List[QueuedMessage] = []


class SyncResult(BaseModel):
    client_id: str
    status: str        # "synced" | "duplicate" | "error"
    detail: Optional[str] = None


# ── Routes ────────────────────────────────────────────────────────────────

@router.post("/offline-messages", response_model=dict)
def sync_offline_messages(req: SyncBatchRequest, current_user: dict = Depends(require_user)):
    """
    Upload a batch of messages the on-device model generated while
    offline. Safe to call repeatedly with the same batch (e.g. after a
    dropped connection mid-sync) — already-synced client_ids are reported
    back as "duplicate", not re-inserted and not treated as an error.
    """
    if not req.messages:
        return {"results": [], "synced": 0, "duplicates": 0, "errors": 0}

    if len(req.messages) > MAX_BATCH_SIZE:
        raise HTTPException(
            413,
            f"Batch too large ({len(req.messages)} messages). "
            f"Split into batches of {MAX_BATCH_SIZE} or fewer."
        )

    conn = _get_conn()
    results: List[SyncResult] = []
    synced = duplicates = errors = 0

    try:
        for msg in req.messages:
            if msg.role not in ("user", "assistant"):
                results.append(SyncResult(client_id=msg.client_id, status="error",
                                           detail="role must be 'user' or 'assistant'"))
                errors += 1
                continue

            subject = (msg.subject or "").strip() or None
            topic = (msg.topic or "").strip() or None
            content = msg.content.replace("\x00", "")   # PostgreSQL rejects NUL characters

            # A SAVEPOINT per message: if one message is bad, only it is rolled back and
            # reported, instead of PostgreSQL aborting the whole batch.
            conn.execute("SAVEPOINT sync_msg")
            try:
                # NOTE: no conflict target on purpose. The unique index on client_id is a
                # PARTIAL index (WHERE client_id IS NOT NULL), and PostgreSQL only accepts
                # "ON CONFLICT (client_id)" for a partial index if the same WHERE clause is
                # repeated. Leaving the target out means "skip this row if it hits ANY unique
                # constraint", which is exactly what a duplicate client_id does.
                cursor = conn.execute(
                    """INSERT INTO chat_history
                           (user_id, role, content, subject, topic, client_id, synced_from_offline)
                       VALUES (?, ?, ?, ?, ?, ?, 1)
                       ON CONFLICT DO NOTHING
                       RETURNING id""",
                    (current_user["id"], msg.role, content, subject, topic, msg.client_id)
                )
                row = cursor.fetchone()
                conn.execute("RELEASE SAVEPOINT sync_msg")
            except Exception as e:
                conn.execute("ROLLBACK TO SAVEPOINT sync_msg")
                print(f"[sync] message {msg.client_id} rejected: {type(e).__name__}: {e}")
                results.append(SyncResult(client_id=msg.client_id, status="error",
                                           detail="could not be saved"))
                errors += 1
                continue

            if row:
                results.append(SyncResult(client_id=msg.client_id, status="synced"))
                synced += 1
            else:
                # ON CONFLICT DO NOTHING means no row came back: this client_id was
                # already synced in an earlier attempt. Not an error: that is the whole
                # point of idempotency.
                results.append(SyncResult(client_id=msg.client_id, status="duplicate"))
                duplicates += 1

        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"[sync] batch failed: {type(e).__name__}: {e}")
        raise HTTPException(500, "Sync failed on the server. Your messages are safe on your phone; please try again later.")

    # One last_active bump for the whole batch (mirrors auth.py's save_message). It runs
    # AFTER the messages are committed and can never fail the sync: a problem here
    # (for example the helper function missing) must not make the app retry messages
    # that were already saved.
    if synced:
        try:
            conn.execute("""
                INSERT INTO user_activity (user_id, last_active, warned)
                VALUES (?, now_iso(), 0)
                ON CONFLICT(user_id) DO UPDATE SET last_active=now_iso()
            """, (current_user["id"],))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"[sync] could not update last_active (messages were saved): {type(e).__name__}: {e}")

    conn.close()
    return {
        "results": [r.dict() for r in results],
        "synced": synced,
        "duplicates": duplicates,
        "errors": errors,
    }


@router.get("/status")
def sync_status(current_user: dict = Depends(require_user)):
    """
    How much offline-synced history exists for this student — mostly
    useful for the admin/parent dashboard to show "N messages happened
    offline" rather than being indistinguishable from normal chat.
    """
    conn = _get_conn()
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM chat_history WHERE user_id = ? AND synced_from_offline = 1",
        (current_user["id"],)
    ).fetchone()
    conn.close()
    return {"offline_synced_message_count": row["cnt"] if row else 0}