# v49 release index

The immutable source release is annotated tag `v49-data-api-closure-20260821` at `d78f496bcdf2cd6941791986007cd7a885c4c532` (tree `f0549c319d1e0b0cf5e0aab5a2b297361675b701`). It preserves the complete pre-hygiene database closure, API closure, historical data, audit evidence, and repository state.

- Release manifest: `docs/releases/v49/RELEASE_MANIFEST.json`
- Source checksums: `docs/releases/v49/SOURCE_TREE_FILES.sha256`
- Data inputs: `docs/releases/v49/DATA_INPUT_MANIFEST.json`
- Audit index: `docs/releases/v49/AUDIT_INDEX.md`
- Active database root: `database/`
- Historical database skeleton: `db/` at `v49-data-api-closure-20260821` only

The active tip may remove anchored historical captures, prompts, reports, generated intermediates, and `db/`; retrieve them with `git show v49-data-api-closure-20260821:<path>` without rewriting history.

## Main integration — 2026-08-25

- Old main anchor: `592c765d0af5bf15b1666784dce784ac8e22624d` and annotated rollback tag `main-pre-v49-research-integration-20260825`.
- Preserved Round 9 tip: `47978c519c3c7141690e3894315a1ef1b7a403db`.
- New main anchor: the single integration commit identified by annotated tag `v49-research-main-integration-20260825`.
- Integration package: `docs/releases/v49/main-integration-20260825/`.
- Audit package: `docs/audits/v49-main-integration-20260825/`.
- History policy: all 72 incoming commit SHAs are preserved; detailed descriptions live in the versioned ledger and narratives rather than rewritten messages.
- Authority policy: Round 6 object similarity and Round 7 object NLP remain superseded; Round 8 remains authoritative; Round 9 provides research candidates, not active product vocabulary.
- Next research gate: Round 10 `DESIGN_HISTORY_RELATION_GRAMMAR_ROUND1`.

The integration is documentation and reachability closure only. It performs no deployment and no branch cleanup.

## Round 11–12 main integration — 2026-08-25

- Main-before anchor: `cc311ab0c9a74731cc1bb0158579708a8a9158fc`.
- Preserved Round 11/12 anchors: `5ca999b53d9a5d18b47317817402f9e51ad26cec` and `fc11f033d2fcdbb98130879cdbd3e4a52890e5d2`.
- Common ancestor: `4bd82deba482ec2fbf8c4856080151416fb8ee83`; observed divergence: 1 main-only / 2 Round12-only commits.
- Release package: `docs/releases/v49/round11-round12-main-integration-20260825/`.
- Audit package: `docs/audits/v49-round11-round12-main-integration/`.
- Recovery assets: two remote backup branches, two annotated tags, and retained verified bundle SHA-256 `dbd5c6160ad0305eb7bfaa7932e53c8637fa7eeec9bc7484d5043e84e943695c`.
- Integration policy: two-parent merge, no history rewrite, no force push, no deletion, no deployment, and no activation of research candidates.

## TRACE Round 13 research closure — 2026-08-25

- Source anchor: `83f1fba3464f5828fcfd15a1c557035bb1341bf3`.
- Research package: `docs/research/trace-v49-exploration-composition-review-round1/`.
- Audit package: `docs/audits/v49-exploration-composition-review-round1/`.
- Preservation: Round 12 candidate freeze v1 and five Instance v1 artifacts remain immutable; five Instance v2 artifacts bind their parent hashes and change topology only.
- Decision: two pair questions remain inquiry-only, one remains deferred, and zero pair activation candidates are produced. Seven narrower noun candidates, six inquiry topologies, and one structural annotation remain inactive external-review candidates.
- Boundary: no active vocabulary or grammar, no real semantic Image, no product route/API/renderer, no protected-system semantic change, and no deployment.
- Next gate: external human design-history review followed by a separate semantic-activation decision.

## TRACE Round 14 research closure — 2026-08-26

