# Layout and Connection Validation

## Deterministic geometry

The shared Canvas core uses fixed 224 × 104 node rectangles. Auto-arrange assigns entity IDs, sorted lexically, to fixed lanes:

| Lane | X | Initial Y | Vertical step |
| --- | ---: | ---: | ---: |
| Root | 64 | 72 | 136 |
| Controlled assignment | 384 | 72 | 136 |
| Curated membership | 704 | 72 | 136 |
| Semantic | 1,024 | 72 | 136 |
| Other | 1,344 | 72 | 136 |

The 136-pixel vertical step leaves 32 pixels between 104-pixel-tall nodes. Adjacent lanes are 320 pixels apart, leaving 96 pixels between 224-pixel-wide nodes. For valid lane assignment, these constants make same-lane and cross-lane rectangle overlap impossible by construction. The full verifier enumerated all 31,980 object/template cases and confirmed finite coordinates, contained bounds, valid connectors, and zero overlap.

Bounds include each visible rectangle's full width and height. Viewport fit uses finite positive viewport dimensions, nonnegative padding, and clamps zoom to the Canvas minimum and maximum.

## Connection derivation

Connections are materialized only when both endpoint entity IDs are in the visible set. IDs retain their semantic kind:

- `connection:controlled_assignment:<validation-assignment-id>`;
- `connection:curated_membership:<validation-membership-id>`;
- `connection:semantic_edge:<edge-id>` in synthetic mode only.

Real v49 datasets have no semantic-edge connections. Controlled and curated connections remain separate even when they originate from the same typed folder row.

The connector path is deterministic orthogonal geometry:

```text
M source-port-x source-center-y
H midpoint-x-with-parallel-lane-offset
V target-center-y
H target-port-x
```

Parallel connections are separated by a deterministic 12-pixel midpoint offset. Coordinates are rounded to three decimal places. Accessible connection labels prefer the matching semantic accessible row and otherwise fall back to endpoint labels.

## Template and missing-data behavior

All four templates use the same dataset, layout, connection, bounds, fit, accessibility, persistence, and export functions. Template selection is data-driven: unavailable optional categories produce no fabricated `Unknown`, `N/A`, or missingness node. Multiple medium/theme/movement/membership values remain distinct by validation identity and are sorted deterministically.

## Full-cohort gate

The verifier geometrically exercised every public object in every template:

```text
AUTO_LAYOUT_OBJECT_TEMPLATE_CASES=31980
AUTO_LAYOUT_COLLISION_COUNT=0
NODE_OUTSIDE_COMPUTED_BOUNDS_COUNT=0
NONFINITE_POSITION_COUNT=0
NONFINITE_VIEWPORT_COUNT=0
INVALID_CONNECTOR_COUNT=0
DANGLING_CONNECTION_COUNT=0
DUPLICATE_CONNECTION_ID_COUNT=0
MISSING_ACCESSIBLE_CONNECTION_ROW_COUNT=0
```

No global edge-crossing or visual-aesthetic optimization is in scope.
