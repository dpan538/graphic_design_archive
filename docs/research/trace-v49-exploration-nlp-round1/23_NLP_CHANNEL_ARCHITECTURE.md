# NLP channel architecture

## Evidence state

`DOCUMENT_STATE=FINAL_EVIDENCE_BOUND_AUDIT_ONLY`

This document evaluates future positions for a text-derived channel. It does
not install a channel, select a public model, add an API, choose fusion weights,
or modify the frozen structured system.

## Preserved profile

Any future research result must remain aspect-separated:

```ts
interface NlpSemanticProfile {
  titleAffinity?: number;
  subjectAffinity?: number;
  objectDescriptionAffinity?: number;
  sourceNarrativeAffinity?: number;

  jointlyAvailableAspects: readonly string[];
  unavailableAspects: readonly string[];

  sourceLeakageDiagnostics: unknown;
  languageDiagnostics: unknown;

  methodId: string;
  modelRevision: string;

  historicalRelation: false;
  semanticRelation: false;
  probability: false;
}
```

The profile reports semantic text affinity, not a historical or semantic
relation. Source narrative remains isolated. Unavailable aspects are explicit;
they are not scored as zero or filled with generated text.

## Candidate positions

| Position | Role | Evidence required before later use | Round 7 state |
| --- | --- | --- | --- |
| `NLP-POSITION-A` | explanation-only semantic channel | bounded intelligible public-safe explanations and acceptable leakage disclosure | `NEEDS_MORE_DATA` |
| `NLP-POSITION-B` | additional candidate-generation channel | full-cohort recall, bounded pools, source/language robustness, and independent evaluation | `NEEDS_MORE_DATA` |
| `NLP-POSITION-C` | reranker over `CG-CUR-4` candidates | task-specific labels, ranking stability, and proof that the structured candidate boundary is unchanged | `NEEDS_MORE_DATA` |
| `NLP-POSITION-D` | independent parallel affinity channel | at least one full-cohort lexical/dense architecture, explicit aspects, review packet, and leakage/hubness accounting | `NEEDS_MORE_DATA` |
| `NLP-POSITION-E` | late fusion with structured profile | separately validated channels, declared objective, expert judgments, and a later fusion study | `DEFER` |

At most positions may be shortlisted; no position becomes public or
implemented automatically. Final architecture receipt:

```text
NLP_CHANNEL_POSITION_VARIANT_COUNT=5
NLP_CHANNEL_POSITION_SHORTLIST=NONE
NLP_CHANNEL_ARCHITECTURE_SHA256=41778806f6bbf5ff5b90667f61a3e5df202e0e13b4873c7b5db42cd01fb58a2f
```

## Channel boundaries

The structured and NLP paths remain independent:

```text
structured public profile
  -> CG-CUR-4 candidate retrieval
  -> M2 / M5 / M7 research profiles

governed public text
  -> aspect-separated lexical or dense retrieval
  -> source/language/leakage diagnostics

comparison only
  -> bounded overlap and disagreement rows
```

NLP is not tuned to reproduce `M2`, `M5`, or `M7`. High disagreement may be a
substantive finding rather than an error. `M7` is an asymmetric structured
retrieval architecture; it must not be compared with a symmetric NLP mode as
if both answer the same task without explicit qualification.

## Explanation contract

Each bounded candidate explanation must include:

- query and candidate public IDs;
- aspect ID and aspect availability;
- lexical/dense method and exact revision;
- source field roles and corpus/registry pins;
- original-input or named robustness variant;
- identical/near-duplicate diagnostics;
- source and language diagnostics;
- structured-label masking state;
- the independent `M2`/`M5`/`M7` comparison, if present; and
- `historicalRelation=false`, `semanticRelation=false`, and
  `probability=false`.

No score-only explanation is sufficient. A scalar cannot hide title, subject,
description, or source-narrative disagreement.

## Non-selection boundary

```text
STRUCTURED_NLP_FUSION_SELECTED=false
STRUCTURED_NLP_FUSION_WEIGHTS_SELECTED=false
CG_CUR_4_CHANGED=false
M2_SPECIFICATION_CHANGED=false
M5_SPECIFICATION_CHANGED=false
M7_SPECIFICATION_CHANGED=false
PUBLIC_NLP_MODEL_SELECTED=false
PUBLIC_NLP_WEIGHTS_SELECTED=false
PUBLIC_EXPLORATION_MODEL_SELECTED=false
```

`NLP-POSITION-E` cannot advance in this round. A later fusion experiment would
require its own governed objective, labels, lineage, weights, ablations,
explanation contract, bias review, and public-safety decision.
