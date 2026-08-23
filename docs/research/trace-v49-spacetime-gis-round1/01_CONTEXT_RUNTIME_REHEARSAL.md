# Context V1 runtime rehearsal

## Decision

`CONTEXT_V1_RUNTIME_REHEARSAL=PASS`

`CONTEXT_V1_ENGINEERING_LOGIC=FROZEN`

The frozen `trace-context-v1` projection is pre-generated, preverified, and read-only at public runtime. The normal Context API, governed server loader, and governed Canvas path do not reach the Round 2 real-data reconciliation loader, SQLite, the eligibility-ledger parser, or Search. Context semantics, term identity, explanations, provenance, publication decisions, and public IDs were not changed.

## Runtime path

The rehearsed path is:

```text
committed trace-context-v1 JSON artifacts
  -> server-only reader
  -> one validated process-level immutable index
  -> selected public-record DTO
  -> governed Canvas adapter and graph
  -> accessible rows and export-only SVG preparation
```

The public API controller first checks the exact full Context resource shape. Only that branch dynamically imports the Context API runtime. It returns before the generic repository provider is imported or opened. Conversely, an unrelated API resource does not import the 13 MB Context projection.

## Static dependency audit

The verifier parses TypeScript/JavaScript syntax trees and walks resolved runtime import, re-export, `import()`, and `require()` edges. Type-only imports are excluded. This is a reachable-module audit, not a filename grep.

| Runtime entry | Reachable modules | Runtime edges | Heavy validation imports | SQLite imports | Search imports |
| --- | ---: | ---: | ---: | ---: | ---: |
| Context API runtime | 9 | 8 | 0 | 0 | 0 |
| Projection loader | 8 | 7 | 0 | 0 | 0 |
| Governed Canvas route | 39 | 84 | 0 | 0 | 0 |

Additional execution-boundary probes passed:

- unrelated API request Context module loads: `0`;
- Context request generic provider opens: `0`;
- Context request newly loaded Search runtime modules: `0`;
- Context path guard precedes both the lazy generic-provider import and `provider.open()`.

The manifest retains SHA-256 bindings to SQLite and the eligibility ledger as provenance strings. The public reader does not open, hash, or parse either source artifact.

## Projection preflight

`npm run verify:context-v1-projection` rebuilt the projection twice in memory and byte-compared every committed artifact. It passed the frozen release binding, policy, term registry, explanation registry, exception registry, record census, and aggregate projection-hash checks.

Generation/reconciliation continues to use frozen source inputs only in this explicit preflight/CI path. No regeneration or source reconciliation occurs during a public request.

## Full-cohort rehearsal

The production-like non-browser rehearsal exercised all public and held identities through the committed projection:

| Check | Result |
| --- | ---: |
| Public lookups | 7,995 |
| Public lookup failures | 0 |
| Full DTO/Canvas/accessibility/export pipeline passes | 7,995 |
| Published representations resolved | 16,106 |
| Accessible rows resolved | 24,101 |
| Governed Canvas nodes derived | 24,101 |
| Governed Canvas connections derived | 16,106 |
| Held lookups | 7,928 |
| Held exposures | 0 |
| Non-`NOT_FOUND` held failures | 0 |
| Process-level index build attempts | 1 |
| Successful process-level index builds | 1 |

For every public object the rehearsal performed selected-record lookup, DTO construction, explanation resolution, provenance resolution, Canvas dataset conversion, governed graph derivation, accessible-row derivation, and safe SVG-export preparation. Held identities returned the same generic `NOT_FOUND` result and were never written to evidence.

## Performance

Measurement environment: Node `v22.21.0`, V8 `12.4.254.21-node.33`, Darwin arm64, `--expose-gc`. These local timings are engineering rehearsal measurements, not service-level guarantees.

| Metric | Result |
| --- | ---: |
| Cold module import + first selected-record lookup | 479.590 ms |
| Module import / committed JSON parse | 52.051 ms |
| Manifest verification | 109.485 ms |
| Registry validation | 0.542 ms |
| Record validation and index construction | 57.819 ms |
| Public-payload boundary validation | 259.203 ms |
| Total integrity validation/index construction | 427.094 ms |
| First selected-record lookup, including cold validation | 427.540 ms |
| Warm lookup P50 | 0.003 ms |
| Warm lookup P95 | 0.004 ms |
| Warm lookup P99 | 0.005 ms |
| Warm lookup max | 0.591 ms |
| Governed runtime heap delta | 18,296,176 bytes |

The reader's module-scoped cache was empty before the first lookup, built successfully once, and remained the same referential index for all 15,923 public-plus-held lookups and the subsequent warm pass. Integrity verification was not removed; it moved no farther than the existing once-per-process lifecycle boundary.

## Reproduction

From `frontend/`:

```bash
npm run verify:context-v1-projection
node --conditions=react-server scripts/probe-context-api-lazy-boundary-v1.mjs
node --expose-gc --conditions=react-server scripts/rehearse-context-runtime-v1.mjs \
  --evidence-dir /private/tmp/trace-v49-context-runtime-rehearsal-round4
npm run test:context-api-v1
```

The rehearsal writes only aggregate, sanitized evidence. The authoritative final run produced three files under `/private/tmp/trace-v49-context-runtime-round4-final` with evidence receipt SHA-256 `9435e23a1884790af3956f9108ec058c1a1be771381d2c183d18f0daec059770`. No Round 3 sealed evidence was rewritten.
