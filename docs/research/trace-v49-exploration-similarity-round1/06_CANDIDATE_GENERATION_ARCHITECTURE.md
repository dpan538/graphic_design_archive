# Candidate-generation architecture

## Architectural decision under test

Exploration retrieval is a two-stage analysis pipeline:

```text
public governed/approved records
  -> deterministic inverted candidate index
  -> bounded object-local candidate set
  -> separately selected analysis model
  -> affinity + comparability profile
  -> explanation
```

Candidate generation maximizes controlled recall; scoring evaluates affinity.
Retrieval through a posting is not score credit. The modules may share an
immutable normalized public record view, but the candidate generator cannot
import a scoring model and the scorer cannot depend on how a candidate entered
the set.

No candidate architecture is selected by this contract. CG-CUR-1 through
CG-CUR-6 remain benchmark variants until recall, reduction, bias, hubness, and
performance evidence is evaluated.

## Public-only deterministic index

`build_exploration_candidate_index(records, ...)` accepts the sealed normalized
public cohort and constructs in-memory token-to-public-ID postings. It rejects:

- a non-public object ID;
- a duplicate public ID;
- a held record or held disposition;
- a residual-curation or interaction reference outside the public cohort; and
- malformed temporal or geography fields.

The index contains public surface IDs only. It does not contain internal UUIDs,
held IDs, private values, or a pair table. Its deterministic receipt binds the
schema and implementation version, sorted object IDs, direct postings,
curatorial recall postings, residual-curatorial postings, interaction postings,
and `randomnessAffectsCandidateSet=false`.

## Posting namespaces

Direct governed or approved postings are family- and field-qualified:

| Family | Fields | Role |
| --- | --- | --- |
| Context | medium, theme, movement context | governed direct retrieval |
| Temporal | decade | governed retrieval alias for temporal extent |
| Geography | governed geography; deterministic geography class | assignment is governed direct retrieval; class is candidate/explanation fallback only |
| Source | source identity | optional approved retrieval; corpus-bias diagnostics required |
| Descriptive | object type, observed creator | optional approved retrieval |
| Interaction | approved bounded cell token | high-information retrieval only; never duplicate base credit |

Unknown, not-governed, or no-published-movement values do not receive postings
as shared positive evidence. A direct posting may be omitted when its document
frequency exceeds a declared maximum ratio; the current analysis default of
0.25 is a benchmark parameter, not a selected threshold.

`SIG-GEOGRAPHY-CLASS` is derived from `SIG-GEOGRAPHY-ASSIGNMENT`: all 93
governed geography IDs deterministically map to one class. Its posting may
recover broader geography candidates or support an explanation, but it is not
an independent feature and adds zero affinity beside its assignment parent.

Raw curated memberships occupy a separate `curatorialRecall` namespace. They
may supply candidate recall reasons containing support and denominator, but
`scoringAllowed=false`. A `curatorialResidual` namespace can contain only
memberships previously approved by lineage review. Round 6 finds zero such
signals, so the current residual namespace is empty.

## Curatorial candidate variants

Every run declares exactly one of the six variants:

| ID | Curatorial recall rule | Required interpretation |
| --- | --- | --- |
| `CG-CUR-1` | any shared curated container | high-recall negative reduction baseline; no score credit |
| `CG-CUR-2` | at least two shared curated containers | shared-count filter; no score credit |
| `CG-CUR-3` | at least one shared container at or below the declared support threshold | support-sensitive recall; low support is not importance |
| `CG-CUR-4` | sum of declared information weights reaches a threshold | information-weighted recall; weights and support denominators exposed |
| `CG-CUR-5` | residual curation only after governed source-fact removal | currently no residual postings because residual count is zero |
| `CG-CUR-6` | no curation; governed/approved direct features only | direct-retrieval control |

Curatorial support thresholds, information threshold, and broad-container stop
ratio are run parameters. Stopping a broad posting changes candidate recall,
not a hidden affinity score. The generator records direct and curatorial
candidate counts separately.

## Object-local retrieval contract

`generate_exploration_candidates(index, query_id, ...)`:

1. validates the query against the public index;
2. gathers qualifying direct and optional interaction postings;
3. gathers the declared CG-CUR recall layer;
4. unions and deduplicates public candidate IDs;
5. excludes the selected object;
6. orders the unscored set lexically by public candidate ID; and
7. hashes candidate IDs, index receipt, and declared parameters.

The candidate result contains query ID, variant, candidate IDs, bounded
retrieval reasons, direct and curatorial counts, total pool size, 7,994-object
denominator, reduction ratio, receipt hash, and
`randomnessAffectsCandidateSet=false`.

Retrieval reasons expose reason type, family, qualified token, observed support,
and corpus denominator. Curatorial reasons additionally state that scoring is
not allowed. These reasons explain recall; they are not affinity contributions.

## Scoring and explanation boundary

`score_pair` or `rank_candidates` accepts candidate IDs from this stage but
recomputes family evidence from the independent basis. It does not convert
posting count into score. The explanation layer joins:

- candidate retrieval reasons from this module;
- scored independent-family contributions from the selected analysis model;
- ignored lineage duplicates;
- unavailable-family comparability state; and
- optional separately residualized interaction evidence.

Raw curated Jaccard M0 is isolated in `negative_control.py`. It is not imported
by this candidate module, by scoring-eligible model code, or by any future
public/runtime scorer.

## Determinism and ordering

Candidate membership and ranking use no randomness. Input records, values,
postings, candidate IDs, and reasons are normalized and sorted. Scored scalar
rankings use descending diagnostic score and ascending candidate public ID.
M8 uses deterministic Pareto layers and public-ID tie resolution without an
undocumented scalar.

Duplicate titles remain distinct because identity is the public object ID.
Seeded randomness may later position a fixed result set under a separately
declared layout policy; it cannot alter the index, candidate set, affinity,
comparability, or rank.

## Offline reference and candidate recall

For research evaluation, scalar models may stream the complete 31,956,015
unordered public pairs. The streamer retains only bounded per-object top-k
heaps and aggregate hashes. It never materializes or commits pair rows.

`candidate_recall` compares CG-CUR candidate sets with each model's exhaustive
top 10, 20, and 50. Report macro and micro recall, candidate-pool P50/P90/P95/
P99/MAX, zero-candidate count, near-full-corpus count, index bytes and heap,
build time, candidate runtime, and object-local query P50/P95. The provisional
shortlist target is recall@20 at least 0.98 with material reduction; a miss is a
documented trade-off rather than grounds to weaken the reference.

## Persistence and deployment boundary

Only source code, bounded aggregate results, bounded top-k hashes, and
release-style receipts may be committed. The in-memory index and streamed pair
values are analysis artifacts, not database migrations or frontend payloads.
There is no request-time all-pairs scan, stored 28-million-row curatorial pair
table, client pair matrix, public API, route, renderer, or runtime dependency in
this round.
