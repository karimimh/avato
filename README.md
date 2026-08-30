# Avato (آواتو)

Avato turns one Persian voice note and 1–12 photos or short clips into a private,
vertical, subtitled video. The MVP includes guided RTL onboarding, local Persian
speech-to-text, correction-first editing, three FFmpeg templates, curated music,
watermarked trials, paid exports, an Iranian payment-provider boundary, retention,
and account/project deletion.

The product specification is in `docs/avato-mvp-spec.md`; implementation and
acceptance evidence is tracked in `docs/implementation-status.md`.

## Run locally

Requirements: Docker Desktop with Compose. Node.js 22 is only needed for running
frontend checks on the host; Python 3.12+ and `uv` are only needed for backend
checks on the host.

```bash
cp .env.example .env
docker compose up --build
```

Compose waits for PostgreSQL, runs Alembic migrations, creates the private MinIO
bucket and synthetic local music, fixes the Whisper cache ownership, then starts
the API, worker, retention scheduler, web app, and reverse proxy.

- Product: <http://localhost:8080>
- Direct frontend: <http://localhost:3000>
- Direct API: <http://localhost:8100>
- Health/readiness: <http://localhost:8080/api/health> and
  <http://localhost:8080/api/ready>
- MinIO console: <http://localhost:9101>

The first transcription downloads the configured faster-whisper model into the
named `whisper_models` volume and can therefore take longer. Subsequent jobs reuse
it. Set `WHISPER_MODEL=tiny` for a fast smoke environment or retain the default
`small` model for better Persian transcription.

Local payment mode is deterministic and moves no money. Production payment uses
the Zarinpal adapter when `PAYMENT_PROVIDER=zarinpal`, a merchant ID, and an HTTPS
callback URL are configured.

## Main workflow

1. Start without registration and record or upload a 5–90 second voice note.
2. Add 1–12 private photos/clips, choose duration, template, title, and music.
3. Register or sign in when saving.
4. Listen to original and cleaned narration; trim and reprocess when needed.
5. Correct uncertain Persian words, split/merge subtitle sections, and choose the
   media for each section without a timeline.
6. Reorder, replace, remove, or choose a cover; regenerate the deterministic draft.
7. Confirm rights, create the eligible free watermarked export, or spend one credit
   on a 1080×1920 watermark-free export. Credits are charged only after the object
   is durably stored.
8. Preview, download, share, retry, or delete. Projects expire after 30 days of
   inactivity, with a three-day warning event.

## Configuration

All settings are documented in `.env.example`. Important production values are:

- PostgreSQL and Redis URLs
- internal and public S3-compatible endpoints, credentials, private bucket, and SSE
- `WHISPER_MODEL`, device, compute type, and optional Hugging Face credentials
- `PAYMENT_PROVIDER`, Zarinpal merchant ID, and allow-listed HTTPS callback URL
- public frontend/API origins, TLS termination, monitoring, and backups

Production music must replace the synthetic fixtures with explicitly licensed
tracks. See `docs/asset-licenses.md`. No user media or model weights are committed.

## Quality and acceptance checks

Frontend:

```bash
cd web
npm ci
npm run lint
npm run format:check
npm run typecheck
npm run build
E2E_BASE_URL=http://localhost:8080 npm run test:e2e
```

The Playwright suite uses installed Google Chrome at a mobile Pixel viewport and
generates its own synthetic WAV/PNG fixtures.

Backend host checks:

```bash
cd backend
uv sync --frozen
uv run ruff format --check .
uv run ruff check .
uv run mypy app tests
uv run pytest
```

Full infrastructure/media integration checks while Compose is running:

```bash
docker compose run --rm --no-deps \
  -e RUN_DB_TESTS=1 \
  -v "$PWD/backend/tests:/app/tests:ro" \
  backend .venv/bin/pytest -q -p no:cacheprovider
```

These tests exercise PostgreSQL ownership and concurrency, MinIO deletion and
durability, callback forgery/idempotency, retention, real FFmpeg rendering for all
templates, output dimensions/audio, free/paid watermark flags, and the rule that a
failed export consumes no credit.

## Repository layout

```text
backend/app/       FastAPI domain, providers, media pipeline, and Celery jobs
backend/migrations Reviewed Alembic schema history and catalog seeds
backend/tests/     Unit, media, security, and infrastructure integration tests
web/src/app/       RTL landing, studio, projects/editor, and credit purchase UI
web/e2e/           Automated mobile Chrome acceptance workflow
nginx/             Local reverse proxy and upload boundary
docs/              Specification, traceability, and asset licensing
```

## Privacy and operational notes

Objects are private and partitioned by user/project. Browser links are short-lived
signed URLs, API access is ownership-checked, filenames/content are validated, and
analytics accept only an allow-list that excludes transcript/media content.
Deleting a project or account removes its object prefix before database rows.

To inspect or stop the stack:

```bash
docker compose ps
docker compose logs -f backend worker beat web
docker compose down
```

`docker compose down --volumes --remove-orphans` permanently removes all local
PostgreSQL, Redis, MinIO, and Whisper-model data; use it only when a full local reset
is intended.
