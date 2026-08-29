# Checkpoint 011: v50 database and Exploration v3 runtime

Parent checkpoint: `dbf0fed447c5398468714e49d5322587f29983e3`

Authorized source: `5419770959bdb8998b693fb2275b47e29b92367c`

Work branch: `codex/trace-v49-exploration-higher-order-association-closure-round16b`

Checkpoint 011 implements and verifies a research-only storage and read-model capability for first-class pair and higher-order associations. It does not populate production facts, activate product records, import Round 16A transitions into v3, deploy, or establish any historical closure claim. Association identity, association revision, participant incidence, composition, interaction state, transition, workflow, and export remain separate governed objects.

## v50 PostgreSQL capability

The additive v50 layer follows the complete frozen v49 replay and adds 35 tables, 28 integrity functions, and 26 views. Its stable association identity binds the exact participant senses and immutable bounded scope identity; qualification-only successor revisions may change contextual qualifications without changing that identity. Higher-order associations have arity three or greater and `pair_projection_policy=NONE`. Explicit internal-pair support can cite governed pair revisions, but no database function manufactures pair rows from a hyperedge.

Complete aggregate seals bind canonical parent-and-child content. Child and seal writers share advisory and parent-row locking: a concurrent loser receives SQLSTATE `40001`, a post-seal membership retry receives `55000`, and unsupported Repeatable Read or Serializable membership writes receive `25000`. Positive `api_v3` views expose only final production-authorized heads and their exact positive child sets. The committed synthetic fixtures remain transaction-local research controls and leave zero residue.

Two fresh PostgreSQL 16.13 databases were replayed and tested independently:

| Database | Replay | Test | Fixture residue | Normalized schema SHA-256 |
|---|---:|---:|---:|---|
| `gda_v50_round16b_2317` | PASS | PASS | 0 | `1152a494e6b64595c9f9291c1d314a9434cb763c7f2a02512d2768e286f571b4` |
| `gda_v50_round16b_2318` | PASS | PASS | 0 | `1152a494e6b64595c9f9291c1d314a9434cb763c7f2a02512d2768e286f571b4` |

Both schema dumps normalize to the same byte identity. Both real two-session race matrices produced the same checksum-ledger SHA-256, `595efb06ae1508b3f2cf952e3d0f1af2e9bd70b12bd4fcde93a530b3b70442ab`, and proved the child-first and seal-first invariants before dropping the disposable race databases.

The frozen database evidence is pinned as follows:

| Evidence | SHA-256 |
|---|---|
| `database/schema-manifest-v50-round16b.json` | `bac907114133ea9b261fdff426434365f020ba92bd0e377b8b2d9629438319c3` |
| final replay receipt | `7034cf1474d1baeec36d09033f28e35ae2d58f754009ebe194f5a9102725b83b` |
| `database/functions/020_exploration_v3_integrity.sql` | `a7b8dff684f5a2b77eda64ccbd6b50454d1d62ad6b2009805a34c2d5792eb2d8` |
| `database/FREEZE_V49.json` | `f0dda59dd515ba243eaf213bce9f42513727f1ab0a44685635921c3759a7d22e` |
| verified 40-file replay-prefix order | `4d7ad0949a89d9d685908df1425951d032d310c7c21b7cc08c25960f1b4f684f` |
| normalized schema | `1152a494e6b64595c9f9291c1d314a9434cb763c7f2a02512d2768e286f571b4` |
| each replay's race `CHECKSUMS.sha256` | `595efb06ae1508b3f2cf952e3d0f1af2e9bd70b12bd4fcde93a530b3b70442ab` |

The final manifest verifier reports `PASS`, 12 managed files, 126 unchanged frozen files, 40 prefix files, 35 tables, 28 functions, 26 views, a passing execution receipt, and the normalized schema hash above. No v49 object was replaced.

## Exploration v3 runtime boundary

The generated read model exposes twelve first-class collection families through active and research-control list/item routes. Every active collection is empty. The controls exercise representation and invariant rejection only; they are not active historical facts.

| Collection | Active | Research controls |
|---|---:|---:|
| concepts | 0 | 21 |
| concept senses | 0 | 21 |
| scopes | 0 | 6 |
| associations | 0 | 14 |
| incidences | 0 | 37 |
| association realizations | 0 | 10 |
| composition-coherence reviews | 0 | 2 |
| compositions | 0 | 2 |
| navigation states | 0 | 1 |
| transitions | 0 | 0 |
| workflows | 0 | 1 |
| exports | 0 | 1 |

The runtime supports `PAIR` and `HIGHER_ORDER` association kinds without a fixed backend schema maximum, but the governed product arity bound is still unresolved. Associations and compositions have separate identities and counts. Explicit workflow `transition_ids` define workflow membership; the current transition policy is `NONE_NO_V2_INHERITANCE`, transitions are unavailable, and no Round 16A pair-derived transition is silently inherited. Active pending review, implicit hyperedge projection, production activation, and active product records are all zero.

Runtime artifacts are frozen at:

| Artifact | SHA-256 |
|---|---|
| `frontend/generated/trace-exploration-v3/read-model.json` | `f1ae8a35895b27c15fb3d9b42828b8611633ee8ee7e2cbc825772b590304351b` |
| `frontend/generated/trace-exploration-v3/manifest.json` | `8346574defad9dcb16f49202f88d0aeb25c11440deb41fe5623f515f6c28e9a1` |
| `frontend/generated/trace-exploration-v3/CHECKSUMS.sha256` | `45b0d047fa103ae3fb56b31909d8aa3bfa4f3fc586131891b60ab5bdfa70b243` |
| semantic independent receipt | `bcd87f7bf83d86e86b274909c067f6c073463f11f33c4d1b70c1e170b0f60668` |
| runtime independent receipt | `978c12415b6cd8e4406c557598b5e5c71ee91d2a45565f1b7c0f60f47ba3046c` |

