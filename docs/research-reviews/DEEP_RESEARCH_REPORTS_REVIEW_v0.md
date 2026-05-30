# Deep Research Reports Review v0

**Date:** 2026-05-29  
**Reviewed files:**

- `Audit of the Global Coverage Framework for a Rights-Aware Graphic Design History Index.docx`
- `Authority and Vocabulary Normalization Audit for a Rights-Aware Graphic Design Archive Gateway.docx`

**Note:** The expected `Source & Rights Feasibility Audit` report is not currently present in the project folder. The current new reports cover global coverage and authority/vocabulary normalization.

## Executive Read

Both reports say the project is directionally strong but not ready for design-system freeze.

The shared reason is structural: if the archive-cabinet visual system is frozen now, the interface will make current gaps look authoritative. The blockers are not visual style; they are geography granularity, multilingual/script modeling, source-family coverage, authority-resolution workflow, and protocol-aware rights handling.

## Global Coverage Audit

Decision:

- `FREEZE_READY: no`

Main blockers:

- multilingual/script schema not explicit enough;
- macro-regions still flatten key sovereign, subregional, Indigenous, and diasporic geographies;
- `source_registry.csv` is too small and too vulnerable to museum/poster bias;
- rights model needs protocol-aware handling for Indigenous/community materials and unresolved-rights materials;
- event-node layer needs more dateable anti-colonial, state-formation, script-transition, and digital-transition anchors.

High-priority geography additions:

- Central Asia: Kazakhstan, Uzbekistan, Kyrgyzstan, Tajikistan, Turkmenistan;
- Caucasus: Armenia, Georgia, Azerbaijan, Caucasus diaspora routes;
- Iran as first-class Persian print/design context;
- Palestine/Israel/Mandatory Palestine and diaspora routes;
- Caribbean split beyond generic Latin America/Caribbean;
- Pakistan, Bangladesh, Sri Lanka, Nepal as separate South Asian contexts;
- Southeast Asia country splits and Singapore/Malaya/Jawi-Rumi context;
- West Africa, Horn of Africa, Southern Africa;
- Indigenous North America;
- Aboriginal and Torres Strait Islander Australia;
- Māori print and Pacific Island subregions.

High-priority regional movement additions:

- Arabic periodical modernity;
- Iranian modern graphic design and postrevolutionary public graphics;
- Soviet script reform in Central Asia;
- Pakistan Urdu commercial graphics;
- Bangladesh language movement graphics;
- South Asian vernacular packaging and magazines;
- Singapore campaign poster regime;
- Jawi/Rumi Malay print transition;
- Vietnam propaganda to Doi Moi design;
- Indonesian revolutionary and state graphics;
- Philippine komiks and film print;
- Taller de Grafica Popular / Mexican popular print;
- Chilean editorial and film magazine design;
- Caribbean music/carnival/tourism graphics;
- Southern Africa anti-apartheid workshop graphics;
- Māori niupepa and language print;
- Aboriginal rights graphics;
- East Asia editorial and platform design.

High-priority event-node additions:

- 1937 Taller de Grafica Popular founded in Mexico City;
- 1952 Bengali/Bangla language movement;
- 1955 Bandung Conference;
- 1959 ICAIC foundation;
- 1961 NID established;
- 1965 Singapore campaign poster phase;
- 1905 Zig-Zag launch in Chile;
- 1972 Aboriginal Tent Embassy;
- 1982 Medu / culture and resistance network;
- 1979 Iranian Revolution public graphics;
- 1986 Doi Moi media transition;
- 2004 Korea OASIS web archiving;
- 1842 early Māori newspaper phase.

High-priority source registry additions:

- East Asia: NDL Japan, National Library of Korea, Korean Newspaper Archive, OASIS Korea, NLC China, CADAL, Hong Kong Memory, CUHK Digital Repository, NCL Taiwan, Taiwan Memory.
- Southeast Asia: NewspaperSG, NLB poster collection, National Archives of Singapore, Vietnam National Library, Vietnam National Museum of History poster collection, Perpusnas Indonesia, National Library of the Philippines.
- South Asia: DSAL, NID Archives, NCA Archives, National Library of Pakistan, Punjab Public Library, Sri Lanka National Archives.
- MENA: Jrayed, NLI Arabic Press, Qatar Digital Library, Bibliotheca Alexandrina DAR, NLAI Iran, Arab Image Foundation.
- Africa: NLSA Repository, SAHA, Nelson Mandela Foundation collection, DISA, National Library Nigeria, Kenya National Library Service, Ethiopian NALA, African Activist Archive.
- Latin America/Caribbean: Hemeroteca Digital Brasileira, Memoria Chilena, BNMM Hemeroteca Digital, dLOC, National Library of Jamaica Digital.
- Caucasus/Pacific/Oceania: National Library of Armenia, Iverieli Georgia, Azerbaijan National Library, Trove, Papers Past, AIATSIS, Pacific Digital Library.
- Authority/web sources: Getty AAT/TGN/ULAN, VIAF, LC Linked Data, Archive-It, Wayback Machine.

Schema/API changes requested by the report:

