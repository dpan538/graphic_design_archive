# B3 — Education, machine and public-use positioning

**Task:** Queue B / B3.  
**Researcher:** subagent `/root/b3_audiences`.  
**Date accessed:** 2026-08-16 (Australia/Brisbane).  
**Method:** read-only desk research using the linked primary standards/institutional pages and peer-reviewed publications in the source register below. This report does not assess an implementation beyond the supplied accepted-state baseline: 15,923 archive objects; 7,995 research-eligible; 7,928 held; **0 accepted TRACE relations**; positive visual-rights coverage 0%.

## Decision in brief

The primary audience should be **design-history researchers** (including postgraduate researchers and research-active curators) who need to move from a bounded corpus to inspectable object-level sources and provenance. The product may welcome a wider public, but it should not promise a general-purpose image-discovery service or an authoritative account of influence.

Ranked audiences are:

| Rank | Audience | Product status | Justification and bounded promise |
|---:|---|---|---|
| 1 | Design-history researcher | **PRIMARY** | TRACE's defensible value is an inspectable research path: object record → claim/evidence/provenance (when accepted), and honest absence when it is not. Data Citation Principle 3 requires claims relying on data to cite it; Principle 7 calls for specific, verifiable version/provenance information. That makes this audience the one to which release-pinning and evidence boundaries deliver the most direct research value. [S1] |
| 2 | Research-active curator / archive operator | **SECONDARY (expert collaborator)** | They can assess descriptions, source lineage, rights status, gaps and prospective claims. They are not a primary operational user until the project provides submission, review, institutional-partnership and preservation workflows; none should be implied now. W3C treats provenance as a basis for assessing data quality and interpretive context. [S2] |
| 3 | Graduate student / educator | **SECONDARY** | Object-level sources and a visible distinction between evidence, interpretation and absence can support source literacy, but a teaching product needs learning scenarios, guidance, assessment and accessible reusable materials. Europeana and the US National Archives provide such dedicated education layers; the archive alone is not evidence of educational effectiveness. [S3][S4] |
| 4 | Informed design-history reader / independent researcher | **SECONDARY (public research reader)** | They can follow curated pathways and inspect sources, provided jargon is explained and every visualisation has a readable alternative. They should be invited to investigate, not told that a visual connection establishes historical influence. |
| 5 | Machine/API client, including an AI agent | **INFRASTRUCTURE AUDIENCE** | Stable, documented, release-specific data can make the corpus discoverable and reusable by machines as well as people—the explicit aim of FAIR—and enable citation, replication, audit and small computational studies. It is infrastructure value, not a primary user experience or proof that the data are suitable for model training. [S5][S1] |
| 6 | General visitor | **TERTIARY / dissemination audience** | A public landing and constrained discovery are worthwhile, but the current accepted TRACE=0 state means this audience must see a research index and evidence-preview, rather than an influence map. Discovery should never outrank verification. |

**Education verdict: secondary, not core.** It is a meaningful public-research and disciplinary-literacy layer, not a core contribution in the next release. It becomes a potential core strand only after deliberate curricular co-design, teacher/student testing and evaluated learning outcomes. This is a high bar: major heritage services publish purpose-built lesson activities, document-analysis scaffolds and educator communities rather than treating browsing as pedagogy. [S3][S4]

**Machine/API verdict: necessary infrastructure, not innovation by itself.** The Read API should be retained as a narrowly documented, read-only, release-pinned research interface. Its contribution is strongest when it returns enough context to reproduce a displayed fact—identifiers, release/source/version, field-level provenance, rights/reuse status, confidence/review state, gaps and stable citations—not merely search results. This follows FAIR's machine-actionable emphasis, W3C guidance on licence/provenance, and data-citation requirements for specificity, persistence and access. [S5][S2][S1] A conventional JSON endpoint, filtering, or API alone is **not** a research contribution.

## What each audience may legitimately receive

