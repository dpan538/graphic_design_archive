# Homepage design — pinned split-screen (v1)

Supersedes the visual system described in `FRONTEND_DESIGN_DECISION.md` §7e
(linear scroll, single spot-colour band). §7e now points here. Positioning,
canonical statement, and scope/history figures are unchanged and still live in
§2a — this document is layout, motion, and colour only.

Status: **approved, not yet implemented.** Desktop only. Mobile stays frozen
on the existing `HomeMobile` build until this desktop design is finished and
validated, then mobile is re-derived from it as its own round.

---

## 1. Architecture — pinned left nav / right pane

One pinned block (`ScrollTrigger`, `pin: true`) spans all four sections.
Inside it:

- **Left nav** — fixed for the whole pinned block. Ground colour is the
  constant hero colour `#3c4242` (`--hero-bg`), never swapped. Lists the four
  section names (01 Identity · 02 Contribution · 03 Enter the Archive · 04
  Research Status); the active section's label takes its assigned accent
  colour (§3), the rest sit dim on `--hero-dim`.
- **Right pane** — content swaps **per section**, discretely, not a
  continuous crossfade across the whole pinned range. Each section owns its
  own background (§3) and its own **inner** scroll-scrubbed sub-animation
  that plays out while that section's slice of the pinned scroll range is
  active. Section-to-section is a page-switch (short transform, not a scrub);
  within a section, motion is continuous scrub.

Implementation shape: a single `ScrollTrigger` on the pinned container
computes overall progress 0→1; that range is divided into four slices (weights
uneven — Contribution's slice is the longest, since it carries the most
sub-animation); each slice's local 0→1 drives that section's own GSAP
timeline / Three.js scene state. Crossing a slice boundary triggers the
discrete section-switch transform. `prefers-reduced-motion`: no pin, sections
render as an ordinary stacked column, all inner sub-animations replaced by
their resting/final frame.

---

## 2. Colour system

Two grounds only, everywhere on the page:

| Token | Value | Use |
|---|---|---|
| `--hero-bg` | `#3c4242` | Left nav (always). Identity's right pane (section 01 only — it shares the left nav's ground since it's the first screen). |
| `--hero-text` / `--hero-dim` | `#faf7f0` / `#f0e8d5` | Text on `--hero-bg`. |
| *(new, page-scoped)* `--contrib-top` | ≈ `#fbfaf7` (near-white; sample-match against the reference swatch when built) | Contribution's upper card. |
| *(new, page-scoped)* `--contrib-bottom` | ≈ `#1f4b73` (deep steel blue; sample-match when built) | Contribution's lower panel. Distinct from `--hero-bg` — not a reuse. |

Sections 03 (Enter the Archive) and 04 (Research Status) right-pane
background colours are **open** — not yet designed. Default to `--hero-bg`
until that round; revisit when those two sections get their own design pass.

**Accent colours** — reused from the existing global palette
(`globals.css`), two disjoint roles, never used as a fill:

- **Nav-title colours** (one per section, text/underline only):
  01 Identity → `--sky` · 02 Contribution → `--green` · 03 Enter the Archive →
  `--coral` · 04 Research Status → `--yellow`.
- **Marker colours** (small in-content marks only — a chart tick, an
  underline, the 3D highlight point): `--pink` and `--teal`, brightened
  slightly if they read too muted against `--contrib-bottom` when built.

---

## 3. 01 · Identity

**Superseded.** The Identity section's built behaviour is specified in
[`HOMEPAGE_IDENTITY_SEQUENCE_v1.md`](HOMEPAGE_IDENTITY_SEQUENCE_v1.md) —
gallery → spheres → grid → black → MGDA, with a pinned layer that never
translates. The word-mining description below was the earlier concept and is
kept only for the marks' provenance (the underline/circle phrases still come
from `IDENTITY_MARKS`).

<details><summary>Earlier concept (not built)</summary>


First screen. Right pane on `--hero-bg`, matching the left nav.

**Resting state:** the name ("Modern Graphic Design Archive") large, as now.
Below it, the two existing paragraphs (`IDENTITY_P1` / `IDENTITY_P2`,
unchanged copy) at **28px**.

**Inner scroll (scrubbed):**

1. Both paragraphs shrink continuously 28px → 18px.
2. As they shrink, three verbatim phrases already inside `IDENTITY_P1` get
   marked, mixed treatment (not all one style):
   - "verified records" — **underline**
   - "explicit provenance" — **circle** (hand-drawn-style stroke, drawn in
     via `stroke-dashoffset` as the scroll passes this point)
   - "evidence-bounded computational research" — **underline**
3. Continuing to scroll, the marked phrases animate off their in-paragraph
   position to a new, larger-set line beneath the (now small, dimmed)
   paragraphs — position-interpolated (measured start/end rects, driven by
   scroll progress, not a one-shot Flip) rather than reflowed instantly. Each
   phrase's circle/underline fades out once it settles into the new line.
4. The assembled line reads exactly the extracted text, unedited:
   **"Verified records. Explicit provenance. Evidence-bounded computational
   research."** — set larger, in the marker blue (`--teal`, the lighter
   reference swatch, ≈ `#7a9bd6` sample-matched at build time), as the
   section's closing statement.

No new copy is introduced anywhere in this sequence — the recombined line is
a literal subset of the already-approved paragraph text.

Known implementation risk: step 3 needs accurate rect measurement and a
resize listener; ship a first working pass and refine the timing/easing by
eye rather than expect to land it in one iteration.

</details>

---

### 3.1 Identity v2.1 (September 2026)

Rebuilt as "six ways to draw a circle" — see HOMEPAGE_IDENTITY_SEQUENCE_v1.md
§F and §F8 for the film, the studies, the serif → sans → bold wordmark and
what was verified.

