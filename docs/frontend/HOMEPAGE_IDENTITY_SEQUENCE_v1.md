# Homepage · 01 Identity — full scroll sequence (v1)

The authoritative spec for the Identity section's behaviour. Written before
implementation, and **checked line-by-line against the built result
afterwards**. If the build and this document disagree, one of them is wrong —
resolve it, don't leave it.

Scope: desktop only, the right pane of the pinned split-screen
(`HOMEPAGE_DESIGN_v1.md` §1). The left nav is untouched throughout.

---

## A. Layer model (why it feels pinned)

Two layers inside the section, not one long translating track:

| Layer | Contents | Movement |
|---|---|---|
| **Scroll layer** | Header block + gallery | Translates vertically — this is the only part that scrolls |
| **Pinned layer** | Everything from the first sphere onward | **Never translates.** Fills the pane; its state changes in place |

The earlier single-track build made the whole section slide continuously,
which is why nothing read as "pinned". Once the gallery is gone, the page
must feel **stopped** — scrolling advances state, not position.

## A2. Three acts, and what drives each

Identity is staged as three acts, and **not everything is scrubbed to
scroll** — that is what made earlier passes feel mechanical.

| Act | Beat | Driver |
|---|---|---|
| **I — The gallery** | A convincing, filled, white collection grid. Real captions, real vocabulary, and **no images**. The reader is meant to notice the absence themselves. | scroll |
| **II — The void** | The gallery leaves, the ground darkens, one sphere **inflates on its own**, then more arrive as you scroll, the row pans, and the field floods. | mixed |
| **III — The reveal** | Hard cut to black; MGDA lands; the tagline types. | event |
|

**Scrubbed to scroll:** gallery travel, spheres 2–6 arriving, the row's pan.
Those are the beats where the reader should feel they are doing the moving.

**Self-driven (fire once on entering the act, with real easing):** the first
sphere's inflation, the grid flood, the black cut, MGDA's entrance, the
typing. These play at their own tempo regardless of how fast the wheel turns
— a scroll-scrubbed "reveal" is never dramatic, because the reader can stall
it halfway.

**Easing.** GSAP 3.13+ ships the former premium plugins free, and 3.15 is
installed, so `CustomEase` and `CustomWiggle` are available and used:
drama comes from overshoot and settle, not from a smooth ramp. The first
sphere overshoots and wobbles in; MGDA punches in and settles.

`ScrollSmoother` was considered and **rejected**: it transforms a wrapper
element, and a transformed ancestor breaks `position: sticky`, which the
whole pinned split-screen depends on. The rAF lerp in §C stays.

## B. Timeline

`p` = the section's own local progress, 0 → 1. Section weight **6.0**
(six screens of scroll distance).

| `p` | What happens | Layer |
|---|---|---|
| 0.00 – 0.30 | Header + gallery scroll upward past the viewport | scroll |
| 0.30 – 0.38 | Gallery fades out; **background darkens** from `#3c4242` toward `#23282a` | both |
| 0.38 – 0.46 | A **small dot inflates** into one large sphere, roughly centred | pinned |
| 0.46 – 0.64 | Spheres 2–6 appear **one at a time**, in line to the right of the first | pinned |
| 0.54 – 0.64 | Once a new sphere is being cut off at the right edge, the row **slowly pans** (content moves left = camera pans right). Not before. | pinned |
| 0.64 – 0.68 | **Sudden cut**: the pane fills with a **regular grid** of circles (even rows and columns — not scattered) | pinned |
| 0.68 – 0.72 | **Sudden cut to black** | pinned |
| 0.72 – 0.82 | **MGDA** appears, centred (~150px cap height) | pinned |
| 0.82 – 0.90 | Tagline types out: **Read. Trace. Reframe.** | pinned |
| 0.90 – 1.00 | **MGDA → "Modern Graphic Design Archive"**; the typewriter cursor keeps blinking | pinned |

Order is strict at the black cut: **black first, then MGDA, then the
typewriter.** Never simultaneous.

After `p = 1.00` the pane holds on black and the existing section crossfade
carries into Contribution. No vertical slide out of Identity.

## C. Motion quality

Raw `ScrollTrigger` progress is linear and reads mechanical. The rendered
progress is a **lerp toward the scroll-driven target** on a rAF loop
(≈0.08/frame), so every stage eases in and out and fast flicks don't snap.
This is applied at the `HomeDesktop` level, so all four sections get it.

## D. Static design

### Header block

- **Headline** ("Design history, verified and connected.") — the serif
  statement face (Baskervville), **italic, regular weight**, matching the
  header wordmark's register. Not the heavy sans; the page has too much bold.
- **Description** — two paragraphs, right of the headline, both blocks
  **top- and bottom-aligned** (first and last baselines parallel). The
  headline's line-height is set generously so its block height matches the
  paragraphs'.
- **No orphans** — no paragraph may end with a single word alone on a line
  (`text-wrap: pretty`).
- The whole block sits **lower** than a flush top edge — it is not pinned to
  the top of the pane.

### Gallery frames

Four per row. Each card is a complete, believable collection record:

```
┌──────────────────────┐   hairline outer frame, generous padding
│  ┌────────────────┐  │
│  │     [img]      │  │   hairline inner image frame
│  └────────────────┘  │
│  [Title]             │
│  [Year]              │
│  [Medium]            │
└──────────────────────┘
```

Every field is a bracketed placeholder — **that is the point**, not an
apology. Refinements this round: hairline (not 1.5px) borders, more generous
internal padding, **varied image aspect ratios** so the grid doesn't read
mechanically regular, and meta text in the page's own label style.

### Spheres

Warm white (`#fbfaf7`), ~18rem, no border. Six of them.

### Closing

Pure black (`#0a0a0a`). MGDA centred, ~150px. Tagline below in the accent
yellow with a blinking cursor.

