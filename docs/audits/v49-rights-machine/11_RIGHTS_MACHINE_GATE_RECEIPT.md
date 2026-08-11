# 11 — Rights, visual-registry and machine-contract gate receipt

- Package: v49 Phase 1D, decision stage
- Initial commit: `967cbe34a8f30f8e74fa117e1bdee74644f71afe`
- Frozen ancestor: `0404c7f96f9189f576c4c5b1368061e4082e436b`
- Prompt A prerequisite: **PASS**
- Independent normative cross-check: **PASS**
- Deterministic package verifier: **PASS**
- PostgreSQL/API/runtime implementation: **NOT PERFORMED**

## Gate contract

This receipt closes the remaining rights, visual-registry and public-machine-contract decisions needed to specify physical keys, foreign keys, state vocabularies, release snapshots and serializer suppression. It does not claim that those decisions have been implemented. Unknown rights, policy, provider or health information remains typed and fail-closed; it is never silently upgraded.

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
ENGINEERING_PRE_DDL_READY=false
RESEARCH_SEMANTICS_PRE_DDL_READY=false
RIGHTS_VISUAL_PRE_DDL_READY=false
MACHINE_CONTRACT_PRE_DDL_READY=false
OVERALL_PRE_DDL_READY=false
DATABASE_IMPLEMENTED=false
FREEZE_READY=false
PROMOTION_READY=false
DEPLOYMENT_READY=false
```

The five pre-DDL readiness fields stay false in this decision-stage receipt only because the user-required independent joint A+B verifier runs after the separately committed reversible-cleanup stage. That later verifier may set them true if it finds no remaining authority, identity, cardinality, state, version, serialization or classification contradiction. Missing API/OpenAPI/JSON Schema/JSON-LD/DCAT, CI, deployment, browser evidence and frontend Repository integration are later implementation gates and cannot by themselves keep physical-schema specification blocked.

## Measured evidence

| Gate | Evidence | Result |
|---|---|---|
| Prompt A closure | Phase 1C manifest/checksum plus authority verifier | PASS; parity true, unaccounted input 0, unclassified graph/raw facts 0 |
| Canonical candidate | byte hash and 15,923 surface bundles | PASS; exact frozen SHA-256 |
| Legacy visual inventory | compact 71-row deterministic ledger | PASS; 15,923 accounted, 0 unaccounted |
| Reference classification | 15,788 reference-bearing plus 135 no-reference bundles | PASS; typed 100%, unclassified 0 |
| Locator units | 15,790 occurrences / 15,788 distinct values | PASS; no deduplication or permission inference |
| Positive-rights coverage | adjudicated evidence + versioned permitting policy + attribution + no restrictive condition | PASS as measurement; 0 / 15,788 = 0.0000% |
| Five rights/delivery axes | evidence, provider policy, delivery decision, endpoint health, takedown | PASS; distinct entities/states |
| Delivery lattice | 20 ordered rules and five closed modes | PASS; one positive `REMOTE_IMAGE` rule, terminal fail-closed rule |
| Dual releases | independent manifests, seals, sidecars and current-pointer CAS | PASS as locked decision |
| Machine redaction | version pairs, stable URNs, positive allowlist and structural locator omission | PASS as locked decision |
| Negative oracle | 39 uniquely identified cases | PASS as specification |
| Normative consistency | B6 complete re-read and stale-term scan | PASS; residual P0/P1/P2 = 0/0/0 |
| Deterministic verifier | `python3 scripts/verify_v49_rights_machine.py --json` | PASS; detached 216 checks and closed-package 219 checks, 0 failures |

## Locked fail-closed boundary

1. Active takedown restricts to `BLOCKED` or `CITATION_ONLY` and overrides every positive input.
2. Missing, unknown, conflicting or stale rights evidence restricts to `LINK_ONLY` or `CITATION_ONLY`.
3. Provider viewer-only policy restricts to `SOURCE_VIEWER` or `LINK_ONLY`.
4. Endpoint health can only degrade delivery; it can never establish or elevate permission.
5. Only the conjunction of adjudicated permission, a permitting versioned provider policy, complete attribution and qualified health can yield `REMOTE_IMAGE`.
6. Any mode below `REMOTE_IMAGE` structurally omits pixel, thumbnail and image-service locator fields from the public DTO.
7. Held/internal/raw locators are never copied into a public serializer input.
8. Registry absence yields a valid research-only record; an explicit incompatible selector yields `409 RELEASE_VERSION_MISMATCH` with no locator fallback.
9. Post-seal mutation and stale current-pointer CAS fail; a takedown overlay remains more restrictive than sealed evidence.
10. Derived Search/TRACE products cannot create canonical rows, claims, relations or visual references.

## Authority and release boundary

PostgreSQL will be the normalized working database. A sealed research release and a sealed visual-registry version are separate immutable copied projections. Each has its own manifest, SHA-256, detached sidecar and CAS-protected mutable `current` pointer. Advancing either pointer does not mutate or silently inherit the other release. Third-party pixel URLs are excluded from the research release canonical-fact layer.

## Reproduction boundary

```text
python3 scripts/verify_v49_authority_research_delta.py --json
python3 scripts/verify_v49_rights_machine.py --json
git diff --check
```

Both verifiers are deterministic, read-only and network-free. The rights verifier reads the frozen candidate, reconciliation evidence, Prompt A package and Phase 1D decision artifacts. It does not write a database, frozen asset, visual registry or frontend file.

## Actions explicitly not performed

No PostgreSQL/DDL, migration, data import/export/regeneration, Docker, npm install, Next.js server/build, TypeScript compile, browser, screenshot, third-party HTTP/IIIF probe, image download, API/OpenAPI/schema implementation, CI/deployment, frozen-data/QA mutation, dirty-main mutation, PR, merge, force operation or deployment was performed in this stage.
