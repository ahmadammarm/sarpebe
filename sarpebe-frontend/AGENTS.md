# SARPEBE Frontend — Agent Guide

This file provides AI coding agents with all necessary context, architectural rules, and engineering directives to work safely and correctly on the SARPEBE frontend.

---

## Project Context

You are working on the frontend of SARPEBE, an Educational SaaS. The frontend is a Next.js 16 application that serves as the primary interface for Indonesian educators to generate curriculum-aligned lesson plans, manage their history, and upload curriculum documents.

The frontend communicates exclusively with the SARPEBE backend via REST API. It has no direct database access.

---

## Tech Stack

| Tool | Version | Role |
|---|---|---|
| Next.js | 16.x | React framework with App Router |
| React | 19.x | UI rendering |
| TypeScript | 5.x | Static type safety |
| Tailwind CSS | 4.x | Utility-first styling |
| pnpm | latest | Package manager |
| ESLint | 9.x | Code linting |

Planned additions (not yet installed — install when needed):
| Tool | Role |
|---|---|
| Zustand | Global client state management |
| Zod | Schema validation for forms and API responses |
| TanStack Query | Server state, caching, and background refetching |

---

## Architecture

The project follows a strict layered architecture. Each layer may only call the layer directly below it.

```
Page (app/)
    Handles: Routing, layout composition, data-fetching trigger
    No direct API calls. No raw fetch() calls.
    |
    v
Custom Hook (lib/hooks/)
    Handles: Data fetching, loading/error state, side effects
    Calls the API client layer. Returns clean state to the page.
    |
    v
API Client (lib/api/)
    Handles: All HTTP communication with the backend
    Single base client. No fetch() calls outside this directory.
    |
    v
Backend API (sarpebe-backend)
```

### Directory Reference

```
sarpebe-frontend/
├── app/                        # Next.js App Router — pages and layouts only
│   ├── layout.tsx              # Root layout: providers, fonts, metadata
│   ├── page.tsx                # Landing page
│   ├── (auth)/                 # Auth route group — no dashboard shell
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   └── (dashboard)/            # Protected route group
│       ├── layout.tsx          # Dashboard shell: sidebar, topbar
│       ├── lesson-plans/
│       │   ├── page.tsx        # List lesson plans (paginated)
│       │   ├── [id]/page.tsx   # View single lesson plan
│       │   └── new/page.tsx    # Generate lesson plan form
│       └── curriculum/
│           └── page.tsx        # Upload and manage curriculum documents
│
├── components/
│   ├── ui/                     # Primitive, unstyled-or-minimally-styled components
│   ├── layout/                 # Structural shell components
│   └── features/               # Feature-specific composed components
│
├── lib/
│   ├── api/
│   │   ├── client.ts           # Base HTTP client — single instance
│   │   ├── lesson-plans.ts     # Lesson plan API functions
│   │   └── curriculum.ts       # Curriculum document API functions
│   ├── hooks/                  # Custom React hooks
│   ├── stores/                 # Global client state (Zustand)
│   └── utils/
│       ├── formatters.ts       # Display formatting helpers
│       └── validators.ts       # Shared Zod schemas
│
└── types/                      # Global TypeScript interfaces (single source of truth)
    ├── lesson-plan.ts
    ├── curriculum.ts
    └── api.ts                  # Generic API response, pagination, error types
```

---

## Engineering Directives

### 1. Layer Boundaries

- Pages (`app/`) must not import from `lib/api/` directly. Data fetching belongs in hooks.
- Hooks (`lib/hooks/`) must not contain JSX or rendering logic.
- Only files in `lib/api/` may call `fetch()` or the base HTTP client. No `fetch()` calls anywhere else.
- Components must not manage server state — that belongs in hooks using TanStack Query.

### 2. HTTP Client

- All API communication goes through `lib/api/client.ts`. This file is the single place where the base URL, default headers, and auth token injection are configured.
- Individual API files (e.g., `lesson-plans.ts`) call the base client — they never call `fetch()` directly.
- Global error handling (e.g., 401 redirect to login, 500 toast notification) is implemented once in `client.ts`, never duplicated across API files.

### 3. Async Generation and Job Polling

- Lesson plan generation returns `202 Accepted` from the backend with a `job_id`.
- The frontend must not assume the result is immediately available. After triggering generation, use `lib/hooks/useJobPolling.ts` to poll the job status endpoint at a regular interval.
- Show a loading/pending state to the user until the job resolves to `completed` or `failed`.
- Implement exponential backoff or a reasonable fixed interval (e.g., 3 seconds) for polling. Do not poll faster than necessary.

