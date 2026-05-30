# First 48 Target Verification Pass v0

Date: 2026-05-30

Purpose: mechanical verification of the first 48 target records/search paths before any ingest script is written.

This is not a historical interpretation pass. It checks whether each target can be treated as:

- a stable exact record;
- a deterministic search path;
- a metadata-only / link-only record;
- a candidate for `IMG02` or `IMG03`;
- blocked or requiring replacement before ingest.

## Executive Result

The first 48 set is usable, but not as a blind automated crawl list.

Machine-readable output:

- `data/first_ingest_target_verifications.csv`
- `api_first_ingest_target_verifications`

Summary:

- Ready for manual metadata ingest now: 30
- Ready only after exact URL / browser / page-level recheck: 12
- Search-path only and should not be ingested as a source record yet: 5
- Recommended source replacement: 1

Image decisions:

- `IMG00` remains correct for restricted/unclear image records.
- `IMG02` is confirmed for the NAS multilingual sign case where viewing is permitted and reproduction requires written permission.
- `IMG03` is plausible for the selected NAIDOC posters because AIATSIS/NAIDOC page text gives Creative Commons BY-NC-ND evidence, but the records still require protocol notes and exact license capture.
- `IMG04` is correct for authority, institutional, event, standards, and text-only pages.

## Verification Rules Used

- Public visibility is not treated as image permission.
- Source-level openness is not enough to upgrade images; item-level evidence is required.
- Search result snippets are acceptable only for target discovery, not for final source capture.
- If a source page blocks automated reading but appears to be a stable target, it is marked `needs_browser_recheck`.
- If the target is a search path, it remains planning data until an exact record URL is captured.

## Row-Level Verification