The final TypeScript runtime/API suite passes 408 checks. The independent stdlib-only runtime verifier passes 15 reconstructed checks and rejects all 84 corruption controls without importing, invoking, or reusing the primary projection implementation. The final semantic independent verifier passes 798 checks and retains all six closure flags as false.

## Governed production-mode HTTP measurement

The canonical HTTP evidence is command `1787932926489-cp011-v3-production-http-load-memory-final-governed`, written to `v3-production-http-checkpoint011-correction4-final`. It tested the production build over `127.0.0.1` only, used no external network, passed 1,168 of 1,168 cases, preserved the read-model SHA-256 `f1ae8a35895b27c15fb3d9b42828b8611633ee8ee7e2cbc825772b590304351b`, and terminated its process group cleanly without SIGKILL or residual processes. The verification-summary SHA-256 is `44f2999a1f417f723b660e54bf8d979965bc5cd88a12849c51ec492be2521607`.

The 1,168 cases comprise 160 functional HTTP cases, 500 bounded concurrency requests, 500 paced sustained-read requests, seven control-export replay requests, and one artifact-integrity case. Startup, runtime-memory, and process-termination checks are additionally bound in the summary receipts. The concurrency measurements were:

| Concurrency | Requests | Failures | Duration ms | p50 ms | p95 ms | p99 ms | Max ms | Requests/s |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 100 | 0 | 168.387999990955 | 1.5191659913398325 | 2.21635868656449 | 2.491494561545554 | 3.1510000117123127 | 593.866546341613 |
| 5 | 100 | 0 | 104.12758309394121 | 4.901583539322019 | 7.423960097366943 | 8.348166946088897 | 8.682291954755783 | 960.3603294026577 |
| 10 | 100 | 0 | 90.55924997664988 | 8.436916978098452 | 10.71843394311145 | 11.668718222063038 | 12.342042056843638 | 1104.2494281454888 |
| 25 | 100 | 0 | 94.97558395378292 | 22.129645512904972 | 24.37928119325079 | 24.81358597637154 | 24.888125015422702 | 1052.9021864046877 |
| 50 | 100 | 0 | 106.73175007104874 | 40.87893752148375 | 54.486532969167456 | 55.19710134132765 | 55.21129094995558 | 936.92832670159 |

The sustained read used concurrency 10, completed 500 requests with zero failures in 9,814.637750037946 ms, and observed p50/p95/p99/max latencies of 4.867124545853585 / 10.780605662148444 / 18.262569144135327 / 23.60520896036178 ms at 50.94431529050238 requests/s. Its planned duration was 10 seconds; the request cap ended the paced run at a completion ratio of 0.9814637750037946. Peak RSS was 232,816,640 bytes; peak heap used was 82,718,456 bytes; peak heap total was 111,722,496 bytes; and peak event-loop-delay p95 was 12.091391 ms.

These are measurements from this loopback test environment. They are not production SLOs, capacity guarantees, deployment evidence, or approval to activate production data.

## Preserved failures and additive corrections

The execution record retains failed attempts and the corrections that supersede them. They are historical audit evidence, not current failing gates:

- the first final 2317 replay stopped on an invalid PL/pgSQL composite multi-target `INTO`; the partial database was discarded, the function was corrected and repinned, and a fresh 2317 was created;
- the first corrected 2317 replay then exposed an unclosed final-disposition boolean group; that partial database was also discarded, the expression was split into equivalent fail-closed checks, and correction 2 replayed and tested successfully;
- 2318 remained pristine throughout the 2317 corrections and was verified pristine before its independent successful replay;
- the final database verifier was corrected to accept PostgreSQL's truthful bounded Homebrew packaging suffix while still requiring numeric PostgreSQL 16 parity across both replays;
- the final runtime audit found incomplete normative hash reconstruction, participant-scope parity, item-route coverage, explicit workflow transition membership, DTO key boundaries, adversarial coverage, and derived metric checks; the final artifacts add those checks and pass 408 TypeScript checks plus 84 independent corruption rejections;
- mistyped local verification commands, a sandbox-only Google Fonts DNS failure, and a sandbox loopback-bind denial were preserved; the exact corrected commands, approved-network build, and approved loopback verifier passed;
- earlier HTTP directories remain immutable diagnostic evidence. Only `correction4-final` is the canonical governed measurement summarized here.

## Closure decision and next boundary

This checkpoint proves representational, integrity, deterministic-read-model, and loopback runtime capability for the governed research controls. It does not prove that the candidate-association universe is complete, that higher-order evidence review is complete, that prior compositions are globally coherent, that all active vocabulary is product reachable, or that Function 3 is closed. The next checkpoint must conduct the fresh recursive gap audit and issue the evidence-bounded closure or non-closure decision.

```text
PAIR_ASSOCIATION_CLOSURE=false
HIGHER_ORDER_ASSOCIATION_CLOSURE=false
GLOBAL_COMPOSITION_COHERENCE_CLOSURE=false
PRODUCT_ASSOCIATION_REACHABILITY_CLOSURE=false
COMPUTATIONAL_SPACE_CLOSURE=false
FUNCTION3_CLOSURE=false

FORCE_PUSH_USED=false
HISTORY_REWRITTEN=false
ROLLBACK_TAG_PUSHED=false
DEPLOYMENT_PERFORMED=false
PRODUCTION_DATA_IMPORTED=false
PRODUCTION_ACTIVATION_PERFORMED=false
```

The machine-readable checkpoint receipt is `docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/v50-v3-runtime-checkpoint011-receipt.json`.
