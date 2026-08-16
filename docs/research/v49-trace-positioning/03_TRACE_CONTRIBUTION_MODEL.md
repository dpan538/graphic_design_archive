# TRACE contribution model

## The epistemic contract

TRACE must model assertions *about* design history, not render a diagram as if it were history. The following are non-interchangeable: **object/entity; evidence occurrence; claim; typed semantic relation; review decision; rendered projection**. CRMinf distinguishes argumentation, belief and proposition; PROV distinguishes entities, activities and agents. A layout mark is therefore never a substitute for an asserted, reviewable proposition [SR03][SR08].

| Evidence state | Meaning | Public treatment |
|---|---|---|
| `single-source` | A bounded attribution/statement with one independently identified provenance root. | May show as attributed claim only, with locator and qualification; not causal/influence edge. |
| `corroborated` | Compatible support from at least two independent provenance roots. | May support a relation only with predicate-specific review and full dossier. |
| `contested` | Credible sources materially disagree. | Show disagreement/qualification; do not collapse to a neutral edge. |
| `qualified` | Claim has stated temporal, attributional or scope limits. | Display the limitation with the claim/relation. |
| `contextual` | Shared metadata, tree membership, proximity or background context. | Group/filter/navigation only; never a semantic relationship. |
| `orphan` | Endpoint, source, locator or claim wording cannot be resolved. | `HELD`; no node-link, soft edge, cluster or inferred label. |
| `computed association` | Similarity or model output with inputs/method/version. | Separately labelled analytical output only; never source-backed or causal relation. |

**Dual-source is not dual-review.** Independent provenance roots increase documentary diversity; mirrored/copying records still count as one root. Dual review is two accountable checks of modelling/policy application. Strong predicates such as `influenced_by` require both independent corroboration and independent review; neither repairs missing locators or endpoints [SR03][SR04].

## Relation publication threshold

A public relation requires a release ID and immutable relation/claim IDs; resolved directed endpoints and controlled predicate; cautious claim text and scope; source/evidence IDs plus precise locator; source-root independence judgement; evidence status; review decision/rationale; qualifications/counter-evidence; record provenance; and projection version. A relation is `HELD` if any mandatory element is absent. Causal/influence wording has the strictest gate and never follows merely from date, geography, medium, visual similarity, membership, co-occurrence or legacy layout [SR03][SR04][SR09].

At the supplied baseline the accepted count is exactly zero. Thus the relation layer must be withheld, with no centrality/density/rankings, labels, lines, force layout or substitute candidate count. This is a substantive negative result, not an embarrassing error state.

## Name decision

**Do not call TRACE an influence map.** Use `TRACE Preview — Evidence Navigation` now; `Evidence Trace` is even clearer. Retain `TRACE` only alongside the explicit no-inference status. The future name may be relaxed only after a released, auditable, predicate-specific relation corpus and a review/evaluation record exist.

## Standards boundary

Use conceptual lessons from CRMinf, PROV, Web Annotation, IIIF and Linked Art, while stating “informed by” rather than “compliant with.” The two-week window must not attempt RDF/JSON-LD, triple store/SPARQL, ontology migration, IIIF server, annotation protocol/backend or automatic relation extraction [SR03][SR08][SR09][SR10].
