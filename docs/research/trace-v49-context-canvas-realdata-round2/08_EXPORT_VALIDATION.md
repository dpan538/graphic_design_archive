# Export Validation

## Shared export contract

The PNG pipeline prepares an SVG snapshot from the current composition, computed bounds, visible nodes, and derived connection geometry. It uses the same display-label fitting helper as the live Canvas and escapes ampersands, angle brackets, quotes, apostrophes, and XML-invalid code points before string construction.

Each node retains the full source label in an SVG `<title>` while bounded display text is rendered inside the rectangle. Real candidate state and category remain present in the accessible/inspector data; export does not relabel a proposed connection accepted.

Export metadata contains only:

- the Context Canvas label;
- the selected public stable ID;
- the validation release ID.

Filename construction sanitizes the public stable ID and redacts UUID-shaped values. Export values are also scanned/redacted for UUID-shaped strings. No raw source URL or held identifier is an intended input.

## Functional limits

```text
DEFAULT_PNG_SCALE=2
MAX_PNG_SCALE=4
MAX_EXPORT_DIMENSION_PX=16384
MAX_EXPORT_PIXEL_AREA=64000000
```

Export work receives an abort signal. A record switch or unmount aborts the old session's pending conversion so an export prepared for Object A cannot complete after Object B becomes current.

## Completed all-object verification

For every one of the 7,995 public datasets, the non-browser verifier prepared SVG snapshots and asserted:

- every visible entity and connection resolves;
- bounds and every path coordinate are finite;
- XML parsing/escaping succeeds;
- source and display labels remain distinct where truncation occurs;
- the filename is safe and deterministic;
- no internal UUID, held stable ID, or prohibited source field appears;
- the result matches the second deterministic pass.

The four-template pass covered 31,980 exports, while the synthetic regression supplied hostile text coverage for XML metacharacters, Unicode graphemes, and invalid controls.

## Evidence status

```text
EXPORT_SVG_PREPARATION_OBJECT_COUNT=7995
EXPORT_SVG_PREPARATION_TEMPLATE_CASES=31980
EXPORT_PREPARATION_FAILURE_COUNT=0
EXPORT_INVALID_XML_COUNT=0
EXPORT_NONFINITE_GEOMETRY_COUNT=0
EXPORT_UNSAFE_FILENAME_COUNT=0
EXPORT_UUID_EXPOSURE_COUNT=0
EXPORT_HELD_EXPOSURE_COUNT=0
EXPORT_MISSING_FULL_LABEL_COUNT=0
EXPORT_SVG_BYTES_P50=6496
EXPORT_SVG_BYTES_P95=7091
EXPORT_SVG_BYTES_P99=8903
EXPORT_SVG_BYTES_MAX=12050
EXPORT_PREPARATION_SHA256=3c88449337f52ece7be2b8bf282812fb2402b020f72ced7984a9a7c03ab410b9
PNG_BROWSER_CONVERSION=USER_REVIEW_PENDING
```

Actual bitmap download is intentionally not claimed: no localhost or browser execution was performed by request.