## 4. 02 · Contribution

**Built as a deliberate visual replication of the Coreaxis reference**, not a
loose interpretation. That reference is the template, and the structure below
follows it directly:

| Reference | MGDA |
|---|---|
| breadcrumb `HOME > SERVICES > …` | **dropped** — it navigated nowhere and cost height the lower half needed |
| heavy uppercase page title | `FROM SOURCE TO ARCHIVE` |
| mono intro paragraph | the scope/limits sentence |
| three bullet + heading + paragraph columns | Reconciliation · Spot-Check & Semantic Review · Governed Publication |
| blue lower half, isometric line drawing left | the year-distribution chart, then the isometric field |
| ruled table right: `01/02/03` italic rows, spacer, italic line, heavy statement, org + year footer | same, with MGDA's own rows; the summary line moved **below** the rows it summarises |

The figure labels (`CANDIDATE RECORDS EXAMINED` etc.) carry `--green-deep`
rather than neutral grey — they name what each number counts, which is the
section's evidence. `--green-deep`, not `--green`: the lighter accent falls
under 3:1 on the paper ground at that size.

The ledger figures (40,000+ / 15,923 / 7,995) sit between the intro and the
columns, on a rule — the reference has no equivalent, but they are the
section's evidence and belong above the fold of the white half.

**Two stages, not a morph.** An earlier pass deformed four bars into stems
and this document described that as faithful; it was not — it was my
substitution for what was asked. The built behaviour is: a **per-year**
histogram (227 bars, one per year 1800–2026, peak 572 in 1979) is drawn,
dissolves completely, and only then is the isometric field drawn from
nothing. They are separate objects and never share a frame.

**The histogram is two layers from one frozen release.** Per year: every
canonical object (faint) and the subset that is public (solid). The unfilled
height between them is what stays held.

Source and rule, both authoritative:

- Data: the canonical candidate payload named by `database/FROZEN_V49.md`
  (sha256 `b16bb015…`).
- Eligibility: v49's own migration rule
  (`database/data-migrations/v48-to-v49/extract.py`) — a surface is eligible
  only where `trace.tier == "source_verified"`; `metadata_supported` and
  absent tiers are held.
- Verified against `expected-baseline.json`: all 15,923 surfaces parsed, tiers
  **7,995 / 2,971 / 4,957 — an exact match**. 7,995 + 2,971 + 4,957 = 15,923;
  held = 7,928. Both chart figures already appear in the ledger above it, so
  the chart and the rest of the site cite one release.

An earlier pass drew a captured → canonical → "publishable" funnel. It was
wrong twice over and is recorded so it is not repeated:

- It **mixed release versions** — captured and canonical came from
  `prefreeze_candidate_v46.sqlite`, which self-documents as *not a final
  public-release dataset*, while the ledger cites v49.
- It **mislabelled a rights disposition as a publication state**. 7,370 is
  IMG03 / `open_candidate` from the v48 visual-rights audit, which states that
  a visible image, API, redirect, IIIF or URL does **not** constitute reuse
  authorization. v49 records positive rights = 0. "7,370 publishable records"
  was a semantic error, not a rounding one.

**The build must be watched, not arrived at.** The scene's draw ranges are
mapped onto the window in which its canvas is actually visible
(`lp 0.40 → 0.98`), not onto raw section progress. Measured against section
progress the build finished at 0.26 while the canvas was not revealed until
0.45 — so the entire draw-from-zero ran invisibly and the reader only ever
met the finished field. The canvas is now revealed **empty**, then fills:

| lp | axis | surface | dots | stems |
|---|---|---|---|---|
| 0.42 | 6 | 0 | 0 | 0 |
| 0.50 | 28 | 1281 | 0 | 0 |
| 0.66 | 28 | 4160 | 183 | 0 |
| 0.82 | 28 | 4160 | 525 | 0.45 |
| 0.98 | 28 | 4160 | 620 | 1.00 |

The dots hold the longest sub-range on purpose — that arrival is the part
worth watching.

**Bin reveal is normalised, not indexed.** `--i` is a *fraction* of the span.
The earlier form compared a raw index against a literal `60`, which silently
scaled every bar from index 60 on to zero: the chart was truncated at a
quarter of its width, and because the 1979 peak sits at index 179 the tallest
bar was among those cut, so the plot also read as far too short. Any future
change to the bin count must not reintroduce a literal here.

The figures (40,000+ / 15,923 / 7,995) are not a separate ledger row — each
one heads its own column, so the three-beat rhythm happens once.

Right pane: two-tier fixed panel, `--contrib-top` above, `--contrib-bottom`
below. Section title colour: `--green`.

**Five contributions, one set, both ends of the scroll.** They were briefly
eight split 5 + 3 across the two chart stages, which left the field stage
sparse and made the two halves read as two different documents. Now: five
claims, set as headings (18px, heading face — they were in the numeral face at
body scale and read as captions), each opening a restrained body as the reader
reaches it, then a closing paragraph. All eight points survive in substance —
exclusion and uncertainty share a heading, reproducibility is carried by the
paragraph.

Proportion: **1:1 at rest**, the lower half growing to 74% by the end, which is
what pays for the larger type down there. Contribution also **holds its opening
state** for the first 20% of its range: the card lands ~9% in, and without the
pause the reader scrolls straight through the one composed frame the section
opens on.

Two measured constraints govern the panel, both learned by getting them wrong:

- **Bodies open, they do not reserve.** Holding their space meant the panel had
  to be tall enough for every explanation before one was legible, overflowing
  the 1:1 rest proportion by 319px. They now open on `--rowsIn`, which is timed
  to track `--grow` — when the two curves diverged, the panel fitted at both
  ends and overflowed by ~100px in the middle.
