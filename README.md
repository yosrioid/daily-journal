# Daily Journal

Daily Journal is a Python backend application for saving personal journal
entries from Telegram and generating weekly or monthly reflections.

Before modifying this project, read [AI_CONTEXT.md](AI_CONTEXT.md).

## Current Status

Project foundation is being built incrementally. Current scope:

- FastAPI application skeleton
- Layered folder structure
- Environment configuration
- Health check endpoint
- Initial tests

Database models, Telegram webhook handling, journal storage, and reports are
not implemented yet.

## Development Workflow

Do not push feature work directly to `main`. Work must be done in a phase or
feature branch and merged through a pull request.

Read [docs/DEVELOPMENT_WORKFLOW.md](docs/DEVELOPMENT_WORKFLOW.md) before
starting a new phase.

## Requirements

- Python 3.13+

## Setup

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
cp .env.example .env
```

## Run

```bash
uvicorn app.main:app --reload
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Telegram webhook:

```bash
POST /telegram/webhook
```

The webhook currently validates Telegram updates, resolves or creates the
Telegram user, stores normal text messages as journal entries, and returns an
acknowledgement payload. Outbound Telegram replies are not implemented yet.

Journal API:

```bash
GET /journal
GET /journal?keyword=python
POST /journal
GET /journal/today
GET /journal/{id}
DELETE /journal/latest
DELETE /journal/{id}
```

Journal API requests must include `X-Internal-Api-Token` and
`X-Telegram-User-Id`. The internal token gates these endpoints for trusted
internal use. The Telegram ID resolves the current user, and all journal queries
are scoped to that user's internal `user_id`.

## Test

```bash
pytest
```

CI runs `ruff check .` and `pytest` on pull requests into `main`.

## Database

Development defaults to SQLite through `DATABASE_URL`.

Run migrations:

```bash
alembic upgrade head
```

## Development Order

Follow the priority in [AI_CONTEXT.md](AI_CONTEXT.md). Do not build unrelated
features before the current phase is complete.
