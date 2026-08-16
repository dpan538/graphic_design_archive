# A3 — Archive and standards comparison: bounded interoperability for TRACE

**Task:** Queue A3, read-only standards research  
**Prepared:** 2026-08-16  
**Scope:** CIDOC CRM/CRMinf, W3C PROV, W3C Web Annotation, IIIF, and Linked Art. This is a positioning and design-boundary memo, not an implementation proposal.  
**Access date for every web source:** 2026-08-16.

## Decision in one paragraph

TRACE should borrow *conceptual distinctions* from these standards—especially the separation of an assertion from its evidence and the provenance of the record that makes the assertion usable—but should not advertise standards conformance or build RDF/JSON-LD/ontology infrastructure during the two-week window. The defensible minimum is a release-pinned, internal JSON/relational contract that gives every displayable claim/relation a stable identifier, typed endpoints, evidence/source identifiers, claim wording, qualification/contest status, review state, creation/review provenance, and a release identifier. It should also retain an explicit `not-public`/`held` state. This makes the project compatible in spirit with archival argumentation and provenance practice without claiming that a semantic graph, IIIF service, or linked-open-data publication exists.

## What each standard actually supports—and does not support

| Standard / framework | Verified purpose | Narrow lesson for TRACE | Boundary: do **not** infer or promise |
|---|---|---|---|
| **CIDOC CRM** | A formal ontology for integrating cultural-heritage information; it provides an event-centric conceptual model. | Treat object, actor, event, source/document, and assertion as distinguishable records; preserve identifiers rather than flattening all facts into one display label. | CIDOC CRM adoption/conformance, CRM class/property mapping, a triple store, or comprehensive heritage cataloguing.
| **CRMinf 1.1** | CIDOC CRM extension for argumentation. Its definition says documentation of argumentation supports later reassessment of authenticity/validity and explicitly says it does **not** promote automated formal reasoning about historical facts or replace scholarly arguments. | The closest standards analogue to TRACE: public relation = a claim whose supporting material, authoring/review context and conclusion can be revisited. A visible evidence status is more important than a visually dense link. | That a graph edge is a historical fact; automatic validation of historical influence; that formal data modelling supplies peer review.
| **W3C PROV-DM** | A data model for provenance about entities, activities and agents involved in producing a thing/data; it covers derivation, responsibility, and provenance-of-provenance bundles. | Record how a TRACE record entered a release: source capture/import, normalization/curation/review activity, responsible agent/role, timestamps, and release. Keep source-document provenance separate from the historical claim it reports. | Using `prov:wasInfluencedBy` as a historical design-influence predicate. In PROV it concerns provenance/influence in production of records, not an art-historical causal conclusion.
| **W3C Web Annotation Data Model** | An interoperable model for annotations as a rooted graph with body/bodies, target(s), motivation and lifecycle/agent metadata; it supports specific segments of resources. | Use the body–target intuition for a future evidence pointer: a quotation/claim fragment can target a specific external page, image region or page range, with a motivation such as `describing`, `classifying`, or `commenting`. | A user annotation backend, W3C annotation protocol, annotation JSON-LD endpoints, or treating an annotation's mere existence as corroboration.
| **IIIF Presentation API 3.0** | A presentation-oriented API for displaying compound digital objects, navigation and descriptive context; it explicitly says it is not a discovery/harvesting metadata API. IIIF Image API describes image delivery. | When a rights-holder exposes a manifest/canvas, retain its URL and surface a labelled outbound “View at holding institution” path. It may supply stable representation/segment references, useful for evidence citations. | Hosting, proxying or transforming images; universal IIIF availability; a provenance guarantee; permission to reuse; using IIIF as a substitute for object metadata/search.
| **Linked Art 1.0** | An art-domain application profile, based on a streamlined CIDOC CRM subset and JSON-LD, oriented to interoperability through implementable services. | Adopt its practical discipline: use a deliberately small, documented vocabulary and publish only fields with a clear cross-system purpose. Stable external identifiers and controlled terms can be designed now even if no RDF is emitted. | Full Linked Art compatibility, JSON-LD, Getty alignment, a museum-management model, or record-level uncertainty/provenance handling supplied by Linked Art alone. Linked Art itself identifies data provenance and quantification of uncertainty/belief as out of scope at fine-grained levels.

