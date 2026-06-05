# Non-mainstream Low-coverage Source Probe Health 1990-2026 v3

This audit measures the v3 source-discovery/probe pass. It does not audit ingested item records, does not download images, and does not grant image rights.

## Goal Check

- Baseline global edge candidate sources: 81
- New candidate sources: 228 / target 220 (103.64%)
- Baseline + new candidate pool: 309
- Probe successes: 127 / target 120 (105.83% of target)
- Probe health / ok rate: 55.70%
- P1 actionable rows: 119 (52.19%)
- Source-visible protocol candidates: 13 (5.70%)
- IMG01/IMG03 automatic upgrades: 0

## Probe Status

- ok: 127
- failed: 90
- http_error: 11

## Candidate Priority And Impact

- candidate_priority_all / P1: 135 (59.21%)
- candidate_priority_all / P2: 77 (33.77%)
- candidate_priority_all / P0: 16 (7.02%)
- impact_rating_all / B: 138 (60.53%)
- impact_rating_all / A: 81 (35.53%)
- impact_rating_all / C: 9 (3.95%)
- candidate_priority_ok / P1: 79 (62.20%)
- candidate_priority_ok / P2: 37 (29.13%)
- candidate_priority_ok / P0: 11 (8.66%)
- impact_rating_ok / B: 73 (57.48%)
- impact_rating_ok / A: 51 (40.16%)
- impact_rating_ok / C: 3 (2.36%)

## Macro-region Breakdown

- Africa: candidates 65, ok 29 (44.62%), failed 34, http_error 2, P1 actionable 27, source-visible protocol 2
- Latin America / Caribbean: candidates 58, ok 34 (58.62%), failed 19, http_error 5, P1 actionable 33, source-visible protocol 3
- MENA: candidates 22, ok 14 (63.64%), failed 6, http_error 2, P1 actionable 13, source-visible protocol 1
- South Asia: candidates 22, ok 12 (54.55%), failed 9, http_error 1, P1 actionable 11, source-visible protocol 0
- Eastern Europe / Caucasus: candidates 21, ok 18 (85.71%), failed 3, http_error 0, P1 actionable 16, source-visible protocol 6
- Southeast Asia: candidates 17, ok 9 (52.94%), failed 7, http_error 1, P1 actionable 9, source-visible protocol 1
- Oceania / Indigenous: candidates 13, ok 5 (38.46%), failed 8, http_error 0, P1 actionable 4, source-visible protocol 0
- Central Asia: candidates 8, ok 5 (62.50%), failed 3, http_error 0, P1 actionable 5, source-visible protocol 0
- East Asia: candidates 2, ok 1 (50.00%), failed 1, http_error 0, P1 actionable 1, source-visible protocol 0

## Failure Families

- dns_or_domain: 56
- ssl_or_certificate: 18
- timeout: 13
- http_403: 8
- http_404: 2
- other_failure: 2
- http_500: 1
- network_unreachable: 1

## High-value Reachable Next Queue

