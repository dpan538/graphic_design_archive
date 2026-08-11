# 09 — Research Corpus Policy

- Package: v49 Phase 1C A4
- Policy version: `v49-research-corpus-policy-1.0.0`
- Missingness baseline: `v49-missingness-baseline-1.0.0`
- Effective date: 2026-08-11
- Baseline commit: `6b111a78818a9e9ef37e4909c1f288d3b844b77e`
- Frozen source ancestor: `0404c7f96f9189f576c4c5b1368061e4082e436b`
- Scope result: **PASS**

`PASS` means every one of the 15,923 canonical-input surfaces has one deterministic Browse, research, and TRACE disposition; unknown evidence is held rather than inferred; the policy and missingness vocabulary are versioned; and all membership sets have machine-checkable hashes. It does not mean that a strict scholarly corpus, semantic relations, PostgreSQL, a release, visual rights, or frontend promotion has been implemented.

## 1. Scope and research question

This policy answers one deliberately narrow question:

> Which v48 operational archive objects carry an explicit row-level `source_verified` tier sufficient for a minimal source-bounded descriptive-research eligibility baseline, without treating catalog, Search, workflow acceptance, or legacy TRACE presence as research evidence?

The population frame is exactly the 15,923 surfaces in `generated/public_surfaces_prefreeze_candidate_v48.json`. Under the locked v49.0 identity decision, each input surface accounts for one baseline archive object; this preserves accounting and asserts neither unique intellectual-work identity nor representativeness.

The policy excludes visual rights, provider policy, delivery mode, endpoint health, image acquisition, and display eligibility. Those are independent Prompt B / visual-registry decisions. It also does not infer scholarly, causal, or influence claims.

## 2. Authority boundary

| Asset/layer | Role in this policy | May create canonical objects or research eligibility? |
|---|---|---:|
| v48 candidate JSON | Sole canonical migration input and sole row-level eligibility authority | Yes, only through explicit governed rules |
| Immutable SQLite | Reconciliation evidence | No |
| Transfer and TRACE manifests | Integrity evidence | No |
| Search index | Derived projection | No |
| TRACE catalog, atlas, shards and client caches | Derived legacy projection | No |
| Review catalog | Separate derived held/review population | No |
| Auxiliary TRACE layer | Separate count-ineligible adjunct population | No |

The A2 single candidate pass produced `/private/tmp/v49_phase1c_candidate_rows.tsv` with 15,923 rows, 2,238,838 bytes and SHA-256 `4d5f15cda8e1267426fd91ea76da92573ab2851ee033468ebb0ef206ff0c4c46`. A4 reused that ledger and did not rescan the 190 MB candidate.

The row evidence contradicts a legacy normalization: candidate `trace.tier` is explicitly `source_verified` on 7,995 rows, explicitly `metadata_supported` on 2,971 rows, and blank on 4,957 rows. The SQLite value 12,952 was produced by an old accepted-row fallback that normalized the 4,957 blanks to `source_verified`. SQLite cannot backfill the canonical input, so the 4,957 rows remain held. The coordinated normative correction is recorded in `DATA_MODEL_V49.md`, `MIGRATION_V48_TO_V49.md`, and `ACCEPTANCE_GATES.md`.

## 3. Orthogonal population boundaries

| Population/unit | Count | Policy meaning |
|---|---:|---|
| `LEGACY_INPUT_SURFACES` | 15,923 | Candidate JSON surfaces; the Browse Index population frame |
| `ACCOUNTED_INPUT_SURFACES` | 15,923 | Every source ordinal has one ledger row |
| `UNACCOUNTED_INPUT_SURFACES` | 0 | No surface disappears through parsing, merge or filter |
| `BASELINE_ARCHIVE_OBJECTS` | 15,923 | One conservative v49.0 object per input surface |
| `RESEARCH_ELIGIBLE_OBJECTS` | 7,995 | Explicit candidate `trace.tier=source_verified` only |
| `HELD_OBJECTS` | 7,928 | 4,957 blank-tier plus 2,971 metadata-supported rows |
| `REJECTED_OBJECTS` | 0 | No authoritative rejection rule or decision appears in the sole input |
| `TRACE_ELIGIBLE_OBJECTS` | 0 | No candidate row has an eligible accepted semantic relation/claim path |
| Legacy Search items | 8,636 | Derived reconciliation population, not a corpus |
| Legacy review rows | 4,425 | Separate derived review/hold population; zero overlap with the 15,923 baseline |
| Legacy auxiliary items | 11 | Separate count-ineligible adjunct population |

