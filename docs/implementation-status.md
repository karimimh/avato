# Avato MVP implementation status

Last verified: 2026-08-30

This is the durable traceability and verification record for
`docs/avato-mvp-spec.md`. A checked item means implemented behavior backed by the
evidence below; a visual placeholder alone is not counted.

## Phase checklist

- [x] Domain model, reviewed migrations, private object storage, and seed catalog
- [x] Authentication, onboarding, ownership boundaries, and recent projects
- [x] Voice recording/upload, bounded trim, cleanup, and Persian transcription
- [x] 1–12 media ingestion and deterministic media-to-section first draft
- [x] FFmpeg rendering, curated music mix, subtitles, and three distinct templates
- [x] Correction-first RTL editor with no professional timeline
- [x] Trial, credit ledger, Zarinpal/local provider boundary, exports, and sharing
- [x] Privacy, rights consent, deletion, retention, analytics, and rate limits
- [x] Unit, infrastructure, media, migration, browser, production-build, and audit gates

## Architecture and invariants

- Users own private projects aggregating original/cleaned audio, timed transcript
  segments/words, ordered media, section assignments, render jobs, exports, rights
  consent, purchases, analytics, and an immutable credit ledger.
- Opaque session tokens are stored only as SHA-256 digests; passwords use scrypt.
  Every project resource is ownership-scoped. Uploads have magic-signature,
  filename, type, duration, count, and size validation.
- S3-compatible objects are private and partitioned by user/project. API processes
  use the internal endpoint while browsers receive short-lived URLs signed for the
  public endpoint. Deletion removes the object prefix before database rows.
- Faster-whisper is a lazy local adapter. FFmpeg trims, denoises, normalizes, mixes
  licensed/catalog music below narration, renders Persian ASS subtitles, and emits
  H.264/AAC vertical MP4. Worker event loops dispose their async database pools and
  revalidate project/audio existence after long inference.
- Free output is 720×1280 with a small watermark. Paid output is 1080×1920 without
  a watermark. A paid credit is charged transactionally only after durable object
  storage; the same project can re-export for seven days without another charge.
- Local payment mode is deterministic and moves no money. The production Zarinpal
  adapter uses the v4 request/verify contract, treats success codes 100 and 101 as
  valid, and relies on the unique authority/purchase boundary for callback replay.
- Projects expire 30 days after activity. Celery beat records a three-day warning
  event and deletes expired database/object data. Analytics accept only an explicit
  event/property allow-list and never transcript or media content.

## Functional requirements (§20)

| # | Capability | Implementation and evidence |
|---:|---|---|
| 1 | Create project | Guided studio + owned project API; API/browser tests |
| 2 | Record/upload Persian voice | MediaRecorder and raw upload; mobile E2E + real Persian smoke |
| 3 | Trim beginning/end | Dual bounded controls and reprocessing API; integration test |
| 4 | Original/cleaned playback | Signed private audio players; E2E private-object load |
| 5 | Editable Persian transcript | faster-whisper timed segments + text API/editor |
| 6 | Highlight uncertain words | Word confidence badges; Persian smoke produced 0.4322 minimum |
| 7 | Upload 1–12 photos/clips | UI and server enforcement; validation + mobile E2E |
| 8 | Reorder/remove/replace | Editor controls and ownership-scoped APIs |
| 9 | Optional title | Studio/editor persistence; browser test |
| 10 | Three templates | Clean Story, Dynamic Voice, Memory Film; real render tests |
| 11 | No/curated music | Catalog selection and narration-first FFmpeg mix |
| 12 | Automatic first draft | Deterministic section assignment with ordered reuse guidance |
| 13 | Complete preview | Finished signed video player plus download; decode/render tests |
| 14 | Correct subtitles | Save, restore, split, and merge without timeline |
| 15 | Media-to-section assignment | Per-section selector and invariant-tested API |
| 16 | Template/music/title/cover | Persisted project settings and validated cover ownership |
| 17 | Free watermarked export | Trial lock + 720×1280 render/watermark assertions |
| 18 | Iranian payment | Zarinpal v4 provider plus deterministic local gateway |
| 19 | Paid HQ export | 1080×1920 watermark-free render + transactional ledger tests |
| 20 | Download/share | Short-lived signed download and Web Share/copy fallback |
| 21 | Recent projects | Status/expiry dashboard ordered by activity |
| 22 | Delete project/account | UI/API and database + object-prefix tests |
| 23 | Retry without lost work/payment | Idempotent jobs/callbacks, preserved edits, post-success charge |

## Acceptance criteria (§21)

| Criterion | Evidence |
|---|---|
| First-time Persian user succeeds unaided | Pixel 7 Chrome E2E covers login, voice, one photo, style, save, editor |
| One voice + one photo works | E2E generates synthetic WAV/PNG and verifies signed image bytes load |
| Several photos make coherent draft | Deterministic order/reuse unit tests |
| Persian subtitles readable/editable/synchronized | RTL editor, timing/split/merge tests, ASS render probes, real Persian adapter smoke |
| Three templates are distinct | Three FFmpeg outputs with distinct plans, dimensions, audio, and duration |
| Narration remains understandable with music | -16 LUFS narration, 12% music mix, and audio-stream decode tests |
| Corrections need no timeline | Browser absence audit for timeline/keyframe/layer controls |
| Free export has watermark | Real rendered-output assertion |
| Paid export has no watermark | Real rendered-output assertion |
| Failed export consumes no credit | Transactional failure and concurrency tests |
| Project deletion works | Repeat-safe DB/object deletion and browser cleanup |
| Easier than a general editor | Four guided steps, correction cards, fixed styles, no pro controls |

## Verification matrix

| Gate | Result |
|---|---|
| `ruff format --check`, `ruff check`, strict `mypy` | pass, 65 typed source files |
| Host `pytest -q` | 36 passed; 6 infrastructure cases intentionally skipped |
| Compose PostgreSQL/MinIO/FFmpeg suite | 42 passed in 4.49s |
| Frontend lint, Prettier, TypeScript, Next production build | pass |
| Mobile Google Chrome Playwright suite | 2 passed; Pixel 7 viewport |
| Real Persian faster-whisper smoke | 1 segment, 9 timed words, confidence data present |
| Alembic upgrade on an isolated empty PostgreSQL database | both revisions applied; test DB removed |
| Compose startup graph and probes | migrations/init jobs exit 0; API healthy; landing/health/ready return 200 |
| Development and production Docker targets | pass for backend and web |
| `npm audit --omit=dev` | 0 vulnerabilities |
| `pip-audit` against rebuilt locked environment | no known vulnerabilities |
| Diff/secret scan | clean; no private-key/API-key patterns found |

## External launch configuration

The local MVP is complete and self-contained. Public deployment still requires
operator-owned configuration rather than repository secrets:

- production PostgreSQL/Redis, private S3 bucket, public HTTPS object origin, SSE,
  backups, TLS, monitoring/alert destinations, and capacity limits;
- Zarinpal merchant credentials and an allow-listed HTTPS callback;
- a provisioned faster-whisper model/cache and optional Hugging Face token;
- production music with redistribution/synchronization licenses;
- a mail/SMS provider for delivering the already-scheduled expiry warnings;
- final legal/privacy text and abuse/support escalation contacts.
