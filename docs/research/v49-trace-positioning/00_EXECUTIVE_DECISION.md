# TRACE positioning decision

**Decision date:** 2026-08-16  
**Research scope:** positioning only; no implementation was performed.  
**Release baseline:** `ARCHIVE_OBJECTS=15923`; `RESEARCH_ELIGIBLE_OBJECTS=7995`; `HELD_OBJECTS=7928`; `TRACE_ELIGIBLE_OBJECTS=0`; `POSITIVE_VISUAL_RIGHTS_COVERAGE=0%`; `TARGET_20000_IS_ACCEPTANCE_GATE=false`.

## Decision at a glance

**Recommended one-line positioning.** `graphic_design_archive` is a Digital Humanities research-infrastructure case study for design history: a release-pinned, evidence-bounded navigation system that moves from corpus coverage through curated research pathways to object-level sources, claims, provenance and missingness—without automatically inferring historical influence.

**Primary academic field.** Digital Humanities, specifically design-history digital scholarship. Secondary homes are digital heritage / archival-information science and humanities visual analytics/HCI. It is not principally an influence-network project, digital-preservation repository, or novel visual-analytics technique [SR01][SR02][SR05].

**Primary audience.** Design-history researchers who need to inspect scope, sources and qualifications. Research-active curators and design-history educators/students are secondary; machine clients are infrastructure users; general visitors are tertiary [SR22][SR25].

**Core contribution (conditional, A).** An evidence-bounded, release-pinned method/interface that visibly separates corpus coverage, editorial membership, object-level claims, evidence occurrences, review/provenance and interface projection, and refuses automatic influence inference. It becomes a defensible core contribution only after a deliberately bounded, accepted and auditable claim/relation set plus evaluation exists. It is currently a well-specified research proposition, not an achieved relation-map contribution [SR03][SR04][SR06].

**Secondary contributions (at most three).**

1. **B — Supporting research:** making missingness, qualification, contradiction, contextual/orphan evidence and `HELD` states visible across a macro–meso–micro research path [SR02][SR17].
2. **C — Infrastructure:** release-pinned source/provenance, rights-state and read-only machine-readable records that make a research index inspectable and reusable; this is useful but not unique [SR07][SR22].
3. **D — Product/education:** a carefully labelled route from overview to source dossier for exploratory design-history learning and public interpretation [SR18][SR25].

**Not contributions.** 15,923 objects; a target of 20,000; search/filter; generic API; external image links; graph aesthetics; responsive UI; animation; CI/deployment; and a large data pipeline are infrastructure/product features or portfolio capability signals, not scholarly novelty [SR11][SR13][SR21].

**Two-week decision: GO-NARROW.** Publish the honest, non-relational research-navigation release only if the zero-state, missingness, provenance/rights wording and accessible alternatives are all explicit. Do not publish a relation graph, influence map or implied network.

**20,000 decision.** Stop untargeted collection expansion. Do conditional, gap-specific intake only after source-family normalisation and coverage/missingness measures show a documented deficit; object count is never an acceptance proxy [SR19][SR20].

**Zero-TRACE public strategy.** Use **`TRACE Preview — Evidence Navigation`** (or the safer name **`Evidence Trace`**) with this status in every entry point: “No accepted semantic relations in this release. Explore coverage, curated research pathways and object-level sources; membership, proximity and shared metadata are not evidence of influence.” Do not call it an influence map [SR03][SR16].

## Claim classification

| Major proposed strength | One required classification | Decision |
|---|---|---|
| Evidence-bounded, no-inference TRACE | A. Defensible core contribution | Conditional on accepted, cited, reviewable records and evaluation; otherwise research proposition only. |
| Visible missingness / held / contested states | B. Supporting research contribution | Strong methodological support; effectiveness remains untested. |
| Release provenance, source dossiers, rights state, Read API | C. Infrastructure contribution | Valuable reproducibility and reuse, not a field-first claim. |
| Macro–meso–micro exploratory learning | D. Product/education value | Secondary, pending user evaluation. |
| Responsive visuals, data operations, CI, interface complexity | E. Portfolio capability signal | Strong hiring evidence; no academic novelty claim. |
| Search, filters, generic API, object count, external images | F. Common feature / non-contribution | Mature archives already supply these in various forms. |
| “Influence map”, “network”, “discover/reveal hidden connections”, “rights-cleared images”, “representative global history”, “first/only” | G. Unsupported or prohibited claim | False or misleading at the supplied baseline. |

## Three surfaces: permitted claims

| Surface | May claim | Must not claim |
|---|---|---|
| **Global Atlas** | Release-pinned corpus distribution, documented scope, coverage and missingness. | Completeness, representativeness, causal pattern, influence or absence from history. |
| **Evidence Constellation** | Project-curated research-tree/category membership and navigational context. | Historical relation, lineage, contact, citation or influence from adjacency, proximity or shared parent. |
| **Object Trace** | Object metadata and an inspectable route to source, claim wording, qualification, provenance and `HELD` state. | That a source list/thumbnail/related item is an accepted historical relation. |

## Non-negotiable boundary

The 9,393 old v48 edge ID/label arrays cannot be reliably paired. They are `ORPHANED` material, not TRACE evidence. This package neither reuses, splits, zips nor interprets old layout lines, and no relation is silently generated from visual similarity, time, place, medium, co-occurrence, membership or embeddings.

## Final release gate

Proceed only if all are true: (1) zero accepted relations is prominent and exported; (2) every displayed data layer says whether it is distribution, membership, source context, claim, `HELD` or `UNKNOWN`; (3) no representation or copy implies rights/custody; (4) a table/list, keyboard and reduced-motion route exists; and (5) the release manifest freezes counts and policy. Otherwise retain as an internal prototype.
