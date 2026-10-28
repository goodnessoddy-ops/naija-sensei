/**
 * sw.js — App shell cache for NaijaSensei.
 *
 * WHY THIS EXISTS
 * Found in testing: on-device chat (see index.html's offline-mode code)
 * only works once the page is already open and running in a live tab.
 * If the student closes the tab, restarts the browser, or does a hard
 * refresh while genuinely offline, the browser has to re-fetch
 * index.html itself from the network to load the app at all — and with
 * no connection and nothing cached, that just shows the browser's own
 * generic "You are viewing an offline copy of this page" / no-connection
 * screen instead of NaijaSensei. That's a browser fallback, not anything
 * this app controls — the only fix is a service worker that actually
 * caches the app shell so the browser has something real to serve.
 *
 * STRATEGY
 * - The page itself (navigation requests) and the core JS/CSS it needs:
 *   network-first, falling back to cache. This means anyone with a
 *   connection always gets the current version (so a bug fix like this
 *   one actually reaches them), and only falls back to the last cached
 *   version when truly offline.
 * - Large static assets that rarely change (Three.js, lucide, the avatar
 *   videos): cache-first, since re-fetching multi-MB files on every
 *   single load just to confirm they're unchanged is wasteful — network
 *   is used to fill the cache the first time, and to refresh it in the
 *   background afterward (stale-while-revalidate).
 * - Anything that isn't a same-origin GET (every API call — /chat,
 *   /auth/*, /sync/*, /admin/*, etc. — and all POST/PUT/DELETE requests)
 *   passes straight through untouched. This service worker only serves
 *   the page shell; it must never intercept or cache real API traffic,
 *   which already has its own offline handling built into index.html
 *   (the on-device model, the sync queue, per-feature offline gating).
 *
 * BUMPING THE CACHE VERSION
 * Increment CACHE_VERSION any time SHELL_ASSETS changes, or any time an
 * old cached index.html could otherwise keep being served to a returning
 * visitor after a real update. The activate handler below deletes every
 * cache that doesn't match the current version.
 */

const CACHE_VERSION = "ns-shell-v3";
const SHELL_CACHE = `${CACHE_VERSION}-shell`;
const ASSET_CACHE = `${CACHE_VERSION}-assets`;

// Precached on install — the minimum needed to actually render the app
// with zero network. Deliberately does NOT include offline-queue-demo.html
// or admin.html (not part of the student-facing shell).
//
// NOTE: this deliberately does NOT include "/index.html" — server.py only
// exposes @app.get("/") (which serves index.html's contents), there is no
// route at the literal path /index.html, so fetching it 404s. cache.addAll()
// fails its entire call if even one URL in the list 404s, which meant the
// whole install handler below was silently rejecting on every install and
// SHELL_ASSETS was never actually being cached. "/" is what must be listed
// here and is also the only URL requests actually load the page from.
const SHELL_ASSETS = ["/", "/manifest.json"];

// Fetched eagerly during install — small/medium assets every student
// needs regardless of whether they ever touch offline mode.
//
// Kept deliberately small. The avatar videos and the Three.js files used to be
// downloaded here for every new install, but: the videos are only used by the
// Classroom (which needs the internet anyway), and Three.js only runs on the
// desktop login screen. Fetching them up front cost every phone several MB on
// its very first visit. The videos are now left to the browser's own HTTP cache
// (they are also range-requested, which a service worker cache can't serve
// reliably), and Three.js moved to LAZY_ASSET_PATHS below.
const EAGER_ASSET_PATHS = [
  "/static/lucide.min.js",   // nav icons, needed to render the app shell offline
  "/static/logo.png",        // header + login logo
];

// LAZY_ASSET_PATHS are NOT downloaded during install — only cached the
// first time they're actually requested (which the fetch handler below
// still does with the same cache-first-then-refresh strategy). This is
// deliberately separate from EAGER_ASSET_PATHS: the self-hosted WebLLM
// bundle is ~6.6MB, and most students never enable offline mode, so
// forcing that download on every single install would be a real data
// cost for no benefit to them. It still gets fixed for the students who
// DO use it — the first time they enable offline mode (or send an
// offline-mode chat) while they have a connection, this gets cached
// into ASSET_CACHE and persists there across reloads/tab closes, which
// is the actual bug this is meant to fix (previously the JS module
// itself was re-fetched from a CDN on every fresh page load with no
// persistence at all).
const LAZY_ASSET_PATHS = [
  "/static/web-llm.js",
  "/static/three.core.min.js",     // desktop login-screen 3D scene only
  "/static/three.module.min.js",
];

// Every path eligible for the cache-first-then-refresh runtime strategy
// in the fetch handler below, whether or not it was eagerly precached.
const ASSET_PATHS = [...EAGER_ASSET_PATHS, ...LAZY_ASSET_PATHS];

self.addEventListener("install", (event) => {
  event.waitUntil(
    (async () => {
      const shellCache = await caches.open(SHELL_CACHE);
      await shellCache.addAll(SHELL_ASSETS);
      const assetCache = await caches.open(ASSET_CACHE);
      // addAll() would fail the whole install if even one asset 404s —
      // add individually instead so one missing/renamed file (e.g. during
      // active development) doesn't block the rest of the shell from
      // being cached at all.
      await Promise.all(
        EAGER_ASSET_PATHS.map((path) =>
          fetch(path)
            .then((res) => (res.ok ? assetCache.put(path, res) : null))
            .catch(() => null)
        )
      );
      // Activate this version immediately rather than waiting for every
      // open tab to close first — see the "skipWaiting" note in the
      // registration code in index.html for why that's the right choice
      // for a school app where re-opening the tab is the realistic
      // update path, not necessarily closing every tab first.
      self.skipWaiting();
    })()
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      const names = await caches.keys();
      await Promise.all(
        names
          .filter((name) => name.startsWith("ns-shell-") && !name.startsWith(CACHE_VERSION))
          .map((name) => caches.delete(name))
      );
      // Reclaim space: earlier versions precached the avatar videos.
      const assetCache = await caches.open(ASSET_CACHE);
      for (const r of await assetCache.keys()) {
        if (r.url.endsWith(".mp4")) await assetCache.delete(r);
      }
      await self.clients.claim();
    })()
  );
});

