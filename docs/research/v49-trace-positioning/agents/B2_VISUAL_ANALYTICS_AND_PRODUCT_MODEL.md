# B2 — Visual analytics and product model

**Task.** Queue B / B2, read-only positioning research.  This report assesses whether the proposed Global Atlas, Evidence Constellation and Object Trace are complementary research interfaces, and specifies an honest product state when the release baseline is `TRACE_ELIGIBLE_OBJECTS=0`.  It does not prescribe implementation, create relations, or treat the old v48 graph as evidence.

**Research date:** 2026-08-16  
**Project facts used as constraints (provided task baseline):** `ARCHIVE_OBJECTS=15,923`; `RESEARCH_ELIGIBLE_OBJECTS=7,995`; `HELD_OBJECTS=7,928`; `TRACE_ELIGIBLE_OBJECTS=0`; positive visual-rights coverage `0%`; `TARGET_20000_IS_ACCEPTANCE_GATE=false`.  The 9,393 legacy edge ID/label arrays are unreliable, so no legacy line, layout proximity, or derived v48 graph is admissible as TRACE evidence.

## Decision in brief

The three views can be a coherent **multi-scale research-navigation system**, but only if each has a distinct analytic question, unit of analysis, claim type, and hand-off.  They are *not* three visualizations of an influence graph.  In the zero-relation release, the defensible product is **TRACE Preview — Evidence Navigation** (or simply **Evidence Trace**), whose central outcome is an evidence dossier and an explicit absence/held state, not a line or a generated relationship.

The appropriate visual-analytics claim is modest: the interface supports *locating, comparing, and auditing* corpus coverage, curated research organisation, and object-level evidence.  It cannot claim that users can discover historically valid influence, that visual adjacency encodes affinity, or that the three views establish a causal account.  Munzner's nested model specifically warns that errors in task/data characterisation propagate into encoding and interaction; the public claims must therefore remain below the epistemic strength of the available data ([Munzner 2009](https://www.cs.ubc.ca/labs/imager/tr/2009/NestedModel/)).  Visualisation ethics further requires making otherwise invisible sampling, curator, and archivist contributions visible, rather than presenting a clean path from data to viewer ([Correll 2019](https://doi.org/10.1145/3290605.3300418)).

## 1. A non-duplicative three-view model

| View | The user question it alone answers | Permitted unit and primary encoding | Permitted interaction and hand-off | It must not imply |
|---|---|---|---|---|
| **Global Atlas** | “What does this *release* cover, and where are its gaps?” | Aggregate object counts/rates by time, geography, collection/source family, medium, institution and eligibility. Encode a measured field with labelled scale; encode missing/held/unknown as explicit categories and denominators, never as zero. | Filter one declared facet at a time; reveal exact cohort definition, numerator/denominator and object list/download; hand a bounded cohort to Constellation or search. | A historical canon, cultural importance, visual similarity, popularity, or influence. Density only describes represented records under a release-pinned selection. |
| **Evidence Constellation** | “Which curator-defined research pathways or memberships organise this cohort, and which objects belong to each?” | Curated research-tree nodes, membership links, node type, editorial status and source/release metadata. A link means *membership/navigation only* unless a separately accepted semantic relation says otherwise. | Expand a pathway, compare membership lists, inspect why an object is included and move to its dossier. Offer ordered/tree/list form as co-equal, not a decorative graph as the sole access path. | Object-to-object relation, chronology, centrality, historical proximity, causation, or an inferred community. A force layout must never manufacture meaning from distance. |
| **Object Trace** | “What exactly is asserted about this object, by whom, on what source, with which scope, qualification, contradiction and release provenance?” | One object, explicit claim cards, source citations, provenance, evidence class, confidence/qualification and held/absent records. If a semantic relation is accepted in a later release, show its relation type, direction, evidence and review status here first. | Read claim/source/qualification; export/cite the dossier; disclose unresolved or withheld evidence. Hand back to aggregate cohort or curated pathway without silently elevating membership to claim. | That an object record is itself a verified historical assertion, that an external image is licensed, or that a source link proves an unquoted proposition. |

