# Candidate-index validation

## Evidence state

`VALIDATION_STATE=SEALED_PRECOMMIT_PASS`

The candidate index is a deterministic public-ID inverted index. It contains
no held object, internal UUID, pair row, title identity key, random selection,
or scoring result. Candidate generation admits records for controlled recall;
the scorer independently recomputes approved evidence.

## Posting boundary

The index separates:

- governed/approved direct postings for Context, temporal decade, exact
  geography, source, creator, and object type;
- candidate-only governed geography-class postings, which are deterministically
  derived from exact geography and have `scoringAllowed=false`;
- lineage-approved high-information interaction postings; and
- raw curatorial recall postings, also with `scoringAllowed=false`.

The exact candidate-authorized compound dimension specifications are:

```text
creator × medium
medium × theme
object_type × medium
theme × movement_context
```

Other pair specifications and every triple are excluded from the
high-information candidate namespace unless a later lineage decision changes
the policy. Retrieval through a compound posting cannot repeat parent evidence
in the base score.

## CG-CUR variants

| Variant | Candidate policy | Scoring permission |
| --- | --- | --- |
| CG-CUR-1 | any shared curated container | false |
| CG-CUR-2 | at least two shared containers | false |
| CG-CUR-3 | at least one container below declared support threshold | false |
| CG-CUR-4 | information-weighted posting threshold | false |
| CG-CUR-5 | lineage-approved residual curation only | no current residual input |
| CG-CUR-6 | governed/approved direct postings only | direct evidence is recomputed by scorer |

Equal-recall/equal-pool selection ties use a predeclared deterministic
priority. The exhaustive evidence and independent verifier select CG-CUR-4 as
the candidate-retrieval architecture.

## Required exact checks

The verifier proves:

- public object count 7,995 and held index count zero;
- candidate denominator 7,994 per public query;
- selected object excluded from every pool;
- duplicate titles retain distinct public identities;
- candidate set and receipt are independent of input order and seed;
- candidate-only geography class is indexed and never enters family scoring
  tokens;
- unapproved interaction pairs/triples create zero high-information postings;
- raw curation and M0 never become scorer inputs;
- serialized bytes and heap measurements follow their declared policies; and
- no materialized pair rows are emitted or committed.

## Final result fields

```text
CANDIDATE_GENERATOR_VARIANT_COUNT=6
CANDIDATE_ARCHITECTURE_SELECTED=true
SELECTED_CANDIDATE_VARIANT=CG-CUR-4
CANDIDATE_POOL_P50=3008
CANDIDATE_POOL_P90=3608
CANDIDATE_POOL_P95=3662
CANDIDATE_POOL_P99=5644
CANDIDATE_POOL_MAX=5991
CANDIDATE_RECALL_AT_10=0.9998499061913696
CANDIDATE_RECALL_AT_20=0.9995809881175735
CANDIDATE_RECALL_AT_50=0.9974158849280801
ZERO_CANDIDATE_OBJECT_COUNT=0
NEAR_FULL_CORPUS_CANDIDATE_OBJECT_COUNT=0
CANDIDATE_INDEX_SHA256=abba30fcdded21b8f1ba6f7ec87a47b6bbd83c0d1e40d90670143fb88b83873f
```

The 72x19 candidate recall table passes the complete artifact workflow. The
candidate interaction policy approves 45 observed cells / 427 posting
memberships, rejects caller-supplied tokens, and reports zero support
reconciliation failures. No pair rows are materialized and randomness does not
affect candidate membership.

Evidence sources are `11_CANDIDATE_RECALL_RESULTS.tsv`,
`candidate-index-summary.json`, the central receipt, candidate-module
self-tests, and the passing independent verifier.
