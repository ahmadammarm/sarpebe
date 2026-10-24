# Frontend patterns (sarpebe-frontend)

Applies to everything under `sarpebe-frontend/`. Background: `docs/frontend.md`. Visual rules are in `design-system.md` in this folder.

## Layers

```
Page (app/) -> Hook (lib/hooks/) -> API client (lib/api/) -> backend
```

- **Pages** assemble layout and feature components and call hooks. They never import from `lib/api/` and never call `fetch`. They hold no business logic and little inline JSX.
- **Hooks** own server state (TanStack Query), polling, SSE and mutations. They contain no JSX.
- **API client**: `lib/api/client.ts` is the single axios instance; it adds `Authorization: Bearer <session accessToken>` and the base URL from `lib/api/config.ts` (`NEXT_PUBLIC_API_BASE_URL`). One file per resource (`auth.ts`, `curriculum.ts`, `lesson-plans.ts`), one function per endpoint. Only `lib/api/` may call `fetch` or axios, and the only `fetch` is the SSE stream in `lesson-plans.ts`.
- Components must not fetch server data themselves.

## State

- Server data: TanStack Query in `lib/hooks/`. Do not copy API data into `useState` or a store.
- UI-only state: React state, or a Zustand store in `lib/stores/` if it is shared (the folder does not exist until needed).
- Handle loading and error states explicitly in every hook consumer and page that fetches.

## Generation jobs

Creating a plan returns `202` with `job_id`. Use `useJobStatus` (authenticated SSE, polling fallback with exponential backoff) and show real progress from `status` and `stage`. Never assume the result is ready. Do not poll faster than the existing hooks do.

## Types and validation

- Every API shape has a TypeScript type in `types/` that mirrors the backend schema exactly; update both in the same change (`types/lesson-plan.ts` mirrors `app/schemas/lesson_plan_content.py`). No `any`: use `unknown` and narrow.
- Plans have two content shapes selected by `schema_version` (1 short, 2 full Modul Ajar). New code must keep v1 working; choose the editor with `schema_version`.
- Every form uses a Zod schema from `lib/utils/validators.ts`; form types come from `z.infer`. Validate before the request and show errors inline next to the field, not only in a toast.
- Show backend errors through `getErrorMessage` (`lib/utils/errors.ts`), which maps `code` to Indonesian. Add a mapping when the backend adds a user-facing code.

## Authentication

NextAuth credentials session against `/api/auth/login`. Tokens live in the signed session cookie, never in `localStorage`; the refresh token is not exposed to browser code. `lib/authOptions.ts` renews tokens; `SessionGuard` signs out on refresh failure; `proxy.ts` protects `/lesson-plans/*`, `/curriculum/*`, `/profile/*` and `/admin/*`. After the profile is saved, call `useSession().update({ name })` so the header shows the new name. Do not show protected content to unauthenticated users, even briefly.

## Components

```
components/ui/        primitives (Button, Input, Field, Select, Textarea, Notice, EditableTable); no domain props
components/features/  domain components composed from ui (may know LessonPlan, CurriculumDocument)
components/brand/     notebook-paper pieces (Sheet, Mark, HeaderShell, StatusStamp, FaseTag, ...)
components/landing/   landing page only
```

- Need a new primitive? Add it to `components/ui/`; do not re-implement it inside a feature.
- Named exports for components; default exports only where Next.js requires them (pages, layouts, route handlers).
- Components are `const` arrow functions or function declarations consistently with the surrounding file.
- A module imported by both server and client components must not be a `"use client"` file: constants and helpers shared with server components go in plain modules (as `components/landing/menu.ts` and `lib/theme-script.ts`). Importing a value from a client module into a server component yields a client reference, not the value.

## TypeScript and style

- TypeScript only in `app/`, `components/`, `lib/`, `types/`.
- `async/await`, not `.then()` chains.
- No `console.log` in committed code.
- Tailwind utility classes; custom CSS only in `app/globals.css`. Inline `style` only for genuinely dynamic values. Use design tokens, not arbitrary values.
- Use one place per concern: formatting helpers in `lib/utils/`, schemas in `validators.ts`, types in `types/`, HTTP in `lib/api/`. If a formatter file does not exist yet, create `lib/utils/formatters.ts` rather than formatting inline in components.

## Commands before committing

`npx tsc --noEmit`, `pnpm lint`, `pnpm build` (from `sarpebe-frontend/`). Do not start the dev server or take screenshots unless asked.
