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

## Development Order

Follow the priority in [AI_CONTEXT.md](AI_CONTEXT.md). Do not build unrelated
features before the current phase is complete.
