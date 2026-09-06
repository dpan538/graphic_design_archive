# Exploration presentation — white-box report (2026-09-06)

Scope: the presentation derivation of `features/trace-v49/exploration-view/` (skeleton, templates, forms, render, service, fingerprint), tested through the service without the UI. V2 semantics unchanged.

**Engine.** For a state with n terms the structural engine (`skeleton.ts`) chooses a skeleton family from n and the variant (2: opposed / diagonal / stacked; 3: triangle / chain / arc; 4: clusters / diamond / run; 5–8: ring / rows / spiral), bends it by the state's semantic field (radial / shear / lattice, from the semantic hash), and jitters it by the presentation seed. The template draws its idiom on those positions; the variant also chooses the connection mode (direct / orthogonal / arc) an association's shape runs in. Every connector is a visible V2 association; nothing is drawn between two terms that V2 does not associate.

**Fingerprint.** `presentationFingerprint(scene)` = SHA-256 of the canonical structure: presentation version, template, variant, frame, the field's ground, paper and ink, every definition (gradient stops and directions, the grain's frequency, seed and opacity), every primitive (kind, role, clip, opacity, coordinates, dimensions, radii, path geometry, rotation, fill, stroke), the terms' anchors and regions and the associations' regions. Excluded: vocabulary, titles, the export id, provenance strings, the alt text. `presentationGrammar(scene)` = the histogram of primitive kinds by role plus the terms' spread.

**Seed chain.** presentation seed = FNV-1a(state_hash, "TEMPLATE:variant"); the scene records `semantic <hash12> · seed <n> · skeleton <n> terms · variant <v> · frame <w>×<h>` (the matrix column `layout_seed_used`).

**Canonical states** (one starting point, its complexity ladder): S2 = R16A-STATE-A80ACF6E2D085159CB519F9E (2 terms, 1 associations, semantic b17477021f7c…, field radial); S3 = R16A-STATE-17AA7131B9C7F78E6F839E87 (3 terms, 2 associations, semantic b17477021f7c…, field radial); S4 = R16A-STATE-3128A12EB8ED4537BE35F5CF (4 terms, 3 associations, semantic b17477021f7c…, field radial).

| Test | Status | Detail |
| --- | --- | --- |
| same_input_same_presentation | PASS | 144/144 (3 states × 16 templates × 3 variants) identical fingerprint and SVG on rebuild |
| state_drives_geometry | PASS | 1032/1032 real More transitions change the LINES/0 fingerprint |
| state_drives_geometry_pools | PASS | 66/66 pairs of distinct root pictures differ under GRID/0 across all 26 starting points |
| template_drives_grammar:S2 | PASS | 16/16 distinct fingerprints, 16/16 distinct grammars |
| semantic_invariance:S2 | PASS | research state, terms and associations identical across the 16 templates (R16A-STATE-A80ACF6E2D085159CB519F9E) |
| template_drives_grammar:S3 | PASS | 16/16 distinct fingerprints, 16/16 distinct grammars |
| semantic_invariance:S3 | PASS | research state, terms and associations identical across the 16 templates (R16A-STATE-17AA7131B9C7F78E6F839E87) |
| template_drives_grammar:S4 | PASS | 16/16 distinct fingerprints, 16/16 distinct grammars |
| semantic_invariance:S4 | PASS | research state, terms and associations identical across the 16 templates (R16A-STATE-3128A12EB8ED4537BE35F5CF) |
| variant_drives_presentation_only:DOTS | PASS | 3/3 distinct variant fingerprints, research content identical |
| variant_drives_presentation_only:SPOTS | PASS | 3/3 distinct variant fingerprints, research content identical |
| variant_drives_presentation_only:CHEVRON | PASS | 3/3 distinct variant fingerprints, research content identical |
| variant_drives_presentation_only:CROSSFIELD | PASS | 3/3 distinct variant fingerprints, research content identical |
| variant_drives_presentation_only:LINES | PASS | 3/3 distinct variant fingerprints, research content identical |
| variant_drives_presentation_only:GRID | PASS | 3/3 distinct variant fingerprints, research content identical |
| variant_drives_presentation_only:RAYS | PASS | 3/3 distinct variant fingerprints, research content identical |
| variant_drives_presentation_only:OVERLAP | PASS | 3/3 distinct variant fingerprints, research content identical |
| variant_drives_presentation_only:HALFTONE | PASS | 3/3 distinct variant fingerprints, research content identical |
| variant_drives_presentation_only:STRIPES | PASS | 3/3 distinct variant fingerprints, research content identical |
| variant_drives_presentation_only:PETALS | PASS | 3/3 distinct variant fingerprints, research content identical |
| variant_drives_presentation_only:WAVES | PASS | 3/3 distinct variant fingerprints, research content identical |
| variant_drives_presentation_only:CUBES | PASS | 3/3 distinct variant fingerprints, research content identical |
| variant_drives_presentation_only:ARCS | PASS | 3/3 distinct variant fingerprints, research content identical |
| variant_drives_presentation_only:MOIRE | PASS | 3/3 distinct variant fingerprints, research content identical |
| variant_drives_presentation_only:SCATTER | PASS | 3/3 distinct variant fingerprints, research content identical |
| no_redundant_variants | PASS | every variant of every template draws a different picture on S4 |
| variant_is_structural | PASS | on S4 every pair of variants moves the terms by more than 30px on average — the skeleton family changes with the variant |
| topological_phase_transition | PASS | S2→S3 and S3→S4 under all 16 templates: the shared terms move 108–511px on average (> 30px), the skeleton changes family with the count |
| semantic_field_bends_skeleton | PASS | 2 terms: radial vs shear → 36px, inside margins true; 3 terms: radial vs shear → 37px, inside margins true; 4 terms: radial vs lattice → 61px, inside margins true |
| no_fabricated_edges | PASS | 144 scenes: connectors = the state's visible associations exactly; no association is drawn that V2 does not show |
| seed_chain_derivation | PASS | 48/48 views: presentation seed = FNV-1a(state_hash, template:variant); seed chain = semantic · seed · skeleton · frame |
| no_runtime_randomness | PASS | no Math.random, Date, performance, randomUUID, hrtime or environment in the presentation path |
| volatile_metadata_excluded | PASS | the export id and the vocabulary are absent from the structure and from the view's drawn SVG (the alt text aside) and present only in the export's furniture ledger |
| unsupported_state_fail_closed | PASS | unknown template → INVALID_PRESENTATION; unknown variant → INVALID_PRESENTATION; unknown state → STATE_NOT_FOUND; 9 terms → TEMPLATE_INCOMPATIBLE; variant 3 → INVALID_PRESENTATION_VARIANT |
| all_16_templates_real | PASS | 16 layout functions, 16 template entries, 16 distinct targets |
| screen_export_same_model | PASS | 48/48 views: the export scene shares the view's seed, semantic field, skeleton and associations, laid out for its form's image area; the export SVG is the form's size |

Result: PASS — 36/36 gates.