| Audience | Honest immediate use case | Must be visible | Not yet supportable / do not promise |
|---|---|---|---|
| Design-history researcher | Locate a record, see its supplied fields and source dossier; filter corpus coverage; inspect accepted claim evidence if/when released. | release identifier, record/source identifiers, provenance, evidence/review state, rights label, missing fields and a citation/export path. | Exhaustive or representative design history; inferred influence; complete image access; peer-reviewed scholarship merely because the site supplies data. |
| Curator/operator | Audit a source lineage, inspect rights/missingness and identify records that could be candidates for collaboration. | owner/provider attribution; source URLs; transformation/release history; rights statement versus licence distinction. | Collection-management system, institutional preservation repository, crowdsourced correction service or rights clearance service. |
| Student/educator | Compare objects and sources; practise asking what an object record evidences and what it does not. | plain-language evidence guide; "not established" states; source citation; accessible table/text alternative. | Curriculum alignment, lesson plans, learning analytics or a claim that browsing produces learning gains. |
| Public research reader | Browse a bounded corpus and follow a guided question to sources. | scope, bias/missingness, terminology, no-inference warning, meaningful alt/textual summary. | A neutral universal canon, comprehensive visual search, history settled by an attractive network. |
| Machine/API/AI | Obtain a stable machine-readable release for retrieval, citation, audit or approved metadata analysis. | schema/version; pagination/rate limits; provenance and rights at record/field level; source and release citation; null/held semantics; terms. | A blanket right to scrape, cache, redistribute images, train models or infer relations from co-occurrence. |

The Read API should therefore have two separate contracts: (1) **research retrieval** for documented released metadata and accepted evidence, and (2) **rights-aware external-resource references**, which identify the providing institution and stated rights but do not proxy a permission to reuse the remote visual asset. The Library of Congress illustrates a normal institutional distinction: its public JSON/YAML API exposes structured collection metadata, but it has limits and is not a complete catalogue substitute. [S6]

## Education: useful method, insufficient evidence of a core contribution

Digital cultural heritage plainly has educational use. Europeana explicitly supports educators with reusable resources, learning scenarios and a community, and frames its collections as material for formal and informal learning. [S3] The US National Archives makes the pedagogic model more concrete: its document activities ask students to analyse primary sources rather than passively receive conclusions. [S4]

That comparison supports a focused role for `graphic_design_archive`: **teach evidence-aware visual-historical inquiry**, not "teach design history" in the abstract. A first release may include a one-page enquiry protocol (what is the object? which source says so? what is missing? what claim has and has not been accepted?), source citations and non-visual alternatives. It should **not** claim an education contribution absent co-designed lesson materials and evaluation. The immediate educational claim is product/education value, not a validated pedagogical outcome.

Practical priority:

1. Treat researcher-facing explanation, accessible data tables and citation as required research usability.
2. Add a compact educator/student guide only if it reuses the same evidence states—no separate unreviewed narrative layer.
3. Defer bespoke lessons, classroom accounts, annotation assignments and learner analytics until partnership/testing exists.

## Read API and machine-readable outputs

### Why they matter

FAIR is useful here as a direction, not a certification claim: it asks that digital research objects be more findable, accessible, interoperable and reusable for machines **and** people. [S5] W3C likewise says that Web data should carry licence and provenance information so users can assess reuse and trust. [S2] The Data Citation Principles require a citation to identify a specific version/timeslice and supporting provenance. [S1]

For this project, those standards turn into modest and testable outcomes:

| API/output property | Research value | Classification |
|---|---|---|
| Read-only API documented with endpoint/schema/release version | Reproducible retrieval and repeatable queries | Infrastructure contribution |
| Stable record, source and release identifiers; citation text/export | Lets a paper, teaching handout or bot point to the exact record/release | Infrastructure contribution |
| Field-/claim-level source and provenance, review status, held/unknown/null semantics | Lets users distinguish an observed record from a released/accepted assertion | Supporting research contribution |
| Machine-readable rights statement plus source/original-item URL | Allows a client to discover that reuse is bounded and trace it to the steward | Infrastructure contribution |
| Corpus coverage/missingness fields and release notes | Enables bias-aware reuse and prevents denominator-free comparisons | Supporting research contribution |
| JSON, filters, pagination, search | Useful delivery mechanics, already common in cultural-heritage systems | Common feature / non-contribution |

The API must not make an unreviewed relation more portable than its evidence warrants. At accepted TRACE=0, relation endpoints should return an empty accepted set with a machine-readable reason/status—not preview, candidate or old layout links labelled as historic relations. For AI clients especially, provide a `not_training_permission`/use-boundary note where possible, but do not imply that an API statement itself settles copyright, contract, database-right or text/data-mining questions. Recent cultural-heritage research warns that collection bias and weak metadata can be amplified in AI use. [S7]

### Minimum machine metadata for the two-week release

