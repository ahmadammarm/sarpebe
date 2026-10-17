# Documentation

Detailed documentation for SARPEBE. The repository root holds only the top-level `README.md`; everything else is here. Instructions and code rules for AI coding assistants live in `.claude/` (see `.claude/CLAUDE.md` and `.claude/rules/`).

| Document | Read it to |
|---|---|
| [architecture.md](architecture.md) | Understand the system, layers, and the end-to-end flows. |
| [getting-started.md](getting-started.md) | Set up a machine and generate a first lesson plan. |
| [configuration.md](configuration.md) | Look up any environment variable or fixed constant. |
| [operations.md](operations.md) | Run, deploy, migrate, reindex, and monitor. |
| [api-reference.md](api-reference.md) | Call the REST API: endpoints, bodies, status and error codes. |
| [authentication-security.md](authentication-security.md) | Understand tokens, sessions, rate limiting, and the security model. |
| [ai-pipeline.md](ai-pipeline.md) | Follow the AI flows: ingestion, retrieval, generation, checks, failures, costs, export. |
| [ai-evaluation.md](ai-evaluation.md) | Measure and compare retrieval and generation quality. |
| [database.md](database.md) | See the schema, indexes, rules for queries, and migration history. |
| [frontend.md](frontend.md) | Navigate the Next.js app: routes, data flow, editors. |
| [design-system.md](design-system.md) | Follow the notebook-paper visual language, motion, and copy rules. |
| [testing.md](testing.md) | Run and write tests; know what is and is not covered. |
| [troubleshooting.md](troubleshooting.md) | Fix common problems. |

## Where to start

- New developer: [getting-started.md](getting-started.md), then [architecture.md](architecture.md).
- Working on the AI: [ai-pipeline.md](ai-pipeline.md) and [ai-evaluation.md](ai-evaluation.md).
- Integrating with the API: [api-reference.md](api-reference.md).
- Deploying: [operations.md](operations.md) and [configuration.md](configuration.md).

## Keeping the docs true

Update the relevant document in the same commit as the code change: a new endpoint goes in `api-reference.md`, a new setting in `configuration.md` and `.env.example`, a schema change in `database.md`, a prompt or retrieval change in `ai-pipeline.md` with its evaluation numbers in `ai-evaluation.md`. Do not use emojis. Keep each fact in one place and link to it from elsewhere.
