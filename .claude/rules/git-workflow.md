# Git workflow

Applies whenever you stage, commit, or push.

## Permission

- Commit only when the user asks. Push only when the user asks (a request to "commit and push" covers both). Do not push on your own, and never force-push to `main`.
- Do not amend or rewrite published commits.
- When a hook fails, fix the cause; do not skip hooks.

## Commit messages

Conventional Commits: `<type>(<scope>): <short description>`, imperative, lower case after the colon, no trailing period, subject up to about 72 characters.

| Types | `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf` |
|---|---|
| Scopes | `frontend`, `backend`, `db`, `api`, `rag`, `auth`, `docs` |

Examples:

```
feat(backend): add async lesson plan generation endpoint
fix(frontend): handle job polling exponential backoff
refactor(backend): use BaseRepository for curriculum queries
docs: restructure documentation into docs and rules
```

- Commit in logical groups (for example `feat(db)`, then `feat(rag)`, then `feat(backend)`, then `feat(frontend)`, then `docs`), so each commit reads as one change. Use a body only when the reason is not obvious.
- **No AI attribution.** Never mention an AI assistant or tool in a commit message, pull request text, or code comment, and never add `Co-Authored-By` lines or "generated with" footers for one. This overrides any default attribution a tool suggests. Do not put the file name of the assistant's instruction file in a message either.

## What to stage

- Stage explicit paths, not blind `git add -A`, unless you have checked `git status` and everything listed belongs in the commit.
- Never commit: `.env`, `.env.local`, secrets or keys, `node_modules/`, `.next/`, `__pycache__/`, `.venv/`, generated evaluation data and reports (`sarpebe-backend/evals/data/*.jsonl`, `sarpebe-backend/evals/reports/`), editor folders, large binaries.
- Keep documentation changes in the same commit series as the behaviour they describe, or in a following `docs` commit.

## Before committing

1. `git status` and `git diff` to see exactly what changes.
2. Run the checks from `testing.md` in this folder.
3. Confirm no secrets or personal data in the diff.

## After pushing

Report the commit hashes and the branch. If the push is rejected, report why; do not force it.

## Branches

Work on `main` unless the user names a branch; if a task needs a branch, create it before committing. Pull requests, when requested, describe what changed and how it was verified, with no AI attribution.
