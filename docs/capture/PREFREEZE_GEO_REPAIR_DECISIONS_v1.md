# Prefreeze Geography Repair Decisions v1

Scope: deterministic geography repair for candidate promotion review. This does not edit raw capture data and does not overwrite the official public payload.

## Summary

- queue_rows: 218
- override_rows: 4808
- decision:insufficient_evidence: 130
- decision:auto_apply_candidate: 83
- decision:keep_global_context: 4
- decision:auto_specific_uncontrolled_candidate: 1
- confidence:low: 130
- confidence:medium: 73
- confidence:high: 15

## Largest Suggested Labels

- United States: 64
- Global / transnational: 7
- United Kingdom: 4
- Czech and Slovak contexts: 3
- Middle East and North Africa: 3
- Canada: 3
- Belgium: 1
- Puerto Rico: 1
- Germany: 1
- Russia / USSR contexts: 1

## Guardrails

- Geography repair is source/folder normalization only.
- No image files were downloaded.
- IMG01/IMG03 rights states were not upgraded.
- Specific labels missing from geographies.csv are marked as uncontrolled candidates and retain macro region references.
