# Exploration affinity red team

## Purpose and evidence state

`DOCUMENT_STATE=SEALED_PRECOMMIT_PASS`

This red team attempts to falsify the Round 6 architecture. Passing an
aggregate metric does not excuse a semantic, lineage, security, determinism,
or explanation failure. Runs A and B and the 11-file artifact workflow are
complete. The audit verifier independently passes 11 checks and all 24
EXP-SIM invariants across exactly 24 research files and 11 TSVs.

## Authoritative deterministic replay

Runs A and B used independent cache/output locations and each visited exactly
31,956,015 unordered public pairs. Their timing-bearing files have different
SHA-256 values, as expected, but their canonical deterministic payloads are
byte-equal. Both deterministic payload SHA-256 values are
`c4ba0106e4a361c52f56106f86aa6b4cc360ff48ecb26019fc3d248aac9fde8a`.
This closes the exhaustive replay attack; it does not substitute for final
artifact/package verification.

The spreadsheet operation marker ran exactly once. All 11 TSVs passed import,
inspection, formula/error scanning, rendering, and visual review. This closes
the tabular-format attack; the audit verifier also passes semantic
cross-artifact reconciliation.

## 1. Lineage and double-credit attacks

| Attack | Required rejection or behavior | Evidence |
| --- | --- | --- |
| Add same governed theme, its folder membership, same theme cell, and rarity summary | one source fact contributes once; aliases are explanation/diagnostic only | lineage registry, AX-002, verifier |
| Add temporal decade beside the same governed extent | decade may retrieve or instantiate one TEMP method, but cannot add a second temporal fact | lineage registry, explanations |
| Add governed geography class beside exact governed geography | class may retrieve/explain with zero additive score | candidate/index and model tests |
| Add parent medium/theme plus a matching pair/triple cell | interaction is separately residualized and `parentContributionRepeated=false` | interaction review and scorer experiment |
| Re-label raw curated membership as residual curation | reject because the current independent residual count is zero | curatorial receipt |

Research outcome: `PASS`.

### Recoverable pre-authoritative rehearsal

The first full-corpus attempt reached the real interaction scorer and then
stopped before producing an authoritative receipt. Floating-point rounding made
the final proportional residual slightly negative; clipping that residual to
zero left the emitted interaction-row sum above its aggregate cap. The fix
reserves the largest raw interaction row as a deterministic final balancer
after allocating the other rows and uses the same declared reconciliation
tolerance across model, explanation, benchmark, and verifier. The former
failing vector, 18,000 deterministic fuzz cases, and the model, explanation,
benchmark, and verifier self-tests pass after the repair. This rehearsal was
not accepted as Run A or Run B evidence. The two subsequent clean exhaustive
runs close the full-corpus replay gate; final package verification remains
required.

## 2. Candidate-generation attacks

The candidate generator must reject held/non-public IDs, duplicate public IDs,
unknown-state postings, self-candidates, and malformed governed fields. It must
preserve duplicate titles as distinct identities and exclude the query object.

High-information postings are restricted to the exact lineage-approved
dimension specifications. Compound retrieval does not imply compound score
credit. Geography class remains in a candidate-only namespace with
`scoringAllowed=false`. Curatorial recall reasons likewise expose support and
denominator while carrying no scoring permission.

Adversarial questions:

- Can a raw curated posting cross into a scorer or production/public root?
- Can a support-1 interaction become a candidate hub or unbounded bonus?
- Can input ordering, a seed, a timestamp, or a cache state change membership?
- Can candidate recall look high only because the pool is nearly the full
  7,994-object cohort?
- Can a zero-candidate query disappear from aggregate reporting?

Research outcome: `PASS`.

## 3. Model-semantic attacks

M0 must reproduce the broad-curation failure while remaining diagnostic-only,
shortlist-ineligible, and import-isolated. M1–M8 must not describe a diagnostic
score as relation strength, relevance probability, influence, contact,
lineage, quality, importance, creator intent, or canonicality.

Specific adversaries include:

- duplicate-token inflation in sparse cosine or weighted Jaccard;
- high-cardinality family dominance before family normalization;
- Goodall-style support-1 rarity inflation;
- asymmetric Tversky parameters declared as symmetric;
- BM25F-like output missing query/document roles, field normalization, IDF,
  saturation, or declared field weights;
- map, centroid, projected, or screen distance entering Gower geography; and
- an M8 Pareto profile secretly collapsed to an undocumented scalar.

Research outcome: `PASS`.

## 4. Missingness and comparability attacks

Shared `UNKNOWN_SOURCE_VALUE`, `QUALIFIED_UNKNOWN_SOURCE_VALUE`,
`NO_PUBLISHED_MOVEMENT_CONTEXT`, `NOT_GOVERNED`, or unavailable fields must add
zero default affinity. Matching absence may be shown only in MISSING-D with
`positiveAffinityCredit=0`.

The verifier must reject:

- an affinity result without a comparability profile;
- an observed/eligible ratio that does not reconcile;
- one-sided availability converted into a mismatch score;
- a removed unavailable family that silently strengthens the evidence; and
- a non-applicable state recoded as generic missingness.

Research outcome: `PASS`.

## 5. Interaction and rarity attacks

The benchmark tests raw support, conditional support, lift, PMI, normalized
PMI, log-likelihood ratio, smoothed lift, and shrunk normalized PMI at support
thresholds 2, 3, 5, 10, and 20. It also tests no bonus, capped bonus,
information-residual, and log-likelihood-residual scoring policies.

