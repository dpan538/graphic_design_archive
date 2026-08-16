# A2 — TRACE Epistemic Model

**Task:** Queue A2, read-only research report  
**Prepared:** 2026-08-16 (Australia/Brisbane)  
**Scope:** epistemic policy and public-presentation thresholds only; this report neither changes the database nor treats any legacy layout edge as evidence.

## Decision in brief

TRACE should model and display *assertions about history*, not history itself. An
object, a source occurrence, a claim, a typed semantic relation, a review
decision, and a rendered projection are different things. Collapsing them into
one line in a diagram would convert a visual convenience into an undocumented
historical fact.

This is consonant with CRMinf's distinction between an argumentation activity,
the belief it produces, and a proposition, and with PROV's separation of the
entities, activities, and agents involved in producing a record. [CIDOC CRM,
*CRMinf 1.1*, 2024](https://cidoc-crm.org/crminf/ModelVersion/crminf-1.1);
[Moreau et al., *PROV-DM*, 2013](https://www.w3.org/TR/2013/REC-prov-dm-20130430/).
It also avoids the false objectivity that Drucker identifies when interpretive
humanities material is displayed as if it were observer-independent data.
[Drucker, 2011](https://digitalhumanities.org/dhq/vol/5/1/000091/000091.html).

**Current consequence:** `TRACE_ELIGIBLE_OBJECTS=0` means there are no accepted
semantic relations to project. No relation network, influence map, density,
centrality, or derived connection is publishable in this release. A first
honest TRACE may show (a) corpus and missingness, (b) clearly labelled curated
research-tree membership, and (c) object-level dossiers of source, claim,
qualification, and absence. It must label the relation-bearing surface
**“Evidence Trace — relation layer not yet released”** (or `TRACE Preview` with
that exact explanatory state), rather than an influence map.

## 1. The six non-interchangeable layers

| Layer | Definition | May it imply a historical relation? | Minimum public payload |
|---|---|---:|---|
| **Object / entity** | The identified design object, person, institution, place, event, or work being described. | No. Object co-presence is not a relation. | Stable object identifier, release identifier, identity status. |
| **Evidence occurrence** | A bounded, citable portion of a source: source/version, exact locator or selector, capture date, rights/access state, and provenance route. The Web Annotation model similarly separates body, target, motivation and precise selectors. [W3C, *Web Annotation Data Model*, 2017](https://www.w3.org/TR/annotation-model/). | No. A source can be contextual, contradictory, or merely mention an object. | Source title/creator or institution, URL/identifier, locator, access date, source role, provenance root. |
| **Claim** | A release-pinned, human-readable proposition with a named subject and scope: e.g., “Source S describes X as shown in exhibition E.” A claim records who/what asserts it; it is not automatically accepted historical truth. | Only at its declared wording and qualification; it cannot silently become a graph edge. | Claim ID/revision, wording, epistemic state, linked evidence, reviewer/release state. |
| **Semantic relation** | A typed proposition joining two resolved endpoints with direction, predicate definition and temporal/scope qualifiers: e.g., `designed_for`, `member_of`, `influenced_by`. | Yes, only after the predicate-specific acceptance rule is met. | Relation ID, endpoints, predicate, evidence/claim IDs, acceptance basis, qualification and release. |
| **Review decision** | A documented curatorial/research judgement that evaluates evidence and a proposed claim/relation. | No by itself. Review is quality control, not a second historical witness. | Reviewer role/identity where lawful, date, decision, rationale, evidence set and policy version. |
| **Projection** | A release-pinned visual or API representation derived from accepted records (node placement, edge geometry, counts, filters). | Never beyond the accepted source record. Geometry, cluster or adjacency has no evidential force. | Release/manifest identifier, projection rule/version, included record IDs and explicit “derived” label. |

PROV-O provides a useful lightweight vocabulary for the first, second, fifth
and sixth layers: entities, activities and agents; attribution and
generation/usage chains; and named bundles whose own provenance can be
described. It does **not** make a provenance chain a proof of a design-history
claim. [Lebo, Sahoo & McGuinness, *PROV-O*, W3C Recommendation, 2013](https://www.w3.org/TR/2013/REC-prov-o-20130430/).
Similarly, Web Annotation's body–target structure is appropriate for anchoring
an excerpt or image region, but “aboutness” is not a license to infer a
predicate not stated in the body. [W3C, 2017](https://www.w3.org/TR/annotation-model/).

### Operational invariant

`evidence -> supports/contradicts/qualifies -> claim -> may support -> semantic relation -> may be included in -> projection`

The arrows are one-way and typed. A layout, shared date/place/medium, common
collection, visual resemblance, co-occurrence in a search result, or a model
score can generate an **exploration candidate**, never reverse this chain.

## 2. Evidence states are about support, not a confidence decoration

The following vocabulary is recommended for claims. It is deliberately
smaller than a numerical “confidence” score, because a score obscures what is
actually known and what is missing. Each status must point to its evidence
items and source roots.

| Claim support state | Definition | Public disposition | Relation disposition |
|---|---|---|---|
| `SINGLE_SOURCE` | One reviewed evidence root directly supports the bounded claim. | Public only as an attributed statement (“S reports/identifies/describes …”), with locator and scope. | Held. It cannot yield a general historical, causal, or influence relation. |
| `CORROBORATED` | At least two *independent* reviewed roots support the same bounded claim, without unresolved material contradiction. | Public with sources and release state. | May support a non-causal semantic relation after predicate review. |
| `QUALIFIED` | Support is present but conditional, tentative, partial, translation-dependent, retrospective, anonymous, or limited in scope. | Public only with the qualifier adjacent to the wording; no simplification in labels/tooltips. | Held unless the exact qualified predicate is accepted and visually displayed as qualified. It must not be rendered as an unqualified line. |
| `CONTESTED` | Credible reviewed evidence materially contradicts the claim, endpoint identity, direction, dating, or predicate. | Public as a dispute dossier with support *and* counter-evidence; absence of resolution is visible. | Held from relation projection. A future `contested_claim` record may be displayed in Object Trace, but not as an asserted relation. |
| `INSUFFICIENT` / `ORPHANED` | Evidence is missing a usable locator, source lineage, endpoint resolution, or sufficient relevance. | Not public as a claim; counts/aggregate missingness may be public. | Held. |

This status model implements, rather than merely cites, two standard ideas:
PROV makes provenance useful for assessing quality, reliability and trust;
CRMinf treats argumentation and belief as information that can be represented
and examined rather than silently fused with the world. [Moreau et al., 2013](https://www.w3.org/TR/2013/REC-prov-dm-20130430/);
[CIDOC CRM, 2024](https://cidoc-crm.org/crminf/ModelVersion/crminf-1.1).

### Provenance-root independence

“Two sources” does not mean two URLs. Two evidence items are independent only
when their **provenance roots** are distinct enough that one is not a mirror,
reprint, catalog copy, unsignalled quotation, shared press release, or
derivative record of the other. Record the root work/record, authoring or
responsible agent where known, publisher/institution, edition/version,
derivation route, and dependency finding. PROV explicitly permits provenance
chains and provenance of provenance; that is the right conceptual basis for
exposing dependence before counting evidence. [Lebo, Sahoo & McGuinness,
2013](https://www.w3.org/TR/2013/REC-prov-o-20130430/); [W3C, *Linking Across
Provenance Bundles*, 2013](https://www.w3.org/TR/prov-links/).

Independence is a **research judgement**, not a W3C property that a database
can discover automatically. If dependency cannot be determined, mark it
`UNKNOWN`, do not count it as an independent root, and do not use the pair to
promote `SINGLE_SOURCE` to `CORROBORATED`.

## 3. Evidence roles and hard boundaries

| Evidence role | It can support | It cannot support on its own | State when incomplete |
|---|---|---|---|
| **Direct documentary evidence** | A narrowly worded attributed claim where the source explicitly states the fact or relation. | A broader causal account, undisclosed direction, or universal historical conclusion. | `SINGLE_SOURCE` until independently corroborated. |
| **Scholarly interpretation** | An attributed interpretive claim, its argument and citation trail. | A claim that the interpretation is uncontested. | `QUALIFIED` where the author hedges or scope is narrow. |
| **Institutional collection metadata** | The institution's own identification/description and a source to investigate. | Automatic historical truth or a relationship not represented in the record. | `SINGLE_SOURCE` unless provenance and review justify more. |
| **Contextual evidence** | Time, place, medium, exhibition setting, source environment, or research pathway. | Endpoint-specific membership, influence, collaboration, commission, authorship, or causal link. | Public as “context”, never relation support. |
| **Orphan evidence** | An audit/missingness record only. | A public claim, relation, or visual link. | `ORPHANED`; held. |
| **Computed association** | A reproducible discovery cue such as visual similarity, shared terms, proximity, co-citation, or clustering. | Evidence, corroboration, semantic relation, causation, influence, authorship, or historical fact. | `COMPUTED / NOT A HISTORICAL RELATION`; keep outside TRACE relation count and graph. |
| **Visual comparison** | At most an explicitly labelled viewer/researcher observation of resemblance. | Influence, contact, shared movement, shared institution, dating, or intent. | Candidate only; no semantic link without documentary/scholarly evidence. |

The anti-inference boundary is necessary because even sound visualizations can
make interpretive selections look like certain data; a humanistic graphical
display should instead expose ambiguity and construction. [Drucker,
2011](https://digitalhumanities.org/dhq/vol/5/1/000091/000091.html). It is
also consistent with W3C Web Annotation: an annotation represents a relation
between a body and a target under a motivation, not a mechanism for deriving
unstated historical facts. [W3C, 2017](https://www.w3.org/TR/annotation-model/).

## 4. Relation thresholds: public, held, and prohibited

The standards above provide representational patterns, not a universal
numeric truth threshold. The thresholds below are therefore **TRACE's proposed
release policy**, clearly distinguished from external standards. They should be
published with the release and versioned; FAIR principles support rich,
machine-actionable metadata and documentation of the data and workflows needed
to understand and reuse a research object. [Wilkinson et al., 2016,
doi:10.1038/sdata.2016.18](https://doi.org/10.1038/sdata.2016.18).

| Proposed outcome | Necessary conditions | What can be shown |
|---|---|---|
| **Public evidence dossier** | Stable object identity; one reviewed, citable evidence occurrence with a source root and locator; claim wording does not exceed it; release ID. | Object → source → attributed/qualified claim. No relation edge. |
| **Public non-causal relation** | Resolved endpoints; controlled predicate; `CORROBORATED` support from at least two independent roots **or** one evidence-backed curatorial decision whose scope is explicitly “curated placement”; semantic review accepts it; release seals it. | Predicate, direction, source IDs, status, qualifier and acceptance basis. Curated placement must never be presented as a discovered historical relation. |
| **Public causal / influence relation** | All preceding conditions; directional wording; two independent support roots; at least one directly addresses the claimed influence/causal mechanism (contemporaneous document/testimony or accountable scholarly analysis), not merely resemblance or chronology; relation review acceptance; a second release/curatorial review; no unresolved contrary evidence. | A typed, directional, source-linked relation with scope/date. Use “documented influence” only where the evidence explicitly warrants it. |
| **Public contested dossier** | Identified claim and endpoints; reviewed support and counter-evidence; clear unresolved status; no relation projection. | Claim card/table that foregrounds contestation, not a normal edge. |
| **Held candidate** | Any missing locator, unresolved identity, non-independent duplication, unreviewed status, unsupported computed association, or source conflict not yet represented. | Nothing in public claim/relation data; aggregate missingness may be released. |
| **Prohibited public inference** | Edge arises from visual similarity, co-occurrence, same time/place/medium, shared source page, nearest-neighbour/embedding/model output, or legacy layout. | No edge, no relationship label, no “influence map” language. |

### Dual source is not dual review

* **Dual-source / independent-root corroboration** increases evidential
  diversity. It is about the documentary and interpretive material. A copied
  catalog record and its mirror still count as one root.
* **Dual-review** is two accountable evaluations of a proposed record or
  release. It checks policy application, identity matching, wording, and
  release readiness. It does not turn one source into two, nor repair a
  missing locator.
* For a strong relation such as `influenced_by`, require both. For an explicitly
  attributed single-source statement, one review can be enough for the
  *statement* to be public, but it remains insufficient for a semantic
  influence edge. This preserves useful evidence without overstating it.

The same separation follows CRMinf's premise/conclusion/argumentation model:
an accepted decision records an argumentation activity, while the supporting
documents remain separately inspectable. [CIDOC CRM, *CRMinf 1.1*,
2024](https://cidoc-crm.org/crminf/ModelVersion/crminf-1.1).

## 5. How TRACE's three allowed surfaces should behave at zero accepted relations

| Surface | Allowed now | Not allowed now | Mandatory state label |
|---|---|---|---|
| **Global Atlas** | Release-pinned corpus distributions, coverage/missingness, source-family and rights states, explicitly described as coverage rather than a complete history. | Links, arrows, clusters, or colour semantics that imply influence or membership. | “Coverage and missingness; not a relationship map.” |
| **Evidence Constellation** | Curated research-tree/folder membership, source-dossier pathways, and unassigned/missing states when each is labelled as editorial or navigational placement. | Treating proximity, branch adjacency, common parent, or layout as evidence of historical contact/influence. | “Research pathway / membership, not an inferred historical network.” |
| **Object Trace** | Evidence occurrence → bounded claim → provenance/review/release trail; an explicit absence or held status. | Public accepted relation edge, centrality measure, or causation/influence label. | “No accepted TRACE relations in this release.” |

Because the release has no eligible relation, `Object Trace` is the most
accurate name for the dossier route. “Evidence Trace” is stronger than
“Influence Map”: it names what the system can presently prove—an inspectable
route from object to evidence and provenance—without promising a network it
does not contain.

## 6. Minimum public contract for every future relation

Before a relation leaves `held`, public output must include or resolve to:

1. a stable release token/manifest and relation identifier;
2. resolved subject and object identifiers, direction, controlled predicate,
   predicate definition, temporal and geographic scope where applicable;
3. claim wording/revision and its state (`CORROBORATED`, `QUALIFIED`, or
   `CONTESTED` as applicable), rather than an opaque confidence number;
4. evidence occurrence IDs, source roots, locators/selectors, access dates,
   known rights/access conditions and a dependency/independence judgement;
5. acceptance basis, reviewer decision IDs/dates and policy/model versions;
6. counter-evidence and qualifications, or an explicit statement that none was
   identified **within the reviewed set** (never “none exists”);
7. projection rule/version and a statement that coordinates, grouping and
   filtering are derived interface choices.

This supports verification, provenance and version specificity in data
citation rather than expecting users to trust a mutable view. [FORCE11, *Joint
Declaration of Data Citation Principles*, 2014](https://force11.org/info/joint-declaration-of-data-citation-principles-final/).

## 7. Immediate policy recommendation

1. **Keep `TRACE_ELIGIBLE_OBJECTS=0` and legacy v48 edges excluded.** The
   unpaired 9,393 old edge ID/label arrays have neither resolvable endpoint
   identity nor evidence linkage; they are `ORPHANED`, not a candidate source
   of public relations.
2. **Release an evidence-navigation preview only if its zero-state is
   unmistakable.** The release can be valuable as a corpus/missingness and
   source-dossier interface, but it should not use network statistics, implied
   arrows, “influence”, “connection”, “lineage”, “web”, “mapped relations”, or
   visual density to claim historical knowledge.
3. **Do not set a target relation count.** The first accepted relation should
   be a small, auditable gold set whose predicate-specific evidence packets are
   complete. A count threshold rewards weakening the model.
4. **Publish policy before content.** Predicate rules, independence criteria,
   status vocabulary, review roles, release pinning and public/held exclusions
   should accompany any future TRACE release. PROV and FAIR are useful
   interoperability/reuse guides; they do not certify the archive's historical
   conclusions. [Lebo, Sahoo & McGuinness, 2013](https://www.w3.org/TR/2013/REC-prov-o-20130430/);
   [Wilkinson et al., 2016](https://doi.org/10.1038/sdata.2016.18).

## Sources and evidence log

All URLs were opened/verified on **2026-08-16**. “Supports” identifies the
specific use in this report; it does not imply that a source endorses TRACE's
locally proposed numerical release thresholds.

| ID | Title | Author / institution | Year | URL / DOI | Accessed | Source category | Supports |
|---|---|---|---:|---|---|---|---|
| S1 | *PROV-DM: The PROV Data Model* | Luc Moreau et al.; W3C Provenance Working Group | 2013 | [W3C Recommendation](https://www.w3.org/TR/2013/REC-prov-dm-20130430/) | 2026-08-16 | Formal web standard | Provenance describes entities, activities and agents and can inform reliability/quality assessment; provenance is not itself a truth claim. |
| S2 | *PROV-O: The PROV Ontology* | Timothy Lebo, Satya Sahoo, Deborah McGuinness; W3C | 2013 | [W3C Recommendation](https://www.w3.org/TR/2013/REC-prov-o-20130430/) | 2026-08-16 | Formal web standard | Entity/activity/agent model, qualified provenance relations, responsibility, and named bundles/provenance of provenance. |
| S3 | *Web Annotation Data Model* | Robert Sanderson, Paolo Ciccarese, Herbert Van de Sompel; W3C | 2017 | [W3C Recommendation](https://www.w3.org/TR/annotation-model/) | 2026-08-16 | Formal web standard | Body/target/motivation, selectors, source/rights/provenance fields; annotation does not make an unstated relation. |
| S4 | *CRMinf 1.1: An Extension of CIDOC-CRM to support argumentation* | Martin Doerr, Christian-Emil Ore, Pavlos Fafalios, Athina Kritsotaki, Stephen Stead et al.; CIDOC CRM SIG | 2024 | [CIDOC CRM](https://cidoc-crm.org/crminf/ModelVersion/crminf-1.1) | 2026-08-16 | Cultural-heritage standard / formal model | Separation of argumentation, belief/proposition, premises and conclusions; basis for claim/review/evidence distinction. |
| S5 | *Linking Across Provenance Bundles* | Stian Soiland-Reyes et al.; W3C | 2013 | [W3C Note](https://www.w3.org/TR/prov-links/) | 2026-08-16 | Formal web-standard note | Named provenance bundles and provenance of provenance; supports dependency inspection before treating sources as independent. |
| S6 | *Humanities Approaches to Graphical Display* | Johanna Drucker | 2011 | [Digital Humanities Quarterly 5(1)](https://digitalhumanities.org/dhq/vol/5/1/000091/000091.html) | 2026-08-16 | Peer-reviewed scholarly article | Humanistic visualization should expose interpretive construction, ambiguity and complexity rather than assume observer-independent certainty. |
| S7 | *The FAIR Guiding Principles for scientific data management and stewardship* | Mark D. Wilkinson et al. | 2016 | [doi:10.1038/sdata.2016.18](https://doi.org/10.1038/sdata.2016.18) | 2026-08-16 | Peer-reviewed scholarly article | Rich machine-actionable metadata, provenance, and workflows improve reuse/transparency; applies to data, algorithms, tools and workflows. |
| S8 | *Joint Declaration of Data Citation Principles* | FORCE11 Data Citation Synthesis Group | 2014 | [FORCE11](https://force11.org/info/joint-declaration-of-data-citation-principles-final/) | 2026-08-16 | Scholarly infrastructure principle | Specificity, versioning, verification/fixity and provenance in citable research objects. |

## Limits and unresolved questions

* No standard located here supplies a universal “two-source” rule for design
  history. The thresholds are an explicit conservative TRACE policy proposal,
  to be tested with domain scholars and documented as such.
* Whether a particular author, publisher, catalogue or museum record is an
  independent provenance root remains `UNKNOWN` until its derivation is
  inspected. Institutional reputation alone is insufficient to infer
  independence.
* This report has not assessed a live relation dataset, source corpus or user
  interface. It cannot certify that any existing candidate satisfies the
  policy.