### Why these lessons fit an accepted-TRACE baseline of zero

None of the standards makes a visually inferred association adequate evidence. CRMinf is unusually direct: it frames argumentation documentation as enabling reassessment and rejects replacing scholarly argument with automation. That supports the current hard boundary: **0 accepted TRACE relations means no public relation layer, not a thinly evidenced one.** Atlas coverage, research-tree membership and source dossiers may be shown as different kinds of navigation/context, but must never be serialized, styled or described as a causal relation.

PROV helps prevent a second category error. It can document that a curator/reviewer created or released a TRACE claim record; it cannot establish that designer A influenced designer B. Likewise, IIIF manifests and external image URLs describe delivery/presentation pathways, not copyright permission or historical truth.

## Minimal evidence and provenance contract (design target, not an ontology)

The following is an internal field-level checklist for a future accepted relation/claim DTO. It is intentionally language- and storage-neutral, and has **no** requirement to serialize RDF, JSON-LD, PROV-O, Web Annotation, CRM, CRMinf or Linked Art.

| Required field group | Minimum content | Why it is required | Standards lesson |
|---|---|---|---|
| Claim identity | immutable `claim_id`; release ID; status (`held`, `accepted`, `retracted`) | Lets a public statement be cited and prevents a UI node/link from being the record of truth. | CRMinf assertion/reassessment; PROV entity/versioning.
| Claim semantics | verb from controlled relation vocabulary; directed source/target IDs; exact cautious claim text; scope/qualification | A line is not enough: users must know what is asserted and what is not. | CRMinf argument/conclusion; Web Annotation motivation/body/target.
| Evidence | `evidence_id`; source/dossier ID; locator (page, figure, timestamp, URI fragment/IIIF canvas where available); verbatim excerpt or bounded paraphrase; source type | Enables a reader to check the evidential basis rather than accept layout as authority. | CRMinf evidence; Web Annotation Specific Resource.
| Assessment | evidence status (`single-source`, `corroborated`, `contested`, `qualified`, `contextual`, `orphan`); independence/family flag; reviewer decision and rationale | Makes disagreement and insufficiency first-class; prevents duplicate reposts from masquerading as independent corroboration. | CRMinf argumentation; PROV agents/activities. (The exact labels are project policy, not standard vocabulary.)
| Record provenance | capture/import/normalization/review activity IDs; responsible role(s), date; original and normalized source URLs; release/version | Distinguishes a historical source from the project’s processing history and supports reproducible releases. | PROV entity/activity/agent and bundles.
| Rights/presentation | representation URL, host/holding institution, rights statement as supplied, access date, delivery protocol/IIIF manifest if verified | Makes federated viewing attributable and prevents “external” from being misread as “licensed.” | IIIF presentation vs. delivery; Linked Art digital-content separation.

### Public-state rules

1. A relationship may be publicly rendered only when its record is `accepted`, has at least one stable evidence/source locator and a recorded review decision. If the project adopts a stronger policy (e.g., independent corroboration for causal influence), the policy must be explicit.
2. `single-source`, `corroborated`, `contested`, and `qualified` are *evidence-status labels*, not epistemic certificates. “Corroborated” requires provenance-root independence, not two URLs repeating one original claim.
3. `contextual` evidence (shared date/place/medium, adjacency in a research tree, collection membership) can power filters, grouping or explanatory copy; it cannot produce a historical relationship or influence edge.
4. `orphan` evidence (insufficient endpoint identification, source/locator, or claim wording) remains held. It must not be given a soft edge, cluster proximity, or an auto-generated label that looks accepted.
5. Computed similarity/association must be a separately named result with method, inputs, version and limits. It is neither a source-backed semantic relation nor a causal/influence claim.
6. A source, image host, IIIF manifest, citation and source-dossier membership are not proof of visual rights. Keep the supplied rights statement, source URL and access date; if absent, disclose `UNKNOWN` rather than asserting `NO` or “open.”