This assignment provides a genuine scale transition rather than repeated filtering.  It maps different tasks—**overview/locate**, **browse/compare a curatorial organisation**, and **lookup/identify/audit an evidentiary claim**—rather than displaying the same object list with three skins.  Brehmer and Munzner's task typology distinguishes why/how/what of visual tasks, which supports documenting those task differences before choosing a layout ([Brehmer & Munzner 2013](https://www.cs.ubc.ca/labs/imager/tr/2013/MultiLevelTaskTypology/)).  A visualisation design study is defensible only when it begins with a real domain problem and validates the system and its lessons, rather than treating an implemented display as validation ([Sedlmair, Meyer & Munzner 2012](https://vis.csail.mit.edu/classes/6.859/readings/pdfs/Sedlmair-DesignStudyMethology.pdf)).

### Cross-view invariants

Every view should display the same release identifier, current cohort definition, count semantics, source/provenance link, and a plain-language status key.  Selecting an object or a filter must preserve these invariants across hand-offs.  The UI must distinguish `observed`, `missing`, `held`, `unknown`, and `not-applicable`; collapsing any of them to an unlabelled blank destroys the difference between a cataloguing gap, an excluded record, and an absence in the historical record.  Historical network research identifies missing values, imprecision, contradiction and transformation as materially different uncertainty sources, and recommends quantifying, visualising, enabling exploration of, and propagating uncertainty through transformations ([Conroy et al. 2024](https://doi.org/10.3389/fcomm.2023.1305137)).

The hand-off rule is deliberately asymmetric:

```text
Atlas aggregate/filter → bounded object cohort → curated membership → object dossier
object dossier → its membership context OR aggregate cohort
never: visual co-location / membership → relation or influence claim
```

No view may draw a semantic object-to-object line unless the specific relation is accepted under the project’s evidence/review gate.  This is a product rule, not merely copy.  Provenance-driven visualisation research argues that transformations and interpretive labour need disclosure because they alter historical records and can otherwise be hidden by the final visual form ([Vancisin, Orr & Hinrichs 2020](https://doi.org/10.1109/VISUAL.2020.00014); [Vancisin et al. 2023](https://doi.org/10.1093/llc/fqad029)).

## 2. Exact zero-accepted-relation honest state

### What is publishable now

Publish the Atlas if it reports release-pinned corpus coverage and missingness with denominators; publish the Constellation only as **curated research pathways / membership**; and publish object dossiers as records, sources and claim-provenance scaffolding.  These are useful even with zero accepted TRACE relations: they let a reader find scope, understand curatorial organisation, and inspect what evidence would be needed before a relation becomes public.  They do not, however, constitute an evidence graph.

Use this explicit state at every TRACE entry point:

> **TRACE Preview — no accepted semantic relations in this release.** Explore corpus coverage, curated research pathways and object-level sources.  Membership, shared date/place/medium and visual proximity are not evidence of influence or other historical relationships.  Candidate relation records remain held until the project’s evidence and review threshold is met.

The status must be queryable and exportable, with `accepted_relation_count: 0`, release ID, gate description and timestamp.  A zero is a factual result, not an error state to be cosmetically repaired.

### What the zero state looks like

* **Atlas:** active and useful.  Include a coverage/missingness panel before any aesthetic overview and a cohort table/download.  The visual grouping is statistical aggregation, not historical connection.
* **Constellation:** active only when it renders a declared taxonomy/tree or membership list with editorial provenance.  Its legend must say “research pathway membership; not a relation network.”  Prefer an ordered, labelled tree/list at zero relations; do not show empty, simulated, or force-directed object links.
* **Object Trace:** active as an evidence-dossier route.  The relation subpanel says “0 accepted relations in this release”, explains the gate, shows no placeholder line and provides source/claim/held status.  A candidate or contextual item is not a relation card and must never be counted as one.
* **Navigation labels:** `TRACE Preview` is safer than an unqualified `TRACE` if the existing name will be read as a relation explorer.  **Evidence Trace** is still better if it is defined in the subtitle as a route to claims, sources and provenance, not as an influence trace.  “Evidence Constellation” may remain as a navigation metaphor only with its membership legend.

### Explicitly prohibited in this release

1. “Influence map,” “network of influence,” “maps how designers influenced one another,” “reveals hidden connections,” “relationship graph,” “evidence graph,” and any node-link view that could reasonably be read as one.
2. Populating a network from legacy arrays, shared field values, co-occurrence, visual similarity, embedding distance, link clicks, or spatial layout.
3. Replacing a zero with candidate counts, research-tree membership counts, source counts, or a fabricated “confidence” aggregate.
4. Lines, cluster hulls, centrality ranks, animated particles, or adjacency labels which suggest evidence where no accepted semantic relation exists.

This restriction is not a loss of product quality.  Uncertainty work in DH warns that visualisations which obscure uncertainty harm scholarly use; it recommends foregrounding uncertainty rather than estimating it away ([Therón Sánchez et al. 2019](https://doi.org/10.3390/informatics6030031)).  Conroy et al. likewise note that uncertainty encodings add complexity and should be used judiciously—not layered in indiscriminately to give a graph an appearance of rigor ([Conroy et al. 2024](https://doi.org/10.3389/fcomm.2023.1305137)).

## 3. Encoding discipline: evidence, uncertainty and atmosphere

| Element | Classification | Allowed only if | Required disclosure / alternative |
|---|---|---|---|
| Position on a dated axis/map | **Data encoding** | It maps a declared time/place field and precision policy. | Precision, geocoding/date method, missing count, range/unknown treatment. |
| Bar/area/point size or labelled colour scale | **Data encoding** | It uses an explicit measure and denominator. | Text/table values and scale; no area/opacity substitute for a count without legend. |
| Shape/line style/status chip for `accepted`, `held`, `missing`, `unknown` | **Data encoding** | Categories are documented and keyboard/screen-reader exposed. | Text label plus colour-independent differentiation. |
| Semantic relation line | **Data encoding with high epistemic cost** | The relation has accepted evidence, type, direction, sources, review and provenance. | Inspectable relation card; otherwise no line. |
| Tree connector for research-path membership | **Navigational structural cue** | It visibly says membership/taxonomy and cannot be confused with semantic relation. | Tree/list alternate and editorial provenance. |
| Force-directed location, collision avoidance, bundling | **Layout aid** | It is visually subordinate and cannot be read as distance/similarity. | State “layout has no analytic distance meaning”; prefer stable ordering. |
| Animation for state transition | **Atmosphere/feedback**, not data | It does not encode time, causality or strength. | Instant alternative and reduced-motion compliance. |
| Parallax, particles, ambient motion, decorative grain, blurred/low-opacity photo montage, 3D depth | **Atmosphere** | It is removable without changing information. | Omit in reduced motion; never use to imply historical connectedness or archive authority. |
| Thumbnail/image prominence | **Contextual affordance**, not proof | Rights status and host/source are clear. | Do not imply custody, permission, provenance or visual-analysis evidence. |

The fundamental risk is **visual authority**: a dense, polished graph can make selective metadata, an editorial pathway or a layout heuristic look like a discovered historical structure.  Correll identifies a moral responsibility to make data collection, curation, archivists, undersampled populations and design choices visible; this project should expose those inputs in the legend/dossier rather than hide them in a visual “black box” ([Correll 2019](https://doi.org/10.1145/3290605.3300418)).  Separate structural membership from semantic relationship in both DOM and language, and make the absence of accepted relations more visually prominent than optional aesthetics.

## 4. Responsive interaction model

### Desktop: comparative reading, not spectacle

Desktop can offer linked detail while maintaining one primary task per screen: a stable Atlas with a side coverage/missingness inspector; a **tree/list-first** Constellation with an optional topology view; and a single object dossier with source/claim panels.  Permit a split view only when it retains a visible cohort definition and active status legend.  Zoom/pan is optional—never the only way to find labels, totals, held status or sources.  Opening an item should update an explicit selection summary, not silently recenter and imply a context change.

### Mobile: linear evidence first

On mobile, do not shrink a graph.  Default to a searchable/filterable list, one facet drawer, a compact coverage summary, pathway breadcrumbs, and sequential claim/source cards.  Use a “View data table” / “View records” control that is equal to the visual view.  A simplified static aggregate chart is acceptable only when its caption, exact values and download/list route remain available.  Omit force layout, hover-only tooltips, precision-dependent drag, and decorative motion.  The research purpose survives this adaptation because the core path is semantic: **scope → pathway → dossier**, not spatial navigation.

### Interaction acceptance criteria

* Every visual filter has a labelled form control, visible active-filter summary, reset control, keyboard operation and URL/state representation.
* Every datum that changes a conclusion has a text equivalent and a sortable/filterable HTML table or record list; W3C states that properly marked-up headers and cells make relationships programmatically determinable and let assistive technology retain context ([W3C WAI Tables Tutorial](https://www.w3.org/WAI/tutorials/tables/)).
* Do not rely on colour alone.  WCAG 2.2 requires meaningful graphical objects and UI components to meet 3:1 contrast against adjacent colours, and its use-of-colour criterion requires another way to convey information ([W3C WCAG 2.2 §1.4.11](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast), [§1.4.1](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color)).
* All interactive nodes/records are keyboard reachable with an accessible name and unambiguous visible focus.  WCAG 2.2 requires focus visibility, and its focus-appearance guidance explains the contrast requirements for a custom indicator ([W3C WCAG 2.2](https://www.w3.org/TR/WCAG22/), [Focus Appearance](https://www.w3.org/WAI/WCAG22/Understanding/focus-appearance.html)).
* Respect `prefers-reduced-motion` and provide a persistent motion-off control.  W3C's interaction-animation criterion says non-essential triggered motion must be disableable and specifically recognises `prefers-reduced-motion`; parallax is a named example of non-essential motion ([W3C WAI, SC 2.3.3](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions)).
* A visual summary requires: title/question, cohort/release, measures/denominators, source/provenance, key missingness qualification, data list/table, and text conclusion constrained to what the data show.  Captions and summaries help screen-reader users identify and understand complex tables ([W3C WAI Caption & Summary](https://www.w3.org/WAI/tutorials/tables/caption-summary/)).

## 5. Research evaluation, rather than visual polish metrics

Before calling the system a visual-analytics contribution, evaluate the **right task at each layer** with at least a small, documented study involving intended users (design-history researchers/curators first; students/readers separately).  The study should test whether participants can:

1. identify an Atlas coverage gap and correctly state its denominator and meaning;
2. distinguish research-tree membership from a historical relationship without prompting;
3. trace an object-level statement back to source, qualification and release;
4. correctly report that the current release has zero accepted semantic relations;
5. complete the same evidence-seeking task with keyboard and narrow/mobile layouts.

Record false-inference rate (“did a participant read layout/membership as influence?”), provenance-comprehension rate, time/errors, screen-reader/keyboard findings, and the content of specialist critique.  Do **not** report engagement, animation smoothness, node count, visual density, or screen size as evidence of scholarly value.  The design-study framework calls for task/data understanding, validation and reflection; it is a useful discipline for separating a working interface from a validated domain contribution ([Sedlmair, Meyer & Munzner 2012](https://vis.csail.mit.edu/classes/6.859/readings/pdfs/Sedlmair-DesignStudyMethology.pdf)).

## 6. Product verdict for the main synthesis

* **Three views:** GO, conditional on the contract in §1 and shared release/missingness invariants.  They are complementary only as aggregate coverage → curated pathway → object evidence; otherwise simplify to fewer views.
* **TRACE name:** Do **not** call it an influence map.  In the current release use `TRACE Preview — Evidence Navigation`; retain `TRACE` only if the adjacent definition explicitly says it is not an automated history of influence.
* **Zero relations:** GO-NARROW.  Publish the honest navigation/dossier experience and the absence state; withhold every semantic relation view, analytic ranking and relation-language claim.
* **Visual complexity:** Allow only encodings with explicit semantic and evidentiary contracts.  Treat motion, depth, constellation styling and image montage as removable atmosphere, not scholarship.
* **Accessibility:** a table/list alternative and reduced-motion path are release criteria, not a later enhancement.  A browser-only canvas/hover graph fails the product’s research-access promise.

## Local source register

| ID | Title | Author / institution | Year | URL / DOI | Source category | Specific support used | Accessed |
|---|---|---:|---:|---|---|---|---|
| S1 | *A Nested Model for Visualization Design and Validation* | Tamara Munzner / IEEE TVCG | 2009 | https://www.cs.ubc.ca/labs/imager/tr/2009/NestedModel/ | Peer-reviewed journal article; author university copy | Four nested layers; upstream task/data assumptions propagate; match claims/validation to layer. | 2026-08-16 |
| S2 | *Design Study Methodology: Reflections from the Trenches and the Stacks* | Michael Sedlmair, Miriah Meyer, Tamara Munzner / IEEE TVCG | 2012 | https://vis.csail.mit.edu/classes/6.859/readings/pdfs/Sedlmair-DesignStudyMethology.pdf | Peer-reviewed journal article | Defines design study and nine stages; requires real domain problem, validation and reflection. | 2026-08-16 |
| S3 | *A Multi-Level Typology of Abstract Visualization Tasks* | Matthew Brehmer, Tamara Munzner / IEEE TVCG | 2013 | https://www.cs.ubc.ca/labs/imager/tr/2013/MultiLevelTaskTypology/ | Peer-reviewed conference/journal paper; university page | Distinguishes why/how/what tasks, supporting distinct view tasks. | 2026-08-16 |
| S4 | *Ethical Dimensions of Visualization Research* | Michael Correll / ACM CHI | 2019 | https://doi.org/10.1145/3290605.3300418 | Peer-reviewed conference proceedings | Visualisation ethics; exposes otherwise invisible data collection, curators, archivists and impacted/undersampled populations. | 2026-08-16 |
| S5 | *Towards an Uncertainty-Aware Visualization in the Digital Humanities* | Roberto Therón Sánchez, Alejandro Benito Santos, Rodrigo Santamaría Vicente, Antonio Losada Gómez / *Informatics* | 2019 | https://doi.org/10.3390/informatics6030031 | Peer-reviewed journal article | Obscuring uncertainty can negatively affect scholarly use; argues for uncertainty-aware DH interfaces. | 2026-08-16 |
| S6 | *Uncertainty in humanities network visualization* | Melanie Conroy et al. / *Frontiers in Communication* | 2024 | https://doi.org/10.3389/fcomm.2023.1305137 | Peer-reviewed journal article | Historical-network uncertainty/missingness; four uncertainty-aware steps; caution that encodings increase complexity. | 2026-08-16 |
| S7 | *Externalizing Transformations of Historical Documents: Opportunities for Provenance-Driven Visualization* | Tomas Vancisin, Mary Orr, Uta Hinrichs / IEEE VIS4DH | 2020 | https://doi.org/10.1109/VISUAL.2020.00014 | Peer-reviewed workshop proceedings | Visualisation can hide transformations and interpretation; provenance must disclose contextual labour. | 2026-08-16 |
| S8 | *Provenance visualization: Tracing people, processes, and practices through a data-driven approach to provenance* | Tomas Vancisin et al. / *Digital Scholarship in the Humanities* | 2023 | https://doi.org/10.1093/llc/fqad029 | Peer-reviewed journal article | Interactive provenance disclosure can aid transparency, rigor and acknowledgement of modifications/bias. | 2026-08-16 |
| S9 | *Web Content Accessibility Guidelines (WCAG) 2.2* and understanding documents | W3C Web Accessibility Initiative | 2023–2025 | https://www.w3.org/TR/WCAG22/ | W3C normative standard / official guidance | Contrast, use of colour, focus, reflow/predictability and motion requirements. | 2026-08-16 |
| S10 | *Tables Tutorial* and *Caption & Summary* | W3C Web Accessibility Initiative | 2023 | https://www.w3.org/WAI/tutorials/tables/ | W3C official guidance | Semantic tables and captions/summaries give assistive technology programmatic relationships and context. | 2026-08-16 |
| S11 | *Understanding SC 2.3.3: Animation from Interactions* | W3C Web Accessibility Initiative | 2025 | https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions | W3C official guidance | Non-essential interaction motion must be disableable; `prefers-reduced-motion` is a recognised sufficient technique. | 2026-08-16 |

## Limits and UNKNOWNs

This is a positioning recommendation, not usability evidence.  No target-user study, accessibility audit, telemetry, current interface inspection, DOM semantics, image-rights contracts, or release API schema was supplied or run for this subtask; their actual status is **UNKNOWN**.  The recommendations above define what a future release must demonstrate; they do not certify current compliance or product behaviour.
