# Deployment Guide

This guide covers a simple production-style deployment for Daily Journal.

Daily Journal is a backend service. It needs a reachable HTTPS URL for Telegram
webhooks, a database, and environment variables for secrets.

## Requirements

- Python 3.13 or newer.
- PostgreSQL for production.
- SQLite only for local development.
- A Telegram bot token from BotFather.
- A private webhook secret value.
- A process manager or hosting platform that can run Uvicorn.
- HTTPS termination before requests reach the app.

## Environment Variables

Set these values in the runtime environment. Do not commit `.env`.

```bash
APP_ENV=production
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DB_NAME
TELEGRAM_BOT_TOKEN=replace-with-telegram-bot-token
TELEGRAM_WEBHOOK_SECRET=replace-with-long-random-secret
INTERNAL_API_TOKEN=replace-with-long-random-token
AI_PROVIDER=none
AI_API_KEY=
```

AI settings can stay disabled for v1.

## Install

Create a virtual environment and install the application.

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

Install development dependencies only on machines that run tests.

```bash
python -m pip install -e ".[dev]"
```

## Database Migration

Run migrations before starting the production process.

```bash
alembic upgrade head
```

For a new environment, verify the latest revision is applied.

```bash
alembic current
```

## Start the App

Run the app behind a reverse proxy or platform HTTPS routing.

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Use a process manager from the hosting platform, systemd, Supervisor, or a
container runtime to keep the process running.

## Health Check

After startup, check the health endpoint.

```bash
curl https://your-domain.example/health
```

Expected response:

```json
{"status":"ok","environment":"production"}
```

## Configure Telegram Webhook

Register the webhook URL with Telegram. Use the same secret value as
`TELEGRAM_WEBHOOK_SECRET`.

```bash
curl -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook" \
  -d "url=https://your-domain.example/telegram/webhook" \
  -d "secret_token=$TELEGRAM_WEBHOOK_SECRET"
```

Check the webhook status.

```bash
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getWebhookInfo"
```

## Smoke Test

Use Telegram to send `/start` to the bot.

Expected behavior:

- The app creates or updates the Telegram user record.
- Telegram receives the `/start` response.
- No raw journal text or bot token appears in logs.

Then send a normal text message.

Expected behavior:

- The message is saved as a journal entry.
- Telegram receives `Journal saved.`
- The entry belongs only to the Telegram user who sent it.

## Internal API Smoke Test

Use a trusted environment only. Replace the Telegram ID with the account that
sent the smoke-test message.

```bash
curl "https://your-domain.example/journal/today" \
  -H "X-Internal-Api-Token: $INTERNAL_API_TOKEN" \
  -H "X-Telegram-User-Id: 123456789"
```

The response should include only that user's journal entries.

## Operational Notes

- Run `alembic upgrade head` as part of every deployment.
- Keep `TELEGRAM_WEBHOOK_SECRET` and `INTERNAL_API_TOKEN` long and random.
- Rotate `TELEGRAM_BOT_TOKEN` through BotFather if it is exposed.
- Back up the production database before migrations.
- Keep app logs free of raw journal text, Telegram tokens, and API keys.
- Use PostgreSQL backups or hosting-provider snapshots for recovery.

## Rollback

For code rollback:

1. Deploy the previous known-good commit or tag.
2. Restart the app process.
3. Confirm `/health` returns `ok`.
4. Send `/start` to confirm Telegram replies still work.

For database rollback:

1. Prefer restoring a verified database backup.
2. Use `alembic downgrade` only after checking the migration being reverted.
3. Never downgrade production data blindly.

## Post-Deploy Checklist

- `alembic current` shows the expected revision.
- `/health` returns `ok`.
- Telegram `/start` returns the usage message.
- A normal journal message returns `Journal saved.`
- `/today` returns the saved entry.
- `/weekly` and `/monthly` return reports for the requesting user.
- Logs do not contain raw journal content or secrets.
