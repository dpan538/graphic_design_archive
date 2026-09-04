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
      ├── Spacetime            (Function 2)
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
| 6 | Spacetime | `/trace/spacetime` | TRACE Function 2 | desktop (mobile → fallback) |
| 7 | Exploration | `/trace/exploration` | TRACE Function 3 — Validated Exploration + Open Inquiry | desktop (mobile → fallback) |
| 8 | About | `/about` | Project identity, methodology, design rationale, citation, claim boundaries | desktop + mobile |
| 9 | Source | `/source` | Full provenance, source-by-source licensing, rights, permissions | desktop + mobile |

Visible label for Function 3 is **"Exploration"**. "Exploration Field" is an
internal engineering codename only.

### Reachability rules

- **Object Page is never a direct Homepage action.** It is reached only *through*
  a function — Search results or Index directory results.
- **Context Canvas / Spacetime / Exploration are reached only via `/trace`**, never
  from the Homepage.
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

TRACE  (+ Context Canvas · Spacetime · Exploration)
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

The browser harness cannot scroll and screenshot a pinned stage and runs no animation
frames while hidden, so the dev hook `window.__mgdaTrace.freeze(sp)` (absent in production
builds) pins the scene at a scroll progress and dispatches one synchronous frame
(`mgda:frame`). Each screen is verified at its hold's midpoint (sp 0.05 · 0.25 · 0.47 ·
0.68 · 0.91) at 1960 × 1130: a screenshot, and three DOM checks — bounding-box intersection
between all visible text boxes, the 24 px distance from every caption to every component
box (`boxesFor` mirrored in the check), and the word count of each paragraph's last line
(Range per word). The foot is checked with the body translated up (`document.body.style.transform`)
and the tagline by comparing `max − 300` (opacity 0) with `max` (opacity 1).

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

## 8. Rounds

Every round ships **desktop + mobile together**; mobile is designed ground-up per
§4a (own components / CSS, no pre-2026-08-29 mobile carry-over), not retrofitted.

1. **About** — ✅ built (`/about`) + design foundation (tokens, fonts, reset, `SiteNav`). *(Mobile section order + folded Source per §4a — pending; `SiteNav` now takes `variant="mobile"`.)*
2. **Source** — ✅ built (`/source`), academic register, folds by default. *(Brought forward — it was round 9.)*
3. **Homepage** (§7e) — a reading page: 01 Identity · 02 Contribution · 03 Enter the Archive · 04 Research status; dark-grey ground + spot colour, a scroll-driven grid + text↔heading transform on desktop, pared-back stack on mobile. Copy final per §2a. **+ Global Search** — now a **global utility window** (§7d), `Search` nav icon on every page (mobile nav = `MGDA · Index · Search · About`), URL-backed at `/search`; desktop = long ticket, mobile = ticket, System suggests = light contextual annotation. *(Search ✅ fixture-backed; Homepage in progress this round.)*
4. **Object Page** — ✅ desktop (5 layout treatments + content-fit) **and** mobile (single-column, alt-text clamp, folded Source/Provenance, back-to-top). Split into `page.tsx` (server UA device split) + `lib/` + `desktop/` + `mobile/`, per-component files — **this is the template every later page follows** (§6). **Wired to the sealed v49 public projection (2026-09-03):** `page.tsx` reads the record from the governed Search v2 artifact (`getPublicSearchIndex().byId`) and maps it with `lib/fromDocument.ts`; an ID outside the projection is a 404. Medium, description and a source-record URL are not in the public projection and are omitted; no frame ever stands in for an image, on desktop or mobile. Delivery-state wording is provisional (§9H).
5. **Index** — ✅ desktop **and** mobile at `/directory` (§7c): searchable place selector, year range + separate order, theme badges, editorial active-state line, dense year-grouped catalogue, empty/loading/error states. **Wired to the sealed v49 public projection (2026-09-03):** `GET /api/index/v1` serves the reader-facing objects (5,423 of 7,995 public records — §3b) as one compact catalogue built from the Search v2 and reader-eligibility artifacts (`lib/catalogue.server.ts`); the directory files it in pages of 200 with a "show the next" foot. Places are the source-recorded labels (145 values) — verified structured geography is still pending (§3), so the filter is labelled "Place (as recorded)". Themes are the release's eight governed themes. The Index keeps its own earlier setting (serif lede, small theme key, small control bar); only its colours changed (2026-09-03): the stripe is the site's own sky / coral / yellow instead of blue / red / yellow; the theme dots are eight distinct spot colours; the theme key sits under the intro as a three-across strip (a deep-tone cut was tried and withdrawn as too dark and undistinguished).
6. **TRACE entry** (§7f) — ✅ built (`/trace`): five-screen scroll scene on one signal bus, the three icon entries, the closing block; Exploration's reference page moved to `/trace/exploration`. Desktop only by policy; mobile gets the desktop-required notice.
7. Context Canvas.
8. Spacetime.
9. Exploration (Validated Exploration + Open Inquiry, hard separation).
10. Cross-screen consistency + WCAG 2.1 AA audit + handoff specs; remove/replace legacy routes.

---

## 9. Acceptance

Each round: page(s) build and render at `localhost:8000`; no horizontal overflow;
no title clipping; every control has one unambiguous action; keyboard-operable;
`prefers-reduced-motion` respected; no archive-object imagery; "System suggests"
label only, provider named only on About; fixed backend/API/evidence/rights
contracts unchanged.
