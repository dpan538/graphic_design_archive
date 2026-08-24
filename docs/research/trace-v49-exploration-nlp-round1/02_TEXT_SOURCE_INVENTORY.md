# Text-source inventory

## Evidence state

`DOCUMENT_STATE=SEALED_PRECOMMIT_PASS`

The mandatory inventory gate is complete at the schema-and-field level:

```text
TEXT_SOURCE_FIELD_COUNT=37
TEXT_SOURCE_FIELD_CLASSIFIED_COUNT=37
UNCLASSIFIED_TEXT_FIELD_COUNT=0
NLP_TEXT_FIELD_REGISTRY_VERSION=trace-nlp-text-field-registry-v1
NLP_TEXT_FIELD_REGISTRY_SHA256=b70c98f8a52de2ae5bbaf5d2d69db85381bfa59a0d07722df0823018d2aec3b6
```

Population and rate columns are reconciled in
`03_NLP_TEXT_FIELD_REGISTRY.tsv`; this document states why each source seam is
or is not eligible.

## Frozen source artifacts

| Source artifact | Frozen SHA-256 | Inventory purpose |
| --- | --- | --- |
| `docs/audits/v49-phase2b-migration/18_SURFACE_ROW_LEDGER.tsv` | `48f98f68ca2ec0cef96c82ecc9c01e4129eb9a3f91e08b07ad9a59644a9d4e01` | sole public/held disposition authority |
| `data/prefreeze_candidate_v48.sqlite` | `ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e` | mirror, provenance, and pair-verification audit only |
| `generated/public_surfaces_prefreeze_candidate_v48.json` | `b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48` | canonical public-filtered subjects and source narrative |
| `frontend/generated/trace-context-v1/records.json` | `c767b9661e4cb417cfaae3948d7ed2b974fc88e1dcc9a3686eae90ae8610a9e7` | authoritative governed title and control metadata |
| `frontend/generated/trace-spacetime-v1/record-index.json` | `0f4720672f1e906301e3966dc3970737e3a1e459b27317b47018a2e6445c3dec` | geography/time leakage controls only |
| `docs/audits/v49-exploration-similarity-round1/raw/human-review-summary.json` | `2178df8e22d367cf9ce391d3dfab9f579d7371d4a1aefa1d0b389eb9132d044f` | proof that earlier bounded model output is not corpus input |

Context and Spacetime projections are additionally pinned to
`825f6ecaa9ae1496c8a00ea0fefa5c90319046cf9c1f08a2ef76b9b02df4baeb`
and `f751b0f432ff684fd1000201b910aa397a4d9965468c2f7dd5022d6a4ae01c06`.

## Included aspect authorities

| Field ID | Source seam | Primary role | Decision | Coverage |
| --- | --- | --- | --- | ---: |
| `NLP-FIELD-001` | Context `selectedRecord.title` | `OBJECT_TITLE` | `INCLUDE_TITLE_CHANNEL` | 7,995 |
| `NLP-FIELD-003` | canonical `surfaces[].sourceSubjects` | `OBJECT_SUBJECT_TERMS` | `INCLUDE_SUBJECT_CHANNEL` | 7,838 |
| `NLP-FIELD-004` | canonical `surfaces[].sourceDescription` | `SOURCE_NARRATIVE` | `INCLUDE_SOURCE_NARRATIVE_DIAGNOSTIC` | 7,431 |

The title is the only admitted object-semantic field in the v1 composite.
Subjects remain separate pending leakage review. Source narrative remains a
source diagnostic and never becomes object description.

## Metadata and diagnostic-only seams

Creator attribution and object type are comparison metadata only. Source name,
medium displays, folder titles, representation labels, source provenance,
collection evidence, and source notes may support leakage, holdout, or
explanation diagnostics but add zero object-semantic affinity.

The field registry distinguishes a public-safe display value from permission to
use the value as semantic text. `public_safe`, `rights_safe`, and
`governance_decision` are independent gates.

## Excluded or held mirrors

The audit excludes duplicate title mirrors, partial SQLite capture mirrors,
flattened Search documents, display tables, earlier review output, and dossier,
appendix, registration-card, compound-child, reading-note, and folder-level
text. Exclusion prevents repeated projections from being miscounted as
independent evidence.

Rights labels, provenance language, workflow rationales, uncertainty notes,
private notes, and internal control text are not semantic inputs. Compound
child text is held because it has separate identity and cannot be collapsed
onto its parent surface.

## Investigated but unavailable roles

No governed and populated public seam was established for:

- object alternate title;
- translated title;
- transliterated title;
- subtitle;
- object description;
- object caption;
- abstract;
- OCR or transcription; or
- a verified archive-native multilingual title representation.

One SQLite provenance row names an “Alternate representation,” but it does not
expose a governed alternate-title pair and is held. Schema/table presence is
not treated as evidence that a role is populated, public-safe, or pair-verified.

## Governance consequences

- no unregistered field may enter lexical or dense input;
- same title is never accepted as same identity;
- source-record prose is never relabeled as object description;
- folder and representation labels remain structured controls;
- rights, provenance, source identity, and boilerplate add zero affinity;
- held records are discarded before their text is normalized; and
- any newly discovered seam invalidates the registry hash and requires a new
  governed version rather than silent admission.

Final reconciliation fields:

```text
REGISTRY_TSV_ROW_COUNT=37
REGISTRY_TSV_SHA256=381ff4d1e16bc0f77fa3dd47bce504cfb8feb36f84b8c426af12ae239ed864a1
SOURCE_INVENTORY_RECEIPT_SHA256=87296bf223e2fb3f7da37b2dbc102123bec85fc4d0b16ed65198345c68af9c29
```
