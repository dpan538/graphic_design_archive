### Register — the owner's palette for this view

Grey-white paper `#e8e6e0` as the ground, black `#0a0a0b` type (82 % for prose; labels
`#5f5e5a`), light grey `#c4c3be` for rules. The light blue `#a9c2e4` of the object's plate
is the page's core colour and the saturation everything else is set to (the owner,
2026-09-05): coral `#dd745f` as the one highlight (selection); Medium cyan `#53b3c6`,
Theme green `#3fa684`, Movement warm orange `#d49454` — hues from two reference posters
(a colour chart; a conference poster) at that saturation — used the same way in every
template, on the canvas (the field's outline and accent bar, the chip's bar), in the rail
and the rows (dots) and in the inspector (the dimension's dot): lines and small marks,
never a fill, never the only carrier (the word is always there), never a reading of
strength, confidence or rank. A template may not change the palette.

### The export

The PNG is the reference renderer's (`export-png.ts`, untouched): 224 × 104 boxes joined by
orthogonal connectors with a label at each connector's middle, and a public-safe footer.
That renderer was built for a lane layout; drawn over the canvas's own arrangement its
labels landed on the boxes (the owner's export of 2026-09-04). The composition is therefore
exported in its lanes — the object at the left, its contexts in one column 232 px to the
right, in the projection's order (`lib/arrange.ts exportLayout`) — the same visible set as
the canvas, only the positions differ. Checked in the browser by rendering the export SVG
itself (dev hook `window.__mgdaContextCanvas.exportSvg()`): no text lies on a box or on
another text. What the renderer still does that a later export round must settle: labels
truncated at 18 display units ("Portfolio Cove…"), kind names as `archive_object`, the
projection hash in the footer, no legend, no MGDA identity.

# Frontend Design Decision

Single source of truth for the Modern Graphic Design Archive frontend redesign.
Supersedes the prior "civic ephemera / railway-ticket" interface system. Every
later round refers back to this document.

- **Status:** active — Round 1 (About) in progress
- **Basis:** `origin/main @ 5cbf38bb` (worktree `modern_GD_history_frontend_redesign`, branch `feat/frontend-redesign`)
- **Build/serve target:** `next dev --port 8000` → `localhost:8000`
- **Not changed by frontend work:** database, frozen v49 inputs, API schemas, Search ranking/filters/eligibility, TRACE evidence, association validation, Open Inquiry status, rights decisions, AI/model behavior, TRACE mobile activation policy.

---

## 1. Brand

- **Name:** Modern Graphic Design Archive (was "Graphic Design Archive" / "Modern Graphic Design History" / "Archive Box" — all retired).
- **Domain:** `mgdarchive.com` (purchased; public deployment pending — `DEPLOYMENT_PERFORMED=false`).
- **Repository:** `github.com/dpan538/graphic_design_archive`.
- **One-line purpose:** a verified, extensible platform for design researchers, learners, and AI/agent research tools to read, locate, and explore modern graphic design history.

---

## 2. Product architecture (fixed)

Two parallel homepage-level strategies, not a hierarchy:

```
Modern Graphic Design Archive
├── Global Search  — direct object finding; desktop + mobile; returns public object pages only
├── Index          — archive browsing / classification directory; desktop + mobile (NEW, approved scope)
└── TRACE          — desktop-only research environment (mobile → lightweight fallback)
      ├── Context Canvas       (Function 1)
      ├── Spacetime            (Function 2 — DEFERRED / NOT RELEASED in v49; a research direction under review, shown on the landing, no entry)
      └── Exploration          (Function 3)
            ├── Validated Exploration   — evidence-qualified, deterministic
            └── Open Inquiry            — explicitly unresolved, isolated, read-only
```

Invariants: one Search experience (deterministic relevance only); TRACE has exactly
three functions; Open Inquiry never implies validation and generates no pair edges;
no archive-object image is ever assumed (0 positive visual-rights records);
"System suggests" is optional secondary orientation and provider identity is
disclosed **only** on About/Methodology.

---

## 2a. Positioning, scope & history (canonical)

**What MGDA is — with a primary, not a menu of equals:**

| | |
|---|---|
| **Primary** | A **digital humanities research archive** for modern graphic design history |
| **Infrastructure** | A **governed, verified archive database** |
| **Public interface** | A **designed research interface** over that database |
| **Not** | an educational platform · a commercial discovery product · an online museum · an image-collection website |

It is "a digital humanities research archive" precisely because it holds all of:
**archive · database · provenance · research methods · public reading ·
computational exploration**. (TRACE, in particular, is closer to a research
platform than to reading.)

**Canonical one-liner** (opens the Homepage and About; may be trimmed per surface,
never contradicted):

> A digital humanities research archive for modern graphic design history — built
> from verified records, explicit provenance, and evidence-bounded computational
> research. It is an extensible research infrastructure for locating, reading, and
> examining design-historical records, not a complete history of graphic design.

**Scope & history statement** (the project's own account of how the corpus was
built — reused on Homepage §02 and About/Methodology):

> Since 2024, the Modern Graphic Design Archive has been built through sustained
> archival research rather than automated aggregation. More than **40,000
> candidate records** were located across institutional collections, catalogues,
> archives, and scholarly sources, then reviewed, reconciled, and screened for
> provenance, duplication, publication status, and research relevance. That
> process established a governed archive of **15,923 canonical records**. Of
> these, **7,995** form the current public research archive; **7,928** remain
> held, where the evidence, rights, or publication criteria are not yet
> sufficient for public inclusion. The archive is offered not as a complete
> history of modern graphic design but as a deliberately bounded,
> source-traceable foundation that researchers, learners, and computational
> systems can inspect, question, and extend.

**Author context** (background only — not shown as a credential on the public
UI): Dai Pan / 潘岱 — BFA Design, School of Visual Arts (New York); Master of
Information Technology, University of Queensland. Database work and
design-historical research are the two through-lines; the frontend brief follows
from them — **academic in its claims, editorial in its design, product-grade in
its usability.**

---

## 3. Information architecture — nine pages

| # | Page | Route | Core purpose | Platform |
|--:|------|-------|--------------|----------|
| 1 | Homepage | `/` | Brand entry + Search (expandable window) | desktop + mobile |
| 2 | Index | `/directory` (route folder `index` is reserved by the App Router; visible label stays "Index") | Region/Country · Year · Theme directory browsing, year-ordered | desktop + mobile |
| 3 | Object Page | `/surfaces/{id}` | One archive object — text + citation only, no image | desktop + mobile |
| 4 | TRACE | `/trace` | Entry to the three research functions | desktop (mobile → fallback) |
| 5 | Context Canvas | `/trace/context-canvas` | TRACE Function 1 | desktop (mobile → fallback) |
| 6 | Spacetime | `/trace/spacetime` | TRACE Function 2 — **deferred, not released in v49**: the route is a release boundary, not a surface | desktop + mobile (a text page) |
| 7 | Exploration | `/trace/exploration` | TRACE Function 3 — Validated Exploration + Open Inquiry | desktop (mobile → fallback) |
| 8 | About | `/about` | Project identity, methodology, design rationale, citation, claim boundaries | desktop + mobile |
| 9 | Source | `/source` | Full provenance, source-by-source licensing, rights, permissions | desktop + mobile |

Visible label for Function 3 is **"Exploration"**. "Exploration Field" is an
internal engineering codename only.

### Reachability rules

- **Object Page is never a direct Homepage action.** It is reached only *through*
  a function — Search results or Index directory results.
- **Context Canvas / Exploration are reached only via `/trace`**, never from the
  Homepage (Spacetime, deferred, is reached from nowhere: no dock control, no link).
- **Search is visually part of the Homepage** as a distinct expandable search
  window, but it owns its own route and real URL state (`q`, `yearFrom`, `yearTo`,
  `objectType`, `theme`, `movement`, `after`). It is not a URL-less modal.

### Index vs Search (not the same thing)

- **Index** = archive browsing / directory interface. Classification + chronology,
  not relevance. Flow: Homepage → Index → pick Region/Country · Year · Theme →
  directory results → objects sorted by year → object title → Object Page.
- **Search** = direct object finding interface. Query + hard conjunctive filters,
  deterministic relevance order.

### Index v1 controls (all on the Index page itself, no secondary menu)

- Filters: **Region/Country · Year · Theme**.
- Year ordering is **selectable**.
- **No Movement** in v1 (coverage ~1.4%, too weak).
- **Medium** stays a project concept but is **deferred** from v1 Index until
  classification quality and data source are verified.

### Open data dependencies (must close before those filters ship)

1. **Region/Country** needs a *verified structured* geography field. Today `place`
   is free text and the evidence contract forbids geocoding / geopolitical
   rewrite. Same "verify source" gate as Medium.
2. **Index backing API + year-sorted results** — legacy `/folders*` routes are
   excluded (this redesign replaces that browsing model, not revives it), and
   Search has no chronological order. Index needs its own confirmed data source.

---

## 4. Navigation system

- **Top-left:** wordmark "Modern Graphic Design Archive" (Baskervville), links to `/`.
- **Top-right:** icon-only controls, in order — **Index · TRACE · Search · About · Source**.
  - Each is a real link/button with an accessible name in markup.
  - On **hover _and keyboard focus_**, the target's name appears as large type in
    the otherwise-empty page space (not as a text label inside the nav bar).
    Hover is the enhancement; focus parity and the markup name are the baseline.
- **Mobile:** top bar is exactly **`MGDA · Index · Search · About`** — see §4a and
  §7d. **Search is a global utility** (§7d): its icon appears in every nav, mobile
  included, and opens the one shared Search window over the current page. No
  Source icon (Source folds into About), no TRACE.
  `SEARCH_CLIENT_BUNDLE_TRACE_IMPORT_COUNT` stays `0`.
- **Icon set** (lucide, strokeWidth ~2.75): Index = `TableOfContents` (a
  directory/contents mark, not a bookshelf), TRACE = `Waypoints`, Search =
  `Search`, About = `Info` (an "i"), Source = `Link2` (a chain link — Source
  points out to original sources).

---

## 4a. Mobile (ground-up redesign)

Mobile is **not a reflow of the desktop layout**, and not the same file behind a
breakpoint. It is a **separate code path** — its own `mobile/` component tree and
its own CSS, authored fresh. Mobile CSS predating the 2026-08-29 redesign is
removed, not adapted. Mobile scope is deliberately narrower than desktop — only
the reading-and-finding surfaces ship on phones.

### Device split (how the path is chosen)

`page.tsx` (a Server Component) decides **once, on the server**, from the request
`User-Agent` (coarse mobile match; tablet → desktop), then renders **either**
`desktop/` **or** `mobile/` — never both, never a client-side swap that could
mismatch hydration. A `?view=mobile` / `?view=desktop` query override is honoured
for QA and for a "switch to desktop site" link. The chosen path is the only code
and CSS sent to that device.

- Shared between the two paths: **only** `lib/` — data fetch, DTO types, and pure
  functions (`fitLayout`). No shared JSX, no shared `.module.css`.
- `SiteNav` renders per-variant (a `variant="mobile" | "desktop"` prop, or a
  `SiteNavMobile`), so the mobile bar is genuinely `MGDA · Index · Search · About`
  with no desktop nav code shipped.
- TRACE routes: the mobile path **is** the desktop-required fallback — the
  `desktop/` TRACE tree is never imported on the mobile path
  (`SEARCH_CLIENT_BUNDLE_TRACE_IMPORT_COUNT = 0`).

### Mobile surface map

```
Top bar:  MGDA · Index · Search · About
  MGDA → Homepage    Index → /directory    Search → global window (§7d)    About → /about

Homepage
  └─ (Search is reachable from the nav on every page, not owned by Homepage)

Search  (global utility, §7d)
  └─ query · filters · results             → Object Page

Index
  └─ filters / ordering                    → Object Page

Object Page
  └─ full mobile reading experience (the one content-dense screen)

About
  ├─ Overview / Project
  ├─ Methodology
  ├─ Claim boundaries
  ├─ Citation
  ├─ Design research
  ├─ Source            ← provenance · rights / licence · source register
  └─ Rights & permissions

TRACE  (+ Context Canvas · Exploration; Spacetime deferred, shown as a direction under review)
  └─ unavailable on mobile — address-disabled (see below)
```

### Navigation — re-expressed entries, not removed features

| Desktop nav | Mobile |
|---|---|
| Index | **Index** — kept |
| TRACE | **No entry** — route returns the fallback, never the desktop layout |
| Search | **Search** — kept (§7d): Search is a global utility openable from any page, so it earns a mobile nav slot too |
| About | **About** — kept |
| Source | **No entry** — Source becomes a section *inside* About |

`MGDA` is the home link. The wordmark may reduce to the monogram tile alone below
~400px.

### Source inside mobile About

Source is **not scattered** through About — it stays one addressable, linkable
block, so the provenance chain (*Original source ≠ Archive metadata ≠ Research
evidence ≠ TRACE interpretation*) is still legible on a phone. Mobile About
section order:

```
Overview · Methodology · Claim boundaries · Citation · Design research · Source · Rights & permissions
```

The mobile `Source` section carries the three things a reader needs —
**provenance**, **rights / licence**, **source register** (the per-source list,
collapsed by default). Hash-heavy reproducibility material stays on desktop
`/source`; mobile links out to it rather than inlining it.

### TRACE is address-disabled on mobile

TRACE and its three functions must **never** hand a phone the desktop layout or
runtime. On a mobile viewport / mobile server hint, `/trace*` returns the
lightweight **desktop-required** notice + a link back to Search **before** any
TRACE layout, component, or data module is imported. No compressed "TRACE lite".
The mobile bundle imports zero TRACE code
(`SEARCH_CLIENT_BUNDLE_TRACE_IMPORT_COUNT = 0`). This is product policy, and the
notice says so — it is not a responsive defect.

### Mobile Object Page

The only content-dense screen on mobile.

- **Single column, one measure.** The desktop content-fit column counts
  (`fitLayout.ts`) all collapse to 1. The five information layers keep their
  order: Visual record → Object identity → Catalogue metadata → Description →
  Source · Citation · Provenance.
- **Alt text stays fully visible** — it is the primary payload, never folded.
- **Non-essential blocks collapse by default** (`<details>`): object **Source**
  detail list, **Provenance** ("what MGDA did") list, and the raw citation
  string (the *Copy citation* button stays visible). Section headings stay
  visible; the reader opens what they need.
- **Back to top** — a persistent, mobile-only control; appears after the reader
  scrolls past the first screen, returns to the top of the record. Desktop has
  no such control.
- **Tighter vertical rhythm** than desktop — section gaps step down one unit.

### Mobile visual adjustments

Phones self-illuminate and run brighter than reflective paper, so on a mobile
viewport `globals.css` overrides tokens (no per-component colour forks):

- Ground lifts **toward white** (`--paper` ≈ `#fcfaf2`) — keeps the warm cast,
  drops the "dim" look at high screen brightness.
- Spot colours gain a little **purity / contrast** (blue, red, green-deep,
  teal-deep) so section coding and links survive aggressive display colour
  management on the lighter ground.
- Ink deepens marginally for text contrast.

### Breakpoints

| Band | Width | Behaviour |
|---|---|---|
| **Mobile** | ≤ 640px | surface map above; nav = `MGDA · Index · Search · About`; TRACE fallback; mobile token overrides; Object Page single-column + fold + back-to-top |
| **Tablet** | 641–1024px | desktop layout, full nav; TRACE runs its own capability check |
| **Desktop** | ≥ 1025px | full experience |

SiteNav hides the TRACE / Search / Source items at **≤ 640px**.

---

## 5. Visual system

### 5.1 Synthesis of the design inspirations

Three references were given. They are **synthesised into one original language**,
not imitated.

- **Alex Steinweiss** (invented the illustrated album cover, Columbia, 1939–40).
  What we take: *one clear idea per plate*; a **limited but saturated palette**
  (2–4 spot colours + black) with decisive figure–ground; expressive display
  lettering set against confident sans caps; a **single graphic motif** (arc /
  record-groove curve / bar) used rhythmically; the cover as an object that
  *announces its content*.
- **New York editorial illustration** (New Yorker / NYT idiom — the crowded
  subway, the "SPFing" street, the isometric city). What we take: **flat colour
  with a heavy confident black keyline around everything**; high-chroma primaries
  and secondaries sitting on the same plane; ordered density and visual wit;
  warmth; **no gradient, shadow, glass, or depth trick**.
- **Retro-but-fun colour** (same illustrations): vermilion, cobalt, sky blue,
  sun yellow, leaf green, occasional pink — near full saturation, always bounded
  by black line, on a warm ground. Retro comes from *flat spot-colour printing +
  ink line + bold type*, never from "cream paper + a serif".

**Derived language — "the inked catalogue".** The page reads as if printed in
four spot colours plus a black line block. Every structural edge is a **2–3px
black keyline** (dividers, block borders, table rules, link underlines) — this is
where the *weight* and archive gravity come from. Each of the six About sections
is a **plate**: it opens with a full-bleed block in its coding colour carrying an
oversized heading and numeral (the Steinweiss "cover"), then the body runs on the
cream ground with that colour as the working accent. One motif only: a **quarter
/ half-round arc**, used sparingly (plate corner, numeral disc).

**Explicitly not:** Bauhaus; Swiss/International reductionism as a whole identity;
Japanese minimalism; the prior civic-ephemera / railway-ticket system; progress-dot
rails, tab bars, or any layout lifted wholesale from a reference. No archive-object
imagery, no decorative placeholder imagery, no stock texture, no gradient/shadow.

### 5.2 Palette (tokens) — bright retro spot colour + black line

Retro ≠ yellowed. The ground is a light warm ivory, and the spot colours are
luminous (Steinweiss album covers, not aged paper).

| Token | Hex | Role |
|-------|-----|------|
| `--paper` | `#F8F5EC` | page ground — bright warm ivory |
| `--paper-2` | `#EFE9D9` | inset / second surface |
| `--ink` | `#181510` | **the black line** — keylines, rules, body text |
| `--ink-2` | `#4A4335` | secondary text on ivory |
| `--on-dark` | `#F8F3E6` | text reversed on any colour / ink plate |
| `--blue` | `#2743D6` | cobalt — §1 Purpose |
| `--red` | `#E8492B` | tomato — §2 Methodology |
| `--yellow` | `#F6C63C` | sun — §3 Visual rationale |
| `--green` | `#3DA35D` | kelly — §4 Scale |
| `--teal` | `#1F9B9B` | teal — §5 Contact & citation |
| `--ink` (plate) | `#181510` | black — §6 Boundaries & rights, and the footer |
| `--coral` `#F0876A` · `--sky` `#4FA8DE` · `--pink` `#EC7BAB` | | tertiary accents — figure tiles, keyword spans, card ticks |

Rules: each section **owns one colour** (coding system) and also wears it as a
full plate (expressive). Colour is also used *inside* sections — keyword spans in
prose, per-tile figures in the Scale grid, per-row contact labels, per-card
citation ticks — so the page is never two-tone. Colour is never the sole carrier
of meaning: label + position + the black keyline carry it too.

### 5.2a Section device (motif)

One geometric device per section, **varied, never the same ring repeated**: `1`
concentric grooves · `2` radiating arc fan · `3` chevron stack · `4` ascending
bars · `5` crosshatch + node · `6` half-disc. Inline SVG in `currentColor` at
~44% of the band foreground, bottom-right of each colour band, `aria-hidden`.

### 5.3 Typography — heavier, 18px floor

| Role | Family | Notes |
|------|--------|-------|
| Statement voice | **Baskervville** | masthead statement + pull-quotes + italic emphasis only — the neoclassical counterpoint to the pop colour; set **large** |
| Section headings & numerals | **LINE Seed JP 800 (ExtraBold)** | the heavy display face; big; `line-height ≥ 1.18` on any heading that can wrap |
| Kickers / labels / card titles | **LINE Seed JP 700** | uppercase, tracked — used **sparingly** (section kickers + a few sub-labels only) |
| Body | **Instrument Sans 500** (`strong` 700) | **minimum 18px**; reading size 19px |
| Data figures | **Inter** 200/300/400 | tabular; big decorative numerals kept light |

Scale (16px root): label `1.0625` (17px) · **body-sm `1.125` (18px — hard floor)** ·
body `1.1875` (19px) · body-lg `1.375` (22px) · h3 `1.5` · h2 `clamp(2.1, 4.2vw, 3.4)` ·
h1 `clamp(2.8, 5.4vw, 4.6)` · numeral `clamp(3.4, 10vw, 7.5)`. Reading measure ≈ 42rem.

### 5.4 Icons — larger, more air

**Lucide** (`lucide-react`), stroke **2.75–3**. Control box **≈ 60px** (≥ 50 %
larger than the first pass), icon glyph **≈ 32–34px**, gap between controls
**14–16px**. Icons sit inside black-keyline tiles.

### 5.5 Grid, rules, spacing — tighter, full-width

- Spacing scale (px): 4 · 8 · 12 · 16 · 24 · 32 · 44 · 64 · 88.
- Page gutter `clamp(20px, 4vw, 56px)`; max width `78rem`.
- **Section rhythm is tight:** plates butt against each other, separated by a
  single `3px solid var(--ink)` rule. Inter-section padding ≈ 44–56px, never the
  96–128px of the first pass. Reading flow must stay continuous.
- **Both columns work.** Layout is a narrow left rail (numeral + kicker +
  standfirst) beside a wide main column that itself splits into 2–3 columns for
  lists, reference cards, and data. The right side is never left empty.
- Radius 0 everywhere except 2px on interactive controls. Every block has a black
  keyline; no hairline greys.

### 5.6 Motion — GSAP, restrained

- `gsap` + `gsap/ScrollTrigger` via `@gsap/react` `useGSAP`.
- **Transform-only** reveals (content never hidden by opacity): section blocks
  settle up ~16px on enter (`power2.out`, ~0.7s, `once`); a slightly larger arc /
  numeral drift is allowed (≤ 20px). Masthead settles on load.
- Forbidden: scroll-jacking, pinning, horizontal scroll, elastic easing, long
  staggers, moving controls, opacity that can strand text.
- `prefers-reduced-motion: reduce` → no tweens at all.

---

## 6. Engineering conventions

- **One route = its own `page.tsx`**, and **one component = its own file** with a
  **matching `*.module.css` beside it**. No monolith: a page is composed from many
  small component files (`ComponentName.tsx` + `ComponentName.module.css`), not one
  large `PageView.tsx`. Route folder layout:

  ```
  <route>/
    page.tsx                 route entry — device split + data, no layout
    lib/                     shared, non-visual: data fetch, types, pure utils
    desktop/                 desktop-only tree — components + their .module.css
    mobile/                  mobile-only tree  — components + their .module.css
  ```

- **Desktop and mobile are separate code paths, not one file behind a media
  query.** `page.tsx` chooses `desktop/` or `mobile/` up front (see §4a); the two
  trees **share no JSX and no CSS** — only `lib/` (data, types, pure functions
  like `fitLayout`). This is deliberate: a mobile change can never regress
  desktop, and each tree stays small and readable. Media queries inside a tree are
  still fine for fluid range within *that* platform; they are not the
  platform switch.
- **CSS is isolated from TSX.** Styling lives in **CSS Modules** (`*.module.css`)
  or the global token sheet — never inline style objects as a system, never
  styled-jsx, never a `<style>` block for layout. Runtime animation (GSAP setting
  transforms) is not "CSS in TSX" and is allowed.
- **Global sheet** `src/app/globals.css` = reset + design tokens + base element
  typography + font wiring only. No component styling.
- Fonts via `next/font/google` (Instrument Sans, Baskervville, Inter) exposed as
  CSS variables in `layout.tsx`; LINE Seed JP via `@fontsource/line-seed-jp` import.
- Shared chrome (`SiteNav`) lives in `src/components/site/` with its own module CSS.
- Do not import TRACE runtime into the Search/Homepage bundle.
- Never render an `<img>` / background-image bound to archive-object metadata.
- The legacy ephemera CSS system and `ArchiveShell` are retired; legacy routes
  (`/cards`, `/folders`, `/badges`, sheet studies, …) are out of scope and will be
  removed or redesigned in later rounds.

---

## 7. About page — content architecture (section order fixed by owner)

Grounded in repository fact; IA and public copy improved for a general reader.
**No release IDs, database versions, hashes, API wording, or build/deploy status
on the public page** — that is backend detail, not reader content. Detailed
source-by-source licensing/provenance belongs on **Source**. Six plates after the
masthead:

0. **Masthead** — MGDA monogram + wordmark, icon nav. Opening *states the
   contribution*: "A verifiable record of modern graphic design history, built in
   the open." Lead gives the funnel in plain words (gathered from 100+ sources →
   cleaned/classified/researched → ~16,000 catalogued, 7,995 public). Meta line:
   "In development since 2024 · 44 capture batches · 100+ sources · text and
   citation, no assumed imagery".
1. **Purpose** (cobalt) — read, locate, explore; verified + extensible in plain
   terms; audiences (design researchers · learners & educators · AI/agent tools).
2. **Methodology** (tomato) — "gathering is not publishing"; the pipeline (source
   registry → capture batch → candidate pool → review gates → published record);
   evidence protocol (Evidence / Description / Interpretation / Uncertainty);
   coverage weighted against imbalance; no-inferred-influence; design-research note.
3. **Visual design rationale** (sun-yellow) — heading **"Built like a printed
   catalogue."** (clear, not the cryptic "inked catalogue"). The §5.1 synthesis
   in plain voice with **coloured keyword spans** (Alex Steinweiss / New York
   editorial illustration / spot-colour printing); reference cards; type system.
4. **Scale** (kelly-green) — heading "A large raw pool, cleaned to a verified
   core." A short funnel paragraph + a **colour-coded figure grid**: since 2024 ·
   44 capture batches · 100+ sources · 15,923 catalogued · 7,995 public · 7,928
   held · 1800s–2020s span · 90 object types. Plus the "coverage is deliberately
   uneven" note. **No engineering internals.**
5. **Contact & citation** (teal) — contact (Dai Pan / 潘岱, Brisbane;
   dpan53853@gmail.com + jarl555@qq.com; daipan.art; repository — no Instagram),
   each row colour-tagged; copy-paste citation in **APA · MLA · Chicago · Harvard**,
   per-card colour tick, access date resolved client-side; cite-the-source-first
   note.
6. **Claim boundaries & rights** (black plate, last; footer shares this colour) —
   six boundaries as **native `<details>` accordions, collapsed by default**:
   summary shows the "Supports —" line, expanding reveals "Does not claim —".
   Covers historical relations (0 typed; 21 generic non-directional), inference,
   completeness, visual rights (0 records), TRACE evidence (Open Inquiry = 11
   unresolved, no pair edges), System Suggestions (DeepSeek V4 Flash named **here
   only**). Then a concise rights statement + link to **Source**.

---

## 3b. Reader eligibility — records versus reader-facing objects (2026-09-03)

Every public record is a legal, citable, reproducible archive record. Not every
public record is a reader-facing **object**: 2,572 of the 7,995 carry no
human-readable title — their title is the source's own identifier (the V&A
"O#######" system number, "AIC-192518") or a bare number — and opening one
tells a reader only that the source holds such a record. That is provenance
value, not browsing value. The relation is fixed as:

