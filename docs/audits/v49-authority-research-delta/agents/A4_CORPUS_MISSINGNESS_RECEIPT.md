# A4 — Corpus, Missingness and TRACE Eligibility Receipt

- Task: v49 Phase 1C A4
- Agent scope: corpus selection, input accounting, research/TRACE eligibility, Search/review/auxiliary reconciliation, missingness baseline
- Output status: **PASS**
- Exit status: `0`
- Date: 2026-08-11 (Australia/Brisbane)
- Baseline commit read: `6b111a78818a9e9ef37e4909c1f288d3b844b77e`
- Files modified by A4: exactly four files listed below

## Task boundary

A4 determined a versioned corpus and missingness disposition for every frozen candidate surface. It did not decide visual rights, provider policy, delivery mode or endpoint health; did not promote legacy graph projections; and did not edit any frozen v48 asset or normative architecture document.

## Outputs

| Path | Purpose | Rows/bytes | SHA-256 before final package checksum |
|---|---|---:|---|
| `docs/audits/v49-authority-research-delta/09_RESEARCH_CORPUS_POLICY.md` | Human-readable policy, authority boundary, rules and gates | 159 lines / 12,312 bytes | `d6b80dc9ce46f0891510dc1c59baa8b7024eb6263e5303d6ce57133691928607` |
| `docs/audits/v49-authority-research-delta/10_CORPUS_MEMBERSHIP_BASELINE.tsv` | One deterministic disposition per candidate surface | 15,924 lines / 5,082,837 bytes | `ff81cc7d98829e10d0eca99dc19f6203c42252c0e1a8db215c7eadfb5389d068` |
| `docs/audits/v49-authority-research-delta/11_MISSINGNESS_BASELINE.json` | Machine-readable missingness/reconciliation baseline | 253 lines / 10,175 bytes | `6c82af7e6d9d0e09196775743c3da8d1dd87e6a95b9c528668c43addc0154acb` |
| `docs/audits/v49-authority-research-delta/agents/A4_CORPUS_MISSINGNESS_RECEIPT.md` | This task receipt | self | final package checksum owns final hash |

## Assets read

- `/private/tmp/v49_phase1c_candidate_rows.tsv` — A2 single-pass candidate ledger; 15,923 data rows, 2,238,838 bytes, SHA-256 `4d5f15cda8e1267426fd91ea76da92573ab2851ee033468ebb0ef206ff0c4c46`.
- `/private/tmp/v49_phase1c_a2_summary.json` — A2 deterministic aggregates and field evidence.
- `frontend/public/data/archive-search-v1.json` — derived Search reconciliation only.
- `frontend/public/data/trace-v48/catalog.json` — schema/count inspection only; derived.
- `frontend/public/data/trace-v48/review-catalog.json` — separate review population reconciliation.
- `frontend/public/data/trace-v48/auxiliary.json` — separate auxiliary population reconciliation.
- `docs/adr/0004-research-claims-corpora-and-visual-registry.md`, `DATA_MODEL_V49.md`, `MIGRATION_V48_TO_V49.md`, `ACCEPTANCE_GATES.md`, and `docs/audits/v49-pre-migration/05_TRACE_RESEARCH_SEMANTICS.md` — normative/research context.
- A3 inter-agent evidence — graph classifications and zero-unclassified result used only to confirm that legacy projections do not satisfy TRACE eligibility.

A4 did not rescan `generated/public_surfaces_prefreeze_candidate_v48.json`. This avoided a second 190 MB parse and preserved the one-heavy-reader scheduling boundary.

## Evidence commands

Representative read-only or scoped deterministic commands:

```sh
cat /private/tmp/v49_phase1c_a2_summary.json
head -n 4 /private/tmp/v49_phase1c_candidate_rows.tsv
tail -n 3 /private/tmp/v49_phase1c_candidate_rows.tsv
wc -l /private/tmp/v49_phase1c_candidate_rows.tsv
shasum -a 256 /private/tmp/v49_phase1c_candidate_rows.tsv

jq 'keys, (.items|length), .items[0]' frontend/public/data/archive-search-v1.json
jq '{itemCount:(.items|length), schema:.schema}' frontend/public/data/trace-v48/review-catalog.json
jq '{itemCount:(.items|length), layer:.layer}' frontend/public/data/trace-v48/auxiliary.json

/Users/jarlgiovanni/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node \
  /private/tmp/generate_phase1c_a4.mjs \
  /private/tmp/v49_phase1c_candidate_rows.tsv \
  frontend/public/data/archive-search-v1.json \
  frontend/public/data/trace-v48/review-catalog.json \
  frontend/public/data/trace-v48/auxiliary.json \
  docs/audits/v49-authority-research-delta/10_CORPUS_MEMBERSHIP_BASELINE.tsv \
  /private/tmp/v49_phase1c_a4_stats.json

jq empty docs/audits/v49-authority-research-delta/11_MISSINGNESS_BASELINE.json
awk -F '\t' 'NR==1{if(NF!=19)exit 2;next}{n++;if(NF!=19)bad++}END{if(n!=15923||bad)exit 3}' \
  docs/audits/v49-authority-research-delta/10_CORPUS_MEMBERSHIP_BASELINE.tsv
LC_ALL=C tail -n +2 docs/audits/v49-authority-research-delta/10_CORPUS_MEMBERSHIP_BASELINE.tsv \
  | cut -f3 | sort -u | wc -l
shasum -a 256 docs/audits/v49-authority-research-delta/09_RESEARCH_CORPUS_POLICY.md \
  docs/audits/v49-authority-research-delta/10_CORPUS_MEMBERSHIP_BASELINE.tsv \
  docs/audits/v49-authority-research-delta/11_MISSINGNESS_BASELINE.json
git diff --check -- docs/audits/v49-authority-research-delta/
```

