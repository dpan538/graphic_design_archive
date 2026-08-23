# Curatorial overlap analysis

## Method

The public co-membership analysis uses an inverted folder index and arbitrary-precision membership bitsets. It computes object fanout and exact aggregate pair counts without emitting pair identifiers or materializing a 7,995-by-7,995 matrix. Public object ordering and every aggregate hash are deterministic.

The four candidate membership views reconcile to the same 47,982-assignment digest. Their repeated representation is non-additive; the analysis uses one canonical relation.

## Fanout diagnostics

| Shared-container threshold | Unique public pairs | Object fanout P50 | P95 | P99 | Max | Zero-fanout objects |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| At least 1 | 28,008,976 | 7,439 | 7,648 | 7,691 | 7,691 | 0 |
| At least 2 | 11,187,747 | 3,225 | 3,861 | 5,600 | 5,600 | 0 |
| At least 3 | 4,693,843 | 170 | 2,955 | 2,955 | 2,957 | 111 |

The high fanout is a property of broad project-curated containers. It is not evidence that most archive objects are historically connected.

Exact shared-container pair counts are:

| Shared containers | Pair count |
| ---: | ---: |
| 1 | 16,821,229 |
| 2 | 6,493,904 |
| 3 | 4,693,225 |
| 4 | 608 |
| 5 | 10 |

## Jaccard diagnostic

Jaccard over curated-container sets was benchmarked only as a `STRUCTURAL_DIAGNOSTIC`. Its P50/P90/P95/P99/max are 0.2/1/1/1/1. A value of 1 can arise because two records share the same small set of project containers; it does not imply identical meaning, historical relation, influence, or creator intent. No final similarity metric is selected.

## Curatorial rarity per object

The rare-membership threshold is public support at most 20. The aggregate object-level receipt contains no object rows or identifiers.

| Feature | P50 | P95 | P99 | Max | Mean |
| --- | ---: | ---: | ---: | ---: | ---: |
| Rarest container support | 562 | 3,214 | 3,214 | 3,214 | 1,426.828768 |
| Most-common container support | 7,105 | 7,105 | 7,105 | 7,105 | 6,636.100438 |
| Rare membership count | 0 | 0 | 1 | 2 | 0.04803 |

7,616 objects have zero rare memberships; 374 have one and five have two. The object-vector SHA is `a647968fb7ce64e6feb12bbd13ba07650caee63b3c90d59781e6488e3f73e032`; no vector is committed. The aggregate receipt SHA is `740792056f954e68eaec18cd423560c266109e1e10ec1a838e09d39371e4a273`.

## Interpretation boundary

Permitted: describe how the archive project grouped the current release, estimate candidate-search fanout, and identify broad or narrow curated containers.

Prohibited: infer historical contact, influence, importance, quality, canonicality, creator intent, calibrated probability, or recommendation rank. Rare does not mean important; common does not mean representative.