| Target | Decision | IMG | Verification note | Required action |
|---|---|---:|---|---|
| FIT001 | ready_manual_link_only | IMG00 | Harvard exact object page opened; metadata and rights fields present; copyright lists ARS / VG Bild-Kunst; permissions text is personal/noncommercial-oriented. | Ingest metadata only; no image display. |
| FIT002 | needs_browser_recheck | IMG00 | Harvard target is plausible and cited in external Harvard context, but direct record fetch did not resolve in this pass. | Recheck in browser or Harvard API before source-record creation. |
| FIT003 | ready_manual_text_authority | IMG04 | Getty ULAN search result confirms Walter Gropius authority ID, variants, roles, dates, and vocabulary page. | Ingest as authority record. |
| FIT004 | needs_browser_recheck | IMG04 | Harvard tour URL returned 403 in automated fetch. Related Harvard Bauhaus exhibition pages are available. | Prefer accessible Harvard exhibition page if tour slide remains blocked. |
| FIT005 | ready_manual_link_only | IMG00 | MoMA exact object page opened; object metadata and copyright/licensing restrictions present. | Ingest metadata only; no image display. |
| FIT006 | ready_manual_link_only | IMG00 | MoMA exact object page opened; object metadata available; MoMA licensing restrictions apply. | Ingest metadata only; no image display. |
| FIT007 | ready_manual_text | IMG04 | IBM design-program page opens as stable institutional history page. | Ingest as institutional page. |
| FIT008 | ready_manual_text | IMG04 | IBM logo-history page opens as stable institutional history page. | Ingest as institutional page. |
| FIT009 | ready_manual_link_only | IMG00 | MoMA exact object page opened; metadata available; reproduction routed to licensing. | Ingest metadata only. |
| FIT010 | ready_manual_link_only | IMG00 | MoMA exact object page opened; product/object metadata available; reproduction routed to licensing. | Ingest metadata only. |
| FIT011 | ready_manual_link_only | IMG00 | MoMA exact object page opened; TGP exhibition poster target is stable enough. | Ingest metadata only. |
| FIT012 | ready_manual_link_only | IMG00 | Library of Congress exact item page opens; keep LOC rights advisory as evidence. | Ingest metadata and rights note; no image display unless item rights improve. |
| FIT013 | ready_manual_link_only | IMG00 | Getty CONA exact record opens and provides rich component/work metadata. | Ingest metadata; treat image/copyright as restricted. |
| FIT014 | ready_manual_link_only | IMG00 | MoMA exact object page opens; TGP anti-fascist lecture poster target is stable. | Ingest metadata only. |
| FIT015 | search_path_only | IMG00 | Still a deterministic BND Chile search path, not an exact source record. | Resolve exact BND item URL before ingest. |
| FIT016 | search_path_only | IMG00 | Still a deterministic BND Chile search path, not an exact source record. | Resolve exact BND item URL and creator/subject relationship. |
| FIT017 | search_path_only | IMG00 | Still a contextual MMDH search path. | Find stable object or collection page; otherwise keep as citation-only context. |
| FIT018 | needs_browser_recheck | IMG04 | NDL exact URL is plausible but automated fetch failed. | Recheck in browser / NDL API before source-record creation. |
| FIT019 | search_path_only | IMG04 | NDL report remains a search path. | Capture exact NDL persistent record. |
| FIT020 | ready_manual_text_event | IMG04 | museum.or.jp event page opened; Japanese exhibition/event metadata available. | Ingest as event page. |
| FIT021 | ready_manual_text_institution | IMG04 | JAGDA history page target remains suitable as institutional page. | Ingest manually; no image capture. |
| FIT022 | ready_manual_link_only_issue | IMG00 | Internet Archive exact issue page opened; title, date, topics, language, identifier, and embed/download options visible; rights remain unclear. | Ingest issue metadata only; no image display. |
| FIT023 | needs_page_level_recheck | IMG00 | Parent IA issue is verified, but page 7 role still needs page-level confirmation. | Verify page locator before creating child page record. |
| FIT024 | needs_page_level_recheck | IMG00 | Parent IA issue is verified, but page 8 ad-page classification still needs page-level confirmation. | Verify page locator before creating child page record. |
| FIT025 | ready_manual_link_only | IMG00 | HKU exact record opened; bilingual title and artist text visible; page footer states all rights reserved. | Ingest metadata only; no image display. |
| FIT026 | replace_target | IMG00 | Original OpenArchive target was not confirmed. Seoul Museum of Art Archive has an exact record for the same poster with clearer metadata and explicit copyright warning. | Replace source target with SEMA record `MA-06-00004326`. |
| FIT027 | needs_exact_record_url | IMG00 | Kdemo search results confirm title, registration number `00976552`, date `1987.05.16`, and poster description, but direct item page needs capture. | Resolve exact item page or stable search-result citation. |
| FIT028 | needs_browser_recheck | IMG04 | Kdemo search result confirms Hong Sung-dam oral archive content, but direct automated page returned 404. | Browser recheck required before ingest. |
| FIT029 | ready_manual_viewer_only | IMG02 | NAS exact record opened; access line says viewing permitted and use/reproduction require written permission; credit line present. | Ingest as IMG02/viewer-only, no local copy. |
| FIT030 | needs_browser_recheck | IMG02 | NAS target hit JavaScript anti-bot page in automated fetch; same source pattern as FIT029. | Browser recheck; if access line matches, keep IMG02. |
| FIT031 | needs_browser_recheck | IMG04 | NAS government-record target did not fetch in automated pass. | Browser recheck before ingest. |
| FIT032 | ready_manual_text_institution | IMG04 | NID history page opened; establishment, Eames Report, and institutional chronology text available. | Ingest as institutional page. |
| FIT033 | ready_manual_text_pdf | IMG04 | NID-hosted India Report PDF opened; title/date/authorship visible. | Ingest as text/PDF source, IMG04. |
| FIT034 | needs_browser_recheck | IMG00 | NID Young Designers page did not fetch in automated pass. | Browser recheck; likely metadata/link-only. |
| FIT035 | ready_manual_text_authority | IMG04 | ICOD page opened and is suitable as authority/event source for Morteza Momayez. | Ingest as authority/event page. |
| FIT036 | search_path_only | IMG00 | PGDA collection page opened; still a collection/filter path, not a chosen exact item. | Select exact PGDA item or keep as collection-level context. |
| FIT037 | ready_manual_collection | IMG00 | SAHA Medu collection page opened; collection target is usable as link-only/community archive record. | Ingest collection metadata only. |
| FIT038 | needs_browser_recheck | IMG00 | SAHA exact item URL failed automated fetch. | Browser recheck or choose SAHA collection page if item remains inaccessible. |
| FIT039 | ready_manual_link_only | IMG00 | SA History archive page opened; use as poster/event hybrid but no image display by default. | Ingest metadata/link only. |
| FIT040 | ready_manual_text_event | IMG04 | SA History event article opened; event details and related archive links available. | Ingest as event page. |
| FIT041 | ready_manual_open_with_protocol | IMG03 | AIATSIS/NAIDOC page confirms 2020 Shape of Land title, creator, theme, and CC BY-NC-ND license text. | Ingest with license evidence, required credit, NC/ND restriction, and protocol note. |
| FIT042 | ready_manual_open_with_protocol | IMG03 | AIATSIS/NAIDOC page confirms 2021 Care for Country title, creator, theme, and CC BY-NC-ND license text. | Ingest with license evidence, required credit, NC/ND restriction, and protocol note. |
| FIT043 | ready_manual_open_with_protocol | IMG03 | AIATSIS/NAIDOC page confirms 2022 Stronger title, creator, theme, and CC BY-NC-ND license text. | Ingest with license evidence, required credit, NC/ND restriction, and protocol note. |
| FIT044 | ready_manual_collection | IMG04 | NYPL search result confirms Gran Fury collection page, collection scope, dates, location, and shelf locator. | Ingest collection-level record; no image frame. |
| FIT045 | ready_manual_link_only | IMG00 | NYPL search result confirms Silence = Death item; rights reviewed but inconclusive. | Update to canonical UUID URL in citation; keep IMG00. |
| FIT046 | ready_manual_link_only | IMG00 | NYPL search result confirms Kissing Doesn't Kill item; rights reviewed but inconclusive. | Update to canonical UUID URL in citation; keep IMG00. |
| FIT047 | ready_manual_text_standard | IMG04 | W3C CSS1 Recommendation page opened as stable standards document. | Ingest as standards/text page. |
| FIT048 | needs_browser_recheck | IMG00 | OoCities URL did not fetch in automated pass; remains useful as web-preservation target if accessible. | Browser recheck and Wayback capture lookup required. |

