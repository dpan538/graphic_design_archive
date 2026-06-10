# Region / Geography Enrichment Audit v1

Scope: local, proposal-only enrichment over region/geography normalization candidates. No source records, public surfaces, controlled taxonomy CSVs, or frontend files are rewritten.

## Summary

- direct_conflict_parse_suggestions: 342 (Controlled-geography matches from high-signal conflict evidence.)
- historical_split_suggestions: 228 (Date/term based historical split suggestions for conflict rows.)
- pending_text_suggestions: 803 (Rule-based suggestions from pending or low-signal rows.)
- unique_surfaces_with_enrichment_suggestions: 1147 (Unique surface IDs suggested by any local enrichment pass.)
- original_conflict_review_rows: 344 (Rows in candidate table with geography_conflict_review.)
- original_pending_rows: 3900 (Rows in candidate table with keep_pending.)
- original_low_signal_rows: 163 (Rows in candidate table with review_low_signal_geo_candidates.)

## Direct Conflict Parse Targets

- Mexico: 248
- Brazil: 39
- Argentina: 19
- Egypt: 7
- Aotearoa New Zealand: 6
- Palestinian territories and diaspora: 5
- Mainland China: 3
- Chile: 3
- United Kingdom: 2
- Germany: 2
- France: 2
- United States: 1
- Japan: 1
- India: 1
- Russia / USSR contexts: 1
- Turkey: 1
- South Africa: 1

## Pending / Low-Signal Text Targets

- Indonesia: 381
- Caucasus: 64
- Azerbaijan: 39
- Georgia: 38
- Singapore: 31
- United States: 28
- Bangladesh: 22
- United Kingdom: 19
- Philippines: 19
- Vietnam: 18
- Romania: 15
- Thailand: 15
- Aotearoa New Zealand: 11
- Pakistan: 9
- Ireland: 8
- Nepal: 8
- France: 8
- Ukraine: 8
- Portugal: 5
- Spain: 5
- South Korea: 5
- Canada: 5
- Armenia: 4
- Myanmar: 4
- Germany: 3

## Interpretation

- The 3,900 pending rows should not be accepted as final; local enrichment can surface additional review candidates without changing archive data.
- Direct conflict parse suggestions are stronger than low-signal text suggestions because they rely on high-signal candidate evidence.
- Historical split suggestions should remain review-only until controlled historical geography rows and display rules are confirmed.
- Pending text suggestions are useful for prioritizing manual review and source-family repairs, not for automatic application.
- A Wikidata or external lookup pass can be added later, but should use caching, rate limits, and a dry-run-only output contract.

## Generated Files

- `data/region_conflict_direct_parse_v1.csv`
- `data/region_conflict_historical_split_suggestions_v1.csv`
- `data/region_pending_geo_text_suggestions_v1.csv`
- `data/region_geo_enrichment_audit_summary_v1.csv`
