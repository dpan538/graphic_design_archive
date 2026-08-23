# Preprogramming Foundation and Validation

## Delivered scope

`frontend/src/features/trace-v49/` is disconnected from public routes and renderers. It provides:

- release identity and explicit availability states;
- public-safe references and archive-object allowlist validation;
- evidence policy definitions and accepted-edge validation;
- compile-time separation among semantic edges, controlled assignments, curated memberships, source associations, and visual guides;
- pure deterministic projections for context, spacetime, and sources;
- precision/role-preserving time and place types;
- denominated aggregates and missingness;
- accessible row conversion for every domain;
- public-only synthetic fixtures containing no title, URL, locator, wording, UUID, or held data.

No coordinates, styles, colors, SVG, animation, layout, route integration, legacy import, AI code, or new dependency was added.

## Invariant validation

`node frontend/scripts/verify-trace-v49-preprogram.mjs` exercises all `TRACE-INV-001` through `TRACE-INV-016`, plus explicit availability, identity-conflict rejection, and no-truth-inference source behavior. `tests/type-invariants.ts` makes membership and visual-guide promotion compile failures with `@ts-expect-error` proofs.

Observed result:

```text
TRACE_V49_PREPROGRAM_TESTS=PASS CHECKS=19 INVARIANTS=16
```

The tests additionally check fixture archive IDs against the frozen 7,995-document public search cohort. A semantic edge whose archive endpoint is not in the caller-supplied public set fails closed before projection. Registered active predicate and evidence/locator requirements are independently enforced.

## Determinism and mutation

Each projection copies release/availability metadata, stable-sorts by explicit identity, rejects conflicting duplicates, freezes result arrays/objects where created, and never sorts caller arrays in place. The same release and byte-equivalent input produce deep-equal output. Input JSON snapshots remain byte-identical before/after projection.

The statistics generator:

- validates frozen source hashes, schema hash, object counts, folder count, and search population;
- derives public/held identity only from the audited v49 ledger;
- opens SQLite with `mode=ro&immutable=1`, enables `PRAGMA query_only=ON`, and verifies integrity;
- emits deterministic TSV/JSON/checksum artifacts;
- supports byte-for-byte `--check`.

## Performance

`node --expose-gc scripts/trace-v49-analysis/benchmark_trace_v49_preprogram.mjs` measures 2,000 timed iterations after 200 warmups for every domain at minimal, median, P95, P99, and maximum measured structures. Maximum observed projection P95 was 0.035545 ms; the provisional <20 ms target passed. Raw evidence is in `raw/preprogram-benchmark.json`.

## Validation boundary

The foundation validates representation and publication guards; it does not validate the truth of candidate raw metadata. There are no actual v49 accepted semantic edges to exercise end-to-end. Future nonzero data must be validated against the same invariants, real predicate registry, evidence policy, and public release projection.
