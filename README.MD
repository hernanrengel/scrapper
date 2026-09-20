# Web Scrapper

A user adds a URL; the app scrapes every `<a>` tag on that page (href + the
link's visible name) and stores the result. Scraping runs asynchronously, so
the list shows pages currently in progress instead of blocking the request.
The frontend lists every page that's been scraped, with the number of links
found on each, its status, and lets you drill into a page to see its links
and its status history.

## Tools used

**Backend**
- Python 3.12, Django 6.1, Django REST Framework
- django-environ (env-var configuration)
- psycopg (PostgreSQL driver)
- drf-spectacular (OpenAPI schema + Swagger UI/ReDoc)
- Celery + Redis (async scraping)
- requests, charset-normalizer, beautifulsoup4, lxml (fetching + parsing)
- ruff (lint + format)
- pytest, pytest-django, factory_boy, responses (testing)

**Frontend**
- Node 24, React 19 + TypeScript, Vite
- Tailwind CSS v4, react-router-dom, lucide-react (icons)
- @fontsource/ibm-plex-sans, @fontsource/ibm-plex-mono (self-hosted fonts)
- oxlint (lint)
- Vitest, React Testing Library, jsdom (testing)

**Infra**
- Docker + Docker Compose
- PostgreSQL 16, Redis 7

## Running the project

Everything runs with a single command from `infra/`:

```bash
cd infra
cp .env.example .env   # edit values if you want different Postgres credentials
docker compose up -d
```

This boots PostgreSQL, Redis, the Django API, the Celery worker, and the
frontend, running migrations on backend startup — no other manual steps.

| Service    | URL                        |
|------------|----------------------------|
| Frontend   | http://localhost:5173      |
| Backend    | http://localhost:8000/api/v1/ |
| API docs   | http://localhost:8000/api/schema/swagger-ui/ (or `/redoc/`) |
| Postgres   | localhost:5433 (5432 avoided to dodge clashes with other local instances) |
| Redis      | localhost:6379             |

View logs for any service:

```bash
docker compose logs -f backend   # or worker, frontend, postgres, redis
```

Stop the stack:

```bash
docker compose down
```

### Running without Docker (local development)

**Backend** (needs a Postgres + Redis already running, e.g. via
`docker compose up -d postgres redis` from `infra/`):

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env   # needs a real SECRET_KEY and a DATABASE_URL matching your Postgres
python manage.py migrate
python manage.py runserver
```

Generate a `SECRET_KEY`:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

In a second terminal, run the Celery worker (needed for scraping to actually
happen):

```bash
cd backend
source .venv/bin/activate
celery -A config worker -l info
```

**Frontend**:

```bash
cd frontend
npm install
npm run dev
```

## Testing

Full suite, either inside the running containers:

```bash
docker compose exec backend pytest
docker compose exec backend ruff check .
docker compose exec backend ruff format --check .
docker compose exec backend python manage.py spectacular --validate --fail-on-warn --file /dev/null
docker compose exec frontend npm test
docker compose exec frontend npm run lint
```

or locally, from each project's own environment:

```bash
# backend/ (with .venv active)
pytest
ruff check .
ruff format --check .
python manage.py spectacular --validate --fail-on-warn --file /dev/null

# frontend/
npm test
npm run lint
```
