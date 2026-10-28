# Running NaijaSensei fully offline, on one school's own server

This deployment puts the app, Postgres, and a local AI model (Ollama
running `gemma3n:e2b`) all on **one machine**, reachable by students over
the school's own LAN/WiFi. After first setup, it needs **zero internet
connectivity** to keep working.

If you instead want a public, internet-facing, cloud-hosted deployment
(multiple app replicas, managed Postgres, cloud AI providers, real
Paystack payments), use **DEPLOY.md** instead — it's the same codebase,
just different environment configuration (see `docker-compose.local.yml`'s
own comments for why one codebase supports both).

## Requirements

- One machine (a school's own PC or a small server) with Docker and
  Docker Compose installed.
- A few GB of free disk space (Postgres data + the `gemma3n:e2b` model).
- Internet access **once**, during first setup, to download the base
  Docker images and pull the model. Not needed after that.
- Optional but strongly recommended: an NVIDIA GPU on that machine, for
  much faster AI responses. Works fine on CPU too, just slower per reply.

## Setup

**1. Generate real secrets.**

```bash
./setup_local.sh
```

This writes `.env.local` with freshly generated `JWT_SECRET_KEY`,
`CREDENTIALS_ENCRYPTION_KEY`, `POSTGRES_PASSWORD`, and `ADMIN_PASSWORD`.
It refuses to overwrite an existing `.env.local`, so re-running it later
is safe. **Save the admin password it prints** — write it down or put it
in a password manager; it's shown once in the terminal output but stays
readable inside `.env.local` afterward.

Back up `.env.local` somewhere safe (not just this disk). Losing it means
losing access to the admin panel and to any encrypted student credentials
stored in the database.

**2. Start everything.**

```bash
docker compose --env-file .env.local -f docker-compose.local.yml up -d
```

First startup takes a while — Ollama needs to download the `gemma3n:e2b`
model (a few GB) exactly once, via the `ollama-pull` one-shot job. The app
container waits for that to finish successfully before it starts, so it
never tries to chat with a model that isn't there yet. Watch progress
with:

```bash
docker compose -f docker-compose.local.yml logs -f ollama-pull
```

**3. Connect from student devices.**

Find this machine's LAN IP (e.g. `192.168.1.50` — `ip addr` on Linux,
`ipconfig` on Windows), then from any device on the same WiFi/LAN, visit:

```
http://<this-machine's-LAN-IP>:8000
```

## What's different from the cloud deployment

- **`MODE=offline`** — the app never calls any cloud AI provider, even if
  this machine happens to have occasional internet access (e.g. a metered
  satellite link). Everything routes to the local Ollama model. See
  `ai_providers.py`'s `resolve_mode()`. Set `MODE=auto` instead if you
  *want* it to opportunistically use cloud providers when available and
  fall back to local automatically — you'd then also need to set at least
  one cloud provider key (e.g. `GOOGLE_API_KEY`) in `.env.local`.
- **No Redis** — there's only ever one app process in this topology, so
  the per-process in-memory rate limiting and login lockout
  (`security.py`'s default) is exactly as effective as a Redis-backed one
  would be, at zero extra setup.
- **Billing is optional** — `PAYSTACK_SECRET_KEY` is left blank by
  `setup_local.sh`. `/billing/checkout` returns a clean 503 rather than
  crashing anything. Redemption codes (pre-generated centrally by whoever
  administers the school's NaijaSensei rollout, then distributed on a
  printed sheet or similar) still work fully offline, since redeeming one
  is just a local database check with no external call — see `billing.py`.
- **`ALLOWED_ORIGINS=*`** — wide open by design, because this server is
  only reachable on the school's own LAN in the first place, not the
  public internet. Don't port-forward this to the public internet without
  revisiting that.
- **Postgres is not exposed** outside the Docker Compose network — only
  the app container can reach it.

## Verifying it's working

- Visit `http://<LAN-IP>:8000` from a second device on the same network —
  confirms it's actually reachable over LAN, not just from the host
  machine itself.
- Register a test student account and send a chat message. A response
  from `gemma3n:e2b` confirms the whole offline AI path works.
- Log into the admin panel with the password from step 1 and check
  `/admin/provider-health` — it should show Ollama as the active/healthy
  provider and nothing else configured.
- Turn off the machine's internet connection entirely and repeat the chat
  test — this is the real test of "fully offline."

## Day-to-day operations

- **Restart**: `docker compose -f docker-compose.local.yml restart`
- **Stop**: `docker compose -f docker-compose.local.yml down` (data
  persists in the `postgres_data` and `ollama_data` volumes; add `-v` to
  also wipe them, which you almost never want)
- **Logs**: `docker compose -f docker-compose.local.yml logs -f app`
- **Backups**: back up the `postgres_data` Docker volume periodically
  (e.g. `docker run --rm -v naijasensei_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data`)
  — there's no managed-provider backup safety net in this topology, unlike
  the cloud path.
- **Updating the app code**: pull the new code, then
  `docker compose -f docker-compose.local.yml up -d --build` to rebuild
  just the `app` image; Postgres and Ollama's data volumes are untouched.

## Troubleshooting

- **"database is locked" or connection errors on startup**: the `app`
  container's `depends_on: postgres: condition: service_healthy` should
  prevent this, but if Postgres is slow to initialize on first-ever boot,
  give it another minute and check `docker compose logs postgres`.
- **Chat responses never come back / time out**: check
  `docker compose logs ollama` — on CPU-only hardware, `gemma3n:e2b` can
  take a while per response; this is expected, not a bug, on modest
  hardware. Enabling the GPU passthrough block in
  `docker-compose.local.yml` (commented out by default) helps a lot if
  this machine has an NVIDIA GPU.
- **Forgot the admin password**: it's still in `.env.local` under
  `ADMIN_PASSWORD` — read it directly from that file rather than
  regenerating secrets, which would also invalidate every logged-in
  student's session.
