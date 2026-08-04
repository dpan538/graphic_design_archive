# Frontend atmosphere refactor — material research interface

Status: visual-system candidate on `codex/v48-trace-visualization`

## Reference translation

The reference set is treated as a design grammar, not as imagery to reproduce.

1. Architectural plates contribute measured grids, fine registration rules, generous margins and evidence framed as a precise window.
2. Instrument design contributes matte charcoal, restrained controls, shallow physical depth and small high-signal indicators.
3. Editorial posters contribute a strong grotesk hierarchy, asymmetric information rails and color used as a locator rather than a background default.
4. The fifth and sixth references contribute layered terrain, contour lines, sampling dots, narrow data bands and a dark central analytical field surrounded by warm stock.
5. The final two references contribute sparse annotation, photographic evidence embedded in drawing, subdued coral marking lines and tactile, slightly desaturated color.

## System decisions

### Base material

- Canvas: `#e8e5db`
- Paper: `#efecdf`
- Secondary paper: `#e2dfd3`
- Ink: `#303532`
- Deep analytical field: `#272d2c`
- Rules: `#aaa99f` and `#c6c2b6`

The canvas uses an 18 px measured grid, sparse registration lines and a low-opacity print grain. Cards and drawers are translucent paper layers with shallow, diffuse shadows rather than high-contrast floating boxes.

### Functional color

| Role | Color | Use |
|---|---|---|
| Region | mineral blue `#68859a` | geography and mapped distribution |
| Source | moss `#687e62` | source/provenance branches |
| Movement | mineral violet `#79739b` | movement context |
| Medium | faded coral `#c56f59` | medium/context routes |
| Current focus | coral `#d76d51` | selected evidence and active measurement |
| Secondary signal | cyan `#76b9b1` | reserved analytical signal |

Large areas remain neutral. Functional colors appear on rules, nodes, relation lines, focus states and small metadata bands. Color never replaces a label or evidence state.

### TRACE line language

- Medium routes are reduced from heavy bands to 10 px measured lines.
- Source trunks use 5 px hierarchy lines; twigs use 1.5 px evidence lines.
- The metro and rooted tree sit on a charcoal analytical plate with a fine grid and sparse violet sampling texture.
- Selected edges switch to coral and receive a restrained halo.
- The real map remains a warm, low-contrast geographic field; same-period context is a dashed coral line and retains the explicit “not influence” label.

### Readability boundary

The lower-contrast atmosphere is created with surface, line and saturation choices—not by weakening text. Measured WCAG contrast ratios:

- primary ink / canvas: `9.91:1`;
- secondary ink / canvas: `4.94:1`;
- readable relation colors / paper: `5.67:1` to `6.27:1`;
- paper / deep analytical field: `11.84:1`.

## Scope boundary

This refactor changes frontend tokens and presentation only. Frozen v48 JSON, SQLite, TRACE records, counts, relation semantics and image routing are not modified.

## Acceptance evidence

The acceptance set is stored in `docs/capture/trace-v48-atmosphere/` with its own `SHA256SUMS.txt` manifest. It covers:

- the archive home and shared navigation shell;
- all three desktop TRACE readings: medium/context, source/provenance and time/geography;
- the expanded search workspace on desktop and a 390 × 844 mobile viewport;
- the mobile TRACE evidence fallback, time/geography controls and the real-map canvas after scrolling into view.

The final mobile pass found and corrected an overlap between the navigation stack and the three-view selector. The browser console returned no warnings or errors after the correction.

Focused acceptance gates passed for the v48 TRACE asset verifier, the visualization TypeScript project, screenshot checksums, Git LFS integrity and frozen-file hashes. The full production build was not rerun in this atmosphere-only pass; the local Next development server showed unusually slow cold compilation even though the validated routes eventually returned HTTP 200. That build-pipeline latency remains a separate performance risk.