- NLCV30002 | National Library of Nigeria | Africa / West Africa | P1 / impact A | bibliographic_adapter | HTML/catalog
- NLCV30007 | National Archives of Zimbabwe | Africa / Southern Africa | P1 / impact A | wordpress_rest_or_html_adapter | RSS/Atom;JSON-LD;WordPress REST
- NLCV30011 | National Archives of Tanzania | Africa / East Africa | P1 / impact A | headless_metadata_probe_only | Static JS App
- NLCV30012 | National Library and Archives of Ethiopia | Africa / East Africa | P1 / impact A | html_jsonld_adapter | JSON-LD;PDF
- NLCV30014 | Archives Nationales de Tunisie | Africa / North Africa | P1 / impact A | wordpress_rest_or_html_adapter | RSS/Atom;JSON-LD;WordPress REST
- NLCV30015 | Bibliotheque Nationale d'Algerie | Africa / North Africa | P1 / impact A | wordpress_rest_or_html_adapter | RSS/Atom;JSON-LD;WordPress REST
- NLCV30018 | Archives Nationales du Senegal | Africa / West Africa | P1 / impact A | wordpress_rest_or_html_adapter | RSS/Atom;WordPress REST;PDF
- NLCV30031 | Archivo Nacional de Chile | Latin America / Caribbean / Southern Cone | P1 / impact B | rss_atom_source_adapter | RSS/Atom
- NLCV30032 | Museo de la Memoria y los Derechos Humanos | Latin America / Caribbean / Southern Cone | P0 / impact A | html_metadata_adapter | HTML/catalog
- NLCV30033 | Archivo General de la Nacion Uruguay | Latin America / Caribbean / Southern Cone | P1 / impact B | html_jsonld_adapter | JSON-LD;PDF
- NLCV30035 | Archivo Nacional de Asuncion | Latin America / Caribbean / Southern Cone | P1 / impact A | wordpress_rest_or_html_adapter | RSS/Atom;WordPress REST
- NLCV30037 | Archivo General de la Nacion Peru | Latin America / Caribbean / Andean | P1 / impact B | html_metadata_adapter | HTML
- NLCV30038 | Biblioteca Nacional de Colombia | Latin America / Caribbean / Andean | P1 / impact B | rss_atom_source_adapter | RSS/Atom
- NLCV30039 | Biblioteca Digital de Bogota | Latin America / Caribbean / Andean | P0 / impact A | iiif_manifest_adapter | IIIF
- NLCV30040 | Senal Memoria Colombia | Latin America / Caribbean / Andean | P1 / impact A | html_jsonld_adapter | JSON-LD
- NLCV30045 | Biblioteca Nacional de Venezuela | Latin America / Caribbean / Caribbean / North South America | P1 / impact B | wordpress_rest_or_html_adapter | WordPress REST
- NLCV30046 | Archivo General de la Nacion Venezuela | Latin America / Caribbean / Caribbean / North South America | P1 / impact B | wordpress_rest_or_html_adapter | RSS/Atom;WordPress REST
- NLCV30047 | Biblioteca Nacional de Brasil | Latin America / Caribbean / Brazil | P1 / impact B | html_jsonld_adapter | JSON-LD
- NLCV30049 | Mediateca INAH | Latin America / Caribbean / Mexico | P0 / impact A | html_jsonld_adapter | RSS/Atom;JSON-LD
- NLCV30052 | Archivo General de Centro America | Latin America / Caribbean / Central America | P1 / impact A | wordpress_rest_or_html_adapter | RSS/Atom;JSON-LD;WordPress REST;PDF
- NLCV30054 | Archivo Nacional de Costa Rica | Latin America / Caribbean / Central America | P1 / impact B | html_jsonld_adapter | JSON-LD;PDF
- NLCV30056 | Archivo Nacional de Panama | Latin America / Caribbean / Central America | P1 / impact B | html_metadata_adapter | HTML
- NLCV30061 | National Library of Jamaica | Latin America / Caribbean / Caribbean | P1 / impact B | wordpress_rest_or_html_adapter | RSS/Atom;WordPress REST;PDF
- NLCV30062 | Jamaica Archives and Records Department | Latin America / Caribbean / Caribbean | P1 / impact B | html_metadata_adapter | HTML
- NLCV30063 | National Archives of Trinidad and Tobago | Latin America / Caribbean / Caribbean | P1 / impact A | wordpress_rest_or_html_adapter | RSS/Atom;WordPress REST
- NLCV30064 | National Library of Trinidad and Tobago | Latin America / Caribbean / Caribbean | P1 / impact B | wordpress_rest_or_html_adapter | RSS/Atom;JSON-LD;WordPress REST;PDF
- NLCV30066 | Archivo General de la Nacion Republica Dominicana | Latin America / Caribbean / Caribbean | P1 / impact A | html_jsonld_adapter | RSS/Atom;JSON-LD;Static JS App;PDF
- NLCV30068 | Biblioteca Nacional Jose Marti | Latin America / Caribbean / Caribbean | P1 / impact B | iiif_manifest_adapter | IIIF;RSS/Atom;PDF
- NLCV30074 | Lebanese National Library | MENA / Levant | P1 / impact A | pdf_text_or_link_adapter | PDF
- NLCV30075 | American University of Beirut Libraries | MENA / Levant | P1 / impact A | html_jsonld_adapter | JSON-LD;PDF
- NLCV30077 | Jordan National Library | MENA / Levant | P1 / impact A | pdf_text_or_link_adapter | PDF
- NLCV30078 | Iraq National Library and Archive | MENA / Iraq | P1 / impact A | pdf_text_or_link_adapter | PDF
- NLCV30081 | UAE National Library and Archives | MENA / Gulf | P1 / impact B | html_metadata_adapter | HTML
- NLCV30084 | Oman National Records and Archives Authority | MENA / Gulf | P1 / impact B | wordpress_rest_or_html_adapter | RSS/Atom;JSON-LD;WordPress REST
- NLCV30086 | Bibliotheca Alexandrina Memory of Modern Egypt | MENA / North Africa | P0 / impact A | html_metadata_adapter | HTML/database
- NLCV30087 | National Archives of India Abhilekh Patal | South Asia / India | P1 / impact A | html_metadata_adapter | HTML/database
- NLCV30090 | Sarmaya Arts Foundation | South Asia / India | P1 / impact B | wordpress_rest_or_html_adapter | WordPress REST
- NLCV30092 | Citizens Archive of Pakistan | South Asia / Pakistan | P1 / impact A | wordpress_rest_or_html_adapter | RSS/Atom;JSON-LD;WordPress REST
- NLCV30094 | Liberation War Museum Bangladesh | South Asia / Bangladesh | P1 / impact A | headless_metadata_probe_only | Static JS App;PDF
- NLCV30102 | National Library of Vietnam Digital Library | Southeast Asia / Vietnam | P1 / impact A | wordpress_rest_or_html_adapter | RSS/Atom;JSON-LD;WordPress REST

## Boundary

- This pass is source discovery only.
- Raw probe text is third-party page text and should not be committed unless separately reviewed and redacted.
- `IMG01` and `IMG03` cannot be promoted from heuristic, LLM, platform, TOS, or protocol signals.
- Source-visible protocol candidates only indicate possible source-hosted viewing routes such as IIIF/CONTENTdm/DSpace/Kramerius.
- Impact/source priority remains internal triage only.