```
CANONICAL ARCHIVE — 15,923 canonical records
  ├── HELD — 7,928
  └── PUBLIC RECORDS — 7,995
        ├── RECORD-ONLY — 2,572 · direct URL / source / citation / provenance · not in the Index
        └── READER-FACING OBJECTS — 5,423 · Index-eligible → Index → Object page
```

**The decision is a governed projection, not a UI rule.**
`frontend/scripts/generate-reader-eligibility.mjs` reads the sealed canonical
payload and the Search v2 projection and writes
`frontend/generated/reader-eligibility-v49/` (`eligibility.json`, `manifest.json`,
`CHECKSUMS.sha256`; `npm run verify:reader-eligibility`). Each public record
carries `reader_eligibility = INDEX_ELIGIBLE | RECORD_ONLY` and a reason. The
floor for `INDEX_ELIGIBLE`: public (the Search v2 projection), source-verified
(inherited: `trace.tier === source_verified`), and a human-readable title by
**provenance** rules — `TITLE_IS_SOURCE_IDENTIFIER` (the title equals one of the
record's own source identifiers, or the system number in its source URL, and
carries at most four letters), `TITLE_NUMERIC_ONLY` (no letters at all),
`TITLE_EMPTY`. No rule judges the text's "meaningfulness"; short real titles
(PKZ, Mir, A-Z) stay eligible. The server loader
(`features/reader-eligibility/index.server.ts`) verifies release id, canonical
input hash, Search index hash, counts and checksum, and fails closed (an
unlisted ID is record-only).

**Product rules**

| Surface | Population |
|---|---|
| BROWSE — Index | reader-facing objects only (5,423) |
| NORMAL SEARCH | reader-facing objects primarily *(rule fixed; Search UI wiring pending — the Search page is still fixture-backed)* |
| EXACT RECORD LOOKUP — a stable ID or a source identifier typed in full | may return record-only entries, labelled "Record-only archive entry" |
| DIRECT URL — `/surfaces/{id}` | every public record stays reachable |

**Two object-page presentations.** A reader-facing object renders the full
Object page (visual record, identity, catalogue metadata, description, source,
citation, provenance). A record-only entry renders as an **Archive record**:
eyebrow "Archive record", a plain notice — *retained for catalogue and
provenance purposes; no reader-facing visual or descriptive object content is
currently available; not listed in the Index* — then identity, catalogue
metadata, source, citation and provenance. No empty "Visual record" section
stands in for content.

## 3c. Visual availability — a fourth status, and a census (2026-09-03)

Four statuses are frozen and never collapsed into one another:

```
PUBLIC STATUS     public / held
READING STATUS    reader-facing / record-only            (§3b)
VISUAL STATUS     displayable / remote candidate / source-viewer-only / link only / citation only / no route
EVIDENCE STATUS   source verified / …
```

Index eligibility is "meaningful object identity + sufficient reader-facing
content"; visual availability is its own dimension and never an eligibility
criterion (a Gallica poster with a full title and a source viewer is
reader-facing; a V&A record titled by its system number is record-only
whatever its image state).

The **Visual Availability Census** (`docs/frontend/VISUAL_AVAILABILITY_CENSUS_v1.md`;
artifacts in `frontend/generated/visual-availability-v49/`) answers, with
evidence, how many public records could be remote-rendered: **0** are
displayable (the v49 visual registry is empty); **128** are verified
remote-visual candidates (V&A 82 with item rights unreviewed, Nasjonalmuseet
40 and Commons 6 passing every recorded gate pending the registry); 27
candidates fail at the endpoint (AIC 25 × 403, one 429, one 404); 7,763 are
viewable at source; 77 have citation or link only. The legacy IMG03 pool
intersects the public projection in only 73 records, all inside the 128 + 27.
`MGDA_DISPLAYABLE_VISUAL` is reserved for the visual registry's decision; the
frontend never promotes an image state on its own.

**Index filter (interim, shipped):** "Visual access — All · Viewable at
source · Remote visual candidate · Citation / link only", mapped to the
delivery state; not final copy. **Final (after the registry):** "Visual — All
objects · Visual available · Source view only", where "Visual available"
strictly equals `MGDA_DISPLAYABLE_VISUAL`. Never "Has image".

## 3d. Object page — three visual modes, and the order of work (2026-09-03)

Fixed with the owner, in this order:

1. **Source-viewer URL first.** `frontend/generated/source-viewer-v49/` projects
   every public record's source record URL (7,995 of 7,995, all https, all with
   the pipeline's source-URL review flag), plus the captured source document URL
   (4,501) and the capture date, from the sealed canonical payload
   (`npm run generate:source-viewer` / `verify:source-viewer`; loader
   `features/source-viewer/index.server.ts`). Object pages read it: the Source
   block links the original record, and the visual layer offers one clear
   **View at source ↗** action. No Object page is "dead".
2. **The visual registry, promoted separately.** `frontend/generated/visual-registry-v49/`
   is the only source of `MGDA_DISPLAYABLE_VISUAL` (loader
   `features/visual-registry/index.server.ts`, fail-closed; zero entries in
   v49). `REMOTE_IMAGE` is never a display permission. Batch 1's review sheet
   (`promotion-candidates-batch-1.json`, `npm run export:visual-promotion-candidates`)
   holds the 46 verified, rights-reviewed candidates — Nasjonalmuseet 40,
   Commons 6 — with their evidence; V&A waits on item-level rights, AIC on the
   endpoint and terms. A record listed in the registry switches its Object
   page to the image-present layout automatically.
3. **The interim Index filter stays** ("Visual access", §3c). "Visual
   available" is added only when the registry has entries, mapped strictly to
   `MGDA_DISPLAYABLE_VISUAL`.
