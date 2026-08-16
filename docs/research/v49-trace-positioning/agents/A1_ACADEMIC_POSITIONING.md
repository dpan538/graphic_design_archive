# A1 — Academic positioning of `graphic_design_archive` TRACE

**Task.** Independent, read-only disciplinary assessment for the release-pinned
`graphic_design_archive` TRACE proposal.  Research conducted 2026-08-16.  This
report does not infer functionality that has not been accepted in the stated
baseline.

## Decision

**Primary academic field: Digital Humanities (DH), specifically design-history
digital scholarship.**  The project is best positioned as a DH research
infrastructure and interpretive interface for *graphic-design history*, not as a
new subdiscipline of design history, a museum collection-management system, or a
visual-analytics contribution in itself. Its object domain, questions and
interpretation belong to design history; its proposed scholarly contribution is
the computable, inspectable route between a heterogeneous corpus, curatorial
research organisation, and object-level evidence.

**Secondary field 1: digital heritage / archival and information science.**
This is the appropriate secondary home for selection, descriptive provenance,
rights context, authenticity, source context, and visible absence. It is not a
claim that the project is a trusted preservation repository: external image
federation means that custody and long-term bit preservation remain with source
institutions.

**Secondary field 2: visual analytics / HCI for the humanities.**  It applies to
the interaction design of Atlas, research-tree/Constellation and Object Trace,
especially uncertainty and provenance disclosure. It should be described as an
application/case study unless a comparative user study or a novel visual
encoding demonstrates a contribution to VIS/HCI.

**Not a primary field: research-software engineering.** Release pinning,
machine-readable output and reproducibility can make this valuable research
software/infrastructure, but they do not by themselves make its scholarly
question software engineering. Likewise, the current collection size is neither
a separate discipline nor evidence of a research contribution.

## Baseline that determines the claim ceiling

| Baseline fact | Consequence for disciplinary framing |
| --- | --- |
| `ARCHIVE_OBJECTS=15923`; `RESEARCH_ELIGIBLE_OBJECTS=7995`; `HELD_OBJECTS=7928` | The corpus is a substantial *research index*, but count is not representativeness, preservation custody, or scholarly argument. `HELD` must remain an analytical and public limitation. |
| `TRACE_ELIGIBLE_OBJECTS=0` | There is no accepted semantic-relation corpus and hence no publishable relation map, influence graph, network finding, or validation of a three-scale evidence-navigation method yet. |
| `POSITIVE_VISUAL_RIGHTS_COVERAGE=0%` | “Visual federation” may be a rights-conscious access pattern, never a licence, image repository, or image-rights solution. |
| `TARGET_20000_IS_ACCEPTANCE_GATE=false` | More records cannot substitute for source-linked, reviewed claims. Collection growth is a coverage/operations choice, not a proof of TRACE. |
| 9,393 old edge ID/label arrays cannot be reliably paired | The old v48 graph is not a dataset for DH analysis. It must not be used as visual evidence, a historical network, or a relation-model evaluation set. |

The immediate scholarly unit is therefore a **bounded method and an honest
interface state**, not a completed historical relation dataset. A useful first
release can demonstrate *how a historian should be able to inspect evidence and
missingness*; it cannot claim that it has traced historical influence.

## Why DH is the primary location

DH is the best umbrella because this is a humanities-domain research problem
whose proposed method is the construction, publication and critical use of data,
interfaces and computational representations. Horani Ibanez characterises DH as
a meeting point of humanistic interpretation with computational tools,
statistical methods and visualisation, and as a place where epistemic cultures
negotiate forms of knowledge [S1]. That describes TRACE more accurately than a
product label: a visual path cannot be separated from the source-selection and
interpretive decisions that made it.

The literature warns against displaying historical data as if they were settled
measurements. A systematic review of 126 DH visualisation publications concludes
that historical/humanistic data contain multiple uncertainties and that scholars
are wary of visualisations that appear overly objective [S2]. The related
humanities visualisation framework explicitly treats transformations and
uncertainty across the analysis pipeline as design material [S3]. Thus the
project's plausible DH contribution is **evidence-bounded navigation and the
disclosure of its limits**, rather than “finding patterns” through a graph.

The graphic-design domain is not merely decorative content. The Open Portuguese
Graphic Design Archive frames graphic-design historiography as shaped by the
authorities that define objects, themes and authors, and argues for making
excluded objects/practices visible [S8]. This supports attention to collection
bias and missingness, but it does **not** validate global representativeness of
this corpus. It strengthens the case that interpretive and selection decisions
must be visible.

