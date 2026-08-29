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

## 3. Information architecture — nine pages

| # | Page | Route | Core purpose | Platform |
|--:|------|-------|--------------|----------|
| 1 | Homepage | `/` | Brand entry + Search (expandable window) | desktop + mobile |
| 2 | Index | `/index` (final path TBD) | Region/Country · Year · Theme directory browsing, year-ordered | desktop + mobile |
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
- **Mobile:** wordmark + Search + About are primary; TRACE resolves to the
  desktop-required fallback (which links back to Search) before importing any
  TRACE runtime. `SEARCH_CLIENT_BUNDLE_TRACE_IMPORT_COUNT` stays `0`.

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

- **One route = its own `page.tsx`.** Page composition may be split into sibling
  components in the route folder (e.g. `about/AboutView.tsx`).
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

## 7a. Source page — content architecture

An **academic reference appendix**, not a second About. No project vision,
audiences, Search/TRACE explainer, full claim-boundaries, AI method, design
essay, or the four citation formats — those stay on About, reached by a link.
Restrained visual register: **no full-colour plates**; numbered sections with a
coloured header rule; colour used functionally on section rules, source-type ×
project-role tag chips, and status chips. **The page must fold by default** —
large blocks are `<details>` collapsed.

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

## 8. Rounds

1. **About** — ✅ built (`/about`) + design foundation (tokens, fonts, reset, `SiteNav`).
2. **Source** — ✅ built (`/source`), academic register, folds by default. *(Brought forward — it was round 9.)*
3. Homepage + Global Search (expandable window, URL state) + shared state components.
4. Object Page (text + citation, history-preserving).
5. Index (Region/Country · Year · Theme, year-order) — pending data-source confirmation.
6. TRACE entry + mobile fallback + desktop shell.
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
