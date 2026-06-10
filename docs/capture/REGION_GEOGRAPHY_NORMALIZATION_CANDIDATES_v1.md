# Region / Geography Normalization Candidates v1

Scope: proposal-only per-surface candidate generation. This report does not rewrite surfaces, source records, or controlled taxonomy CSVs.

## Summary

- public surfaces scanned: 7836
- candidate rows generated: 7810
- unresolved rows with auto-map candidates: 586
- unresolved rows needing manual/sensitive review: 44
- unresolved rows with low-signal geography hints: 163
- unresolved rows remaining pending: 3900
- existing region-label conflicts: 344

## Candidate Actions

- keep_pending: 3900
- auto_map: 1390
- map_to_REG004_and_review_exact_child_need: 925
- auto_map_from_unresolved: 586
- review_existing_region_conflict: 344
- review_low_signal_geo_candidates: 163
- map_then_review_constituent_country_when_named: 118
- split_with_protocol_review: 95
- split_and_add_country_if_needed: 57
- map_then_review_1949_1990_records: 56
- split_by_record_evidence: 53
- route_by_date_and_territorial_scope: 26
- review_inferred_sensitive_mapping: 26
- split_with_historical_review: 25
- add_country_geography_then_map: 20
- review_multiple_geo_candidates: 18
- split_place_and_context: 8

## Candidate Status

- manual_review: 3900
- auto_existing_mapping_candidate: 1390
- taxonomy_mapping_candidate: 945
- auto_candidate: 586
- geography_conflict_review: 344
- split_review: 238
- low_signal_geo_review: 157
- review_candidate: 118
- sensitive_or_historical_review: 82
- territory_context_review: 20
- multi_match_review: 18
- historical_period_review: 6
- context_split_review: 3
- protocol_sensitive: 2
- historical_or_political_review: 1

## Current Labels in Candidate Set

- Unresolved region: 4693
- Latin America: 925
- United States: 576
- France: 317
- Brazil: 297
- Mexico: 241
- Italy: 145
- United Kingdom: 133
- Australia / Indigenous: 95
- Germany: 90
- India: 74
- South Africa / Botswana: 57
- China / Hong Kong: 53
- Japan: 35
- Russia: 26
- Palestine / transnational: 25
- Uruguay: 20
- Cuba / transnational: 8

## High-Signal Unresolved Samples

- SURF-SI1970R001 -> United States (high): Trade Card of John Williams, Clothier
- SURF-CHW2026R001 -> Austria (high): Die Thierwelt (The Animal Kinggom)
- SURF-CRG2026R0004 -> United Kingdom (high): The Town Hall, Market Place, Tamworth - geograph.org.uk - 1741283.jpg
- SURF-DNZ1970R001 -> Aotearoa New Zealand (high): Untitled Illustration (Otago Daily Times, 15 August 1867)
- SURF-CRG2026R0048 -> Canada (high): Rossin House promotional pamphlet.jpg
- SURF-COM1970R001 -> Canada (high): Ontario Immigration Poster.jpg
- SURF-DNZ1970R002-GROUP -> Aotearoa New Zealand (high): Untitled Illustration (Otago Witness, 13 December 1879) grouped records, 1879
- SURF-DNZ1970R009-GROUP -> Aotearoa New Zealand (high): Untitled Illustration (Otago Witness, 20 December 1879) grouped records, 1879
- SURF-DNZ1970R012 -> Aotearoa New Zealand (high): Untitled Illustration (Otago Witness, 27 December 1879)
- SURF-DNZ1970R013 -> Aotearoa New Zealand (high): Untitled Illustration (Otago Witness, 03 January 1880)
- SURF-DNZ1970R014 -> Aotearoa New Zealand (high): Untitled Illustration (Otago Witness, 24 July 1880)
- SURF-CRG2026R0081 -> Italy (high): Invidia film poster by Carlo Nicco 1919.jpg