## Standards-aligned vocabulary guardrails

The following mappings are only explanatory design vocabulary; they must not be exposed as compliance claims.

| TRACE concept | Closest external concept | Safe use | Unsafe shortcut |
|---|---|---|---|
| Object record | Linked Art object / CIDOC CRM cultural object; PROV Entity | Stable identifier and distinction between object and its representation. | Claim that a remote image URL *is* the object or that the project has custody.
| Historical claim | CRMinf argument/conclusion; Web Annotation body about target | Maintain independent claim text and target(s). | Treat a graph edge as self-evident data.
| Evidence source/fragment | CRMinf evidence; Web Annotation target/selector | Store exact locator, capture date and source type. | Treat an undated source homepage as a citable fragment.
| Curation/review/release | PROV Activity/Agent; PROV bundle/version | Attribute data work and bind visible outputs to releases. | State that PROV validation validates a historical argument.
| External image/manifest | IIIF Presentation/Canvas or Linked Art digital content | Link to the holder and preserve supplied rights/access details. | Deliver, cache or assert licences for third-party imagery.
| Research-tree membership | Collection/grouping | Describe it as project curation/navigation. | Promote membership to causation or influence.

## What to implement only if the next delivery window permits (not this two-week window)

These are sequencing recommendations, not authorization to change code now.

### Worth planning after an honest-state release

- A compact relation/claim schema that implements the minimum field groups above and has one or two manually reviewed exemplar claims.
- A release manifest carrying schema version, record counts by evidence status, held/accepted counts, vocabulary version and source-register checksum.
- Outbound source/IIIF links where a concrete holding institution and manifest are verified, with no image proxy or custody implication.
- Downloadable citation/source metadata in the existing machine-readable format, retaining `UNKNOWN` rights and missingness fields.
- A mapping note that says “informed by PROV/CRMinf/Web Annotation concepts; not a conformance implementation.”

### Explicitly out of scope for the two-week window

- **No complete ontology/RDF/JSON-LD system.** CIDOC CRM, CRMinf, PROV-O and Linked Art are substantial modeling ecosystems; a rushed partial mapping would create false interoperability claims and divert work from evidence review.
- No triple store, SPARQL endpoint, CRM/CRMinf class mapping, SHACL validation, URI-resolution programme, or Linked Art certification claim.
- No IIIF server, image proxy/cache, manifest generation, image-region tooling, or assumption that every source has IIIF.
- No W3C Web Annotation protocol, user annotations, moderation backend, distributed annotation syncing or automatic quote-to-claim conversion.
- No automatic relation extraction/influence classification, LLM/RAG/embedding enrichment, duplicate-source “corroboration,” or recovery of the unpaired v48 edge arrays.
- No ontology-first migration of every object. Standards should guide the *next accepted claim* first; broad migration is justified only by a concrete interoperability partner/use case.

## Two-week acceptance gates derived from the comparison

| Gate | Pass condition | Failure handling |
|---|---|---|
| Truth-boundary gate | UI/copy distinguishes Atlas distribution, research membership, external-source dossiers, evidence records and accepted historical claims. | Label the relation view `TRACE Preview` or `Evidence Trace`; render no relation edges when accepted count is zero.
| Provenance gate | Any visible claim-like item has release ID, source ID/URL, source locator or explicitly marked lack, and a status. | Keep it contextual/held; do not call it an evidence-backed relation.
| Rights gate | Every federated visual link identifies host and carries supplied rights status or `UNKNOWN`; no local-custody implication. | Remove/disable preview that makes an unsupported rights claim likely.
| Scope gate | Documentation says the internal model is standards-informed and non-conformant. | Do not use “CIDOC CRM/IIIF/Linked Art compliant” in public copy.
| Evidence gate | At least one accepted relation, if released later, records review rationale and independently traceable evidence roots appropriate to the stated relation type. | Publish zero accepted relations honestly and report the count.

