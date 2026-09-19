# Web Scrapper

A user adds a URL; the app scrapes every `<a>` tag on that page (href + the
link's visible name) and stores the result. The frontend lists every page
that's been scraped, with the number of links found on each, and lets you
drill into a page to see its links.

## Tools

- **Backend**: Python 3.14, Django 6.1, django-environ (env-var config),
  psycopg (PostgreSQL driver), ruff (lint + format)
- **Frontend**: Node 24, React 19 + TypeScript, Vite, Tailwind CSS,
  react-router-dom
- **Infra**: Docker + Docker Compose (PostgreSQL 16, Redis 7)

## Running the project

### 1. Database + broker

```bash
cd infra
cp .env.example .env   # edit values if you want different credentials
docker compose up -d
```

Starts PostgreSQL on port 5433 (5432 avoided to dodge clashes with other
local Postgres instances) and Redis on 6379.

### 2. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

`.env` needs a real `SECRET_KEY` and a `DATABASE_URL` matching the port from
step 1. Generate a secret key with:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Lint / format:

```bash
ruff check .
ruff format --check .
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Lint:

```bash
npm run lint
```

A single `docker compose up -d` that boots the entire stack (backend, worker,
and frontend included) is planned but not wired up yet.

## Testing

No automated tests exist yet.