---

## E. Post-build checklist

Verified in-browser at 1800×1000 by measuring computed values across a sweep
of `--local-progress`, not by eyeballing screenshots.

- [x] Header block sits low, not flush to the top — `min-height: 62vh` + `flex-end`
- [x] Headline is serif italic, regular weight — measured `Baskervville / italic / 400`
- [x] Headline and paragraph blocks top- AND bottom-aligned — measured Δtop −2px, Δbottom 0px
- [x] No paragraph ends with a lone word on its own line — `text-wrap: pretty`
- [x] Frames: hairline, generous — **uniform** ratio, see note below
- [x] Background visibly darkens after the gallery
- [x] One sphere inflates from a small dot — measured scales `[1,0,0,0,0,0]` at p 0.46
- [x] Spheres 2–6 appear one at a time — `[1,1,.11,0,0,0]` → `[1,1,1,.22,0,0]` → …
- [x] Panning starts only after a sphere is cut off — panX 0 at p 0.54, −461 at 0.58
- [x] Fill is a regular grid — 7 × 4, `place-items: center`
- [x] Cut to black before MGDA — at p 0.70 black 0.5 / MGDA 0; at 0.74 black 1 / MGDA 0.2
- [x] MGDA before the typewriter — at p 0.80 MGDA 0.8 / cursor 0 / chars 0
- [x] MGDA → full name while the cursor still blinks — at p 1.0 MGDA 0, full 1, cursor 1
- [x] Nothing translates vertically from the first sphere onward — scrollLayer Y and pinned top constant across p 0.30 → 1.0
- [x] Motion is eased — rrAF lerp (§C), not raw scroll progress
- [x] No horizontal page overflow at any stage

**Deviation from the spec, deliberate:** §D asked for *varied* image aspect
ratios. Built and rejected — varied ratios put every card's meta text on a
different baseline and read as ragged rather than considered. Shipped with
one uniform 4:5 ratio, and the "not too regular" intent addressed through
generous insets, hairline strokes and larger gaps instead. Revisit if the
ragged look was actually what was wanted.

### Verified after the three-act rework

Measured, not eyeballed:

- [x] Header block sits at the top of the first screen
- [x] Gallery reads as a working collection: solid white cards, real captions
      (`Exhibition poster · 1962 · Screenprint`), empty plates
- [x] First sphere centres on the **whole viewport**, not the pane — measured
      centre 900px against a 1800px viewport (`--nav-w` backed out)
- [x] Flood grid is 12 × 6 = 72 marks, smaller than the spheres
- [x] Tagline is "A research archive for modern design."
- [x] The MGDA → full-name rename is gone (no `.fullName` node in the DOM)
- [x] Closing block sits below the optical centre (`translateY(6%)`)
- [x] Act boundaries map correctly (unit-checked: 0.29→0, 0.30→1, 0.37→1,
      0.38→2, 0.45→2, 0.46→3, 0.63→3, 0.64→4, 0.67→4, 0.68→5)
- [x] No horizontal overflow; clean console on a fresh load

**Not verifiable in the harness browser:** it pauses `requestAnimationFrame`
entirely (measured: 0 frames/700ms), and ScrollTrigger *and* GSAP both drive
off rAF — so no scroll-driven or timeline-driven beat can execute there. The
static geometry above and the act arithmetic are verified; the motion itself
(sphere overshoot, flood stagger, MGDA punch, typing) needs a real browser.

## F. Redesign v2.1 — "six ways to draw a circle" (approved; round 1 built)

Owner's brief, second pass: Identity is atmosphere and concept, not a data
plate — it has to show that a design archive can *design*, so the reader
believes the site is attractive and precise. The gallery can be more
refined. The six circles of the ellipsis need not be six eras; they can be
six readings of the circle, showing what design can do. Then line becomes
text — *Where design history becomes traceable.* — and the whole thing
plays like a short film: scroll turns the pages, and inside every page
something moves on its own.

Six references were supplied, all circles: a family of thin white loops on
black (Lissajous / an hourglass of stacked ellipses); a ring of broken
radial strokes; a hand-drawn orbital diagram with arrows and crosses; a
sphere built from an LED dot grid, white in the light and RGB in the
shadow; a halftone ring in cream and red; a glossy gradient sphere over a
striped landscape inside a circle.

### F1. The film

| `p` | Page | Scroll drives | Moves on its own |
|---|---|---|---|
| 0.00–0.22 | **The gallery**, refined (F2) | travel | plates settle in with mass; captions arrive after their plate |
| 0.22–0.30 | **Frames become a line.** The plates' outlines lift off the cards, fly to the centre and merge into one thin white ring — the first circle is drawn, not inflated. The ground goes to black under it | the outlines' flight | the merge and its overshoot (0.9 s) |
| 0.30–0.60 | **Six readings of the circle** (F3). The ring is study I; II–VI arrive one per stop as the row pans; each keeps its own idle motion | arrival and pan | every study's idle loop |

