# Image Coverage Metrics Recalibration

Date: 2026-06-01

Purpose:

- Correct the earlier over-optimistic image coverage reading.
- Separate source visibility from publication-grade image coverage.
- Prevent `IMG02` source-hosted/viewer records from being counted as equal to
  open or fully reviewed display images.

## Metric Layers

The archive now reports three different image metrics:

1. Source-visible coverage
   - Counts `IMG01`, `IMG02`, and `IMG03`.
   - Meaning: the user can see or reach image evidence through the archive
     interface or source viewer.
   - This is not enough for the launch-quality image target.

2. Verified open coverage
   - Counts `IMG03` where `rightsReviewed` is true.
   - Meaning: source metadata supports an open/public-domain candidate display.
   - This is the strictest current metric.

3. Weighted publication coverage
   - `IMG03`: 1.00
   - `IMG02`: 0.65
   - `IMG01`: 0.45
   - `IMG00`: 0.00
   - `IMG04`: 0.00
   - Meaning: a more honest launch-readiness score that recognizes `IMG02`
     as useful but incomplete.

## Current Result

From `scripts/audit_image_release_gate.py`:

- Public surfaces: 1095
- Source-visible image-ready: 1002
- Source-visible coverage: 91.51%
- Verified open images: 394
- Verified open coverage: 35.98%
- Weighted publication image score: 781.8
- Weighted publication coverage: 71.4%
- Weighted/publication-grade launch gate: 95%
- Weighted publication points needed: 258.45

## Interpretation

The previous `92%` claim was only source-visible coverage. It should not be
described as true design-archive image coverage.

The actual launch-quality condition is much lower because most late-period and
institutional records are `IMG02`: source-hosted, source-return display records
with rights still governed by the holding institution.

This is acceptable as an ethical display policy, but it is not equivalent to a
fully reviewed open image record.

## Main Gaps

Blocking `IMG00`/`IMG04` sources:

- Art Institute of Chicago API
- V&A Collections API
- The Met Open Access
- Library of Congress loc.gov API
- Getty Research Portal
- Wellcome Collection Catalogue API
- NAIDOC / AIATSIS
- Chinese Posters
- Te Papa Collections Online

Large unverified visible `IMG02` sources:

- Cooper Hewitt Collection GraphQL API
- Georgia State University Library Digital Collections / CONTENTdm
- Wellcome Collection Catalogue API
- Internet Archive / text and periodical collections
- Te Papa Collections Online
- NAIDOC Poster Gallery
- Princeton University Library Digital Collections / Figgy

## Next Rule

- Continue full coverage capture by source territory and category map.
- Do not inflate image coverage by adding weak `IMG02` records alone.
- Promote records from `IMG02` to `IMG03` only when source rights evidence is
  explicit enough.
- Keep `IMG02` as a valid ethical display state, but report it separately from
  publication-grade coverage.
