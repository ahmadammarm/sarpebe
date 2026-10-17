# Frontend

`sarpebe-frontend/` is a Next.js 16 App Router application (React 19, TypeScript, Tailwind CSS 4, shadcn/ui primitives, TanStack Query, NextAuth 4, Zod 4, axios, lucide-react). All user-facing text is Indonesian. The visual language is described in [design-system.md](design-system.md).

## Routes

| Route | File | Access | Purpose |
|---|---|---|---|
| `/` | `app/page.tsx` | public | Landing page. Sections (ids): `beranda` (hero), `fase` (fase finder), `cara-kerja`, `sumber-rujukan` (with a sample module), `administrator`, `pertanyaan-umum` (FAQ). The header menu shows three of them. |
| `/login`, `/register`, `/forgot-password`, `/reset-password`, `/verify-email` | `app/(auth)/*` | public | Account flows. |
| `/lesson-plans` | `app/(dashboard)/lesson-plans/page.tsx` | signed in | Dashboard and list of the user's plans. |
| `/lesson-plans/new` | `.../new/page.tsx` | signed in | Request form, then live progress. |
| `/lesson-plans/[id]` | `.../[id]/page.tsx` | signed in | Editor (completed), progress (running), failure with retry (failed). |
| `/curriculum` | `app/(dashboard)/curriculum/page.tsx` | admin | Upload, list and delete curriculum PDFs. |
| `/api/auth/[...nextauth]` | route handler | - | NextAuth endpoints. |

`proxy.ts` (Next.js middleware via `withAuth`) requires a session for `/lesson-plans/*` and `/curriculum/*`, and redirects non-admins from `/curriculum` to `/lesson-plans?error=unauthorized_admin`. The backend enforces the same rules; the redirect only saves a round trip.

## Layers

```
app/ (pages)  ->  lib/hooks/  ->  lib/api/  ->  backend
```

- **Pages** assemble layout and feature components and trigger hooks. They never call `fetch` or the API client.
- **Hooks** (`lib/hooks/`) own server state with TanStack Query, polling, SSE, and mutations: `useLessonPlans.ts` (list, detail with polling while unfinished, create, update, delete, PDF download), `useJobStatus.ts`, `useCurriculum.ts`, `useAuth.ts`.
- **API client** (`lib/api/`): `client.ts` is the single axios instance (base URL from `config.ts`, bearer token from the NextAuth session on every request); `auth.ts`, `curriculum.ts`, `lesson-plans.ts` hold one function per endpoint. `streamJobStatus` is the one place that uses `fetch`, because the SSE stream needs a header and axios cannot stream in the browser.
- **Types** (`types/`) mirror backend schemas: `lesson-plan.ts` (v1 and v2 content, `Table`, `JobStatus`, `TEACHING_MODELS`), `curriculum.ts`, `auth.ts`, `next-auth.d.ts`.
- **Validation** (`lib/utils/validators.ts`): Zod schemas for every form (login, register, forgot and reset password, lesson plan creation, curriculum upload). Form data types come from `z.infer`.
- **UI state** that is not server data lives in React state or a store under `lib/stores/` (none is needed at present).

## Authentication in the browser

NextAuth with the credentials provider calls the backend login. The access and refresh tokens are kept inside the signed session cookie (never `localStorage`). `lib/authOptions.ts` renews the access token one minute before it expires, keeps the old token on a transient network error, and marks the session `RefreshAccessTokenError` when the backend refuses the refresh token; `SessionGuard` in `app/providers.tsx` then signs the user out. The session is re-checked every 4 minutes so a tab left open still renews. Login error codes map to Indonesian messages in `lib/utils/auth-errors.ts`. Details of the token model: [authentication-security.md](authentication-security.md).

## Creating a lesson plan

`app/(dashboard)/lesson-plans/new/page.tsx`:

