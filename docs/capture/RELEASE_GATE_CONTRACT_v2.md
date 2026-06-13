# Release Gate Contract v2

Scope: launch-facing release gates for the rights-aware modern graphic design
archive index after the June 2026 target update.

## Hard Gates

- Public active source target: 20,000.
- Minimum public source coverage: 80% of the 20,000 target.
- Object source-visible rate: at least 99%.
- Object verified-open rate: at least 95%.
- Object weighted publication-grade image rate: at least 95%.
- Object IMG04 rate: at most 10%.
- Future-date errors: 0 surfaces dated after 2026.

## Source Count Semantics

`archive_active_public_sources` is the launch-facing source count. It is counted
from the generated public payload after rebuild, using distinct public
`sourceName` values. A captured row that has not become part of the generated
public payload is not a successful release source.

`capture_distinct_source_count` and source-coverage v1/v2 capacity metrics are
diagnostic signals. They are useful for planning and crawler health, but they do
not replace `archive_active_public_sources` for launch readiness.

Pre-surface registries, source-prospect registries, and discovery-only candidate
lists do not count as active release sources until item-level source evidence is
captured, cleaned, included in the public payload, and passes the relevant image
and rights gates.

## Object Image Semantics

Object-level image metrics collapse repeated views, repeated photos, or multiple
surfaces for one source object into one gate unit. This prevents recent projects
or richly photographed works from inflating publication-grade image coverage.

Image weights remain conservative:

- IMG03: 1.0
- IMG02: 0.55
- IMG01: 0.3
- IMG00: 0.0
- IMG04: 0.0

IMG04 remains a real no-image/text/authority state, not a parser-failure state.
It is allowed when the source is genuinely text-first, but it is now bounded by
the object IMG04 gate because the archive is image-based.

## Coverage Diagnostics

`source_pool_period_fill_rate` measures capture/source capacity against the
20,000-source target and period distribution. It can differ from
`archive_active_public_sources` because it is based on capture records.

`strict_distribution_adjusted_source_coverage_rate` is a warning signal for
regional imbalance.

`research_quality_adjusted_source_coverage_rate_v2` is the strictest structural
diagnostic. It combines source capacity, period quality-main balance, region
quality-main balance, and source-visible surfaces. A low value means the archive
may have many records but still lacks a balanced research structure.

## Current Baseline After Retargeting

- Public surfaces: 13,680.
- Archive active public sources: 12,342 / 20,000 = 61.71%.
- Capture distinct source count: 13,560.
- Source pool period fill rate: 51.45%.
- Strict distribution-adjusted source coverage: 15.62%.
- Research-quality adjusted source coverage v2: 1.44%.
- Object source-visible: 97.91%.
- Object verified-open: 87.96%.
- Object weighted publication-grade image rate: 93.36%.
- Object IMG04: 1.78%.

## Immediate Implications

- The archive has scale, but it is not launch-ready under the updated gate.
- The next capture round should add public-payload-ready sources, not only
  discovery rows or pre-surface registry entries.
- Rights repair is now as important as source growth: IMG02 and IMG01 rows from
  reliable institutions are the fastest path toward the 95% verified-open and
  weighted-publication targets.
- Regional normalization and research-packet grouping remain release risks
  because they directly depress strict distribution and research-quality
  adjusted coverage.
