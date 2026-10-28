# Deploying NaijaSensei to the cloud

This is the multi-replica, internet-facing deployment path: managed
Postgres, one or more app server replicas behind a load balancer, Redis
for shared rate-limiting state, cloud AI providers, and Paystack billing.

If you're setting this up for a single school on its own local server with
no reliable internet, use **LOCAL_DEPLOYMENT.md** instead — same codebase,
different `MODE` and no external services required.

## 1. Generate real secrets

Never reuse any placeholder value you've seen in this codebase, chat, or
documentation — `security.py` refuses to start the app if it detects a
known-weak or previously-leaked default.

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"   # JWT_SECRET_KEY
python3 -c "import secrets; print(secrets.token_hex(32))"   # CREDENTIALS_ENCRYPTION_KEY
```

Pick a real admin password (12+ characters) for `ADMIN_PASSWORD`.

## 2. Provision infrastructure

- **Postgres** — a managed instance (RDS, Cloud SQL, Neon, Supabase,
  Render Postgres, etc). Note the connection string for `DATABASE_URL`.
  Put PgBouncer (transaction pooling mode) in front of it once you're
  running more than a couple of app replicas — see the sizing note at the
  bottom of `db.py`.
- **Redis** — optional but recommended once you run more than one app
  replica, so rate-limiting and login-lockout state (`security.py`) is
  enforced against total traffic, not per-replica traffic. Any managed
  Redis works (Upstash, ElastiCache, Redis Cloud). Without it, each
  replica just enforces its own share of the limit — a real but smaller
  gap, not a crash.
- **App hosting** — anywhere that runs a Docker container and lets you set
  environment variables: Fly.io, Render, Railway, ECS/Fargate, Cloud Run,
  a plain VM. Build from the included `Dockerfile`.

## 3. Set environment variables

Copy `.env.example`, fill in real values, and set them on your hosting
platform (most platforms want these as dashboard/secret-manager entries
rather than a committed file — don't commit `.env`).

At minimum for a working cloud deployment:

```
JWT_SECRET_KEY=<generated>
ADMIN_PASSWORD=<generated>
CREDENTIALS_ENCRYPTION_KEY=<generated>
DATABASE_URL=postgresql://user:pass@your-db-host:5432/naijasensei
MODE=auto
GOOGLE_API_KEY=<your key>        # at minimum one cloud AI provider
ALLOWED_ORIGINS=https://your-real-frontend-domain.com
REDIS_URL=redis://your-redis-host:6379   # once running >1 replica
```

Add as many of the other provider keys from `.env.example`'s fallback
chain as you can — every provider without a key is silently skipped, and
more keys means the app keeps working even if one provider has an outage
or hits its free-tier quota.

Set `PAYSTACK_SECRET_KEY` if you want real card/bank-transfer payments;
leave it blank and `/billing/checkout` returns a clean 503 while
redemption codes (`admin.py`-generated) still work.

## 4. Initialize the database

Every module's `init_*_db()` function creates its own tables and is safe
to call repeatedly (`CREATE TABLE IF NOT EXISTS`). These all run
automatically on app startup — see `server.py`'s startup event — so a
fresh Postgres database is ready the first time the app boots. Nothing
extra to run manually for a brand-new deployment.

**Migrating existing data from a SQLite deployment?** Run
`migratesqlitetopostgres.py` once, after the app has started at least once
against the new Postgres database (so tables exist) but before pointing
real traffic at it:

```bash
export DATABASE_URL="postgresql://user:pass@your-db-host:5432/naijasensei"
python migratesqlitetopostgres.py /path/to/naija_sensei.db
```

## 5. Build and deploy the image

```bash
docker build -t naijasensei .
docker run -p 8000:8000 --env-file .env naijasensei
```

Or push to your platform's registry and point it at the `Dockerfile`
directly — most platforms (Fly, Render, Railway) will build it for you
from the repo.

The container's `CMD` runs `uvicorn server:app --host 0.0.0.0 --port 8000`
without `--reload` and without a fixed worker count — let your hosting
platform manage replica count (horizontal scaling) rather than running
multiple uvicorn workers inside one container, since horizontal replicas
is what your Postgres pool sizing and Redis-backed rate limiting are
already designed around.

## 6. Verify

- `GET /` should serve the frontend (`Index.html`).
- `GET /admin/stats` with header `X-Admin-Password: <your ADMIN_PASSWORD>`
  should return without a 401.
- Register a test student account, send a chat message, confirm you get a
  real AI response (check `MODE` and that at least one provider key is
  set if you get a "no provider available" error).
- Check `/admin/provider-health` to confirm which AI providers are
  actually reachable from your deployment's network.

## 7. Ongoing operations

- **Scaling**: raise replica count on your platform; keep
  `N × DB_POOL_MAX` comfortably under Postgres's `max_connections` (see
  `db.py`'s sizing note) — use PgBouncer once that gets tight.
- **Cost tracking**: `/admin/api-costs` shows USD spend on paid providers
  (Mistral, ElevenLabs) — see `api_costs.py` for exactly what's tracked
  and what's estimated vs. exact.
- **Provider outages**: `/admin/provider-health` and the
  `provider_events` table (written by `ai_providers.py`) show recent
  failures per provider — useful for deciding whether to add another
  fallback key.
- **Backups**: rely on your managed Postgres provider's automated backups;
  this app does not implement its own.
