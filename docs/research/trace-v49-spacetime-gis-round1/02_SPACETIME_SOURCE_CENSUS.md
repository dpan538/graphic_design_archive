# Spacetime source census

## Frozen source boundary

The census is release-pinned to research release `v49-api-contract-fresh-c` with research-manifest SHA-256 `4addfdb3cb9314587908096572242b9d63e9cef9e6e1be68c0c646491a43a90a`. The generator binds its inputs by SHA-256 in the Spacetime manifest. Generation reads the frozen release profile, surface-row ledger, freeze record, and prefreeze SQLite source; the public runtime reads only the committed projection.

The SQLite and ledger sources are generation/reconciliation authorities. They are not browser payloads, API dependencies, or runtime geography stores.

## Public and held population

| Measure | Count |
| --- | ---: |
| Public objects | 7,995 |
| Held identities | 7,928 |
| Held objects projected | 0 |
| Geography assignments | 7,996 |
| Public objects with geography | 7,995 |
| Public objects with time | 7,995 |
| Multi-region public objects | 1 |

No held identifier is written into the generated projection or Round 4 evidence.

## Geography census

The frozen object surface has 94 distinct raw region displays. The typed controlled-region surface has 93 labels. One release diagnostic differs: raw `Mexico City` versus typed governed `Mexico` for one public record. The typed assignment governs; the raw display remains provenance-only and does not create a city coordinate or second map assignment.

All 93 typed labels have an explicit registry decision:

| State | Registry entries | Public objects |
| --- | ---: | ---: |
| Mapped | 81 | 7,800 |
| Aggregate-only | 11 | 194 |
| Unmapped | 1 | 1 |
| Held | 0 | 0 |

Mapped entries resolve to 84 Natural Earth geometry targets because three governed transnational labels use explicit two-geometry mappings. There are no public historical-status entries and no unresolved-class entries. This is an observed property of this release, not permission to silently normalize such labels in a later release.

The single multi-region public record retains two governed geography assignments. Assignment count can therefore exceed object count by one. Per-period `geographyAssignmentCount` must not be confused with the unique-record denominator.

## Temporal census

| Precision | Count |
| --- | ---: |
| Year | 7,552 |
| Approximate | 305 |
| Day | 78 |
| Month | 27 |
| Range | 33 |
| Unknown | 0 |
| Total | 7,995 |

The governed year extent is 1800–2026 inclusive. Original display text remains on each server-only record summary alongside its inclusive start/end years, precision, and derivation method.

The corrected precision census supersedes the earlier approximate 344/day 66/month 0 handoff. Classification order first preserves explicit ranges, then exact day and month forms, then exact years, and finally qualified/lexically approximate forms.

## Safe identity boundary

Public geography IDs are opaque `SPTGEO:<sha256>` values derived deterministically from the release-pinned controlled-region identity namespace. Private folder IDs are generator inputs only and are never emitted. The registry separately retains the public source-label SHA-256 so label identity can be audited without using label text as the public identifier.

The server-only record index contains public stable object IDs and selected read-model fields. It does not contain held rows, internal UUIDs, private folder IDs, Context projections, exact object coordinates, or semantic edges.