4. **Three visual modes on the Object page** (`VisualRecord`, `MobileVisual`):

```
A  DISPLAYABLE        image rendered in MGDA from the registry URL
                      + attribution + licence + original source
B  SOURCE-VIEWER-ONLY no fake image box; one sentence; "View at source ↗"
                      (link / citation variants: "Open the source record", or none)
C  RECORD-ONLY        compact provenance record; no visual layer; not in the Index
```

**Count scope.** Counts shown in the Index — "5,423 reader-facing objects",
the filter's "5,203 / 143 / 77" — are bound to the `INDEX_ELIGIBLE` projection.
The census's "7,763 / 155 / 50 / 27" are the public population. The two are
never shown together as if they were one series.

## 7a. Source page — content architecture

An **academic reference appendix**, not a second About. No project vision,
audiences, Search/TRACE explainer, full claim-boundaries, AI method, design
essay, or the four citation formats — those stay on About, reached by a link.
Visual register (second cut, 2026-09-03 — the owner found the first "too
thin, not bold, not round enough", and asked for more colour after three
stamps: SOZPHILEX 77, EFTA 50 years, HKSAR 25): set like a sheet of stamps.
Each section opens on a **solid colour plate** carrying its numeral oversized
and cropped by the plate's edge, its title in the heavy rounded face (LINE Seed
800 — no new faces), and one small line-drawn mark of its own; the masthead has
the page's name set too large for a yellow plate and cropped by it. Below the
plate the column is paper and ink, with the section's colour returned as solid
pills, discs and tinted cards; every label on the 17px floor; nothing lighter
than 500. No scroll motion — the marks change from section to section. No
tinted boxes: the pull-statements and citation blocks are built like the plates
(a solid stub carrying one cropped glyph, an ink-outlined body), the rights
columns are a colour head over a paper body. **The page must fold by
default** — the register's entry cards, the acquisition methods, the
transformation categories and the integrity record are `<details>` collapsed.
So that the unfolded page still reads on its own, every section opens with an
explanatory paragraph (Rights, Evidence status and Version gained theirs in the
second cut; the copy restates the section's own data and makes no new claim).

**Contrast rule (2026-09-03, Source and About alike):** the owner found the
plates' contrast inconsistent and the whole too hard. One rule now: every plate
is its token softened by 8% paper; what sits on a plate is paper on the deep
plates and ink on the light ones (yellow, coral, sky); the numeral and the
stub's glyph are that same colour at 90% — never a second hue; every outline is
one weight (1.5px) of one softened ink (62%). **About's rationale** is now
Columbia-centred: six references — Steinweiss, Fujita and Flora at Columbia
Records 1940–1960, the postage stamp, the pictogram systems, the engraver's line
— mirrored in the Source register's Design References group.

0. Masthead — kicker "Source"; the exact framing sentence; the lead is the
   overview statement.
1. **Source overview** — the four layers kept distinct: *Original source ≠ Archive
   metadata ≠ Research evidence ≠ TRACE interpretation*, with a note that a
   source's presence never implies a validated claim.
2. **Source register** (core) — filter chips (All / Archives & Collections /
   Scholarly Research / Datasets & Standards / Design References) + four groups,
   each with a count and a **collapsed** "Show N sources" toggle (auto-opens when
   its filter is active). Every entry carries **source type** and **project
   role(s)** as separate colour-coded tags, plus a field grid (Coverage ·
   Material · Contribution · Identifier · Acquired · Rights · Status). Grounded in
   the project's own ~21 institutional sources + Commons/aggregator datasets +
   governed projections + controlled vocabularies + design references.
3. **Provenance & acquisition** — the chain (Source → Acquisition → Raw
   source-level record → Normalization → Review → Public archive record); the 7
   acquisition methods **collapsed**; notes on frozen snapshots / no auto re-sync
   / role tagging.
4. **Editorial & data transformation** — "Transformation is not inference"
   callout visible; the 8 transformation categories **collapsed**.
5. **Rights & permissions** — the global **Visual material** statement as a
   callout, then three columns: Metadata · Text & citation · Visual material.
6. **Evidence & source status** — the five-status legend (Verified source /
   Public record / Held / Open inquiry evidence / Reference only) + the
   "existence ≠ validation" note.
7. **Version & reproducibility** — a short version ledger; the hash-heavy
   **integrity record collapsed** (`<details>`). This *is* the place for release
   IDs, anchors, and checksums (unlike About).
8. **Source citation** — cite the original source first (stable identifier: DOI /
   ISBN / catalogue ID), then the archive provenance record; link to About for
   how to cite the archive itself.

---

## 7b. Object page — content architecture

A **visual research record**, not a portfolio detail and not a raw DB dump.
Reached **only** from Index or Search; it never links into TRACE (Context Canvas /
Spacetime / Exploration). Text, tables and records are primary; any image is for
identification only and may never exceed ~20% of the page — there is no hero-image
possibility. Five fixed information layers, always in this order: **1 Visual
record · 2 Object identity · 3 Catalogue metadata · 4 Description · 5 Source ·
Citation · Provenance**. Missing metadata → "Not recorded" or the row is omitted;
never "Unknown / Probably / N/A". Object **Source** (where the record came from) is
kept distinct from MGDA **Provenance** (what MGDA did with it); "Cite this object"
is distinct from About's "Cite this project".

- **Visual record is an information block**, not a picture: a small ratio marker
  (CSS only, no bound `<img>`) beside a definition list led by **Alt text**
  (built from catalogue fields, for readers and machines), then Delivery state,
  Ratio, and an **At source** link to the real backend-provided destination.
- **Identity mark**, not a message card: a small CSS "ticket stub" in the
  breadcrumb row's right blank space — a `repeating-linear-gradient` barcode +
  the record number (tabular) + a stamped year. No SVG. Testing-only layout
  switcher is gated behind `?explore`; it does not exist in the live page.
- **Colour** codes the layers with higher-purity accents so they read on the
  cream ground: `--l-ident` vivid blue, `--l-meta` vivid green, `--l-desc`
  amber, `--l-src` vivid teal.
- **Hierarchy by spacing**: a clear gap under the title block (`--s-7`), `--s-7`
  between sections, tight spacing within them. Desktop-tuned to read calm, not
  loose; mobile steps every gap down one unit.

### Content-fit columns (`fitLayout.ts`)

Column counts follow the **record's content volume**, not the chosen layout — a
sparse record is not stretched across four thin columns, a dense one is not
crammed into one. Pure function of the DTO; the same record always resolves the
same way; no DOM measurement, no viewport dependence beyond the plain responsive
breakpoints.

| Block | Signal | Mapping |
|---|---|---|
| Identity metadata grid | count of **populated** identity fields | ≥ 9 → 4 · ≥ 5 → 3 · else 2 (first column always wider; identity currently caps at 6 fields, so 3 or 2 in practice) |
| Description prose | trimmed **character length** | ≥ 900 → 4 · ≥ 480 → 3 · ≥ 240 → 2 · else 1 (single 44rem measure) |
| Source · Citation · Provenance foot | fixed 3 blocks | asymmetric `0.85fr 1.3fr 0.85fr` (citation gets the room); 1 column < 900px |

Thresholds keep every column at ≳ 6 lines within the 66rem frame, so no column
degrades toward one word per line. `density` (`compact / regular / dense`) is
exported for section-spacing use.

### Layout exploration (five treatments, one 66rem frame)

1. Catalogue entry — labelled sections, metadata as a wide-first grid.
2. Tabular — identity + classification as a two-column ledger.
3. Ledger (whole record) — every field as `label | value` rows; citation-only foot.
4. Reading-led — description first, then metadata, then source.
5. Editorial spread — full-width headline, dark Source/Citation/Provenance band.

The `?explore` layout switcher is a **test harness only** — it renders solely with
that URL param and is not part of the live page.

### Mobile Object Page

Single column (all `fitLayout.ts` counts collapse to 1); layer order unchanged;
alt text never folds; object **Source** and **Provenance** detail lists + the raw
citation string collapse by default (`<details>`, *Copy citation* stays visible);
a mobile-only **back-to-top** control appears after the first screen; section
rhythm one unit tighter. Full mobile spec in §4a.

Title must set in **≈ 2 lines** at desktop width — the measure cap is a
readability guide (`text-wrap: balance`, ~36ch / ~32ch on L5), never so tight it
forces a third line.

---

## 7c. Index page — content architecture

Route `/directory` (the App Router reserves the folder name `index`; the visible
label stays **"Index"**). Index and Search both help a reader *find an object* and
share the token system, but they are **not merged**: Index = **browse / scan /
compare** (a filterable directory), Search = **query / narrow / locate**. This
round builds Index only.

**Fixed flow — everything on one page, no secondary menu:**

```
Index → Region/Country + Year + Theme → filtered directory → year order → object title → Object Page
```

**Visual system — a filing index (British catalogue / Japanese timetable).** The
archived folder-file system is **retired**; only its *ideas* carry over — colour
as classification, dot marks, filing codes — re-expressed in the redesign's own
retro spot palette (`globals.css`), **not** the folder inks.

- **Masthead** — an open hero: large `Index`, a Baskervville lede, a short usage
  paragraph, then a **three-band spot rule** (`--blue` / `--red` / `--yellow`,
  Steinweiss triad) — an accent, not a legend.
- **Theme** is the one classifier that carries colour: each of the 8 themes maps
  to a token. On **desktop** up to **three theme dots** end each directory row
  (a `dotted leader` runs to them — timetable / table of contents), and the
  **hero's right column holds a Theme key** (swatch + name for all 8, "hover a
  dot for its name"). On **mobile** there are **no dots and no filing numbers** —
  themes read as plain text in the record line instead (ref: Vrints-Kolsteren,
  The Window Effect), since a bare colour mark isn't self-explanatory on a phone.
- Zero-padded filing codes (`001`, `049`) and tabular numerals throughout —
  catalogue back-matter, not a SaaS list.
- The active-slice line colours its Region (`--blue`) and Theme (`--green-deep`)
  segments; the filter Region/Theme sections take a matching underline.

**List first.** The reader lands on the directory. Filtering is a deliberate
second act behind a **Filter** control: a right **drawer** on desktop, a bottom
**sheet** on mobile, both over a scrim with the list still visible; ESC / scrim /
✕ / "Show NNN objects" closes.

**IA (in order):** 01 page identity · 02 filter controls · 03 active state /
result summary · 04 object directory · 05 ordering · 06 empty / loading / error.

- **01 Identity** — the open hero: `Index`, a lede, a one-paragraph "how to use"
  (`N public records · open the filter · list holds year order · select a
  title`), then the three-band spot rule. Gives the top room; the page is
  otherwise loose below.
- **02 Filters** (in the drawer / sheet) — **Region/Country · Year · Theme** only
  (Movement excluded — ~1.4% coverage; Medium is shown as a dot + in the row
  sub-line but is **not** a v1 filter, pending classification + source checks).
  - *Region* — desktop: searchable list; mobile: native `<select>`. Single-
    select, "All regions" clears.
  - *Year* keeps **filtering and ordering strictly separate** — a `from–to`
    range with **era presets** (Before 1945 / 1945–1979 / 1980–present) and
    decade chips for filtering; a two-button `Oldest / Newest first` for order.
  - *Theme* — small governed set as **toggle badges** (multi-select; "All"
    clears).
  The desktop **drawer** is hairline-separated full-width sections (never reads
  empty), `~19px` control type, a "`N` of `49` records match" line under the
  title; era presets a 3-col grid, decades a 5×2 grid. The mobile **sheet** is
  the accordion.
- **03 Active state** — one editorial line in the sticky control bar:
  `REGION · YEARS · THEMES` + zero-padded `NNN objects` + `Reset` (hidden when
  pristine). The **Filter** button carries an active-filter count.
- **04 Directory** — a **filing index, not search cards**: running filing number,
  year + per-group count hung once, `Object title` — dotted leader — theme dots
  on line 1, `Designer · Place · Type · Medium` on line 2. Title is the only
  click target → Object Page.
- **05 Ordering** — year order (oldest / newest); reorders the year groups.
- **06 States** — loading (skeleton + `aria-busy`), empty ("No objects match…" +
  widen/drop hint + Reset), error (alert + Retry). `?state=loading|error`
  previews them.

**Mobile Index** (390px baseline) — small masthead (title + lede + count +
stripe) · **one** sticky control row (Filter · slice · count · reset) · then the
list. Same hierarchy as desktop, fewer marks: big year band with a 3px rule →
title (restrained weight, a `↗` link cue, no dots, no number) → one plain record
line (`themes · designer · place · type`). The filter sheet is an **accordion** —
every section collapsed on open (so the sheet is short), each header showing its
current value; one expands at a time.

**Files** — `directory/` follows the §6 template: `page.tsx` (server UA split) +
`lib/` (`fixture` directory, `filter` pure logic, `palette` theme inks +
`themeDots`) + `desktop/` (IndexDesktop · IndexControlBar · IndexFilterDrawer ·
IndexDirectory) + `mobile/` (IndexMobile · IndexMobileFilters[accordion sheet] ·
IndexMobileDirectory), each with its own `.module.css`. Fixture-backed; the live
Index API and **verified structured geography** (§3) are not built.

---

## 7d. Search — a global utility window

**Search is not part of Homepage.** It is a **global utility layer**: one Search
window, invoked from the `Search` icon in *every* nav (desktop and mobile), opened
over whatever page the reader is on. Desktop and mobile reuse the same window;
only its size and layout are responsive.

Search does **one** thing: quickly find a **public archive object**. It is **not**
an Index replacement — Index is browse / scan / compare; Search is query / narrow
/ locate. It and Index **do not share design logic or style** (see the two
treatments below), only the token system.

### URL-backed state (not a local modal)

Even as a window, Search state lives in the URL — the canonical Search state from
§2 / the product contract:

```
/search?q=bauhaus&yearFrom=&yearTo=&objectType=&theme=&movement=&after=
```

`/search` is a real route with a **server device split** (§4a) → `desktop/` or
`mobile/` tree. The nav icon links to it from any page; **Close** is
`history.back()`. So:

```
Any page → open Search → query / filters (URL updates)
         → Object Page → Back → the exact previous Search state
```

### Structure

```
01 Search header   — search input · Close
02 Filters         — Year / year range · Object type · Theme · Movement
03 Query state     — active query · active filters · result count · Clear / Reset
04 Results         — Search Result × N
05 Pagination       — cursor, 25 per page in the UI
06 System suggests  — see below
```

Filters differ from Index: **Year · Object type · Theme · Movement** (no Region;
Movement *is* offered here — the shown vocabulary stays visibly sparse). Each
result row is fields only — stable ID, title (the click target → Object Page,
set larger than the supporting text), credited label, display date + numeric
year, place, object type, theme[], movement[]. **No image, no thumbnail slot.**
Missing = omitted or "Not recorded". The match signal is compressed to **two
states** — **`Perfect match`** (direct field hit: exact / all terms / title +
year / movement) in teal, **`Partial match`** (fuzzy or associative) in muted
grey — small, right-aligned on the title line; the underlying six-way `reason`
is kept internally, only the *display* is graded.

The panel stays **short and predictable** (~600px, any viewport): filters are
**collapsed by default**, the results region shows **about three rows** then
scrolls (`max-height`), System suggests is a light strip below it.

### System suggests (in Search)

A **contextual research annotation, not an AI feature** — not a chat box, not an
assistant that occupies the page. A **very light hint layer**: the label
**"System suggests"**, then **one or two short sentences**, each on its own
line, describing the current result set — third-person, no "I", no "I
recommend", never a paragraph:

> System suggests
> The current results span several decades.
> Narrowing the year range may make them easier to scan.
> `[1950–1970]`  `[Theme: Typography]`

— followed by a few **terse inline tokens** styled as quiet text links, **never**
boxed option buttons. It **fades in** and is **completely absent by default**,
appearing only when the result set carries enough context *and* a legitimate
deterministic suggestion exists (no reserved empty slot). Generated by the
guidance provider (DeepSeek); **no provider name, "AI", or model name anywhere in
the Search UI** (that lives only in About / Methodology). It may **not** change
ranking, run a filter, add a result, auto-edit the query, or produce an object —
a token changes Search state **only** on an explicit click. Any guidance failure
degrades to the static equivalent or to absence; deterministic results are never
altered or delayed.

*The wording, tone and per-surface examples for Context / Spacetime / Exploration
are settled in the design rounds; the DeepSeek provider config, thinking mode,
response parsing, schema alignment, fallback triggering, prompt wording and
output length are then tuned in a separate narrow engineering round — UI and
target language first, provider second.*

### Two treatments (deliberately different from Index; refs: legacy card / slip,
the ticket-stamp poster, the museum catalogue card)

