# Global Edge Discovery Probe v1

Rights-safe source-level probe. This report records reachability, protocol signals, adapter hints, and next capture priority. It does not create public archive surfaces and does not download or possess source images.

- Access date: 2026-06-05
- Probe rows: 81
- Metrics rows: 98

## Safety Constraints

- IMG01 and IMG03 are never assigned from heuristic, visual, social, or LLM signals.
- IIIF/CONTENTdm/Kramerius evidence can recommend IMG02 only as source-hosted viewing, not reuse.
- Platform and social sources are discovery leads until original sources and rights are reviewed.
- Impact or priority signals are internal triage only, not public authority or inclusion claims.

## Probe Status

- ok: 60
- failed: 11
- http_error: 10

## Next Capture Priority

- P1 adapter build: 24
- P2 retry/manual verification: 21
- P1 text/source enrichment: 20
- P2 discovery lead queue: 11
- P2 manual source review: 5

## Region Mix

- Asia: 26
- Global: 19
- Latin America: 10
- Middle East and North Africa: 8
- Africa: 8
- Europe: 5
- Oceania: 4
- North America: 1

## Detected Protocols

- IIIF: 18
- RSS/Atom: 15
- Static JS App: 14
- JSON-LD: 13
- WordPress REST: 11
- PDF: 5
- GraphQL: 4
- ArchiveSpace/EAD: 3
- OAI-PMH: 1
- Kramerius: 1

## Adapter Hints

- manual_review_or_alternate_endpoint: 21
- iiif_manifest_adapter: 11
- discovery_signal_only_no_item_image_ingest: 11
- wordpress_rest_or_html_adapter: 9
- html_metadata_adapter: 6
- html_jsonld_adapter: 3
- bibliographic_adapter: 3
- rss_atom_source_adapter: 3
- manual_source_adapter: 2
- academic_graph_adapter: 1
- oai_pmh_adapter: 1
- bibliography_adapter: 1
- graphql_schema_probe_then_adapter: 1
- source_registry_context_adapter: 1
- library_api_adapter: 1
- network_map_adapter: 1
- pdf_text_or_link_adapter: 1
- kramerius_adapter: 1
- headless_metadata_probe_only: 1
- trove_adapter: 1
- digitalnz_adapter: 1

## P1 Candidates

