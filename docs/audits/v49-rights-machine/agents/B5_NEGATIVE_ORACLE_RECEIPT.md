# B5 — Negative-test oracle and consistency receipt

- Agent task: v49 Phase 1D B5
- Worktree: `/Users/jarlgiovanni/Desktop/modern_GD_history_v49_data_platform`
- Branch: `refactor/v49-data-platform`
- Scope result: **PASS**
- Executable implementation tests run: **false**

## Task boundary

B5 owned only:

- `docs/audits/v49-rights-machine/10_NEGATIVE_TEST_SPEC.md`;
- this receipt.

B5 defined implementation-neutral negative tests and cross-checked B1–B4. It did not modify their outputs, normative architecture documents, code, package files, frozen assets, QA images, databases, manifests, checksums, CI, or deployment configuration.

## Assets read

B5 read the current five root v49 documents, `docs/architecture/DDL_DECISION_PACK_V49.md`, all four ADRs, the Phase 1C authority/research gate receipt and manifest, and all available B1–B4 files under `docs/audits/v49-rights-machine/` in full. B3's compact TSV was reviewed as a bounded 71-row aggregate ledger together with its complete JSON summary and receipt; B5 did not reinterpret its measured zero positive-rights coverage as a delivery decision.

## Evidence commands

Representative commands were local and bounded:

```text
git status --short --branch
find docs/audits/v49-rights-machine -maxdepth 2 -type f -print
wc -l -c <named normative, Phase 1C, and B1–B4 files>
sed -n '<complete non-overlapping ranges>p' <named files>
rg -n '<delivery/version/locator/URI/state terms>' <bounded normative and B1–B4 paths>
git diff --check -- docs/audits/v49-rights-machine/10_NEGATIVE_TEST_SPEC.md docs/audits/v49-rights-machine/agents/B5_NEGATIVE_ORACLE_RECEIPT.md
```

No command contacted a provider, network service, database writer, package registry, frontend server, browser, or protected main path.

## Measured specification coverage

| Area | Case count | Result |
|---|---:|---|
| Rights/policy/delivery/health/takedown | 11 | PASS; includes one positive control and every requested negative rule |
| Machine selection/redaction/version | 14 | PASS; includes registry absence, explicit mismatch, held locator, lower-mode non-disclosure and GET-only behavior |
| Seal/immutability/CAS | 9 | PASS; includes both stale-CAS cases and cross-boundary non-mutation |
| Authority/derived-product anti-write | 5 | PASS; Search/TRACE/API products cannot create canonical rows |
| Total deterministic oracle cases | 39 | PASS |

The specification defines exact inputs, expected effective state or typed error, structural serializer outcome, and a protected invariant for every case. `ABSENT(path)` explicitly rejects `null`, empty, redacted, CSS-hidden, or client-filtered substitutes.

## Findings

### P0 — closed within B1–B5

1. Unknown rights plus a healthy remote URL yields no remote pixel; with no qualified canonical record it is `CITATION_ONLY`.
2. Permitted rights plus viewer-only provider policy yields at most `SOURCE_VIEWER`; remote pixels are structurally absent.
3. A dead remote endpoint downgrades to an independently qualified `LINK_ONLY` record link or `CITATION_ONLY`; it cannot widen rights.
4. Active takedown precedes every positive rights/policy/health input and reduces to `BLOCKED` or `CITATION_ONLY`.
5. Post-seal mutation and stale research/visual CAS attempts are atomic failures.
6. Explicit research/visual mismatch is `409 RELEASE_VERSION_MISMATCH`; registry absence remains normal research-only success.
7. Held/raw/internal locators never serialize, including through Search, TRACE, problems, logs, HTML, cursors, or machine alternates.
8. Derived Search, TRACE, visual-registry and API payloads cannot create canonical rows or assertions.

### P0 — primary normative integration required

1. Replace/map legacy `PIXEL_ALLOWED` and `WITHHELD` delivery vocabulary to the closed five-mode registry.
2. Change the old visual-pair-required read rule to the locked research-only success behavior for absent/unavailable registries while preserving typed errors for explicit bad selectors.
3. Use one public digest field, `visualRegistrySha256`, and explicitly map the internal/logical `registrySha256` to it.
4. Replace final-identity `.example` templates with `urn:gdarchive:*`; preserve `.example` text only as a non-resolvable frozen UUID seed input.
5. Preserve the separately addressable rights evidence/assessment, provider policy/evaluation, delivery, health, attribution, and takedown records/inputs rather than reverting to a three-axis shorthand or one `rights_status`.

These findings do not require B5 to rewrite another agent's file. They must be resolved by the primary normative integration and then checked by the independent joint verifier.

### P1

- An active post-seal takedown requires a deterministic overlay SHA in effective response/cache identity. Executable cache-bypass and overlay-reproducibility tests remain pre-freeze implementation work.
- The public HTTPS resolver origin is pending; canonical URNs keep this from reopening the DDL identity decision.

### P2

- Route layout, selector transport, JSON-LD context, DCAT mapping, sitemap, telemetry policy, and human error copy remain later contract/implementation details so long as they cannot weaken the locked identities and redaction rules.

## Unresolved implementation evidence

PostgreSQL constraints/grants/triggers, actual release manifests/sidecars/pointers, Read API, OpenAPI, JSON Schema, JSON-LD/Linked Art/PROV-O/DCAT, frontend Repository integration, CI, deployment, production endpoint-health checks, browser/accessibility tests, and provider positive-rights review are not implemented or executed. Their absence keeps downstream readiness false but is not, by itself, a pre-DDL decision failure.

## Files changed

- `docs/audits/v49-rights-machine/10_NEGATIVE_TEST_SPEC.md`
- `docs/audits/v49-rights-machine/agents/B5_NEGATIVE_ORACLE_RECEIPT.md`

## Actions explicitly not performed

No network, HTTP/IIIF/image request, provider probe, media download, PostgreSQL, SQLite, DDL, migration, import/export, Docker, npm, Next.js, TypeScript, browser, screenshot, API/schema/fixture implementation, frontend/package/CI/deployment change, frozen-asset/QA edit, protected-main mutation, commit, push, PR, merge, or deployment was performed.

## Residual processes

B5 started no server, compiler, browser, database, package installer, data generator, network request, or background process. All B5 shell reads and scoped validation commands exit synchronously. The primary task owns the final repository-wide residual-process scan.

## Exit fields

```text
B5_STATUS=PASS
B5_ORACLE_CASES=39
NEGATIVE_ORACLE_REQUIRED_CASES_PRESENT=true
RIGHTS_DELIVERY_ORACLE_LOCKED=true
MACHINE_REDACTION_ORACLE_LOCKED=true
SEAL_CAS_ORACLE_LOCKED=true
DERIVED_TO_CANONICAL_WRITE_ALLOWED=false
EXECUTABLE_IMPLEMENTATION_TESTS_RUN=false
FILES_MODIFIED=2
RESIDUAL_B5_PROCESS=0
```
