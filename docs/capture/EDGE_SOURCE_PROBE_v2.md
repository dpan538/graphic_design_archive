# Edge Source Probe v2

Access date: 2026-06-01

This probe expands the candidate source pool beyond large museum APIs, prioritising local, community, university, professional, and government sources. It does not promote records into the public archive.

## Guardrails

- Raw payloads are secret-redacted before writing.
- Social platforms are discovery-only and default to `IMG00`; they are not evidence sources.
- Independent/community/private sources default to source-hosted or link-only image states.
- P1 means adapter/source-registry priority, not automatic publication.

## Summary

- Candidates: 64
- Reachable: 48
- P1 candidates: 37
- Macro-region counts: Africa=3, East Asia=14, Eastern Europe=2, Europe=1, Global=3, Latin America=5, Middle East=2, North America=1, Southeast Asia=17
- Protocol hints: ArchiveSpace/EAD=1, IIIF=3, JSON-LD=14, Next/static JS=1, PDF=7, RSS/Atom=6, WordPress REST/RSS=16

## P1 Candidates

| ID | Source | Region | Country | Protocols | Image policy |
| --- | --- | --- | --- | --- | --- |
| ESV201 | M+ Collections | East Asia | Hong Kong | HTML | IMG00_or_IMG02_after_source_terms |
| ESV203 | Hong Kong Heritage Project | East Asia | Hong Kong | HTML | IMG02_source_hosted_or_IMG00_until_item_rights |
| ESV205 | Taiwan Design Research Institute | East Asia | Taiwan | JSON-LD | IMG00_or_IMG02_after_source_terms |
| ESV207 | National Taiwan Museum of Fine Arts | East Asia | Taiwan | HTML | IMG00_or_IMG02_after_source_terms |
| ESV212 | Tokyo TDC | East Asia | Japan | WordPress REST/RSS;JSON-LD | IMG00_or_IMG02_after_source_terms |
| ESV215 | Seoul Design Foundation | East Asia | Korea | HTML | IMG00_or_IMG02_after_source_terms |
| ESV216 | DDP Seoul | East Asia | Korea | HTML | IMG00_or_IMG02_after_source_terms |
| ESV220 | National Library of Korea | East Asia | Korea | HTML | IMG00_or_IMG02_after_source_terms |
| ESV221 | DesignSingapore Council | Southeast Asia | Singapore | WordPress REST/RSS;JSON-LD | IMG00_or_IMG02_after_source_terms |
| ESV222 | BiblioAsia | Southeast Asia | Singapore | Next/static JS | IMG00_or_IMG02_after_source_terms |
| ESV223 | Roots.sg | Southeast Asia | Singapore | HTML | IMG00_or_IMG02_after_source_terms |
| ESV224 | National Gallery Singapore Collection | Southeast Asia | Singapore | JSON-LD;PDF | IMG00_or_IMG02_after_source_terms |
| ESV225 | Asian Film Archive | Southeast Asia | Singapore / regional | WordPress REST/RSS;JSON-LD | IMG02_source_hosted_or_IMG00_until_item_rights |
| ESV226 | VietGD | Southeast Asia | Vietnam | HTML | IMG02_source_hosted_or_IMG00_until_item_rights |
| ESV227 | Dogma Collection | Southeast Asia | Vietnam | HTML | IMG02_source_hosted_or_IMG00_until_item_rights |
| ESV228 | Vietnam National Museum of History | Southeast Asia | Vietnam | HTML | IMG00_or_IMG02_after_source_terms |
| ESV229 | Bophana Audiovisual Resource Center | Southeast Asia | Cambodia | WordPress REST/RSS;JSON-LD | IMG02_source_hosted_or_IMG00_until_item_rights |
| ESV233 | Museum Siam | Southeast Asia | Thailand | HTML | IMG00_or_IMG02_after_source_terms |
| ESV234 | Fine Arts Department Thailand | Southeast Asia | Thailand | HTML | IMG00_or_IMG02_after_source_terms |
| ESV235 | Design Center Philippines | Southeast Asia | Philippines | HTML | IMG00_or_IMG02_after_source_terms |
| ESV236 | Cultural Center of the Philippines | Southeast Asia | Philippines | WordPress REST/RSS;JSON-LD;PDF;RSS/Atom | IMG00_or_IMG02_after_source_terms |
| ESV238 | Grafis Nusantara | Southeast Asia | Indonesia | WordPress REST/RSS;IIIF;JSON-LD | IMG02_source_hosted_or_IMG00_until_item_rights |
| ESV239 | Desain Grafis Indonesia | Southeast Asia | Indonesia | WordPress REST/RSS | IMG02_source_hosted_or_IMG00_until_item_rights |
| ESV240 | Indonesian Visual Art Archive | Southeast Asia | Indonesia | WordPress REST/RSS | IMG02_source_hosted_or_IMG00_until_item_rights |
| ESV242 | Malaysia Design Archive | Southeast Asia | Malaysia | WordPress REST/RSS;ArchiveSpace/EAD;JSON-LD | IMG02_source_hosted_or_IMG00_until_item_rights |
| ESV244 | Another Graphic | Global | post-1990 international | WordPress REST/RSS;JSON-LD;RSS/Atom | IMG02_source_hosted_or_IMG00_until_item_rights |
| ESV245 | Fonts In Use | Global | global | WordPress REST/RSS;RSS/Atom | IMG00_or_IMG02_after_source_terms |
| ESV246 | People's Graphic Design Archive | Global | global/community | WordPress REST/RSS;IIIF;PDF;RSS/Atom | IMG02_source_hosted_or_IMG00_until_item_rights |
| ESV247 | Letterform Archive | North America | United States / global | WordPress REST/RSS;JSON-LD;PDF;RSS/Atom | IMG00_or_IMG02_after_source_terms |
| ESV248 | Design Reviewed | Europe | United Kingdom / global | WordPress REST/RSS;JSON-LD;RSS/Atom | IMG02_source_hosted_or_IMG00_until_item_rights |
| ESV252 | Archivo de la Grafica Chilena | Latin America | Chile | IIIF | IMG00_discovery_only_no_platform_image |
| ESV253 | Memoria Chilena | Latin America | Chile | HTML | IMG00_or_IMG02_after_source_terms |
| ESV255 | Arquivo Nacional Brasil | Latin America | Brazil | WordPress REST/RSS;JSON-LD;PDF | IMG00_or_IMG02_after_source_terms |
| ESV256 | Biblioteca Nacional Digital Brasil | Latin America | Brazil | WordPress REST/RSS | IMG00_or_IMG02_after_source_terms |
| ESV258 | South African History Archive | Africa | South Africa | PDF | IMG02_source_hosted_or_IMG00_until_item_rights |
| ESV259 | UWC Robben Island Mayibuye Archives | Africa | South Africa | HTML | IMG00_or_IMG02_after_source_terms |
| ESV262 | National Library and Archives of Iran | Middle East | Iran | HTML | IMG00_or_IMG02_after_source_terms |

## Failed / Manual Follow-Up

- ESV202 Hong Kong Film Archive: TimeoutError: The read operation timed out
- ESV204 Taiwan Cultural Memory Bank: URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: Missing Subject Key Identifier (_ssl.c:1028)>
- ESV206 Taiwan Film and Audiovisual Institute: HTTP 403: Forbidden
- ESV217 Design Korea: URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known>
- ESV218 MMCA Korea: URLError: <urlopen error [Errno 54] Connection reset by peer>
- ESV219 Seoul Museum of History: URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1028)>
- ESV230 Cambodia National Library: URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known>
- ESV231 Lao National Library: URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known>
- ESV232 Thai Film Archive: RemoteDisconnected: Remote end closed connection without response
- ESV237 Lopez Museum and Library: URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known>
- ESV241 National Library of Indonesia: HTTP 403: Forbidden
- ESV243 Pusat Dokumentasi Seni Malaysia: URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known>
- ESV249 Digital Archive of Graphic Design: URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known>
- ESV250 AIGA Design Archives: URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1028)>
- ESV251 Mexican Design Archive: URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known>
- ESV261 Palestinian Museum Digital Archive: HTTP 429: Too Many Requests