- Source anchor: `6dacbbfa962d687ceee64b23d5437369f845d4f4`.
- Research package: `docs/research/trace-v49-exploration-association-calibration-round1/`.
- Audit package: `docs/audits/v49-exploration-association-calibration-round1/`.
- Decision: an eight-type generic-association taxonomy, four provenance statuses, an ordinal D1–D7 rubric, equal calibrated direct/skip-one eligibility gates, six topology-local rules, and deterministic pruning/splitting are ready with limitations.
- Calibration: 35 associations, 69 provenance rows, 21 passes, 14 failures, 10 hard negatives, zero co-occurrence-only passes, and stable one-at-a-time sensitivity.
- Boundary: the Python engine is normative; TypeScript is a frozen-decision/schema/hash verifier only. No typed historical edge, active relation grammar, public Image, renderer, route, API, object input, model, vector store, deployment, or external-review answer is authorized.
- Next gate: Round 15 internal-only evidence-grounded spatial composition; public activation remains gated by real external human review.

## TRACE Round 15 research closure — 2026-08-26

- Source anchor: `cf4490e93449a46823a6de0c0676e431a7da6738`.
- Research package: `docs/research/trace-v49-exploration-composition-engine-round1/`.
- Audit package: `docs/audits/v49-exploration-composition-engine-round1/`.
- Decision: the Python-normative bounded composition engine, three strict schemas, separate semantic/presentation hashes, six-topology arbitration, finite pruning/split/gap semantics, and internal TypeScript research renderer are ready with limitations.
- Corpus: all 21 frozen passing associations, all 14 failures, all 10 hard negatives, 25 composition fixtures, eight visual-leakage questions per fixture, and bounded synthetic 5/10/20/40-node stress probes.
- Boundary: no recalibration, typed relation, causal/directional/hierarchical output, archive-object/Context/Spacetime semantic input, model, vector store, public route/API/renderer, deployment, or simulated human review.
- Next gate: real external composition/visual-semantics review and internal accessibility/interpretation research; public activation remains unsafe.

## TRACE Round 16 Function 3 backend closure — 2026-08-26

- Immutable source anchor: `aca7b9627ca42776d966f96ce4bd03db1f296ae3`.
- Database snapshot: `v49-api-contract-fresh-c:ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e`; schema 49; 7,995 public and 7,928 held objects.
- Research package: `docs/research/trace-v49-exploration-real-database-round1/`.
- Frontend handoff: `docs/handoff/trace-v49-exploration-real-database-round1/`.
- Audit package: `docs/audits/v49-exploration-real-database-round1/`.
- Contract: exactly four approved categories, 26 attested and academically supported visible terms, 21 qualified associations, 11 real compositions, four maps, 52 immutable states, 816 transitions, nine API capabilities, 12 schemas, OpenAPI, typed client, deterministic trees, and five validated portrait PNG exports.
- Boundary: generic association only; no typed/causal/directional relation, held-data disclosure, fixture fallback, external model, vector store, final frontend, public page, deployment, or completed external human review.
- Decision: `FUNCTION3_BACKEND_COMPLETE_READY_FOR_FRONTEND`; next gate is Claude frontend design and integration.

## TRACE Round 16B evidence-bounded baseline and clean integration — 2026-08-29

- Published research source: `codex/trace-v49-exploration-higher-order-association-closure-round16b` at `8c3588e422a3650b634693b409a9c0b13714d58f`.
- Clean-integration old-main anchor: `8de5d1dedffc6fd70d8b03cd63fdec74c0d40f6e`.
- Research package: `docs/research/trace-v49-exploration-higher-order-association-closure-round16b/`.
- Integration package: `docs/research/trace-v49-exploration-round16b-main-integration/`.
- Integration audit: `docs/audits/v49-exploration-round16b-main-integration/`.
- Product distinction: exactly three TRACE functions, with Function 3 split into Validated Exploration and the isolated Open Inquiry layer.
- Evidence boundary: 21 evidence-qualified pairwise generic associations are validated; 11 scoped higher-order hypotheses are unresolved Open Inquiry records; nine further exclusions are known within an indeterminate complete exclusion universe.
- Closure: pair, higher-order, global-composition, product-reachability, computational-space, and Function 3 closure all remain false.
- External human review remains pending. Frontend visual design and deployment are not part of this integration.
