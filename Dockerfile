# NaijaSensei — app image, used by both the local (docker-compose.local.yml)
# and cloud deployment paths. Doesn't bundle Postgres or Ollama — those are
# separate services/containers either way (see DEPLOY.md for cloud,
# LOCAL_DEPLOYMENT.md for the all-in-one local/offline school deployment).

FROM python:3.12-slim

WORKDIR /app

# System deps: libpq for psycopg2 (even with -binary, some environments
# still want the client library present), build-essential for anything
# that needs to compile from source on an architecture without a wheel.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

COPY . .

# Uploaded files and the RAG index both need a writable directory that
# survives container restarts if you're not mounting a volume over it —
# see docker-compose.local.yml, which does mount one.
RUN mkdir -p uploads static

EXPOSE 8000

# Match uvicorn's own graceful-shutdown handling rather than letting
# Docker SIGKILL it — gives in-flight requests (including a Paystack
# webhook mid-processing) a chance to finish.
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]