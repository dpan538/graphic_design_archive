# Source Expansion Matrix v0

Date: 2026-05-30

This file turns the researched source universe into an execution matrix. It is
not a claim of full coverage. It is a control surface for deciding which source
families to crawl next, which sources remain link-only, and which gaps still
need Deep Research.

## Generated Files

- `data/source_expansion_matrix.csv`
- `data/source_expansion_priority_1930_1970.csv`

## Scope

- Total source rows: 127
- 1931-1970 priority rows: 85
- P1 rows: 35
- P2 rows: 39
- Sources requiring targeted Deep Research: 36

## Region Counts

- Africa: 7
- East Asia: 15
- Eastern Europe: 12
- Global / web / transnational: 7
- Latin America: 13
- Latin America / Transregional: 1
- Latin America and the Caribbean: 4
- Mainland China: 1
- Middle East and North Africa: 6
- North America: 14
- North America / Global digital: 1
- Oceania and Pacific: 7
- South Asia: 7
- Southeast Asia: 12
- Western/Central Europe: 20

## Interpretation

The current live preview is structurally useful but source-poor. It uses AIC,
V&A, Library of Congress, and Met records heavily, so it proves the sheet system
can run but does not yet prove historical coverage. The next crawl should not
simply ask the same APIs for more records. It should deliberately rebalance
toward:

- text-rich periodical, newspaper, catalogue, and institutional sources;
- open or viewer-based image sources that can reduce `IMG00` table-only pages;
- non-Western and underrepresented regional sources;
- authority/context pages that can become real `IMG04` reading pages rather
  than failed-image placeholders.

## P1 1931-1970 Sources

| Source | Region | Access | Record family | Image | Text | Why next |
|---|---|---|---|---|---|---|
| Palestinian Museum Digital Archive | Middle East and North Africa | Public search + web item pages | poster_print_object;book_catalogue_text;authority_context;archive_finding_aid | High-viewer | High | P1 authority/context crawl |
| Cooper Hewitt Collection | North America | API + web + CSV | poster_print_object;archive_finding_aid | High-restricted | Low-Med | P1 object/image crawl |
| DPLA | North America | API | poster_print_object;authority_context | Med | Low-Med | P1 object/image crawl |
| LoC Prints & Photographs API | North America | API | poster_print_object | High-open | Low-Med | P1 object/image crawl |
| DigitalNZ | Oceania and Pacific | API | poster_print_object | Med | Low-Med | P1 object/image crawl |
| Wellcome Collection Catalogue API | Western/Central Europe | API | poster_print_object;archive_finding_aid | High-open | Med | P1 object/image crawl |
| NDL Digital Collections | East Asia | API + web | periodical_newspaper;poster_print_object;book_catalogue_text | High-open | High | P1 text-rich crawl |
| National Library of Korea Open API | East Asia | API + web | periodical_newspaper;archive_finding_aid | Med | High | P1 text-rich crawl |
| Kramerius | Eastern Europe | OAI + web | periodical_newspaper;poster_print_object | High-viewer | High | P1 text-rich crawl |
| POLONA | Eastern Europe | Web | periodical_newspaper;poster_print_object;book_catalogue_text | High-open | High | P1 text-rich crawl |
| dLib.si | Eastern Europe | OAI + web | periodical_newspaper;poster_print_object;book_catalogue_text | High-viewer | High | P1 text-rich crawl |
| Internet Archive / text and periodical collections | Global / web / transnational | API + web | periodical_newspaper;book_catalogue_text | Med | High | P1 text-rich crawl |
| Memoria Chilena | Latin America | OAI + web | periodical_newspaper;poster_print_object;book_catalogue_text | High-viewer | High | P1 text-rich crawl |
| Digital Library of the Caribbean | Latin America and the Caribbean | Public search + downloads + web item pages | periodical_newspaper;poster_print_object;book_catalogue_text | High-viewer | High | P1 text-rich crawl |
| Hemeroteca Digital Brasileira | Latin America and the Caribbean | Public search + viewer | periodical_newspaper;book_catalogue_text | High-viewer | High | P1 text-rich crawl |
| Hemeroteca Nacional Digital de Mexico | Latin America and the Caribbean | Public search + viewer | periodical_newspaper;poster_print_object;book_catalogue_text | High-viewer | High | P1 text-rich crawl |
| M68 Ciudadanias en Movimiento | Latin America and the Caribbean | Public search + web item pages | poster_print_object;book_catalogue_text;archive_finding_aid | High-viewer | High | P1 text-rich crawl |
| Chinese Posters | Mainland China | Public search + web item pages | poster_print_object;book_catalogue_text;archive_finding_aid | High-restricted | High | P1 text-rich crawl |
| National Library of Israel | Middle East and North Africa | Web + API routes to verify | periodical_newspaper;poster_print_object;book_catalogue_text;authority_context | High-viewer | High | P1 text-rich crawl |
| Harvard Art Museums API | North America | API | poster_print_object;book_catalogue_text;authority_context | High-viewer | High | P1 text-rich crawl |
| Library of Congress | North America | API + web | periodical_newspaper;poster_print_object;book_catalogue_text;archive_finding_aid | Med | High | P1 text-rich crawl |
| NYPL Digital Collections | North America | Web | periodical_newspaper;poster_print_object | High-viewer | High | P1 text-rich crawl |
| Internet Archive Metadata API | North America / Global digital | API + web | periodical_newspaper;poster_print_object;book_catalogue_text;web_born_digital | High-restricted | High | P1 text-rich crawl |
| Trove | Oceania and Pacific | API + web | periodical_newspaper;poster_print_object;book_catalogue_text;web_born_digital;archive_finding_aid | High-restricted | High | P1 text-rich crawl |

