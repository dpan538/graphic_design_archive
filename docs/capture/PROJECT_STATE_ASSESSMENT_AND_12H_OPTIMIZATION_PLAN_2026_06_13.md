# Project State Assessment and 12h Optimization Plan - 2026-06-13

## Scope

This document records the post-capture project state after the Commons open-source
cleaning round and sets expectations for the next long optimization pass.

The archive is now in a late-stage database and release-engineering phase. The
main problem is no longer simple source discovery. The main problems are source
authority, rights-state conversion, region/geography normalization, public
surface payload size, and research-packet structure.

This assessment is a planning and release-risk record. It does not change rights
states, download images, rewrite taxonomy, or rebuild public surfaces by itself.

## Current Baseline

- Public surfaces: 13,680.
- Archive-active public sources: 12,342.
- Capture records: 15,121.
- Active public-source gap to the 20,000 launch target: about 7,658.
- Capture-record gap to 20,000 records: about 4,879.

The release-facing source count should continue to use archive-active public
sources rather than raw capture records. A captured source is not successful
until it is cleaned, incorporated into surfaces, and visible in the archive
payload.

## Release Gate Position

Current public-surface release snapshot:

- Object source-visible rate: 97.91%.
- Object verified-open rate: 87.96%.
- Object weighted publication-grade rate: 93.36%.
- Object IMG04 rate: 1.78%.
- Source-visible object gap to the new 99% target: about 150 object-equivalent
  records.
- Verified-open object gap to the 95% target: about 963 object-equivalent
  records.
- Weighted publication-grade gap to the 95% target: about 225 weighted points.

Interpretation:

- IMG04 is currently controlled and should remain below 10%.
- Source-visible coverage is close to the stricter 99% target.
- Verified-open is the largest gate gap.
- Weighted publication is near target, but the remaining gap is concentrated in
  high-authority non-Commons source families.

## Source Coverage and Distribution

Current source-coverage diagnostics:

- Source pool period fill rate: 100.00%.
- Strict distribution-adjusted source coverage rate: 28.96%.
- Period surface balance rate: 100.00%.
- Period quality-main balance rate: 44.23%.
- Region surface balance rate: 6.71%.
- Region quality-main balance rate: 6.47%.
- Research quality adjusted source coverage rate v2: 2.80%.

Interpretation:

- Time-period volume is sufficient at the surface-count layer.
- Region normalization and quality-main distribution are still severe release
  risks.
- The unresolved-region cluster is too large and directly suppresses regional
  coverage diagnostics.
- Additional capture without region cleanup will increase the database size but
  may not improve release coverage.

## Period Structure

Period surface counts and quality-main counts:

- pre-1930: 2,406 surfaces; 871 quality main sheets.
- 1930-1970: 3,684 surfaces; 1,118 quality main sheets.
- 1970-2000: 3,283 surfaces; 966 quality main sheets.
- 2000-2026: 3,559 surfaces; 673 quality main sheets.
- undated/unparsed: 748 surfaces; 20 quality main sheets.

Interpretation:

- 2000-2026 is not simply underfilled by count. It is underfilled by quality
  main-sheet material.
- Contemporary design needs more studio, art-school, community, platform, and
  institution-backed records rather than more broad single-file evidence.
- Undated records remain a quality and trust problem; they need date repair
  before being treated as strong research anchors.

## Sheet and Research Packet Structure

Current sheet topology:

- Main sheets: 13,419.
- Sub/support surfaces: 261.
- Independent text-sheet surfaces: 242.
- Single-anchor dossiers: 13,409.
- Compound/group dossiers: 271.
- Dossiers with two or more text pages: 0.
- Average dossier pages: 2.25.
- Strong group candidates: 351.

Interpretation:

- The archive has scale, but most records still behave as single-source main
  sheets.
- The desired research-packet model is not yet structurally mature.
- Text exists mostly as generated dossier text_page entries, not as enough
  independent editorial text sheets.
- The 351 strong group candidates are the first practical target for converting
  isolated main sheets into main/sub/card/appendix research packets.

## Highest Rights and Weighted-Publication Gaps

The most valuable source families for gate repair are:

- V&A Collections API.
- Cooper Hewitt Collection GraphQL API.
- Library of Congress loc.gov API.
- Art Institute of Chicago API.
- Georgia State University Library Digital Collections / CONTENTdm.
- Wellcome Collection Catalogue API.
- Internet Archive text and periodical collections.
- Te Papa Collections Online.
- NAIDOC Poster Gallery.
- DigitalNZ.
- Princeton University Library Digital Collections / Figgy.
- The Met Open Access.

These sources already have stronger authority than broad Commons expansion.
They should be audited for verified-open conversion, source-visible repair, or
replacement by explicit open records before another broad source-count push.

## Infrastructure Risk

The generated public-surface JSON payloads are already very large, around the
normal GitHub 100MB blob safety threshold. Rebuilding and committing monolithic
payload copies during every source-capture round is not sustainable.

The next optimization pass should prioritize sharded or indexed public-surface
exports before attempting another full source incorporation cycle.

## 12h Optimization Plan

The next long pass should proceed in this order:

1. Surface payload sharding and build safety.
   - Add a sharded export path or manifest around the public-surface payload.
   - Keep the existing payload contract available until the frontend loader is
     migrated.
   - Avoid committing newly rebuilt monolithic payloads as the primary artifact.

2. Release gate clarification.
   - Treat archive-active public sources as the release source-count metric.
   - Keep raw capture records as a diagnostic, not as launch source success.
   - Record the 20,000 source target against active public sources.

3. Rights-state and weighted-publication repair.
   - Audit top gap sources for IMG02-to-IMG03 or IMG04-to-source-visible repair.
   - Do not auto-upgrade IMG01/IMG03 from heuristic, platform, TOS, or LLM
     signals.
   - Only upgrade where source terms, open metadata, or authoritative collection
     evidence supports it.

4. Region/geography normalization.
   - Reduce unresolved region and global fallback records.
   - Apply only high-confidence normalization rows automatically.
   - Keep historical/date-sensitive records in manual review queues.

5. Research-packet structure.
   - Use the strong group candidate queue to create or plan main/sub/card/text
     packet conversions.
   - Do not downgrade main sheets by word count alone.
   - Treat impact, source depth, relation density, period span, rights state,
     region scarcity, and editorial need as the packet-structure factors.

6. Source-specific capture.
   - After the cleanup pass, add institutional source adapters rather than more
     broad Commons sweeps.
   - Prioritize art schools, community archives, national libraries, open
     collections, design repositories, and under-covered small countries.
   - Use cleaning gates before counting any new source as successful.

## Expected Outputs

Expected outputs from the long pass:

- A sharding or payload-size mitigation script/report.
- Updated release-gate documentation or metrics that distinguish raw capture
  count from active public source count.
- A rights/weighted-publication repair report for the top gap source families.
- A region/geography cleanup report focused on unresolved/global-fallback
  reduction.
- A first packet-structure action plan for strong grouping candidates.
- Re-run metrics for source coverage, layered image/source state, release gate,
  sheet topology, and source success.

## Explicit Non-Goals

- Do not edit, stage, commit, or push `research-repo/`.
- Do not stage unrelated frontend files or old raw capture files.
- Do not download image binaries.
- Do not treat Commons platform presence alone as verified-open authority beyond
  existing Commons open-license metadata rules.
- Do not claim 5,000 or 20,000 successful sources until the sources are cleaned,
  incorporated into public surfaces, and counted by the active public-source
  metric.
