# Development Failures and Constraints

Date: 2026-06-01

This report records development failures, near misses, and hard constraints
that emerged during source expansion, raw-payload capture, frontend/data
coordination, and GitHub publication. It is part of the project methodology:
failures are treated as evidence for improving the archive workflow rather
than as incidental implementation noise.

## 1. GitHub Secret Scanning Alert

Issue:

- GitHub reported a possible valid Google API key in a committed raw HTML
  payload from a source probe.
- The exposed string came from third-party page content, not from a project
  credential. It appeared inside a raw captured HTML file, which was then
  pushed to GitHub.
- The affected commit was rewritten and force-pushed after redaction.

Resolution:

- Added shared secret-redaction patterns to source-probe and capture scripts.
- Added `scripts/audit_secret_patterns.py`.
- Redacted the affected raw files and amended the pushed commit.
- Verified the repository with `scripts/audit_secret_patterns.py` before the
  replacement push.

Constraint:

- Every script that writes raw HTML, JSON, XML, or text payloads must redact
  common API-key/token patterns before writing to disk.
- `scripts/audit_secret_patterns.py` must pass before any commit that includes
  raw source payloads.
- Do not assume that third-party HTML is safe merely because it is public.
- Avoid printing suspected secret strings in terminal summaries, reports, or
  final messages.

## 2. Raw Payload Trial Pollution

Issue:

- A capture script was run multiple times while its filters were still being
  tightened.
- Earlier trial runs wrote broad `pages` and `blocks` WordPress payloads into
  the raw evidence directory.
- Although the final records were filtered, the stale raw files remained and
  would have made the evidence folder look broader and noisier than the actual
  published batch.

Resolution:

- Added a raw-directory cleanup step to the batch script before capture.
- Restaged only the final clean raw evidence set.

Constraint:

- Batch scripts that write to a batch-specific raw directory should clear that
  directory at the start of a run, unless the batch is explicitly append-only.
- Raw payload directories must correspond to the final generated records or to
  explicitly documented failed attempts.
- Trial payloads should not be committed as evidence.

## 3. Over-Broad WordPress Capture

Issue:

- A generic WordPress capture pass initially included site pages such as terms
  of use, advisory board pages, and administrative announcements.
- These records had text and sometimes images, but they were not archive
  records, design objects, source-context records, or useful research
  evidence.

Resolution:

- Restricted capture to content-oriented REST bases such as `posts`, `item`,
  `product`, `projects`, `work`, and `archive`.
- Added exclusions for terms/privacy pages, tender/application notices,
  reopening notices, job/vacancy pages, and other administrative content.
- Added relevance filtering around poster, graphic design, typography,
  publication, print, visual culture, archive, exhibition, identity, packaging,
  cinema, publicity, advertising, and related terms.

Constraint:

- A reachable source is not automatically a valid archive source.
- A source record must pass a relevance gate before entering a capture batch.
- Institutional pages may be retained as source-registry evidence, but should
  not become main sheets unless they document a historically relevant design
  object, event, movement, method, institution, or archive context.

## 4. Thin Sheet Inflation

Issue:

- Earlier batches promoted too many sparse records into main sheet surfaces.
- This made the public archive feel like a sign-in ledger or metadata table
  rather than a research interface.

Constraint:

- Main sheets should require a higher completeness threshold than early
  prototypes allowed.
- Sparse records should be routed toward cards, slips, appendices, bookmarks,
  grouped source records, or text pages before becoming main sheets.
- Image presence alone is not enough for a main sheet; source text, citation,
  rights evidence, and classification confidence also matter.

## 5. Appendix Repetition and Placeholder Risk

Issue:

- Appendix surfaces were introduced, but early generation behavior could
  repeat similar AX01 pages and use placeholder-like content that was not
  tightly connected to the actual record.

Constraint:

- Appendices must be generated from real record payloads, citations, rights
  evidence, source lists, relations, or classification rationale.
- Consecutive identical appendix types should be avoided unless each appendix
  has clearly different evidence.
- AX01 is not limited to `IMG00`; it can support `IMG01`, `IMG02`, and `IMG03`
  rights evidence where rights decisions require explanation.

## 6. Image Coverage Metrics

Issue:

- Earlier image coverage metrics combined source-hosted, open, restricted, and
  placeholder states too loosely.
- This made coverage appear healthier than the actual publication experience.

Constraint:

- Report image coverage by period and by image state, not only as one global
  percentage.
- Separate source-visible coverage from publication-grade coverage.
- Treat `IMG02` as useful visual access but not as open-image proof.
- Track repeated image URLs and placeholder images as quality failures.

## 7. Collaboration and Staging Boundaries

Issue:

- Multiple windows were editing frontend assets, reading-note components, and
  data scripts simultaneously.

Constraint:

- Data/capture work must stage only files owned by the current task.
- Do not stage frontend design files from another window unless explicitly
  asked.
- Rebuilds that write frontend static payloads should be coordinated when
  another window is replacing visual assets.

## 8. Required Pre-Commit Checks for Capture Work

Minimum checks before committing capture/source-probe work:

- Run `scripts/audit_secret_patterns.py`.
- Check staged file list manually.
- Check source-record URL duplicates inside the new batch.
- Check image URL duplicates inside the new batch.
- Confirm raw evidence directory matches the final batch run.
- Confirm the capture report states that the batch is not automatically final
  publication data unless that is explicitly true.

## 9. Methodological Consequence

These failures reinforce the archive's central rule:

The project is an index and research framework, not a bulk mirror. Capture is
only the first step. Every record must still pass through rights review,
source evaluation, relevance filtering, grouping, surface-type assignment, and
publication-quality checks before it becomes part of the public archive.
