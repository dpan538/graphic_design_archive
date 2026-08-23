# Real-Data Shape and Label Report

## Association shape

The frozen source contains 47,982 distinct canonical `(surface_id, folder_id)` pairs. The public projection uses 24,102 proposed folder memberships and derives 16,106 controlled-assignment candidates from the medium, theme, and movement subset.

| Projected group | Instances | Objects | Minimum | P50 | P95 | P99 | Maximum |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Controlled assignments | 16,106 | 7,995 | 2 | 2 | 2 | 3 | 4 |
| Curated memberships | 24,102 | 7,995 | 3 | 3 | 3 | 4 | 5 |
| Combined associations | 40,208 | 7,995 | 5 | 5 | 5 | 7 | 9 |

Seven public objects have multiple values within one typed category: five movement cases, one theme case, and one region case. The full verifier found zero entity-ID collisions, connection-ID collisions, conflicting labels for one identity, undocumented connection categories, or source-label mutations.

## Label distribution

Lengths use the current grapheme-aware display policy. Counts are occurrences, not unique strings. Candidate label values are intentionally not reproduced.

| Label population | Count | Min | P50 | P90 | P95 | P99 | Max | Non-ASCII | Han | Diacritic | Multiline | Control-bearing | XML-special | Truncation required | Invalid |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Public object title | 7,995 | 2 | 23 | 84 | 109 | 163 | 806 | 691 | 1 | 470 | 0 | 2 | 828 | 4,640 | 0 |
| Controlled-assignment occurrence | 16,106 | 6 | 28 | 39 | 39 | 41 | 52 | 0 | 0 | 0 | 0 | 0 | 0 | 8,958 | 0 |
| Curated-membership occurrence | 24,102 | 4 | 14 | 39 | 39 | 41 | 52 | 0 | 0 | 0 | 0 | 0 | 0 | 9,426 | 0 |
| All projected occurrences | 48,203 | 2 | 14 | 39 | 46 | 103 | 806 | 691 | 1 | 470 | 0 | 2 | 828 | 23,024 | 0 |

```text
DISPLAY_LABEL_POLICY_VERSION=1
LABEL_COUNT=48203
LABEL_P50_LENGTH=14
LABEL_P95_LENGTH=46
LABEL_P99_LENGTH=103
LABEL_MAX_LENGTH=806
DISPLAY_TRUNCATION_REQUIRED_COUNT=23024
EMPTY_LABEL_COUNT=0
INVALID_LABEL_COUNT=0
SOURCE_LABEL_MUTATION_COUNT=0
```

The two control-bearing titles are valid under the display/export normalization policy and produced no invalid label, malformed XML, or source mutation. The verifier found 155 repeated public object-title strings attached to different public identities; this is permitted because titles are not identifiers. Controlled and curated candidate labels had zero same-label/different-identity cases, and every identity class remained hash/stable-ID based.

## Display policy

`frontend/src/features/trace-v49/context/canvas/display-label.ts` limits node labels to 26 graphemes, node identifier display to 32, and connection labels to 38. It collapses display-only controls and whitespace without mutating `fullText`. The complete source string remains available through the inspector, accessible representation, node `aria-label`, and SVG `<title>`. Export calls the same helper.

The current policy uses `Intl.Segmenter("und", { granularity: "grapheme" })` with an `Array.from` fallback, so raw UTF-16 slicing never separates surrogate pairs. It is a bounded functional policy, not a claim of precise font measurement.

## Missing and multiple values

- Optional movement absence creates no placeholder node.
- Multiple typed values remain distinct by source identity and validation namespace.
- Sorting terminates in stable source or hashed validation identity; SQLite row order is irrelevant.
- Medium/theme/movement typed rows appear in both controlled and curated categories by policy, not accidental duplication.
- Raw `objects.medium` remains deferred and is not projected as a third relation.

## Measured selected-object payload

| Metric | P50 | P90 | P95 | P99 | Maximum |
| --- | ---: | ---: | ---: | ---: | ---: |
| Entity count | 6 | 6 | 6 | 8 | 10 |
| Connection count | 5 | 5 | 5 | 7 | 9 |
| Serialized dataset bytes | 6,167 | 7,047 | 7,434 | 8,882 | 16,510 |
| Accessible-row count | 6 | 6 | 6 | 8 | 10 |
| Export SVG bytes | 6,496 | 6,906 | 7,091 | 8,903 | 12,050 |
