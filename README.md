# Vacancy Max

Tell it how many paid leave days your company gives you. It tells you exactly
which days to request so that Moroccan public holidays do the rest of the work.

> 18 days of leave, planned well, can be 40+ days away from the office.

## The one input

    POST /api/v1/optimizer/plan/   {"days": 18}

Year, weekends and the Moroccan holiday calendar are the app's knowledge, not
the user's. See [ADR 0002](docs/adr/0002-single-user-input.md).

## Stack

| Layer | Choice |
| --- | --- |
| Backend | Django 5.2 LTS · Django REST Framework · Python 3.13 (via `uv`) |
| Database | PostgreSQL 17 (SQLite for tests) |
| Frontend | React 19 · TypeScript · Vite · TanStack Query |
| Contract | drf-spectacular → OpenAPI → `openapi-typescript` (generated, never hand-written) |
| Quality | ruff · mypy --strict · pytest + Hypothesis · ESLint · Vitest · pre-commit · GitHub Actions |

## Layout

    backend/
      config/            settings split by environment, urls, asgi/wsgi
      apps/
        common/          shared bases, the single API error envelope
        accounts/        custom User (declared early, used from M5)
        calendars/       holiday data + "is this day off?"
        optimizer/
          domain/        ★ pure Python solver. zero Django. CI-enforced.
          services.py    the only bridge between ORM and domain
          api/           thin views over services
      tests/             domain (fast, pure) · integration · api
    frontend/
      src/app/           router, providers
      src/features/      feature-first: optimizer, calendar
      src/shared/        api client, ui primitives, hooks
    docs/                domain model, algorithm, ADRs

## Getting started

    cp .env.example .env
    make install          # uv sync + npm install + pre-commit hooks
    docker compose up -d  # optional: Postgres. omit to use SQLite.
    make migrate
    make seed             # load Moroccan holidays
    make dev-api          # http://localhost:8000/api/docs/
    make dev-web          # http://localhost:5173

Run `make` alone to list every target.

## Roadmap

| | Milestone | Ships |
| --- | --- | --- |
| M0 | Scaffold | ✅ structure, tooling, CI, docs |
| M1 | Calendar | Holiday YAML, models, seed command, year endpoint |
| M2 | Solver | The pure domain optimizer, TDD, property-based tests |
| M3 | API | `POST /optimizer/plan/`, OpenAPI schema, generated TS types |
| M4 | UI | One input, a year heatmap, break cards |
| M5 | Accounts | Save plans, `.ics` export, share links |

## Ground rules

1. No Django import inside `optimizer/domain/`. CI enforces it.
2. Views are thin. Logic lives in `services.py` and the domain.
3. Frontend API types are generated (`make types`), never typed by hand.
4. Holiday data changes are YAML diffs, reviewed like code.
5. Unconfirmed Hijri dates are labelled as estimates wherever they are shown.
