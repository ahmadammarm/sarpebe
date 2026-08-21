# SARPEBE Frontend
**Next.js Web Application**

The frontend for SARPEBE is the primary user interface for Indonesian educators. It enables teachers to generate curriculum-aligned lesson plans, manage their history of generated plans, and upload official curriculum documents for the AI engine to reference.

---

## Tech Stack

| Technology | Version | Purpose |
|---|---|---|
| Next.js | 16.x | React framework with App Router |
| React | 19.x | UI component library |
| TypeScript | 5.x | Static type checking |
| Tailwind CSS | 4.x | Utility-first styling |
| ESLint | 9.x | Code linting |
| pnpm | latest | Package manager |

---

## Project Structure

The project follows a layered architecture where each directory has a single, clearly defined responsibility. No layer skips past the one below it.

```
sarpebe-frontend/
├── app/                        # Next.js App Router — pages and layouts
│   ├── layout.tsx              # Root layout: fonts, global providers
│   ├── page.tsx                # Landing / marketing page
│   ├── (auth)/                 # Auth route group (no dashboard shell)
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   └── (dashboard)/            # Protected route group with dashboard shell
│       ├── layout.tsx          # Dashboard layout: sidebar, topbar
│       ├── lesson-plans/
│       │   ├── page.tsx        # List all lesson plans (paginated)
│       │   ├── [id]/page.tsx   # View a single generated lesson plan
│       │   └── new/page.tsx    # Form to generate a new lesson plan
│       └── curriculum/
│           └── page.tsx        # Upload and manage curriculum documents
│
├── components/
│   ├── ui/                     # Primitive, reusable UI components (DRY base layer)
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   ├── Badge.tsx
│   │   ├── Card.tsx
│   │   ├── Modal.tsx
│   │   └── Spinner.tsx
│   ├── layout/                 # Structural shell components
│   │   ├── Sidebar.tsx
│   │   ├── Topbar.tsx
│   │   └── PageHeader.tsx
│   └── features/               # Feature-specific components composed from ui/
│       ├── lesson-plans/
│       │   ├── LessonPlanCard.tsx
│       │   ├── LessonPlanList.tsx
│       │   └── GenerateForm.tsx
│       └── curriculum/
│           └── DocumentUploader.tsx
│
├── lib/
│   ├── api/                    # All HTTP calls to the backend (centralized)
│   │   ├── client.ts           # Base HTTP client: base URL, auth headers, error handling
│   │   ├── lesson-plans.ts     # Lesson plan API functions
│   │   └── curriculum.ts      # Curriculum document API functions
│   ├── hooks/                  # Custom React hooks (abstract data fetching from UI)
│   │   ├── useLessonPlans.ts
│   │   ├── useLessonPlan.ts
│   │   └── useJobPolling.ts    # Polls job status until generation completes
│   ├── stores/                 # Global client state (Zustand or React Context)
│   │   └── auth-store.ts
│   └── utils/
│       ├── formatters.ts       # Date, number, token count display helpers
│       └── validators.ts       # Shared Zod schemas for form + API validation
│
├── types/                      # Global TypeScript interfaces (single source of truth)
│   ├── lesson-plan.ts
│   ├── curriculum.ts
│   └── api.ts                  # Generic API response, pagination, and error types
│
└── public/                     # Static assets
```

---

## Layered Architecture

```
Page (app/)
  |
  | uses
  v
Custom Hook (lib/hooks/)
  |
  | calls
  v
API Client (lib/api/)
  |
  | HTTP
  v
Backend API (sarpebe-backend)
```

Pages never call `lib/api` directly. Hooks manage all data fetching and state, keeping pages clean and declarative.

---

## DRY Principles Applied

- `lib/api/client.ts` is the single HTTP client instance. Auth headers, base URL, and global error handling are defined once — never repeated across individual API files.
- `types/` act as the single source of truth for data shapes, shared by pages, hooks, components, and API functions alike.
- `components/ui/` provides base UI primitives. Feature components compose from them rather than re-implementing styles or behaviors.
- `lib/utils/validators.ts` centralizes Zod schemas so the same validation rules apply to both form submission and API request payloads.

---

## Getting Started

### Prerequisites

- Node.js 20+
- pnpm

### Installation

```bash
cd sarpebe-frontend
pnpm install
```

### Environment Variables

Copy the example file and fill in the values:

```bash
cp .env.local.example .env.local
```

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Base URL of the SARPEBE backend API |
| `NEXT_PUBLIC_SUPABASE_URL` | Your Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Your Supabase anonymous key |

### Running the Development Server

```bash
pnpm dev
```

The application will be available at [http://localhost:3000](http://localhost:3000).

### Building for Production

```bash
pnpm build
pnpm start
```

### Linting

```bash
pnpm lint
```

---

## Related

- [Main Repository README](../README.md)
- [Backend — sarpebe-backend](../sarpebe-backend/README.md)
