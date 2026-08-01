# New-chat prompt — design and interaction refinement on frozen v46

You are refining the web experience of `modern_GD_history`, not changing its research data.

## Hard boundary

- Treat `generated/public_surfaces_prefreeze_candidate_v46.json` as read-only.
- Do not run data captures, rebuild candidate JSON, alter TRACE evidence, promote review records, modify source authority, or change active counts.
- Do not use older candidates as the displayed data source.
- Keep `generated/prefreeze_candidate_v46_object_geography_review_hold.json` and `generated/prefreeze_candidate_v46_duplicate_representation_review_hold.json` isolated from active UI counts.
- Do not build the entire project unless a scoped visual check actually requires it. Prefer the current localhost flow and screenshots for acceptance.

## Current frozen baseline

- 15,921 active objects; no active unresolved geography or uncertain authority.
- All active objects have accepted TRACE. TRACE may show documented evidence paths, object place, year, creator, source record, and collection structure.
- There are zero evidence-backed historical `influenced_by` edges. Never draw an influence arrow merely from geographical proximity, shared source, visual resemblance, or temporal overlap.
- Read `docs/capture/PREFREEZE_CANDIDATE_V46_FROZEN.md`, `docs/capture/PREFREEZE_CANDIDATE_V46_TRACE_ATLAS.md`, and `docs/capture/PREFREEZE_CANDIDATE_v46_SEARCH_TRACE.md` before modifying presentation.

## Product direction

The product is a readable, research-led modern graphic-design archive. It should feel like one coherent archive page system, not a grid of isolated cards or A4 sheet replicas.

- Preserve the existing archival visual language: warm paper field, dark typographic anchors, fine structural rules, restrained solid badges/dots, and strong editorial hierarchy.
- Improve hierarchy through typography, grouping, column rhythm, spacing, and explicit reading order — not by adding arbitrary coloured background blocks.
- Translate sheet logic into responsive web layouts: linear, vertically scrollable object pages with structured sections rather than fixed paper containers.
- Desktop may use two-to-four-column editorial combinations where content density permits. Mobile must privilege reading, use progressive disclosure/accordions for long supporting text, and avoid pages longer than roughly eight phone screens before optional sections collapse.
- On mobile, navigation is icon-first at the bottom with browser-safe-area support. The top control area can collapse. Do not add cork-like visual trim: tactile feedback means subtle pressed states and, only if already permitted by browser/user settings, optional quiet click feedback.
- Avoid repeated decorative motifs at short intervals, decorative long black vertical bars on mobile, concentric ring ornaments, and visual elements that look like controls but are not controls.
- Large titles may enlarge only their first one or two lines on mobile; remaining title text must step down cleanly with no clipping or overflow.

## TRACE and search interaction

- Search should look intelligent through transparent query interpretation, suggested refinements, and clear evidence summaries — not through an ungrounded AI persona.
- TRACE needs three distinct visual modes:
  1. selected-object lineage expanded on demand;
  2. geography × decade aggregation;
  3. source-family × object-geography matrix.
- Never render the full 45k-node active TRACE graph in the browser. Use aggregate payloads and capped selected-object expansion.
- Use neutral labels for aggregation: `co-located`, `concurrent`, `shared source context`. Reserve historical relationship arrows for direct evidence only.

## Acceptance evidence required

1. Screenshot key pages at desktop and narrow mobile widths using the current localhost instance.
2. Verify no horizontal overflow, title clipping, overlapping controls, inaccessible bottom navigation, or text that becomes unreadably small.
3. Check that every visible button has one unambiguous action and that decor is not mistaken for interaction.
4. Confirm that object page, catalogue/contents, search, TRACE entry point, and a long-text mobile page maintain the same hierarchy.
5. Report changed files, screenshots, remaining design risks, and explicitly confirm that no frozen v46 data artifact changed.
