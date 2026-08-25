# Project log

This active log is a compact index of release-level decisions. The complete pre-hygiene implementation log remains immutable at tag `v49-data-api-closure-20260821` and can be read with:

```bash
git show v49-data-api-closure-20260821:PROJECT_LOG.md
```

## v49 release state — 2026-08-21

- Source closure commit: `d78f496bcdf2cd6941791986007cd7a885c4c532`.
- Source tree: `f0549c319d1e0b0cf5e0aab5a2b297361675b701`.
- Immutable annotated tag: `v49-data-api-closure-20260821`.
- Schema SHA-256: `df1e7741e59e5e6bf1ca80f2a33edfad1abb2fc6d95b57d4d6993b49917020dd`.
- Release projection digest: `11d92b70bd3a87113d4daabac2b5e4e38a3416cc55be894b42b0dd3d072ca640`.
- Canonical objects / proposed curated folder-membership assignments: 15,923 / 47,982.
- Eligible / held: 7,995 / 7,928.
- Accepted TRACE / positive visual rights: 0 / 0.
- Public Read API templates: 18; all tested with no 5xx/search 503.

## Current decisions

- `database/` is the only active database root; legacy `db/` is source-tag history only.
- v49 database implementation and canonical inputs are frozen byte-for-byte.
- `generated/public_surfaces_prefreeze_candidate_v48.json` is the sole canonical population input.
- SQLite/search/TRACE/manifests remain reconciliation-only and cannot repair canonical state.
- The browser never connects directly to PostgreSQL; `api_v1`/release-derived reads form the public boundary.
- Historical raw captures, backups, pre-v49 generated output, prompts, reports, and unrelated archive material are recoverable by immutable ref rather than duplicated in the active tip.
- Future database changes require v50+, a new forward-only migration, and an ADR.

## Current indexes

- Release: `docs/releases/v49/RELEASE_INDEX.md`
- Data retention: `docs/releases/v49/DATA_RETENTION.md`
- Audits: `docs/releases/v49/AUDIT_INDEX.md`
- Repository layout: `docs/maintenance/REPOSITORY_LAYOUT.md`
- Retention policy: `docs/maintenance/RETENTION_POLICY.md`
- Database freeze: `database/FROZEN_V49.md`
- Read API: `docs/api/v49-read-api-catalog.md`

## TRACE interface direction — 2026-08-23

### Context Canvas

- Confirmed as the first TRACE implementation: an ERD-style interactive research canvas with typed entities and typed connections.
- Initialize from deterministic templates; provide a sidebar entity palette, drag/add, automatic connections from validated context data, pan/zoom/reposition, auto-layout, inspector, and PNG export.
- Do not permit manual historical-relation creation. Canvas and layout edits are local composition only; canonical data remain read-only.
- Final typography, color, spacing, visual language, and component styling are deferred to the later frontend redesign.

### Spacetime

- Confirmed as the second TRACE direction: map-first, with exactly one selected time layer/bucket at a time for v1 and a discrete selector rather than autoplay.
- Use governed aggregate geographic marks; selecting geography reveals matching recorded objects.
- Parameter inventory and geography/time governance are next. No map implementation belongs in this round.

### Exploration Field

- Confirmed as the third TRACE research direction: a non-object-facing conceptual relation inspiration field for composing nodes, flows, clusters, and persistent tree-map topology.
- The primary unit is `CONCEPTUAL_RELATION_NODE`. Exploration exposes zero archive objects and accepts no Context, Spacetime, object metadata, similarity, affinity, recommendation, or object-ranking input.
- Seeded deterministic composition may choose only among governed conceptual structures. It cannot invent vocabulary, evidence, or historical facts. Renderer and relation vocabulary remain future work.

### Context Canvas real-data validation — 2026-08-23

- Real-data validation uses the audited 7,995-object public cohort while retaining proposed candidate states; it is validation-only, not a governed public TRACE release, and introduces no accepted semantic edges.

### Context V1 governance closure — 2026-08-23

