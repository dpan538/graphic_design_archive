# A1 agent receipt — authority, lineage, and parent assets

- Agent package: A1
- Independent boundary: canonical/reconciliation/integrity/derived authority; missing v47 parents; legacy builder clean-checkpoint closure; TRACE projection boundary
- Output files owned:
  - `docs/audits/v49-authority-research-delta/01_SCOPED_AUTHORITY_MATRIX.md`
  - `docs/audits/v49-authority-research-delta/02_PARENT_ASSET_DEPENDENCY_LEDGER.tsv`
  - `docs/audits/v49-authority-research-delta/agents/A1_AUTHORITY_LINEAGE_RECEIPT.md`
- Exit status: **PASS**
- Files outside this ownership boundary modified: **none**
- Frozen assets modified: **none**

## Task boundary

A1 determined the authority role of the v48 final candidate, reconciliation SQLite, transfer/TRACE manifests, Search/TRACE products, historical parents, repair inputs, and adjunct evidence. It identified every concrete dependency needed to explain the missing v47-parent boundary, statically assessed legacy entrypoints without executing them, and fixed the v49 preservation contract to frozen-output verification.

A1 did not perform graph-row classification, corpus selection, raw-provider rights review, visual-provider policy, database implementation, or migration execution.

## Assets read

Normative and prior-audit evidence:

- `ARCHITECTURE.md`
- `MIGRATION_V48_TO_V49.md`
- `docs/architecture/DDL_DECISION_PACK_V49.md`
- `docs/adr/0001-canonical-postgres-and-read-only-release.md`
- `docs/adr/0002-immutable-data-versioning.md`
- `docs/adr/0004-research-claims-corpora-and-visual-registry.md`
- `docs/audits/v49-pre-migration/03_DATA_ASSET_AUTHORITY_AND_LINEAGE.md`
- `docs/audits/v49-pre-migration/04_DATABASE_AND_DDL_READINESS.md`
- `docs/audits/v49-pre-migration/12_FREEZE_READINESS_MATRIX.md`
- `docs/audits/v49-pre-migration/13_PROCESS_AND_COMMAND_RECEIPT.md`

Builders and contracts:

- `scripts/build_prefreeze_candidate_v47_aic_balance.py`
- `scripts/build_prefreeze_candidate_v47_search_sqlite.py`
- `scripts/repair_prefreeze_candidate_v48_loc_geography.py`
- `scripts/build_prefreeze_candidate_v48_loc_geo_repair.py`
- `scripts/build_prefreeze_candidate_v48_search_sqlite.py`
- `scripts/audit_prefreeze_candidate_v48_freeze.py`
- `scripts/build_prefreeze_candidate_v48_transfer_manifest.py`
- `scripts/build_prefreeze_candidate_v48_trace_visualization.py`
- `frontend/scripts/generate-archive-search-index.mjs`
- enumerated current-tree v46/v47/v48 input paths listed in `02_PARENT_ASSET_DEPENDENCY_LEDGER.tsv`
- bounded metadata from the v48 transfer manifest, TRACE manifest, and archive Search index
- historical Git objects for the two missing v47 paths at `31f8481ba960087a3ba740d62a40639bbf48258a` and `1d919fb0e6c5ed5bba9bf728cf7aa27fb7ce821b`

Spreadsheet/TSV guidance read:

- `spreadsheets/SKILL.md`
- `spreadsheets/style_guidelines.md`
- `spreadsheets/artifact_tool_docs/API_QUICK_START.md`
- `spreadsheets/domain_guidance/scientific_research.md`

The A1-local workspace dependency loader did not return within the bounded wait and was terminated. The primary task separately confirmed bundle `26.805.11740`, its Node runtime, and `@oai/artifact-tool` dependency path. A1 did not retry the loader; the primary task owns independent artifact-tool TSV validation.

## Commands executed

All repository commands were read-only. Representative exact command classes:

