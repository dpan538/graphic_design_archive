# Context Governance Policy v1

`CONTEXT_GOVERNANCE_POLICY_VERSION=context-governance-v1`

## Scope and source hierarchy

The policy governs the public Context projection derived from the frozen v49 research release. Eligibility comes only from the authoritative public/held surface ledger. Typed medium, theme, and movement source rows supply candidate classifications. The frozen source state remains `proposed`; Context publication is a separate derived decision.

## Allowed kinds and decisions

Allowed Context kinds are `medium`, `theme`, and `movement_context`. Publication decisions are `PUBLISHED`, `QUALIFIED`, `HELD`, `EXCLUDED`, and `DEFERRED_TO_OTHER_DOMAIN`. Context V1 publishes the audited medium, theme, and movement candidates as project-curated context. Region is deferred to Spacetime.

## Identity

Term IDs are deterministic, kind-bound hashes of private source identity under the stable Context public-ID policy. Labels do not define identity. Representation IDs are deterministic hashes of public surface ID, Context kind, and governed term ID. Neither ID reveals a private folder token, UUID, source locator, array position, or validation-only `ctxv49:` identifier. Explanatory-copy and mapping-policy versions are stored separately so copy changes do not churn identity.

## Explainability and provenance

Every visible representation resolves exactly one registered explanation and a safe provenance record. The explanation identifies meaning, why the representation is shown, source basis, derivation, epistemic role, publication state, permitted interpretation, prohibited interpretations, connection wording, accessibility wording, and policy version. Provenance exposes the basis `project_curated_typed_membership`, source kind, frozen source state `proposed`, mapping version, governance version, and decision—never internal folder identity.

## Eligibility, held exclusion, and missingness

Only the 7,995 ledger-eligible public records may enter the projection. Held records and syntactically valid unknown IDs return indistinguishable not-found responses. An eligible record remains valid even if a future representation is held; publication coverage and object eligibility are separate decisions. Missingness must be explicit and must never be repaired from held rows or inferred labels.

## Multi-value and ambiguity handling

Multiple same-kind values are preserved when source identity and mapping are valid. The one two-theme grouped record and five two-movement records remain multi-valued; no value is coerced or merged. Ambiguity is never guessed: use `QUALIFIED` or `HELD` where the limited project-curation statement is unsafe. Vocabulary merges require an explicit registered decision and evidence.

## Review and exceptions

The review combines exhaustive automated identity, label, eligibility, state, determinism, and collision checks with manual review of all 25 terms, every multi-value case, movement terms and structures, abnormal labels, near concepts, and prohibited-inference risks. Non-standard decisions belong in the exception register, not label blacklists or hidden code branches.

## Versioning and supersession

The policy, mapping, explanation registry, exception register, term registry, and source hashes are bound in the projection manifest. Any semantic or identity-policy change requires a new governed projection version. The source v49 database and research release identity do not change.

## Prohibited inference

Context publication does not establish historical relation, influence, causation, contact, lineage, chronology, original archival order, creator intent, objective taxonomy, historical importance, or definitive movement membership. Shared Context between records does not establish a relation between those records.