The held count is a corpus-selection disposition, not the canonical acceptance state and not the legacy publication layer. A held input surface is still accounted and still receives its baseline archive object.

## 4. Versioned membership rules

Rules are evaluated in source ordinal order and are mutually exclusive.

| Rule | Predicate over candidate row | Research disposition | Reason code |
|---|---|---|---|
| `R-ACCOUNT-001` | Valid unique nonblank `surfaceId` and `sourceRecordId`, with one source ordinal/pointer | Browse `ACCOUNTED` | `ONE_BASELINE_OBJECT_PER_INPUT_SURFACE` |
| `R-RESEARCH-001` | `trace.tier` is exactly `source_verified` | `RESEARCH_ELIGIBLE` | `EXPLICIT_SOURCE_VERIFIED_TIER` |
| `R-RESEARCH-002` | `trace.tier` is exactly `metadata_supported` | `HELD` | `METADATA_SUPPORTED_BELOW_STRICT_EVIDENCE_THRESHOLD` |
| `R-RESEARCH-003` | `trace.tier` is absent or blank | `HELD` | `MISSING_EXPLICIT_EVIDENCE_TIER` |
| `R-RESEARCH-004` | Any nonblank unregistered tier | `HELD` | `UNREGISTERED_EVIDENCE_TIER_FAIL_CLOSED` |
| `R-REJECT-001` | Evidence-bearing governed rejection decision | `REJECTED` | No matching rows in v48 candidate |
| `R-TRACE-001` | Accepted registered semantic relation supported by an eligible claim/evidence path and selected by this corpus version | `TRACE_ELIGIBLE` | No matching rows in v48 candidate |
| `R-TRACE-002` | Otherwise, including only legacy node/tree/edge crosswalks | TRACE `HELD` | `NO_ELIGIBLE_ACCEPTED_SEMANTIC_RELATION_OR_CLAIM` |

Neither candidate `trace.state=accepted` nor a legacy review state upgrades a row: acceptance, workflow, publication layer, epistemic class and metric eligibility are separate axes. Search membership, catalog membership, tree membership, node presence, edge count, source URL presence, or an accessible endpoint also cannot satisfy `R-RESEARCH-001`.

No automatic duplicate merge, row rejection, delimiter split, influence inference, or unknown-relation fallback occurs.

## 5. TRACE eligibility is intentionally zero

A3 independently confirmed that the candidate contains 126,822 opaque membership edge-ID references but does not provide authoritative endpoint/evidence/accepted-claim/semantic-relation records. In 9,393 surfaces, `edgeIds` and `edgeLabels` have unequal lengths, so positional zipping is prohibited.

The complete legacy graph classification accounts for all 255,695 edges as 217,554 `LEGACY_PROJECTION_ONLY`, 6,004 `COMPUTED_ASSOCIATION` without a governed analysis run, and 32,137 `HELD_UNSUPPORTED`; unclassified graph facts are zero. `CANONICAL_ASSERTION_CANDIDATE` only permits preserving a proposed raw assertion/crosswalk. It does not create a semantic relation, accepted claim, or TRACE eligibility.

Therefore every baseline object has TRACE disposition `HELD`, and `TRACE_ELIGIBLE_OBJECTS=0`. This is a fail-closed evidence result, not a claim that no historical relation exists.

## 6. Search, review and auxiliary reconciliation

The derived Search population and candidate population have different boundaries:

| Set relation | Count |
|---|---:|
| Search items / unique IDs | 8,636 / 8,636 |
| Candidate ∩ Search | 2,585 |
| Search − candidate | 6,051 |
| Candidate − Search | 13,338 |
| Candidate ∪ Search | 21,974 |

Within the 15,923 candidate rows, Search intersects 80 research-eligible rows and 2,505 held rows; it omits 7,915 research-eligible and 5,423 held rows. This demonstrates why Search presence is neither inclusion evidence nor a research-quality proxy. The 6,051 Search-only IDs are not imported and cannot create canonical rows.

The 4,425 review surface IDs have zero intersection with the candidate baseline. The 11 auxiliary object IDs are also a distinct legacy layer. Both remain reconciliation evidence outside `10_CORPUS_MEMBERSHIP_BASELINE.tsv`.

