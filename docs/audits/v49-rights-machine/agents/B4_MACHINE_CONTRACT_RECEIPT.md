# B4 — Machine contract and redaction receipt

- Agent task: v49 Phase 1D B4
- Worktree: `/Users/jarlgiovanni/Desktop/modern_GD_history_v49_data_platform`
- Branch: `refactor/v49-data-platform`
- Scope result: **PASS**
- Implementation performed: **false**

## Task boundary

B4 owned only:

- `docs/audits/v49-rights-machine/08_MACHINE_VISUAL_EXPOSURE_CONTRACT_V1.md`;
- `docs/audits/v49-rights-machine/09_STABLE_ID_URI_POLICY.md`;
- this receipt.

B4 did not edit a normative architecture document, frontend/package file, frozen asset, QA file, visual baseline, truth table, negative-test package, database, API, schema, CI, deployment, manifest, or checksum.

## Assets read

B4 read the current v49 root architecture/data/API/migration/acceptance documents, the DDL decision pack, all four ADRs, the Phase 1C gate receipt/manifest/checksums, Phase 1B A6 and A10, and all available Phase 1D B1/B2 outputs in full. B4 also checked the B3 output area during the task; B3 owns its measured baseline and B4 does not use a visual count as a serialization permission.

## Evidence commands

Representative local read-only commands were:

```text
git status --short --branch
rg --files <bounded normative/audit paths>
wc -l <required documents>
sed -n '<complete non-overlapping ranges>p' <required documents>
```

Scoped validation commands after authoring:

```text
rg -n '<version/URI/locator/reason-code terms>' <B4-owned files>
git diff --check -- <B4-owned files>
git diff --name-only -- <B4-owned files>
```

No command contacted a network endpoint or printed a secret/provider payload.

## Locked findings

1. Every successful reproducible research response exposes `researchReleaseId`, `researchManifestSha256`, `visualRegistryVersion`, and public `visualRegistrySha256`; the visual pair is atomically non-null or atomically null.
2. B2's internal/logical `registrySha256` denotes the same digest. The public serializer has one field name and no competing fifth value.
3. Registry absence is a normal research-only success. An explicit incompatible visual pair is a typed `409 RELEASE_VERSION_MISMATCH`; neither case falls back to another registry.
4. Objects, semantic relations, claims, citable sources, and external visual references have immutable class-specific UUID/URN identity independent of release and deployment hostname.
5. `.example` strings in the historical UUIDv5 recipe remain exact non-resolvable seed names. `.example` templates are prohibited as final public identifiers.
6. The public serializer constructs DTOs from an empty positive allowlist. `SAFE`, conditional `PUBLIC`, `INTERNAL`, and `HELD` are closed classes; unknown fields are non-public.
7. Held/raw/internal locators never enter a public response, problem, log, Search/TRACE payload, HTML metadata, JSON-LD, sitemap, cursor, or visual-registry public asset.
8. Only `REMOTE_IMAGE` may emit `remoteImageUrl`; lower modes structurally omit pixel, thumbnail, and image-service fields. Current v1 also omits thumbnail/service fields in `REMOTE_IMAGE`, matching the B1 truth table.
9. Rights, provider policy, attribution, endpoint health, and takedown remain independent. Health can retain or lower exposure but never grant it.
10. Public `/api/v1` is GET/HEAD/OPTIONS-only and cannot trigger provider fetches, image proxying, ingestion, review, seal, CAS, export, or derived-to-canonical writes.

## Priority findings

| Priority | Finding | Disposition |
|---|---|---|
| P0 | Existing normative public key `registrySha256` conflicts with the user-required `visualRegistrySha256` machine field unless mapped explicitly. | B4 locks one public field and an exact internal mapping; primary normative integration must use one vocabulary. |
| P0 | Existing `.example` canonical/problem URI templates can be misread as final. | Replaced by domain-independent project URNs; historical UUID seed text is preserved and explicitly non-resolvable. |
| P0 | Registry absence and mismatch were previously allowed to vary by endpoint. | Locked to research-only success for absence and typed 409 for an explicit mismatch. |
| P0 | Field redaction by UI/CSS is insufficient. | Locked structural omission and positive serializer allowlist before cache/serialization. |
| P1 | Active takedown changes the effective response beyond sealed four-field identity. | Added required overlay digest when an override affects exposure. |
| P1 | Exact API selector transport and executable schemas remain absent. | Correctly deferred to implementation; not a reopened DDL decision. |
| P2 | HTTPS resolver origin is unknown. | URNs are canonical now; origin adoption has a later fail-closed rule. |

## Unresolved implementation items

PostgreSQL DDL, actual Read API, OpenAPI, JSON Schema, JSON-LD, Linked Art/PROV-O, DCAT, canonical HTML, sitemap/robots, diff/change feed, CI, deployment, frontend Repository integration, production endpoint-health checks, resolver hosting, and browser/rights-leakage tests are not implemented. Their absence keeps later readiness false but does not reopen the pre-DDL identity/state/version/serialization decisions in B4.

The primary task still owns normative-document harmonization, B3/B5 cross-consistency, package manifest/checksums, cleanup, final joint verification, Git commits, push, protected-main comparison, and residual process scan.

## Explicitly not performed

No network, HTTP/IIIF/image request, provider probe, image download, PostgreSQL, SQLite, Docker, npm, Next.js, TypeScript, browser, screenshot, data import/export, migration, API/schema/fixture implementation, frontend/package/CI/deployment change, frozen-asset/QA edit, protected-main mutation, commit, push, PR, merge, or deploy was performed.

## Residual processes

B4 started no server, compiler, browser, database, package installer, data generator, network request, or background process. All B4 shell commands completed synchronously. Final OS-wide process ownership remains with the primary task.

## Exit fields

```text
B4_STATUS=PASS
MACHINE_CONTRACT_DECISIONS_LOCKED=true
STABLE_ID_URI_POLICY_LOCKED=true
REGISTRY_ABSENT_RESEARCH_USABLE=true
EXPLICIT_VERSION_MISMATCH=true
PUBLIC_SERIALIZER_POSITIVE_ALLOWLIST=true
HELD_LOCATOR_PUBLIC_COUNT=0
PUBLIC_API_MUTATION_METHOD_COUNT=0
IMPLEMENTATION_PERFORMED=false
RESIDUAL_B4_PROCESS=0
```