## Secondary positioning and its limits

### 1. Digital heritage / archival-information science

UNESCO treats digital heritage as digital or digitised cultural, educational,
scientific and administrative resources, including databases, images, graphics,
software and web pages; it calls for purposeful lifecycle maintenance and a
balance between access and rights [S5]. Its selection principle also requires
accountable, defined policies and procedures [S5]. This aligns with release
snapshots, source dossiers, rights flags and explicit `HELD` status.

Archival scholarship reinforces the distinction between a record's relationships
and an interface's reorganisation: studies of original order in digital archives
found varied structures/relationships and challenges in archival representation
[S7]. Recent digital-archive scholarship argues that system design, audience
profile, labour and lacunae change what sources mean and urges attention to
digital provenance [S6]. Consequently TRACE can legitimately *expose a research
representation* and provenance; it must not present its curated pathways or
interface topology as original archival order.

This secondary label has a hard boundary. The proposed platform neither takes
custody of external images nor establishes an institution's preservation
responsibility. Avoid “digital preservation archive”, “museum-grade archive”,
or “heritage repository” unless it acquires entrusted collections, preservation
plans, institutional mandate, and demonstrable stewardship.

### 2. Visual analytics / HCI

Visualisation is relevant where it helps researchers assess collection coverage,
trace sources, compare claims, and see uncertainty. A 2022 review of interactive
DH visualisation identifies uncertainty, large/multidimensional-data performance,
and availability as continuing challenges [S4]. Panagiotidou and Vande Moere
argue that qualitative uncertainty includes collection, storage, authorial
biases and assumptions, and should be considered in its socio-technical context
[S9]. These findings support UI requirements such as visible unknowns, source
routes, non-authoritative encodings, accessible tabular equivalents, and no
automatic edge inference.

But visual complexity is not a VIS/HCI contribution. Without an explicit
research question, alternative designs, evaluation protocol, participant
evidence and findings, this is a **DH application of visual analytics**, not a
new visual-analytics technique. With `TRACE_ELIGIBLE_OBJECTS=0`, any network
view is particularly likely to create an authority illusion; it should render
an empty/held state, coverage/missingness, and explanatory method rather than
invent connections.

## What can and cannot be a contribution now

| Candidate statement | Status at this baseline | Classification / required evidence |
| --- | --- | --- |
| A release-pinned route from corpus coverage through curated research organisation to object-level claims, sources and provenance, with a rule against automatic influence inference | **Promising but not yet demonstrated.** Defensible only as a design/method proposition until reviewed relations and a released audit trail exist. | Supporting research contribution in DH; potentially core after implementation and evaluation. |
| Explicit display of missingness, held material, uncertainty and limits | Defensible as a methodological commitment; effectiveness is untested. | Supporting DH / digital-heritage contribution. Assess with field-level documentation and user review. |
| A 15,923-object graphic-design research index | Potentially useful infrastructure, not a historical finding. | Infrastructure contribution; describe source/selection bias and update scope. |
| Source dossiers, provenance fields, release IDs, read-only machine output | Valuable reproducibility and re-use infrastructure if released and documented. | Infrastructure contribution; FAIR/reuse claims require stable identifiers, licences and preservation documentation. |
| External-image / no-custody federation | A rights-aware access design only. | Product/infrastructure decision. It neither conveys image rights nor makes the platform rights-compliant by itself. |
| Atlas, Constellation and Object Trace visuals | Potential navigation and public-education value. | Product/HCI contribution only after task-based evaluation; not a research finding. |
| Responsive visual effects, animation, CI, deployment, data volume | Evidence of implementation/operations skill. | Portfolio capability signal; no academic novelty claim. |
| “Influence map”, “network of design influence”, “reconstructs design history” | Unsupported and misleading at zero accepted relations. | Prohibited claim. |

## Recommended scholarly description

Use this provisional formulation in research contexts:

> `graphic_design_archive` is a Digital Humanities research-infrastructure case
> study for graphic-design history: a release-pinned interface designed to move
> from corpus coverage and curatorial pathways to inspectable object-level
> claims, sources, provenance and missingness without automatically inferring
> historical influence.

Two qualifications are essential: (1) call it a **case study/prototype of an
evidence policy** until accepted relations and evaluation exist; (2) say that
the present release has no accepted TRACE relations. The formulation must not
imply a completed influence analysis.

