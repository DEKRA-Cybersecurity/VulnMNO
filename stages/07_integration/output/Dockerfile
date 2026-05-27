# Build-context expected to be the repo root.
# docker compose at stages/07_integration/output/docker-compose.yml uses ../../../ as context.
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# System deps for argon2-cffi build + Postgres client lib
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libffi-dev libpq-dev curl \
 && rm -rf /var/lib/apt/lists/*

# Backend project lives under stages/04_api_build/output/backend/
COPY stages/04_api_build/output/backend/ ./backend/
WORKDIR /app/backend

RUN pip install --no-cache-dir \
    "fastapi>=0.110" "uvicorn[standard]>=0.27" \
    "sqlalchemy>=2.0" "alembic>=1.13" "aiosqlite>=0.19" "asyncpg>=0.29" \
    "pydantic>=2.6" "pydantic-settings>=2.2" \
    "PyJWT>=2.8" "argon2-cffi>=23" "python-multipart>=0.0.9"

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
