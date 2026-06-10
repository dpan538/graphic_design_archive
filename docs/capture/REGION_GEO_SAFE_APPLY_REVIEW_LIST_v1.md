# Region/Geography Safe Apply Review List v1

This audit is proposal-only. It does not modify source records, public surfaces, region labels, or geography labels.

## Summary

- scored suggestions: 1373
- ready for auto apply: 88
- priority manual review: 1057
- historical split review: 228

## Suggestion Types

- pending_text_resurface: 803
- direct_conflict_parse: 342
- historical_split: 228

## Confidence Levels

- medium: 1137
- low: 148
- high: 88

## Suggested Actions

- manual_only: 803
- split_by_date: 464
- apply_directly: 88
- manual_review: 18

## Manual Review Priority

- P1_medium_review: 673
- P1_date_sensitive_medium: 236
- P2_low_signal_review: 148

## Auto-Apply Labels

- Brazil: 30
- Mexico: 28
- Argentina: 17
- Egypt: 7
- Chile: 3
- Germany: 1
- South Africa: 1
- Turkey: 1

## Historical Split Labels

- Mexico; United States military occupation context: 220
- France; wartime occupation/state-context review: 4
- Russia / USSR contexts; republic-specific review: 3
- Germany; East/West Germany review: 1

## Top Labels by Suggestion Type

### direct_conflict_parse
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

### historical_split
- Mexico; United States military occupation context: 220
- France; wartime occupation/state-context review: 4
- Russia / USSR contexts; republic-specific review: 3
- Germany; East/West Germany review: 1

### pending_text_resurface
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

## Output Files

- `data/region_geo_ready_for_auto_apply_v1.csv`
- `data/region_geo_priority_manual_review_v1.csv`
- `data/region_geo_requires_historical_split_review_v1.csv`

## Interpretation

- `ready_for_auto_apply` is limited to high-confidence direct conflict parses with no historical dispute, no multi-country risk, and no sensitive label risk.
- `priority_manual_review` keeps pending text resurfacing and date-sensitive medium suggestions out of automatic application.
- `requires_historical_split_review` is separated because split labels need taxonomy support before they can be used in public statistics.
