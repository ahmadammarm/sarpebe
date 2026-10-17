// Plain module (no "use client") so both the server-rendered page and the client header can import it.

/** The three landing-page menu items; each id is the id of a <section> on the page. */
export const LANDING_MENU = [
  { id: "cara-kerja", label: "Cara kerja" },
  { id: "sumber-rujukan", label: "Sumber rujukan" },
  { id: "administrator", label: "Administrator" },
] as const;