- Context V1 is frozen as a release-derived `project_curated_context` read model: it describes how the archive project classifies a selected public record and does not publish historical relations, influence, causation, creator intent, chronology, or definitive movement membership.
- The governed projection `trace-context-v1` contains 25 controlled terms and 16,106 published representations for all 7,995 eligible public records. Frozen source rows remain `proposed`; publication is a separate Context governance decision.
- Governed Canvas defaults to the selected record plus controlled medium, theme, and movement-context representations. Curated memberships are provenance only; default membership nodes/connections and real semantic edges are zero.
- Context has an additive release-pinned public Read API and compact server-only projection. The route remains unlinked and `noindex`; final visual design and public navigation are deferred.
- Region is excluded from Context and handed to Spacetime parameter governance. No map/time implementation is included.

### Context runtime + Spacetime functional foundation — 2026-08-23

- Context V1 runtime behavior is rehearsed and frozen: the Context API dispatches through its compact governed projection without loading the Search index, SQLite, or the generic archive repository in the normal Context path.
- Spacetime V1 governs all 7,996 public typed-region assignments across the 7,995-record public cohort, with explicit mapped, aggregate-only, and display-unmapped outcomes. It publishes recorded project context only; it does not assert object coordinates, historical presence, movement, influence, or semantic relations.
- The functional foundation uses a checksum-bound Natural Earth Admin 0 Countries 50m artifact, an Equal Earth default projection, deterministic aggregate marks, 23 decade buckets, and release-pinned server API reads. Final visual design, public navigation, and visual acceptance remain deferred.
- Exploration Field is independent from Context and Spacetime. Their projections are not semantic inputs to Exploration.

### Historical Exploration data-discovery research — superseded 2026-08-25

- Spacetime V1 engineering logic is frozen after production-runtime rehearsal, exhaustive period/geography validation, deterministic renderer parity, cache and stale-request hardening, and functional browser acceptance. Final visual design and public navigation remain deferred.
- The Round 5 data-discovery package remains immutable historical evidence only. Its object/metadata signals are not an active Exploration architecture or input.
- Context and Spacetime engineering closures remain frozen and authoritative for their own TRACE functions.

### Historical Exploration affinity research Round 1 — superseded 2026-08-25

- `CG-CUR-4`, `M2`, `M5`, and `M7` are `SUPERSEDED_NON_AUTHORITATIVE_EXPLORATION_RESEARCH`.
- The sealed Round 6 research and audit packages remain evidence that object-centric similarity was investigated and rejected. They are not current architecture, future renderer input, a model shortlist, or a human-review next step.

### Historical Exploration NLP semantic corpus audit Round 1 — superseded 2026-08-25

- The sealed Round 7 research and audit packages remain useful evidence of source/provider leakage, absent governed object-description text, absent semantic ground truth, and absent verified multilingual pairs.
- The entire object-title, object-subject, source-narrative, lexical-neighbor, dense-neighbor, and structured/NLP fusion direction is `SUPERSEDED_NON_AUTHORITATIVE_EXPLORATION_RESEARCH`.
- No external semantic model is approved. Active model download, inference, registry, encoder, checkpoint, vector-index, and selection surfaces have been removed.

ROUND7_OBJECT_NLP_STATUS=SUPERSEDED_NON_AUTHORITATIVE_EXPLORATION_RESEARCH

ROUND7_NLP_EVIDENCE_RETENTION=SEALED_HISTORICAL_ONLY

PROJECT_LOG_UPDATED=true

CONTEXT_STATUS=FROZEN

SPACETIME_STATUS=FROZEN

`CONTEXT_CANVAS_FUNCTIONAL_CORE=COMPLETE`

`CONTEXT_CANVAS_REAL_DATA_VALIDATION=ACTIVE`

`CONTEXT_V1=GOVERNED_DATA_AND_READ_MODEL_READY`

`CONTEXT_CANVAS_FINAL_VISUAL_DESIGN=DEFERRED`

`CONTEXT_V1_RUNTIME_REHEARSAL=PASS`

`CONTEXT_V1_ENGINEERING_LOGIC=FROZEN`

`SPACETIME=GOVERNED_FUNCTIONAL_FOUNDATION_READY`

`SPACETIME_GIS_GOVERNANCE=PASS`

`SPACETIME_TIME_GOVERNANCE=PASS`

`SPACETIME_FUNCTIONAL_FOUNDATION=PASS`

`SPACETIME_VISUAL_DESIGN=DEFERRED`