The attack succeeds if raw PMI/lift inflation is mistaken for importance, if
joint-observable denominators are replaced with global/cohort counts, if
negative excess becomes positive evidence, if multiple interaction rows exceed
the aggregate cap, or if any parent fact is scored twice.

Research outcome: `PASS`.

## 6. Hubness, source-bias, and broad-curation attacks

For k=10, 20, and 50 the benchmark must expose occurrence mean, variance,
skewness, Gini, top-1% share, maximum, and zero-occurrence count. It must test
associations with dominant source, broad curation, common medium/theme,
metadata observability, geography, and decade.

Source experiments cannot silently turn same-source identity into positive
affinity. SOURCE-3 is valid only for an explicit contrastive task and SOURCE-4
changes ordering/diversification without changing pair scores. Family
contribution shares must be true normalized shares, distinct from
contribution units, and reconcile to the explanation.

If severe hubness is observed, local scaling, global/mutual-proximity-style
scaling, and reciprocal-neighbor filtering are analysis-only experiments. A
correction is not selected merely because one statistic improves.

Research outcome: `PASS_WITH_DIAGNOSTIC_CAUTION`.

## 7. Explanation and provenance attacks

Standalone validation must reject a self-consistent forged explanation, not
merely a stale outer hash. It recomputes contribution denominators and shares,
comparability, residual caps, BM25F-like field formulas, top-interaction hashes,
and the final explanation hash. It binds method ID/version and source treatment
to the exact analysis run and parameter receipt.

The explanation path fails if it omits retrieval reasons, unavailable
families, ignored duplicates, release/projection/registry/index pins, or an
applicable numerator/denominator/source identity. It also fails if a relation
flag is not false, probability language is emitted, a held/internal identity
appears, or a scalar is presented without family and comparability context.

Research outcome: `PASS`.

## 8. Materialization, privacy, and import attacks

The scoped committed package must contain zero internal UUIDs, held IDs, raw
private identifiers, pair rows, normalized object rows, object vectors, private
URLs, or full source records. The only object-level research packet is bounded
to public IDs/titles and deterministic review rows.

Static/import scans must prove that the M0 raw-curation implementation remains
isolated from candidate, scoring-eligible, explanation-runtime, frontend,
production, and public scorer roots. JavaScript/TypeScript import variants and
dynamic Python import variants are adversarial inputs, not trusted omissions.

Research outcome: `PASS`.

## 9. Determinism and provenance attacks

Two full executions use separate cache/output locations. After removing only
declared performance/timestamp fields, their canonical payloads and SHA-256
digests must match. Cohort records, model context, compiled feature context,
lineage, basis, candidate index, parameters, ranking hashes, output summary,
and bounded top-k artifacts are independently pinned.

A seed, timestamp, filesystem path, process ID, cache state, or input order
must not change candidate membership, affinity, comparability, rank, or
explanation identity.

Research outcome: `PASS_A_B`.

## 10. Forbidden-scope attacks

The changed-file and dependency scans must find no database mutation,
canonical release change, Search change, Context/Spacetime governance rewrite,
frontend route, public API, renderer, template freeze, clustering, embedding,
AI model, learned metric, vector database, or pair-matrix artifact.

Research scope outcome: `PASS`; the audit changed-file receipt rechecks the
final pre-commit inventory.

## Invariant matrix

The independent verifier must report all 24 required invariants:

| Invariant | Red-team assertion | Final status |
| --- | --- | --- |
| EXP-SIM-INV-001 | raw curated Jaccard cannot enter a production/public scorer | `PASS` |
| EXP-SIM-INV-002 | every scored signal resolves to one lineage row | `PASS` |
| EXP-SIM-INV-003 | one source fact contributes at most once to base affinity | `PASS` |
| EXP-SIM-INV-004 | interactions remain separate from parents | `PASS` |
| EXP-SIM-INV-005 | shared missing/unknown adds zero default affinity | `PASS` |
| EXP-SIM-INV-006 | every score exposes comparability | `PASS` |
| EXP-SIM-INV-007 | contributions expose denominator or source identity | `PASS` |
| EXP-SIM-INV-008 | curation never becomes historical relation | `PASS` |
| EXP-SIM-INV-009 | rarity never means importance by definition | `PASS` |
| EXP-SIM-INV-010 | map-coordinate distance contributes zero | `PASS` |
| EXP-SIM-INV-011 | same source is not automatically positive | `PASS` |
| EXP-SIM-INV-012 | every model is deterministic | `PASS` |
| EXP-SIM-INV-013 | every run is release/projection/registry pinned | `PASS` |
| EXP-SIM-INV-014 | held objects enter no scoped index/result/packet | `PASS` |
| EXP-SIM-INV-015 | internal UUID exposure count is zero | `PASS` |
| EXP-SIM-INV-016 | no full pair matrix is committed | `PASS` |
| EXP-SIM-INV-017 | probability terminology is absent | `PASS` |
| EXP-SIM-INV-018 | no public similarity model is selected | `PASS` |
| EXP-SIM-INV-019 | no clustering model is selected | `PASS` |
| EXP-SIM-INV-020 | randomness affects neither score nor candidates | `PASS` |
| EXP-SIM-INV-021 | symmetric models pass reversal tests | `PASS` |
| EXP-SIM-INV-022 | query-model asymmetry is declared | `PASS` |
| EXP-SIM-INV-023 | every shortlist model passes mechanical cases | `PASS` |
| EXP-SIM-INV-024 | every candidate result has an explanation path | `PASS` |

Any non-pass result must be carried into `22_MODEL_SHORTLIST_DECISION.md` and
`23_ROUND_DECISION.md`. It may force a narrower shortlist, no selection, or a
recoverable checkpoint; it must not be waived to manufacture completion.
