/**
 * offline-queue.js — Generic offline write queue for NaijaSensei's
 * on-device AI mode.
 *
 * WHAT THIS IS FOR
 * When a student uses the on-device model with no network connection,
 * any resulting message can't reach the server in real time. This module
 * stores those writes in the browser's IndexedDB (survives page reloads
 * and app restarts, unlike an in-memory array) and flushes them to the
 * server automatically the next time the device is actually online.
 *
 * IDEMPOTENCY IS THE WHOLE POINT
 * Every queued item gets a client-generated UUID (`client_id`) at the
 * moment it's created, before any network attempt. If a sync request
 * succeeds on the server but the response never makes it back (e.g. the
 * connection drops at that exact moment), this module will retry the
 * same item with the SAME client_id next time. The server's /sync/*
 * endpoints are built to treat a repeated client_id as a no-op, not a
 * duplicate insert — see sync.py's docstring. Never regenerate a
 * client_id for an item that's already been queued once.
 *
 * USAGE (see offline-ai-poc.html for a full worked example)
 *
 *   import { OfflineQueue } from "./offline-queue.js";
 *   const queue = new OfflineQueue({
 *     apiBase: "https://your-naijasensei-server.com",
 *     getToken: () => localStorage.getItem("access_token"),
 *     onQueueChange: (pendingCount) => updateBadge(pendingCount),
 *   });
 *
 *   // Whenever the on-device model produces a message:
 *   await queue.enqueue("chat_message", {
 *     role: "assistant",
 *     content: replyText,
 *     subject: currentSubject,
 *     topic: currentTopic,
 *   });
 *
 *   // Call once on page load, and the queue also auto-syncs on the
 *   // browser's 'online' event and on a periodic timer while online:
 *   queue.startAutoSync();
 */

const DB_NAME = "naijasensei-offline-queue";
const DB_VERSION = 1;
const STORE = "outbox";

// (queue item "kind" -> server endpoint + how to shape the batch body).
// Add a new entry here for each new offline-write type you wire up
// (e.g. "exam_answer" once that flow is built) — everything else in this
// file is generic and doesn't need to change.
const SYNC_ROUTES = {
  chat_message: {
    endpoint: "/sync/offline-messages",
    buildBody: (items) => ({
      messages: items.map((it) => ({
        client_id: it.client_id,
        role: it.payload.role,
        content: it.payload.content,
        subject: it.payload.subject ?? null,
        topic: it.payload.topic ?? null,
        created_at_device: it.created_at,
      })),
    }),
  },
};