`SPACETIME_ENGINEERING_LOGIC=FROZEN`

`SPACETIME_RUNTIME_REHEARSAL=PASS`

`SPACETIME_FINAL_VISUAL_DESIGN=DEFERRED`

`EXPLORATION_FIELD=CONCEPTUAL_RELATION_INSPIRATION_FIELD`

`EXPLORATION_OBJECT_CENTRIC_BRANCH=SUPERSEDED`

`EXPLORATION_OBJECT_NLP_BRANCH=SUPERSEDED`

`EXPLORATION_PRIMARY_UNIT=CONCEPTUAL_RELATION_NODE`

`EXPLORATION_FRONTEND_OBJECT_EXPOSURE=ZERO`

`EXPLORATION_SIMILARITY=PROHIBITED`

`EXPLORATION_RECOMMENDATION=PROHIBITED`

`EXPLORATION_OBJECT_RANKING=PROHIBITED`

`EXPLORATION_CONTEXT_INPUT=PROHIBITED`

`EXPLORATION_SPACETIME_INPUT=PROHIBITED`

`EXPLORATION_EXTERNAL_MODEL_POLICY=DENY_BY_DEFAULT`

`EXPLORATION_APPROVED_EXTERNAL_MODEL_COUNT=0`

`EXPLORATION_RELATION_VOCABULARY=RESEARCH_NEXT`

`EXPLORATION_RELATION_GRAMMAR=RESEARCH_NEXT`

`EXPLORATION_IMAGE_CONTRACT=DEFINED`

`EXPLORATION_INSTANCE_CONTAINER_CONTRACT=DEFINED`

`EXPLORATION_RENDERER=NOT_IMPLEMENTED`

`EXPLORATION_PUBLIC_ROUTE=NOT_IMPLEMENTED`

`FINAL_TRACE_VISUAL_DESIGN=DEFERRED`

## TRACE v49 Round 9 — design-history relation vocabulary discovery Round 1

- Built a 50-work scholarly corpus across all eight required source strata without archive objects, object titles, Context, Spacetime, or external research models.
- Froze 33 exact noun or nominal-phrase candidates as `trace-design-history-relation-candidates-v1` with SHA-256 `818b306406d6a557a563ec285ae36394106c4c88a3e14cae19e4f1da4e92f4d5` before verification.
- Completed all five required roles for every candidate: 165 matrix rows, zero incomplete candidates, and no sampling.
- Passed 16 source-bounded research senses to the Round 10 handoff, deferred 12, and rejected 5. Four polysemous nouns remain split and deferred; no synonym merge was authorized.
- Validated all 16 passing glosses in ordinary language with three independent comprehension checks and an adversarial review.
- Preserved the active Exploration domain at zero relation types. No grammar, renderer, route, API, database, Search, Context, or Spacetime change was made.

`ROUND9_RELATION_VOCABULARY_DISCOVERY=COMPLETE`

`ROUND9_CANDIDATE_REGISTRY_VERSION=trace-design-history-relation-candidates-v1`

`ROUND9_CANDIDATE_REGISTRY_SHA256=818b306406d6a557a563ec285ae36394106c4c88a3e14cae19e4f1da4e92f4d5`

`ROUND9_RAW_CANDIDATE_TERM_COUNT=33`

`ROUND9_PASS_TO_GRAMMAR_COUNT=16`

`ROUND9_DEFER_COUNT=12`

`ROUND9_REJECT_COUNT=5`

`ROUND9_CANDIDATE_TERM_FULL_VERIFICATION_RATE=1.0`

`ROUND9_CANDIDATES_WITH_INCOMPLETE_VERIFICATION=0`

`EXPLORATION_RELATION_VOCABULARY_RESEARCH_CANDIDATE=READY_FOR_GRAMMAR_RESEARCH`

`EXPLORATION_ACTIVE_RELATION_TYPE_COUNT=0`

`EXPLORATION_RELATION_GRAMMAR=RESEARCH_NEXT`

`NEXT_RESEARCH_ROUND=DESIGN_HISTORY_RELATION_GRAMMAR_ROUND1`

## v49 main integration closure — 2026-08-25

