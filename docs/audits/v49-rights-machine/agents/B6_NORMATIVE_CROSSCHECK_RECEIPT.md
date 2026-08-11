# B6 — Independent normative terminology and cross-document receipt

- Agent task: v49 Phase 1D B6
- Worktree: `/Users/jarlgiovanni/Desktop/modern_GD_history_v49_data_platform`
- Branch: `refactor/v49-data-platform`
- Scope: independent read-only cross-check of B1–B5 against the existing v49 normative corpus
- Normative files modified by B6: **none**
- Implementation performed: **false**

## Task boundary

B6 owns only this receipt. It does not own or edit B1–B5 artifacts, the five root normative documents, the DDL decision pack, any ADR, frontend/package code, a frozen asset, QA evidence, a manifest/checksum, or a final joint-verifier receipt.

The check covers the required locked terms:

- five delivery modes and their structural exposure boundary;
- `rights.visual_locator` versus a technical endpoint observation;
- `rights.provider_policy_evaluation` and `rights.object_visual_reference`;
- the five independent rights/visual decision axes;
- independent research/visual release, seal, CAS and mismatch-window behavior;
- atomic nullable visual pair and research-only success;
- one public `visualRegistrySha256` field;
- positive serializer allowlists;
- stable `urn:gdarchive:*` identifiers with the historical `.example` seed-only exception;
- later API/schema/CI/deployment artifacts remaining non-DDL implementation gates.

## Assets read in full

### Phase 1D B1–B5

- `docs/audits/v49-rights-machine/01_P0_CROSSWALK.md`
- `docs/audits/v49-rights-machine/02_RIGHTS_VISUAL_MACHINE_DECISION_PACK_V49.md`
- `docs/audits/v49-rights-machine/03_VISUAL_ENTITY_CARDINALITY_MATRIX.md`
- `docs/audits/v49-rights-machine/04_RIGHTS_DELIVERY_TRUTH_TABLE.tsv` (header plus all 20 rules)
- `docs/audits/v49-rights-machine/05_LEGACY_VISUAL_DISPOSITION_BASELINE.tsv` (header plus all 71 compact groups)
- `docs/audits/v49-rights-machine/06_LEGACY_VISUAL_DISPOSITION_SUMMARY.json`
- `docs/audits/v49-rights-machine/07_DUAL_RELEASE_SEAL_CAS_SPEC.md`
- `docs/audits/v49-rights-machine/08_MACHINE_VISUAL_EXPOSURE_CONTRACT_V1.md`
- `docs/audits/v49-rights-machine/09_STABLE_ID_URI_POLICY.md`
- `docs/audits/v49-rights-machine/10_NEGATIVE_TEST_SPEC.md`
- B1, B2, B3, B4 and B5 agent receipts under `docs/audits/v49-rights-machine/agents/`

### Normative corpus

- `ARCHITECTURE.md`
- `DATA_MODEL_V49.md`
- `READ_API_V1.md`
- `MIGRATION_V48_TO_V49.md`
- `ACCEPTANCE_GATES.md`
- `docs/architecture/DDL_DECISION_PACK_V49.md`
- all four ADRs under `docs/adr/`

The corpus changed while B6 was running because the primary task was integrating Phase 1D terms. B6 therefore records the pre-integration conflict evidence below and separately records the frozen final scan that resolved it. B6 did not make those primary-document changes.

## Evidence commands

Representative local commands were:

```text
git status --short
find docs/audits/v49-rights-machine -maxdepth 2 -type f -print
wc -l <all named normative and B1–B5 files>
sed -n '<complete non-overlapping ranges>p' <all named files>
cat <bounded named files>
rg -n '<locked delivery/locator/policy/bridge/release/hash/URI/gate terms>' <normative corpus>
git diff -- <normative corpus>
git diff --check -- docs/audits/v49-rights-machine/agents/B6_NORMATIVE_CROSSCHECK_RECEIPT.md
```

