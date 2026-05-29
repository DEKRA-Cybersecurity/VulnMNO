# Build-context expected to be the src/ directory (one level above this file).
# Used by src/docker/docker-compose.yml.
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# System deps for argon2-cffi build + Postgres client lib
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libffi-dev libpq-dev curl \
 && rm -rf /var/lib/apt/lists/*

# Backend project lives under src/backend/
COPY backend/ ./backend/
WORKDIR /app/backend

RUN pip install --no-cache-dir \
    "fastapi>=0.110" "uvicorn[standard]>=0.27" "python-multipart>=0.0.9" \
    "sqlalchemy>=2.0" "alembic>=1.13" "aiosqlite>=0.19" "asyncpg>=0.29" \
    "pydantic>=2.6" "pydantic-settings>=2.2" \
    "PyJWT>=2.8" "argon2-cffi>=23" \
    "jinja2>=3.1" "itsdangerous>=2.1" "slowapi>=0.1.9" "pyyaml>=6.0" \
    "httpx>=0.27"

EXPOSE 8000
# --proxy-headers + --forwarded-allow-ips=* makes the access log record the
# real client IP from X-Forwarded-For instead of the reverse-proxy's address.
# Correct behind Caddy (it forwards the client), and it lets the traffic
# simulator (scripts/simulate_traffic.py) attribute requests to distinct
# per-user IPs in the log. Trusting XFF from anywhere is itself a lab-grade
# weakness (a client hitting :8000 directly can forge its logged source IP).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--proxy-headers", "--forwarded-allow-ips", "*"]
