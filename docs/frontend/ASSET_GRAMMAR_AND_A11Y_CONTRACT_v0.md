# Asset Grammar and Accessibility Contract v0

Date: 2026-06-03

This contract applies to every public archive asset: main sheet, subsheet,
appendix, text sheet, card, slip, bookmark, reading note, register, badge, and
folder drawer.

The project may use complex printed-object references, but no asset may become
less readable in order to look more archival.

## Minimum Legible Type

Required information must not fall below these sizes:

| Role | Minimum |
|---|---:|
| Body text | `0.72rem` |
| Metadata, table values, source/citation rows | `0.62rem` |
| Micro labels, stamps, field labels, state codes | `0.56rem` |

Type below `0.56rem` is allowed only when it is decorative: accession texture,
ornamental numbering, calibration marks, crop marks, or nonessential specimen
marks. Decorative text must be removed from the accessibility tree with
`aria-hidden="true"` or marked with `data-decorative="true"`.

## Line Length

Reading pages and about/methodology pages should keep readable prose between
55 and 75 characters per line. Cards, slips, and ledger cells should be shorter.

Rules:

- long prose blocks use a `max-width` in `ch`;
- tables use fixed columns and wrapping instead of long uninterrupted rows;
- URLs, source identifiers, and multilingual titles may wrap anywhere;
- if a layout needs smaller text to fit, the content must move to a subsheet,
  appendix, slip, or text page rather than shrinking below the minimum.

## Reading Order Contract

Visual order may be experimental, but DOM and keyboard order must remain stable:

```text
title
date / creator
source
image state
summary
metadata
citation / action
```

This is the archive grammar. A surface may omit fields that are not available,
but it must not reorder the evidence in a way that hides source, rights,
uncertainty, or the source-return action.

## Asset Grammar

Every asset is a reduction of the same evidence structure:

```text
asset =
  identity
  + source
  + rights / image state
  + classification
  + citation
  + uncertainty
  + action
```

Different families emphasize different parts:

| Asset | Primary job |
|---|---|
| Main sheet | Highest-confidence research surface; image, core facts, and source-return context |
| Subsheet | Secondary record or grouped member with enough evidence to read, but not enough to lead |
| Appendix | Evidence ledger: rights, citation, relations, protocol, source verification |
| Text sheet | Reading surface: source-derived/curated context plus explicit image evidence if available |
| Card | Compact visual/title record |
| Slip | Card-bound text or source supplement |
| Bookmark | Last-resort pointer or folder reading device |
| Reading note | Folder-level reading frame, not an object record |

## Image Accessibility

- IMG01/IMG02/IMG03 must render an `img` with nonempty `alt`.
- IMG00 must render an intentionally empty image field with text explaining
  that the image is withheld or source-linked.
- IMG04 must omit the image frame because the page is text-only.
- Wikimedia/aggregator images must identify the source chain; they are image
  supplements, not original holdings.

## Automated Check

Run:

```bash
npm run asset:a11y-check
```

The check verifies:

- visible required text below minimum sizes;
- horizontal page overflow;
- focusable links/buttons/summary elements;
- missing image alt text;
- empty image frames without explanatory text;
- basic contrast failures;
- desktop, mobile, and zoomed viewport states.

The report is written to `frontend/.asset-a11y-check/report.json` and is not a
publication artifact.

## Review Rule

If the automated check fails, the next step is to fix the asset or mark the
text as decorative. Do not lower the threshold to pass a visual draft.