- **Fill with padding, never with `fr` rows.** `minmax(min-content, 1fr)` rows
  fight each row's own min-content once a body opens; that overflowed 18 of 21
  sampled states. The closed state is filled by row padding that retracts as
  the bodies open, sized from measured slack: 148px closed, 35px open, so 7px a
  side across five rows is always inside budget.

Row closure: the numeral cell is `align-items: stretch`. Sized to its own text
it left every row's right-hand rule stopping partway down, reading as an open
box.

The pinned frame's offset is **measured from the masthead at runtime**, not
assumed. Hardcoded at `4.75rem` it went stale as the header grew to 95px, so
the frame's top 19px sat behind the header and its bottom overran the viewport
by the same 19px — which reads as the whole section sitting low with the title
crowding the top edge.

Optical centring of the white half: `.columnTitle`'s bottom margin has to
retract with its collapsed height. Keeping it left ~18px of dead space under
the last visible ink, so the half measured centred (52/52 by box) while reading
bottom-heavy (62/82 by ink). Ink now balances within 2px at every state.

**Nav jumps are dealt, not scrubbed.** Animating the scroll ran the eased
scrub across the whole span between origin and destination, so clicking
"Contribution" from Identity replayed every intermediate state as a fast
flashback and dropped the reader into a mid-sequence frame. Instead the scroll
lands instantly and the same opacity-free card pull plays. Two things this
must get right, both learned by getting them wrong:

- **The deal window scales with the section's own share.** A fixed slice of
  total progress is 9% of Contribution's range but 72% of Research status's,
  so a jump past a fixed margin landed three-quarters through the short
  sections. Proportional, every section is entered ~10.5% in.
- **Local progress is measured from the END of the deal window**, so a section
  still sliding in shows its REST state. Measured from the section's start, a
  nav jump landed every section ~10.5% into its range — which for Identity is
  past the gallery's exit at 0.09, into the gap before the next beat: a black
  screen. Identity, as the bottom of the deck, lands on its own start.
- **A settle must kill the tween it supersedes.** Otherwise the next tick of
  the superseded tween overwrites the settled value and strands the section
  mid-slide — observed at `--enter: 0.51`.

## 5. 03 · Enter the Archive

Three ways in, stacked. The section's own ground is the first surface — the
title sits centred in it — and three full-width cards are anchored to the
bottom at decreasing heights. **1 : 0.75 : 0.5 : 0.25** counting the ground,
which lands every band on the same quarter of the pane (measured: four bands
of 226px on a 905px pane).

| Card | Height | Ground | Ink | Verb | Destination |
|---|---|---|---|---|---|
| *(the ground)* | — | `#f4e7dc → #ecdccd` | `#3a3833` | — | **Start with what you know.** |
| Index | 75% | `#327b43` | white | *Browse.* | `/directory` |
| Search | 50% | `#765cbc` | white | *Find.* | `/search` |
| TRACE | 25% | `#4d6f9b` | white | *Explore.* | `/trace` |

**One left axis.** The title's ink, each card name, each condition and each
description all start on the same edge (measured: 394.8px for all of them). An
earlier pass put the copy in its own column to use the width; it read as a
second layout rather than one card. The right-hand space is used by letting
the lines RUN — each is a single line at 20px — not by moving text into a
column.

Each card carries a condition ("When you know a period, region, or theme.")
above its description: the condition is what tells a reader whether this is
their way in, so it leads. Verbs are set in the masthead's italic serif
(`--font-statement`), the same voice as *Archive* in the wordmark.

**No ordinals.** Index, Search and TRACE are peers; numbering them would
invent a sequence the product does not have.

**The palette landed between two corrections, in this order.** It first read
**dull**, and the cause was saturation rather than darkness: S 0.30–0.42
against Contribution's S 0.59. Pushing the cards to Contribution's exact
luminance (0.102, i.e. 6.93:1 under white) fixed the dullness and **overshot** —
three saturated grounds at that contrast read as harsh.

The resting values are between: **S 0.34–0.42, white at ~5.2:1** (5.19 / 5.21 /
5.17). Softer than Contribution's blue rather than equal to it — a deliberate
trade of numeric parity with the section above for comfort in a section that is
three full-bleed colour fields. Still real margin over the 4.5:1 the 20px copy
requires; the ~4.9:1 alternative left almost none, and any later change to text
size or opacity would have dropped it below.

TRACE was briefly a pale sand, which forced it to break the white-ink rule to
stay legible (white on it measured 1.32:1) and sat too far from the other two
to read as one set. Blue restores a single rule: **every card is white ink.**
The title on the ground is `#3a3833`, a warm grey rather than black — at pure
black it read harder than anything else on the page.

