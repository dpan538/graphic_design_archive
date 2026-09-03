/* Theme colour — the Index's one classification that carries colour: eight
   of the site's own spot colours, each distinct from the next. Colour never rides
   alone: every dot carries a title/aria label, and the theme name sits in
   the filter and the active-state line. Keyed by the release's eight
   governed themes (the Search facets). */

import type { IndexRecord } from "./catalogue";

export const THEME_INK: Record<string, string> = {
  "Modern typography and layout": "var(--ink-2)",
  "Midcentury modern graphic communication": "var(--blue)",
  "World War and public-information graphics": "var(--red)",
  "Postwar exhibition and cultural posters": "var(--green)",
  "Public health and social communication": "var(--teal)",
  "Travel and transport poster culture": "var(--yellow)",
  "Corporate identity and design systems": "var(--pink)",
  "New Deal and civic poster programs": "var(--coral)",
};

export const themeInk = (t: string) => THEME_INK[t] ?? "var(--ink-2)";

export type ThemeDot = { theme: string; ink: string };

/* Up to three theme dots per record — a scan mark, supplementary to the row
   text, tied to the Theme filter. */
export function themeDots(r: IndexRecord): ThemeDot[] {
  return r.themes.slice(0, 3).map((t) => ({ theme: t, ink: themeInk(t) }));
}
