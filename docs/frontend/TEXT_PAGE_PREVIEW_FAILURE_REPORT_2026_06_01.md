# Text Page Preview Failure Report

Date: 2026-06-01

## Summary

The text page design review entered a failure loop because layout work,
preview generation, screenshot capture, and verification were not treated as
one controlled process. The result was repeated user-visible screenshots that
did not reliably reflect the latest layout changes.

## What Failed

- The review repeatedly relied on temporary screenshot files with reused names.
- Static HTML extraction was attempted with fragile section slicing, causing
  incomplete group previews.
- Quick Look rendering was used as an ad hoc fallback and produced unreliable
  visual evidence for full layout review.
- Browser-based capture was attempted only after design revisions had already
  accumulated, instead of being established before visual judgment.
- Screenshot failure was mixed with design iteration, which made it unclear
  whether the layout or the capture method was at fault.
- The assistant reported visual completion before a fresh, canonical capture
  had been generated and inspected.

## User-Visible Impact

- The user saw repeated screenshots that were cropped, stale, incomplete, or
  visually inconsistent with the stated changes.
- Text page design review consumed multiple hours without a trustworthy visual
  checkpoint.
- The user could not distinguish design quality problems from capture-path
  failures.
- Confidence in later layout claims was reduced.

## Root Causes

- No fixed asset-preview entrypoint for grouped layout review.
- No manifest-driven screenshot process.
- No automated overflow, image-load, or ratio checks before reporting.
- Too much reliance on manual visual checking and temporary files.
- Failure to stop layout work when the capture path became unstable.

## Corrective Action

The project now has a fixed capture workflow for text pages:

```bash
npm run preview:text-pages
npm run capture:text-pages
```

The capture script:

- opens the isolated preview URL at `127.0.0.1:3037/text-pages`;
- captures the full page;
- captures each text-page group by selector;
- writes a timestamped run directory;
- writes a manifest;
- fails on missing groups, empty groups, overflow, broken images, or incorrect
  page ratios.

## New Constraint

Future asset work must not proceed beyond implementation into user-facing
review until the canonical capture loop has generated fresh screenshots and a
passing manifest.

This failure report is linked to
`docs/frontend/ASSET_PREVIEW_CAPTURE_CONSTRAINTS.md`.