**The four surfaces are inserted in sequence**, staggered off the SLOT's own
`--enter` value rather than off `--local-progress`. That matters: `--enter` is
1 whenever the section is seated, so the section still rests complete and
readable — an entrance keyed to local progress would leave the cards off-screen
at `lp 0`. Title leads (`--enter` 0 → 0.30), then Index (0.18 → 0.52), Search
(0.38 → 0.72), TRACE (0.58 → 0.92). Verified: at `--enter` 1 the three cards
land on exactly their quarter bands (679 / 453 / 226px above the pane's floor).

The entrance offset and the hover lift share `transform`, so they are composed
in one declaration (`translateY(calc(entrance + hover))`) rather than
overwriting each other.

**The deal window is 55% of a section's share, not 10%.** At 10% this
four-stage insert ran inside 0.15 of a viewport height — too fast to read as a
sequence. At 55% it takes 0.82. The two long sections are unaffected; both are
already capped by `SLIDE_MARGIN`. Nav jumps use `back.out(1.35)` over 1.15s so
a clicked arrival carries the same elasticity as a scrolled one.

**The overshoot is an ease-out-back computed in CSS**, and all three custom
properties it uses (`--in`, `--u`, `--eased`) **must be registered with
`@property`**. Unregistered, they substitute as raw token text, so `--eased`
expands into nested `calc()`s multiplied together — invalid — and the whole
`transform` is dropped to identity, silently killing the entrance. Verified at
`--enter` 0.5: Index reaches 223 against a seated 226, i.e. 3px past its band
before settling.

*Measurement note for anyone verifying this:* `.card` carries a 320ms
transition on `transform`. Sampling positions faster than that reads every card
as already seated and the whole sequence as linear. Disable the transition or
wait past it.

## 6. 04 · Research Status — the mirrored ranked stream (rounds 3–4)

Round 1 (a Three.js point massif on navy) was withdrawn: the particles read
as haze. Round 2 fused two references into a white poster on a cream ground;
the owner's review of it — figure too small, retro, two grounds, end labels
crowded — produced round 3, which is what stands.

### The two references, and what each contributes

| Reference | What it gives plate 1 |
|---|---|
| UK-cities population chart (ranked coloured ribbons) | One ribbon per entity, thickness = quantity, ranked, crossing when rank changes; names at the end in the ribbon's colour |
| "State of the Bots" spectrogram poster | A band mirrored about a horizontal axis; blue at the centre, warm colours fringing it; vertical striations per time column; blurred halation; multiply-mixed colour on a light ground; a quiet caption block |

**The fusion.** One light ground, no card, no canvas on a background. Above
the axis, every PUBLIC record by place; below it, every HELD record by
place. One ribbon is one place, thickness is records per five years
(1900–2026, 26 bins), colour is rank by total. The release's asymmetry is
the composition — the top half is named by United Kingdom, United States,
Norway, Germany; the bottom by Indonesia, Kazakhstan, Bolivia, Algeria,
Peru and the region groups — and no zero is printed anywhere.

### Data → geometry (`lib/statusRibbons.ts`, computed once on the server)

- Source: `data/status-v49.json`, re-extracted in round 2 so each of the
  15,923 records carries its place as an index into the 424-place ledger;
  sources and object types top 25. Reconciles 15,923 / 7,995 / 7,928.
- In range 1900–2026: 14,393 records (7,493 public · 6,900 held). The 1,530
  dated before 1900 are stated in the legend and drawn on the panorama.
- **Fifteen ribbons per half**: named places, then region groups for the
  residual where a prefix gathers ≥150 records across ≥5 places
  ("Latin America +33 places" 935, "E. Europe +21" 692, "Africa +23" 531,
  "MENA +17" 528, "South Asia +6" 280, "SE Asia +9" 234, "East Asia +5"
  204), then one "N more countries" ribbon. Named ribbons give way to groups
  so a half never exceeds fifteen. The public half needs no groups.
- Stacking order per bin: activity over the trailing fifteen years, ties by
  total — the places being gathered in an era rise to the axis, so the braid
  crosses when eras change. Rank 0 sits on the axis.
- Thickness: linear, 1,000 records per half. 1965–69 (1,212 public) and
  1985–89 (1,037) overrun and are clipped at the figure's top edge, exactly
  as the poster's last column runs off its sheet; the first lens caption
  says why.
- Colour: a spectral ramp read from the axis outward — rank 0 blue, then
  teal, yellow-green, yellow, orange, red, magenta, violet for the smallest.
  The largest masses are blue with warm fringes, which is the poster's
  balance. Label text is the ribbon hue pulled 36% toward ink.
- Rendering, SVG only: the SVG is **stretched to its box**
  (`preserveAspectRatio="none"`) so the figure takes every pixel; strokes
  are non-scaling. Layers: blurred copies multiplied underneath (halation,
  σ 12), the bands edge to edge with no outlines, then the same shapes
  filled with a vertical hairline pattern (striae, 34%).
- **End labels at 2026 only.** The 1900 end was built and removed: every
  ribbon starts near the axis there, so thirty leaders fanned from one point
  and the column read as clutter. Thirty labels at 14px on a ≥32-unit pitch
  (23px at the built height) with thin leaders — the one place on the page
  below 17px, at the owner's request, and the lens brings them to 22–28px.
- Short names: last path segment; parent-qualified on collision
  ("Indonesia (SE Asia)", "Brazil (Latin America)"). The same rule names the
  margin's tables. `PLACE_COLOR` carries each ribbon's hue into the margin
  so the tables' bars read as the same drawing.

### Scroll choreography (owner's brief, in viewport-heights `--v`)

Section weight 6.0; `--v = --local-progress × 6`.

| `--v` | Figure | Margin |
|---|---|---|
| 0 → 1.5 | Drawn left → right: a ground-coloured cover retreats, a spectral print-head rides the frontier; the end labels arrive as it lands | blank until 0.5 |
| 0.5 → 1.3 | — | Records by place (32 rows: bar in the place's hue, total, "n public" or **held**) |
| 1.25 → 2.05 | — | Sources, top 25 of 272 |
| 1.5 → 2.25 | **Lens 1** ×2.0 on 1965–69 | — |
| 2.0 → 2.8 | — | Object types, top 25 of 271 |
| 2.25 → 3.0 | **Lens 2** ×1.6 on the public labels | — |
| 2.75 → 3.75 | — | Rights and dating |
| 3.0 → 3.75 | **Lens 3** ×1.6 on the held labels | — |
| 0.5 → 3.8 | — | **Every place · 424** rolls beneath: name, total, share bar in the place's hue; an empty bar is the zero |
| 3.8 → 4.25 | slide to the year panorama (1800–2026, ink/rose dots with glow) | |
| 5.0 → 5.4 | slide to the reading | |

The lens is a scrubbed CSS transform on the chart row (sheet + labels),
clipped by the figure box: a smoothstep per station over 0.25, then a hold.
Station values come from `LENSES` as inline custom properties; registered
`@property` numbers make the multiplication inside `transform` valid. Each
station has a caption in the foot's block (index · id · text), quoting
figures computed from the same data.

### Layout (1960×1130 build)

Plate grid: figure column · margin column (clamp 380–460px). Head rule,
figure 1090×694 (sheet 822×719 incl. axis, labels 260), foot rule with the
caption block and a 3×2 legend. Margin: rotating table slot, then the wall
(27%). Everything on `--ground #f9f8f4`, hairlines `rgba(23,22,26,.12)`,
no boxes, no shadows.

### Verified this round

- Sheet 822×719 on a 1643-wide plate (round 2: 494×617 inside a card).
- 30 labels, no overflow, no truncation, pitch 23.0px; lens 2 shows them at
  22px on a 37px pitch.
- Every text node outside the end labels ≥17px (walked programmatically).
- Draw 0.5: cover at half, head at the frontier; lens 1 at `matrix(2,…)`.
- Region rows fit their slot with short names; wall single column, 9,938px,
  ≈2.6× scroll speed.
- `tsc` clean except the pre-existing `AboutView.tsx` error. A stale
  Turbopack issue ("LABELS_L doesn't exist") survived HMR after the export
  was removed; the dev server was restarted to clear it.

### Round 4 — built from nothing, the strip, the reading

Owner's review of round 3: the cover-reveal was "a little perfunctory";
both figures must grow from nothing; "Positive rights 0 / 0" is not a
figure to show; the panorama's 1965 peak looks abnormal — remove it or
change the form; the strip must fit half a page of scroll with a growth
animation; the reading needs more height; overall, more visual complexity
and better effect.

**The figure grows out of the axis** (`--draw`, 0 → 1 over 1.5
viewport-heights). A first version of this round revealed the bands behind
a spectral "print head" with bars rising ahead of it; the owner's review
called the result cruder and the head a distraction ("the chart grows out of
the horizontal axis — that feeling is weak"). The head and the bars were
removed. What stands:

| `--draw` | What happens |
|---|---|
| 0.00–0.10 | the axis draws itself left to right (`pathLength=1`, dash offset); ticks and grid come up; year labels follow at 0.16 intervals |
| 0.02–0.87 | **the bands grow from the axis one five-year slice at a time.** The whole ribbon set is defined once (`<g id="rb-bands">`) and rendered through 26 `<use>`s, each clipped to its bin's 40-unit column and scaled about the axis (`transform-origin: 0 500px`) by its own eased factor — slice *b* rises at 0.02 + 0.03·b over 0.10. Nothing is revealed; everything is grown |
| 0.14–0.92 | the halation (σ 12 at 0.64, σ 34 at 0.32, multiplied) develops a little behind the growth front — a soft horizontal mask on its wrapper follows the front with an 8% feather |
| 0.80–1.00 | the striae print |
| 0.84–0.97 | the end labels and their leaders light one by one, sliding 10px in |

**The strip** (plate 2, half a page): the year panorama was replaced. One
column a year, 1800–2026 (227), public in blue on top, held in rose beneath,
the split proportional; the column's depth of colour is its record count on
a square-root scale that saturates at 260 — so 1965's 850 is the most
saturated column, not a spike. A decade row above carries 23 totals
(`1960s 1,913`, `1980s 2,185`…), each block positioned over its own years.
Growth: the front crosses the 227 years over 0.5 vh of scroll (`--pg`,
4.1 → 4.6), each column rising from the floor with a 0.12 window; decade
totals light as the front reaches them. Glow is a `drop-shadow` per colour
group.

**The reading** has a page (pages column 250%: figure 1 · strip 0.5 ·
reading 1; stops at −1 and −1.5). Title 50px, intro 22px, terms 20px with
16px row padding; the release row (Release · Anchored · Status · Objects ·
Public / held) moved here from the strip. "Positive rights 0 / 0" is gone
from every plate. The reading's rows come up from `--v` 4.4, so the frame
that holds the strip and the reading together shows a title under the
strip, not a blank.

Verified (frozen states): at draw 0.3 slices 0–6 are full, slice 7 at
0.78, slice 8 at 0.35, slice 10 flat, and the halo mask sits at 15–23% of
the width; at draw 1 every slice is at 1 and the last label is fully lit;
the strip at `--pg` 0.5 has years ≤100 risen and ≥150 flat, and its head,
decade row and year axis all sit inside the plate (an earlier grid column
of `auto` let the head's nowrap text widen the whole plate past the
viewport — fixed with `minmax(0, 1fr)`); stops −1035 / −1552px; `tsc`
clean.

### Round 5 — the wheel, and a viewport lesson

**The wheel.** The blank under the rights facts (the last margin slot)
now holds a radial barcode in the manner of the two references the owner
supplied (a spoked wheel of coloured blocks; a polar stacked bar): one spoke
per place for the 60 largest, decades 1900s → 2020s from the hub outward
(the century before is on the strip), a block wherever the place has
records in that decade, coloured by that decade's commonest object type
(seven named types + other; system names shortened in the legend, full on
hover), runs of the same type merged into one longer block. 321 blocks.
It grows with its slot (`--sp`, 2.85 → 3.45 vh): spokes draw from the hub,
then the blocks come up ring by ring. Its caption is four words — the owner
asked that the chart, not the sentence, be the point.

**Viewport lesson.** Chrome cuts a CSS-transformed SVG group's content at
the SVG viewport edge *before* scaling, so while a slice grew, the bins that
overrun the sheet (1965–69, 1985–89) showed flat tops. The chart SVGs now
run 30% past the sheet top and bottom (`viewBox 0 −300 1000 1600`,
`top −30%; height 160%`) so the overrun stays inside the viewport; the
figure box crops it as before. Verified: axis and the "0" tick coincide
(554px), scaled slices show their true shape.

Two follow-ups from the owner's next look. The halation wrapper had kept
the sheet's box, so above the sheet the overrunning 1965 spike had bands
but no halo — a pale band laid across it; the wrapper now spans the same
30% overrun (−540…3453px at the build, identical to the chart SVG). And
the 2020s block of the strip's decade row, seven years wide and
right-aligned, had run back over the 2010s total; it now starts at its own
year and runs 6px into the plate's padding instead. Decade figures are
tabular with −0.02em tracking; 23 blocks, no overlaps.

### Round 6 — smoothness and spring

Owner's review: the scroll still stuttered in places; wanted the elastic
motion coordinated and the reading calmer.

**Where the frames went.** Every scroll frame changed `--local-progress`,
and in plate 1 that repainted the figure's SVG: 26 clipped `<use>` groups
× 30 paths with `mix-blend-mode: multiply` (780 blended draws), and the
halation wrapper's moving mask repainted the two blurs (σ 12, σ 34) with
it. During the strip's growth the `drop-shadow` filters inside the SVG
re-ran on 454 column transforms.

**What changed.**
- The growth slices are HTML boxes now: 26 absolutely positioned divs, one
  bin each (4% of the sheet, spanning the chart's 160% height so the axis
  is their exact middle), each holding a full-width SVG (`width: 2500%`,
  the global `svg { max-width: 100% }` lifted) that draws the band set
  through `<use>`, shifted so its bin sits in the box. The box is what
  scales — a composited transform, no repaint. `--b` inherits so the box
  and its SVG share the bin index.
- No blend on the bands; only the halation multiplies. The halation
  wrapper is its own layer (`will-change: transform`), so the blurs are
  rastered once and the mask moves over them.
- The strip's glow is one `drop-shadow` on the SVG element (a composited
  effect), not filters inside it.
- The progress loop in `HomeDesktop.tsx` is a light spring instead of a
  0.08 lerp: velocity += Δ·0.028, ×0.82 per frame. Simulated: 8% overshoot
  of a step, settles in ~1 s, and follows a moving target with 6.8 frames
  of lag (the lerp lagged ~12). A wheel tick's step is a fraction of a
  percent, so the overshoot reads as give, not bounce.
- One ease for the section: ease-out-back (c1 1.2–1.4) on the lens
  (moves now 0.3 vh), on each growing slice (a 7% sprout past its height,
  then settle), on the strip's columns, and on the tables' 18px entry
  slide. Tables cross-fade over 0.22 vh; captions fade over 0.2 vh with a
  6px rise.

Verified (frozen): slice boxes align to the sheet (SVG 822px at left 0);
at draw 0.3 slice 7 stands at 1.069 (overshoot) and slice 9 at 0.33; the
final figure is pixel-for-pixel the earlier one; the lens reaches k 2.04
at u 0.73 before settling to 2. Frame timing itself cannot be measured in
the harness — judge on the machine.

### Pacing, September 2026

The figure is built over 2 vh (was 1.5), each slice rising over 0.2 of the
draw with a 0.028 stagger, so five slices are in motion at once — a wave,
not steps (at draw 0.5, slices 12–16 stand at 1 / 0.81 / 0.41 / 0.07 / 0);
lens moves take 0.4 vh; the stations sit at 2.0 / 2.65 / 3.3; the margin's
tables shift to 0.5–1.45 / 1.4–2.3 / 2.25–3.05 / 3.0–4.2.

### Remaining

Judge the build, the lens and the strip's growth live (the harness cannot
run the ticker); the wall's speed; mobile stays frozen.

## 4y. Dev server runs Turbopack

`package.json` → `"dev": "next dev --turbopack"`.

Webpack's dev pipeline loads `mini-css-extract-plugin`, whose hot-reload path
throws `Cannot read properties of null (reading 'removeChild')` when a
hot-replaced stylesheet's `<link>` has already been detached. It fires per CSS
hot-reload and accumulates through a session of CSS-module editing — which is
most of this section's work. Turbopack does not use that plugin, so the error
class does not exist there (verified: 0 webpack bundles, 0 mini-css-extract
requests, and no console errors across four consecutive CSS hot reloads).

Safe because the only Webpack customisation in `next.config.ts` is guarded by
`if (!dev)`, and `next build` still runs Webpack — so the production cache
setting is untouched. Nothing in the codebase depends on CSS-module class
naming, which Turbopack formats differently
(`Component-module__hash__name` vs `Component_name__hash`); only ad-hoc
verification selectors do, so match on the bare name (`[class*="table"]`)
rather than the Webpack form.

**Known limitation, unrelated to this change:** the Contribution white half
overflows by 40–64px at a 720px-tall viewport. The layout is currently sized
for ~1000px. Not yet addressed.

## 4z. Vertical rhythm — standing rules

These are rules, not notes. Every one of them was written after the same class
of defect shipped: a box that measured centred but read off-centre. **Centring
is judged on ink, not on boxes** — measure from the first glyph's top to the
last glyph's bottom, not from the element's border box.

1. **A collapsed element must retire its margins and padding too.** Height
   driven to 0 while a margin survives leaves dead space that no centring can
   see. `.columnTitle`'s bottom margin left ~18px under the last visible ink:
   the white half measured 52/52 by box and read 62/82 by ink.
2. **Never ship a near-empty structural row.** When the organisation name was
   removed, the footer stayed as a 34px strip holding only a year. The
   statement above it was perfectly centred in its own band and still read
   top-heavy, because the composition — not the box — was unbalanced. Fold the
   remnant into the neighbouring band instead.
3. **Text must never be a shrinkable flex item.** `flex: 0 0 auto` on any
   element carrying copy. The intro lost 3px off its second line, and a line
   cut just above the baseline reads as a row of dots — a rendering artefact,
   not a layout one, to anyone looking at it.
4. **Slack goes to the content that grows, never to a fixed block.** The
   closing paragraph sat top-aligned in a tall flexible cell and read as
   uncentred; the five headings needed that room anyway.
5. **Break two-clause lines at their own punctuation**, not wherever the
   measure runs out.
6. **A box must finish opening before its text becomes readable.** Where one
   value drives both `max-height` and `opacity`, the text is legible while the
   box is still growing — clipped, and off-centre in a container that has not
   reached its final size. Drive them separately so the fade *trails* the
   expansion (the mirror of the upper half's `--textFade` leading its
   collapse). The closing paragraph was visible at 35% opacity while clipped by
   8px, skewed 7px off centre.

**Sample the whole range, not the ends.** Rules 4 and 6 both shipped because
centring was verified at `--local-progress` 0 and 1 only. Every defect of this
class so far has lived in the middle of a reveal. Gate on: no element clipped
while its opacity is above ~0.2, and ink skew within ~2px at *every* sampled
state where the content is legible.

Verification for any change to this section: sample `--local-progress` across
0→1 and assert zero overflow, zero clipping on lit text, and ink gaps within
~2px at both ends.

## 4a. Section hand-over — dealt, not dissolved

Sections change by **sliding at full opacity**, like a card drawn off a deck:
the incoming section travels its own full height over the outgoing one, and
its opaque ground is what hides what is beneath. Nothing is ever translucent.

A cross-fade briefly renders two solid-background pages on top of each other,
which is what made the change of section look cheap. Because opacity is no
longer involved, the hand-over window can be far wider than a fade could be
(`SLIDE_MARGIN = 0.045`, ease-out cubic) — that width is what makes it read as
smooth rather than snapped.

The deal happens **inside the incoming section's own share**, never in the tail
of the outgoing one. Starting it a margin *before* the boundary meant the
Contribution card began covering Identity at 88% of Identity's progress — past
its last act boundary (0.985) — so Identity's closing tagline was buried before
it could run and Contribution appeared to cut in early. The last act now
resolves at p = 0.3788, before the card starts at p = 0.3846.

Verified across the Identity → Contribution boundary: offset 924 → 399 → 123 →
13 → 0 px, with **both sections at opacity 1 at every sample**. Section 0 is
the bottom of the deck and is always seated, which is also why its rest state
is correct on first paint — there is no ramp for it to land in the middle of.

**Entry (page-switch in):** top:bottom height ratio ≈ **4:5** (bottom
already the larger of the two, not a thin sliver). The ledger table exists
immediately at entry (numbers present, structure visible) — descriptive text
is not yet shown. On this page-switch-in transition, a data chart (§4.2)
draws itself once, from empty to fully drawn.

**Inner scroll (scrubbed), in order:**

1. The white/blue boundary continues moving upward — `--contrib-bottom`'s
   visible height grows.
2. The ledger table's row spacing grows with it, and `CONTRIBUTION_BODY`
   fades in.
3. Midway, the 2D chart (already drawn at entry, §4.2) fades out. The same
   canvas region — still positioned inside the table, not a separate
   floating element — switches to the Three.js scene (§4.3).

### 4.0 September 2026 notes

A self-driven "film" over the middle (0.10 → 0.92, 12 s, input refused)
was built and withdrawn on the owner's review — it read as the page
acting on its own; Contribution is scroll-bound. What stays: the field's
canvas is 2% smaller (`scale(0.98)` from the bottom centre) because the
tallest stems grazed the caption, and the scene renders only when its
progress moves, kept warm from Identity's act 7.

### 4.1 Ledger and copy — content angle

Two-tier narrative, both hedged accurately (no exhaustive/expert-review
claim):

- **Primary — methodology.** How records move from candidate → canonical →
  published: gathered across heterogeneous archives, reconciled, **spot-
  checked** and reviewed at a **semantic level** (not an exhaustive manual
  pass, not expert art-historical review), screened against evidence /
  publication / rights conditions; records that don't clear the bar are held,
  not silently dropped. This is `CONTRIBUTION_BODY`'s existing direction,
  written with more specificity but the same hedge.
- **Secondary — source-coverage direction.** Verified against
  `docs/capture/NONMAINSTREAM_SOURCE_SUCCESS_REGISTRY_2026_V3.md`: the
  project has been actively expanding source discovery into traditionally
  under-covered regions (Africa, Latin America/Caribbean, MENA, Southeast
  Asia, Eastern Europe/Caucasus, South Asia, Central Asia, Oceania/
  Indigenous — 500+ newly verified museum/library/cultural-centre/archive
  sources as of the latest registry pass). **Framed as an active
  infrastructure direction, not a completed-content claim** — that registry
  pass is explicitly source-level and has not yet fed the published 7,995
  records, so copy must not imply the current archive already draws heavily
  from these sources.

### 4.2 2D chart — decade histogram (replaces the earlier "growth since
2024" idea)

Real project entry only began in 2026 (2024–early 2026 was research/
literature review, not data entry), so a "records added per project-year"
curve would be empty-then-a-spike — not meaningful. Instead:

- **Type:** bar chart / histogram, bucketed by **decade of the record's own
  subject year** (earliest year in the archive → 2026 — the same year range
  as the 1800–2026 dictionary used elsewhere in the product).
- **Data source (real, pulled at implementation, not invented for the doc):**
  a per-decade count derived from the archive's own year field — exact
  source file to be confirmed against the current data layer when built.

### 4.3 3D scene — isometric Three.js, different data dimension

Deliberately a **different** axis than the 2D chart (batch structure, not
subject-year), so the two visuals aren't the same data twice:

- **Data:** the 44 capture batches. Real per-batch figures pulled from
  `data/capture_runs/capture_run_manifest_v1.csv` at implementation time —
  not fabricated for this document.
- **Sequence, in order, all drawn directly in the canvas:**
  1. Isometric wireframe axes/grid draw in (sequential line reveal, not an
     instant appear).
  2. Sphere data points populate onto the grid, staggered (not all at once).
  3. One point lights up — a glowing highlight, representing a current
     milestone figure (e.g. the published count).
  4. **After** the highlight appears, additional points keep being mapped in,
     continuing at a slow, steady rate for as long as this section is in
     view. This is a hard requirement, not optional polish: the animation
     must not read as "we found one best point and stopped" — the glow is one
     verified point inside a data set that keeps growing, never the
     endpoint of the exploration.
- **Point budget:** cap total live points around 40–60; recycle/fade older
  ones rather than accumulating without bound.
- **Technique (approved: Option A):** Three.js, `InstancedMesh` for the
  spheres, a billboard glow sprite for the highlight instead of real Bloom
  post-processing (cheaper, same read at this scale), orthographic camera
  for the isometric look, `next/dynamic` lazy import, paused when off-screen
  or the tab is hidden, DPR capped, static single frame under
  `prefers-reduced-motion`.

---

## 5. 03 · Enter the Archive / 04 · Research Status

Content unchanged from the existing build (three-entry contents list;
closing boundary note) — see `lib/content.ts` (`ENTRIES`, `RESEARCH_STATUS`).
Nav-title colours `--coral` / `--yellow` respectively. Right-pane background:
**open**, defaults to `--hero-bg` for now (§2).

---

## 6. Open items (not blocking implementation start)

- Exact sampled hex for `--contrib-top` / `--contrib-bottom` / the Identity
  marker blue — approximated above from the reference swatches, confirm by
  eye once built.
- Sections 03/04 right-pane background colours.
- Exact per-decade record counts (§4.2) and per-batch figures (§4.3) — pull
  from real data files at build time.

## 7. Files

`app/page.tsx` (existing server device-split, unchanged) →
`app/home/desktop/HomeDesktop.tsx` rebuilt around the pinned-block
architecture (§1), with a new `home/desktop/three/` module for the Contribution
3D scene (dynamically imported) and a `home/lib/` addition for the decade/
batch data shaping. `home/mobile/` untouched this round.

### §4 checked against the request, item by item

Written by re-reading the request line by line, not from memory.

| Asked | State |
|---|---|
| Type/layout back inside the design system | **Done** — prose on `--font-body`, numerals on `--font-num`, body on the 18px `--fs-body-sm` floor, spacing on `--s-*` |
| Intro not three lines | **Done** — 2 lines (measured) |
| Fill the whitespace on the right | **Done** — measure widened 62ch → 96ch |
| Three figures become the three columns' points | **Done** — separate ledger row deleted, each figure heads its column |
| Histogram every 5 years from the earliest year | **Done** — 46 bins, 1800–2025, from `additive_20k_year_coverage_v1.csv` |
| 12,932 was confusing | **Fixed, and it was my error** — I had summed 4 of 5 period bands, silently dropping 748 undated. No competing total is printed now; the caption names what the axis measures |
| After scroll, keep only the three numbers | **Done** — text retires; lower half grows 397px → 675px |
| Content transitions away before it has fully appeared | **Partly** — the in-section clipping is fixed (0 frames with clipped or overflowing text). Whether the *section* hands over too early is Contribution's scroll weight (4.2 vs Identity's 8.0) and is **not yet addressed** |
| Left panel = the supplied reference, in Three.js | **Built, not verified** — see below |
| Not a morph; second drawn from zero after the first clears | **Done** — measured 0 frames where both are visible; separate objects, `--build` gated after `--histoIn` |