## 7. Deterministic membership and set hashes

`10_CORPUS_MEMBERSHIP_BASELINE.tsv` has one header plus 15,923 data rows and 19 columns. It preserves source identity/order and records policy version, missingness version, Browse disposition, research disposition/reason, TRACE disposition/reason, derived Search presence and the candidate TRACE crosswalk fields.

Set hashes use SHA-256 over the UTF-8 byte stream of unique identifiers sorted lexicographically, each followed by LF.

| Set | Rows | SHA-256 |
|---|---:|---|
| Browse baseline surface IDs | 15,923 | `7bae71cb2915a6ea6a9c9c43024a0a84bab5200edffad96298f398a7b8053d46` |
| Accounted surface IDs | 15,923 | `7bae71cb2915a6ea6a9c9c43024a0a84bab5200edffad96298f398a7b8053d46` |
| Research-eligible surface IDs | 7,995 | `e474377554ee061f3b7b8953ed0715f131874d1dc3b3e9cb130e3035bb987882` |
| Held surface IDs | 7,928 | `b5b9e59ccbfbb07bf8493890216ddb18d57b2bb89fbd4d566fcc6944cbbd2c91` |
| Rejected surface IDs | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| TRACE-eligible surface IDs | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| Search surface IDs | 8,636 | `05bfd0a89fd050222c4ad77bdd90bf479313a1fd0f058053be287e284b7089e8` |

The TSV byte hash at creation is `ff81cc7d98829e10d0eca99dc19f6203c42252c0e1a8db215c7eadfb5389d068` (5,082,837 bytes). Package `CHECKSUMS.sha256` remains the final file-integrity authority after all audit files are assembled.

## 8. Missingness contract

`11_MISSINGNESS_BASELINE.json` is the machine-readable baseline. Each observation names its population frame, denominator, unit, method, count, evidence confidence and promotion rule. The current governed observations are:

- 4,957 rows: evidence tier not collected/unknown, held;
- 2,971 rows: metadata insufficient for this strict source-bounded threshold, held;
- 15,923 rows: no eligible accepted semantic relation/claim path for a v49 TRACE projection, held.

Search absence is a derived projection difference, not research missingness. Review and auxiliary exclusion is a population-frame distinction, not a missing canonical row. Visual-rights/display missingness is explicitly out of scope.

Provider/source-family concentration is not inferred from source-record prefixes or URL hosts. It remains P1 until a governed normalized provider/source registry exists; this prevents an apparently precise but semantically false concentration measure.

## 9. Gates

| Gate | Result | Evidence |
|---|---|---|
| All candidate input surfaces accounted | PASS | 15,923/15,923; unaccounted 0 |
| Browse baseline separated from strict research eligibility | PASS | 7,995 eligible; 7,928 held; 0 rejected |
| Blank/unknown tier fail-closed | PASS | 4,957 held; no SQLite fallback |
| Catalog/Search presence cannot upgrade eligibility | PASS | Rules and reconciliation matrix |
| TRACE requires accepted registered relation/claim | PASS | 0 eligible; 15,923 held; A3 unclassified 0 |
| Research corpus policy versioned | PASS | `v49-research-corpus-policy-1.0.0` |
| Missingness baseline versioned | PASS | `v49-missingness-baseline-1.0.0` |
| 20,000 is an acceptance gate | PASS (`false`) | No policy rule references it as a gate |
| Provider/source concentration | PARTIAL (P1) | Deferred until normalized registry; no guess substituted |
| Rights/visual registry | OUT OF SCOPE | Independent Prompt B closure |

The repository-wide verifier command is:

```sh
python3 scripts/verify_v49_authority_research_delta.py --json
```

It must recompute the membership counts and hashes, validate the TSV/JSON contracts, and remain stdout-only, offline and non-mutating.

## 10. Actions explicitly not performed

- No candidate JSON, SQLite, manifest, Search file, TRACE file, shard or v48 asset was edited.
- No PostgreSQL, DDL, migration, import, export, deduplication, merge, delimiter split or data regeneration was run.
- No network, image download, HTTP probing, npm, Next, TypeScript, browser automation, Docker or frontend process was started.
- No visual-rights, provider-policy or delivery-mode decision was made.
- No held row was silently promoted and no object was added or removed to approach 20,000.