function openDb() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(STORE)) {
        const store = db.createObjectStore(STORE, { keyPath: "client_id" });
        store.createIndex("kind", "kind", { unique: false });
        store.createIndex("status", "status", { unique: false });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

function uuid() {
  if (crypto.randomUUID) return crypto.randomUUID();
  // Fallback for older WebViews without crypto.randomUUID.
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export class OfflineQueue {
  /**
   * @param {Object} opts
   * @param {string} opts.apiBase - e.g. "https://api.naijasensei.com" (no trailing slash)
   * @param {() => string|null} opts.getToken - returns the current JWT, or null if not logged in
   * @param {(pendingCount: number) => void} [opts.onQueueChange] - called after every enqueue/sync
   * @param {number} [opts.syncIntervalMs] - periodic retry while online (default 30s)
   * @param {number} [opts.maxAttempts] - give up on a permanently-broken item after this many tries (default 10)
   */
  constructor(opts) {
    this.apiBase = opts.apiBase.replace(/\/$/, "");
    this.getToken = opts.getToken;
    this.onQueueChange = opts.onQueueChange || (() => {});
    this.syncIntervalMs = opts.syncIntervalMs || 30000;
    this.maxAttempts = opts.maxAttempts || 10;
    this._dbPromise = openDb();
    this._syncing = false;
    this._timer = null;
  }

  async _withStore(mode, fn) {
    const db = await this._dbPromise;
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE, mode);
      const store = tx.objectStore(STORE);
      const result = fn(store);
      tx.oncomplete = () => resolve(result);
      tx.onerror = () => reject(tx.error);
    });
  }

  /** Queue one write. Returns the client_id so the caller can show
   * optimistic UI ("sending... queued for later") if useful. */
  async enqueue(kind, payload) {
    if (!SYNC_ROUTES[kind]) {
      throw new Error(`Unknown offline-queue kind "${kind}" — add it to SYNC_ROUTES first.`);
    }
    const item = {
      client_id: uuid(),
      kind,
      payload,
      created_at: new Date().toISOString(),
      status: "pending",
      attempts: 0,
      last_error: null,
    };
    await this._withStore("readwrite", (store) => store.put(item));
    await this._notifyChange();
    // Try immediately in case we're actually online — no reason to wait
    // for the next timer tick if the connection is fine right now.
    if (navigator.onLine) this.trySyncAll();
    return item.client_id;
  }

  async _getAllPending() {
    return this._withStore("readonly", (store) => {
      return new Promise((resolve, reject) => {
        const items = [];
        const req = store.openCursor();
        req.onsuccess = () => {
          const cursor = req.result;
          if (cursor) {
            if (cursor.value.status === "pending") items.push(cursor.value);
            cursor.continue();
          } else {
            resolve(items);
          }
        };
        req.onerror = () => reject(req.error);
      });
    }).then((p) => p); // unwrap the nested promise from _withStore
  }

  async pendingCount() {
    const items = await this._getAllPending();
    return items.length;
  }

  async _notifyChange() {
    this.onQueueChange(await this.pendingCount());
  }

  async _remove(clientId) {
    await this._withStore("readwrite", (store) => store.delete(clientId));
  }

  async _markAttempt(item, errorMsg) {
    item.attempts += 1;
    item.last_error = errorMsg;
    if (item.attempts >= this.maxAttempts) {
      item.status = "failed"; // stop retrying a request the server keeps rejecting
    }
    await this._withStore("readwrite", (store) => store.put(item));
  }

  /** Attempt to flush every pending item. Safe to call repeatedly and
   * concurrently — re-entrant calls are ignored while one is in flight. */
  async trySyncAll() {
    if (this._syncing) return;
    if (!navigator.onLine) return;
    const token = this.getToken();
    if (!token) return; // not logged in yet — nothing to sync against

    this._syncing = true;
    try {
      const pending = await this._getAllPending();
      if (pending.length === 0) return;

      // Group by kind so each server endpoint gets one batch call
      // instead of one request per queued item.
      const byKind = {};
      for (const item of pending) {
        if (item.attempts >= this.maxAttempts) continue; // give up quietly
        (byKind[item.kind] ||= []).push(item);
      }

      for (const [kind, items] of Object.entries(byKind)) {
        const route = SYNC_ROUTES[kind];
        let resp;
        try {
          resp = await fetch(this.apiBase + route.endpoint, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify(route.buildBody(items)),
          });
        } catch (networkErr) {
          // Still offline, or the request just failed in flight — leave
          // every item in this batch as pending, try again next tick.
          for (const item of items) await this._markAttempt(item, String(networkErr));
          continue;
        }

        if (!resp.ok) {
          const text = await resp.text().catch(() => resp.statusText);
          for (const item of items) await this._markAttempt(item, `HTTP ${resp.status}: ${text}`);
          continue;
        }

        const data = await resp.json();
        // Server reports per-item status; "synced" and "duplicate" both
        // mean this item is done and can be removed locally — duplicate
        // just means an earlier attempt already landed it server-side.
        const doneIds = new Set(
          (data.results || [])
            .filter((r) => r.status === "synced" || r.status === "duplicate")
            .map((r) => r.client_id)
        );
        for (const item of items) {
          if (doneIds.has(item.client_id)) {
            await this._remove(item.client_id);
          } else {
            await this._markAttempt(item, "Server did not confirm this item — will retry.");
          }
        }
      }
    } finally {
      this._syncing = false;
      await this._notifyChange();
    }
  }

  /** Call once, e.g. on app load. Syncs immediately if online, then
   * re-syncs on the browser's 'online' event and on a periodic timer. */
  startAutoSync() {
    if (navigator.onLine) this.trySyncAll();
    window.addEventListener("online", () => this.trySyncAll());
    if (this._timer) clearInterval(this._timer);
    this._timer = setInterval(() => this.trySyncAll(), this.syncIntervalMs);
  }

  stopAutoSync() {
    if (this._timer) clearInterval(this._timer);
    this._timer = null;
  }
}
