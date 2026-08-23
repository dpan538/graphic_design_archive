# Minimal Future TRACE Public Read Models

The current empty atlas/object/relation-type contracts remain honest. This round does not implement endpoints. The smallest useful future expansion is five release-owned resources; relation/claim detail should not be added until governed rows exist.

| Resource | Purpose | Required public source/fields | Explicit exclusions and rules | Cardinality / provisional payload |
|---|---|---|---|---|
| TRACE availability summary | distinguish ready, empty, not-published, held, unknown, error | release pair; domain state; reason codes; exact denominators; last governed build identity | no inference from empty arrays; no raw counts presented as public data | 1 resource; current atlas 547 B |
| object TRACE summary | route an eligible public object to domain availability | public object stable ID; release pair; per-domain state/counts; missingness | held objects; internal UUIDs; raw payload; unreviewed relation count as semantic | 1/object; expected <1 KiB |
| context dataset | typed assignments/memberships plus separately accepted relations | selected public ref; stable public term/container IDs; kind/state; accepted edges with registered predicate/evidence refs; counts/denominator; accessible rows | raw labels without review; held endpoints; membership→edge inference | P50/P95/max associations 5/5/9; prototype ~4.3/4.2/7.0 KiB |
| spacetime dataset | role/precision-preserving events and aggregates | selected ref; place/time stable IDs; role; precision; start/end; coordinate value + provenance + evidence; unknown/unmapped/denominator; accessible rows | generic exact place/date; source-authority geography relabeled as object role; unproven coordinates | 2 candidates/object currently, 0 mapped; prototype ~1.9 KiB |
| sources/evidence dataset | explicit object/source/evidence/claim chain | public-safe source/evidence/claim IDs and labels; typed link role; locator availability; review/publication state; accepted edge refs; accessible rows | raw URL/locator/UUID; citation⇒support; row count⇒certainty | current governed cardinality 0; source bridge 1; prototype ~1.6 KiB |

All resources must:

- pin exact `researchReleaseId` and `researchManifestSha256`;
- select only the 7,995 release-owned public object cohort;
- reject any archive-object endpoint outside that cohort;
- use stable public IDs created by a governed projection, never pass through internal UUIDs;
- preserve explicit availability state;
- expose denominators and missingness for aggregates;
- paginate any list that can grow; bind cursors to release, resource, filters, and deterministic order;
- satisfy relation-type evidence policy before emitting an accepted semantic edge;
- carry an accessible non-graphic representation as the semantic reference.

Expected payload sizes are neutral-model benchmark evidence, not API commitments. Re-measure after serializer design and real governed population.

Deferred resources: relation-type registry, relation detail, claim/evidence detail, and release-level distributions. Their current populations are zero, so creating non-empty contracts now would invite invented semantics. Aggregate distributions become eligible only after role/precision governance and publication review.

```text
TRACE_PUBLIC_READ_MODEL_READY=false
```

Requirements are known; the underlying reviewed/public projections are not ready.