### Testable contribution path

To promote this from a carefully framed system case study to an academic
contribution, the next release needs all of the following:

1. A published relation/claim acceptance rubric, including the meaning of
   `single-source`, corroborated, contested, qualified, contextual and held.
2. A non-zero, deliberately bounded, independently sourced and reviewer-audited
   set of public claims, with identifiers that link every visual mark to sources
   and release provenance. A count threshold alone is insufficient.
3. A documented negative result: how candidate assertions were rejected/held and
   how the UI makes this legible. This makes the no-inference policy auditable.
4. An evaluation matched to the claim: historians/curators can recover source
   context and uncertainty; readers do not mistake an association for influence;
   accessibility review covers non-visual and reduced-motion paths.
5. Coverage/bias analysis by date, region, source family, institution and medium
   before asserting any corpus-wide historical pattern.

This path is stricter than a generic product roadmap: it connects an academic
claim to falsifiable evidence. If these conditions are not met, publish as a
transparent research index and interface demonstration, not as new knowledge
about graphic-design history.

## Field-specific publication homes (conditional)

| Output actually evidenced | Appropriate framing / possible venue family | Do not claim |
| --- | --- | --- |
| Dataset + selection, provenance, licences, coverage and reuse documentation | DH/data-infrastructure paper or data-paper venue (for example, *Journal of Open Humanities Data*) | a historical conclusion or preservation custody merely from metadata release |
| Reviewed, source-linked relation model + uncertainty interface + qualitative task evaluation | DH system/case-study paper; VIS4DH/DH visualisation case study | general HCI/VIS novelty without comparative evaluation |
| Historian-led account of a bounded graphic-design question, with cited primary/secondary sources | Design-history article/digital scholarly edition | a general history of global influence from coverage data |
| Curatorial public interface with transparent limitations | Digital-heritage exhibition/interpretation statement | a formal archive authority or image-rights clearance |

## Source register for this assessment

All pages below were opened/checked on **2026-08-16**. “Exact supported
judgment” states the limited inference taken here; it is not a claim that the
source endorses this specific project.

