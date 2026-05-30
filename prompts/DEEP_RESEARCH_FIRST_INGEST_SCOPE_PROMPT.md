# Deep Research Prompt: First Experimental Ingest Scope for a Rights-Aware Modern Graphic Design History Archive Index

Use this prompt to determine which movements, formations, historical events, and source categories should be included in the project's first experimental ingest scope.

This is not a request to write a design-history essay. The output must be structured enough to guide database seeding, source review, and the first controlled ingest test.

## Project Definition

The project is a rights-aware archive index and research framework for modern graphic design history.

It does not replace archives, copy collections, build a course, produce a textbook, or impose a single historical narrative. It indexes and links distributed works, texts, people, institutions, movements, media technologies, places, sources, citations, rights states, and historical nodes back to original sources.

The project prioritizes indexing over possession:

- metadata before images;
- citation before interpretation;
- source links before local copies;
- rights state before display;
- classification with evidence, not visual intuition alone;
- unresolved or uncertain relations must remain visible rather than hidden.

The public interface is planned as an archive-cabinet / filing-system metaphor:

- cabinet / drawer / folder / loose-leaf sheet / appendix / card / registration card / bookmark;
- folders are filter views, not duplicate corpora;
- one global `SEQ`;
- display number grammar: `GD / {ERA} / {HN} / {MV|NONE} / {SEQ} / {TIER}-p{PAGE}`;
- fixed table kinds: `SOURCE`, `NORMALIZED`, `RIGHTS`, `CLASSIFICATION`, `RELATIONS`, `CITATIONS`;
- image zones: `IMG00`, `IMG01`, `IMG02`, `IMG03`;
- English UI chrome during development, source-language metadata preserved.

The project has already established that the correct standard is not "complete all world graphic design history," but a launch-complete, globally structured, gap-aware framework that does not structurally defer non-Euro-American histories.

## Current Skeleton

The current project skeleton includes:

- 15 global historical nodes, from writing/printing preconditions through contemporary platform/generative visual communication.
- 15 launch regions:
  - Western and Central Europe;
  - Eastern Europe, Balkans, USSR, and socialist contexts;
  - North America;
  - Latin America and the Caribbean;
  - Japan;
  - Korea;
  - East Asia as transnational frame;
  - Mainland China;
  - Hong Kong;
  - Taiwan;
  - Southeast Asia;
  - South Asia;
  - Middle East and North Africa;
  - Africa;
  - Oceania and Pacific.
- 109 geography/context rows.
- 74 regional movement/formation rows.
- 48 regional event-node rows.
- 35 source-registry rows.
- 24 experimental ingest candidates.
- Source/right policy model with `IMG00`, `IMG01`, `IMG02`, and `IMG03`.

Important existing rights conclusion:

- `SOURCE_RIGHTS_READY_FOR_EXPERIMENTAL_INGEST: yes`
- Image-rich ingest is not approved by default.
- Unknown or ambiguous image rights must default to `IMG00`.
- The frontend must consume rights decisions from the database and must not decide image display from raw image URLs.

## Current Candidate Source Pattern

The current experimental ingest shortlist includes these source behaviors:

- open-image / `IMG03`: Smithsonian Open Access, The Met Open Access, explicit CC/PD Internet Archive items;
- IIIF/embed / `IMG02`: carefully reviewed Rijksmuseum, Library of Congress, Europeana records;
- thumbnail-only / `IMG01`: DigitalNZ small-thumbnail metadata records;
- link-only / `IMG00`: PGDA, Fonts In Use, Letterform Archive, Trove, NDL, Memoria Chilena, SAHA, many Internet Archive/Wayback records, V&A unless reviewed;
- authority-only / no image risk: Wikidata + VIAF + Getty authority clusters.

The first experimental ingest must test both low-risk open records and high-value link-only records. It should not accidentally become an open-image museum-object demo.

## Research Goal

Determine the first experimental ingest scope:

Which movements, formations, historical events, media regimes, and source categories should be represented in the first controlled ingest so that the project can test its methodology across global, rights-sensitive, multilingual, and non-linear design-history material?

The output must answer:

1. Which historical nodes must be sampled first?
2. Which movements/formations must be represented first?
3. Which dateable events should anchor the first ingest?
4. Which regions must appear in the first ingest, and why?
5. Which sources are suitable for each selected movement/event?
6. Which source records should be `IMG00`, `IMG01`, `IMG02`, or `IMG03`?
7. Which materials should be indexed only as metadata/link/citation despite their historical importance?
8. Which areas should remain in the global framework but not be crawled until source terms or rights evidence improve?

## Critical Methodological Constraint

Do not rank movements by canonical fame or visual attractiveness.

Rank them by whether they stress-test the archive framework:

- source metadata vs normalized metadata;
- rights ambiguity;
- non-Latin scripts;
- multilingual titles and names;
- region/date filtering;
- movement `NONE` or multiple movements;
- anonymous/collective authorship;
- periodical issue/page relationships;
- source record vs object record distinctions;
- authority ambiguity;
- protocol-sensitive materials;
- link-only records as first-class records;
- relationships among person, institution, event, movement, work, text, medium, and source.

## Required Output

Produce a structured report with these sections.

### 1. Executive Decision

State whether the current skeleton is ready to define a first experimental ingest scope:

- `FIRST_INGEST_SCOPE_READY: yes/no/yes_with_conditions`

Then state:

