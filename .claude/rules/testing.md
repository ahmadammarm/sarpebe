# Testing rules

Applies to all code changes. Background: `docs/testing.md`.

## Before finishing any change

- Backend changes: run `pytest` from `sarpebe-backend/` (use the project's `.venv`). All tests must pass.
- Frontend changes: from `sarpebe-frontend/` run `npx tsc --noEmit`, `pnpm lint`, `pnpm build`.
- Report failures honestly with the output. Do not claim success for steps that were not run.
- Do not start dev servers, run the worker, or take screenshots unless the user asks.

## Backend tests

- Framework: pytest, pytest-asyncio (`asyncio_mode = auto`), httpx. Unit tests in `tests/unit`, endpoint tests in `tests/integration`.
- No test may use the network, a real Gemini key, Redis, or PostgreSQL. Mock `generate_structured`, the embedding service, storage, and Celery `.delay`.
- Use `tests/conftest.py` fixtures: `async_client` (app with mocked DB), `override_auth` and `mock_user`, `db` (in-memory SQLite with auth tables only). Do not set secrets in tests beyond what `conftest.py` sets.
- Build data with `tests/factories.py` (`make_request`, `make_passage`, `activities_table`, `make_modul_dict`); extend the factories instead of copying big dictionaries.
- New behaviour gets a test; every new failure mode gets a test of what the user sees (status and `code`, or the plan's failure message). Bug fixes start with a test that fails first.
- Keep old-version behaviour tested when content shapes change (v1 plans still open and export).
- Prompt builders, checks, chunkers, fusion and metrics are pure functions: test them directly with small inputs.
- Tests must not depend on the developer's `.env`.

## What cannot be tested here

pgvector search, full-text search and row locking need PostgreSQL. Verify those by reasoning, offline migration rendering, and the evaluations (`docs/ai-evaluation.md`), and say so.

## Evaluations

`python -m evals.run ...` calls live models and the database and costs tokens. Never add it to tests or CI, and never run it without being asked. Test only its pure helpers (`tests/unit/test_evals.py`).

## Frontend

There is no test runner yet. Type checking, linting and a production build are the minimum. If a runner is added, document it in `docs/testing.md` and here.

## Style

- Name tests for behaviour (`test_repair_keeps_first_answer_when_second_is_worse`).
- One assertion topic per test; arrange data with factories; no sleeps.
- Do not weaken or delete a test to make a change pass; fix the cause or explain why the test is obsolete.