No evidence command contacted a provider, network service, database writer, package registry, browser, or protected main path.

## Locked terminology matrix

| Concern | Required locked term or behavior |
|---|---|
| Delivery modes | Exactly `BLOCKED`, `CITATION_ONLY`, `LINK_ONLY`, `SOURCE_VIEWER`, `REMOTE_IMAGE`; `PIXEL_ALLOWED`, `WITHHELD`, `denied`, and open-ended governed-image mode prose are not competing effective modes. |
| Visual address | `rights.visual_locator` is the immutable typed locator occurrence. `endpoint_health_observation` is a time-bound technical observation for one locator; endpoint health is not locator identity or permission. |
| Provider policy | Immutable `provider_policy_version` evidence is evaluated by `provider_policy_evaluation` for one `object_visual_reference`; it remains separate from rights assessment and delivery. |
| Object ↔ visual | `rights.object_visual_reference` is the real-FK N:M bridge with natural key `(archive_object_id,external_visual_reference_id,reference_role)`. |
| Five axes | Rights evidence/assessment; provider-policy evidence/evaluation; delivery decision; endpoint health; takedown. Attribution is a separate positive-delivery prerequisite, not a rights state. |
| Dual release | Research and visual boundaries each use `draft → candidate → validated → sealed`, their own manifest/SHA/sidecar/current-CAS, no cross-mutation, no live-canonical drift. |
| Mismatch window | Research current may advance without a compatible visual current. That yields normal research-only data with locators absent. An explicitly requested incompatible visual pair is `409 RELEASE_VERSION_MISMATCH`; no fallback. |
| Response pair | `researchReleaseId + researchManifestSha256` is always present on successful research data. `visualRegistryVersion + visualRegistrySha256` is atomic and nullable. |
| Visual digest | `registrySha256` may remain the logical/database digest name only when explicitly mapped to the single public `visualRegistrySha256`; a serializer never emits both. |
| Serializer | Construct from an empty, schema-owned positive allowlist. `HELD`/`INTERNAL`/raw locators are structurally absent; lower modes cannot leak alternate pixel/thumbnail/image-service fields. |
| Stable identity | `urn:gdarchive:{object|relation|claim|source|visual-reference}:<uuid>` is domain-independent identity until a governed HTTPS origin exists. `.example` is allowed only as an exact historical UUIDv5 seed-name input and is never emitted/dereferenced as final identity. |
| Gate boundary | Identity/cardinality/state/version/serialization decisions block DDL. PostgreSQL implementation, actual Read API/OpenAPI/JSON Schema/JSON-LD/DCAT, CI/deployment, frontend adapter, production health service and browser QA are later gates. |

## Conflict ledger observed before primary integration

Each row names the exact integration delta visible when B6 read the pre-integration normative text. The frozen final scan below confirms that every `B6-C*` row has been resolved in the final working copy; the ledger remains evidence of what was checked rather than a list of current defects.