```text
sed -n ... and nl -ba ... | sed -n ... <selected documents and builders>
rg --files docs | sort
rg -n -i <authority, v47, parent, builder, TRACE, Search patterns> <bounded paths>
find docs/audits/v49-authority-research-delta -maxdepth 2 -type f -print
git status --short --branch
git log --all --format=... -- <v47 parent paths>
git cat-file -e HEAD:<v47 parent path>
git cat-file -p <historical commit>:<v47 parent path>
git ls-tree -l <historical commit> <v47 parent paths>
git show -s --format=... <historical commits>
git check-attr filter diff merge text -- <v46-v48 large paths>
git ls-files <enumerated dependency paths>
stat -f '%N\t%z' <enumerated dependency paths>
jq <bounded role/count metadata> <transfer manifest, TRACE manifest, Search index>
git ls-files 'frontend/public/data/trace-v48/*.json' 'frontend/public/data/trace-v48/neighborhoods/*.json'
```

A single overly broad initial `rg` matched the one-line candidate JSON and produced truncated terminal output. It made no write, was not repeated, and no conclusion relies on the truncated payload. Subsequent searches were path- and file-type-bounded.

## Evidence and measured results

- Both direct v47 parent paths are absent from audited HEAD.
- Historical Git commits retain 134-byte LFS pointers:
  - v47 JSON: SHA-256 OID `bc9d83892c91beabc7a1ec593f4d4315d7f377f3d9d98df6e2f20b082142ff7f`, declared size 190,062,921;
  - v47 SQLite: SHA-256 OID `e3b597f365960007562aa8715fcbc713220239c6a011b3040fd926ae4e47cd7c`, declared size 421,670,912.
- The direct v48 JSON builder, direct v48 SQLite builder, network LOC collector, and old freeze auditor are not clean-checkpoint self-contained.
- Enumerated v46 bodies, v47 active/adjunct CSVs, sample input, and helper code for the indirect v46→v47 stage are present and tracked. This is static path closure, not replay proof.
- The legacy TRACE builder has all four declared current inputs but reads authoritative-looking graph facts from reconciliation SQLite, uses v47 adjunct data, uses a derived frontend payload for routes, maps otherwise unknown labels to `medium_context`, and rewrites the entire TRACE product. It cannot establish v49 graph authority.
- Transfer metadata explicitly excludes the v47 JSON/SQLite intermediates.
- The final frozen candidate JSON is sufficient as the sole v49.0 canonical migration input under the locked one-row/one-baseline-object rule.
- v47 parent recovery is not required or authorized for Phase 1C migration design.

## Findings

| Priority | Count | Summary |
|---|---:|---|
| P0 closed | 2 | parent authority/preservation boundary; derived graph facts fail closed |
| P1 retained | 2 | exact legacy byte replay unverified; legacy writers/network entrypoints remain unsafe for migration |
| P2 retained | 1 | historical LFS body availability not tested |

## Unresolved items

- The combined graph reconciliation must still reach zero unclassified graph facts.
- The primary verifier must prove its declared input set excludes both v47 parents and that it never converts a reconciliation/derived row into a canonical row.
- Exact archival replay may be tested only in a later, separately authorized quarantined task; it is not a v49 migration gate.
- Visual rights/provider/delivery decisions remain out of scope for Prompt B.

## Static output self-check

The final A1 check verifies:

- all three owned files exist;
- the TSV has exactly one header and a constant tab-field count;
- the TSV is valid UTF-8 and contains no carriage returns;
- every literal repository path in the ledger is either present, deliberately absent with a recovery reference, a declared glob/group, or an external locator;
- Markdown headings/code fences are balanced;
- `git diff --check` passes for the three owned files;
- no other A1-owned path is modified.

## Actions explicitly not performed

- no v47 parent fetch, copy, recovery, generation, or LFS materialization;
- no five-frozen-asset full hash pass and no SQLite integrity check;
- no legacy builder, data export, migration, verifier, or database write;
- no PostgreSQL, Docker, npm, Next.js, TypeScript, browser, screenshot, image download, HTTP request, or frontend operation;
- no frozen asset, specification, code, package, CI, deployment, QA, or protected-main modification;
- no commit, push, PR, merge, deploy, cleanup, reset, checkout, or stash.

## Exit

```text
A1_STATUS=PASS
A1_FILES_MODIFIED=3
A1_RESIDUAL_EXECUTION_SESSION=0
GLOBAL_RESIDUAL_PROCESS_SCAN=PRIMARY_TASK_OWNED
PARENT_ASSET_AUTHORITY_BOUNDARY_LOCKED=true
V49_BASELINE_MIGRATION_REQUIRES_V47_PARENTS=false
LEGACY_V48_EXACT_BYTE_REPLAY_FROM_CURRENT_HEAD=UNVERIFIED
```