## P2 1931-1970 Sources

| Source | Region | Access | Record family | Image | Text | Why next |
|---|---|---|---|---|---|---|
| African Activist Archive | Africa | Public search + web item pages | poster_print_object;book_catalogue_text;authority_context;archive_finding_aid | High-viewer | High | P2 global-balance manual or semi-manual |
| Digital Innovation South Africa | Africa | Web | periodical_newspaper;book_catalogue_text;archive_finding_aid | Low-none | High | P2 global-balance manual or semi-manual |
| National Repository of Nigeria | Africa | Public search + downloads | periodical_newspaper;poster_print_object;book_catalogue_text | Low-none | High | P2 global-balance manual or semi-manual |
| South African History Archive | Africa | Web | poster_print_object;archive_finding_aid | High-restricted | Med | P2 global-balance manual or semi-manual |
| Wits Historical Papers / Medu Art Ensemble resources | Africa | Web + finding aids | poster_print_object;book_catalogue_text;archive_finding_aid | High-restricted | High | P2 global-balance manual or semi-manual |
| Bibliotheca Alexandrina Digital Assets Repository | Middle East and North Africa | Web | periodical_newspaper;book_catalogue_text | Med | High | P2 global-balance manual or semi-manual |
| Encyclopaedia Iranica / Iranian poster contextual records | Middle East and North Africa | Web | poster_print_object;book_catalogue_text;authority_context | Low-none | High | P2 global-balance manual or semi-manual |
| Poster House Iranian design pages | Middle East and North Africa | Web | poster_print_object;book_catalogue_text;archive_finding_aid | Low-none | High | P2 global-balance manual or semi-manual |
| AIATSIS NAIDOC poster collection | Oceania and Pacific | Web + manual protocol review | poster_print_object;archive_finding_aid | High-open | Low-Med | P2 global-balance manual or semi-manual |
| PANDORA / Australian Web Archive | Oceania and Pacific | Web | web_born_digital;archive_finding_aid | Med | Med | P2 global-balance manual or semi-manual |
| Papers Past | Oceania and Pacific | Public search + OCR + open-data subset | periodical_newspaper;poster_print_object;book_catalogue_text | High-viewer | High | P2 global-balance manual or semi-manual |
| State Library of NSW Collection | Oceania and Pacific | Public web item pages | poster_print_object;book_catalogue_text;archive_finding_aid | High-open | High | P2 global-balance manual or semi-manual |
| Te Papa Collections Online | Oceania and Pacific | Public web item pages | poster_print_object;book_catalogue_text;archive_finding_aid | High-open | High | P2 global-balance manual or semi-manual |
| Design in India / India Design Council references | South Asia | Web | book_catalogue_text;authority_context | Low-none | High | P2 global-balance manual or semi-manual |
| NID Archives and institutional publications | South Asia | Web + manual PDF | book_catalogue_text;authority_context;archive_finding_aid | Low-none | High | P2 global-balance manual or semi-manual |
| National Digital Library of India | South Asia | Web + search | book_catalogue_text;authority_context | Low-none | High | P2 global-balance manual or semi-manual |
| National Library of India | South Asia | Web | periodical_newspaper;book_catalogue_text;authority_context | Med | High | P2 global-balance manual or semi-manual |
| Tasveer Ghar | South Asia | Public search + web pages | poster_print_object;book_catalogue_text;authority_context;archive_finding_aid | High-restricted | High | P2 global-balance manual or semi-manual |
| Korean Newspaper Archive | East Asia | Web | periodical_newspaper | High-viewer | High | P2 source probe |
| NDL Image Bank | East Asia | Web | periodical_newspaper;poster_print_object;book_catalogue_text | High-open | High | P2 source probe |
| Shibusawa Shashi Database | East Asia | Public search + web pages | book_catalogue_text;authority_context | Low-none | High | P2 source probe |
| Czech Digital Library | Eastern Europe | Web | periodical_newspaper;poster_print_object;book_catalogue_text | High-viewer | High | P2 source probe |
| DIGAR | Eastern Europe | Web | periodical_newspaper;poster_print_object;book_catalogue_text;archive_finding_aid | High-viewer | High | P2 source probe |
| Hungaricana | Eastern Europe | Public search + web item pages | periodical_newspaper;poster_print_object;book_catalogue_text;archive_finding_aid | High-viewer | High | P2 source probe |
| Slovakiana | Eastern Europe | Web | periodical_newspaper;poster_print_object | High-viewer | High | P2 source probe |
| Szukaj w Archiwach | Eastern Europe | Web | poster_print_object;book_catalogue_text;authority_context;archive_finding_aid | High-viewer | High | P2 source probe |
| ePaveldas | Eastern Europe | Web + downloadable metadata endpoints | periodical_newspaper;poster_print_object | High-open | High | P2 source probe |
| Endangered Archives Programme | Global / web / transnational | Public search + IIIF/source viewer | periodical_newspaper;poster_print_object;book_catalogue_text;archive_finding_aid | High-viewer | High | P2 source probe |

## Deep Research Need

No broad Deep Research pass is needed before the next mechanical step. We now
have enough source candidates to expand the 1931-1970 crawl intelligently.

Deep Research should be used only for targeted holes where access, rights, or
local source names are still weak:

- South Asia beyond NID and the Eames India Report;
- MENA and Iranian/Arabic/Persian/Hebrew typography/poster sources;
- Africa beyond South Africa/Medu;
- Korea and Mainland China source APIs and rights;
- Latin America machine access for Brazil, Mexico, Argentina, Cuba, and
  Caribbean materials;
- Oceania/Pacific and Indigenous protocol handling beyond AIATSIS/Trove.

## Next Production Recommendation

For the next 1931-1970 expansion run, choose a mixed set:

1. one open/viewer image source,
2. one text-rich periodical/newspaper source,
3. one non-Western regional source,
4. one authority/context text source,
5. one existing API source only for targeted gap repair.

This should increase reading pages and image-bearing sheets without making the
archive dependent on copying images locally.