- Prepared a fast-forward-only update from old `main` anchor `592c765d0af5bf15b1666784dce784ac8e22624d` through the preserved Round 9 tip `47978c519c3c7141690e3894315a1ef1b7a403db` plus one documentation-only integration commit.
- Preserved all 72 incoming commit identities and documented every commit from its actual diff, changed paths, packages, tests, tree, and place in the linear research chain.
- Added the integration decision, 72-row ledger, 72-section narrative, phase/dependency map, 30-branch reachability inventory, authority map, validation, and rollback package under `docs/releases/v49/main-integration-20260825/`.
- Added the sealed audit receipt under `docs/audits/v49-main-integration-20260825/` and the prospective commit-body policy under `docs/maintenance/COMMIT_DESCRIPTION_POLICY.md`.
- Preserved Search, Context, and Spacetime as ACTIVE/FROZEN; preserved Round 6 object similarity and Round 7 object NLP as superseded research; preserved Round 8 as the authoritative Exploration conceptual reset.
- Classified Round 9 relation vocabulary as research candidates for Round 10 grammar research only. Integration does not activate terms, begin Round 10, delete branches, change the frozen database, or deploy.
- Established rollback anchor `main-pre-v49-research-integration-20260825` at the old main commit; the new main anchor is the integration commit identified by `v49-research-main-integration-20260825`.

`V49_MAIN_INTEGRATION_DATE=2026-08-25`

`V49_MAIN_OLD_ANCHOR=592c765d0af5bf15b1666784dce784ac8e22624d`

`V49_ROUND9_TIP=47978c519c3c7141690e3894315a1ef1b7a403db`

`V49_INCOMING_COMMIT_SHA_PRESERVATION=72/72`

`V49_MAIN_UPDATE_MODE=FAST_FORWARD_ONLY`

`V49_MAIN_NEW_ANCHOR_TAG=v49-research-main-integration-20260825`

`EXPLORATION_ROUND6_OBJECT_SIMILARITY=SUPERSEDED_BUT_RETAINED`

`EXPLORATION_ROUND7_OBJECT_NLP=SUPERSEDED_BUT_RETAINED`

`ROUND9_RELATION_VOCABULARY=GRAMMAR_RESEARCH_CANDIDATES_ONLY`

`NEXT_RESEARCH_ROUND=DESIGN_HISTORY_RELATION_GRAMMAR_ROUND1`

## TRACE v49 Round 10 — design-history relation grammar research Round 1

- Reproduced exactly the 16 passed Round 9 senses with input identity SHA-256 `da22e62828b9d6ae2dd1692ec4f23b82a984ce9d53240d198246915668481aec`; no deferred or rejected Round 9 term entered.
- Completed review of all 16 Node roles and the exhaustive 16×16 ordered-pair space. Eight senses have bounded research-candidate roles; the other eight remain deferred because they require splitting, remain too broad, or present universal/high-connectivity risk.
- Applied the two-independent-source composition gate to every pair. No pair passes. Three pairs remain deferred research questions, all 16 diagonals reject an unsupported self-relation, and 237 off-diagonal pairs default deny.
- Added 28 grammar sources and 30 bounded attestations across 24 source strata, with explicit peer-review uncertainty retained for book chapters, edited books, an editorial article, and a commentary. Saturation is claimed only within the seven reviewed discovery batches.
- Completed seven computational review processes over every Node and all 256 cells, with final outcomes serialized only after independent completion. This is process independence, not external human design-history review.
- Preserved all 16 labels separately, recorded explicit anti-flattening comparisons, six vocabulary gaps, and eight semantic any-like deferrals, and authorized no universal Node, Flow edge, self-loop, Cluster, multistep grammar, arrow, or transitive inference.
- Kept the active relation vocabulary and grammar unresolved with zero active relation types. No renderer, route, API, database, Search, Context, Spacetime, model, archive object, title, deployment, PR, or main update is part of this round.

`ROUND10_RELATION_GRAMMAR_RESEARCH=COMPLETE_WITH_LIMITATIONS`

`ROUND10_INPUT_TERM_COUNT=16`

`ROUND10_INPUT_TERM_SHA256=da22e62828b9d6ae2dd1692ec4f23b82a984ce9d53240d198246915668481aec`