- the recommended number of records for the first ingest;
- the recommended number of movements/formations;
- the recommended number of event nodes;
- the recommended number of sources;
- the minimum global balance requirement.

Avoid vague language. Give a concrete recommendation.

### 2. Selection Principles

Create a numbered list of selection principles.

The principles must balance:

- global coverage;
- source feasibility;
- rights safety;
- metadata richness;
- methodological value;
- noncanonical design history;
- source-language and script diversity;
- ability to test the archive-cabinet sheet templates.

### 3. First Ingest Movement / Formation Scope

Use this table:

| Priority | Movement / formation | Region(s) | Date range | Related HN nodes | Related event nodes | Why it must be included in first ingest | Source families | Expected rights/image zone | Risks |

Include at least:

- one canonical European modernist formation;
- one Eastern European / socialist / avant-garde or poster formation;
- one North American professional/corporate/editorial formation;
- one Latin American formation;
- one Japanese formation;
- one Mainland China, Hong Kong, or Taiwan formation;
- one Korean formation;
- one Southeast Asian formation;
- one South Asian formation;
- one MENA formation;
- one African formation;
- one Oceania/Pacific or Indigenous formation;
- one counterpublic / protest / queer / feminist / Black / labor / decolonial formation;
- one vernacular/commercial/popular media formation;
- one digital/web/interface/platform formation.

The first ingest can contain overlap, but the overlap must be explicit.

### 4. First Ingest Event-Node Scope

Use this table:

| Priority | Event node | Region/geography | Date/date range | Related movement(s) | Related HN nodes | Why it anchors browsing/search | Candidate sources | Expected rights/image zone | Notes |

Prefer dateable anchors, not only broad styles.

Include:

- at least 3 pre-1945 nodes;
- at least 3 postwar/professionalization nodes;
- at least 3 protest/counterpublic/decolonial nodes;
- at least 3 digital/born-digital/platform nodes or near-digital transitions;
- at least 3 non-Euro-American dateable nodes.

### 5. First Ingest Source Match Matrix

Use this table:

| Source | Access method | Selected movement/event use | Region | Record type | Metadata fields likely available | Terms/rights risk | Recommended image zone | Automated ingest suitability | Manual review needed |

The table must include:

- at least 2 open-image sources;
- at least 2 link-only high-value sources;
- at least 1 IIIF/embed source;
- at least 1 thumbnail-only source;
- at least 1 authority source;
- at least 1 periodical/newspaper source;
- at least 1 web archive source;
- at least 1 community archive source;
- at least 1 non-Western national library or aggregator.

### 6. Candidate Query Plan

Create deterministic search/query plans. Do not design this around AI search.

Use this table:

| Movement/event | Source | Query terms | Language/script variants | Filters | Expected result type | False-positive risks | Notes |

Include multilingual terms where useful:

- Chinese simplified/traditional;
- Japanese;
- Korean;
- Arabic/Persian/Hebrew/Turkish where relevant;
- South Asian scripts where relevant;
- Spanish/Portuguese;
- French;
- Indigenous/community terms where appropriate.

If the source does not support advanced querying, describe the manual search path.

### 7. Rights-Safe Display Plan

Use this table:

| Movement/event/source cell | Default record policy | Default display policy | Image zone | Rights evidence required before escalation | Why this is safe enough |

The report must explicitly name any historically important materials that should still remain `IMG00`.

### 8. Minimum Record Set Recommendation

Recommend a concrete minimum record set, for example 36, 48, 60, or another number.

Use this table:

| Cell ID | Region | Movement/event | Source | Target record count | Required fields | Expected sheet/card type | Image zone |

The target must be realistic for an experimental ingest but broad enough to test the system.

Do not recommend hundreds of records. This is a controlled test of structure, not a data-volume milestone.

### 9. Exclusion / Deferral Rules

List which materials should remain in the global framework but should not be crawled yet.

Use this table:

| Material/source type | Reason to defer | What can still be indexed safely | Condition for future ingest |

Include:

- politically or culturally sensitive materials;
- unclear image rights;
- platform/social media records;
- private or commercial archives;
- anonymous community materials;
- records with weak authority resolution;
- sources whose terms forbid automated access.

### 10. Database Patch Recommendations

Return machine-usable recommendations grouped by target file:

```text
data/experimental_ingest_shortlist.csv
- add/adjust ...

data/regional_movements.csv
- add/adjust ...

data/regional_event_nodes.csv
- add/adjust ...

data/source_registry.csv
- add/adjust ...

data/search_vocabulary.csv
- add/adjust ...

db/schema or API
- add/adjust ...
```

### 11. Final Readiness Flag

End with:

- `FIRST_INGEST_CAN_START_AFTER_TERMS_REVIEW: yes/no`
- `BLOCKING_SCOPE_GAPS: ...`
- `BLOCKING_RIGHTS_GAPS: ...`
- `RECOMMENDED_FIRST_INGEST_RECORD_COUNT: ...`
- `RECOMMENDED_FIRST_INGEST_MOVEMENT_COUNT: ...`
- `RECOMMENDED_FIRST_INGEST_EVENT_COUNT: ...`
- `RECOMMENDED_SOURCE_COUNT: ...`

## Output Style

Be precise and operational.

Do not produce inspirational prose. Do not design the frontend. Do not write a general history of graphic design. The output should allow a researcher or developer to update CSV seed files, plan source terms reviews, and prepare the first experimental ingest.