### 4. Type Safety

- All data structures returned from the API must have a corresponding TypeScript type in `types/`. Never use `any` or inline object types for API response shapes.
- API response types in `types/api.ts` must mirror the backend Pydantic schema exactly. When the backend schema changes, update the frontend type in the same pull request.
- Form field types must be derived from the Zod schema in `lib/utils/validators.ts`, not defined separately. Use `z.infer<typeof schema>` as the form's data type.

### 5. Forms and Validation

- All user-facing forms must use a Zod schema defined in `lib/utils/validators.ts`.
- Validation must run client-side before the API call is made. Do not rely solely on server-side validation for user-facing errors.
- Display field-level error messages inline with the relevant input. Do not only show a generic toast for form errors.

### 6. Authentication

- The auth token (Supabase JWT) is stored in the auth store (`lib/stores/auth-store.ts`), not in `localStorage` directly.
- `lib/api/client.ts` reads the token from the auth store and attaches it to every request as `Authorization: Bearer <token>`.
- Protected pages must check authentication in their layout or via Next.js middleware. Never show protected content to unauthenticated users, even briefly.

### 7. Component Structure

- `components/ui/` contains primitive components (Button, Input, Card, Badge, Spinner, Modal). These components accept no domain-specific props — they are purely presentational.
- `components/features/` contains domain-specific components composed from `components/ui/`. A feature component may know about `LessonPlan` or `CurriculumDocument` types.
- Pages compose from `components/features/` and `components/layout/`. Pages do not define significant inline JSX — they assemble components.

### 8. State Management

- Server state (data from the API) is managed by TanStack Query hooks in `lib/hooks/`. Do not put API response data in Zustand.
- Client state (UI state that is not fetched from a server, e.g., sidebar open/closed, modal visibility, auth session) is managed in `lib/stores/`.
- Do not use `useState` for data that should be fetched from the API. Use a custom hook backed by TanStack Query instead.

### 9. Styling

- Use Tailwind CSS utility classes. Do not write custom CSS files except for global base styles in `app/globals.css`.
- Do not use inline `style` props for anything other than genuinely dynamic values (e.g., calculated widths).
- Maintain consistent spacing, color, and typography by using design tokens defined in the Tailwind config rather than arbitrary values.

---

## DRY Conventions

- `lib/api/client.ts` is the single HTTP client. Auth headers, base URL, and error handling are defined once. Never duplicate them.
- `types/` is the single source of truth for all data shapes. Import from `types/` — never redeclare an interface inline in a component or hook.
- `lib/utils/formatters.ts` is the single place for all display formatting (dates, numbers, token counts, currency). Never format inline in a component.
- `lib/utils/validators.ts` is the single place for Zod schemas. The same schema is used for the form type, client-side validation, and (optionally) validating the API response.
- `components/ui/` components are the single source for base UI patterns. If a new primitive is needed, add it there — do not re-implement it in a feature component.

---

## Coding Standards

- All files must be TypeScript. No `.js` or `.jsx` files in `app/`, `components/`, `lib/`, or `types/`.
- Use `const` arrow functions for components: `const MyComponent = () => { ... }`.
- Export components as named exports, not default exports, except for page files which Next.js requires as default exports.
- Use `async/await` for all asynchronous operations. Avoid `.then()` chains.
- Handle loading and error states explicitly in every hook and page that fetches data.
- Do not use `console.log()` in committed code. Use structured logging or remove before committing.

---

## What NOT to Do

- Do not call `fetch()` outside of `lib/api/`. If a new endpoint is needed, add a function to the appropriate API file.
- Do not use `any` as a TypeScript type. If a type is unknown, use `unknown` and narrow it explicitly.
- Do not put business logic in pages or components. Logic belongs in hooks or utility functions.
- Do not hardcode the API base URL in individual files. It comes from `NEXT_PUBLIC_API_BASE_URL` via `lib/api/client.ts`.
- Do not store sensitive information (tokens, keys) in `localStorage` outside the auth store abstraction.
- Do not use the default Next.js README content — it has been replaced with a project-specific one.

---

## Environment Variables

All environment variables are prefixed with `NEXT_PUBLIC_` to be accessible in the browser. Declare them in `.env.local` (not committed) based on `.env.local.example`.

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Base URL of the SARPEBE backend API |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anonymous (public) key |

---

## Related

- [Root AGENTS.md](../AGENTS.md)
- [Backend AGENTS.md](../sarpebe-backend/AGENTS.md)
- [Frontend README](README.md)