## Limits and interpretation

- These standards are frameworks, not evidence that this project's proposed three-scale interface is novel. They support defensible boundaries and interoperability discipline, not a contribution claim by themselves.
- CRMinf's argumentation model is the strongest positive analogue for evidence-bounded TRACE, but it does not establish that the project has implemented CRMinf or that its review process is academically sufficient.
- The sources establish standards’ scopes. They do not verify current project implementation, rights coverage, provenance completeness, or any external archive’s practices.
- Therefore public wording should be **“informed by archival provenance and argumentation practices”**, never “standards-compliant,” until a separately documented conformance assessment exists.

## Source register

| ID | Title | Author / institution | Year | URL / DOI | Source category | Specific support for this memo |
|---|---|---:|---:|---|---|---|
| S1 | *CIDOC Conceptual Reference Model* | CIDOC CRM Special Interest Group / ICOM CIDOC | 2024–2026 site edition | https://cidoc-crm.org/ | Official standards organisation | CRM is a cultural-heritage conceptual model; informs object/event/source distinctions, not an implementation mandate. |
| S2 | *Definition of the CRMinf: An Extension of CIDOC-CRM to support argumentation*, v1.1 | Martin Doerr, Christian-Emil Ore, Pavlos Fafalios, Athina Kritsotaki, Stephen Stead; CIDOC CRM-SIG | 2024 | https://cidoc-crm.org/sites/default/files/CRMinf%20v1.1%20%282024.12.09%29.pdf | Official specification | Argument documentation supports reassessment; explicitly rejects formal-logic automation/replacement of scholarly argument. |
| S3 | *PROV-DM: The PROV Data Model* | W3C Provenance Working Group | 2013 | https://www.w3.org/TR/prov-dm/ | W3C Recommendation | Provenance’s Entity–Activity–Agent core, derivations, responsibility and bundles/provenance of provenance. |
| S4 | *PROV-Overview* | W3C Provenance Working Group | 2013 | https://www.w3.org/TR/prov-overview/ | W3C Recommendation overview | PROV family context and intended use for quality/reliability/trust assessments of data/thing production. |
| S5 | *Web Annotation Data Model* | W3C Web Annotation Working Group | 2017 | https://www.w3.org/TR/annotation-model/ | W3C Recommendation | Annotation as body/target relation with motivation, lifecycle/agents and selectors for specific resources. |
| S6 | *Presentation API 3.0* | IIIF Consortium | 2020 | https://iiif.io/api/presentation/3.0/ | Official API specification | Presentation of compound digital objects; explicit non-goal of metadata harvesting/discovery; manifests/canvases/annotations and persistent URI guidance. |
| S7 | *API Specifications* | IIIF Consortium | 2026 (live index) | https://iiif.io/api/ | Official API documentation | Distinguishes current Image, Presentation, Authorization, Change Discovery and Content Search APIs; avoids treating “IIIF” as one unspecified capability. |
| S8 | *Linked Art Data Model 1.0* | Linked Art Editorial Board | 2026 (live version 1.0 documentation) | https://linked.art/model/ | Official application-profile documentation | Art-domain application profile; CRM subset, JSON-LD, small implementable services, iterative/limited scope; data provenance and uncertainty quantification excluded at granular levels. |
| S9 | *Introduction to the Linked Art Model* | Linked Art Editorial Board | 2026 (live documentation) | https://linked.art/model/intro/ | Official application-profile documentation | Intended art-historical/heritage modelling audience and scope framing. |

**Citation convention:** All URLs above were opened directly on 2026-08-16; there are no search-snippet-only citations. “Year” is the document publication/version year where supplied, or “live” where the official site does not assign a single publication year.