## Recommended Target Corrections

These are not yet applied to `data/first_ingest_record_targets.csv`; they should be reviewed as a small patch before the first ingest.

1. FIT026 should be replaced with the Seoul Museum of Art Archive record:
   - title: `1988년 《한국민중판화모음전》 포스터`
   - source: Seoul Museum of Art Archive
   - stable URL: `https://sema.seoul.go.kr/semaaa/front/archive/view.do?iId=21227`
   - source identifier: `MA-06-00004326`
   - production date: `1988.09.16`
   - image policy: `IMG00`, because the page warns against unauthorized reproduction/transmission/distribution.

2. FIT045 should preserve the current NYPL URL as an access URL but store the canonical UUID citation URL surfaced by NYPL:
   - `https://digitalcollections.nypl.org/items/d8e91040-c6b8-012f-9eea-58d385a7bc34`

3. FIT046 should preserve the current NYPL URL as an access URL but store the canonical UUID citation URL surfaced by NYPL:
   - `https://digitalcollections.nypl.org/items/c4788cb0-c6b8-012f-4439-58d385a7bc34`

4. FIT023 and FIT024 should not be promoted to source records until the exact Internet Archive page locators are verified visually.

5. FIT015, FIT016, FIT017, FIT019, and FIT036 should remain `search_path_only`.

## Immediate Ingest Subset

The safest first subset for manual source-record creation is:

- FIT003, FIT007, FIT008, FIT020, FIT021, FIT032, FIT033, FIT035, FIT040, FIT047
- FIT001, FIT005, FIT006, FIT009, FIT010, FIT011, FIT012, FIT013, FIT014, FIT022, FIT025, FIT029, FIT037, FIT039, FIT044, FIT045, FIT046
- FIT041, FIT042, FIT043 after adding protocol and NC/ND license notes

This gives enough diversity to test:

- authority pages;
- institutional pages;
- museum objects;
- source-only link records;
- periodical issue parent record;
- viewer-only image policy;
- open-but-restricted Creative Commons image policy;
- activist/community archive records;
- standards/web text records.

Machine-readable ready subset:

- `data/ready_manual_ingest_targets.csv`
- current generated count: 30

## Do Not Ingest Yet

Do not create source records yet for:

- FIT015
- FIT016
- FIT017
- FIT019
- FIT023
- FIT024
- FIT026 until replaced
- FIT027
- FIT028
- FIT030
- FIT031
- FIT034
- FIT036
- FIT038
- FIT048

These are not rejected. They need exact URLs, browser checks, page-level locators, or source replacement before ingest.
