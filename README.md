# Avato (آواتو)

**Turn a Persian voice note and a few photos into a subtitled, vertical,
ready-to-share video. No video editing required.**

Avato is a full-stack MVP for Persian-speaking users in Iran. The user records or
uploads a 5–90 second voice note in Persian (Farsi) and adds 1–12 photos or short
clips. Avato cleans up the audio, transcribes it locally, aligns the media to the
spoken phrases, and renders a 9:16 video with Persian subtitles for Instagram
Reels, Stories, and similar formats.

The product is built for that market: the UI is Persian and right-to-left (RTL),
speech recognition targets Persian, prices are in Iranian rials, and paid exports
go through Zarinpal, an Iranian payment gateway, because international payment
providers are generally unavailable to Iranian users. The code, comments, and docs
are in English.

## Features

- **Guided four-step studio**: voice → media → style → review. Users can start
  without an account and register when they save.
- **Voice input**: record in the browser (MediaRecorder) or upload a file. Trim
  the start and end, then compare the original and cleaned narration. Cleanup is
  done with FFmpeg denoising and loudness normalization.
- **Local Persian speech-to-text** with
  [faster-whisper](https://github.com/SYSTRAN/faster-whisper). It produces timed
  segments and words, and words with low confidence are highlighted for review.
- **Correction-first editor with no timeline**: fix subtitle text, split or merge
  sections, restore the original transcript, choose the photo or clip for each
  section, reorder, replace, or remove media, and pick a cover.
- **Automatic first draft**: deterministic assignment of media to speech
  sections. Sections are at least 1.2 seconds long, and media repeat in order
  when there are fewer visuals than sections.
- **FFmpeg rendering**: three templates (Clean Story, Dynamic Voice, Memory
  Film), Persian ASS subtitles, optional curated music mixed under the narration,
  and H.264/AAC MP4 output.
- **Free and paid exports**: one free 720×1280 export with a watermark, then
  watermark-free 1080×1920 exports paid with credits. A credit is charged only
  after the rendered file has been stored, so a failed export costs nothing.
- **Payments**: credit packs backed by an append-only credit ledger. A pluggable
  provider supports a Zarinpal v4 adapter and a deterministic local gateway that
  moves no money. Callbacks are idempotent.
- **Projects and sharing**: recent-projects dashboard, short-lived signed
  download links, Web Share with a copy-link fallback, and project and account
  deletion.
- **Privacy and security**: private S3 objects partitioned by user and project,
  ownership checks on every project resource, scrypt password hashing, session
  tokens stored only as SHA-256 digests, upload validation by magic bytes, size,
  count, and duration, Redis rate limits, security headers and CSP, and an
  analytics endpoint that accepts only allow-listed events.
- **Retention**: projects expire after 30 days of inactivity. A Celery beat job
  records a warning event three days before expiry and deletes expired data.

Not included in this MVP:

- Email or SMS delivery for the expiry warning. The warning event is recorded,
  but no message is sent.
- A licensed music catalog. The repository ships three procedurally generated
  test tracks; see [docs/asset-licenses.md](docs/asset-licenses.md).
- Production deployment configuration (TLS, monitoring, backups) and a hosted
  instance.
- Items the spec defers until after validation, such as more aspect ratios,
  direct publishing, or translation.

## Architecture

```text
Browser (Next.js, RTL)
        │
        ▼
     nginx :8080 ──────► web (Next.js dev server)
        │ /api
        ▼
  FastAPI backend ──────► PostgreSQL   (users, projects, transcript, ledger, jobs)
        │   │
        │   └──────────► MinIO / S3    (private audio, media, renders; signed URLs)
        ▼
  Redis (Celery broker, rate limits)
        │
        ▼
  Celery worker ── FFmpeg cleanup and rendering, faster-whisper transcription
  Celery beat   ── daily expiry warnings and deletion of expired projects
```

- **API** (`backend/app/api`): FastAPI routers for auth, projects, assets,
  transcript, draft, catalog, payments, exports, and operations
  (`/health`, `/ready`, `/analytics`).
- **Domain and services** (`backend/app/domain`, `backend/app/services`):
  project rules, upload validation, transcript editing, draft section
  assignment, the credit ledger, and deletion.
- **Provider boundaries**: storage (`storage/`, S3-compatible), transcription
  (`transcription/`, faster-whisper loaded lazily), and payments (`payments/`,
  Zarinpal or local). Each sits behind a small interface.
- **Workers** (`backend/app/workers`): transcription, rendering, and retention
  tasks. Jobs are idempotent, and a worker re-checks that the project still
  exists after long-running inference.
- **Media** (`backend/app/media`): audio cleanup and analysis, ffprobe, ASS
  subtitle generation, and the FFmpeg command builder for each template.
- **Database**: SQLAlchemy 2 (async) models with reviewed Alembic migrations that
  also seed the template and music catalog.

## Tech stack

| Area | Technologies |
| ---- | ------------ |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2 (asyncio, asyncpg), Alembic, Pydantic Settings, httpx |
| Jobs | Celery 5 + Redis (worker and beat) |
| Media and AI | FFmpeg, faster-whisper (local, CPU int8 by default) |
| Storage | PostgreSQL 17, MinIO (S3-compatible) via boto3 |
| Frontend | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS 4, TanStack Query, lucide-react, Estedad font |
| Infrastructure | Docker Compose, nginx reverse proxy, multi-stage Dockerfiles (development and production targets) |
| Quality | pytest, Ruff, strict mypy, ESLint, Prettier, Playwright (mobile Chrome) |

## Repository layout

```text
backend/
  app/            FastAPI app: api/, core/, db/, domain/, services/, media/,
                  payments/, storage/, transcription/, workers/
  migrations/     Alembic schema history and catalog seeds
  scripts/        Local bucket and synthetic music seeding
  tests/          Unit, media, security, and infrastructure integration tests
web/
  src/app/        Landing page, studio, projects list, project editor, credits
  src/lib/        API client
  e2e/            Playwright mobile acceptance test
nginx/            Local reverse proxy and upload size limit
docs/             Product spec, implementation status, asset licenses
docker-compose.yml
.env.example
```

## Running locally

Requirements: Docker with Compose. Node.js 22 (see `.nvmrc`) is needed only for
frontend checks on the host, and Python 3.12+ with
[uv](https://docs.astral.sh/uv/) only for backend checks on the host.

```bash
cp .env.example .env
docker compose up --build
```

Compose waits for PostgreSQL, runs the Alembic migrations, creates the private
MinIO bucket and the synthetic music tracks, then starts the API, Celery worker,
Celery beat, web app, and nginx.

| URL | Service |
| --- | ------- |
| http://localhost:8080 | App (through nginx) |
| http://localhost:8080/api/health, `/api/ready` | Health and readiness checks |
| http://localhost:3000 | Next.js directly |
| http://localhost:8100 | FastAPI directly |
| http://localhost:9101 | MinIO console |

The first transcription downloads the faster-whisper model into the
`whisper_models` volume, so it takes longer than later runs. Set
`WHISPER_MODEL=tiny` for a quick smoke test, or keep the default `small` model for
better Persian accuracy. The default `PAYMENT_PROVIDER=local` uses a fake
checkout page and moves no money.

```bash
docker compose ps
docker compose logs -f backend worker beat web
docker compose down              # add --volumes to wipe all local data
```

## Configuration

Every setting is listed in [`.env.example`](.env.example) with a local default or
an empty placeholder. The main groups are:

- **App and URLs**: `APP_ENV`, `FRONTEND_URL`, `NEXT_PUBLIC_API_URL`, and host
  port overrides (`*_PORT_FORWARD`)
- **Data stores**: `DATABASE_URL`, `POSTGRES_*`, `REDIS_URL`, `CELERY_*`
- **Object storage**: `S3_ENDPOINT_URL` (internal), `S3_PUBLIC_ENDPOINT_URL`
  (embedded in signed browser links), bucket, credentials,
  `S3_SERVER_SIDE_ENCRYPTION`
- **Transcription**: `WHISPER_MODEL`, `WHISPER_DEVICE`, `WHISPER_COMPUTE_TYPE`,
  and an optional `HF_TOKEN`
- **Payments**: `PAYMENT_PROVIDER` (`local` or `zarinpal`), `PAYMENT_CALLBACK_URL`,
  `PAYMENT_LOCAL_SECRET`, `ZARINPAL_MERCHANT_ID`, `ZARINPAL_SANDBOX`

The values in `.env.example` are local-development defaults only. Real
deployments need their own secrets, an HTTPS callback URL for Zarinpal, and
licensed music.

## Testing

Backend checks on the host:

```bash
cd backend
uv sync --frozen
uv run ruff format --check .
uv run ruff check .
uv run mypy app tests
uv run pytest
```

Tests that need PostgreSQL and MinIO are skipped on the host. To run them inside
the Compose stack (while it is up):

```bash
docker compose run --rm --no-deps \
  -e RUN_DB_TESTS=1 \
  -v "$PWD/backend/tests:/app/tests:ro" \
  backend .venv/bin/pytest -q -p no:cacheprovider
```

The integration tests cover database ownership and concurrency, object deletion
and durability, payment callback forgery and idempotency, retention, real FFmpeg
renders for all three templates (dimensions, audio, watermark), and the rule that
a failed export consumes no credit.

Frontend checks:

```bash
cd web
npm ci
npm run lint
npm run format:check
npm run typecheck
npm run build
E2E_BASE_URL=http://localhost:8080 npm run test:e2e   # requires Google Chrome
```

The Playwright test runs the full flow at a Pixel 7 viewport with WAV and PNG
fixtures that it generates itself.

## Project status

The MVP runs end to end locally through Docker Compose. It is a personal project
and has no public deployment or real users yet. The
[product spec](docs/avato-mvp-spec.md) defines the scope, and
[docs/implementation-status.md](docs/implementation-status.md) maps each
requirement and acceptance criterion to its implementation and tests, and lists
the configuration a production launch would still need.