| ID | Title | Author / institution | Year | URL / DOI | Source type | Exact supported judgment |
| --- | --- | --- | --- | --- | --- | --- |
| S1 | *Digital Humanities at the Intersection of Three Approaches to Data Visualisation: Statistical Graphics, Data Humanism, and Humanistic Interpretation* | Aida Horani Ibanez, University of Luxembourg | 2024 | [DOI 10.5281/zenodo.14169050](https://doi.org/10.5281/zenodo.14169050) | Peer-reviewed journal article / repository record | DH combines humanistic interpretation with computational/statistical tools and visualisation; DH is a site where epistemic cultures negotiate knowledge. Supports DH, not pure UX, as primary frame. |
| S2 | *Communicating Uncertainty in Digital Humanities Visualization Research* | Georgia Panagiotidou et al., UCL / IEEE TVCG | 2023 | [DOI 10.1109/TVCG.2022.3209436](https://doi.org/10.1109/TVCG.2022.3209436) | Peer-reviewed journal article; accepted manuscript at UCL | A systematic review of 126 DH visualisation publications finds multiple sources of uncertainty and scholar concern about overly objective visualisations. Supports visible uncertainty/missingness. |
| S3 | *Towards an Uncertainty-Aware Visualization in the Digital Humanities* | Roberto Therón Sánchez et al., University of Salamanca | 2019 | [DOI 10.3390/informatics6030031](https://doi.org/10.3390/informatics6030031) | Peer-reviewed open-access journal article | Humanities visualisation must expose computational decisions and uncertainties through the data-analysis pipeline. Supports provenance/limit display; not automated historical inference. |
| S4 | *A Review of Research on Interactive Visualization Applications in Digital Humanities* | Documentation, Information & Knowledge | 2022 | [DOI 10.13366/j.dik.2022.05.042](https://dik.whu.edu.cn/jwk3/tsqbzs/EN/10.13366/j.dik.2022.05.042) | Peer-reviewed review article | Review identifies uncertainty, large/multidimensional data performance and availability as DH visualisation challenges. Supports secondary VIS/HCI positioning and the need for evaluation. |
| S5 | *Charter on the Preservation of Digital Heritage* | UNESCO General Conference | 2003 | [UNESCO legal text](https://www.unesco.org/en/legal-affairs/charter-preservation-digital-heritage) | International standard / primary policy text | Defines digital heritage broadly; calls for lifecycle maintenance, accountable selection, access-rights balance and authenticity. Supports heritage-infrastructure framing and limits of a non-custodial platform. |
| S6 | *Digitized archives, content providers, and slow scholarship: why archival researchers should care about digital provenance* | Elizabeth R. Williamson, University of Exeter | 2026 | [DOI 10.1093/llc/fqag062](https://doi.org/10.1093/llc/fqag062) | Peer-reviewed journal article | System design, audience profile, labour and lacunae affect research; provenance should be naturalised. Supports treating source/context/missingness as substantive, not cosmetic. |
| S7 | *Original Order in Digital Archives* | Jane Zhang | 2012 | [Archivaria article](https://archivaria.ca/index.php/archivaria/article/view/13410) | Peer-reviewed archival-science article | Digital archives exhibit varied record structures and pose representation challenges. Supports separating curated interface relations from original archival order. |
| S8 | *Open Portuguese Graphic Design Archive: statements as interruptions of institutionalised unit* | Joana Baptista Costa & Mariana Leão; Design History Society report | 2022 | [Design History Society](https://www.designhistorysociety.org/blog/view/report-dhs-conference-bursary-by-joana-baptista-costa-and-mariana-le%C3%A3o-open-portuguese-graphic-design-archive-statements-as-interruptions-of-institutionalised-unit) | University/scholarly-society project account | Graphic-design historiography is shaped by institutional authority and can exclude objects/practices. Supports bias/missingness as design-history concerns, not a claim of this corpus's representativeness. |
| S9 | *Communicating qualitative uncertainty in data visualization: Two cases from within the digital humanities* | Georgia Panagiotidou & Andrew Vande Moere | 2022 | [DOI 10.1075/idj.22014.pan](https://doi.org/10.1075/idj.22014.pan) | Peer-reviewed journal article | Collection/storage circumstances and authorial bias form qualitative uncertainty; visualisation should consider socio-technical context. Supports source-context UI requirements. |
| S10 | *About ReSA / Why ReSA?* | Research Software Alliance | 2023–2026 page, citing Katz & Barker 2023 | [ReSA](https://www.researchsoft.org/about/) | Research-infrastructure organisation / primary community statement | Defines research software as software created during or for a research purpose and emphasises reproducibility, quality and sustainability. Supports infrastructure framing only. |
| S11 | *FAIR for Research Software (FAIR4RS) Principles* | RDA, ReSA & FORCE11 FAIR4RS Working Group | 2022 | [RDA output](https://www.rd-alliance.org/group_output/fair-principles-for-research-software-fair4rs-principles/) | Community standard / primary output | FAIR4RS connects findability, accessibility, interoperability and reusability with research software. Supports release documentation as infrastructure, not proof of historical validity. |
| S12 | *Designing to Restory the Past: Storytelling for Empowerment through a Digital Archive* | International Journal of Design | 2023 | [article](https://www.ijdesign.org/index.php/IJDesign/article/view/4410/1022) | Peer-reviewed design/HCI research article | A digital archive can be studied through research-through-design; it provides an analogue for case-study framing, not direct evidence that TRACE has achieved social impact. |

## Limits and unresolved questions

- **UNKNOWN:** whether individual source institutions permit the exact visual
  embeds/derivatives contemplated by federation. Per-object rights documentation,
  not an external URL, is required.
- **UNKNOWN:** whether the 7,995 research-eligible records represent geographic,
  temporal, linguistic, institutional or medium diversity. Counts alone do not
  answer it.
- **UNKNOWN:** whether prospective users comprehend the three views or are less
  likely to infer false influence. This requires a study; it cannot be concluded
  from literature.
- **UNKNOWN:** whether a trace-relation workflow is sufficiently distinct from
  existing provenance-aware archival interfaces. Comparative research and a
  released reviewed relation set are required.

## Bottom line for the parent synthesis

Frame the project as **Digital Humanities for design-history research**, with
digital-heritage/archival science and humanities visual analytics as two
secondary dialogues. Its academically defensible present value is the *policy
and infrastructure for inspectable, bounded research navigation*. At zero
accepted relations, it has no evidence base for a TRACE network contribution;
therefore “Evidence Trace Preview” or “Evidence navigation (no accepted
relations in this release)” is academically safer than “influence map.”

