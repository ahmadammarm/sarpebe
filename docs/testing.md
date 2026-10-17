# Testing

## Backend

Framework: pytest with pytest-asyncio (`asyncio_mode = auto`), pytest-mock, and httpx for API tests. Configuration is in `sarpebe-backend/pytest.ini`. About 350 tests run in under 20 seconds and need no network, no Gemini key, no Redis, and no PostgreSQL.

```bash
# from sarpebe-backend/, virtual environment active
pytest                                    # everything
pytest tests/unit                         # unit tests
pytest tests/integration                  # API tests with mocked collaborators
pytest tests/unit/test_chunking.py        # one file
pytest tests/unit/test_chunking.py -k oversize    # one test by name
```

### Layout

```
tests/
  conftest.py        environment for tests, fixtures (mock_user, override_auth, mock_db, async_client, db)
  factories.py       builders: make_request, make_passage, activities_table, make_modul_dict
  fixtures/          sample files
  unit/              pure logic and services with mocked I/O
  integration/       FastAPI endpoints through httpx with dependency overrides
```

### Fixtures and conventions

- `conftest.py` sets `AUTH_JWT_SECRET`, `EMAIL_BACKEND=console`, and `REQUIRE_EMAIL_VERIFICATION=true` before the app is imported, so tests never read the developer's `.env` secrets.
- `async_client` is an httpx client over the real FastAPI app with `get_db` replaced by `mock_db` (an `AsyncMock`). `override_auth` replaces `get_current_user` with `mock_user`. Endpoint tests therefore check routing, validation, status codes and error codes, not database behaviour.
- `db` is a real SQLAlchemy session on in-memory SQLite (aiosqlite) containing only `profiles`, `refresh_tokens` and `auth_tokens`. Use it for repository and auth-service logic that needs real rows. PostgreSQL-specific features (pgvector, `tsvector`, `FOR UPDATE` behaviour) cannot run on SQLite and are not covered by it.
- Gemini is always mocked (patch `generate_structured`, `embedding_service`, or the client). No test may call the network.
- Build test data with the helpers in `tests/factories.py` instead of repeating large dictionaries; `make_modul_dict` returns a valid v2 Modul Ajar that tests then mutate to create each failure.

### What is covered

| Area | Test files |
|---|---|
| Authentication | `test_security.py`, `test_auth_service.py`, `integration/test_auth_api.py`, `test_seed_users.py` |
| Ingestion | `test_pdf_extract.py` (builds a PDF with a table in the test), `test_chunking.py`, `test_ingestion_service.py`, `test_embedding_service.py`, `test_labels.py` |
| Retrieval | `test_retrieval.py` (fusion, floor, rerank, passage selection, query), `test_fase.py` |
| Generation | `test_lesson_plan_prompt.py`, `test_lesson_plan_content.py`, `test_lesson_plan_checks.py`, `test_llm_client.py`, `test_llm_service.py`, `test_generation_task.py` |
| Plans and export | `test_lesson_plan_service.py`, `test_modul_pdf.py`, `integration/test_lesson_plans_api.py`, `integration/test_curriculum_api.py`, `integration/test_api.py` |
| Costs | `test_cost_calculator.py`, `test_cost_logging.py` |
| Evaluation helpers | `test_evals.py` (pure functions only) |

### Writing a test for new behaviour

1. Put pure logic in `tests/unit` and endpoint behaviour in `tests/integration`.
2. Mock Gemini, storage and Celery `.delay`; assert on what was sent (for example that the prompt has tagged data and no schema, or that a repair call happens exactly once).
3. For every new failure mode add a test that proves the user-visible result (status code and `code`, or the plan's `failed` message).
4. Keep the existing behaviour of old schema versions covered when changing content shapes.

## Frontend

There is no automated test suite yet. Before committing frontend changes run, from `sarpebe-frontend/`:

```bash
npx tsc --noEmit      # types
pnpm lint             # eslint
pnpm build            # compiles every route; catches server/client module mistakes
```

Check behaviour manually in a browser for UI work. If a test runner is added later, put the setup instructions here and add the command to `.claude/rules/testing.md`.

## Evaluations are not tests

`python -m evals.run ...` measures retrieval and generation quality on real documents with live models. It costs tokens and is never part of `pytest` or CI. See [ai-evaluation.md](ai-evaluation.md).

## Before every commit

1. `pytest` passes.
2. For frontend changes, `npx tsc --noEmit`, `pnpm lint` and `pnpm build` pass.
3. New or changed behaviour has a test; prompt or schema changes bump `PROMPT_VERSION` and have an evaluation comparison.

## Known gaps

- No PostgreSQL-backed tests: pgvector search, full-text search and row locking are exercised only against a real database by hand or by the evaluations.
- No browser or component tests for the frontend.
- No load tests for concurrent generation.