| ID | Priority | Path / section | Current or prior conflicting term | Required locked term / resolution |
|---|---|---|---|---|
| `B6-C01` | P0 | `docs/architecture/DDL_DECISION_PACK_V49.md` §9 | Delivery vocabulary `PIXEL_ALLOWED`, `LINK_ONLY`, `CITATION_ONLY`, `WITHHELD`; takedown forces `WITHHELD`. | Replace with the exact five-mode registry. Active takedown forces only `BLOCKED` or `CITATION_ONLY`; only `REMOTE_IMAGE` may emit the v1 remote pixel. |
| `B6-C02` | P0 | `docs/architecture/DDL_DECISION_PACK_V49.md` §§9–10 | No independent provider-policy-evaluation axis; visual receipt shorthand is provider/endpoint plus assessment/delivery/health. | Add `provider_policy_version/evaluation`, `object_visual_reference`, typed `visual_locator`, five-axis separation, and attribution/takedown prerequisites from B1/B2. |
| `B6-C03` | P0 | `docs/architecture/DDL_DECISION_PACK_V49.md` §10 | Public pair is written `(visualRegistryVersion,registrySha256)`; mismatch-window and normal research-only success are absent. | Map logical `registry_sha256` to public `visualRegistrySha256`; make the public visual pair atomic/nullable; distinguish current incompatibility/absence from an explicit incompatible selector. |
| `B6-C04` | P0 | `docs/architecture/DDL_DECISION_PACK_V49.md` §12 | Phase 1B graph/raw/license and executable machine-delivery evidence still appear as undifferentiated DDL blockers. | Recognize the Phase 1C closed authority/research receipt and the Phase 1D decision package; retain later implementation as pre-freeze/promotion gates, not empty-schema blockers. |
| `B6-C05` | P0 | `docs/adr/0004-research-claims-corpora-and-visual-registry.md` decisions 5–6 | Public `registrySha256`; heading “three orthogonal axes”; open-ended governed embed/thumbnail/local modes. | One public `visualRegistrySha256`; five independent records/axes; exact five delivery modes and truth-table precedence. |
| `B6-C06` | P0 | `docs/adr/0004-research-claims-corpora-and-visual-registry.md` decision 6 | Provider endpoints and URLs are described without the full `external_visual_reference` → `object_visual_reference` → typed `visual_locator` identity/cardinality. | Integrate B2 entities, natural keys/cardinalities, real-FK typed subjects/scopes and endpoint-health observation targeting one locator. |
| `B6-C07` | P0 | `docs/adr/0004-research-claims-corpora-and-visual-registry.md` decision 7 | `.example` HTTPS templates are presented as canonical object/relation/claim/release identities. | Canonical public class IDs use `urn:gdarchive:*`; future HTTPS is a governed resolver alias. Preserve `.example` only for exact historical UUIDv5 seed inputs. |
| `B6-C08` | P0 | `docs/adr/0004-research-claims-corpora-and-visual-registry.md` readiness | Old Phase 1B raw/license/graph evidence and actual machine artifacts remain mixed with logical DDL decisions. | Record Phase 1C closure, Phase 1D decision closure and defer OpenAPI/schema/JSON-LD/DCAT/CI/deployment/frontend/health/browser implementation to later readiness. |
| `B6-C09` | P0 | `docs/adr/0003-runtime-repository-and-fixture-mode.md` contract | `VisualRegistrySelector`, `VisualRegistryRef`, `ArchiveVersionRef.visual` and provider `open(...visual...)` are mandatory and expose `registrySha256`. | Visual selector/ref must be optional/nullable as an atomic `visualRegistryVersion + visualRegistrySha256` pair; registry absence is research-only success; explicit mismatch is typed. |
| `B6-C10` | P0 | `docs/adr/0003-runtime-repository-and-fixture-mode.md` composition | Rights assessment, delivery and endpoint health only; omission language filters modes after a presentation bundle exists. | Include provider-policy evaluation and takedown; define empty-object positive serializer allowlist and structural locator absence before serialization/cache. |
| `B6-C11` | P0 | `docs/adr/0002-immutable-data-versioning.md` decision/visual manifest | Provider objects/endpoints; three-state shorthand; consumer pair uses public `registrySha256`; no explicit research-current mismatch window. | Typed provider/reference/bridge/locator records; five axes; one public `visualRegistrySha256`; independent pointers may create an explicit fail-closed visual-unavailable window. |
| `B6-C12` | P0 | `docs/adr/0001-canonical-postgres-and-read-only-release.md` decision/authority rules | Consumer pair uses `registrySha256`; only rights assessment, delivery mode and endpoint health are named. | Map logical/public SHA names and preserve rights evidence, provider-policy evaluation, delivery, health and takedown separately. |
| `B6-C13` | P0 | `ACCEPTANCE_GATES.md` G6 | Requires both exact pairs and names public digest `registrySha256`. | Exact research pair is mandatory; visual pair is atomic/nullable and publicly named `visualRegistrySha256`; absence is normal research-only success. |
| `B6-C14` | P0 | `ACCEPTANCE_GATES.md` G7/G15 | Provider/IIIF endpoint identity and three axes; no complete B2 identity/cardinality or transient mismatch oracle. | Require typed visual locator, object bridge, provider-policy evaluation, five axes, separate seals/CAS, explicit mismatch window, takedown overlay and post-seal non-drift. |
| `B6-C15` | P0 | `ACCEPTANCE_GATES.md` G14 | Actual crawlable HTML, JSON Schema, JSON-LD, Linked Art/PROV-O, DCAT, diff feed and sitemap are bundled into “Architecture PASS,” making implementation absence look DDL-blocking. | Pre-DDL PASS covers stable IDs/URN mapping, exact version identity, field classes, positive allowlist, fail-closed exposure and negative oracle. Actual artifacts remain pre-freeze/pre-promotion implementation gates. |
| `B6-C16` | P1 | `ARCHITECTURE.md` invariants/layer table | Logical/public visual SHA is not distinguished; `rights` owns “typed endpoint roles.” | Say internal `registry_sha256` maps to public `visualRegistrySha256`; use typed visual locators while retaining endpoint health as the technical observation axis. |
| `B6-C17` | P1 | `MIGRATION_V48_TO_V49.md` M4/M7 | Prior shorthand used external visual provider/endpoints and public `registrySha256`; normal missing-compatible-registry behavior was absent. | Import raw locator roles into B2 identities/bridges without permission inference; public pair uses `visualRegistrySha256`; mismatch window yields research-only success and structural omission. |
| `B6-C18` | P1 | Cross-corpus serializer wording | Several documents only say “omit held pixels,” which can be implemented as null/filter/CSS hiding. | Require DTO construction from an empty positive allowlist; a forbidden field does not exist in API, Search, TRACE, HTML metadata, logs, cursors or public alternates. |
| `B6-C19` | P2 | Phase-specific gate prose | Some baseline status/commit-budget prose names Phase 1B even during a Phase 1D checkpoint. | Preserve historical status where clearly labeled, but final gate receipt must use Phase 1D authority/readiness and its authorized three-commit boundary. |

