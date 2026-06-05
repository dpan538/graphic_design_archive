# Non-mainstream Low-coverage Source Probe 1990-2026 v3

Rights-safe source-level probe. This report records reachability, protocol signals, adapter hints, and next capture priority. It does not create public archive surfaces and does not download or possess source images.

- Access date: 2026-06-05
- Probe rows: 228
- Metrics rows: 98

## Safety Constraints

- IMG01 and IMG03 are never assigned from heuristic, visual, social, or LLM signals.
- IIIF/CONTENTdm/Kramerius evidence can recommend IMG02 only as source-hosted viewing, not reuse.
- Platform and social sources are discovery leads until original sources and rights are reviewed.
- Impact or priority signals are internal triage only, not public authority or inclusion claims.

## Probe Status

- ok: 127
- failed: 90
- http_error: 11

## Next Capture Priority

- P2 retry/manual verification: 101
- P1 adapter build: 68
- P1 text/source enrichment: 51
- P2 manual source review: 8

## Region Mix

- Africa: 65
- Latin America / Caribbean: 58
- MENA: 22
- South Asia: 22
- Eastern Europe / Caucasus: 21
- Southeast Asia: 17
- Oceania / Indigenous: 13
- Central Asia: 8
- East Asia: 2

## Detected Protocols

- RSS/Atom: 59
- WordPress REST: 55
- JSON-LD: 43
- PDF: 33
- Static JS App: 30
- IIIF: 10
- DSpace: 3
- CONTENTdm: 1

## Adapter Hints

- manual_review_or_alternate_endpoint: 101
- wordpress_rest_or_html_adapter: 50
- html_metadata_adapter: 19
- html_jsonld_adapter: 13
- headless_metadata_probe_only: 11
- bibliographic_adapter: 10
- iiif_manifest_adapter: 9
- rss_atom_source_adapter: 5
- pdf_text_or_link_adapter: 4
- dspace_oai_or_rest_adapter: 3
- manual_source_adapter: 1
- contentdm_source_adapter: 1
- aggregator_metadata_adapter: 1

## P1 Candidates

- NLCV30002 | National Library of Nigeria | Africa / West Africa | HTML/catalog | bibliographic_adapter
- NLCV30007 | National Archives of Zimbabwe | Africa / Southern Africa | RSS/Atom;JSON-LD;WordPress REST | wordpress_rest_or_html_adapter
- NLCV30009 | Kenya National Library Service | Africa / East Africa | RSS/Atom;JSON-LD;WordPress REST | wordpress_rest_or_html_adapter
- NLCV30011 | National Archives of Tanzania | Africa / East Africa | Static JS App | headless_metadata_probe_only
- NLCV30012 | National Library and Archives of Ethiopia | Africa / East Africa | JSON-LD;PDF | html_jsonld_adapter
- NLCV30014 | Archives Nationales de Tunisie | Africa / North Africa | RSS/Atom;JSON-LD;WordPress REST | wordpress_rest_or_html_adapter
- NLCV30015 | Bibliotheque Nationale d'Algerie | Africa / North Africa | RSS/Atom;JSON-LD;WordPress REST | wordpress_rest_or_html_adapter
- NLCV30016 | Centre de Documentation Saharienne | Africa / North Africa | IIIF | iiif_manifest_adapter
- NLCV30018 | Archives Nationales du Senegal | Africa / West Africa | RSS/Atom;WordPress REST;PDF | wordpress_rest_or_html_adapter
- NLCV30022 | National Archives of The Gambia | Africa / West Africa | RSS/Atom;JSON-LD;WordPress REST | wordpress_rest_or_html_adapter
- NLCV30026 | Rwanda Cultural Heritage Academy | Africa / East Africa | RSS/Atom;JSON-LD | html_jsonld_adapter
- NLCV30027 | Eswatini National Archives | Africa / Southern Africa | JSON-LD;PDF | html_jsonld_adapter
- NLCV30028 | Lesotho National Archives | Africa / Southern Africa | RSS/Atom;JSON-LD;WordPress REST | wordpress_rest_or_html_adapter
- NLCV30030 | Museo de Arte Moderno de Buenos Aires | Latin America / Caribbean / Southern Cone | RSS/Atom;JSON-LD;WordPress REST;Static JS App;PDF | wordpress_rest_or_html_adapter
- NLCV30031 | Archivo Nacional de Chile | Latin America / Caribbean / Southern Cone | RSS/Atom | rss_atom_source_adapter
- NLCV30032 | Museo de la Memoria y los Derechos Humanos | Latin America / Caribbean / Southern Cone | HTML/catalog | html_metadata_adapter
- NLCV30033 | Archivo General de la Nacion Uruguay | Latin America / Caribbean / Southern Cone | JSON-LD;PDF | html_jsonld_adapter
- NLCV30034 | Biblioteca Nacional del Paraguay | Latin America / Caribbean / Southern Cone | RSS/Atom;WordPress REST | wordpress_rest_or_html_adapter
- NLCV30035 | Archivo Nacional de Asuncion | Latin America / Caribbean / Southern Cone | RSS/Atom;WordPress REST | wordpress_rest_or_html_adapter
- NLCV30037 | Archivo General de la Nacion Peru | Latin America / Caribbean / Andean | HTML | html_metadata_adapter
- NLCV30038 | Biblioteca Nacional de Colombia | Latin America / Caribbean / Andean | RSS/Atom | rss_atom_source_adapter
- NLCV30039 | Biblioteca Digital de Bogota | Latin America / Caribbean / Andean | IIIF | iiif_manifest_adapter
- NLCV30040 | Senal Memoria Colombia | Latin America / Caribbean / Andean | JSON-LD | html_jsonld_adapter
- NLCV30045 | Biblioteca Nacional de Venezuela | Latin America / Caribbean / Caribbean / North South America | WordPress REST | wordpress_rest_or_html_adapter
- NLCV30046 | Archivo General de la Nacion Venezuela | Latin America / Caribbean / Caribbean / North South America | RSS/Atom;WordPress REST | wordpress_rest_or_html_adapter
- NLCV30047 | Biblioteca Nacional de Brasil | Latin America / Caribbean / Brazil | JSON-LD | html_jsonld_adapter
- NLCV30049 | Mediateca INAH | Latin America / Caribbean / Mexico | RSS/Atom;JSON-LD | html_jsonld_adapter
- NLCV30051 | Biblioteca Nacional de Guatemala | Latin America / Caribbean / Central America | RSS/Atom;JSON-LD;WordPress REST;PDF | wordpress_rest_or_html_adapter
- NLCV30052 | Archivo General de Centro America | Latin America / Caribbean / Central America | RSS/Atom;JSON-LD;WordPress REST;PDF | wordpress_rest_or_html_adapter
- NLCV30054 | Archivo Nacional de Costa Rica | Latin America / Caribbean / Central America | JSON-LD;PDF | html_jsonld_adapter
- NLCV30056 | Archivo Nacional de Panama | Latin America / Caribbean / Central America | HTML | html_metadata_adapter
- NLCV30061 | National Library of Jamaica | Latin America / Caribbean / Caribbean | RSS/Atom;WordPress REST;PDF | wordpress_rest_or_html_adapter
- NLCV30062 | Jamaica Archives and Records Department | Latin America / Caribbean / Caribbean | HTML | html_metadata_adapter
- NLCV30063 | National Archives of Trinidad and Tobago | Latin America / Caribbean / Caribbean | RSS/Atom;WordPress REST | wordpress_rest_or_html_adapter
- NLCV30064 | National Library of Trinidad and Tobago | Latin America / Caribbean / Caribbean | RSS/Atom;JSON-LD;WordPress REST;PDF | wordpress_rest_or_html_adapter