1. The form collects kelas (with a live fase tag from `lib/utils/fase.ts`), mata pelajaran, topik, jumlah pertemuan (1 to 6), menit per pertemuan (20 to 240), model pembelajaran (select), and catatan kelas (up to 500 characters with a counter). `lessonPlanCreateSchema` validates before the request; field errors show inline.
2. `useCreateLessonPlan` posts and returns `{ id, job_id }`.
3. `useJobStatus(job_id)` follows the job: it first opens the authenticated SSE stream; if that fails or closes early it polls `GET /jobs/{id}` with exponential backoff (1.5 s up to 8 s). A 404 ends the job as failed. It returns `status`, `stage`, `error`, and `isDone`.
4. `GenerationProgress` shows the real steps: waiting, finding relevant parts of the CP, drafting, checking time and tables, ready. The user may close the page; the plan stays in the list.
5. On completion the page navigates to `/lesson-plans/{id}`; on failure `describeFailure` (`lib/utils/lesson-plan.ts`) turns the stored message into plain Indonesian with a hint, and the user can edit the inputs and retry. Retrying from the detail page reuses the plan's saved `request_options`.

## Editors

`app/(dashboard)/lesson-plans/[id]/page.tsx` chooses by `plan.schema_version`:

| Version | Component | Content |
|---|---|---|
| 1 | `LessonPlanEditor.tsx` | Title, objectives, activities (duration and description), materials, assessment, citations (read-only). |
| 2 | `LessonPlanEditorV2.tsx` | The full Modul Ajar, described below. |

`LessonPlanEditorV2` sections: general information (read-only identity, title, initial competencies, facilities, target students, Pancasila profile, learning model), core components (objectives with source chips, meaningful understanding, trigger questions, preparation), activities per meeting (editable tables with a running total of minutes against the target), assessment (diagnostic, formative, summative, overview table, rubric table), enrichment and remedial, reflection, attachments (worksheet, reading material, glossary), and references (read-only). Behaviour:

- Unsaved-change tracking compares JSON; a warning appears and `beforeunload` is armed while edits are pending.
- Saving tidies the content (drops blank lines and empty rows) and sends it with `PUT`. The server validates it and returns the stored version.
- `warnings` from the server checks appear in a notice at the top.
- Each objective shows the sources it came from (`S1 - document, hlm. 14`) as highlighted chips built from the server's `references`; an objective without a valid source is labelled as the model's own design. References cannot be edited.
- `components/ui/editable-table.tsx` edits a `Table`: columns are fixed (the backend requires one cell per column in every row), rows can be added and removed. From `sm` up it renders a real table with a textarea per cell; below `sm` each row becomes a labelled card so nothing scrolls sideways.
- PDF download calls the export endpoint and saves the blob (`downloadLessonPlanPdf`).

## Curriculum management (admin)

`UploadForm` validates a `.pdf` name and a size limit (`MAX_UPLOAD_MB`, 20) with Zod, posts multipart data, and `CurriculumList` polls while any document is `processing`. Labels entered here must match what teachers will type (see [troubleshooting.md](troubleshooting.md)).

## Error handling

`lib/utils/errors.ts` maps backend `code` values to Indonesian messages; the backend's English `detail` is never shown. `getErrorMessage(error, fallback)` returns the mapped text or the fallback. Add a code to `MESSAGES_BY_CODE` when the backend gains a user-facing one.

## Landing page

The three header items (`cara-kerja`, `sumber-rujukan`, `administrator`) live in `components/landing/menu.ts` (a plain module importable from server and client code) and each `id` must match a `<section id>` in `app/page.tsx`; the header highlights the section in view. Content describes only real behaviour. `SampleModule` shows an example module (activity table and rubric) clearly labelled as an example; `FaseFinder` maps a class number to its fase using `lib/utils/fase.ts`.

## Environment

`NEXT_PUBLIC_API_BASE_URL`, `NEXTAUTH_URL`, `NEXTAUTH_SECRET` (see [configuration.md](configuration.md)).

## Commands

From `sarpebe-frontend/`: `pnpm install`, `pnpm dev` (port 3000), `pnpm build`, `pnpm start`, `pnpm lint`, and `npx tsc --noEmit` for a type check. There is no automated frontend test suite yet; see [testing.md](testing.md).