*(As built, thirteenth pass: three readings — the line, the eye, the engraving; the film's beats and the act boundaries are in F8.)*
| 0.60–0.68 | **Line becomes text.** The studies unravel: their strokes leave, travel, and write the sentence as a single-stroke line — glyph by glyph with `pathLength`, the way the circles were drawn | — | the writing (1.6 s) |
| 0.68–0.72 | **Text becomes the field.** The sentence's strokes break into the dot grid (the built beat), now on the sphere's LED palette | — | the burst (0.5 s) |
| 0.72–0.815 | cut to black, **MGDA** (F4) | — | the stamp |
| 0.815–0.985 | *Read. Trace. Reframe.* → *A research archive for modern design.* (F4) | — | the stamps, the resolve |
| 0.985–1.00 | launch into Contribution, as built | — | — |

### F2. The gallery, refined

The collection grid should look like a museum's own site, not a mock of
one. A 12-column measure with hairline rules between rows; plates in
three real proportions (portrait, square, landscape) with a 1px ink
frame, a 2px paper inset and a soft floor shadow; the "[IMG]" mark
becomes a small centred registration cross; captions set as a museum
does — creator in medium weight, title in italic with the date, then
medium and dimensions in a lighter grey, all at 17px+; on hover a plate
lifts 4px and its caption's rule extends. Plates arrive with mass
(scale 1.04 → 1, blur → sharp), captions 120 ms after their plate. Still
no images, and still no placeholder art.

### F3. Six readings of the circle

Each study sits in a 420px stage, white or cream on black unless noted,
built with SVG where lines are the point and Canvas/WebGL where dots are.
Each has an idle loop that never stops while it is on screen; scroll only
brings it in and pans the row.

| # | Study | Construction | Idle motion |
|---|---|---|---|
| I | **The line** — a family of thin ellipses sharing a centre, the hourglass of stacked loops | SVG, 14–24 ellipses, 1px, drawn in with `pathLength` from the merged ring | the loops precess: each ellipse's tilt drifts a few degrees on its own period, so the figure breathes like a moiré |
| II | **The strokes** — a ring of broken radial dashes, three concentric bands | SVG lines, 180 spokes, dash lengths from a seeded random | the bands turn at three speeds, inner fastest; a slow flicker moves through the dashes |
| III | **The orbit** — the hand-drawn diagram: eight small circles with a dot and a tick, arrows on arcs around them, crosses in the margins | SVG, stroke 1.5px with a slight hand-drawn jitter filter | the arrows advance along their arcs; the ticks inside the circles turn like second hands |
| IV | **The sphere** — the LED dot grid: white where lit, RGB in the shadow | Canvas, ~1,100 dots on a 3D sphere projected, lit from the upper left | the sphere rotates slowly; the terminator moves across it so dots switch from white to colour |
| V | **The halftone** — a ring of dots whose sizes make cream and red rings | SVG circles, radial halftone sampling | the red band drifts around the ring; dot sizes pulse with a slow wave |
| VI | **The rendered sphere** — a gradient sphere in a circular window over striped ground | CSS/Canvas gradients with film grain (SVG turbulence) | the sphere's highlight slides; the stripes move like a slow landscape |

The row's order is the order of abstraction: line → strokes → diagram →
dots → halftone → image. That is also the story: from a drawn circle to a
picture of one.

### F4. Type — no linear moves

As proposed before: a word arrives with mass (scale 1.08 → 1 on the
section's ease-out-back, blur 5px → 0), its tracking settles (0.28em →
rest), a hairline draws under MGDA with `pathLength`; *Read. Trace.
Reframe.* is three stamps 420 ms apart with the full stop clicking in
after each; the settled line resolves out of the last of the field's
dots; figures count up in tabular numerals; every ease is the section's
ease-out-back or the HomeDesktop spring, never `linear` or `ease`.

### F4a. MGDA's entrance — serif → sans → bold

Owner's note: the cut to black and MGDA's arrival are hasty — not a
linear opacity, and the wordmark should arrive *as a type effect*, ideally
changing from serif to sans to bold.

The sequence, ~2.6 s, self-driven on entering the act:

| t | Beat |
|---|---|
| 0.00–0.30 | **The field collapses to one point.** The dot grid's dots race to the centre (per-dot delay by distance, ease-in) and become a single white dot; the ground is already black |
| 0.30–0.55 | **Held black.** The dot holds — a real pause, 250 ms, so the black is a cut and not a fade |
| 0.55–1.15 | **Line becomes letters.** From the dot a hairline runs out and draws the outlines of M · G · D · A in **Baskervville** (the site's serif) with `pathLength`, left to right, 140 ms per glyph; the outlines fill from the baseline up |
| 1.15–1.65 | **Serif → sans.** Each glyph's outline morphs into its **Instrument Sans** form (serifs retract, contrast evens out), 80 ms stagger, ease-out-back — the letters visibly *shed* their serifs |
| 1.65–2.15 | **Sans → bold.** The outlines thicken into **LINE Seed 800**, the wordmark's real face; a 1.03 → 1 scale thump lands with the weight; tracking settles 0.24em → 0.04em |
| 2.15–2.60 | **The rule.** A hairline draws under the word, left to right; then the taglines begin (F4) |

At every instant the letters are real letterforms of a real face, not a
crossfade: the three faces' outlines for M, G, D, A are extracted once at
build time (a Node script with `opentype.js` over the served font files —
Baskervville and Instrument Sans from next/font's cache, LINE Seed from
its served files) into one JSON of SVG path data, normalised to a common
em box. At runtime the four glyphs are SVG paths and GSAP's `MorphSVG`
(free since 3.13) interpolates outline → outline; `pathLength` draws the
first. The DOM wordmark in LINE Seed takes over on the last frame
(identical geometry, so the hand-off is invisible), and everything after
it — the rule, the taglines — is the built DOM.

Reduced motion: the wordmark is simply set in LINE Seed 800, at rest.

### F5. Engine

- Studies I, II, III, V: inline SVG, animated with CSS keyframes
  (transform, dash offset) so idle loops cost the compositor only.
- Study IV: one small Canvas, 1,100 dots, rAF only while the study is on
  screen (IntersectionObserver), paused otherwise.
- Study VI: CSS gradients + an SVG `feTurbulence` grain, transforms only.
- The frames-to-ring merge and line-to-text: SVG path morph (GSAP
  MorphSVG is in 3.13+ free) and `pathLength` drawing of a single-stroke
  face for the sentence (Hershey-style strokes, exported once to paths).
- Entrances and the pan stay scrubbed via `--local-progress`; every
  self-driven beat fires once per act via `data-act`, as the built
  sequence does.
- Reduced motion: every study at rest, the sentence typeset.

### F6. Rounds

1. The six studies as static compositions, the row, the pan, the gallery
   refinement.
2. Idle loops, the frames-to-ring merge, line-to-text writing, text-to-
   field burst.
3. Type vocabulary on every text beat, timing against the film feel,
   reduced motion, documentation.

### F7. What stays

The layer model, the act boundaries and drivers, the field and the black
cut, the launch into Contribution, and the rule that visibility is
declarative and only motion is timed.

### F8. Built — round 1 (what stands in the code)

- `identity/studies.tsx` — the six studies as SVG (I, II, III, V), a
  canvas (IV, `LedSphere.tsx`: 27 rings of dots on a sphere, lit from the
  upper left, turning at 0.22 rad/s only while on screen), and CSS
  gradients with `feTurbulence` grain (VI). Idle loops are CSS keyframes:
  I's family spins over 96 s while its stack precesses ±5°; II's three
  rings turn at 64/50/36 s, the middle one reversed; III's ticks turn and
  its arrows run their arcs on `offset-path`; V's cream and red layers turn
  against each other; VI's stripes drift and its sphere gleams.
- The row: `--sphere-size` clamp(17rem, 23.5vw, 27.5rem) (440px at the
  build), `--sphere-fit` 2, each study labelled (I · the line … VI · the
  image) in 17px caps; arrival on the section's ease-out-back.
- The frames: eight outlines (the cards' proportions, 150px tall) fly from
  −56vh with a per-frame rotation, round off as they converge and land
  exactly on study I's base circle (392px — measured equal); all but the
  first fade at the merge, the first hands over at 0.17–0.19 while study I
  draws itself (act 2, `pathLength` keyframes, 0.045 s per loop).
- The sentence: 35 glyph outlines of Instrument Sans 600 from
  `scripts/extract-identity-glyphs.mjs` (fontkit over the @fontsource
  files, normalised to a 1000-unit em) drawn with `pathLength`, filled
  from 70% of each glyph's draw, then burst on their scatter vectors as
  the field blooms.
- The field: 16 × 8, the LED palette in its lower-right shadow; on the
  collapse every dot falls into the centre (≈ −5.2× / −4.6× its slot
  offset) so the field becomes the point the wordmark grows from.
- `identity/Wordmark.tsx` — the wordmark is an SVG of LINE Seed 800
  outlines at rest; on act 6 a GSAP timeline replays §F4a: point (0.3 s),
  held black (0.25 s), the serif outlines drawn 0.55–1.15 s, filled,
  morphed to Instrument Sans 400 at 1.15 s and to LINE Seed 800 at 1.65 s
  (`MorphSVG`, `shapeIndex: "auto"`, back-out eases), a 1.035 → 1 thump at
  1.9 s, the rule drawn at 2.15 s. Rest state is restored on interrupt.
- Act III's type: *Read. Trace. Reframe.* as three stamps (scale 1.12 →
  1, blur 5px → 0, tracking 0.22em → 0) at 2.8 s + 0.42 s each; the line
  holds and clears at 5.4 s; the settled line resolves word by word from
  5.7 s. Visibility of Act III is gated on the act (6, 7), timing is the
  film's own.
- The gallery: hairline row rules, plates with a 1px ink frame and a 3px
  paper inset, a registration cross in place of "[IMG]", captions at 17px
  in a museum's order, plates arriving with mass and captions 120 ms
  after them, a 4px lift on hover.
- LINE Seed JP was already served through `@fontsource/line-seed-jp`
  imports in `globals.css` — the earlier note that it was only named was
  wrong; the extraction script reads the same package.

Verified (frozen states, 1960×1130): 15 cards, 6 studies, 35 glyphs,
wordmark 753×224px at rest; frames at 0.115 mid-flight (325px, opacity 1),
ring = study I circle at 0.155; studies at 0.31 (II, III centred, IV
arriving) and at 0.47 (VI dead centre, left 918 ≈ pane centre − 220);
sentence at 0.545 drawn to its last glyph; field at 0.66; collapse at
0.74; act 6 shows the wordmark, the rule and the first stamp. Server
compile clean; `tsc` clean. The wordmark timeline, the idle loops'
continuity and the LED sphere's turn cannot be watched in the harness
(rAF is suspended) — judge on the machine.

**Round 1, second pass — density.** The owner's first look (in a tab that
had kept the previous stylesheet through a hot update: labels in mixed
case, black-filled glyphs, 46px dots — the markup was new, the CSS old)
found the field and the sphere reading as a mirror ball and the whole at
"20% of the complexity". Densified: the field is 40 × 20 marks of r 3.4
in an SVG (800 circles, one paint) with the LED palette held back to ~12%
of the shadow corner; the sphere has 46 rings and ~2,500 dots of 1.9px,
lit dots off-white, a grey terminator band, the primaries darkened; study
I has 36 + 18 loops at 0.7px in two counter-turning families over a
13-loop stack; II has five rings of 72–180 fine dashes at 1.4px, alternate
rings reversed; III gains dashed inner rings and two inner arcs; V has 30
rings at 7.2-unit pitch. The dev server was restarted on a cleared cache so
the served stylesheet is the one in the repo; a hard reload is required in
any tab that was open through the rebuild.

**Round 1, third pass — black and white, and the road.** Owner: no names
under the circles; everything in dots and lines, one colour; more
complexity; the fourth study redesigned; the field's colour reads oddly;
no rule under MGDA; the wordmark's animation can pass through more faces.
Done: the labels are gone. Study IV is now a halftone-printed sphere —
~6,000 dots on a 64-ring lattice whose SIZE is the light on them, over a
wire lattice of 12 meridians and 8 parallels, with a hairline terminator
ring; one colour. Study VI is a moiré: two families of 44 concentric rings,
the second centred 26 units off and wandering, clipped to the disc. Study
III gained a 120-tick dial turning slowly around the diagram. Study V's
inner band is the same white at 42%. The field is 56 × 28 marks (1,568)
whose radii carry two crossed waves and a ring — an interference halftone —
all white, the smaller marks at lower opacity. The wordmark's road is now
seven faces: the italic serif is drawn as a line, fills, stands upright
(Baskervville roman), sheds its serifs (Instrument Sans 400), thickens
(700), passes into LINE Seed 400, 700 and lands in 800 with a 1.04 → 1
thump at 3.45 s; the rule is gone; the stamps follow at 4.1 s, the settled
line at 7.0 s. Verified frozen: 0 labels, 1,568 marks, 88 moiré rings, 120
dial ticks, 0 rules; every study renders in the paper white; the stamp's
tracking visibly settling on "Reframe." at 4.6 s after the act.

**Round 1, fourth pass — slower, and three studies from scratch.** Owner:
everything too fast to read; III, IV and VI disliked outright — chaotic and
too alike; the field wants colour *while it changes*, more marks and more
layers; MGDA too bouncy, "cheap". Done:
- Pace. Identity's weight 8 → 11, so every scrubbed beat (frames, studies,
  sentence, field) runs ~40% longer at the same scroll speed. Study I draws
  in over 2.2 s with a 0.06 s stagger; plates and captions arrive over 1.4 /
  1.1 s. The studies enter on a smoothstep, not a back-out.
