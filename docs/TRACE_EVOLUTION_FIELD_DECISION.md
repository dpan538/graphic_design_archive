# TRACE evolution field — visual and technical decision

Status: implemented candidate on `codex/v48-trace-visualization`

## Purpose

The Global Atlas now treats visual analysis as a primary research surface. It shows how the frozen active-object record changes over time, geography and medium without replacing object evidence pages or implying undocumented historical influence.

The supplied references were translated into four design rules:

1. A dense central field is surrounded by quiet paper, marginal labels and exact measurement rails.
2. Concentric structure supports long-duration reading; the center is early time and the outside is recent time.
3. Layered color behaves like geological strata or analytical light. It is restricted to data marks and current focus.
4. Fine points, ticks and outlines carry detail; large saturated interface surfaces are avoided.

## Evidence mapping

| Graphic mark | Frozen field | Meaning | Explicit non-meaning |
|---|---|---|---|
| Concentric ring | `atlas.decades` | One recorded decade, 1800–2020 | Not a stylistic era boundary |
| Radial axis | `atlas.regionMatrix[].region` | One normalized aggregate geography | Not a cultural route |
| Point area | `atlas.regionMatrix[].counts[]` | Log-scaled active-object count | Not importance or influence |
| Outer tick | `atlas.relationTypes[]` | Documented TRACE relation frequency and family | Not an edge between regions |
| Stacked landscape band | compact catalog `mediumGroup × decade` | Exact active-object count for a display-only medium group | Not reclassification |
| White profile | selected region’s decade counts | The selected geography against the global medium landscape | Not diffusion from that geography |
| Coral cursor | selected decade | Current interaction focus | Not a publication cutoff |

The interface states that it visualizes archive coverage and does not claim geographic diffusion, cultural continuity, causality or historical influence. The v48 influence count remains zero.

## Interaction model

- Hovering or keyboard-focusing a radial point updates the exact region, decade and count readout.
- Activating a non-zero point opens the existing filtered object layer through `exploreCell`; the visualization never creates a separate untraceable result set.
- The time control switches between cumulative development and one-decade inspection.
- Play advances one decade every 720 ms and stops at 2020. Reduced-motion preference disables playback.
- Region selection overlays its exact temporal profile on the global medium landscape.
- Every decade column in the landscape is keyboard focusable and selectable.
- Exact region × decade rails and the table fallback remain below the graphic.

## Mobile behavior

The radial field becomes a sticky research plate. Seven evidence chapters pass over it while the page scrolls; an `IntersectionObserver` updates the selected decade from the chapter currently crossing the reading band. Point visibility and scale transition linearly, producing a scroll-linked development sequence without fabricating intermediate records.

The medium landscape remains available as a high-resolution horizontally scrollable plate rather than being replaced by a simplified decorative card. Chapter cards expose decade totals, cumulative totals and the three leading recorded regions. When CSS view timelines are available, cards enter linearly; reduced-motion users receive the complete static state.

## Loading and performance budget

- The initial radial field uses the compact `atlas.json` aggregate only: 15 region axes × 23 decade rings, with at most 345 interactive cells.
- The 2.6 MB compact active catalog is fetched once and decoded client-side to build exact medium strata.
- No neighborhood shards, review records or auxiliary records are loaded by the evolution field.
- SVG mark count is bounded and deterministic; no force simulation or perpetual animation runs.
- Playback uses one timer and mobile scroll observation uses seven chapter targets.

## Frozen-data boundary

This implementation changes presentation and verification code only. It does not modify v48 JSON, SQLite, active counts, review/hold separation, auxiliary eligibility, object geography, authority evidence, image routing or TRACE edges.

## Acceptance record

Browser acceptance used 1440 × 1000 desktop and 390 × 844 mobile viewports. The captured final state contains 255 non-zero interactive observation points, 20 documented relation ticks, seven medium landscape layers and seven mobile scroll chapters. Console inspection returned no warnings or errors.

Verified interactions:

- cumulative and single-decade modes switch their pressed state;
- playback advances the selected decade and can be paused;
- a United States × 1840s point opens the existing active-object drawer with the same region and decade filters;
- scrolling the mobile story to the 1960s chapter changes the selected decade to index 16 / 1960;
- the medium landscape remains horizontally navigable on a 390 px viewport.

The production build completed optimized compilation in 17.5 minutes and passed its project-wide type phase. It did not complete static generation: the existing build attempts 8,783 pages and multiple unrelated `/surfaces/[id]` routes exceeded Next’s 60-second per-page limit. The build was stopped after it entered repeated retries. TRACE-focused TypeScript and visualization verification pass independently; the full-site static-generation architecture remains a separate release risk.
