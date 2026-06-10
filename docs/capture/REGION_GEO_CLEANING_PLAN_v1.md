# Region/Geography Cleaning Plan v1

This plan is dry-run only. It prepares review and application queues without mutating archive data.

## Batch Action Queue

- action rows: 88
- ready_for_batch_apply_after_sample_audit: 64
- spot_check_before_apply: 24

### Auto-Candidate Labels

- Brazil: 30
- Mexico: 28
- Argentina: 17
- Egypt: 7
- Chile: 3
- Germany: 1
- South Africa: 1
- Turkey: 1

## Manual Review Compression

- compressed clusters: 64
- P1_medium_review: 673
- P1_date_sensitive_medium: 236
- P2_low_signal_review: 148

### Largest Manual Labels

- Indonesia: 381
- Mexico: 220
- Caucasus: 64
- Azerbaijan: 39
- Georgia: 38
- Singapore: 31
- United States: 29
- Bangladesh: 22
- United Kingdom: 21
- Philippines: 19
- Vietnam: 18
- Aotearoa New Zealand: 17
- Romania: 15
- Thailand: 15
- France: 10

## Historical Split Queue

- historical split rows: 228
- Mexico; United States military occupation context: 220
- France; wartime occupation/state-context review: 4
- Russia / USSR contexts; republic-specific review: 3
- Germany; East/West Germany review: 1

## Recommended Next Cleaning Order

1. Spot-check the 88 action rows by label/source family before applying any mapping.
2. Review the 220 Mexico / United States military occupation rows as a historical-context policy decision, not a simple country relabel.
3. Audit the large pending-text clusters for Indonesia, Caucasus, Azerbaijan, Georgia, and Singapore to separate source geography from topic geography.
4. Convert confirmed cluster rules into a second, narrower auto-map pass only after review evidence is consistent.

## Output Files

- `data/region_geo_cleaning_action_plan_v1.csv`
- `data/region_geo_manual_review_clusters_v1.csv`