Both are a restrained slip, `SEARCH ;` in teal monospace, no title bar, only a
faint soft shadow — **never taller than the viewport**: the input · filters ·
query-state stay put, the **results list scrolls inside**.

- **Desktop** — a **clean keyline card**, ~32rem, **anchored top-right** over a
  dimmed scrim (scrim or ✕ closes), **draggable** by the stub (grip mark;
  `cursor: grab` / `grabbing`), clamped in-viewport. **No decorative edge
  treatment.** Filters are **collapsible** (a `Filters` toggle with an
  active-count badge) — a **2-abreast, 3-row grid** when open (`From | To` ·
  `Object type | Theme` · `Movement`), each cell a labelled field with a **custom
  chevron kept clear of the box edge**. Collapsing them frees the height for
  results. System suggests, when present, sits in a light slot below the
  scrolling results. Match chips are plain teal text, right-aligned on the title
  line.
- **Mobile** — the **ticket** (perforated edge, `QUERY ;` / `FILTERS ;`),
  ~350px, **absolutely centred**, its own layout (not a shrink). Filters
  **collapsed by default** on the height-constrained ticket (the list comes
  first). Match chips are **one word** — `Exact · Year · Movement · Matched ·
  Related · Close` — right-aligned on the title line, never on their own row.
  System suggests renders the same light annotation.
- **Colour** — one calm spot (`--teal-deep`), never red: red on a *find* utility
  reads as an alarm.

### Files

`search/` follows the §6 template: `page.tsx` (server UA split) + `lib/`
(`fixture` searchable objects, `query` pure parse + match + paginate, `suggest`
static fallback suggestions) + `desktop/` (SearchDesktop · SearchInput ·
SearchFilters · SearchResults · SystemSuggests) + `mobile/` (SearchMobile +
its parts), each with its own `.module.css`. Fixture-backed; the live
`search.public-objects.v1` / `guidance.system-suggestions.v1` APIs are not wired.

---

## 7e. Homepage — content architecture

The Homepage answers three reader questions, in this order: **what is this · why
is it worth reading · where do I go in.** It is a **reading page**, not a
landing page — no hero product pitch, no feature grid, no marketing CTA. Four
sections, fixed order: **01 Identity** (canonical one-liner, §2a) · **02
Contribution** (dated ledger + methodology/source-coverage narrative) · **03
Enter the Archive** (three entries: Index / Search / TRACE) · **04 Research
status** (one boundary note). Copy for all four lives in `home/lib/content.ts`
and is final.

**Full visual/motion/colour design has moved to a dedicated document:**
[`HOMEPAGE_DESIGN_v1.md`](HOMEPAGE_DESIGN_v1.md) — the pinned left-nav /
right-pane split-screen, the Identity text-mining scroll interaction, the
Contribution nested-scroll growth + decade histogram + Three.js isometric
scene, and the colour system. The single-band linear-scroll treatment
described in earlier drafts of this section is **superseded**; do not
implement from memory of it.

Desktop only, this round — mobile stays on the existing `HomeMobile` build
(full-bleed blue band, static stack) until the desktop redesign is finished
and mobile is re-derived from it separately.

### Files

`app/page.tsx` follows the §6 template: server UA split →
`home/desktop/HomeDesktop.tsx` (+ a `three/` module for the Contribution
scene) or `home/mobile/HomeMobile.tsx`, both reading from `home/lib/`. No API
calls.

---

## 7f. TRACE landing — the entry to three research views (2026-09-03 → 2026-09-04, settled after fourteen owner reviews)

This is the maintenance record for `/trace`. Anyone changing the page should be able to
find here what each part is, why it is so, which numbers hold it together, and which
practices the owner has rejected.

### Route, scope, boundary

- `/trace` (`frontend/src/app/trace/page.tsx`) is the shared entry to the three functions,
  not a fourth surface. The former Exploration reference page moved to
  `/trace/exploration`; Context Canvas and Spacetime keep `/trace/context-canvas` and
  `/trace/spacetime`.
- Desktop only by policy (§4): the server checks the mobile hint
  (`isLikelyMobileTraceRequest`) and returns `TraceDesktopRequired` before any research
  runtime is imported.
- The page answers four things only — what TRACE is, what each view is for, how the three
  relate, how a computed result may and may not be read — and carries nothing else: no
  recents, trending, recommendations, AI-generated questions, marketing call to action, or
  "System suggests". Nothing on the landing computes, ranks or suggests.
- Baseline figures are read at build time from the governed manifests
  (`generated/trace-context-v1`, `trace-spacetime-v1`, `trace-exploration-v1`,
  `trace-open-inquiry-v1`), never typed in: 7,995 public objects · 23 periods · 93 governed
  geographies · 21 evidence-qualified associations · 11 open inquiries · years 1800–2026.

### The concept, in the owner's words

TRACE explores the design history no single record can show on its own — the traces left
between records: the context an object sits in; the gathering and absence of records in
time and space; the associations observable between concepts under evidence; the questions
the material still cannot answer. The three views ask three levels of question — Context
Canvas, *Where does this object sit?*; Spacetime, *Where and when do records gather?*;
Exploration, *What becomes worth questioning when records are considered together?* — and
never *what history means*. The foot states it: "TRACE is an evidence-bounded environment
for reading history between records…", and the closing block opens on "TRACE the design
history no single record can show on its own." — TRACE set as the title word and read as
the verb.

### Files

| File | Holds |
|---|---|
| `trace/page.tsx` | server route: mobile guard, baseline from the manifests, `<TraceDesktop>` |
| `trace/lib/content.ts` | every string: title, line, lead, `WAYS` (name · href · question · brief · boundary · does), `BETWEEN`, `PRINCIPLES`, `BASELINE_NOTE`, `TRACE_DEFINITION`, `CLOSING_WORD` + `CLOSING`, `CAPTIONS` (screen · at · x · y · text · align · kind · width) |
| `trace/desktop/TraceDesktop.tsx` | the client stage: `SCRIPT`, the scroll handler (`apply`), the text layer, the dock, the leader lines, the closing block, the dev freeze hook |
| `trace/desktop/TraceDesktop.module.css` | the register and every text region (`[data-screen]`) |
| `trace/desktop/instruments.ts` | the scene: the bus, the budgets, `boxesFor`, the five screens, the blend, the HUD, the wires, the reactive components |
| `trace/desktop/Instrument.tsx` | one canvas running one program at ~30 fps while visible |
| `trace/desktop/world-outline.ts` | generated: the governed coastlines and the mapped geographies' marks |
| `trace/desktop/icons.tsx` | the three glyphs |
| `trace/exploration/page.tsx` | Function 3's reference page at its own route |

### The flow: five screens, one scene

The scene is one pinned sheet — `.sceneWrap` is 800vh so every screen can be read; `.scene`
is sticky under the nav — with two canvases (the set behind the text; the field's outer
rings in front, over the text), one clock and one scroll state. `SCRIPT` maps the scene's
scroll `sp` (0 as it pins, 1 as it releases) to the system's state `s` (0..4, fractional
between screens):

| scroll | state | |
|---|---|---|
| 0 – 0.10 | 0 | **TRACE** holds |
| 0.10 – 0.18 | 0 → 1 | transformation |
| 0.18 – 0.32 | 1 | **Context Canvas** holds |
| 0.32 – 0.40 | 1 → 2 | transformation |
| 0.40 – 0.54 | 2 | **Spacetime** holds |
| 0.54 – 0.60 | 2 → 3 | transformation |
| 0.60 – 0.76 | 3 | **Between records** holds (`PATTERN_HOLD`, shared with the scene) |
| 0.76 – 0.82 | 3 → 4 | transformation |
| 0.82 – 1 | 4 | **Exploration** holds |

Between screens the whole set TRANSFORMS: every screen is a `Frame` built on the same fixed
budgets — N = 1,400 particles, M = 96 polylines of V = 48 vertices, padded with parked
points and lines — and `blend()` moves every particle and every vertex index by index
(`smooth()` easing; anchors switch at the half). Each screen has its own layout
(`boxesFor(k)`: `main`, `left`, `right`, `strip` as fractions of the sheet), so the
composition moves, not only the figures. Drawn flat, depth implied by dot size, ring
foreshortening and particle density — **no perspective camera**.

### The components — each exactly once (4 + 3 + 3 + 3, plus reactive ones)

Boxes are (x, y, w, h) as fractions of the sheet.

- **0 TRACE.** The SPHERE (main 0.56, 0.20, 0.41 × 0.50): 36 meridians × 25 points, coral
  to paper to mint down its height, the column at the bus's period lit; a crown mark is the
  cursor. The FUNNEL (left 0.05, 0.62, 0.22 × 0.34): twelve dotted rings down a bright axis
  into a spiral, the ring at `period % 12` lit, delivering FLOW every 5 s. The STRIP (0.50,
  0.06, 0.18 × 0.035): 23 cells, the window at `periodF`. The LATTICE (right 0.50, 0.78,
  0.44 × 0.17): a grid sunk toward a coral mass standing at `periodF`'s place on the small
  time axis (the governed years at its ends), one orbit — "time is linear · context is not".
- **1 Context Canvas.** The CHAIN (main 0.03, 0.24, 0.50 × 0.45): five overlapping rings, the
  record's coral inner ring in the middle one, the context ring the walk has reached in sky,
  a line through. The NETWORK (left 0.03, 0.79, 0.42 × 0.18): 4-6-6-6-4 layered nodes, the
  walk's path lit. The HALFTONE (right 0.66, 0.64, 0.31 × 0.32): a dot field sized by a
  gradient centred where the walk is. Reactive: the PRISM (0.52 w, 0.70 h; 0.10 w × 0.20 h),
  arcs running outward each time a walk completes.
- **2 Spacetime — a flight interface: map and time.** The WORLD MAP (main 0.05, 0.14,
  0.57 × 0.50): the release's coastlines (`public/trace-spacetime-v1/natural-earth-50m-admin0-v5.1.1.geojson`,
  rings under 4 sq° dropped, Douglas–Peucker at 1.1°, 194 rings / 1,804 points in
  `world-outline.ts`) as ~1,200 points in an equirectangular frame (lon −170..180,
  lat −56..84) with a 30° graticule; one aggregate mark per MAPPED geography (81) at its
  feature's label point, radius 3 + 11·√(n / max) by source-assignment count (UK 3,214 · US
  1,175 · Norway 562 · Germany 427 · Russia 231 · France 224 lead); the held one
  (`region = period % 6`) coral with a dotted bearing line from the frame's centre;
  aggregate-only geographies stay off the map by the registry's policy. The GEOGRAPHY TAPE
  (left 0.64, 0.16, 0.05 × 0.40), vertical: the six largest as bars. The TIME TAPE (right
  0.05, 0.68, 0.57 × 0.05): 23 ticks, the cursor at `periodF` bracketed in coral, the
  governed years at its ends. Reactive: the LEDGER (0.72 w, 0.74 h; 0.25 w × 0.18 h), six
  rows × 23 columns, the bus's column and row read together. No scan.
- **3 Between records.** Built literally from the owner's prototype (Exploration's former
  scope): seven rings, one inside the next (main 0.46, 0.08, 0.50 × 0.86), each
  `[cx + sc·sin(5u + φ), cy + 0.9·sc·sin(4u)]` with `sc = R·(0.22 + 0.78·k/6)`, 200 coral
  particles each (r 1.2, +1.6 at the head; the head at `u = t·0.045`), on the scope's two
  scales and nothing else — no tracking brackets (`frame: 0`), the field faded out. The
  figures never change; across the hold the scroll blends each ring continuously between an
  eight-segment sampling and its smooth form (`round = sin(π·prog)`), so the scroll cannot
  stutter. Its readout line: "a pattern, not a claim".
- **4 Exploration.** The DIAL (main 0.05, 0.10, 0.46 × 0.54): a ring the sweep lights, a
  satellite with its crosshair, the open-inquiry ring apart in sand. The WAVE (right 0.03,
  0.75, 0.52 × 0.21): a packet whose centre follows the sweep, bumping on the pulse; the
  inquiry LOOP apart at its right. Reactive: the OSCILLON (0.58 w, 0.06 h; 0.36 w × 0.16 h)
  sheared by the sweep; the PULSES from the satellite.
- **Everywhere.** The QUANTA field (concentric and offset rings; the outer rings on the
  front canvas over the text; faded out on screen 3), the readout TILES (0.72 w, 0.06 h),
  the tracking brackets on the main form, the wires. The tiles, the halftone and the
  ledger's cells are hash-seeded texture, not data. Binding the ledger to the governed
  atlas cells (373 non-zero) is an open item.

### The bus

Every component reads from one signal bus and some write to it (`bus`, `computeBus()`):

| signal | tempo | writes | reads |
|---|---|---|---|
| PERIOD | 23 buckets scanned by the clock (~83 s per cycle) and pushed on by the scroll (`setScroll`); `periodF` continuous | `periodChangedAt`, `region = period % 6` | sphere column, funnel ring, strip window, lattice mass, map's held mark, geography tape bar, time-tape cursor, ledger column and row |
| WALK | one step every 4.2 s | `walkDoneAt` on a completed path | chain's context ring, network path, halftone centre, prism |
| SWEEP | 0.22 rad/s | `pulseAt` when it passes the satellite | dial, oscillon shear |
| PULSE | on the sweep's pass | — | wave bump, inquiry loop, pulses |
| FLOW | the funnel's delivery every 5 s | `flowAt` | lattice well depth |

Rules: everything that MOVES follows `periodF`, never the integer bucket, so the scroll
never steps; every decay is 2–3 s (exchanges are slow — no high-frequency flicker); the
wires are the couplings drawn and run only between FIXED anchors (frame edges, tape ends,
the tiles, the readout), never after a moving mark, so nothing jumps.

### The text layer

- **Hero** (screen 0, left `--s-5`, top 13 %, width 46 %): `TRACE` in the statement face,
  solid; the line broken before "One" — "Three research views." / "One governed archive."
  (`max-width: 30ch`); the lead. The readout line (top left, sand capitals) belongs to
  screen 0 only.
- **Notes**, one per view, each in its own empty region: Context Canvas right 3 % / top
  22 % / width 38 %, ranged right — name, question, brief, boundary, what the function does
  (three composition templates, the same rows in text, a public-safe export); Spacetime
  right 3 % / top 20 % / width 26 % — name, question, brief, boundary (the "what it does"
  paragraph removed at the owner's ask); Between records left `--s-5 + 20px` / top 12 % /
  width 38 % — name, question, brief, boundary; Exploration right 3 % / top 24 % / width
  38 %, ranged right — name, question, brief, what the function does (the validated map of
  at most eight concepts with its plain-text tree and exports; the eleven scoped inquiries
  apart). A note fades in as its screen settles.
- **Captions** (`CAPTIONS`): inserted into the scene as the scroll goes on, positioned in
  sheet percentages; right-aligned ones are positioned from the right (`right:`) so they
  never wrap word by word. Two kinds: LABELS in the technical face beside a component
  ("one record, and the contexts it is filed in", "23 periods — when", "association —
  generic, non-directional", "open inquiry — held apart"…) accumulate; PARAGRAPHS in the
  reading face take turns — on each screen only the latest paragraph the scroll has reached
  is shown, in one place — so no two paragraphs share the sheet, and the page is never pure
  animation. The first screen carries labels only.
- **Rules, checked in the browser at each frozen state** (all empty on screens 0–4 at
  1960 × 1130): no text box intersects another; every caption lies at least 24 px outside
  every component box; no paragraph ends on a lone last word (`text-wrap: pretty` on every
  paragraph, `balance` on the question and the closing line).

### The entries

A fixed column on the right (`.dock`): the nav's 60 px control (2 px paper border,
inverted on hover / focus), in line with the nav's Source icon, vertically centred in the
viewport, never scrolling away, with the nav's own reveal (the name in the heading face
beside the column, level with the hovered control) and the names as accessible labels. No
numbers — the views have no order. The glyphs (`icons.tsx`) are 38 px on a 24-unit grid,
stroke 1.8, round caps, each mark's bounding box centred on (12,12): Context Canvas is
*connect* (one node joined to two); Spacetime is a compass (preferred to a map pin);
Exploration is an open eye that shines. While a view's screen holds a leader line draws
from the scene's anchor mark (top right) to its icon, an elbow, and is gone once the scene
releases (`sp ≥ 0.985`). There are no other controls.

