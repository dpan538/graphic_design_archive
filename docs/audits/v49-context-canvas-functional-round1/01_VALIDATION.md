# Validation

All commands ran from `frontend/` unless noted. No development server, localhost listener, browser automation, or screenshot workflow ran.

| Gate | Command | Result |
| --- | --- | --- |
| Clean install | `npm ci` | PASS — 145 packages installed |
| TypeScript | `npx tsc --noEmit --pretty false` | PASS |
| Context Canvas | `node scripts/verify-context-canvas-v49.mjs` | PASS — 31 checks, 18 invariants, 4 templates, 9 associations, P95 0.066 ms |
| TRACE preprogram | `node scripts/verify-trace-v49-preprogram.mjs` | PASS — 19 checks, 16 invariants |
| Search index | `npm run verify:search-v49-index` | PASS — 7,995 documents; frozen SHA unchanged |
| Search regression | `npm run test:search-v49` | PASS — 14 checks, 7,995 documents |
| Read platform/API | `npm run test:read-platform` | PASS — direct data coupling 0 |
| Runtime typecheck | `npm run typecheck:runtime` | PASS |
| Page-by-key runtime | `node scripts/verify-page-by-key-module-contract.mjs` | PASS |
| Production build | `npm run build` | PASS — 47 static pages; `/trace/context-canvas` emitted as static content |
| Patch hygiene | `git diff --check` | PASS |
| Protected paths | source-to-worktree Git comparison | PASS — no protected paths changed |

## Canvas verifier coverage

The pure Node/Jiti verifier covers all `CTX-CANVAS-INV-001` through `CTX-CANVAS-INV-018`, template initialization, deterministic layout and SVG geometry, fit-to-content, viewport transforms, reducer actions and history bounds, persistence version rejection, typed connection derivation, safe export preparation, accessible-row coverage, forbidden imports, and the current maximum-workload benchmark.

## Build result

Next.js 15.5.18 compiled, typechecked, prerendered 47 pages, and emitted `/trace/context-canvas` at 14.9 kB route size / 117 kB first-load JavaScript. No preview server was started.

See `raw/` for command receipts.