- III is **the contours**: thirty closed lines nested like a trunk's rings,
  each a circle bent by three low harmonics with its own phase; the set
  turns once in 320 s and every third contour breathes ±2°. IV is **the
  spiral**: Vogel's phyllotaxis, 1,300 dots a golden angle apart at r ∝ √n,
  size falling outward, turning once in 200 s. VI is **the engraving**: a
  canvas sphere hatched in 86 parallel ribbons whose width is the darkness
  at that point, a hairline outline, the light drifting round it. Six
  languages now: loops · strokes · contours · spiral · halftone · hatching.
- The field is two layers: A, 64 × 32 marks (2,048) with the interference
  sizes, each passing through its own hue (an oklch mix, `--inFlight` =
  4·e·(1−e), so colour only while a mark is in flight) and landing white;
  B, 16 × 8 rings that draw themselves once the marks have landed and leave
  first on the collapse.
- The wordmark's road is 9.5 s, all `power2.inOut` / `power3.inOut`: point
  0–0.6 s, held to 1.0, the italic serif drawn 1.0–2.2 and filled, then
  roman 2.3, sans 3.4, bold sans 4.6, LINE Seed 400 5.6, 700 6.7, 800 7.7;
  the weight settles with a 1.018 → 1 press over 1.2 s — no bounce. Stamps
  at 9.8 s, 0.7 s apart, 1.1 s each on a soft curve; the settled line from
  14 s.
