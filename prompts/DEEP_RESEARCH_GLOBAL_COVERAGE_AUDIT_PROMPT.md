# Deep Research Prompt: Global Coverage Audit for a Rights-Aware Modern Graphic Design History Archive Index

Use this prompt to audit whether the project’s current global coverage framework is broad, balanced, and structurally adequate before the visual archive system is finalized.

## Project Definition

The project is a rights-aware archive index and research framework for modern graphic design history.

It does not replace archives, copy collections, build a course, or impose a single historical narrative. It indexes and links distributed works, texts, people, institutions, movements, media technologies, places, sources, citations, rights states, and historical nodes.

The public interface is planned as an archive-cabinet design system:

- cabinet / drawer / folder / loose-leaf / appendix / card / registration card / bookmark;
- one global `SEQ`;
- folders as filter views, not duplicate corpora;
- display number grammar: `GD / {ERA} / {HN} / {MV|NONE} / {SEQ} / {TIER}-p{PAGE}`;
- five sheet tiers: `S`, `M`, `L`, `XL`, `XXL`;
- fixed table kinds: `SOURCE`, `NORMALIZED`, `RIGHTS`, `CLASSIFICATION`, `RELATIONS`, `CITATIONS`;
- image zones: `IMG00`, `IMG01`, `IMG02`, `IMG03`;
- English UI chrome during development, source-language metadata preserved.

## Current Database / Coverage Skeleton

Audit against these current structures:

- `historical_nodes`: 15 global historical spine nodes from writing/printing preconditions through contemporary platform/generative visual communication.
- `movements`: 38 canonical/cross-regional movements, formations, technical regimes, counterpublic formations.
- `regions`: 15 launch regions:
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
- `coverage_matrix`: 225 region × historical-node coverage rows.
- `geographies`: 109 geography/context rows.
- `regional_movements`: 74 regional movements/formations.
- `regional_event_nodes`: 48 dateable regional event nodes.
- `regional_source_priorities`: 90 region/source-need rows.
- `sources`: 35 current candidate archive/source records.

The project already recognizes that it cannot claim total completion of all world graphic design events. The correct standard is: a launch-complete, gap-aware global framework that does not structurally defer non-Euro-American histories.

## Audit Goals

1. Identify major missing regions, countries, territories, diasporas, or transnational routes.
2. Identify missing movements, formations, schools, print cultures, state formations, counterpublics, media cultures, typography/script histories, commercial vernaculars, and digital/platform formations.
3. Identify missing dateable regional event nodes that should exist before design-system freeze.
4. Identify missing source families and concrete sources for each region.
5. Identify language/script needs that affect schema, search, and UI.
6. Identify rights and cultural protocol risks that affect image display and indexing policy.
7. Identify where current categories reproduce Euro-American, museum-centric, or poster-centric bias.
8. Recommend changes to database seed files, not frontend visuals.

## Required Output

Produce a structured report with these sections:

### 1. Executive Assessment

State whether the current skeleton is:

- structurally adequate;
- adequate with high-priority gaps;
- not yet adequate for design-system freeze.

Explain the answer.

### 2. Missing / Weak Geography Coverage

Use a table:

| Area | Current status | Missing context | Why it matters | Suggested `geographies.csv` rows |

Include countries/contexts that should not be collapsed into macro-regions.

### 3. Missing / Weak Regional Movements and Formations

Use a table:

| Region | Proposed movement/formation | Date range | Formation type | Related HN nodes | Source families | Rights risk | Notes |

Include noncanonical and nonmuseum-centered formations:

- vernacular commercial print;
- advertising and packaging;
- newspaper/periodical design;
- state public information;
- colonial/postcolonial print;
- anti-colonial/decolonial graphics;
- feminist, queer, labor, Black, Indigenous, diasporic, and community graphics;
- script and typography histories;
- film/popular media graphics;
- digital/interface/platform design.

### 4. Missing / Weak Regional Event Nodes

Use a table:

| Proposed event node | Region/geography | Date range | Event type | Related HN nodes | Related movements | Why this is structurally necessary |

These should be dateable enough to support browsing and filtering.

### 5. Source Coverage Audit

Use a table:

| Region/geography | Source type needed | Candidate sources | Access method | Rights/terms risk | Notes |

Prioritize:

- national libraries;
- museum collections;
- design archives;
- poster archives;
- periodical/newspaper archives;
- university special collections;
- community archives;
- web archives;
- authority/vocabulary sources;
- digitized books/catalogues.

### 6. Search Vocabulary / Language / Script Audit

Use a table:

| Language/script | Region | Required search terms or authority strategy | UI/schema impact |

Pay attention to:

- Chinese simplified/traditional;
- Japanese kanji/kana;
- Hangul/Hanja;
- Arabic/Persian/Hebrew;
- Devanagari/Bengali/Tamil/Telugu/Malayalam/Sinhala;
- Thai/Khmer/Burmese/Lao;
- Cyrillic;
- Indigenous languages and scripts where relevant;
- transliteration/romanization variants.

### 7. Rights and Protocol Risks

Use a table:

| Risk area | Affected materials | Recommended indexing policy | Image-zone implication |

Map recommendations to:

- `IMG00`: link only;
- `IMG01`: thumbnail only;
- `IMG02`: embed/IIIF only;
- `IMG03`: open image.

### 8. Bias and Methodology Warnings

List where the current skeleton risks:

- over-centering Europe/U.S.;
- over-centering museum holdings;
- over-centering posters;
- treating vernacular/commercial/popular media as secondary;
- flattening East Asia, Africa, Latin America, Southeast Asia, South Asia, MENA, or the Pacific;
- confusing visual resemblance with documented relation;
- confusing source availability with historical importance.

### 9. Concrete Patch Recommendations

Return machine-usable recommendations grouped by target file:

```text
data/geographies.csv
- add ...

data/regional_movements.csv
- add ...

data/regional_event_nodes.csv
- add ...

data/source_registry.csv
- add ...

data/search_vocabulary.csv
- add ...

db/schema or API
- add/adjust ...
```

### 10. Design-System Freeze Decision

End with:

- `FREEZE_READY: yes/no`
- `BLOCKING_GAPS: ...`
- `NEXT_DEEP_RESEARCH_NEEDED: ...`

Do not design the visual interface. Do not produce wireframes. This audit is about whether the historical, geographic, source, rights, and classification framework is strong enough to support the later archive-cabinet design system.
