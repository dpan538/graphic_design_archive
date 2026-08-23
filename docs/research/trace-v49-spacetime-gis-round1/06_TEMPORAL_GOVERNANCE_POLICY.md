# Temporal governance policy

## Governed role

The temporal role is `recorded_date_context`: the weakest release-supported statement about when a record is situated. It is not automatically an exact creation date or historical-event claim.

Policy version: `spacetime-temporal-governance-v1`.

## Observation model

Every public record retains:

- original source display text;
- inclusive start year;
- inclusive end year;
- precision: day, month, year, range, approximate, or unknown;
- derivation method `FROZEN_YEAR_EXTENT_AND_LEXICAL_PRECISION_V1`;
- an opaque observation ID.

Temporal source display is not rewritten into a stronger assertion. A range remains a range; qualified/circa/decade-like text remains approximate; exact month/day syntax remains at its observed precision.

## Corrected full-cohort census

All 7,995 public objects have a governed temporal observation: 7,552 year, 305 approximate, 78 day, 27 month, 33 range, and zero unknown. The governed extent begins in 1800 and ends in 2026.

This replaces the provisional 344 approximate / 66 day / 0 month handoff. The verifier protects the corrected distribution.

## Bucket policy

Bucket policy is `DECADE`. Twenty-three half-open periods cover `[1800,1810)` through `[2020,2030)`. Period IDs are stable `SPT-PERIOD-<start>-<end>` identifiers.

The default period is chosen deterministically as the period with the greatest record count, breaking a tie by the earlier start year. For the current release this is `SPT-PERIOD-1980-1990` with 1,898 unique public records.

## Range membership

Range policy is `INTERVAL_OVERLAP`. A record with inclusive temporal extent `[recordStart, recordEnd]` belongs to a half-open bucket `[bucketStart, bucketEnd)` when:

```text
recordStart < bucketEnd
and
recordEnd >= bucketStart
```

A range can therefore contribute to more than one decade. UI and API language says “records whose recorded temporal extent overlaps this period,” never “records created during this decade.”

Each period exposes a unique-record denominator plus mapped/unmapped counts and a precision breakdown. Geography assignment totals can exceed denominators when a multi-region record belongs to the period; that difference is explicit.

## Pure functions

Temporal semantics are implemented outside React through `governTemporalCandidate`, `deriveTemporalExtent`, `buildTimeBucketRegistry`, `deriveBucketMemberships`, `selectTimeBucket`, `filterRecordsByTimeBucket`, and `deriveTimeBucketCounts`. The renderer does not decide membership or precision.