- first-class `language_tag_bcp47`;
- first-class `script_code_iso15924`;
- `title_original`, `title_transliterated`, `title_translated_en`, `title_sort_key`;
- `name_original`, `name_variant`, `name_preferred_by_community`;
- controlled `transliteration_scheme`;
- richer rights fields: `rights_basis`, `rights_notes`, `display_zone_max`;
- IIIF fields: `iiif_rights`, `required_statement`;
- protocol fields: `protocol_notice`, `tk_label`, `community_access_flag`, `sensitivity_flag`, `deceased_name_warning`;
- relation qualifiers separating documented influence, shared institution, shared political network, distribution route, and formal similarity only;
- source type/access mode enums;
- filters by geography, movement, event node, language, script, source type, rights zone, and protocol flag.

## Authority & Vocabulary Audit

Decision:

- `AUTHORITY_NORMALIZATION_READY: no`

Recommended strategy:

- use plural authority control by entity class;
- do not use one master authority;
- preserve source-language labels and attested transliterations;
- use local editorial authority for works, movements, regional formations, themes, contested/historical geographies, script-centered formations, vernacular/platform/activist/decolonial/community categories;
- treat Wikidata as secondary discovery/crosswalk infrastructure, not final authority;
- keep `possibly_same_as`, `candidate_match`, and `multiple_possible_matches` separate from reviewed identity.

Recommended primary authorities:

- Getty AAT: media, techniques, broad concepts;
- Getty ULAN: people, studios, art/design corporate bodies where covered;
- Getty TGN: art-historical places;
- LCNAF and national library authorities: names not adequately covered by Getty;
- VIAF: reconciliation layer;
- ISO 639 and ISO 15924: language/script coding;
- WorldCat/OCLC: texts/publications and bibliographic context;
- ISNI: creative public identities where present;
- ORCID: authenticated research identities only where directly relevant.

Main schema blockers:

- no explicit reviewed authority-resolution state machine;
- `entity_aliases` is too thin for language, script, source, transliteration system, and validity dates;
- `external_identifiers` needs stronger status, evidence, confidence, and deprecation handling;
- canonical movements and regional formations need structural distinction in schema/API;
- geography needs historical jurisdictions, contested status, and role-coded assertions;
- predicates need evidence rules, inverse labels, and public-visibility controls;
- public read models must expose uncertainty and source-language labels, not only preferred normalized labels.

Recommended search vocabulary model:

`search_vocabulary.csv` should become a controlled multilingual query layer where one row is one term in one language/script/form, linked to an entity or classification when possible.

Recommended fields:

- `entity_id` or `classification_id`;
- `term_text`;
- `term_type`;
- `language_code`;
- `script_code`;
- `romanization_system`;
- `source_id`;
- `authority_source_id`;
- `broader_term_ids`, `narrower_term_ids`, `related_term_ids`;
- `region_scope_id`;
- `time_scope`;
- `deprecated_redirect_to`;
- `expansion_mode`;
- `never_imply_identity`;
- `never_imply_influence`;
- `citation_required_for_expansion`.

Predicate rule with strong methodological value:

Only `visually_resembles` may be asserted from visual comparison alone, and it must be low-confidence / non-causal. `influenced_by`, `associated_with`, `part_of`, movement membership, and historical relation claims require documentary, source-metadata, or scholarly citation.

## Immediate Implications for This Project

### Do Now

1. Add an authority-normalization schema migration.
2. Add richer multilingual/appellation fields without destroying existing seed CSVs.
3. Add authority resolution events and evidence bundles.
4. Add protocol-aware rights fields before the first experimental ingest.
5. Expand coverage seed generation for the missing geographies, regional movements, and event nodes.
6. Expand `source_registry.csv` using the coverage audit source recommendations.

### Do After Source & Rights Feasibility Audit

1. Select first experimental ingest sources.
2. Map candidate sources to `IMG00`-`IMG03`, with `IMG04` reserved for pages with no image frame.
3. Decide which APIs/IIIF endpoints are safe enough for automated or semi-automated tests.
4. Test 20-30 records through the full paper-surface model.

### Do Not Yet

1. Do not freeze the visual archive system.
2. Do not rewrite the visual archive Deep Research prompt yet.
3. Do not let Cursor implement final cabinet UI from current data.
4. Do not claim global completion.

## Implemented Follow-Up

The recommended `007_authority_normalization_skeleton.sql` migration has been added. It covers:

- authority resolution event log;
- evidence/citation bundle support;
- richer entity appellations;
- richer place/geography appellations;
- strengthened relation predicate rules;
- protocol-aware rights extensions;
- language/script fields for source records and normalized entities;
- read models exposing authority status, labels, scripts, identifiers, and unresolved matches.

In parallel, the missing `Source & Rights Feasibility Audit` should still be run or added to the project folder, because neither of the two reviewed reports replaces it.

The coverage seed files were also expanded from the Global Coverage Audit recommendations:

- `geographies.csv`: 71 to 109 rows;
- `regional_movements.csv`: 55 to 74 rows;
- `regional_event_nodes.csv`: 35 to 48 rows;
- searchable seed documents: 797 to 867.