Verified frozen: 30 contours, 1,300 spiral dots, 1 canvas, 2,048 marks +
128 rings; a mark mid-flight computes to `oklch(0.83 0.14 85)` and lands
white; rings at dash offset 0.06 at 0.70; MGDA at rest with no rule.

**Round 1, fifth pass — the eye, the crowd, the set switched off.** Owner:
V should be an eye that looks about; VI not complex enough and its hand-off
to the sentence too plain; the field's rings disliked — the "archive is a
crowd" idea preferred: the marks should become people and run for the
edges, then black like an old television switching off; MGDA and its line
were not one centred group; study I's self-driven draw must lock scrolling
while it plays. Done:
- V is **the eye**: a halftone iris of 56 radial threads (1,092 dots) with a
  limbal ring, a black pupil with a dotted rim and a glint, inside a
  halftone sclera; the iris group looks about in saccades (`steps(1)`,
  seven fixations over 17 s) and two black lids meet at the centre for a
  blink every 8.5 s.
- VI has three plates now: the horizontal hatching, cross-hatching at 50°
  laid only where the light is below 0.34, and the engraver's guides —
  five parallels and five slowly turning meridians. On its way out it
  **unrolls**: the stage stretches to 4.2× wide and 0.6 high while a
  **ruled sheet** of 44 hairlines sweeps down the pane (each line's opacity
  follows `--spheresOut` with its own delay); the sentence is drawn on the
  rules, which fade as the letters fill.
