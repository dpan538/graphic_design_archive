# Curatorial validation

## Population and duplicate-view integrity

The cohort reconciles 15,923 objects into 7,995 public and 7,928 held with zero overlap. Four candidate views each contain the same 47,982 membership assignments and digest `b2ddbe94f4d569f6b9970246855b535374b7c1a9b8ac047de58899c860bd4573`. The generator and verifier enforce non-additive duplicate views.

The structure registry contains exactly 20 rows: 16 populated and four empty. Classification counts are exact:

```text
CANDIDATE=4
EMPTY=4
INTERNAL_ONLY=15
LEGACY_ONLY=15
POPULATED=16
PUBLIC_GOVERNED=4
UNSAFE=14
UNKNOWN=0
```

The governed TRACE projection is a known fail-closed empty with classifications `EMPTY` and `PUBLIC_GOVERNED`; it is not `UNKNOWN`.

## Semantic hardening

Every applicable public/held memberships-per-object distribution contains exact integer `multipleCount`; 24 applicable receipts pass. Non-applicable graph/public-only cases retain explicit rationales.

Key exact values include:

| Structure | Public multiple | Held multiple |
| --- | ---: | ---: |
| Folder membership | 7,995 | 7,928 |
| Legacy trace branches | 7,993 | 7,928 |
| Research dossiers | 7,995 | 7,458 |
| Reading notes | 7,995 | 7,928 |
| Object trace edges | 7,995 | 7,928 |
| Compound parents | 15 | 0 |
| Governed Spacetime geography | 1 | N/A |
| Appendices | 0 | 0 |

Graph/scalar counts no longer masquerade as object memberships:

- folder-related graph: `membershipCount=0`, `directedReferenceCount=2016`, `undirectedEdgeCount=1008`;
- SQLite trace nodes: `membershipCount=0`, `structureRowCount=97889`;
- SQLite trace edges: `membershipCount=0`, `structureRowCount=255695`.

## Public folder and overlap census

The public folder substrate has 24,102 memberships across 118 nonempty containers. Memberships/object P50/P95/max is 3/3/5; container size P50/P95/max is 11.5/547.55/7,105. All 7,995 public objects have multiple memberships.

Exact aggregate co-membership: 43,891,194 raw pair events and 28,008,976 unique public pairs sharing at least one container. No pair row or matrix is committed. Fanout and Jaccard remain structural diagnostics only.

Curatorial deterministic receipt SHA: `2fd240562ba627a815489efb2371f47200488443658af6e27e4c9dc2774a29a9`. Structure-registry raw file SHA is sealed in the ledgers.
