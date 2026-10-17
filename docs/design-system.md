# Design system: "buku tulis modern"

The interface looks like a modern school notebook: paper surfaces, ruled lines, a red margin rule, ballpoint-blue actions, and a yellow highlighter reserved for cited sources. The aim is calm, legible, and education-appropriate, not a children's template and not generic SaaS. Tokens and utilities are defined once in `sarpebe-frontend/app/globals.css`.

## Palette

Always use the semantic classes below, or the shadcn names (`bg-primary`, `border-input`, `text-muted-foreground`). Do not hard-code hex values or Tailwind palette colors such as `emerald-*` or `slate-*`.

| Token | Class examples | Light | Dark | Use |
|---|---|---|---|---|
| `paper` | `bg-paper` | `#f5f7fc` | `#0e1424` | Page background. |
| `sheet` | `bg-sheet` | `#ffffff` | `#151d33` | Cards and the "page of paper". |
| `rule`, `rule-strong` | `border-rule` | `#dde5f4`, `#c3cfe8` | `#26314f`, `#34436a` | Dividers, ruled lines, input borders. |
| `ink`, `ink-soft` | `text-ink`, `text-ink-soft` | `#16213e`, `#55627f` | `#e9eef9`, `#9fadcb` | Text and secondary text. |
| `ballpoint`, `wash` | `text-ballpoint`, `bg-wash` | `#1d4ed8`, `#e8eefc` | `#8eabff`, `#1d2848` | Actions, links, focus, active steps. |
| `margin`, `margin-text`, `margin-wash` | `text-margin-text`, `bg-margin-wash` | `#d13b3b`, `#b42b2b`, `#fcebea` | `#ff8a80`, `#ff9d95`, `#3a1d26` | Errors, the margin rule, "unsaved" notes. |
| `tick`, `tick-wash` | `text-tick`, `bg-tick-wash` | `#136b43`, `#e3f5ec` | `#5ad1a0`, `#12332b` | Success, done steps. |
| `highlight` and `--mark-*` | `<Mark>` | `#ffe14d` fill, `#16213e` ink | same | The highlighter. Identical in both themes on purpose. |

Dark mode is set with `data-theme="dark"` on `<html>` (Tailwind `dark:` is wired to it). An inline script (`lib/theme-script.ts`) sets the theme before paint to avoid a flash.

## Typography

| Role | Font | Where |
|---|---|---|
| Headings | Bricolage Grotesque (`font-display`, applied to `h1` to `h3`) | Titles, section names. |
| Text | Atkinson Hyperlegible Next (`font-sans`) | Everything else; chosen for legibility because teachers read long documents. |
| Margin notes | Caveat (`font-hand`) | Short annotations only (for example "Dicatat otomatis dari dokumen CP"), never body text. |

Inputs use 16 px (`text-base`) so iOS does not zoom on focus.

## Components

| Component | Rule |
|---|---|
| `<Sheet>` (`components/brand`) | A page of paper. `margin` adds the red margin rule. Main content areas sit on a Sheet. |
| `<Mark>` | The highlighter. Only for cited sources and at most one key phrase per screen. `draw="load"` or `"view"` makes the stroke draw itself. Its text and fill are fixed (`--mark-ink`, `--mark-fill`); never give it a theme-dependent text color. |
| `Textarea lined` | Draws ruled lines behind text. Use for list-like fields (one item per line). |
| `<StatusStamp>` | Status is always an icon plus a word, never color alone. |
| `<Notice>` | Inline message with tone `error`, `success`, or `info`. Errors say what went wrong; the caller adds how to fix it. |
| `<Field>`, `<PasswordField>` | Label, input, and hint or error wired together with `aria-describedby`. Use them instead of loose inputs. |
| `EditableTable` | Cell-by-cell table editor; a real table from `sm`, labelled cards below it. |
| `FaseTag` | Shows the Kurikulum Merdeka fase for a class number. |
| `buttonVariants()` | Apply to a `<Link>` for link-styled buttons; do not nest a `<Button>` in a link. |

Primitives in `components/ui` take no domain props. Domain components live in `components/features`; brand pieces in `components/brand`.

## Layout and responsiveness

- Design from 320 px up. Page side gutters are `px-5 sm:px-6 lg:px-8` (20 px on phones); keep new containers on that scale. Use `sm`, `md`, `lg` for layout changes and `min-[480px]:` for the few phone-landscape cases.
- Top bars (landing `LandingHeader` and the workspace layout) both use `components/brand/HeaderShell`. Below `md` (768 px) the bar shows only the name, the theme toggle, and an icon-only hamburger. Links, the user's name and role, and "Keluar" live in a panel that slides down under the bar. Put new navigation in the `nav` and `actions` props and the `panel` render prop, not on the phone bar.
- While the phone menu is open `HeaderShell` dims the page with a fixed `bg-black/50` scrim (never a theme color, because `--ink` is light in dark mode) and locks page scrolling.
- Give flex and grid children `min-w-0` and long user text `[overflow-wrap:anywhere]`. Buttons grow on touch screens via `pointer-coarse:`.
- Tables never force horizontal page scroll: editable tables become cards below `sm`; read-only sample tables scroll inside their own container.

## Motion

Motion is purposeful, CSS-only (no animation library), and respects `prefers-reduced-motion`.

| Pattern | Use |
|---|---|
| `.rise` with a `--delay` stagger | Page-load entrances. |
| `<Reveal>` | Content that appears as it scrolls into view. |
| `<Mark draw>` | The highlighter draws itself. |
| `.row-in`, `.pop` | Mounting list rows, completed-step check. |
| `animate-in fade-in ...` (`tw-animate-css`) | Notices and status text. |

Hidden-until-revealed styles apply only under `html[data-js]`, so nothing is hidden when JavaScript is off. Reduced motion collapses durations globally and skips the theme transition. Add motion only where it explains a state change or points at the one thing that matters.

### Theme switch

`setTheme(theme, origin)` in `lib/theme.ts` wraps the change in `document.startViewTransition` and animates `clip-path` on `::view-transition-new(root)` as a circle growing from the toggle button's center (pass that center as `origin`). It falls back to an instant switch when the API is missing.

## Accessibility

- Visible keyboard focus on every control (`focus-visible:ring-3 ring-ring/40` pattern).
- Labels for every input; inline field errors, not only toasts; `aria-live` for status and save messages.
- Status never relies on color alone. Check contrast in both themes when adding a color pair.
- Tables have captions (visually hidden when the heading already names them) and header scopes.
- Inputs and selects are 40 px high (`h-10`); buttons grow on touch screens via `pointer-coarse:`.

## Copy

- All user-facing text is Indonesian, sentence case, plain verbs, no emojis. A control says what happens ("Simpan perubahan", "Susun modul ajar"); an action keeps the same name through the flow.
- Errors never apologize and are never vague: say what went wrong and what to do. Show backend errors through `getErrorMessage`, never the backend's English `detail`.
- Describe only what the app actually does. Do not add testimonials, statistics, or contact details that are not real.
- Technical words teachers know are fine (Capaian Pembelajaran, Modul Ajar, fase, asesmen); avoid system words (job, token, schema) in the interface.
