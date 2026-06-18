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

## Test

```bash
pytest
```

CI runs `ruff check .` and `pytest` on pull requests into `main`.

## Development Order

Follow the priority in [AI_CONTEXT.md](AI_CONTEXT.md). Do not build unrelated
features before the current phase is complete.