`ROUND10_PASS_NODE_CANDIDATE_COUNT=8`

`ROUND10_DEFER_NODE_COUNT=8`

`ROUND10_PASS_PAIR_RULE_COUNT=0`

`ROUND10_DEFER_PAIR_RULE_COUNT=3`

`ROUND10_UNSUPPORTED_DEFAULT_DENY_COUNT=237`

`ROUND10_UNIVERSAL_NODE_PASS_COUNT=0`

`EXPLORATION_ACTIVE_RELATION_TYPE_COUNT=0`

`RELATION_GRAMMAR_CANDIDATE_READY_FOR_IMAGE_BUILD=false`

`NEXT_RESEARCH_ROUND=EXPLORATION_IMAGE_BUILD_AND_GENERATIVE_CONSTRAINTS_ROUND1`

## TRACE v49 Round 11 — Exploration constraint-kernel preprogramming Round 1

- Fast-forward synchronized `main` from `0241b0f51e2523901b0858d54ffb7f5d2a9aa13c` to the authoritative Round 10 commit `4bd82deba482ec2fbf8c4856080151416fb8ee83` after independently rerunning the current Round 8–10, Search, Context, Spacetime, API, database-freeze, typecheck, and production-build gates. No force push, merge commit, history rewrite, or deployment occurred.
- Added a generic, renderer-neutral constraint kernel, build contract, and Image compiler with explicit `UNRESOLVED`, `RESEARCH_CANDIDATE_ONLY`, and `GOVERNED_ACTIVE` activation states. The kernel is default deny and does not read Round 9/10 TSVs or embed their real candidate labels.
- Attempted one current-state real compilation and rejected it atomically: real build attempts/successes/rejections are 1/0/1, with no partial Image. Active vocabulary, grammar, Flow-pair, Cluster, and chain rule counts all remain zero.
- Passed all 20 required adversarial cases plus ten fail-open mutation cases. Three deterministic, test-only synthetic Image builds proved compilation, replay hashing, immutable Image, Instance creation, and mutable Container behavior without authorizing any production semantic relation.
- Reconciled the sealed Round 10 package exactly: 16 input senses, 8 bounded Node candidates, 8 deferred Nodes, 256 ordered pairs, 0 pass pairs, 3 deferred pairs, 16 rejected self-relations, 237 default-denied pairs, 0 universal passes, 2 inactive Cluster handoffs, 2 inactive chains, and 6 open vocabulary gaps.
- Kept all synthetic fixtures outside production imports and preserved zero archive-object, Search, Context, Spacetime, external-model, renderer, route, API, database, and deployment changes. Nine real-Image blockers remain open.
- The next research gate is independent composition evidence and external design-history domain review; Round 11 does not activate Round 9 terms, a Round 10 grammar, or a real semantic Image.

`ROUND11_CONSTRAINT_KERNEL_PREPROGRAMMING=COMPLETE_WITH_LIMITATIONS`

`ROUND11_DECISION=PREPROGRAMMING_READY_WITH_LIMITATIONS`

`CONSTRAINT_KERNEL_READY=true`

`IMAGE_COMPILER_INFRASTRUCTURE_READY=true`

`REAL_SEMANTIC_IMAGE_READY=false`

`CURRENT_REAL_BUILD_ATTEMPT_COUNT=1`

`CURRENT_REAL_BUILD_SUCCESS_COUNT=0`

`CURRENT_REAL_BUILD_REJECTION_COUNT=1`

`SYNTHETIC_TEST_IMAGE_BUILD_COUNT=3`

`ACTIVE_RELATION_VOCABULARY_COUNT=0`

`ACTIVE_RELATION_GRAMMAR_COUNT=0`

`ACTIVE_PAIR_RULE_COUNT=0`

`ACTIVE_CLUSTER_RULE_COUNT=0`

`ACTIVE_CHAIN_RULE_COUNT=0`

`REAL_IMAGE_BLOCKER_COUNT=9`

`NEXT_RESEARCH_ROUND=DESIGN_HISTORY_COMPOSITION_EVIDENCE_AND_DOMAIN_REVIEW_ROUND1`

## TRACE v49 Round 12 — research candidate freeze and inquiry flow engine Round 1

