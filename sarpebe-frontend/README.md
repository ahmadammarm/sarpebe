# SARPEBE Frontend

Next.js web application for SARPEBE: landing page, account flows, lesson plan creation with live progress, a full Modul Ajar editor with editable tables and PDF or Word export, and curriculum document management for administrators. All text is Indonesian.

This file is a short orientation. The full documentation is in the repository's [docs](../docs/README.md) folder.

## Stack

Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS 4, shadcn/ui primitives, TanStack Query, NextAuth 4 (credentials), Zod 4, axios, lucide-react, pnpm.

## Layout

```
sarpebe-frontend/
  app/                 pages and layouts: (auth), (dashboard), landing, NextAuth route
  components/
    ui/                primitives (Button, Field, Select, Textarea, Notice, EditableTable, ...)
    features/          auth, curriculum, lesson-plans (editors, progress, list)
    brand/             notebook-paper design pieces (Sheet, Mark, HeaderShell, ...)
    landing/           landing page sections
  lib/
    api/               axios client and one file per resource
    hooks/             TanStack Query hooks, job tracking (SSE with polling fallback)
    utils/             validators (Zod), errors, fase, lesson plan helpers
  types/               types mirroring backend schemas
  proxy.ts             route protection (session and admin role)
```

Layers: Page -> Hook -> API client -> backend. See [frontend](../docs/frontend.md).

## Run it

```bash
pnpm install
cp .env.local.example .env.local     # NEXT_PUBLIC_API_BASE_URL, NEXTAUTH_URL, NEXTAUTH_SECRET
pnpm dev                             # http://localhost:3000
```

The backend must be running (see the [backend README](../sarpebe-backend/README.md)). Checks: `npx tsc --noEmit`, `pnpm lint`, `pnpm build`.

## More

| Topic | Document |
|---|---|
| Routes, data flow, editors | [frontend](../docs/frontend.md) |
| Visual language, motion, copy | [design-system](../docs/design-system.md) |
| Sessions and tokens | [authentication-security](../docs/authentication-security.md) |
| API the app calls | [api-reference](../docs/api-reference.md) |
| Environment variables | [configuration](../docs/configuration.md) |
| Problems | [troubleshooting](../docs/troubleshooting.md) |

Project overview: [root README](../README.md).
