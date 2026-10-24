# Design system rules ("buku tulis modern")

Applies to all UI work in `sarpebe-frontend/`. The full description, with the palette table, is in `docs/design-system.md`. Tokens live in `app/globals.css`.

## Visual language

A modern school notebook: paper surfaces, ruled lines, a red margin rule, ballpoint-blue actions, a yellow highlighter reserved for cited sources. Calm and legible for teachers; not a children's template, not generic SaaS. Light and dark themes (`data-theme="dark"` on `<html>`).

## Colors

- Use semantic classes: `bg-paper`, `bg-sheet`, `text-ink`, `text-ink-soft`, `border-rule`, `border-rule-strong`, `text-ballpoint`, `bg-wash`, `text-margin-text`, `bg-margin-wash`, `text-tick`, `bg-tick-wash`, or shadcn names (`bg-primary`, `border-input`).
- Never hard-code hex values or Tailwind palette colors (`emerald-*`, `slate-*`). Change a color by changing its token in both themes.
- Errors use margin red, success uses tick green, actions use ballpoint blue. Status is always an icon plus a word (`<StatusStamp>`), never color alone.
- The highlighter (`<Mark>`, `.mark`) has a fixed fill and ink in both themes. Do not set a theme-dependent text color on it. Use it only for cited sources and at most one key phrase per screen.
- Overlays that dim the page use a fixed `bg-black/50`, not a theme color (`--ink` is light in dark mode).

## Typography

Headings: Bricolage Grotesque (`font-display`, already applied to `h1` to `h3`). Text: Atkinson Hyperlegible Next. Margin notes: Caveat (`font-hand`), short annotations only. Inputs stay at 16 px (`text-base`).

## Components and structure

- `<Sheet>` for a page of paper (`margin` adds the red rule); `<Notice>` for inline messages; `<ConfirmDialog>` for confirming something that cannot be undone (pass a password field as its children when the action needs one); `<Pagination>` for paged lists; `<Field>` and `<PasswordField>` for inputs so label, hint and error are linked; `Textarea lined` for one-item-per-line fields; `EditableTable` for tables.
- Link-styled buttons: `buttonVariants()` on `<Link>`; never nest a `<Button>` in a link.
- New primitives go in `components/ui/` and take no domain props. Brand pieces go in `components/brand/`.
- Structural devices (numbering, dividers, labels) must encode something true about the content. Do not number things that are not a sequence.

## Layout and responsiveness

- Design from 320 px up. Side gutters `px-5 sm:px-6 lg:px-8`. Breakpoints `sm`, `md`, `lg`; `min-[480px]:` for phone landscape.
- Top bars use `components/brand/HeaderShell`. Below `md` the bar shows only the name, the theme toggle and a hamburger icon; links, the user's name and role, and "Keluar" go in the sliding panel. New navigation goes in the `nav`, `actions` and `panel` props, not on the phone bar. The open panel dims the page and locks scrolling.
- Flex and grid children get `min-w-0`; long user text gets `[overflow-wrap:anywhere]`. Buttons grow on touch via `pointer-coarse:`.
- No horizontal page scroll. Editable tables become cards below `sm`.

## Motion

CSS-only, purposeful, and reduced-motion aware. Use `.rise` (page load, `--delay` stagger), `<Reveal>` (scroll into view), `<Mark draw>`, `.row-in`, `.pop`, and `animate-in fade-in` for notices. Hidden-until-revealed styles apply only under `html[data-js]`. Add motion only where it explains a state change or points at the one thing that matters; extra animation reads as generated.

Theme switch: `setTheme(theme, origin)` in `lib/theme.ts` uses `document.startViewTransition` with a `clip-path` circle growing from the toggle's center; it falls back to an instant switch and respects reduced motion. Pass the toggle button's center as `origin`.

## Accessibility

Visible keyboard focus on every control; labels on every input; inline field errors; `aria-live` for status and save messages; table captions and header scopes; check contrast in both themes when adding a color pair.

## Copy

- All user-facing text is Indonesian, sentence case, plain verbs, no emojis, no filler.
- A control says what happens ("Simpan perubahan", "Susun modul ajar"); an action keeps one name through its flow.
- Errors say what went wrong and what to do; they never apologize and are never vague. Show backend errors through `getErrorMessage`, never the backend's English `detail`.
- Describe only what the app really does. No testimonials, statistics, or contact details that are not real.
- Use teachers' words (Capaian Pembelajaran, Modul Ajar, fase, asesmen), not system words (job, token, schema).
- Landing menu items live in `components/landing/menu.ts`; each `id` must match a `<section id>` in `app/page.tsx`.