## B1–B5 internal consistency

### Blocking contradictions

No blocking B1–B5 contradiction was found in delivery precedence, typed FK identity, dual release/seal/CAS, public redaction, stable URNs, or negative-test outcomes.

The packages agree that:

1. first matching B1 truth-table precedence decides one of the five modes;
2. health cannot grant or widen authorization;
3. `object_visual_reference` is the N:M use boundary and `visual_locator` is separate from provider/reference identity;
4. the sealed research and visual projections are immutable, independently current-CAS controlled, and compatible only by exact declared pair;
5. active takedown is a monotonic restrictive overlay;
6. an absent compatible registry leaves the research record usable, while an explicitly incompatible selector is visible and has no fallback;
7. B4's public `visualRegistrySha256` is the public spelling of B2's logical `registrySha256`, not a fifth value;
8. only `REMOTE_IMAGE` can expose the v1 remote-pixel field, and B1/B4 both keep thumbnail/image-service fields absent in v1;
9. B3's measured 0.0000% positive-rights coverage is not inferred into a denial of future permission and is not a PASS threshold;
10. Search/TRACE/registry/API products cannot write back to canonical layers.

### Non-blocking clarifications to retain

| ID | Priority | Observation | Required interpretation |
|---|---|---|---|
| `B6-I01` | P1 | B2 §7 permits an explicit mismatch to be either a typed mismatch or research-only “according to endpoint contract,” while B4/B5 later lock explicit selector mismatch to `409`. | Treat B4/B5 as the narrower final endpoint behavior: missing/current-incompatible visual selection is research-only success; explicitly supplied incompatible pair is `409 RELEASE_VERSION_MISMATCH`. Normative documents must not preserve the earlier either/or. |
| `B6-I02` | P1 | B3 reports `rawStructuredEvidenceSurfaceBundles=15923` while mutually exclusive `closedStatusCounts.EVIDENCE_PRESENT=0`; its overall dispositions are instead 15,788 `RIGHTS_UNKNOWN` plus 135 `NO_VISUAL_REFERENCE`. | Do not read the zero as “no raw evidence observations.” The compact ledger preserves evidence-presence columns separately, while adjudicated rights remain unknown. A final executive/gate receipt should state this axis/precedence explicitly. |
| `B6-I03` | P2 | B2's deterministic external-reference UUID name begins `urn:graphic-design-archive:...`, while B4 public IDs use `urn:gdarchive:visual-reference:...`. | These are not aliases: the former is an exact internal UUIDv5 name input; the latter is the canonical public URN. Neither string grants rights or contains a locator. |

