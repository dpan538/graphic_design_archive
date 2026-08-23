# Exploration source inventory

## Authoritative cohort and inputs

Analysis is release-bounded to 7,995 public objects. The frozen candidate population contains 15,923 objects partitioned into 7,995 public and 7,928 held with no overlap. Held structures may be inspected to validate aggregate boundaries, but held identifiers and rows never enter committed Exploration statistics.

The deterministic loader reconciles these inputs rather than allowing any one source to repair another:

| Input | Role | SHA-256 |
| --- | --- | --- |
| Frozen candidate JSON | Canonical object and legacy curated-structure substrate | `b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48` |
| Immutable SQLite candidate | Internal structural cross-check | `ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e` |
| Eligibility ledger | Public/held boundary | `48f98f68ca2ec0cef96c82ecc9c01e4129eb9a3f91e08b07ad9a59644a9d4e01` |
| Governed Context projection | Public medium/theme/movement features | `825f6ecaa9ae1496c8a00ea0fefa5c90319046cf9c1f08a2ef76b9b02df4baeb` |
| Governed Spacetime projection | Public time/geography features | `f751b0f432ff684fd1000201b910aa397a4d9965468c2f7dd5022d6a4ae01c06` |

The loader verifies governed artifact files against their manifests before using them. Public metadata fields such as source, creator, and object type remain analysis-only metadata; they are not promoted to governed Context terms.

## Source and structure census

The public cohort has 15 normalized source values. The current candidate structure contains:

| Structure | Count |
| --- | ---: |
| Objects / dossiers | 15,923 / 15,923 |
| Folders / folder types | 185 / 4 |
| Membership assignments | 47,982 |
| Reading notes | 354 |
| Registration cards | 185 |
| Appendices | 15,453 |
| Compound-child references | 132 |
| Related-folder directed references / undirected edges | 2,016 / 1,008 |
| Legacy trace trees / branches | 30 / 85 |
| Dossier pages | 46,961 |
| Bookmarks | 0 |

The observed folder-type container counts are medium 10, theme 8, movement 11, and region 156. These are actual observed types; no additional type is invented to satisfy a template.

## Twenty-structure registry

The sanitized registry records 20 source/curatorial structures: 16 populated and 4 empty. Populated does not mean public or safe. The important states are:

- public governed: governed Context representations and governed Spacetime geography;
- candidate/internal/unsafe: raw folder membership and the folder-related graph;
- legacy/internal/unsafe: appendices, compound children, trace trees/branches, object-trace-edge membership, reading notes, registration cards, dossiers, source collections, source documents, and SQLite trace structures;
- empty: accepted semantic relations and the governed TRACE projection are known fail-closed public-governed empties; bookmarks are a known legacy/internal empty; the sealed public folder-membership release is a known candidate empty. No structure remains `UNKNOWN`.

Four duplicate representations of the canonical membership relation each contain 47,982 assignments and share the same pair digest `b2ddbe94f4d569f6b9970246855b535374b7c1a9b8ac047de58899c860bd4573`. They are duplicate views and are explicitly non-additive.

## Signal-family inventory

The 64-signal registry covers eight families:

1. governed Context;
2. governed temporal;
3. governed geography;
4. source/corpus composition;
5. descriptive metadata;
6. curatorial structure;
7. missingness/uncertainty;
8. frequency, intersection, and concentration.

Thirteen usable dimensions are inventoried in the cross-dimensional receipt. Geographic distance, rights/image state, and raw source collection are deferred because no governed semantics or public-safe class supports them.

## Public/private boundary

Committed outputs contain aggregate rows only, except that the 15-case pathological register may contain approved stable public object IDs for reproducible regression. No held ID, internal UUID, URL, raw private folder token, title, object-vector row, normalized source row, full object-pair row, or Cartesian zero cell is committed.