const SHELL_NETWORK_TIMEOUT_MS = 3500;

// Network-first, but not at any cost:
//  - If the network answers in time with a good (2xx) response, use it and refresh
//    the cache, so people with a connection always get the current version.
//  - If it is slow (a "connected" WiFi/data plan with no real internet can hang for
//    a minute), errors out, or returns a server error page, serve the cached copy
//    instead of leaving the student staring at a blank screen. The request keeps
//    going in the background and refreshes the cache for next time.
//  - Error responses are never written to the cache, so a bad response (a 502, or a
//    tunnel's interstitial page) can't overwrite the good cached app.
function _shellSig(res) {
  return res.headers.get("etag") || ((res.headers.get("last-modified") || "") + "|" + (res.headers.get("content-length") || ""));
}
async function _notifyShellUpdated() {
  const all = await self.clients.matchAll({ type: "window" });
  all.forEach((c) => c.postMessage({ type: "shell-updated" }));
}

async function shellNetworkFirst(event, req, key, timeoutMs = SHELL_NETWORK_TIMEOUT_MS) {
  const cache = await caches.open(SHELL_CACHE);
  const cached = await cache.match(key);
  // If the saved copy has to be served (slow or failed network) and the network later
  // delivers a NEWER version, tell the page so it can offer a reload. Without this, a
  // phone on a slow connection could keep showing an old build without anyone knowing.
  const state = { servedCached: false, changed: false };

  const networkPromise = fetch(req).then(async (res) => {
    if (res.ok) {
      state.changed = !!cached && _shellSig(cached) !== _shellSig(res);
      await cache.put(key, res.clone());
      if (state.changed && state.servedCached) _notifyShellUpdated();
    }
    return res;
  });

  // Nothing cached yet (first ever visit): the network is the only option.
  if (!cached) return networkPromise;

  // Keep the worker alive so the background refresh can finish.
  event.waitUntil(networkPromise.catch(() => {}));

  const timeout = new Promise((resolve) => setTimeout(() => resolve(null), timeoutMs));
  try {
    const res = await Promise.race([networkPromise, timeout]);
    if (res && res.ok) return res;
  } catch (e) {
    /* offline: fall through to the cached copy */
  }
  state.servedCached = true;
  if (state.changed) _notifyShellUpdated();
  return cached;
}

function isAssetPath(pathname) {
  return ASSET_PATHS.includes(pathname);
}

self.addEventListener("fetch", (event) => {
  const req = event.request;
  const url = new URL(req.url);

  // Only ever touch same-origin GET requests. Everything else (API
  // calls, cross-origin CDN imports like the WebLLM/webgpu module, any
  // non-GET method) passes straight to the network untouched.
  if (req.method !== "GET" || url.origin !== self.location.origin) {
    return;
  }

  // Navigations (loading the page itself) and the shell's own files:
  // network-first, with the cached copy as the fallback.
  if (req.mode === "navigate" || SHELL_ASSETS.includes(url.pathname)) {
    // Navigations are cached under "/" - the actual server route that serves the
    // page - not "/index.html", which doesn't exist as a route (see SHELL_ASSETS).
    const key = req.mode === "navigate" ? "/" : url.pathname;
    event.respondWith(shellNetworkFirst(event, req, key));
    return;
  }

  // Large, rarely-changing static assets: cache-first, refreshed in the
  // background so a real update still arrives eventually without making
  // every load wait on a multi-MB re-fetch first.
  if (isAssetPath(url.pathname)) {
    event.respondWith(
      (async () => {
        const cache = await caches.open(ASSET_CACHE);
        const cached = await cache.match(req);
        const networkFetch = fetch(req)
          .then((res) => { if (res.ok) cache.put(req, res.clone()); return res; })
          .catch(() => null);
        return cached || (await networkFetch) || new Response("", { status: 504 });
      })()
    );
  }
});

// ── Push notifications: "Mr. Sensei replied" ─────────────────────────────
// The server sends a push when a reply finishes (see _maybe_push in server.py), even if
// the student has closed the app. If the app is open and visible the page already shows
// the reply, so no notification is needed.
self.addEventListener("push", (event) => {
  let data = {};
  try { data = event.data ? event.data.json() : {}; }
  catch (e) { data = { body: event.data ? event.data.text() : "" }; }
  event.waitUntil((async () => {
    const wins = await self.clients.matchAll({ type: "window", includeUncontrolled: true });
    if (wins.some((w) => w.visibilityState === "visible")) return;
    await self.registration.showNotification(data.title || "Mr. Sensei replied", {
      body: data.body || "Your answer is ready.",
      icon: "/static/logo.png",
      tag: data.tag || "chat-reply",       // same tag: a newer reply replaces the old notification
      renotify: true,
      data: { url: data.url || "/", thread: data.thread || "general" },
    });
  })());
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const d = event.notification.data || {};
  event.waitUntil((async () => {
    const wins = await self.clients.matchAll({ type: "window", includeUncontrolled: true });
    for (const w of wins) {
      if ("focus" in w) {
        await w.focus();
        w.postMessage({ type: "open-thread", thread: d.thread || "general" });
        return;
      }
    }
    if (self.clients.openWindow) await self.clients.openWindow(d.url || "/");
  })());
});