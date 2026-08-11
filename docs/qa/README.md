# QA screenshot evidence governance

`screenshots/` contains 60 tracked legacy QA files. Phase 1D preserves their
paths and bytes; it does not promote them into a complete release receipt or
claim that every image is safe for republication. The current directory must
therefore be read as historical visual evidence with known metadata and
coverage gaps.

`SCREENSHOT_MANIFEST.schema.json` is the governance contract for future
capture receipts. A conforming manifest must:

- pin the research release ID and research manifest SHA-256;
- pin the visual-registry version and SHA-256 as one atomic pair, or record the
  pair as absent;
- record path, byte size, SHA-256, filename extension, actual signature MIME,
  width, and height for every image;
- keep rights provenance and external-pixel disposition separate from endpoint
  availability or successful capture;
- link every assertion to a versioned test oracle and record observed versus
  expected behavior;
- report interaction and accessibility coverage explicitly, including
  keyboard, screen reader, reduced motion, touch, swipe, scroll, source drawer,
  Search, map, and error-state coverage;
- use `NOT_EVALUATED` for missing evidence rather than silently implying PASS.

The schema deliberately distinguishes `fileExtension` from `actualMimeType`.
The legacy set includes files whose `.png` suffix does not match their JPEG
signature. This skeleton does not rename or re-encode those files.

Third-party pixels must not be added merely because a URL is reachable, an
IIIF service exists, or a browser can capture it. A future manifest must record
rights provenance and the effective delivery decision; unresolved or held
pixels are not eligible for new Git QA evidence.

Phase 1D baseline:

- tracked screenshot files: **60**;
- pre/post path-plus-content fingerprint:
  `287289be2f58cae02f8746290c37ebec8880cd1bf461f112a64733b1cb499220`;
- existing screenshots renamed, deleted, or re-encoded: **0**.