The repository owner will execute the independent package verifier and artifact-tool TSV check:

```sh
python3 scripts/verify_v49_authority_research_delta.py --json
```

## Measured results

```text
LEGACY_INPUT_SURFACES=15923
ACCOUNTED_INPUT_SURFACES=15923
UNACCOUNTED_INPUT_SURFACES=0
BASELINE_ARCHIVE_OBJECTS=15923

RESEARCH_ELIGIBLE_OBJECTS=7995
TRACE_ELIGIBLE_OBJECTS=0
HELD_OBJECTS=7928
REJECTED_OBJECTS=0
```

Candidate row tier evidence:

```text
explicit source_verified=7995
explicit metadata_supported=2971
missing/blank tier=4957
unknown nonblank tier=0
```

The legacy SQLite value 12,952 equals the 7,995 explicit source-verified rows plus an old derived fallback over the 4,957 blank-tier rows. The fallback is not canonical authority and was not used.

Search reconciliation:

```text
Search=8636
candidate intersection=2585
Search-only=6051
candidate-only=13338
union=21974
```

The 4,425 review surface IDs and 11 auxiliary object IDs remain separate derived layers. Review/candidate intersection is zero.

TRACE result:

- 15,923/15,923 baseline objects are TRACE-held;
- `TRACE_ELIGIBLE_OBJECTS=0`;
- the candidate carries 126,822 opaque edge references, while 9,393 rows prohibit positional edge-ID/label zipping;
- A3 accounts for all 255,695 legacy graph edges and reports `UNCLASSIFIED_GRAPH_FACT=0`;
- no legacy crosswalk, accepted flag, tree/node presence or computed association creates an accepted semantic relation/claim.

## Findings and priorities

| ID | Priority | Result | Finding / disposition |
|---|---|---|---|
| A4-P0-01 | P0 | CLOSED | No versioned corpus membership existed. Policy 1.0.0 and a 15,923-row ledger now account for every input surface. |
| A4-P0-02 | P0 | CLOSED | Legacy accepted-to-source-verified fallback could silently promote 4,957 blank tiers. They now fail closed to `HELD`; coordinated normative documents distinguish 7,995 explicit from 12,952 derived. |
| A4-P0-03 | P0 | CLOSED | Catalog/TRACE presence could be read as research eligibility. Policy makes all such implications false and records `TRACE_ELIGIBLE_OBJECTS=0`. |
| A4-P0-04 | P0 | CLOSED | Missingness lacked a versioned frame, reason, denominator and promotion rule. JSON baseline 1.0.0 now supplies them. |
| A4-P1-01 | P1 | OPEN | Provider/source-family concentration requires a governed normalized source registry. Prefix/URL-host inference was rejected as semantically unsafe. |
| A4-OOS-01 | Out of scope | OPEN | Visual rights/display missingness belongs to Prompt B and must remain independent. |

## Risks and recommended actions

- Never restore the 12,952 derived normalization as row-level candidate authority. The 4,957 blank tiers require row-specific evidence and a governed review decision.
- Treat `HELD` here as corpus disposition, not canonical rejection, workflow state or publication layer.
- Preserve `TRACE_ELIGIBLE_OBJECTS=0` until registered semantic relations and eligible evidence-bearing claims are implemented and selected by a sealed corpus.
- Run the independent verifier after all agent products land; any count/hash/classification mismatch must fail the Phase 1C gate rather than mutate data.
- Add provider/source-family concentration only after its identity registry exists; do not fabricate it from source ID prefixes.

## Actions explicitly not performed

- No v48 JSON, SQLite, manifest, shard, Search, TRACE, QA or visual asset was modified.
- No PostgreSQL, DDL, migration, fixture, API, adapter, frontend or visual page was implemented.
- No npm install, Next dev/build, full TypeScript, browser automation, Docker, data export/regeneration, image download or HTTP probe ran.
- No deduplication, merge/split, delimiter split, hidden row drop, unknown-relation fallback or influence inference ran.
- No branch change, commit, push, PR, merge or deployment was performed by A4.

## Residual processes

An escalated read-only `ps` scan found only the scan command itself and no A4 Node, Next, TypeScript, browser automation or generator process. `RESIDUAL_A4_PROCESS_COUNT=0`.
