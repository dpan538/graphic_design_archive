# Deferred Visual Design

This round freezes functional and semantic behavior, not TRACE's final visual identity. The functional prototype should be neutral, legible, spatially clear, and operable; it is intentionally not a visual-design precedent.

## Frozen for the redesign handoff

- `TraceContextDataset` remains immutable and renderer-neutral.
- Controlled assignments, curated memberships, and accepted semantic edges remain distinct types and labels.
- Users add/hide entities only; dataset-backed connections appear automatically and cannot be authored or edited.
- The four template IDs, versioned deterministic initialization, local-only composition meaning, and default `context-overview` remain stable.
- World-coordinate positions, typed-lane layout seam, orthogonal geometry helper, fit behavior, zoom bounds, and 50-state history remain pure functional contracts unless deliberately versioned.
- Palette button add, node keyboard movement, selection, inspector facts, accessible rows, status semantics, and narrow-screen operability remain required.
- PNG export remains canvas-only, public-safe, full-content, native-browser, and 2× by default.
- The prototype remains unlinked/noindex and synthetic-only until a governed public Context projection exists.

## Intentionally redesignable

| Surface | May change later | Must not change implicitly |
|---|---|---|
| Typography | Families, scale, rhythm, wrapping, label hierarchy | Accessible names, readable labels, stable IDs |
| Color | Palette, category tokens, background, states | Semantic category distinction, contrast, non-color cues |
| Spacing/layout presentation | Panel proportions, gaps, density, responsive composition | Deterministic template result and non-overlap at supported workload |
| Nodes | Shape, borders, field arrangement, metadata hierarchy | Entity identity, root protection, drag/focus/selection behavior |
| Connections | Stroke, arrow/port treatment, label presentation, hit area | Typed category, endpoint truth, deterministic geometry input, no authoring affordance |
| Toolbar/panels | Grouping, icons, disclosure pattern, narrow-screen sheets | Control semantics, accessible names, keyboard/button alternatives, disabled/busy states |
| Motion | Transitions and feedback | Reduced-motion behavior, deterministic committed state, no semantic implication |
| Export appearance | Background, padding, node/edge styling, optional footer treatment | Full-content bounds, safe fields, chrome exclusion, 2× default pipeline |

The redesign may replace React markup and CSS and may introduce presentation components around the pure state/layout/export contracts. It should not move semantic decisions into visual components or infer meaning from proximity, line style, position, or animation.

## Explicitly not designed in this round

Final colors, typography, spacing scale, motion language, brand system, node/edge appearance, toolbar appearance, icon system, pixel visual system, and polished mobile layout are deferred. The old archive-box/folder skeuomorphic language is not a fallback.

No visual or component scaffolding is authorized here for Spacetime maps/time controls or Exploration Field lattices, scores, seeds, factors, or 8–10 template families. Those functions have separate future research and governance work.

## Redesign acceptance checklist

Before replacing the prototype presentation, the later frontend round should verify:

1. pure module inputs/outputs and all `CTX-CANVAS-INV-001..018` still pass;
2. every displayed connection retains its dataset category and accessible-row counterpart;
3. entity add/hide/move actions remain local composition actions;
4. keyboard, focus, status, touch, and narrow-screen paths remain complete;
5. export uses the same committed geometry and contains no application chrome/private metadata;
6. real data remains blocked until a governed public Context projection is supplied;
7. visual review is performed by the user separately from this no-preview functional round.
