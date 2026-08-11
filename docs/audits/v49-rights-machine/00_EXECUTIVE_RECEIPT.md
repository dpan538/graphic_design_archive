# v49 Phase 1D — Rights, visual registry and machine-contract executive receipt

- Decision package: **PASS**
- Implementation status: **NOT IMPLEMENTED**
- Worktree: `/Users/jarlgiovanni/Desktop/modern_GD_history_v49_data_platform`
- Branch: `refactor/v49-data-platform`
- Initial/local/remote commit at entry: `967cbe34a8f30f8e74fa117e1bdee74644f71afe`
- Frozen source ancestor: `0404c7f96f9189f576c4c5b1368061e4082e436b`

## Prerequisite result

Phase 1D began only after local and remote were equal, the worktree was clean, the frozen ancestor was present, the protected dirty main matched its recorded fingerprints, and Prompt A's manifest/checksums passed. The Phase 1C verifier returned PASS with all authority/count/research gates required by this phase:

```text
INPUT_PARITY=true
UNACCOUNTED_INPUT_SURFACES=0
UNCLASSIFIED_GRAPH_FACT=0
UNCLASSIFIED_RAW_SOURCE=0
METADATA_SUPPORTED_CONFLICT_RESOLVED=true
AUTHORITY_RESEARCH_DELTA_CLOSED=true
```

## Closed pre-DDL decisions

This package closes the remaining logical decisions that determine future physical keys, FKs, state columns, immutable version boundaries and public-field suppression:

1. `rights.external_visual_reference` is a provenance-occurrence identity, not a URL, permission, provider object, representation or archive object.
2. Archive object ↔ visual reference is N:M through `rights.object_visual_reference` with real FKs. Observation/assessment/takedown target families use closed exactly-one typed subtypes; arbitrary `target_type + target_id` is prohibited.
3. Rights observations/assessments, provider-policy versions/evaluations, delivery decisions, endpoint-health observations and takedown state remain independent. Attribution is an explicit positive-delivery prerequisite.
4. Delivery is exactly `BLOCKED`, `CITATION_ONLY`, `LINK_ONLY`, `SOURCE_VIEWER` or `REMOTE_IMAGE`. Only `REMOTE_IMAGE` may expose the v1 allowlisted remote-pixel field; lower modes structurally omit pixel, thumbnail and image-service fields.
5. Research release and visual registry have independent `draft → candidate → validated → sealed` lifecycles, manifests, detached sidecars, immutable copied projections and CAS-protected current pointers. A visual version declares exactly one compatible research pair.
6. A missing compatible registry is a normal research-only state. An explicitly supplied incompatible pair is `409 RELEASE_VERSION_MISMATCH`; no prior/current registry is inherited by fallback.
7. Public responses use the exact research pair and an atomic optional visual pair named `visualRegistryVersion + visualRegistrySha256`. Internal `registry_sha256` is the same digest, not another public field.
8. Canonical public resource identity is `urn:gdarchive:{object|relation|claim|source|visual-reference}:<lowercase-uuid>`. Frozen `.example` strings remain non-resolvable UUIDv5 seed inputs only.
9. Public DTOs start from an empty positive allowlist with closed `SAFE`, `PUBLIC`, `INTERNAL` and `HELD` classes. Held/internal/raw locators are absent before cache and serialization, not hidden by CSS.
10. API/OpenAPI/JSON Schema/JSON-LD/DCAT, CI, deployment, frontend Repository adoption, production health checks and browser QA remain later implementation gates and do not reopen these decisions.

## Measured legacy visual baseline

The canonical v48 candidate JSON was parsed once by B3 and independently once by B7. Both produced the same values and hashes:

| Unit | Value |
|---|---:|
| Candidate surface visual bundles | 15,923 |
| Accounted / unaccounted | 15,923 / 0 |
| Reference-bearing / no reference | 15,788 / 135 |
| External locator occurrences / distinct values | 15,790 / 15,788 |
| `image.url` / `viewerUrl` / `sourceViewerUrl` / `evidenceImageUrl` | 15,621 / 165 / 2 / 2 |
| Compact deterministic disposition groups | 71 |
| Unclassified visual references | 0 |
| Positive-rights-qualified bundles | 0 |
| Positive-rights coverage | 0.0000% |

All 15,788 reference-bearing bundles are typed `RIGHTS_UNKNOWN`, `POLICY_UNKNOWN` and `UNMAPPED_PROVIDER`; the 135 remaining bundles are typed `NO_VISUAL_REFERENCE`. This is 100% classification with a conservative evidence result, not a claim that later governed review could never authorize a reference. HTTP, IIIF, `open_candidate`, `rightsReviewed`, credit or license text was not promoted into permission.

## Verification result

B6 independently re-read the integrated normative corpus and found zero residual P0/P1/P2 conflicts. B7 then ran the read-only deterministic verifier once:

```text
python3 scripts/verify_v49_rights_machine.py --json
```

It returned exit 0 with 216 checks and 0 failures. It revalidated all five frozen hashes, Prompt A gates/checksums, the candidate population and seven sequence/set hashes, the 71-row visual ledger, the 20-rule truth table, the 39-case negative oracle, stable URNs, optional visual-pair semantics and absence of legacy public terms. PID 18190 exited and was not restarted.

After the primary task added the executive/gate wrappers, manifest and checksums, it ran the same verifier over the closed package. That final invocation returned exit 0 with 219 checks and 0 failures, including 31 manifest artifacts and all 32 checksum entries. Its PID 19374 exited; the verifier wrote no file or database.

## Gate boundary

```text
AUTHORITY_RESEARCH_DELTA_CLOSED=true
RIGHTS_VISUAL_DECISIONS_LOCKED=true
MACHINE_CONTRACT_DECISIONS_LOCKED=true
DUAL_RELEASE_MODEL_LOCKED=true
TAKEDOWN_AND_CAS_RULES_LOCKED=true
LEGACY_VISUAL_REFERENCE_INVENTORIED=100%
LEGACY_VISUAL_REFERENCE_TYPED=100%
LEGACY_POSITIVE_RIGHTS_COVERAGE=0.0000%
UNCLASSIFIED_VISUAL_REFERENCE=0
RIGHTS_MACHINE_DECISION_PACKAGE=PASS
OVERALL_PRE_DDL_READY=false
DATABASE_IMPLEMENTED=false
FREEZE_READY=false
PROMOTION_READY=false
DEPLOYMENT_READY=false
```

`OVERALL_PRE_DDL_READY` remains false in this stage receipt because the user-required joint A+B verifier is executed only after the separately committed reversible runtime-cleanup stage. Cleanup cannot change this rights/machine gate.

## Actions explicitly not performed

No PostgreSQL, DDL, migration, data import/export/regeneration, Docker, npm install, Next.js server/build, TypeScript compile, browser, screenshot, HTTP/IIIF/provider probe, image download, API/OpenAPI/schema implementation, CI/deployment, frozen-asset/QA mutation, dirty-main mutation, PR, merge or deployment was performed in this decision stage.
