# Daily Journal

Daily Journal is a Python backend application for saving personal journal
entries from Telegram and generating weekly or monthly reflections.

Before modifying this project, read [AI_CONTEXT.md](AI_CONTEXT.md).

## Current Status

Version 1 is ready for personal MVP use. Current scope:

- FastAPI application skeleton
- Layered folder structure
- Environment configuration
- Health check endpoint
- Database models and Alembic migrations for users, journal entries, and reports
- Telegram webhook handling with user auto-registration
- Outbound Telegram replies for webhook confirmations and commands
- Journal storage, today lookup, search, delete latest, and delete by ID
- Telegram today and delete latest commands
- Telegram search command
- Telegram mood summary command
- Rule-based mood and tag extraction for new journal entries
- Weekly report generation and retrieval
- Monthly report generation and retrieval
- Tests for core database, Telegram, journal, mood, weekly report, and monthly
  report behavior

Release notes: [docs/releases/v1.md](docs/releases/v1.md).

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

Deployment guide: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

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
acknowledgement payload. When `TELEGRAM_BOT_TOKEN` is configured, webhook
responses with `reply_text` are also sent back to the Telegram chat.

Journal API:

```bash
GET /journal
GET /journal?keyword=python
GET /journal/export/markdown
POST /journal
GET /journal/today
GET /journal/{id}
PUT /journal/{id}
DELETE /journal/latest
DELETE /journal/{id}
```

Journal API requests must include `X-Internal-Api-Token` and
`X-Telegram-User-Id`. The internal token gates these endpoints for trusted
internal use. The Telegram ID resolves the current user, and all journal queries
are scoped to that user's internal `user_id`.

Journal updates can change derived metadata such as `processed_text`, `summary`,
`mood_score`, `mood_label`, `tags`, and `entry_date`. They do not overwrite
`raw_text`.

New journal entries receive basic rule-based mood and tag analysis. This does
not use an external AI provider and never modifies `raw_text`.

Reports API:

```bash
POST /reports/weekly
GET /reports/weekly
POST /reports/monthly
GET /reports/monthly
```

Reports API requests use the same `X-Internal-Api-Token` and
`X-Telegram-User-Id` headers. Weekly reports use a Monday-to-Sunday period and
monthly reports use the calendar month. Reports are generated only from the
requesting user's journal entries.

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
