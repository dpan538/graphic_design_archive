# C1 — AI Runtime Retirement Receipt

## Result

`PASS` for the C1 static retirement boundary.

- `QWEN_RUNTIME_IMPORTS=0`
- `ACTIVE_ASSISTANT_ROUTES=0`
- `MODEL_RUNTIME_PRODUCTION_IMPORTS=0`
- `ASSISTANT_RUNTIME_REFERENCE_FILES=0`
- `DETERMINISTIC_SEARCH_PRESERVED=true`
- `TRANSFORMERS_PACKAGE_AND_LOCK_REFERENCES=0`
- `TASK_OWNED_RESIDUAL_PROCESSES=0`

This receipt does not claim a Next.js build, browser test, full TypeScript check,
or production runtime verification. The controller owns the single bounded
TypeScript gate for the combined cleanup change set.

## Boundary

C1 retired only the active browser-local assistant runtime and its dedicated
dependency/CSS surface. It did not change archive data, generated search data,
the full Search route, TRACE, A4 components, QA assets, frozen assets, or the
protected dirty main worktree. It did not commit, push, merge, deploy, start a
server, or run a build.

Baseline HEAD while C1 worked:
`f75ded85000749beb4735fbbddcce99e9395b0b2`.

## Skills and references read

The following instructions were read before editing and constrained the patch:

- Next.js skill, plus `route-handlers.md`, `directives.md`,
  `rsc-boundaries.md`, and `functions.md`;
- React best-practices skill, plus `bundle-conditional.md`,
  `client-event-listeners.md`, `rerender-derived-state-no-effect.md`,
  `rerender-move-effect-to-event.md`, and `rerender-dependencies.md`.

Consequences for this patch: the obsolete POST Route Handler was removed as a
route boundary; the remaining interactive Search stays a client component;
the assistant-only global event/effect and conditional model import were
removed; deterministic Search state remains local and derived values remain
render-time values.

## Assets read or inspected

- `frontend/src/components/archive/reader/Reader.tsx`
- `frontend/src/components/archive/shell/ArchiveShell.tsx`
- `frontend/src/components/archive/shell/search.tsx`
- `frontend/src/app/api/archive-assistant-evidence/route.ts`
- `frontend/src/lib/assistant-memory.ts`
- `frontend/src/lib/assistant-retrieval.ts`
- `frontend/src/lib/qwen35-adapter.ts`
- assistant-specific regions of `frontend/src/app/globals.css`
- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/src/lib/archive-search-client.ts` and
  `frontend/src/app/search/page.tsx` existence/contract references

## Evidence commands

Representative commands (all run from the isolated v49 worktree) were:

```text
git grep -n -I -E '@huggingface/transformers|qwen35-adapter|assistant-memory|assistant-retrieval|archive-assistant-evidence|archive:open-assistant' -- 'frontend/src/**/*.ts' 'frontend/src/**/*.tsx'
rg -n 'IconAssistant|openAssistant|archive:open-assistant|btn-turn--assistant|assistant' frontend/src/components/archive/reader/Reader.tsx frontend/src/components/archive/shell/ArchiveShell.tsx frontend/src/components/archive/shell/search.tsx
npm install --package-lock-only --ignore-scripts --no-audit --no-fund
node -e '<compare HEAD package-lock package graph with current package-lock>'
rg -l -i 'qwen|@huggingface/transformers' frontend/src --glob '*.ts' --glob '*.tsx' --glob '!data/**' --glob '!generated/**'
rg -l -i 'archive-assistant|archive:open-assistant|assistant-memory|assistant-retrieval|qwen35-adapter' frontend/src --glob '*.ts' --glob '*.tsx' --glob '!data/**' --glob '!generated/**'
find frontend/src/app/api -type f -path '*assistant*'
rg -n 'assistant|btn-turn--assistant|page-turn__sep' frontend/src/app/globals.css
rg -n 'archive-search-client|searchArchiveSurfaces\(trimmed, 30\)|Open full archive \+ TRACE search' frontend/src/components/archive/shell/search.tsx
git diff --check
ps -axo pid=,ppid=,etime=,command=
```

No command printed secret values.

## Changes

### Production runtime removed

- removed the Reader `archive:open-assistant` dispatch, Research control, and
  assistant icon;
- removed ArchiveShell assistant context/mode state, global event listener, and
  assistant SearchBox props;
- reduced `search.tsx` to its pre-existing deterministic local archive-search
  flow and UI;
- removed the assistant POST route;
- removed assistant browser memory, retrieval, and Qwen adapter modules;
- removed only assistant-specific CSS selectors, the now-unused assistant
  page-turn separator, and corrected one contextual-panel comment.

### Dependency removed atomically

Before editing, the only production source import of
`@huggingface/transformers` was in the removed Qwen adapter. The successful
package-lock-only update produced:

- package graph: `218 -> 176` entries;
- removed entries: `42` (Transformers, ONNX, and their now-unreachable
  transitive packages);
- added package entries: `0`;
- retained packages with a changed `version`, `resolved`, or `integrity`: `0`;
- package.json/root-lock dependency parity: `true`;
- `@huggingface/transformers` present in package.json: `false`;
- `@huggingface/transformers` present in package-lock.json: `false`.

The seven lockfile additions are reachability flags (`dev`/`optional`) on
retained shared packages, not package/version churn. No `frontend/node_modules`
directory was created.

## Static verification

| Check | Measured result | Status |
| --- | ---: | --- |
| Qwen/Transformers production source files | 0 | PASS |
| assistant event/route/module production reference files | 0 | PASS |
| Hugging Face/ONNX/Qwen model import files | 0 | PASS |
| assistant API route files | 0 | PASS |
| assistant CSS selector files | 0 | PASS |
| Transformers package/lock reference files | 0 | PASS |
| `archive-search-client` import in SearchBox | 1 | PASS |
| `searchArchiveSurfaces(trimmed, 30)` call | 1 | PASS |
| full archive + TRACE Search link | 1 | PASS |
| archive Search client exists | true | PASS |
| full `/search` route exists | true | PASS |
| retired route/modules still present | 0 | PASS |
| package/root-lock parity | true | PASS |
| retained package version/resolution/integrity drift | 0 | PASS |
| `git diff --check` | exit 0 | PASS |

The CSS diff removes 128 lines and adds one comment-only line. Every removed
selector was assistant-specific or the separator solely rendered beside the
removed assistant control; no ordinary Search rule was removed.

## Command and process receipt

The first package-lock-only invocation was sandboxed and failed with `EPERM`
before writing `frontend/package-lock.json` (`exit 255`). The identical command
was then run with the required worktree write permission and completed once
successfully (`exit 0`, `up to date in 4s`). It used `--ignore-scripts`,
`--no-audit`, and `--no-fund`; it did not install dependencies.

The final read-only process scan found no command containing the target
worktree path together with `npm`, `Next`, `tsc`, Qwen, or Hugging Face. Both
npm invocations exited. `TASK_OWNED_RESIDUAL_PROCESSES=0`.

## Explicitly not verified or performed

- No Next dev/build/start or browser automation.
- No npm dependency installation and no lifecycle scripts.
- No full or bounded TypeScript compilation in C1. A targeted parser attempt
  could not load TypeScript because this worktree intentionally has no
  `node_modules`; it made no changes. The controller's one bounded TypeScript
  check remains the compilation oracle.
- No frontend screenshot or visual claim.
- No edit outside the C1 allowlist and this receipt.
- No commit, push, PR, merge, deployment, database, or frozen-asset operation.

## Exit

`C1_EXIT=PASS_STATIC_SCOPE`
