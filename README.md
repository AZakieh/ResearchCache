# ResearchCache

A caching proxy for open scientific datasets. It sits in front of researcher
download requests, caches files from approved repositories (EBI, NCBI,
Zenodo, Ensembl, Copernicus, OpenNeuro, Mendeley Data) in Cloudflare R2, and
serves repeat requests at full local speed instead of the origin's.


## How it works

Every request passes through an 8-stage pipeline, run in a fixed order.
Stage 4 is the only place an access decision is ever made, and it issues an
HMAC-signed token — the serve stage cannot run without a validly signed
`Decision`, so it's structurally impossible to serve bytes without going
through the access check.

| Stage | Module | Responsibility                                                          |
|---|---|-------------------------------------------------------------------------|
| 0 | `stage0_receive.py` | Canonicalise the URL, enforce HTTPS, hash the client IP                 |
| 1 | `stage1_identity.py` | Resolve the caller: anonymous or API key                                |
| 2 | `stage2_resolve.py` | Check the origin host against the allow-list                            |
| 3 | `stage3_policy.py` | Look up licence/access-tier policy                                      |
| 4 | `stage4_decision.py` | ALLOW/DENY, HMAC-signed — the safety-critical stage                     |
| 5 | `stage5_cache.py` | Redis cache lookup                                                      |
| 6 | `stage6_serve.py` | Stream-through serve: HIT from cache, MISS fetches + caches + streams simultaneously |
| 7 | `stage7_audit.py` | Append-only audit log write                                             |

The MVP implementation is intentionally minimal —
anonymous/API-key identity, open-access-only policy, Redis+R2 storage,
Postgres audit logging — but the interfaces are built for the real thing
(federated identity, licence/embargo evaluation, tiered storage, analytics)
to slot in later without the callers changing.

## What's built so far

Progress follows an 18-step build order. Steps 1–8 are done:

- [x] **1. Project skeleton** — `pyproject.toml`, Docker Compose (Postgres +
      Redis), `Makefile`, `.env.example`
- [x] **2. Shared data models** — `Principal`, `Policy`, `Decision`,
      `CacheEntry`, `AuditEvent` (all frozen dataclasses)
- [x] **3. Configuration** — Pydantic Settings, fails fast on missing
      required env vars
- [x] **4. Database schema** — Alembic migration for all 6 Postgres tables
      (`policies`, `cache_entries`, `audit_events`, `api_keys`,
      `benchmark_results`, `allowlist`)
- [x] **5. Stage 0 — receive/normalise** — URL canonicalisation, HTTPS
      enforcement, daily-salted IP hashing
- [x] **6. Stage 2 — resolve/allow-list** — origin allow-list enforcement,
      rejects unlisted hosts before any network call
- [x] **7. Stage 3 — policy lookup** — Zenodo licence metadata via
      its REST API, defaults to `unknown`/`open` elsewhere, always persisted
- [x] **8. Stage 4 — access decision** — the ALLOW/DENY decision
      and its HMAC signing/verification

Not yet built: Stage 1 identity (Step 13), the Redis/R2 storage layer
(Steps 9–10), Stage 5 cache lookup and Stage 6 stream-through serve (Steps
11–12), Stage 7 audit (Step 14), the FastAPI routes and middleware (Steps
15–16), the benchmark page (Step 17), and integration tests + production
deploy (Step 18).

32 unit tests pass across the models and the four stages implemented so far.

## Project layout

```
researchcache/
├── pipeline/           # The 8-stage request pipeline
│   ├── stage0_receive.py
│   ├── stage1_identity.py    # not yet implemented
│   ├── stage2_resolve.py
│   ├── stage3_policy.py
│   ├── stage4_decision.py
│   ├── stage5_cache.py       # not yet implemented
│   ├── stage6_serve.py       # not yet implemented
│   ├── stage7_audit.py       # not yet implemented
│   └── runner.py             # not yet implemented
├── models/             # Shared dataclasses — the contracts between stages
├── api/                # FastAPI route handlers (not yet implemented)
├── store/
│   ├── db.py            # SQLAlchemy async engine, session factory, ORM models
│   ├── meta_store.py     # Redis metadata store (not yet implemented)
│   └── object_store.py   # R2/S3 object store (not yet implemented)
├── config.py            # Pydantic Settings
└── main.py               # App entry point (not yet implemented)

migrations/              # Alembic migrations
tests/unit/               # Per-stage unit tests
infra/                   # docker-compose.yml, nginx.conf
allowlist.yaml            # Approved origin hostnames
```

## Getting started

```bash
cp .env.example .env          # fill in R2 credentials, secrets, etc.
make dev                      # starts Postgres + Redis via Docker Compose, then uvicorn --reload
make test                     # runs the unit test suite
make lint                     # ruff check + ruff format --check
make migrate                  # alembic upgrade head
```

`DECISION_HMAC_SECRET` and `ADMIN_SECRET` must each be at least 64 characters
of random entropy:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Tech stack

Python 3.12 · FastAPI + uvicorn · Pydantic Settings · SQLAlchemy async +
asyncpg · Alembic · Redis (`redis[asyncio]`) · Cloudflare R2 via
`aiobotocore`/`boto3` · httpx · structlog · pytest + pytest-asyncio

## Security posture (MVP)

The MVP serves open-access data only, but several safety properties are
built in from the start rather than bolted on later:

- **Decision token invariant** — the serve stage requires a signed
  `Decision`; a `Decision` can only be constructed by `stage4_decision.decide()`,
  which requires `DECISION_HMAC_SECRET`.
- **Origin allow-list** — checked before any network call; an unlisted host
  never reaches the origin.
- **No raw IP retention** — client IPs are SHA-256 hashed with a daily-
  rotating salt before they touch any log or the audit table.
- **HTTPS-only** — both client-facing and origin-fetch traffic; non-https
  origin URLs are rejected at Stage 0.