## Priority summary before final scan

| Priority | Count | Meaning |
|---|---:|---|
| P0 | 15 | Normative integration required before the independent pre-DDL verifier may pass. |
| P1 | 5 | Public/internal naming, serializer precision or interpretation clarification required. |
| P2 | 2 | Historical/namespace wording should remain explicit but does not alter keys/cardinality. |

Counts include `B6-C*` and `B6-I*` entries and are intentionally not a statement that B1–B5 failed. The P0s are primary-document integration deltas.

## Final frozen scan

The final scan re-read the integrated portions of all five root normative documents, the DDL decision pack and all four ADRs, then repeated exact negative and positive term scans across that entire corpus. It found no remaining normative conflict.

Final commands included:

```text
rg -n 'ENGINEERING_PRE_DDL_READY|RESEARCH_SEMANTICS_PRE_DDL_READY|RIGHTS_VISUAL_PRE_DDL_READY|MACHINE_CONTRACT_PRE_DDL_READY|OVERALL_PRE_DDL_READY' <normative corpus>
rg -n -i '<delivery/locator/policy/bridge/release/hash/URI/gate terms>' <normative corpus>
rg -n -P 'PIXEL_ALLOWED|WITHHELD|three\\s+(?:orthogonal\\s+)?axes|provider/endpoint|visual_endpoint|(?<!visual)registrySha256|https?://[^\\s`]*\\.example(?!/identity/v49/)' <normative corpus>
git diff --check -- docs/audits/v49-rights-machine/agents/B6_NORMATIVE_CROSSCHECK_RECEIPT.md
```

The last negative scan returned `NO_CONFLICTING_OCCURRENCES`. Historical references to Phase 1B remain only where explicitly labeled as historical audit/checkpoint evidence. The only normative `.example` values are the exact frozen UUIDv5 seed-name inputs in the DDL pack, accompanied by an explicit prohibition on emitting, resolving or treating them as final identity.

| Locked concern | Final evidence | Result |
|---|---|---|
| Delivery vocabulary | The exact five-mode set appears in architecture, data model, DDL pack, Read API, acceptance gates and rights ADRs. Only `REMOTE_IMAGE` may expose the v1 remote-pixel field. | PASS |
| Locator versus endpoint | `rights.visual_locator` is typed immutable identity; `endpoint_health_observation` targets a locator and cannot establish permission. No `visual_endpoint` pseudo-entity or provider/endpoint shorthand remains. | PASS |
| Provider policy and object bridge | `provider_policy_version/evaluation` and the real-FK N:M `object_visual_reference` bridge are present in the DDL/data/migration/acceptance contracts. | PASS |
| Five independent axes | Rights evidence/assessment, provider-policy evidence/evaluation, delivery, endpoint health and takedown are separately named; attribution remains a prerequisite rather than a sixth authorization state. | PASS |
| Dual release, seal, CAS and mismatch | Independent research/visual manifests, seals and current-pointer CAS are fixed; current mismatch yields research-only success and an explicit incompatible selector yields `409` without fallback. | PASS |
| Nullable visual pair | Successful research responses always carry the research pair; the visual pair is atomically present or null, with structural locator absence when unavailable. | PASS |
| Public visual digest | `visualRegistrySha256` is the single public spelling; internal `registry_sha256` is explicitly mapped and is not emitted as a competing alias. | PASS |
| Positive serializer | DTOs start from an empty schema-owned allowlist; held/internal/raw and non-`REMOTE_IMAGE` pixel/thumbnail/image-service locators are structurally absent. | PASS |
| Stable identity | Canonical class IDs use `urn:gdarchive:*`; future HTTPS routes are governed aliases; `.example` is limited to the exact frozen seed recipe. | PASS |
| Gate separation | The DDL pack, ADR 0004, Read API and acceptance gates state that API/OpenAPI/schema/JSON-LD/DCAT/CI/deployment/frontend/health/browser implementation is later pre-freeze/pre-promotion work and does not reopen physical-schema decisions. | PASS |
| Five readiness dimensions | Architecture, the DDL pack, ADR 0004 and acceptance gates name engineering, research semantics, rights/visual, machine contract and overall readiness separately; B6 does not set their joint result. | PASS |

Resolution accounting:

```text
PRE_INTEGRATION_P0=15
PRE_INTEGRATION_P1=5
PRE_INTEGRATION_P2=2
RESOLVED_B6_C_ROWS=19
NORMATIVE_RESIDUAL_P0=0
NORMATIVE_RESIDUAL_P1=0
NORMATIVE_RESIDUAL_P2=0
B1_B5_NONBLOCKING_INTERPRETATION_NOTES=3
B1_B5_BLOCKING_INTERNAL_CONTRADICTIONS=0
```

The three `B6-I*` notes are not unresolved normative conflicts: final documents arbitrate missing/current-incompatible visual selection versus explicit selector mismatch, preserve evidence-presence separately from adjudicated disposition, and distinguish deterministic UUID seed names from public URNs. They remain in this receipt so downstream verifiers can test those boundaries directly.

## Actions explicitly not performed

- no edit to a normative file or another agent's artifact;
- no PostgreSQL, SQLite, DDL, migration, import, export, Docker, npm, Next.js, TypeScript, browser or screenshot;
- no network, HTTP/IIIF/provider probe, image download, pHash, blurhash or media processing;
- no frontend/package/CI/deployment/frozen-asset/QA/protected-main modification;
- no commit, push, force push, PR, merge or deployment.

## Residual processes

B6 started no server, compiler, browser, database, package installer, data generator or background process. All B6 read commands completed synchronously. Repository-wide process ownership remains with the primary task.

## Exit status

```text
B6_STATUS=PASS
B1_B5_BLOCKING_INTERNAL_CONTRADICTIONS=0
PRIMARY_NORMATIVE_INTEGRATION_PENDING=false
NORMATIVE_TERMINOLOGY_CONSISTENT=true
DELIVERY_MODE_VOCABULARY_CONSISTENT=true
VISUAL_LOCATOR_ENDPOINT_BOUNDARY_CONSISTENT=true
FIVE_AXIS_MODEL_CONSISTENT=true
DUAL_RELEASE_CAS_MISMATCH_CONSISTENT=true
NULLABLE_VISUAL_PAIR_CONSISTENT=true
PUBLIC_VISUAL_SHA_FIELD_CONSISTENT=true
POSITIVE_SERIALIZER_ALLOWLIST_CONSISTENT=true
STABLE_URN_POLICY_CONSISTENT=true
LATER_IMPLEMENTATION_NOT_DDL_BLOCKER=true
NORMATIVE_FILES_MODIFIED_BY_B6=0
IMPLEMENTATION_PERFORMED=false
RESIDUAL_B6_PROCESS=0
```
