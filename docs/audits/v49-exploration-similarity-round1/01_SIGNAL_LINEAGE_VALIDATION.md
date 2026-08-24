# Signal lineage validation

## Evidence state

`VALIDATION_STATE=SEALED_PRECOMMIT_PASS`

The inherited Round 5 Exploration registry contains exactly 64 signals. Round
6 classifies every row by source artifact, source row family, direct and
transitive parents, source-fact group, epistemic level, scoring disposition,
candidate/scoring/explanation permissions, and an explicit reason.

## Verified classification

| Scoring disposition | Expected row count |
| --- | ---: |
| `INDEPENDENT_BASE_SIGNAL` | 8 |
| `DEPENDENT_INTERACTION_SIGNAL` | 2 |
| `CANDIDATE_GENERATION_ONLY` | 9 |
| `COMPARABILITY_ONLY` | 8 |
| `EXPLANATION_ONLY` | 9 |
| `DIAGNOSTIC_ONLY` | 19 |
| `REJECT` | 9 |
| **Total** | **64** |

The current deterministic registry resolves the rows to 28 source-fact groups
and ten scoring-allowed signals: eight independent bases plus two interaction
carriers that can contribute only through a separately capped residual layer.
The final raw receipt, TSV bytes, and independent verifier reproduce these
counts exactly; all applicable EXP-SIM invariants pass.

## Independent basis contract

The expected basis has eight units across five research families:

- governed medium, theme, and published movement context;
- governed temporal extent;
- exact governed geography assignment;
- approved source identity under an explicit SOURCE treatment only;
- observed public creator attribution; and
- approved object type.

Temporal decade and governed geography class are deterministic retrieval or
explanation representations, not additional base facts. Mapping state,
precision, multi-region, and missingness signals govern comparability or
explanation. Rarity/concentration diagnostics and pair/triple cells cannot
repeat their source facts as base evidence.

## Curatorial lineage gate

The current lineage result expects zero independent curatorial residual
signals. Raw curated membership remains a candidate-recall/provenance substrate
and structural diagnostic. The M0 raw-curated Jaccard implementation is a
negative control, is never shortlist eligible, and must remain absent from
candidate, scoring-eligible, explanation-runtime, frontend, production, and
public scorer imports.

```text
CURATORIAL_AS_RECALL_INDEX=true
CURATORIAL_AS_INDEPENDENT_SCORE=false
CURATORIAL_RESIDUAL_SIGNAL_COUNT=0
SAME_SOURCE_FACT_DOUBLE_SCORE_COUNT=0
RAW_CURATED_JACCARD_IMPORT_BOUNDARY=PASS
```

`03_SIGNAL_LINEAGE_REGISTRY.tsv` passes artifact import, inspection,
formula/error scanning, rendering, and visual review at 64 data rows by 16
columns. Lineage signal SHA-256 is
`a476dd4a613ad08b394e00d3dc191423a80b20858c8340a5cf1a253ef3db4709`;
the deterministic lineage receipt is
`cd952bf0d23fb642830a8800eb9c12cf2edc8185cb1ef4fcb140423bf2488bed`.
All 93 governed geography IDs have one deterministic class mapping, with five
distinct classes and zero missing or ambiguous mappings.

## Validation requirements

The final verifier establishes:

- exactly 64 unique signal IDs and zero unclassified rows;
- every scoring-allowed signal resolves to one lineage row;
- every base-scoring source-fact group occurs at most once;
- all direct/transitive parents resolve and the graph is acyclic;
- candidate, scoring, and explanation flags agree with dispositions;
- geography class is derived candidate/explanation-only evidence;
- only the approved pair/triple carriers enter the residual interaction layer;
- curatorial parents are not credited twice; and
- every row retains `historical_relation=false`,
  `semantic_relation=false`, and `probability=false` semantics.

Evidence sources are `03_SIGNAL_LINEAGE_REGISTRY.tsv`,
`signal-lineage-summary.json`, `independent-basis-summary.json`, the mechanical
AX-002 case, the M0 import scan, and the passing 24-invariant verifier receipt.
