# Current TRACE Runtime Baseline

Source branch `feat/v49-fuzzy-search-round1-20260823` was verified at `f9bdfdd293023592ddc6af92858a24857c5a532a`. The default repository mode is the sealed derived-v49 provider.

## Browser baseline before implementation

The current application was run locally at `http://127.0.0.1:3047` before changes. `/trace` rendered:

```text
This public release has no verified TRACE evidence.
Verified TRACE objects: 0
```

The page title was `TRACE evidence atlas — Modern Graphic Design History`; no browser console warnings or errors were observed. The new foundation was not connected to this route.

## API baseline

| Request | HTTP | Current response state |
|---|---:|---|
| `/api/v1/releases/current/trace/atlas` | 200 | `totalExact=0`; explicit zero-evidence message |
| `/api/v1/releases/current/trace/objects?layer=active&first=50` | 200 | empty nodes; total 0; no next cursor |
| `/api/v1/releases/current/trace/relation-types` | 200 | empty array |
| representative object neighborhood | 404 | release has no TRACE-eligible object |
| representative relation-type detail | 404 | not published in this release |
| representative relation detail | 404 | not published in this release |
| representative claim detail | 404 | not published in this release |

Successful responses carry the current release pair. Not-found responses use the release-bound Problem Details schema. This matches the intended fail-closed historical contract.

## Contract defect observed, not changed

The derived repository ignores `layer`, `first`, and `after` for the empty TRACE object collection. Bogus layer, `first=0`, `first=101`, and malformed cursor probes all returned the same 200 empty page, although OpenAPI declares an enum, bounds 1–100, and cursor validation. Fixture mode validates pagination but also accepts a bogus layer. This is `TRACE-BLOCK-008` and remains outside this round because public API changes were forbidden.

## Retained v48 comparison

The rich v48 `TraceExplorer` and its 580 declared assets remain tracked but are not imported by `/trace`. They are a `LEGACY_IMPLEMENTATION_CANDIDATE`, not v49 truth. Other existing pages still publish v48 counts/taxonomy, creating a release-labeling conflict documented as `TRACE-BLOCK-006`; those pages were not changed.

The required after-change browser smoke is recorded in the audit package. Functional parity requires the same text, zero count, and clean console.