- Release ID, release date, source commit/SHA, schema/API version and a changelog/citation endpoint.
- Object ID, source record ID/URL, provider/institution and per-field provenance where data are transformed or synthesized.
- Explicit values for `unknown`, `not_evaluated`, `held`, `not_applicable`, and `no_accepted_trace`; do not coerce these into false null/negative claims.
- For every surfaced visual resource: original item URL, image/service URL (if any), provider, attribution requirement, rights-statement URI/licence URI if supplied, access date, and whether the archive stores a copy (**false** in this project).
- For a future accepted relation: relation ID/type, claim wording, evidence IDs, independent-source basis, reviewer/review date, status, qualification/contradiction and release ID. Until then, do not publish it as a relation.

The list is deliberately DTO-level rather than a recommendation to build RDF or a full ontology. DCMI itself notes that its terms can be used in JSON or relational databases without adopting RDF's formal implications. [S8]

## Rights-aware external visual federation: actual advantage and hard boundary

### Defensible advantage

"Visual federation" should mean that the site **references or renders an image/service controlled by its supplying institution while preserving a route back to its item record and rights information**, rather than asserting custody of a new image collection. Properly executed, this can:

1. keep the supplying institution, catalogue record and rights context visible;
2. avoid presenting a local asset store as though the project owns/cleared every image;
3. let providers correct, replace or withdraw their own service/record; and
4. make absence of usable visual rights measurable instead of silently treating a thumbnail as an open asset.

These are provenance and transparency benefits, not a safe harbour. IIIF's Image API permits rights/attribution metadata, including a rights URI and information that may need display; it does **not** make a licence mandatory or grant reuse permission. [S9] Europeana similarly makes each provided digital object/preview carry a rights statement and separates CC0 metadata from rights in the object itself. [S10] Thus, the supplied baseline `POSITIVE_VISUAL_RIGHTS_COVERAGE=0%` rules out claims such as "free-to-use images", "rights-cleared visual corpus" or "open training set."

### Legal and operational boundary (not legal advice)

- A link, embed, IIIF URL or public API response is not by itself a licence to copy, cache, redistribute, crop, transform, use commercially or train a model on an image. Follow the provider's stated terms and obtain professional advice for a proposed use where needed.
- Metadata rights and image rights are distinct. Europeana's agreement makes metadata CC0 but requires a rights statement for each digital object/preview. [S10]
- A RightsStatements.org label is a high-level, machine-readable description of status, **not** a licence and does not warrant correctness; users are directed to the holding institution for uncertainties. [S11]
- Rights must be displayed as `UNKNOWN` when no verified per-item statement exists; `UNKNOWN` is not permission, and it is not proof of restriction either.
- Do not call a remote work "non-hosted" if the product transcodes/proxies/caches it. Report the actual custody/delivery path. Do not promise takedown speed, image persistence or provider availability without an operational policy.
- Preserve source URL, institution, rights URI and any required attribution close to the visual and in the API; make image failure degrade to a record link and text alternative.

The right public wording is therefore: **"The archive does not claim custody or reuse permission for linked visual assets; consult the supplying institution and item-level rights information."** This is a transparency practice, not legal advice and not a substitute for rights clearance.

## Recommendation for product copy and release state

At the stated zero-relation baseline, use **"TRACE Preview"** or **"Evidence Trace"** only with a persistent notice: *No TRACE relations have been accepted in this release. Explore corpus coverage, research pathways and object/source dossiers; absence of a link is not evidence of no historical relation.* Avoid "influence map", "network of influence", "maps how design travelled" and any copy that treats shared date/place/medium or visual similarity as a relation.

This keeps two important audiences aligned: researchers get a bounded evidence interface; public readers and students learn that visualisation is a question-navigation device, not an inferential engine. It also prevents machine clients from laundering unresolved candidates into asserted relations.

## Implementation-facing prioritisation (no implementation undertaken)

| Priority | Do in the honest-state release | Defer |
|---|---|---|
| Must | Scope/missingness notice; release/source citation; readable object/source dossier; rights/source labels; empty accepted-TRACE response/state; API schema/version docs; accessible non-visual equivalent. | — |
| Should | Short enquiry protocol for students/readers; download/citation examples; machine-readable release provenance/rights fields. | Dedicated education microsite, classroom accounts and course integration. |
| Must not claim/build as a shortcut | Automated influence, image-rights clearance, API-to-AI permission, or a full teaching programme. | LLM/RAG/SLM, embeddings/clustering, user annotation backend, relation backfill, ontology/RDF programme and broad image caching. |