## Failed Or Manual Retry

- NLCV30001 | National Archives of Nigeria | failed | URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1028)>
- NLCV30004 | National Archives of Namibia | failed | URLError: <urlopen error timed out>
- NLCV30005 | Botswana National Archives and Records Services | http_error | HTTP Error 404: Not Found
- NLCV30006 | National Archives of Zambia | failed | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known>
- NLCV30008 | National Records and Archives Services Malawi | failed | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known>
- NLCV30010 | Uganda National Library | failed | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known>
- NLCV30013 | Archives du Maroc | http_error | HTTP Error 500: Internal Server Error
- NLCV30017 | National Library of Sudan | failed | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known>
- NLCV30019 | Bibliotheque Nationale du Senegal | failed | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known>
- NLCV30020 | Archives Nationales de Cote d'Ivoire | failed | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known>
- NLCV30021 | Bibliotheque Nationale de Cote d'Ivoire | failed | URLError: <urlopen error [SSL: WRONG_VERSION_NUMBER] wrong version number (_ssl.c:1028)>
- NLCV30023 | National Library of Sierra Leone | failed | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known>
- NLCV30024 | National Archives of Liberia | failed | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known>
- NLCV30025 | Rwanda Archives and Library Services Authority | failed | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known>
- NLCV30029 | CeDInCI | failed | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known>
- NLCV30036 | Repositorio Institucional BNP Peru | failed | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known>
- NLCV30041 | Archivo General de la Nacion Colombia | failed | URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1028)>
- NLCV30042 | Biblioteca Nacional del Ecuador | failed | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known>
- NLCV30043 | Archivo Nacional del Ecuador | http_error | HTTP Error 403: Forbidden
- NLCV30044 | Biblioteca y Archivo Historico de la Asamblea Legislativa Bolivia | failed | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known>
- NLCV30048 | Itaú Cultural Enciclopedia | http_error | HTTP Error 403: Forbidden
- NLCV30050 | Museo del Estanquillo | failed | URLError: <urlopen error timed out>
- NLCV30053 | Biblioteca Nacional Miguel Obregon Lizano | http_error | HTTP Error 403: Forbidden
- NLCV30055 | Biblioteca Nacional de Panama | failed | URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1028)>
- NLCV30057 | Biblioteca Nacional de El Salvador | failed | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known>
- NLCV30058 | Archivo General de la Nacion El Salvador | http_error | HTTP Error 403: Forbidden
- NLCV30059 | Biblioteca Nacional de Honduras | failed | URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: Hostname mismatch, certificate is not valid for 'www.ihah.hn'. (_ssl.c:1028)>
- NLCV30060 | Instituto de Historia de Nicaragua y Centroamerica | failed | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known>
- NLCV30065 | Bibliotheque Nationale d'Haiti | failed | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known>
- NLCV30067 | Biblioteca Nacional Pedro Henriquez Urena | http_error | HTTP Error 403: Forbidden
- NLCV30069 | Archivo Nacional de Cuba | failed | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known>
- NLCV30070 | National Library of Israel Collections | http_error | HTTP Error 403: Forbidden
- NLCV30072 | Istanbul University Library Rare Works | failed | URLError: <urlopen error timed out>
- NLCV30073 | Milli Kutuphane Turkey | failed | URLError: <urlopen error [Errno 51] Network is unreachable>
- NLCV30076 | Moise A. Khayrallah Center Archive | http_error | HTTP Error 404: Not Found

## Next Rule

Promote reachable protocol-family rows into source-family adapters first. Discovery-only rows should become source-registry or edge-source leads, not public image records, until a stable original source and rights basis are available.
