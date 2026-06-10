# Region / Geography Auto Candidate QA Sample v1

Scope: stratified review sample for proposal-only region/geography normalization candidates. This report does not apply any candidate.

## Summary

- candidate rows read: 7810
- QA sample rows: 205
- auto-map candidates available: 586
- low-signal candidates available: 163

## Sample Types

- auto_map_stratified: 125
- low_signal_review: 40
- sensitive_or_multi_review: 40

## Largest Auto Targets

- Aotearoa New Zealand: 173
- United States: 111
- Iran: 71
- United Kingdom: 46
- Turkey: 42
- Egypt: 32
- Germany: 20
- Canada: 16
- Australia: 12
- Nigeria: 12
- Ghana: 11
- Japan: 10
- Italy: 9
- Netherlands: 4
- Switzerland: 3
- Austria: 2
- Russia / USSR contexts: 2
- Mainland China: 2
- France: 2
- Poland: 2

## Review Rule

- If the stratified sample shows low false-positive risk, the next script may generate a dry-run normalized payload for `auto_map_from_unresolved` only.
- If false positives cluster by source family, add source-family guards before any application script.
- Low-signal and sensitive/multi-review samples must not be applied automatically.

## Generated File

- `data/region_geography_normalization_auto_review_sample_v1.csv`