## Evidence limits / uncertainties

- No audience interviews, usability study, curriculum partnership, legal review, provider agreement or API payload were supplied to this task. Claims about existing project capability are therefore bounded to the fixed baseline and requested direction.
- `0%` positive visual-rights coverage is treated as a release fact supplied in the task; it has not been independently recomputed here.
- `UNKNOWN` is required for a provider/API/rights policy that cannot be verified at item level. In particular, third-party terms and jurisdiction-specific exceptions require review outside this report.

## Source register

| ID | Title | Author / institution | Year | URL / DOI | Source category | Specific support for this report |
|---|---|---|---:|---|---|---|
| S1 | *Joint Declaration of Data Citation Principles — FINAL* | Data Citation Synthesis Group / FORCE11 | 2014 | https://doi.org/10.25490/a97f-egyk | Formal scholarly-practice standard | Claims should cite supporting data; citation needs unique identification, access, persistence, specificity/verifiability, provenance/fixity; human and machine actionability. |
| S2 | *Data on the Web Best Practices* | W3C | 2017 | https://www.w3.org/TR/dwbp/ | W3C Recommendation | Licence information enables reuse assessment; provenance supports trust, quality assessment and interpretation; Web data should be understandable to humans and machines. |
| S3 | *Europeana for Educators* | Europeana Foundation | 2026 (page current at access) | https://www.europeana.eu/en/educators | Official programme page | Purpose-built learning scenarios, reusable materials and educator community demonstrate the extra work needed to call an archive an education offering. |
| S4 | *Teaching With Documents* | U.S. National Archives and Records Administration | 2026 (page current at access) | https://www.archives.gov/education/teaching-with-documents | Official educational-method page | Its primary-source activities emphasise contextual analysis and informed judgment rather than passive reception, supporting the proposed evidence-literacy framing. |
| S5 | *The FAIR Guiding Principles for scientific data management and stewardship* | Wilkinson, M. D. et al. | 2016 | https://doi.org/10.1038/sdata.2016.18 | Peer-reviewed, *Scientific Data* | FAIR's explicit concern for machine and human reuse of scholarly digital objects supports a release-pinned, documented API—but does not certify it. |
| S6 | *JSON/YAML for LoC.gov* | Library of Congress | 2026 (page current at access) | https://www.loc.gov/apis/json-and-yaml/ | Official API documentation | Public structured collection data with declared access/pagination limitations; evidence that an API is normal archive infrastructure, not a contribution by itself. |
| S7 | *AI, Cultural Heritage, and Bias: Some Key Queries That Arise from the Use of GenAI* | Heritage (MDPI) | 2024 | https://doi.org/10.3390/heritage7110287 | Peer-reviewed journal article | Cultural-heritage bias and incomplete/heterogeneous metadata may be amplified by AI; supports explicit AI-use limits and missingness context. |
| S8 | *DCMI Metadata Terms* | Dublin Core Metadata Initiative | 2026 (current specification) | https://www.dublincore.org/specifications/dublin-core/dcmi-terms/ | Metadata standard | Includes provenance, rights, licence, source, audience and citation terms; explicitly permits use in JSON/relational contexts without RDF formal implications. |
| S9 | *IIIF Image API 3.0* | International Image Interoperability Framework | 2020 | https://iiif.io/api/image/3.0/ | Technical standard | Rights property identifies a licence/rights statement; providers may require extra displayed information. It does not itself grant rights or require a rights value. |
| S10 | *The Data Exchange Agreement* | Europeana Foundation | 2025 (updated) | https://pro.europeana.eu/page/the-data-exchange-agreement | Official policy / licensing framework | Separates CC0 metadata from per-digital-object/preview rights statement; directly supports separating metadata and image rights. |
| S11 | *Rights Statements — FAQ* | RightsStatements.org | 2026 (page current at access) | https://rightsstatements.org/en/documentation/faq.html | Standards-consortium documentation | Statements are high-level status descriptions, not licences or guarantees; they are human/machine readable and users should check with the holding institution where in doubt. |
| S12 | *The Library of Congress APIs* | Library of Congress | 2026 (page current at access) | https://www.loc.gov/apis/ | Official API documentation | Separates technical API documentation from non-computational research guidance, reinforcing distinct human and machine access pathways. |