## Existing Region Conflicts

- United States: 267
- Germany: 34
- France: 17
- United Kingdom: 15
- Brazil: 4
- Japan: 4
- Italy: 3

Sample conflicts:

- SURF-CGS2026R0908: France -> evidence suggests Mexico · Temple of Xochicalco, Exposition Universelle Paris 1867, from Illustrated London News, 01. Juni 1867
- SURF-CGS2026R0912: United States -> evidence suggests Mexico · The American Flag. (Matamoros, Tamaulipas, Mexico), Vol. 1, No. 10, Ed. 1 Tuesday, July 7, 1846 - DP
- SURF-CGS2026R0913: United States -> evidence suggests Mexico · The American Flag. (Matamoros, Tamaulipas, Mexico), Vol. 1, No. 10, Ed. 1 Tuesday, July 7, 1846 - DP
- SURF-CGS2026R0914: United States -> evidence suggests Mexico · The American Flag. (Matamoros, Tamaulipas, Mexico), Vol. 1, No. 14, Ed. 1 Sunday, July 19, 1846 - DP
- SURF-CGS2026R0915: United States -> evidence suggests Mexico · The American Flag. (Matamoros, Tamaulipas, Mexico), Vol. 1, No. 14, Ed. 1 Sunday, July 19, 1846 - DP
- SURF-CGS2026R0916: United States -> evidence suggests Mexico · The American Flag. (Matamoros, Tamaulipas, Mexico), Vol. 1, No. 15, Ed. 1 Tuesday, July 21, 1846 - D
- SURF-CGS2026R0917: United States -> evidence suggests Mexico · The American Flag. (Matamoros, Tamaulipas, Mexico), Vol. 1, No. 16, Ed. 1 Friday, July 24, 1846 - DP
- SURF-CGS2026R0918: United States -> evidence suggests Mexico · The American Flag. (Matamoros, Tamaulipas, Mexico), Vol. 1, No. 17, Ed. 1 Monday, July 27, 1846 - DP
- SURF-CGS2026R0919: United States -> evidence suggests Mexico · The American Flag. (Matamoros, Tamaulipas, Mexico), Vol. 1, No. 18, Ed. 1 Friday, July 31, 1846 - DP
- SURF-CGS2026R0920: United States -> evidence suggests Mexico · The American Flag. (Matamoros, Tamaulipas, Mexico), Vol. 1, No. 19, Ed. 1 Monday, August 3, 1846 - D
- SURF-CGS2026R0921: United States -> evidence suggests Mexico · The American Flag. (Matamoros, Tamaulipas, Mexico), Vol. 1, No. 19, Ed. 1 Monday, August 3, 1846 - D
- SURF-CGS2026R0922: United States -> evidence suggests Mexico · The American Flag. (Matamoros, Tamaulipas, Mexico), Vol. 1, No. 19, Ed. 1 Monday, August 3, 1846 - D

## Interpretation

- A large part of `Unresolved region` can be triaged before any new capture because many records already carry country/place evidence in source metadata.
- Candidate rows with `auto_map_from_unresolved` should still be sampled before application, but they are the safest first cleanup batch.
- `review_existing_region_conflict` rows show current public folder labels that disagree with high-signal geography fields and should block automated application.
- Slash labels remain review queues. They should be split from record evidence, not replaced by one preferred string.
- `Uruguay` is the clearest controlled-geography addition: the public folder is explicit, but no controlled geography row exists yet.
- True source-gap capture should follow this cleanup, especially for Southeast Asia, MENA beyond Palestine, Africa beyond Southern Africa, and Pacific/Aotearoa contexts.

## Generated Files

- `data/region_geography_normalization_candidates_v1.csv`
- `data/region_geography_normalization_candidate_summary_v1.csv`
- `docs/capture/REGION_GEOGRAPHY_NORMALIZATION_CANDIDATES_v1.md`
