# B2 — Visual entity and dual-release receipt

- Agent task: Phase 1D B2
- Worktree: `/Users/jarlgiovanni/Desktop/modern_GD_history_v49_data_platform`
- Branch: `refactor/v49-data-platform`
- Scope status: **PASS**
- Implementation performed: **false**

## Task boundary

B2 was limited to the logical identities, real-FK cardinalities, independent research/visual immutable boundaries, state/seal/sidecar/current-CAS protocols, compatibility/mismatch behavior, takedown overlay interaction, and role/`SECURITY DEFINER` boundary.

B2 did not own the measured legacy visual-disposition TSV, final rights truth table, machine serializer field contract, stable public URI policy, negative-test package, normative-document edits, cleanup, or joint verifier.

## Assets read in full for this scope

- `ARCHITECTURE.md`
- `DATA_MODEL_V49.md`
- `READ_API_V1.md`
- `MIGRATION_V48_TO_V49.md`
- `ACCEPTANCE_GATES.md`
- `docs/architecture/DDL_DECISION_PACK_V49.md`
- `docs/adr/0002-immutable-data-versioning.md`
- `docs/adr/0004-research-claims-corpora-and-visual-registry.md`
- Phase 1C executive, authority, corpus, TRACE delta, gate receipt and manifest evidence under `docs/audits/v49-authority-research-delta/`
- `docs/audits/v49-pre-migration/06_RIGHTS_AND_VISUAL_FEDERATION.md`
- `docs/audits/v49-pre-migration/10_MACHINE_API_SECURITY_CI_DEPLOYMENT.md`

## Evidence commands

All commands were local and read-only except the four scoped `apply_patch` outputs:

```text
git status --short --branch
rg --files <bounded architecture/ADR/audit patterns>
wc -l <bounded architecture/ADR/audit files>
du -h docs/audits/v49-authority-research-delta/*
sed -n <complete non-overlapping ranges> <required documents>
find docs/audits/v49-rights-machine -maxdepth 2 -type f -print
git diff --check -- <four B2 paths>
```

No URL or secret value was requested or printed.

## Locked findings

1. The external visual reference is a provenance-bound identity, not a URL, downloaded representation, archive object, permission, health result, or delivery state.
2. Archive object ↔ external visual reference is N:M through a typed FK bridge; it cannot reverse-create the 15,923 baseline objects.
3. Provider, provider object, locator role, rights observation/assessment, provider-policy version/evaluation, delivery decision, health observation, attribution, takedown event/scope/override all have separate identities.
4. Rights-observation subjects, assessment subjects, and takedown scopes use closed exactly-one typed subtype families with real FKs. Arbitrary `target_type + target_id` is prohibited.
5. PostgreSQL is the normalized working database; sealed research and visual boundaries are copied immutable projections and never live canonical views.
6. A visual registry is compatible with exactly one research pair. A research release can have many independently updated visual versions.
7. Research current and visual current use separate CAS histories. Research may advance into an explicit visual-mismatch window; old visual permission is never inherited.
8. Third-party pixel-bearing locators are excluded from the research release and from any fail-closed visual entry.
9. Active takedown is an append-only restrictive overlay, wins over sealed decisions, and requires a new visual version without rewriting sealed bytes.
10. Seal, CAS, observation, decision, and takedown functions have distinct role grants and cannot cross-mutate boundaries.

## Coordination

B1 reported the closed delivery modes `BLOCKED`, `CITATION_ONLY`, `LINK_ONLY`, `SOURCE_VIEWER`, and `REMOTE_IMAGE` plus the rule that endpoint health never widens authorization. B2 uses the same vocabulary and separates provider-policy evaluation from rights assessment.

## Files changed

- `docs/audits/v49-rights-machine/02_RIGHTS_VISUAL_MACHINE_DECISION_PACK_V49.md`
- `docs/audits/v49-rights-machine/03_VISUAL_ENTITY_CARDINALITY_MATRIX.md`
- `docs/audits/v49-rights-machine/07_DUAL_RELEASE_SEAL_CAS_SPEC.md`
- `docs/audits/v49-rights-machine/agents/B2_VISUAL_ENTITY_DUAL_RELEASE_RECEIPT.md`

No normative architecture document or any other path was edited by B2.

## Explicitly not performed

- no PostgreSQL, DDL, migration, database connection, data import/export, or frozen-asset change;
- no npm, Next.js, TypeScript, browser, screenshot, Docker, network, HTTP/IIIF probe, image download, pHash, blurhash, or derivative;
- no provider permission inference, positive-rights adjudication, automatic URL/provider mapping, deduplication, merge, or delimiter split;
- no frontend, package, CI, deployment, QA image, dirty-main, commit, push, PR, merge, or deploy action.

## Remaining integration work

- B3 must establish the 100% typed legacy baseline; B2 does not substitute prior SQLite URL counts for that proof.
- B4/B5 must lock public serialization/redaction and executable negative-test oracles.
- The primary task must reconcile terminology into normative documents and run the independent joint verifier.
- Physical DDL and all implementation evidence remain future work.

## Exit fields

```text
B2_STATUS=PASS
VISUAL_ENTITY_IDENTITIES_LOCKED=true
VISUAL_ENTITY_CARDINALITIES_LOCKED=true
DUAL_RELEASE_MODEL_LOCKED=true
TAKEDOWN_AND_CAS_RULES_LOCKED=true
ARBITRARY_POLYMORPHIC_TARGET_PROHIBITED=true
DATABASE_IMPLEMENTED=false
RESIDUAL_B2_SHELL_SESSION=0
```