### The closing block

Its own section after the scene, with the ground held dark to the end of the scroll
(`document.documentElement.style.background`) so nothing pale shows past it:

1. the headline "**TRACE** the design history no single record can show on its own."
   (statement face, `balance`, 24ch) — joined to TRACE the control by a fixed line
   (`.footLead`: from the headline's right edge, across to the nav TRACE icon's column, up
   to the header's edge) shown only once the headline has come up past 45 % of the
   viewport;
2. the definition paragraph at the left, and the identity tagline beside it at the right,
   shown only at the page's very end (`max − scrollY < 8`);
3. Shared research principles (titles only) beside Current TRACE baseline (the ledger from
   the manifests, and the baseline note).

### Register

Ground `#050506`, paper `#efe9dd`, sand `#c9a37b` for labels and rules, red spine
`#c8322b` as a 1 px segmented hairline at the sheet's left edge inside the scene only,
growing with the scroll; a 28 px dot grid at 9 %, film grain at 4.5 %; coral 240,135,106 ·
mint 95,191,179 · sky 79,168,222 only for what carries a signal. Type: title
`clamp(6rem, 10.5vw, 12rem)` statement italic, solid; line `clamp(1.9rem, 2.6vw, 2.6rem)`;
view names `clamp(2.6rem, 3.6vw, 3.8rem)`; questions `clamp(1.25rem, 1.5vw, 1.5rem)`
italic; labels in the numeric face at `--fs-label` (the 17 px floor), 0.08em tracking,
with a 1 px sand rule; paragraphs in the reading face at 82 % paper; closing
`clamp(2.6rem, 4vw, 4.2rem)`; tagline `clamp(2rem, 2.6vw, 2.6rem)`; principles 1.25rem;
ledger numerals 1.5rem tabular. No new fonts.

### Motion and performance

Each canvas runs ~30 fps while on screen and the pane is visible, one frame otherwise;
DPR capped at 2; reduced motion holds the clock at 0 (a static scene, the draw-in
complete). The set draws itself in once over 2.4 s on arrival. The scroll handler is
rAF-throttled; the page's CSS variables (`--tp`, `--sp`) come from scroll only; no timed
page animation, no easing on scroll, no scroll-jacking.

### Verification method

The fixed synthetic stress fixture (`lib/stress-fixture.server.ts`; development builds,
`?state=stress` and `?state=stress-missing`): a long title, attribution and type; Medium 4
terms (one long), Theme 6 (two long), Movement 3 — or none; opened with one Theme term set
aside, a Theme term selected, the inspector and the rows open. Layout testing only,
banner-labelled; the real workload is 3 nodes (P50 and P95) and 5 at most.
`npm run test:context-canvas-design` (`scripts/test-context-canvas-design.mjs`, jiti over
the governed reader) checks, for four real objects (3, 4, 4 and 5 nodes) and both stress
variants under every layout: the three wordings; every wire starts on the object and ends
on its chip, straight or orthogonal, every visible chip on exactly one wire, none for a
dimension not recorded, wordings 20 px from either card and never on one another; the same
ids, fields and wording under every layout; the ticket export (labels as titles, the
wordings on the branches, the MGDA mark, no full hash, identifier or publication state in
sight, the binding in <desc>); the clipboard tables.
In the browser at 1960 × 1130: the object with all three contexts, a selected context with
the inspector and coverage, Movement not recorded, loading / empty / the two failures,
the rows open, a set-aside context with the "+" and System suggests, the four layouts on
the stress fixture; DOM checks — no text box intersects another (closed folds excluded),
wire wordings clear of cards and field words, no paragraph ends on a lone word, the
minimum font size, no page scroll; the ticket SVG rendered inline and measured (no text on
text, nothing outside the sheet). Functional runs on real records: add / remove / undo /
redo, Fit against Reset, reload persistence and object switching. Gates: `tsc`,
`typecheck:runtime`, `test:read-platform`, `verify-context-canvas-v49`,
`rehearse-context-runtime-v1`, `test:context-canvas-design`, the hygiene audit.

### Interactive text is never grey

The owner's rule (2026-09-05): grey (`--t-sand`) is for labels only. Anything the reader
can act on — the "Change the selected object" summary, the inspector's folds, the rows'
disclosure line, the template select — is set in black and inverts (black ground, paper
text) on hover and focus, so nothing that can be clicked looks disabled. The stage is
positioned and could paint over a neighbouring column; the inspector's column is therefore
positioned above it, and the canvas column's track is `minmax(0, 1fr)` with its overflow
hidden so a wide toolbar can never widen the column past its track.

### Bad practice — removed, do not reintroduce

A perspective camera or side-view "3-to-2" rendering (it broke the picture); human figures
of any kind; the moiré star; a scan sweeping the map; corner registration marks; numeric
"system lines" printing the bus's counters under the notes (WALK 3 / 5 …); components
repeated across screens (the globe, the spiral, the scope in two places); twelve components
on one screen (a pile-up); an outlined title; a grey sheet; paragraphs appearing together;
captions positioned from the left when ranged right; wires that follow moving marks;
integer period steps under the scroll; "Start with" intros and 01/02/03 numbering on the
entries; any recents, trending, recommendation or "System suggests" on the landing.

---

## 7g. Context Canvas — TRACE Function 1 (2026-09-04, owner's brief of the same day)

The maintenance record for `/trace/context-canvas`. The function is the reference
implementation's, unchanged; this round re-set what is seen.

### Route, scope, boundary

- `/trace/context-canvas?record={SURF-…}` (`frontend/src/app/trace/context-canvas/page.tsx`).
  Desktop only by policy (§4): the server checks the mobile hint and returns the mobile nav
  plus `TraceDesktopRequired` before any research runtime is imported; the governed imports
  stay inside one `await Promise.all` after the guard (the suggestions UI test reads the file
  for that order).
- The selected object is the projection's first deterministic sample unless `?record=`
  names a public stable ID; changing it is the existing behaviour (an ID, or one of the
  twelve samples), folded in the rail. No new picker, no Search.
- The product logic is untouched: composition state, reducer, entity and row derivations,
  persistence (browser-local, keyed to release · projection · record), and the PNG export
  are `features/trace-v49/context/canvas/*` as before; the route no longer renders that
  folder's reference UI (`ContextCanvas.tsx` and its parts stay for their tests).
- Context is project-curated archival positioning only. The page never draws a line between
  two things, never ranks a context, never reads distance as strength, never shows
  `ROLE` / `STATE` / hashes on the canvas, and never names a provider.

### What the page reads as

One selected archive object → three governed contextual dimensions → inspect and compare.
The owner's IA: 01 the head (TRACE · CONTEXT CANVAS · "See how one archive object is
positioned within project-curated context." · the selected object's title and stable ID) ·
02 the controls (template; Medium / Theme / Movement availability and inclusion; the
existing add action; the way to the rows) · 03 the spatial canvas · 04 the inspector ·
05 the accessible rows · 06 System suggests · 07 export · 08 the shared states.

### Layout (1960 × 1130) — three workspaces

Under the nav: the rail at the left, the canvas as the body, the inspector at the right
only while open, the dock's 60 px column reserved past them. The page does not scroll;
the rail and the inspector scroll inside. Three workspaces (the owner's, 2026-09-05):
NORMAL — rail expanded (17rem), inspector closed: the canvas is 1,300 × 920 px, 72 % of
the usable width; INSPECT — the inspector open (17rem), the canvas 1,020 px; CANVAS
FOCUS — the rail compact (11rem), the canvas 1,400 px, 78 %. The inspector is closed by
default, opens itself when a context (or the object) is selected, and closes from its own
control in the dock. Under the three view entries, past a rule, the page's two LOCAL TOOLS
— not a fourth and fifth function: the inspector's toggle (a split-view glyph, revealed as
"Inspector" / "Close inspector") and the global ADD CONTEXT "+" (revealed as "Add
context", or "No context to add" and disabled when the object has nothing governed left).
The "+" opens the right panel as ADD CONTEXT (`AddContextPanel`): the governed context
this object carries that is not on the canvas, grouped Medium · Theme · Movement — "No
additional context" where none — each with one Add; adding puts the term in its field,
selects and focuses it, shows its wire, updates the rows and counts, and hands the panel
back to the inspector. Nothing can be searched for, typed or made from blank canvas. The
rail's per-dimension "N on canvas · M available [+]" stays as the secondary way. The rail's
"‹" collapses it to the compact form (the title, three dimension indicators, "›" to expand;
the choice kept per browser). The canvas: the stage (a 1 px black rule, the 28 px dot
grid), the toolbar under it as one 32 px line, and the rows panel folded beneath as one
30 px disclosure line.

### The canvas (`lib/arrange.ts`, `desktop/Stage.tsx`, `desktop/CanvasItem.tsx`)

World units at zoom 1. The OBJECT (320 × 140) stands once: the light-blue plate with
"Selected object", the title (two lines), the stable ID, year · type — no more. Its
contexts stand in three FIELDS — thin 1.5 px outlines in the dimension's accent with a
16 × 5 px accent bar before the dimension's word inside at the top left; no fill — as
CHIPS (280 × 52), a paper line with a black rule and a 5 px accent bar at the left edge,
the governed label only, one size everywhere. A field is the union of its default place
(wherever the object now stands) and its chips wherever they have been dragged, so its
label never lies; a dimension with nothing on the canvas is a COMPACT marker (236 × 36,
one line: the word and "Not recorded" or "n set aside"), never a large empty region. Chips
are laid out in the projection's order; Arrange and Reset restore the layout; Fit never
zooms past 1. The one claim boundary — "Context describes archival positioning, not
historical influence." — stands once, as the canvas's footer; the inspector does not
repeat it.

### The connections — one class, three wordings (the owner's, 2026-09-05)

Governed Context V1 has exactly one connection class, the selected object to one of its
context representations, and the registry reads it three ways: Medium "classified as",
Theme "themed as", Movement "curated within" (`connectionLabel`, the adapter's contract).
The canvas draws them as WIRES (`connectorsOf` in `lib/arrange.ts`, `Stage`): a 1 px
neutral line from the side of the object plate that faces the chip to the chip's facing
side, the wording on a paper tab at the middle; no arrowhead, no weight, no colour of its
own; 1.5 px and darker only while its chip is hovered or selected. Never between two
terms, never between two objects, never for a dimension not recorded; the count of wires
equals the count of representations on the canvas. Overview and Focus wire every chip (the
ring is 120 px so the wording has room); Columns wires each column once (96 px); Dense
draws none and prints the wording in the band's head. The rows' accessible names carry the
same wording ("Theme context (themed as)"). No other relation exists on this page: not
object–object, not term–term, not influence, similarity, causation, hierarchy or
chronology — those questions belong to Exploration, and Region to Spacetime.

### Adding context — the rail's "+" (the owner's, 2026-09-05)

Each dimension line reads "N on canvas · M available" (the "· M available" only while
M > 0; "Not recorded" where the object carries none). While M > 0 the line ends in a "+"
(`aria-expanded`, `aria-controls`) that opens that dimension's AVAILABLE list inline —
each term with an Add. Add places the already-governed representation in its field
(`slotFor`), the reducer selects it, the chip takes keyboard focus, the inspector opens
on it, the rows update, its wire appears with its wording, the count falls, and the list
closes when nothing is left. A field with more of its kind available says "+ n available"
in its head (an assist; the rail is the control). Dragging a row's Add onto the canvas
remains the secondary way. Nothing can be created from blank canvas: a reader only places
what the server already approved. Real workloads are small — of 7,995 objects, 7,884
carry two representations, 106 three, 5 four; the canvas's default is P50 = 3 nodes and
its maximum 5 (`SURF-LOCTRACE2026R00867`: one Medium, one Theme, two Movements). The
synthetic 4 / 6 / 3 fixture stays a defensive layout test, never a product target.

### Entering, choosing the object, and what a reload keeps (the owner's, 2026-09-05)

Entering `/trace/context-canvas` always opens a canvas — never a chooser page (the owner
rejected one: "无法理解也无法找到正确的交互部分"). Without `?record=` the route sends the
reader, as a redirect to its own `?record=` address, to the object opened most recently in
this browser — a first-party cookie (`mgda-context-last`, the public stable ID and nothing
else) the canvas sets and renews for thirty minutes — or else to the LANDING record: the
reader-facing object carrying governed context in all three dimensions with the most
representations, ties by stable ID (`getGovernedContextLandingRecord`; in v49 that is the
1 · 1 · 2 record "Solidarity with the people of Southern Africa"). The rail's chooser
(`ObjectChooser`), folded under "Change the selected object", is the way to another object:
- SEARCH by title or ID (`/api/trace/v1/context-objects?q=`, through the governed reader):
  words find READER-FACING titles only (the reader-eligibility projection's verdict; case
  and diacritics do not matter — "Kestavalla" finds "Kestävällä"); a public record ID or its
  prefix finds any of the 7,995 governed public records, record-only ones included, marked
  "record-only". Results are links; the title is what a result is known by, the ID and the
  count of contexts its second line. Arrow down from the box into the results, Enter opens.
- START WITH AN EXAMPLE: five objects picked from the reader-facing ones by fixed criteria,
  first by stable ID, never by hand (`getGovernedContextExampleOptions`): one context of
  each kind; Medium and Theme with Movement not recorded; two Themes; two Movements (four
  contexts — the most any v49 object carries); a title in another language.
- OPEN BY RECORD ID, behind a fold: the exact public record ID, any governed public record;
  held records fail closed as before.
- QA SAMPLES, behind their own fold and only in development or with `?qa=1`: the
  projection's twelve deterministic samples — "12 of 7,995 governed public records, evenly
  spaced by stable public ID. For deterministic testing; not a representative sample." The
  sampling (index = floor(i × 7994 / 11): 0, 726, 1453, 2180, 2906, 3633, 4360, 5087, 5813,
  6540, 7267, 7994) and its tests stay; the production interface never calls them a
  reader's sample, and the native select is gone.
An object opens with one representation of each dimension on the canvas and the rest left
to add — "1/2 on canvas", "+ 1 available" — so every canvas shows every relation and the
add is there to be found (development previews open whole). A reload restores the reader's
composition — its membership, what was set aside, what was selected — and lays it out
again under the layout as it is now; positions from another layout or an earlier
arrangement are never drawn. In v49 no object carries more than four representations and
110 carry all three dimensions.

### The canvas ground (the owner's, 2026-09-05)

The stage's ground is the ticket's grey-white (`--c-canvas`, `#f2f0eb`), a step brighter
than the page's paper; the rail, the inspector, the rows and the toolbar stay on the paper.
The chips and the wording knockouts take the ground's colour, so the canvas and its export
are one sheet and the canvas stands out from the workspaces around it.

### Moving things — a drag ends in a verdict (the owner's, 2026-09-05)

The owner dragged chips across the canvas and the fields — drawn around wherever their
chips stand — grew into one another, the wordings floated, the picture read as nested
boxes. So a drag ends in a VERDICT (`dropVerdict` in `lib/arrange.ts`, on the drag's end):
a context may be moved within its own field's chip area (never over the field's word, in
Dense never into the label column), never onto another item; the object stays where its
fields are laid out around it. Anything else is put back where it started and the status
line says why ("‘Poster’ stays in Medium: a context moves within its own field." / "…was
put back: items never stand on one another." / "The object stays where its fields are laid
out around it; drag the ground to pan."). While the drag lasts the wire follows the chip
and its field reaches for it; the verdict decides. The rail's count reads "n/T on canvas"
— what stands, out of what the object carries (the compact rail and the ticket's key say
the same) — so the reader sees at once how much there is to add. The object's plate is
320 × 156, room for a title clamped to two lines, a stable ID that breaks after a hyphen
onto a second line, and the year · type line; focus rings in the rail are drawn
inside the control (the rail scrolls and clipped a ring outside its edge, which read as a
"blocked" frame); the layout's one-line brief keeps a tight leading, the room going between
the rail's groups.

### The wires — one connection class, three wordings (the owner's, 2026-09-05)

Governed Context V1 has one connection class — the selected object to one of its context
representations — read as the registry's three wordings: Medium "classified as", Theme
"themed as", Movement "curated within"; nothing else is ever drawn (no term–term,
object–object, causal, similarity, influence, hierarchy or chronology relation; nothing
for a dimension not recorded). `connectorsOf` in `lib/arrange.ts` routes them: orthogonal
1 px neutral wires, no arrowhead, no weight, from the object's card to the actual chip —
right edge → Theme chip's left edge, left edge → Medium chip's right edge, bottom edge →
Movement chip's top edge, or the nearest clear side (the wider gap decides). A chip
approached from the side has its own wire (lane 34 px past the object's edge); a stack
approached from above (Columns, Focus's compact stacks) is one wire to its first chip and
the stack is the wire's group; Dense's bands are reached from one lane 34 px outside the
bands' left edge, one wire per band into its first chip, the wording inside the band's
label column. A wire never passes through another field or a card: when the straight
approach is blocked (Focus — the second compact stack under the first) the wire leaves
the object's side, takes an outer lane down the clearer side and enters the chip from
that side, its wording turned along the lane. The wording sits ON the wire and interrupts
it (a paper knockout), on the longest run outside the field — at least 20 px from every
card, 24 px from the field's word, never on another field's outline — and wordings that
would lie on one another slide along their own run until apart. A wire whose chip is
hovered or selected turns 1.5 px in the dimension's accent: focus, never strength. A
field's word never carries the wording. Rings: 160 px in Overview and Focus (room for the
wording), 110 px in Columns, 72 px in Dense.

### Four templates — layout only (the owner's, 2026-09-05)

The public control is CANVAS LAYOUT, never "template": the governed composition template
stays the one "Context overview" (`context-overview` v2, the contract's name), and the
four reader-facing choices are layout presets over exactly the same governed object and
contexts (`LAYOUTS` in `lib/content.ts`, `arrangeWith` in `lib/arrange.ts`; a per-browser
choice). A layout may never add or remove a context, change membership, importance,
order, evidence, coverage, the selected object or the semantic colours; switching one
keeps the selected object, the canvas's membership, the selected term and the inspector,
and changes positions and the fit only (the reducer clears the selection on a commit, so
the tree re-selects).

| layout | the object | the fields | extra control |
|---|---|---|---|
| Overview (default) | at the centre | Medium left, Theme right, Movement below, each 72 px from the plate; a Movement row wider than the object and its rings stands below the side columns | none |
| Focus | at the left | the chosen dimension read in full beside it (two columns past six chips); the other two compact beneath the object — the same chips, no smaller: larger means "being read", not "more important" | a compact FOCUS selector — Medium · Theme · Movement — a dimension the object carries nothing of disabled; it opens on the selected term's dimension, else the first with a chip |
| Columns | above | three equal columns, Medium · Theme · Movement, 24 px apart — for comparison, no line across | none |
| Dense | above | three bands, the word in a 176 px label column at the left, chips three to a row — nearest to a research index; long labels wrap to two lines and keep their full text as the chip's title | none |

### The rail, the inspector, the rows, the suggestions

- Rail (`PageHeader`, `ContextControls`): the head; the template select (one governed
  template — the control stays LIVE with its one option, and the note says so; a greyed
  control read as broken); the three dimensions as lines
  "MEDIUM · 1 on canvas" / "MOVEMENT · Not recorded" (a line brings its field into view;
  a set-aside context gets an Add); one control opens the rows. Not filters.
- Inspector (`Inspector`), five things and one fold (the owner's, 2026-09-05): for a
  context — the dimension (dot + word), the label, "Project-curated context", "Why it
  appears" (the registry's one sentence), Coverage — "N of 7,995 public records carry this
  classification." (from `generated/trace-context-v1/terms.json` via
  `lib/coverage.server.ts`; the cohort from the manifest) — and "Source basis" (the
  registry's sentence). Then "Technical provenance ▸": Release (short, "v49"), Projection,
  Integrity as the checksum's first eight characters with "Copy full", and "Copy technical
  provenance" (the full release identity, manifest, policy versions, identifiers,
  decision, publication, the permitted reading and what is not established — everything
  the contract and the governance policy's explainability requirements record, copied,
  never displayed). Then the existing add / remove. No separate reading-rules fold: the
  canvas's footer carries the one interpretation boundary. Idle (opened by hand with
  nothing selected): one sentence and the technical fold. For the object: its four
  source-reported fields and a link to its record page.
- Rows (`ContextRows`): a `<details>` panel under the toolbar, folded by default (open, at
  most a third of the viewport, scrolling inside), three columns (Medium · Theme ·
  Movement), "Not recorded" where none; each row selects its chip and brings it into view,
  a chip selected marks its row; "Go to chip" moves focus onto the chip; Add / Remove on
  the row's own line; "on canvas" / "set aside" as the visible state (the connection word
  stays in the row's accessible name). "Copy context" puts the same presentation on the
  clipboard as tables — `text/html` (a real table, for notes and documents) and
  `text/plain` as a Markdown table (for chats, editors) — an Object table (Title, Date,
  Attribution, Type, Source, ID; empty fields omitted), a Context table (Dimension ·
  Context, one row per term on the canvas, "Not recorded" or "n set aside" where none),
  the one interpretation boundary, and "MGDA · v49 · Context Canvas"; no hashes, no
  connection or publication language. One PRESENTATION MODEL (`lib/presentation.ts`)
  feeds the canvas's fields, the rows and the clipboard, so the three can never say
  different things.
- System suggests: the shared panel (`tone="dark"`), rendered only while a context is set
  aside, so every suggestion carries an existing action (`EXPAND_*`); no `RETURN_TO_OBJECT`.
  The fallback note's wording is the provider's — an open item for the guidance round.
- Toolbar (`CanvasToolbar`): − % + · Fit · Arrange · Undo · Redo · Reset · Export PNG, with
  the status line (`aria-live`) at its right. "Reset view" of the reference was the same
  call as Fit and was folded into it.
- Export (`lib/export-card.ts`, rasterised by the reference's `downloadContextCanvasPng`):
  an MGDA TICKET, 1800 × 1200 — a grey-white ticket (`#f2f0eb`, a step brighter than the
  page's paper so it reads and shares well; square-cut, never rounded) laid on black, a
  hairline frame inset 14 px on either side of a perforated rule with round notches parting
  the long body (70 %) from the stub; the body sits on the canvas's own 28 px dot grid at
  16 %, the plates, words and notes on paper knockouts. The body: CONTEXT MAP as a tree after a table-of-contents diagram — the selected
  object's plate at the left, a spine, one branch per dimension with the wording ON the
  branch, the terms on the canvas as leaves in the dimension colours (the selected one
  coral); a dimension with nothing on the canvas is named and marked "Not recorded" (or "n
  set aside") and gets no branch. The stub: two thin decorative bars (the brand sheet's
  lavender `#a785fe` and blue `#537cde` — decoration only, never a ground), the MGDA mark on
  an ink tile with the wordmark (the nav's own), CONTEXT CANVAS · RESEARCH RECORD, the
  title, year · attribution, source, the stable ID as the serial, the dimension key with
  counts, the interpretation boundary, "v49 · trace-context-v1 · 825f6eca" and the site,
  and a line of microtext along the edge. Type is set for the sheet, not the screen: 14 px
  the smallest upright line (kickers), leaves 20, dimension words 18, the stub's title 30,
  the boundary 19 — on an 1800 px sheet. Membership, selection, wording and colours are
  preserved; the geometry is normalised (never the screen's pixels); a tree taller than the
  body (only a synthetic fixture — the real workload is five nodes) is scaled down as one,
  never cut, and a long stable ID breaks after a hyphen on the plate and the stub. No full
  hash, internal identifier, publication state or suggestion is printed; the full binding
  is in <desc>. The reference's SVG renderer stays for its tests.
### States

Loading (the canvas held in `INITIALIZING`, `aria-busy`, the controls disabled, a caption
in the stage's corner; dev preview `?state=loading`) · populated · `availability="empty"`
(the object alone, three fields "Not recorded", the canonical sentence in the corner; dev
preview `?state=empty` — the v49 projection never produces it) · one dimension not
recorded (most records: 7,884 of 7,995 carry medium and theme only) · set aside · the
failure page (`ContextFailure`: the reader's own code and message, the requested ID kept in
the open change-object forms, "Retry the same request" for the same governed request; no
dataset mounted) · partial: not supported, the dataset is one integrity-bound unit ·
mobile: the desktop-required notice.

### Register — the owner's palette for this view

Grey-white paper `#e8e6e0` as the ground, black `#0a0a0b` type (82 % for prose; labels
`#5f5e5a`), light grey `#c4c3be` for rules; light blue `#a9c2e4` for the object's plate;
coral `#e8917d` as the one highlight (selection); and one restrained accent per dimension
— Medium cyan `#2f9fc6`, Theme green `#3a9a78`, Movement warm orange `#d4842e` — used the
same way on the canvas (field outline, accent bars), in the rail and the rows (dots) and
in the inspector (the dimension's dot): thin lines and small marks, never a fill, never
the only carrier (the word is always there), never a reading of strength, confidence or
rank. Type one step smaller than the reading pages so the workspace reads in one
screen: labels 14 px (`--c-fs-label`), prose 15 px, chips and row labels 16 px, the page
name 28 px, plate and inspector names 20 px — a per-page exception to the 17 px floor, at
the owner's instruction. Film grain at 4.5 %; the dock as on the landing.

### Verification method

`npm run test:context-canvas-design` (`scripts/test-context-canvas-design.mjs`, the
page's pure modules against the governed projection through jiti): the three wordings per
kind on four real objects (the default 3-node object, two 4-node objects including the one
with two Themes, the 5-node maximum) and the two stress variants; under every layout the
same ids, three fields with the right states, no two items overlapping, every connector
from the object with the contract's wording and none for a dimension not recorded, one
wire per representation in Overview and Focus, one per column in Columns, none in Dense;
the research card in every layout (1800 × 1200, no arrowheads, no full hash, no internal
identifier, no publication language, no suggestions, the fingerprint, the boundary, every
label as a `<title>`, the binding in `<desc>`); the clipboard tables. In the browser at
1960 × 1130 (a fresh tab, zero console errors): the add flow on the two-Theme object —
remove, "+", the available list, Add → the chip back in its field, focused, selected, the
inspector on it, the rows updated, its wire and wording; undo, redo; Fit against Reset;
remove one, switch to Columns, reload → the composition and the layout restored, the
viewport fitted again; then the 5-node object untouched by the other's composition; the
stress fixture in the four layouts, the loading, empty and failure states, the mobile
notice. The card is rendered inline and measured (no text on text, nothing past the
sheet). The harness cannot deliver key presses to a hidden pane, so keyboard activation of
"+" and Add is verified as native buttons in Tab order with accessible names, and left to
a live check.

### Bad practice — removed, do not reintroduce

Cards with `ROLE` / `STATE` rows on the canvas; three equal columns; a permanently open
inspector eating the canvas's width; a "+" for the inspector's toggle; a second full
metadata card in the rail; the dataset's hashes in the inspector by default; a permanent
System suggests panel with a generic note; lines, arrows or connectors between the object
and its contexts; grey cells as fields; colour as the only carrier of a dimension, or as a
fill; region labels closer than 24 px to a chip; a control bar floating over the canvas
that overflows it; "Reset view" beside Fit; a disabled template select; grey text on
anything clickable.

---

### 7h · Spacetime — Space × Time over the sealed GIS (2026-09-05, third pass) — FROZEN / DEFERRED_FROM_PRODUCT

**The question, upgraded (the owner's).** Not "where are this decade's records" — a map
with a decade filter is weaker than a sorted table when 1,630 of 1,898 records sit in one
country — but *how does the archive's geographic concentration change across time?* Space
and Time meet on the map itself. The GIS is the sealed Codex implementation — Natural Earth
5.1.1 50m, Equal Earth, 93 governed geographies (81 mapped · 11 aggregate-only · 1
unmapped), 23 decade periods with INTERVAL_OVERLAP membership, aggregate / density /
texture rendering, selection and focus, matching-record retrieval, three read APIs, audited
SEALED_PASS — untouched. The presentation is `src/app/trace/spacetime/desktop/*` over
`useSpacetimeWorkspace` (`features/trace-v49/spacetime/map/SpacetimeWorkspace.tsx`, whose
functional view stays for the runtime and API scripts): the one orchestration, now also
holding the two ADJACENT ATLASES (the same read API, one request each, the last period
change winning) and the deterministic derivations over them — `rankSpacetimeRows`,
`deriveSpacetimePeriodProfile`, `deriveSpacetimeTemporalWindow` — the desktop fetches and
derives nothing of its own (`test:spacetime-design` reads the source for this).

**The IA.** 01 PERIOD PROFILE (the rail) — what this decade looks like: "1980s · 1,898
public records · 22 recorded geographies · Top concentration: United Kingdom, 1,630 records
· 85.9% of public archive records in this period", the previous and next periods' totals
beside it; mapped / not mapped and the precision mix behind "Data quality". Then the
research control, MAP LAYER — Distribution (where this period's records gather) ·
Temporal (how each place's records stand in the previous, this and the next period) — and
under it, small and secondary, MAP STYLE: Aggregate · Density · Texture, three drawings of
the same data ("About the styles" folded); the way to the PLACE RANKING. 02 the MAP. 03
PLACE PROFILE (the right column, only once a place is chosen; not an inspector): the
place, its class ("Not plotted on the map" only when it applies), "1980s · 49 records ·
2.6% of public archive records in this period · Rank #3 of 22 recorded geographies", then
AROUND THIS PERIOD — a three-column ledger, Records · Share · Rank in the previous, this and
the next period (United States: 226 / 49 / 129; 20.6% / 2.6% / 29.3%; #1 / #3 / #2), the
current column set apart, "—" where a period has no neighbour, "…" while the neighbours
load; Data quality folded; the qualification only for a place without a position; View
matching records · World view; provenance folded; SYSTEM SUGGESTS at the foot. 04 RECORD
EVIDENCE — the matching records, in the one drawer, whose other tab is the PLACE RANKING:
Place · Records · Share of period · Rank, records descending, a light amber "Not plotted"
mark (its reason on hover) instead of a mapping-state column.

**The map, redrawn (the owner's reference sheets: fine line maps, dot-matrix counts, glyph
marks; the solid disc is BAD PRACTICE, never again).** Three orders of line and one of
tone from the Natural Earth geometry alone: the coast a firm warm ink line (an under-layer
of every land path's stroke, the fills leaving its outer edge), boundaries hairlines, land
a pale warm tone on the canvas ground, mapped land a pale blue; hover mint; the selection
a pale coral with a red edge. DISTRIBUTION · Aggregate draws each mapped place's records as
a RING at its governed anchor — the radius the sealed count policy (`max(4, min(18, 3 +
0.75√n))`), the form the sealed count tier: a thin ring (1–4), a ring (5–24), a ring with
its centre (25–99), a double ring (100 or more) — in cobalt, red when chosen; the sealed
marks' solid circles are never shown. Density keeps the sealed dots, small; Texture the
sealed tier pattern, quiet. TEMPORAL draws, at the same anchor, THREE BARS — records in
the previous, this and the next period, one scale for every place (the window's most,
on a square root, 2–20 px), the current bar in cobalt, its neighbours a neutral grey, the
chosen place's current bar red, a dash where a period has no neighbour; at world scale
only places of the third sealed tier (25 records) and above carry the full glyph, the rest a
small ring until hovered or chosen; a focused view shows every glyph. No growth or decline
colours, no arrows, no trend. NOT PLOTTED: in the Temporal layer the aggregate-only and
unmapped places stand in a companion list at the map's corner with the same three bars —
a place that cannot be placed still has its temporal evidence. A chosen place, focused,
shows its sealed dot field — one dot a record — inside its geometry in red (the owner's
sixth sheet). Labels are interaction-led: the chosen place and the hovered one, name and
this period's count (the three counts in the Temporal layer). FIT is gone (the map fits
itself); WORLD VIEW appears only with a selection or a focus and clears the selection and
the extent, nothing else. The projection is the sealed Equal Earth (fitted uniformly; the
curve of Australia is the projection's own, not a distortion) — the GIS offers one other,
Natural Earth I, and switching would be a one-line change the owner has not asked for.

**The period rail.** One column a year, 1800 to 2026 — public records by recorded year
from the release's frozen per-record status dataset (`lib/years.server.ts`, its 7,995
checked against the projection's cohort) on a square root; the decades as the units of
choice, the chosen one's columns red, full years at the fifties, short forms between. In
the Temporal layer the window shows itself: the previous and next decades' columns in
cobalt under a cobalt rule, the rest faded, PREVIOUS · CURRENT · NEXT under the three; a
chosen place adds its three counts as a small row beneath. No animation.

**System suggests, on the window.** The context carries eight counts — the period's
public total, the place's records, its rank, the count of recorded geographies, and the
previous and next periods' totals and the place's records in them — and, as labels, the
comparisons those counts state ("share larger than in the previous period"); the model may
voice them, never derive them. The deterministic fallback: "United States accounts for 49
of 1,898 public records in the 1980s, ranking third among 22 recorded geographies. Its
share of the public archive is smaller here than in the 1970s." The gate is unchanged: one
to three sentences, sixty words, no forbidden word, no percentage, no number the context
did not supply, two actions at most.

**Verification.** `npm run test:spacetime-design` (the desktop over the one orchestration,
no fetch of its own; the layer before the style; no Fit; World view gated; the ring form
and the sealed radius; the tier-led level of detail; the three-bar glyph with the current
bar apart and no growth colour; the not-plotted companion; the window on three real
atlases — United States 226 / 49 / 129, ranks 1 / 3 / 2, the United Kingdom's 1,630 of
1,898 at rank 1, the first period without a previous; the guidance gate and fallback).
Browser at 1960 × 1130: the ten states of the previous pass plus the Temporal layer at
world scale and focused. The sealed gates stay green.

**Withdrawal from the product (2026-09-05, the owner's decision).** Spacetime is not released in
v49 because the current archive does not yet meet the geographic and temporal coverage
threshold required for this research surface — not failed, deferred. The research-readiness
census (`docs/frontend/SPACETIME_RESEARCH_READINESS_CENSUS_v1.md`; `scripts/spacetime/`) found
the archive steep: of 93 governed geographies only 8 pass a STRICT research gate and 7 more a
RELAXED one, and before the 1890s no decade has more than two geographies with five records. A
world map of every governed geography would draw a coverage the archive does not have. What
changed, and only this: the TRACE landing keeps the Spacetime screen — its timing, its place in
the sequence, the instrument's map and tapes — but the note now reads *A research direction
under review* with the owner's two sentences and the status NOT AVAILABLE IN THIS RELEASE, and
has no control, no link and no leader line; the dock (landing and shared) carries the two
released views; "Three research views" became "Two research views"; the baseline ledger states
the release boundary instead of figures; `/trace/spacetime` is a text boundary page that imports
no workspace, GIS, reader or guidance; the exploration reference view and the homepage no longer
link or name it as available; the System Suggestions public path answers `TRACE_SPACETIME` with
`SURFACE_NOT_RELEASED` (404) while the service and its gate stay. Untouched, as frozen research
infrastructure: `features/trace-v49/spacetime/*` (GIS, governed readers, read API — still served
under `/api/v1/releases/{release}/trace/spacetime/*`), the generated projection and its audits,
the desktop workspace files of this section, the design and runtime tests (the design test and
the suggestions-UI test now describe a surface that is not mounted and are not part of the
release gate), and the census. Reopening Spacetime is a governance round over the census's
registry, not a frontend change.

## 7i. Exploration — a bounded generative visual explorer (2026-09-06)

**The product (the owner's).** *Choose one starting point. MGDA generates a governed
exploratory view from validated associations. You may reveal more or less complexity or
move to another permitted view; the underlying tree, associations and map remain
system-defined.* Exploration is not a graph editor and not a research inspector: the
picture is the product, the description reads it. The user does four things — choose a
starting point, make the view simpler or richer, ask for another view, export the
stamp — and nothing else: no adding a term, deleting a node, drawing an edge,
drag-to-connect, choosing an association, a topology, a tree or a position, editing a
relation, tuning confidence, composing concepts or generating a node.

**The data is V2, and it is small.** The active authority is the Round 16A Exploration
V2 production read model (`generated/trace-exploration-v2/production-read-model.json`)
and its state machine; V3 is a fail-closed research schema with no active product
state and is never read. The census (2026-09-05, confirmed by the owner's independent
recount): 4 categories; 81 category entries with only 10 distinct labels — category ×
topology slots, not words; 31 vocabulary terms of which 26 seed a composition and 5
have no qualified association; 21 pair associations; 228 compositions of 2 / 3 / 4
terms (42 / 162 / 24), 45 distinct by node-and-association set; 5,760 states whose
visible term count is only ever 2, 3 or 4 (1,080 / 3,528 / 1,152) — the interface's
"8" is a ceiling the data never reaches; 120 distinct pictures by visible terms +
associations + focus. A real MORE (a legal EXPAND that adds a visible term) exists in
1,032 states, always with exactly one target; a real LESS in 2,160 (in some the
smallest legal reduction removes two terms); 2,664 states can go neither way. The
product accepts this as a small, exact combinatorial system and does not inflate it.

**The service (`features/trace-v49/exploration-view/`, API
`/api/trace/exploration-view/v1`).** A view layer over V2 that never adds a term, an
association or a transition and never touches the frozen V2 renderer, controller,
service or derivations (byte-identical to HEAD; the sealed export ledger still
replays). Starting points are the 26 seed WORDS, grouped by governed category; a word
resolves to a governed initial state — the entry's initial state, then one
SELECT_COMPOSITION when the canonical composition is another (six words have no
canonical entry; the resolver also prefers a root with a real More, stable id as the
tie-break). MORE / LESS are offered only when a legal V2 transition changes the
visible count, resolved server-side through the transition index (the smallest
change first); ANOTHER VIEW rotates deterministically through the distinct pictures
of the same category and the same `seed_node_id` (never another starting point,
never across categories; a pool of one says SINGLE VIEW). Every view restores from
`map · state · template · variant` byte-identically; the same input renders the same
bytes; a stale hash or another map's state is refused.

**Content state × presentation state.** Two states, kept apart: V2's content (starting
word, composition, visible terms, associations, complexity, focus) and the
presentation (template, variant, seed). Eight templates — pure graphic, no word
inside the picture — replicate the owner's reference stamps in form and extend them:
DOT ROWS (France 1985 Télévision: rows of alternating dots, one row a term, a row of
black-and-grey pairs an association), SPOTS (South Africa R10: a lattice of large
spots in a stepped colour sequence, a column a term, an association row keeps only
its two columns), CHEVRON BANDS (Germany 1973: a band a term, an association the
cross-hatch where two bands meet), CROSS FIELD (Canada 1983: a halftone of crosses
whose size follows the terms' cross-shaped figures and the corridors between
associated terms), LINES AND BARS (Sweden 2026: thin lines, a band of bars a term, a
shared row of short bars an association); MODULAR GRID (Venezuela 1975: the focused
term a three-cell circle cut by the grid, other terms quartered circles, an
association a path of rings), RAYS (the Bundespost homage: a sector a term, an arc
band an association), OVERLAP (its translucent panels: an association is an
overlap). Each has three variants; positions, sizes, bar lengths, dot radii and
colours are fixed tables and the seed — never confidence, strength, support status or
evidence; nothing means direction, cause, chronology or importance. Template and
variant are selected by a deterministic seed (FNV-1a of state hash and salt); More /
Less keep the treatment; Another view moves to the next compatible template. The
page's SVG and the PNG are one scene; the export adds only the stamp's furniture
(issuer, term count as the denomination, the starting word as the caption, a tiny
provenance line) under its own render version `trace-exploration-stamp-png-v1`
and export id `TEP1-…`; the frozen v2 export (`portrait-png-v2`, `TEV2-…`) is
untouched.

**The page (`/trace/exploration`, desktop; the Context Canvas register).** LEFT RAIL:
STARTING POINT as one unmistakable state — the word, its category, CHANGE — then
COMPLEXITY (− · n terms · +, each step disabled with the view's own boundary: *This
view is at its richest / simplest*), ANOTHER VIEW (*View n of m for this starting
point* / *A single view*), EXPORT PNG, and at the foot the secondary entry OPEN
INQUIRY · 11. CHANGE enters a selection state: the rail becomes one task — the 26
words in four governed groups, the current word filled, marked ✓ CURRENT and not a
candidate; available words plain on a hairline; hover / keyboard focus inverted with a
leading mark; disabled greyed — with KEEP CURRENT STARTING POINT to leave; Complexity,
Another view, Export and the inquiry entry are hidden until a word is chosen. BODY:
the stamp, inline, pure graphic, with a status line. RIGHT: DESCRIPTION, open when a
view is first generated; once the reader closes it, More / Less / Another view leave
it closed; the dock's one tool is Description. Its order: SYSTEM SUGGESTS in its own
bounded card (the reading entry; narration only, no action — the rail carries the
controls) → WHAT IS SHOWN (the exact terms and association pairs the V2 state
supplies, the deterministic counterpart) → PRESENTATION (template · variant; layout,
colour, scale and position carry no historical meaning) → TECHNICAL PROVENANCE,
folded. Open Inquiry is a right drawer, never a peer mode: it begins, in order, with
*Open inquiry* · *Evidence remains incomplete.* · *This is not a validated historical
association.*, then the eleven questions as an index, one at a time, with its own
bounded System suggests at the foot; nothing from it enters the view, its
controls, its candidates or the export.

**System suggests, an association narrator.** For `TRACE_VALIDATED_EXPLORATION` and
`TRACE_OPEN_INQUIRY` only: one or two sentences, forty-five words, from the visible
labels, association pairs and counts alone; no cause, influence, chronology,
sequence, diffusion, hierarchy, importance, strength or confidence — a disclaimer may
name a claim only to deny it (*without asserting influence, sequence or causation*;
*rather than causal or directional*); no unsupplied number, no percentage; at most one
action, and the page asks for none. The deterministic fallback narrates the visible
structure: *Propaganda is shown here alongside exhibition and trade through two
evidence-qualified generic associations. These connections are exploratory rather
than causal or directional.*; the inquiry fallback: *This inquiry considers a bounded
question between … ; it remains outside the validated graph because its evidence is
incomplete.* Global provider, model and the other surfaces are unchanged.

**Verification.** `npm run test:exploration-view-v1`: the 26 starting points resolve
to their own seed (the six two-step words included, the five isolated words refused);
over all 5,760 states More / Less availability equals the existence of a legal
transition that changes the visible count and applying them changes it by the
smallest legal step; Another view keeps the starting point and the category, cycles
the deduplicated pool and returns to the first picture; restore is byte-identical;
every template × variant lays out 2-, 3- and 4-term views inside the field with no
word in the view and the furniture on the export; the PNG is 1080 × 1620 from the
same scene; the frozen v2 files are byte-identical to HEAD and three sealed export
rows replay; the page reads no V3 and exposes no raw action; the narration gate. The
existing gates (`test:trace-exploration-v2`, `test:system-suggestions`,
`test:read-platform`, the canvas design test, hygiene) stay green.

**Copy pass (2026-09-06, the owner's P0–P2).** No engineering language and no repeated
information on the surface: the rail's statement is two sentences; the starting point is
the word, its category and CHANGE; the selection state says *Keep current*; the complexity
notes are *Simplest available view.* / *Richest available view.* / *The only available
size.*; the export is *Export current view* with the size as weak metadata; the status
line is *word · n terms · n associations*. In DESCRIPTION, System suggests narrates one
concrete sentence about this picture and the fixed boundary sits once beneath it
(*Associations shown here are exploratory, not causal or directional. The view is
generated from validated associations; its structure is system-defined.*); WHAT IS SHOWN
is the counts and the exact pairs, once; PRESENTATION is *template · variant* and *Layout
and styling are presentational only.* Open Inquiry cards read *n terms · Open inquiry*;
the relation form and the inquiry id live under Technical provenance; the evidence gap
and source boundary are product sentences.

**Verification suite (2026-09-06; `npm run verify:exploration-presentation-v1`, outputs
in `docs/qa/exploration-presentation-verification-v1/`).** Proves the eight templates are
deterministic, state-conditioned generation. The presentation FINGERPRINT
(`exploration-view/fingerprint.ts`) hashes the generated structure only — template,
variant, ground, every primitive's kind, role, coordinates, dimensions, radii, path,
rotation, opacity and inks, the terms' and associations' regions — never a word, title,
export id, provenance string or seed. White-box gates: identical input → identical
fingerprint and SVG; every real More transition changes the geometry; every pair of
distinct root pictures within a starting point's pool differs; the eight templates give
eight fingerprints and eight grammars on the same state while the research state, terms
and associations stay identical; every variant differs, research identical; no
Math.random / Date / performance / environment in the presentation path; the export
line changes only the furniture; an unknown template, variant or state fails closed;
eight distinct layout functions; the page's SVG and the export derive from one scene.
Black-box, on the running server: 3 governed states (design diplomacy's 2 → 3 → 4
ladder) × 8 templates = 24 views, five page reloads each with one SVG hash equal to the
API's, five PNG exports each with one SHA-256; the S4 variants; pHash and SSIM over
every template pair per state and every variant pair — an exact or pHash-identical
pair is a hard failure, SSIM > 0.9 or pHash ≤ 6 a review flag for the owner's eye, never
a verdict. Metamorphic: same state / other template keeps the research and changes the
picture; same template / other state (the owner's LINES pair, and the ladder) changes
the picture within one grammar; More / Less are server transitions with the presentation
regenerated from the returned state; Another view keeps the starting point and never
repeats the previous picture. The suite exposed one defect, fixed in this round: the
templates had reduced the state's seed through small moduli, so different states with the
same term count could collapse onto one picture (6 of 66 pool pairs; the owner's
production-site / material-displacement LINES pair); every template now draws many
independent bits of the seed (`pick(seed, salt, n)`), and the gates hold with no
change to any template's grammar.

**Second visual engine (2026-09-06; the owner's "视觉细节和视觉算法的重构").** The
owner's critique of the first engine: the templates lacked surprise and detail (the
references have gradients and grain, which the first engine had refused); the view sat
as a stamp-minus-text instead of a full-frame picture; variants only recoloured (the
suite's SPOTS/0~1 and CROSSFIELD/0~2 review flags); the grammar counted primitives
without spatial relation; the layout was coupled to the term count. The rebuild:

- *Structural engine* (`exploration-view/skeleton.ts`). For n terms a SKELETON FAMILY
  is chosen from n and the variant — 2: opposed / diagonal / stacked; 3: triangle /
  chain / arc; 4: clusters / diamond / run; 5–8: ring / rows / spiral — then bent by the
  state's SEMANTIC FIELD (radial / shear / lattice, kind, strength and sign read from
  the semantic hash; clamped to 8 % margins), then jittered by the presentation seed
  (`pick(seed, salt, n)` per parameter, FNV-1a of state hash + template:variant in
  `seed.ts`). The variant is STRUCTURAL: it changes the skeleton family and the
  CONNECTION MODE an association's shape runs in (direct / orthogonal elbow / arc) and
  the field's density — never only the inks. The owner's fourth layer (force-directed
  by association density) was not built: with n − 1 associations in every V2 state the
  density is degenerate, and drawing more would fabricate edges. No template draws a
  connector that is not a visible V2 association (gated).
- *Sixteen templates* (`templates.ts`), each a pure-graphic idiom drawn on the
  skeleton's positions, with gradients (`SceneDef` linear / radial) and a grain
  (feTurbulence, fixed seed, one 240 px tile repeated as a pattern so the filter is
  rasterised once, not per frame): DOTS, SPOTS, CHEVRON, CROSSFIELD, LINES, GRID, RAYS,
  OVERLAP (rebuilt) + HALFTONE, STRIPES, PETALS, WAVES, CUBES, ARCS, MOIRE, SCATTER.
  The field responds to the terms (denser, larger, warmer near a motif); the association
  is the shape two motifs share, laid along the variant's route. Gradients and grain
  are allowed inside the Exploration picture from this round (the reference stamps carry
  them); the site's §2 rule stands elsewhere.
- *The view is the picture* (`render.ts` `renderExplorationViewSvg`): the 840 × 1120
  frame alone, centred and as large as the sheet allows, flat — no paper, no
  furniture, no word, no shadow, and nothing in it changes on hover or click (the
  owner: view 不需要 drop shadow，hover 也不需要有变动). What answers the pointer is
  the CURSOR alone (`desktop/StageCursor.tsx`): over the stage the system pointer is
  hidden and a drawn cursor — a ring and a dot — follows it on the animation frame;
  over a term's motif the ring opens and four corners appear in the motif's ink, over
  an association's shape it becomes a crosshair, near the picture's edge it contracts,
  with the button down it shrinks. It never flickers: a GEOMETRIC DEADZONE (a term or
  association counts only inside its own region rect, never on a stray primitive), a
  STABILITY GATE (a new reading must hold 70 ms before the cursor changes) and a
  CROSSFADE (the parts fade out and in). Fine pointers only; reduced motion drops the
  ease; the element takes no pointer events and is hidden from assistive technology. No
  region outline ever reaches the page (线框不至于暴露到前端); the terms' and
  associations' regions stay in the SVG as invisible data for the tests and the cursor.
- *The page opens on design diplomacy drawn as the modular grid* (`page.tsx`
  LANDING_TEMPLATE): the largest governed pool, in the treatment of the owner's
  reference picture; a restored URL or a named start keeps its own presentation. (The
  owner tried production for its contrast and asked for the page to be restored the
  same day.)
- *Five export forms* (`forms.ts`, `renderExplorationExportSvg`, PNG at the form's
  size): the owner's five reference stamps replicated in form — Télévision 1985
  (1400 × 980, inset frame, serif), South Africa R10 (900 × 1800, wave edge, label box),
  Germany 1973 (1400 × 900, black ground, capitals block, red number), Canada 1983
  (1200 × 1000, cream, rotated number and issuer), Sweden 2026 (1100 × 1450, mono) —
  with the archive's identity in the issuer's place: the MGDA block, the number of terms
  alone as the denomination (the owner: 不要叫 2 terms，直接 2), the starting word as
  the subject, TRACE as the postal mark, and, so the sheet is a research product, the
  LEDGER — the terms shown, the associations drawn as pairs, the category, the
  presentation (template · variant), the release and the export id. No hash, no date.
  Text and picture never share ground: the picture takes the image area, and the image
  area spans at least 80 % of the paper's width or height on every form (the owner's
  "full width or full height" for the PNG, measured; the acceptance test holds the
  line), the number of terms is a hint in the text area (the German form's
  red corner mark, never over the grid — the owner: 图形是最大展示，terms 数量仅作为
  hint), and every furniture line is MEASURED (`estimateTextWidth`, a conservative
  advance per face) and WRAPPED to its column (`flow`, at the ledger's separators;
  upright lines advance down, the South African form's rotated lines advance in
  columns). The acceptance test lays out every distinct picture (45) on every form
  (225 layouts) and fails if any line leaves the paper, stands on the picture, crosses
  the frame line or overlaps another line. The PNG is rasterised at EXPORT_SCALE = 2
  (Télévision 2800 × 1960, South Africa 1800 × 3600, Treaty 2800 × 1800, World Council
  2400 × 2080, Streaming 2200 × 2900) — the owner's 导出精度需要提高.
  Each template is matched to one form (`EXPLORATION_FORM_OF_TEMPLATE`: 3–4 templates
  per form); the export re-lays the same template, variant and seed for the form's
  image area, so the picture and the stamp share one skeleton and one set of
  associations while the frame differs. The manifest carries `form_id`, `form_name`,
  `dimensions` and the `seed_chain`; the rail's export note reads *form · PNG w × h*
  from the presentation DTO.
- *Verification suite, second edition.* The fingerprint now covers the frame and every
  definition; the grammar adds the terms' spread. New white-box gates: every variant
  moves the terms (> 30 px mean) — `variant_is_structural`; between term counts the
  shared terms move > 30 px — `topological_phase_transition`; two states of one count
  under one seed lie differently and inside the margins — `semantic_field_bends_skeleton`;
  connectors equal the state's visible associations exactly — `no_fabricated_edges`;
  the seed chain derives as documented — `seed_chain_derivation`; sixteen distinct layout
  functions. Black-box: 3 states × 16 templates = 48 views (five reloads, five exports,
  form and dimensions checked), the S4 variants, a 12-request export burst against the
  render limiter (MAX_IN_FLIGHT 4 → 429 REQUEST_LIMIT_EXCEEDED, byte-identical 200s,
  recovery), a view-weight budget (≤ 400 KB, ≤ 6,000 primitives per picture). The
  REVIEW class is gone; the ACCEPTABLE VISUAL DELTA is a hard threshold per kind,
  measured on the view pictures (not the furnished exports): same state / other
  template SSIM < 0.90 and pHash > 0; same template / other state SSIM < 0.65; same
  state / other variant SSIM < 0.85; golden image SSIM ≥ 0.99. Goldens: the 48
  variant-0 view pictures under `docs/qa/exploration-presentation-verification-v1/golden/`
  (declared Git LFS in `.gitattributes`; `EXPLORATION_GOLDEN=update` rewrites them). The
  matrix (`visual-generation-matrix.json`, format v2) records `layout_seed_used`,
  `skeleton_family`, `semantic_field` and `term_anchors` per entry; the contact sheets
  are `exploration-48-view-contact-sheet.png` and `exploration-export-forms-sheet.png`.

## 7j. System Suggests — release-readiness pass (2026-09-06)

**Scope.** The four active surfaces — SEARCH_RESULTS (1–2 sentences, ≤ 45 words, 0–2
approved refinements), TRACE_CONTEXT (0–1 real action), TRACE_VALIDATED_EXPLORATION
(narration only), TRACE_OPEN_INQUIRY (0–1 reading action). TRACE_SPACETIME stays deferred:
the public path answers 404 before any provider. The label is *System suggests* everywhere;
the model and provider are described on About / Methodology only; no avatar, no history,
no input box. 45 words is a ceiling, never a target.

**Facts, not words.** Request schema v2 (`features/system-suggestions/schema.server.ts`):
the page names its state — Search: query + filters, with the count it shows; Context
Canvas: the object and the governed representation ids on the canvas; Exploration: the
map and state; Open Inquiry: the inquiry id — and the server resolves the facts from the
authoritative reader (`facts.server.ts`: the public Search service, the governed Context
projection, the Exploration V2 map through the view service, the Open Inquiry registry),
checks the shown counts against them, and builds STATEMENTS (deterministic sentences with
ids), the labels and pairs the note may name, the counts it may state, the actions the
page can really take, and one fingerprint over all of it. Only public-safe fields enter.
A v1 TRACE context that describes its own facts (the frozen reference workspaces) is
answered deterministically and never reaches a model.

**The model expresses; the system owns facts and actions.** The model receives the
statements, labels, counts and the allowlist and returns `note`, `used_fact_ids`,
`suggestion_ids`. The gate (`assertFactualNote`) re-reads the note against the facts:
every number a supplied count; every quoted term a supplied label; a sentence that pairs
names exactly one shown pair (A—B and B—C never A—C; a chain never a star); no source or
record counts; no weak / strong / similar / semantic / co-occurring; no promise of what a
refinement will find; nothing set aside or not recorded called missing, absent or never
existed; no likely / possible / validated framing of an inquiry; no cause, influence,
sequence, history. A note that fails falls back to the deterministic note from the same
facts — never a trimmed model sentence. Exploration's single pair reads *In this view, X is
paired with Y.*; WHAT IS SHOWN remains the exact ledger, and each pair carries the program's
*View association details* entry (endpoints, the public basis, *Source details are not
public in this release.*). The Open Inquiry disclosure is fixed UI text in its order.

**Provider.** DeepSeek Responses, `deepseek-v4-flash`, `reasoning.effort: none`, temperature
0 (a 0.2 comparison through `SYSTEM_SUGGESTIONS_TEMPERATURE`), `max_output_tokens 512`, no
tools, no streaming, strict JSON schema, `store: false`, timeout 2.5 s (cap 5 s). Only
assistant message `output_text` parts are read; reasoning items are skipped; an error,
incomplete or empty response fails closed with its own status; 429 is rate-limited. Zero
suggestions is a legal answer; the ceilings are per surface.

**Cache.** Key = surface · release/data version · context fingerprint · prompt version ·
language · model configuration; 500 entries, Search 5 min, governed surfaces 30 min;
in-flight requests for one key merged; a last-good copy (6 h) answers a provider failure for
the same facts; the panel drops any answer that is not its latest request's. A template
change is not a new key; the same four words with other edges are.

**The live Search window** (`app/search/desktop`) now runs on the public search API —
results, exact counts, cursor paging, the live dictionaries and year range — and asks the
shared endpoint for its guidance with the count it shows; the fixture remains only behind the
mobile ticket, which is outside this desktop pass. The in-process rate limiter (30 per
requester per minute) is not a cross-instance quota.

**Verification.** `npm run test:system-suggestions` (41 checks), `npm run
test:trace-system-suggestions-ui` (29), `npm run verify:system-suggestions-release-v1`
(the matrix: Search, Context Canvas, Validated Exploration, Open Inquiry, input and safety,
provider, cache and race, product boundary, the dev server; 86 cases → `docs/qa/
system-suggestions-release-v1/system-suggests-test-cases.jsonl` and
`SYSTEM_SUGGESTS_RELEASE_REVIEW.md`), `npm run verify:system-suggestions-live-v1` (the real
provider on 4 × 5 × 3 = 60 fixed public-safe cases, recording latency, usage, status and the
gated note; SKIPPED with reason when no key is present — never claimed from mock runs).

## 7k. Mobile — round M1 (2026-09-06, the owner's brief after the merge)

From this round on, design work is mobile only; the desktop is frozen at main.
The rules the owner set: every mobile file apart from the desktop's (no width
switch inside one file); the mobile palette a step brighter and more saturated,
the paper a touch whiter; the top bar the monogram tile and three icon controls
only — Index · Search · About — with no wordmark; the Index without annotation
lines, its opening designed, its list lighter; long object titles folded by
default; Search on the live API; About with its own mobile tree, so the desktop
bar with five icons can never appear on a phone, and with the research approach
and the design rationale intact; Source stays inside About on the phone; the
homepage untouched for now.

- *Shell and bar.* `components/site/mobile/MobileShell.module.css` (the mobile
  tokens: paper #fffdf9, blue #2b4cff, red #ff4a2a, yellow #ffcf33, green #33b95e,
  teal #17b0b0, sky #4db6ff, coral #ff8763; the 17 px floor) and
  `SiteNavMobile.tsx` (MGDA tile + Index · Search · About, 48 px tiles; Search
  toggles the window closed as on the desktop). The desktop `SiteNav` no longer
  carries a mobile variant; every mobile root (Home, Index, Search, Object, About,
  the TRACE desktop-required notices) uses the mobile bar and the shell.
- *About.* `app/about/mobile/AboutMobile.tsx`: seven sections on colour plates
  with cropped numerals and line marks — Purpose · Methodology (research approach:
  method prose, pipeline, evidence protocol, design-research note) · Visual design
  rationale (the six references, the type system) · The archive in numbers ·
  Contact & citation (copy buttons; citations built after mount) · Source (the
  desktop /source folded in: overview layers, the register by group, acquisition,
  transformation, rights conditions, evidence status, version and integrity) ·
  Claim boundaries & rights. `about/page.tsx` and `source/page.tsx` split by device
  on the server; `/source` on a phone is the About tree opened at Source.
- *Index.* The opening is one sky plate: the kicker, the count as a numeral cropped
  by the plate's foot, the population line (no annotation line); rows are the title
  and one light line (type · place); the filter sheet unchanged. *Object.* A title
  over 72 characters folds to three lines with a 44 px "Full title" control
  (`MobileTitle.tsx`); the h1 keeps the full text. *Search.* The mobile ticket runs
  on `app/search/lib/live.ts` (results, exact count, cursor paging, live
  dictionaries) and the shared guidance endpoint; the fixture is gone from the
  mobile path. Every mobile stylesheet size below the floor was raised to 17 px.
- *Verification.* `node frontend/scripts/test-mobile-design.mjs` (61 checks: the
  trees import no desktop nav or tree, carry the bar and the shell, About's seven
  sections and its rationale and approach, Search on the live hooks, the Index
  opening, the folded title); in the browser with a mobile user agent: three icons
  and no wordmark on every page, the minimum font 17 px on Home, Index, Search,
  Object and About, the Index numeral clear of its line, Search 508 = the API's
  count with the guidance note, the long title folded, seven plates with marks.

## 8. Rounds

Every round ships **desktop + mobile together**; mobile is designed ground-up per
§4a (own components / CSS, no pre-2026-08-29 mobile carry-over), not retrofitted.

1. **About** — ✅ built (`/about`) + design foundation (tokens, fonts, reset, `SiteNav`). *(Mobile section order + folded Source per §4a — pending; `SiteNav` now takes `variant="mobile"`.)*
2. **Source** — ✅ built (`/source`), academic register, folds by default. *(Brought forward — it was round 9.)*
3. **Homepage** (§7e) — a reading page: 01 Identity · 02 Contribution · 03 Enter the Archive · 04 Research status; dark-grey ground + spot colour, a scroll-driven grid + text↔heading transform on desktop, pared-back stack on mobile. Copy final per §2a. **+ Global Search** — now a **global utility window** (§7d), `Search` nav icon on every page (mobile nav = `MGDA · Index · Search · About`), URL-backed at `/search`; desktop = long ticket, mobile = ticket, System suggests = light contextual annotation. *(Search ✅ fixture-backed; Homepage in progress this round.)*
4. **Object Page** — ✅ desktop (5 layout treatments + content-fit) **and** mobile (single-column, alt-text clamp, folded Source/Provenance, back-to-top). Split into `page.tsx` (server UA device split) + `lib/` + `desktop/` + `mobile/`, per-component files — **this is the template every later page follows** (§6). **Wired to the sealed v49 public projection (2026-09-03):** `page.tsx` reads the record from the governed Search v2 artifact (`getPublicSearchIndex().byId`) and maps it with `lib/fromDocument.ts`; an ID outside the projection is a 404. Medium, description and a source-record URL are not in the public projection and are omitted; no frame ever stands in for an image, on desktop or mobile. Delivery-state wording is provisional (§9H).
5. **Index** — ✅ desktop **and** mobile at `/directory` (§7c): searchable place selector, year range + separate order, theme badges, editorial active-state line, dense year-grouped catalogue, empty/loading/error states. **Wired to the sealed v49 public projection (2026-09-03):** `GET /api/index/v1` serves the reader-facing objects (5,423 of 7,995 public records — §3b) as one compact catalogue built from the Search v2 and reader-eligibility artifacts (`lib/catalogue.server.ts`); the directory files it in pages of 200 with a "show the next" foot. Places are the source-recorded labels (145 values) — verified structured geography is still pending (§3), so the filter is labelled "Place (as recorded)". Themes are the release's eight governed themes. The Index keeps its own earlier setting (serif lede, small theme key, small control bar); only its colours changed (2026-09-03): the stripe is the site's own sky / coral / yellow instead of blue / red / yellow; the theme dots are eight distinct spot colours; the theme key sits under the intro as a three-across strip (a deep-tone cut was tried and withdrawn as too dark and undistinguished).
6. **TRACE entry** (§7f) — ✅ built (`/trace`): five-screen scroll scene on one signal bus, the three icon entries, the closing block; Exploration's reference page moved to `/trace/exploration`. Desktop only by policy; mobile gets the desktop-required notice.
7. **Context Canvas** (§7g) — ✅ built (`/trace/context-canvas`): one selected object on a light-blue plate, three labelled fields (Medium · Theme · Movement) around it, a narrow rail and inspector, the rows folded beneath; the reference's state, persistence and PNG export unchanged. Desktop only by policy.
8. **Spacetime** (§7h) — ⏸ deferred from the product (2026-09-05; not released in v49, see the withdrawal note at the end of §7h); had been built (`/trace/spacetime`): the reading workspace over the sealed GIS — the period rail of 23 decades, the map as the body in cobalt / signal red / mint on the canvas ground, PLACE CONTEXT with the bounded System suggests at its foot, the matching records and the geography table as drawers, the shared TRACE dock; `npm run test:spacetime-design` (49 checks) + the sealed Spacetime gates. *(Mobile → the desktop-required notice, as the canvas.)*
9. **Exploration** (§7i) — ✅ built (`/trace/exploration`): the bounded generative visual explorer over Exploration V2 — 26 starting words, More / Less as real transitions, Another view within the starting point, sixteen pure-graphic templates on a skeleton + semantic-field engine with five reference export forms (2026-09-06 second engine), the Description with System suggests as an association narrator, Open Inquiry as a reading drawer; `npm run test:exploration-view-v1`, `npm run verify:exploration-presentation-v1`.
10. Cross-screen consistency + WCAG 2.1 AA audit + handoff specs; remove/replace legacy routes.

---

## 9. Acceptance

Each round: page(s) build and render at `localhost:8000`; no horizontal overflow;
no title clipping; every control has one unambiguous action; keyboard-operable;
`prefers-reduced-motion` respected; no archive-object imagery; "System suggests"
label only, provider named only on About; fixed backend/API/evidence/rights
contracts unchanged.