- The field is **the crowd**: 1,352 marks land white, then each becomes a
  person — a white head over a coloured body (eight colours, the Tokyo
  poster's pairs) — and the crowd runs: every person leaves along their
  own heading away from the centre, on a cubic ease-in with their own beat
  (`--lead`), fading to 15%.
- Then **the set switches off**: the screen squashes to a bright line
  (`scaleY` → 0.004, brightness 2.8, a 2px glowing line drawn over it),
  the line shrinks to a point, the point fades — and the wordmark's own
  point grows from where it was.
- The wordmark is centred on its **ink** (bounds exported by the script),
  not its advances: measured, the wordmark's ink centre and the tagline's
  centre both fall on x = 1138.
- While study I draws (act 2, 3.6 s) the wheel, touch and the scrolling
  keys are refused by `preventDefault`, so the scroll position — and
  ScrollTrigger's layout — never moves.
Verified frozen: 1,352 people, 44 rules, 1,092 iris dots; the unrolled
engraving under the drawing sentence at 0.515; bodies up at 0.70; the
crowd scattering at 0.735; the line at 0.777 (`scaleY` 0.40, line at 60%).

**Round 1, sixth pass — no bounce, the eye holds and looks back.** Owner:
the page-level spring is too elastic — pages catch halfway, lurch, and a
nav jump bobs; the ruled sheet read as half a page; the eye was clipped top
and bottom; the row should hold on the eye and the eye should interact.
Done: the HomeDesktop smoothing is critically damped (0.036 / 0.68 per
frame — velocity, no overshoot) and the nav-jump card pull is `power3.out`
/ `power3.in`, not `back`; when the wheel rests inside a hand-over window
the scroll glides to the window's near end in 0.7 s, so no frame holds two
cards half-dealt. In 04 the lens, the slices, the strip's columns and the
tables' entries are smoothstep, not ease-out-back. The ruled sheet now
sweeps to the bottom by half the unravel and fades only once the letters
fill. The lids are parked 20 units further out (a 452-unit blink). The row
now pans one step to the eye at 0.40–0.42, **holds on it 0.42–0.50** (most
of a screen), then takes the last step at 0.50–0.53; the unravel and the
sentence follow at 0.53 / 0.535. The eye is a client component
(`identity/Eye.tsx`): while it is on screen the iris follows the pointer —
its offset written to `--lx / --ly` on a wrapper group and eased over
420 ms, saturating at ±34 × ±26 units — while the saccades and blinks keep
running underneath.

**Round 1, seventh pass — the eye opens; the row stops stuttering.**
Owner: the eye's ball should be smaller and the eye must visibly open, or
it does not read as an eye; the six-circle stretch stutters badly.
Where the frames went: every study's idle motion was a transform on a
`<g>` INSIDE its SVG, which re-rasterises the whole SVG every frame — some
5,000 marks across the row, on top of the engraving redrawing ~30,000
samples per frame. Done: every moving part is now an HTML **layer**
(`will-change: transform`) over an SVG that never changes — I is four
layers (base, two loop families, the stack), II five (one per ring), III
two (the steady contours, the breathing thirds), IV one, the eye four
(sclera, follow, saccade, lids) — so each SVG is rasterised once and the
motion is the compositor's; the engraving draws at 20 fps with 4.5-unit
sampling and 7.4-unit cross-hatch pitch; nothing idles unless the row is
on stage (acts 2–4). The eye: iris 52–118, pupil 40, in a sclera out to
206; it arrives **closed** — two black caps meeting at its centre — and the
scroll step that centres it (`--panExtra`, 0.40–0.42) opens the lids on a
smoothstep; the blink runs on an inner layer on its own clock; the pointer
follow writes to the follow layer's transform directly.

**Round 1, eighth pass — the film drives itself from IV to VI.** Owner:
study I drew before the gallery's frames had merged; the caps parting did
not read as lids lifting; IV should not simply appear but gather from
dots; from IV's arrival the reader should be made to watch — scroll
refused — until the engraving is done; and a fast scroll into MGDA flashed
the finished wordmark for a frame. Done: act 2 now begins at 0.175 (after
the merge), and the act list gained a boundary at 0.30 (IV's arrival), so
the closing acts are 7 and 8. Entering act 4 from below starts a 10 s
`power1.inOut` tween of the window scroll from local 0.30 to 0.545 — IV
gathering, the eye opening, its hold, the last step to VI — with the wheel,
touch and keys refused until it completes; scrolling back through the
stretch later is an ordinary scrub. IV's 1,300 dots each arrive from their
own scatter (260–680 units out) on the study's arrival ease, the far ones
last. The eye now sits inside an **almond clip** — an ellipse whose height
runs from a 1.2% slit to the full circle on `--panExtra`, the lids lifting
— with the blink as the same clip closing on an inner layer, and a drawn
lid line round the eye. The wordmark's initial state is applied in a
layout effect, synchronously before the act's first paint; no frame shows
the finished mark before the point. Two follow-ups from checking: the row
itself now appears only at 0.172 (before act 2 study I rests fully drawn,
and showing the row from 0.12 had put the finished figure under the
converging frames — the overlap in the owner's first screenshot); and the
spiral's gather is keyed to `--arrived` 3 → 4 rather than the study's own
entrance, so IV slides in as a cloud and gathers inside the self-driven
stretch. Verified frozen: at 0.15 only the merged ring is on screen; at
0.30 the spiral's dots sit 260–680 units out, at 0.318 mid-gather, at
0.335 in place; the eye's clip reads 1.2% at 0.37, 25.1% at 0.41, 49% at
0.46. The self-driven stretch and the wordmark's first frame cannot be
exercised in the harness (no rAF, and the act is set on the DOM rather
than through React) — judge on the machine.

**Round 1, ninth pass — the ellipsis as one film; the section off the
style pass when off stage.** Owner: the six-circle stretch still dropped
frames; the frames-to-ring hand-off was "not smart" (a ring with no
drawing if the wheel stopped at 0.16); IV need not gather; the whole
six-circle stretch should refuse scroll and play at our tempo, then
release into the sentence; a small stutter from MGDA into Contribution.
Done:
- One film for the ellipsis. Crossing 0.09 from below starts a 20 s
  `power1.inOut` drive of the scroll to 0.545 — the frames' flight and
  merge, study I drawing itself, II–VI arriving, the step to the eye, its
  opening and hold, the last step to the engraving — with the wheel, touch
  and keys refused until it completes; the reader then scrolls into the
  sentence. The separate act-2 lock and act-4 drive are gone (`playFilm`
  in HomeDesktop serves both sections).
- Off stage, off the style pass: the row (`display: none` outside acts
  1–5), the frames (1–2), the sentence and rules (5–6), the screen and the
  set's line (6). Until now every scroll frame of the whole section
  recomputed ~6,000 marks' and 1,352 people's custom properties.
- The unravel is one `clip-path` wipe per stage (six elements), not a
  dash offset on every stroke; the spiral arrives whole.
- Contribution's scene renders only when its progress has moved, and is
  kept warm from Identity's act 7 so the hand-over does not pay for a
  first frame.
Verified frozen: the gating table (row/frames/bridge/screen) at acts 0, 2,
5, 6, 7; the wipe at 0.56 (`inset(0 60% 0 0)`).

**Round 1, tenth pass — three studies.** Owner: the wipe on the
engraving's exit and the eye's closed slit both read as bugs; scrolling
the gallery landed straight on a finished study I, which then flickered
and redrew; cut II, III and IV — keep the line, the eye and the
engraving; and Contribution's film felt like the page acting on its own —
revert it. Done: the row is I · the line, II · the eye, III · the
engraving; the timeline closes up (arrivals 0.22–0.28, the step to the
eye 0.30–0.32 where it opens, the hold to 0.42, the last step 0.42–0.45,
the studies leave 0.45–0.50, the sentence 0.455–0.515); the film runs
0.09 → 0.46 in 16 s; the clip wipe is gone (the studies leave with the
viewport's contraction and fade; only the engraving unrolls). The
flicker: the row was displayed from 0.172 while study I's rest state is
fully drawn, and act 2 at 0.175 then replayed the draw from nothing —
the row now exists only from act 2 (`display`) and fades from the same
0.175, so its first painted frame carries the draw-in. Contribution is
scroll-bound again.

**Round 1, eleventh pass — the film in segments.** Owner: the chain from
the gallery to the three circles was broken in practice — the circle
appeared hard, redrew hard, the redraw was skipped, and the row moved on
before anything finished. Two causes. The single 16 s sweep never paused:
the row was dragged into its arrivals while study I was still drawing
(delays ran to 5 s), and the act change then snapped the strokes to
drawn. And the merged ring faded (0.17–0.19) before study I's base circle
had drawn itself — a circle vanishing and being redrawn. Done: the film
is a GSAP timeline of five segments of local progress — 0.09 → 0.176 in
3 s (the frames fly and merge); a 5.5 s hold at 0.176 (study I draws:
loops at 0.3 s + 0.045 s × i, 2.2 s each); → 0.34 in 5.5 s (the eye and
the engraving arrive, a step to the eye, the eye opens over 0.30–0.34);
→ 0.42 in 3.5 s (on the eye, following the pointer); → 0.46 in 2.5 s (the
last step, the engraving centred); then input is released and the reader
scrolls into the sentence. The base circle is no longer drawn at all — it
is the ring the frames merged into, geometrically identical, so the ring
hands over the instant the row exists (0.175 → 0.18) and only the loops
draw.

**Round 1, twelfth pass — the film's beats checked frozen.** Freezing the
eleventh pass showed two faults the owner would have met live. The 5.5 s
hold sat at 0.176, where the row's fade had only reached 0.2 — study I
drew itself at a fifth of its brightness under the still-visible ring.
And the eye's lids were scrubbed on the same variable as the step to the
eye, so it opened while still sliding in. Done: the hold sits at 0.18
(row fully up, ring gone — verified: frames' opacity 0, row 1, base circle
drawn at rest); the lids have their own beat, `--eyeLift` over 0.34–0.38,
after the eye is centred (verified: eye centred at the pane's centre with
the clip at its 1.2% slit at 0.34, fully open at 0.38); the last step is
0.38–0.45 and the film ends at 0.45 exactly, the engraving centred and
untouched (verified: centred, stage transform identity, rules at 0) — the
reader's first wheel turn then starts the unroll. Six segments: 0.09 →
0.18 in 3 s (frames fly and merge); hold 5.5 s (study I draws — its last
loop lands at 5.47 s); → 0.34 in 5 s (the eye and the engraving arrive;
one step); → 0.38 in 2.4 s (the lids lift); hold 3 s (the open eye looks
about, follows the pointer); → 0.45 in 2.5 s (the last step); 21.4 s in
all. The film's own timing — the GSAP tween driving `scrollTo` — cannot be
run in the harness (no animation frames while the pane is hidden); only
the frozen states above are verified, the tempo is for the owner.

**Round 1, thirteenth pass — tempo and the frame budget.** Owner: the
step from circle I to the eye and the step to the engraving were both a
little slow, the eye's opening stuttered, and frames still dropped —
"slow reads as jank". Three causes found and removed. (1) The eye's lids
were a `clip-path` ellipse over the whole eye stack, scrubbed per frame:
every frame of the opening (and of each blink) repainted ~2,200 marks on
the main thread. The lids are now two black plates whose edges are arcs
of the eye's own circle — closed, the arcs meet at the centre; each moved
by one radius (48.64% of the stage) they coincide with the circle — as
transform layers, the blink a transform on their inner layers; nothing
repaints. A hairline seam marks the closed lids. (2) The engraving's
hatching (~150 filled ribbons, 4–8 ms) was drawn on the main thread every
50 ms — a dropped scroll frame in three during the film. It now renders
in a Worker into an OffscreenCanvas and arrives as ImageBitmaps that the
page's canvas presents through a `bitmaprenderer` context; the same
program runs on the main thread only where OffscreenCanvas is missing.
(3) The eye's pointer-follow measured its rect on every pointer move —
with the film dirtying style every frame, a forced layout per move; it
now re-measures at most four times a second. Tempo: the beats run back
to back with no idle stretch — arrivals 0.19–0.26, the step 0.26–0.30,
the lids 0.30–0.34 (linear in the variable; the film's ease is the lids'
ease), the hold at 0.34, the last step 0.34–0.45 — and the film is 3 s
(fly) · 5.5 s (draw) · 3.2 s (arrive + step) · 1.4 s (lids, `power2.out`)
· 2.4 s (hold) · 1.8 s (last step): 17.3 s, from 21.4. Act boundaries
moved to where the film rests or nothing visible moves (0.175, 0.19,
0.34, 0.45), since each act change re-renders the section and recalcs its
style; the row is displayed from act 1 at opacity 0 so its layers exist
before the hand-over. Verified frozen: the row present and invisible at
0.15; the eye centred with the lids at rest at 0.30, half parted (±107
of 440) at 0.32, whole (±214) at 0.34; the arrivals mid-way at 0.23; the
engraving centred at 0.45; the canvas presenting through `bitmaprenderer`
with a non-blank first frame; no console errors. The film's tempo and
the frame rate themselves can only be judged live.

**Round 1, fourteenth pass — one motion to the eye; the field off the
main thread.** Owner: circle I to the eye still slow; the engraving a
little dark; the dot field's animation later stutters badly. Done: (1)
the eye and the engraving no longer arrive and THEN step — the row moves
with them (arrivals 0.19–0.25, the pan 0.20–0.26), one motion that ends
with the eye centred, in 2.2 s (`power1.inOut`); the lids 0.26–0.30 in
1.3 s; the hold 2.2 s; the last step 0.30–0.45 in 1.6 s — 15.8 s in all,
from 17.3; act boundaries now 0.175 / 0.19 / 0.30 / 0.45. (2) The
engraving gets a faint ground tone over the disc (7%), a heavier hatch
base (0.3 from 0.16, weight 0.5 from 0.46), and brighter cross-hatch,
guides and outline. (3) The field and the crowd — 1,352 marks, 2,704
circles — were an SVG with per-mark custom properties: every scroll
frame of act 6 recomputed the field's style, re-laid it out and
repainted it, 15–25 ms. It is now `identity/CrowdField.tsx`: one canvas,
drawn by a Worker into an OffscreenCanvas from the progress value it is
sent (HomeDesktop writes the section's progress to a ref every frame;
the component posts it only when it changes, only in act 6), presented
through a `bitmaprenderer` context; the same program — the marks'
geometry, the flight through their hue, the bodies, the run — draws
straight into the canvas where OffscreenCanvas is missing. The DOM in
act 6 holds one element where it held 4,000. `--gridIn`, `--crowd` and
`--run` stay in the stylesheet as the documented beats; nothing in CSS
reads them. Verified frozen: at 0.23 study I 253 px left of centre with
the eye half-way in and the engraving still entering (one motion); the
eye centred with lids closed at 0.26 and open at 0.30; the engraving
centred at 0.45; the field mid-flight at 0.64, at rest with bodies at
0.70, running at 0.745, presented by the Worker's bitmaps (a dev-only
`window.__mgdaCrowd.draw(p)` hook drives it in the harness); no console
or server errors. Frame rate and tempo are for the owner, live.

**Round 1, fifteenth pass — the field's blink; the standing start.**
Owner: where the line becomes the field, a small figure/ground gesture —
an eye closing, a mouth opening — would give the field a hint, kept
restrained, two or three seconds; and the gallery-to-circle transition
still hesitates a little. Done: (1) THE BLINK. The first time the field
comes to rest an eye opens in it in negative — the marks inside an
almond (460 × 260 of the 1000 × 620 field, a lens with pointed ends,
soft-edged) shrink away; those inside the pupil (radius 56) stay, larger
and at full brightness, a positive figure inside the negative one — it
glances 26 units to the right, and closes; the field is whole again.
2.4 s on the field's own clock (open 0.72 s ease-out, held, closed over
0.62 s), once per visit, drawn by the same Worker (`CrowdField.tsx`: the
program returns whether the figure is live and the Worker keeps posting
frames at 30 fps while it is). The page holds for it: the first scrub
down through the rest point (0.685; a real scrub, not a nav jump's leap,
never scrolling back up) snaps the scroll to the point in 0.35 s and
holds 2.7 s with input refused — the studies' film language, one beat
long. The field's beats were re-spaced so the rest is a real rest: the
marks land by 0.682, the bodies rise 0.69–0.72, the run is 0.72–0.776.
(2) THE START. The film's first segment is an ease-OUT (2.4 s, from 3 s
in-out): the reader is already moving when the frames begin to fly, and
a standing start there read as the hesitation. Two more things that paid
at that instant are gone from it: the eye's two halftones — ~2,200 SVG
elements that every scroll frame of the section recomputed (an inherited
custom property changes each frame) and each act change repainted — are
now two SVG *images* (data URIs; an image inherits nothing and is
rasterised once), and the studies' row exists from the section's first
paint (opacity 0 until 0.175) instead of being created at act 1, so
nothing is built at the hand-over. Identity's DOM is 384 elements.
Verified frozen: the row present and invisible at 0.05 with both images
loaded and no inline circles; the eye whole at 0.30; at 0.685 the field
at rest, then the eye open in negative with its pupil, then closing,
then the field whole (four frames over ~3 s from the Worker); the bodies
rising at 0.705; no console or server errors. The hold itself and the
tempo of the start are for the owner, live.

**Round 1, sixteenth pass — the figure in both signs; the engraving lights
up; a nav jump wins.** Owner: the field's eye could be refined by joining
the negative figure to the field's positive form; the engraving arrives
without any effect and should light up like a highlight; clicking a nav
title during the studies' film jumped and then snapped back. Done: (1) the
eye is drawn in negative and positive at once — inside the almond the marks
shrink away, along its edge they swell and brighten into the lids' line, in
the pupil they stay large and bright with a faint iris ring between; 2.8 s
(open 0.78 s, held with a glance, closed over 0.67 s), the hold 3.1 s. (2)
Study III enters at 55% brightness and lights up as the row brings it to the
centre (brightness and a soft glow on `--panExtra2`), then breathes at rest
in act 5 until the reader moves. (3) `goToSection` kills any film in
progress before it jumps — the film's tween had kept driving `scrollTo` and
dragged the page back.

Remaining (rounds 2–3): the frames' outlines could lift *from* the
gallery's own plates rather than from above; III's arrows should ease at
the arcs' ends; a reduced-motion pass on the studies; the settled line
"from the dots" (F3 rule 5) is still a blur-resolve.
