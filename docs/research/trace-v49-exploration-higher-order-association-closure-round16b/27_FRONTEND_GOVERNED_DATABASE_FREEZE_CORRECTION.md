# Checkpoint 14: frontend governed-database-freeze correction

## Outcome

The first frontend boundary in the clean Checkpoint 13 checkout truthfully failed. The legacy Exploration reset guard treated every path changed below `database/` since its older source SHA as prohibited and therefore rejected all eleven governed additive v50 files introduced by Round 16B.

This was not frozen-v49 drift. The repository's authoritative freeze verifier returned `PASS`, database version `50`, 126 frozen files, zero frozen-path drift, and eight unmanifested additive database files backed by the v50 ADR. The failure exposed incompatible guard semantics that were hidden by earlier runs outside a true clean final-reproduction sequence.

## Additive correction

`frontend/scripts/exploration-reset-guard.mjs` now:

- retains the full database diff and its count as transparent measurements;
- invokes `scripts/repository/verify_v49_database_freeze.py` as the governed integrity decision;
- fails closed when that verifier cannot run, does not return `PASS`, or reports any frozen-path drift;
- does not use a brittle allowlist for the eleven current v50 paths.

The domain suite adds one positive control proving that additive v50 files with zero frozen drift are accepted and one negative control proving that frozen-path drift is rejected.

## Verification

The corrected guard and domain boundary pass with eight structural checks and all twelve red-team cases rejected. The constraint kernel, inquiry adapter, composition review, association calibration, composition engine, v3 projection, 408-check v3 API suite, runtime typecheck, and production build also pass. The first production build was blocked by sandbox DNS while resolving the two declared Google Fonts; the identical narrowly network-enabled correction passed and generated all 46 static pages.

The clean Checkpoint 13 database bootstrap attempt is not presented as reproduction evidence. It stopped before creating a role, database, server, or socket because the host had exhausted all 32 System V shared-memory identifiers. No unrelated IPC segment or process was altered. The exact failed-bootstrap root was removed after an approved process/socket absence proof. Fresh database reproduction remains required from the published corrected checkpoint.

## Closure boundary

This correction changes no association, evidence, composition, state, workflow, export, or closure decision. All six closure flags remain false. Final clean reproduction, fresh two-database replay, production HTTP/load/memory/export validation, complete reachable-blob proof, final audit sealing, and final ordinary branch publication remain pending.