- GED0002 | Getty Research Portal | Global / global art history | JSON-LD | html_jsonld_adapter
- GED0004 | Internet Archive | Global / global books and web | IIIF | iiif_manifest_adapter
- GED0005 | OpenAlex | Global / scholarly graph | API | academic_graph_adapter
- GED0006 | BASE Search | Global / open repositories | OAI-PMH | oai_pmh_adapter
- GED0009 | Zotero Public Group Libraries | Global / scholarly bibliography | API/HTML | bibliography_adapter
- GED0010 | China International Design Museum | Asia / East Asia | HTML/manual | manual_source_adapter
- GED0012 | National Library of China | Asia / East Asia | HTML/catalog | bibliographic_adapter
- GED0014 | M+ Collections | Asia / East Asia | RSS/Atom;GraphQL;Static JS App | graphql_schema_probe_then_adapter
- GED0015 | National Diet Library Digital Collections | Asia / East Asia | IIIF | iiif_manifest_adapter
- GED0016 | DNP Graphic Design Archives | Asia / East Asia | HTML | html_metadata_adapter
- GED0017 | Waseda University Library | Asia / East Asia | IIIF;RSS/Atom;WordPress REST | iiif_manifest_adapter
- GED0018 | Tokyo ADC | Asia / East Asia | HTML | source_registry_context_adapter
- GED0019 | Tokyo TDC | Asia / East Asia | JSON-LD;WordPress REST | wordpress_rest_or_html_adapter
- GED0020 | JAGDA | Asia / East Asia | WordPress REST | wordpress_rest_or_html_adapter
- GED0021 | Ginza Graphic Gallery | Asia / East Asia | HTML | html_metadata_adapter
- GED0022 | National Central Library Taiwan | Asia / East Asia | catalog/HTML | bibliographic_adapter
- GED0023 | Korean Design Archive | Asia / East Asia | JSON-LD | html_jsonld_adapter
- GED0025 | Priya Paul Collection | Asia / South Asia | IIIF;JSON-LD;Static JS App | iiif_manifest_adapter
- GED0028 | SADAA | Asia / South Asia diaspora | IIIF | iiif_manifest_adapter
- GED0031 | Malaysian Design Archive | Asia / Southeast Asia | RSS/Atom;JSON-LD;WordPress REST | wordpress_rest_or_html_adapter
- GED0033 | Vietnam National Library | Asia / Southeast Asia | catalog/HTML | bibliographic_adapter
- GED0036 | Fundacion IDA | Latin America / Southern Cone | IIIF;JSON-LD | iiif_manifest_adapter
- GED0037 | Diseno Nacional | Latin America / Southern Cone | RSS/Atom;JSON-LD;WordPress REST | wordpress_rest_or_html_adapter
- GED0039 | Archivo de Ilustracion Argentina | Latin America / Southern Cone | WordPress REST | wordpress_rest_or_html_adapter
- GED0041 | Princeton Latin American and Caribbean Ephemera | Latin America / Caribbean and Latin America | IIIF | iiif_manifest_adapter
- GED0042 | La Patria Uruguay | Latin America / Southern Cone | JSON-LD | html_jsonld_adapter
- GED0044 | Hemeroteca Digital Brasileira | Latin America / Brazil | RSS/Atom;WordPress REST;Static JS App;PDF | wordpress_rest_or_html_adapter
- GED0046 | Arabic Design Archive | Middle East and North Africa / Arab world | IIIF;Static JS App | iiif_manifest_adapter
- GED0051 | Dar al-Kutub | Middle East and North Africa / North Africa | RSS/Atom | rss_atom_source_adapter
- GED0053 | Arab Image Foundation | Middle East and North Africa / Levant | RSS/Atom;PDF | rss_atom_source_adapter
- GED0059 | African Activist Archive | Africa / Southern Africa and diaspora | HTML | html_metadata_adapter
- GED0060 | SAHA | Africa / Southern Africa | PDF | pdf_text_or_link_adapter
- GED0061 | Nelson Mandela Foundation Archive | Africa / Southern Africa | IIIF;ArchiveSpace/EAD;JSON-LD;Static JS App;PDF | iiif_manifest_adapter
- GED0062 | Graphic Front | Europe / Eastern Europe | HTML | html_metadata_adapter
- GED0064 | Kramerius Czech Digital Library | Europe / Central/Eastern Europe | IIIF;Kramerius | kramerius_adapter

## Failed Or Manual Retry

- GED0001 | World Digital Library | http_error | HTTP Error 403: Forbidden
- GED0003 | HathiTrust Digital Library | http_error | HTTP Error 403: Forbidden
- GED0008 | WorldCat and ArchiveGrid | http_error | HTTP Error 403: Forbidden
- GED0011 | CADAL | failed | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known>
- GED0013 | National Newspaper and Periodical Index | http_error | HTTP Error 412: Precondition Failed
- GED0024 | CIViC Archive | failed | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known>
- GED0026 | Tasveer Ghar | failed | URLError: <urlopen error [Errno 54] Connection reset by peer>
- GED0027 | Design Dashtahjaat | failed | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known>
- GED0029 | ASEAN Digital Library | failed | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known>
- GED0032 | Indonesia Design Archive | failed | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known>
- GED0034 | Thai Graphic Design Century | http_error | HTTP Error 404: Not Found
- GED0035 | Perpusnas Indonesia | http_error | HTTP Error 403: Forbidden
- GED0038 | Grafica Latina | failed | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known>
- GED0040 | ICAA Documents Project | http_error | HTTP Error 403: Forbidden
- GED0043 | Arquivo ESDI | failed | URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: certificate has expired (_ssl.c:1028)>
- GED0045 | Hemeroteca Nacional Digital de Mexico | failed | URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: Hostname mismatch, certificate is not valid for 'www.hndm.unam.mx'. (_ssl.c:1028)>
- GED0047 | Syrian Design Archive | failed | URLError: <urlopen error timed out>
- GED0048 | Archival Alliance | http_error | HTTP Error 404: Not Found
- GED0049 | Qatar Digital Library | http_error | HTTP Error 403: Forbidden
- GED0052 | Palestinian Museum Digital Archive | http_error | HTTP Error 429: Too Many Requests
- GED0056 | Frobenius Institute Digital Collections | failed | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known>

## Next Rule

Promote reachable protocol-family rows into source-family adapters first. Discovery-only rows should become source-registry or edge-source leads, not public image records, until a stable original source and rights basis are available.