**Not verified, and I am not going to claim otherwise:** the Three.js field.
The harness browser pauses `requestAnimationFrame` outright (measured 0
frames / 500 ms), and both Three.js and the render loop depend on it, so the
scene cannot draw here. What is confirmed is only that the canvas mounts at
1246×1150 with a live WebGL context and no runtime errors. Whether it
actually matches the reference needs a real browser.

### Round 7 — the opening state and the rail (2026-09-03)

Owner: the first screen after a hard reload, and the left rail, must belong to
the same sheet as About and Source; nothing later on the homepage changes; the
layout stays — the four titles at the lower left, no annotations, no heavy
visualisation — and the right side keeps the tone of a modern museum archive
(MoMA, the Met), set in Baskervville rather than bold. Done: the ground of the
opening is the sheet's paper; the serif statement, the copy and the gallery's
captions are ink; the empty plates are paper-2 on a hairline (1px ink 38%)
with the registration cross; by local 0.09 the ground has gone to black and
everything on it to paper through one variable (`--fg`), so the film's black
stage is unchanged. The rail keeps its layout (four titles, lower left, heavy
face, small numerals) on the same paper: the active title at full ink with a
2px rule in its section's colour, the others held at 55%. The rail keeps its dark
ground (#2f3434) on every section — the owner found a paper rail pulled the
eye to the right, and the pages around it were designed against a dark rail;
a stage-following ground was tried and withdrawn. A first cut that set the opening in LINE Seed
800 with a sky pill and made the active title a colour plate was withdrawn —
it read as loud and crowded.