- Froze the exact 16 Round 9 passing senses as immutable package `trace-exploration-research-candidates-v1` with canonical SHA-256 `b7d42015862e12fd54bc05a9ed0a53223771fc03954c112e72652c0349fb6f90`; eight retain bounded research-preview Node roles and eight remain deferred.
- Recomputed the evidence census from sealed Round 9–11 artifacts: the total corpus is 78 sources/85 attestations, while direct frozen-candidate evidence is 57 distinct sources/62 attestations, bounded-candidate evidence is 31/35, and deferred-candidate evidence is 27/27.
- Added four normative language-neutral JSON Schemas and a Python standard-library reference engine for the complete freeze → seed → primary inquiry flow → bounded tree → Research Inquiry Instance pipeline. TypeScript remains a strict loader/hash/conformance adapter, not the normative semantic engine.
- Hardened Round 11 untrusted inputs with exact-field parsing, duplicate and dangling-reference rejection, arity/role consistency, explicit origin policies, semantic-carrier separation, schema-aware canonicalization, and undeclared recursive archive-object, Context, Spacetime, model, and vector contamination detection.
- Compiled exactly five deterministic, non-public Research Inquiry Instances: three pair questions and two single-node questions covering all eight bounded candidates. Maximum observed structure is two semantic Nodes, two siblings, depth three, and six total tree items.
- Preserved zero active vocabulary, grammar, pair, Cluster, and chain rules; zero real Exploration Images, public Instances, Containers, routes, APIs, renderers, PNGs, objects, Context/Spacetime inputs, external models, or deployments. External human design-history review remains incomplete.

`ROUND12_RESEARCH_CANDIDATE_FREEZE=READY`

`ROUND12_FREEZE_SHA256=b7d42015862e12fd54bc05a9ed0a53223771fc03954c112e72652c0349fb6f90`

`ROUND12_FROZEN_CANDIDATE_COUNT=16`

`ROUND12_BOUNDED_CANDIDATE_COUNT=8`

`ROUND12_DEFERRED_CANDIDATE_COUNT=8`

`ROUND12_RESEARCH_INQUIRY_INSTANCE_COUNT=5`

`ROUND12_BOUNDED_NODE_COVERAGE=8/8`

`ACTIVE_RELATION_VOCABULARY_COUNT=0`

`ACTIVE_RELATION_GRAMMAR_COUNT=0`

`REAL_SEMANTIC_IMAGE_READY=false`

`NEXT_RESEARCH_GATE=EXTERNAL_DOMAIN_REVIEW_AND_INQUIRY_GRAMMAR_ACTIVATION_RESEARCH`

## v49 Round 11–12 history coordination — 2026-08-25

- Reconciled main maintenance `cc311ab0c9a74731cc1bb0158579708a8a9158fc` with sealed Round 11 `5ca999b53d9a5d18b47317817402f9e51ad26cec` and Round 12 `fc11f033d2fcdbb98130879cdbd3e4a52890e5d2` through an authorized two-parent merge from common ancestor `4bd82deba482ec2fbf8c4856080151416fb8ee83`.
- Preserved all three existing commit identities and sealed research/audit subtrees. Rebuilt the final active-script ledgers at 230/230/230 with zero missing, extra, duplicate, or unknown entries while retaining main's enhanced hygiene diagnostics.
- Established two remote backup branches, two annotated tags, and a verified 91,051,946-byte bundle with a successful four-commit restore drill before updating main.
- All Round 8–12, Search, Context, Spacetime, API, typecheck, database-freeze, repository-hygiene, audit, LFS, Git integrity, and production-build gates pass. No research activation, history rewrite, force push, branch/tag cleanup, bundle cleanup, or deployment is authorized.

`ROUND11_ROUND12_HISTORY_COORDINATION=AUTHORITATIVE`

`EXISTING_COMMIT_SHA_PRESERVATION=3/3`

`ACTIVE_RELATION_VOCABULARY_COUNT=0`

`ACTIVE_RELATION_GRAMMAR_COUNT=0`

`REAL_SEMANTIC_IMAGE_READY=false`

`NEXT_RESEARCH_GATE=EXTERNAL_DOMAIN_REVIEW_AND_INQUIRY_GRAMMAR_ACTIVATION_RESEARCH`
