# Visual analytics and portfolio value

## The three-view system is complementary only under this task contract

| View | Task | Encodes | Required hand-off | Never encodes |
|---|---|---|---|---|
| Global Atlas | Overview / locate a bounded cohort | counts/distributions, denominators, coverage and missingness | a filtered cohort with release ID | relation, influence, historical absence or completeness |
| Evidence Constellation | Browse a declared editorial organisation | research-tree/category membership, with editorial provenance | a selected member/pathway | semantic relation from adjacency/proximity/shared parent |
| Object Trace | Inspect/audit one record | source, claim wording, qualification, review/provenance and `HELD` state | source dossier or the originating cohort | a source list/thumbnail as relationship proof |

This gives a real scale transition: aggregate coverage → named curated pathway → source-level dossier. If implementation cannot preserve the semantics and labels, remove the redundant view rather than restyling it. Design-study scholarship supports task-driven visualisation and evaluation, not display-first novelty [SR15][SR16].

## Honest visual rule

Current zero-state copy:

> **TRACE Preview — Evidence Navigation. No accepted semantic relations in this release.** Explore corpus coverage, curated research pathways and object-level sources. Membership, shared date/place/medium and visual proximity are not evidence of influence or other historical relationships.

At zero accepted relations: Atlas may be active; Constellation must be a labelled tree/list-first membership display; Object Trace may show dossiers/holds. Prohibit lines, force layouts, centrality, density, animated particles, cluster hulls, adjacency labels or “related” metrics that reasonably imply a historical network [SR02][SR16].

## Encoding versus atmosphere

Data encoding is permitted only when its field, denominator and uncertainty policy are visible: time/map position, count, status category, or a future accepted relation with source/review/provenance. A tree connector is only a navigational cue and must say so. Force position, motion, parallax, particles, 3D depth, visual grain and photo montage are atmosphere; they must be removable without loss of information and cannot communicate causality, strength or historical authority [SR16][SR17].

## Accessibility and responsive release criteria

Desktop may use linked detail but no hover/zoom-only information. Mobile defaults to a searchable/filterable list, coverage summary, breadcrumb and sequential source cards; it does not shrink a graph. Every consequential visual datum needs an equivalent semantic HTML table/list with visible cohort/release, keyboard controls, focus, non-colour status cues, reduced-motion support and a text conclusion limited to the displayed data. WCAG 2.2 and WAI table guidance support these as baseline access, not polish [SR26][SR27]. Current compliance is `UNKNOWN` because no runtime audit was executed.

## Portfolio framing

For a front-end/data hiring panel, the credible achievement is a difficult information-design and operations problem: fail-closed data contracts, evidence-sensitive visual states, responsive visual-to-table fallback, source/rights context and repeatable releases. Do not call it a novel VIS technique or claim performance/accessibility without tests. A stronger portfolio proof is one bounded vertical slice—capture → provenance → review/hold → sealed release → machine DTO → accessible dossier—than more animation or records [SR15][SR16].
