# Exploration candidate explanation contract

## Eligibility rule

No score-only result is eligible for an internal shortlist or future public
consideration. Every candidate must have a deterministic explanation path from
retrieval, through independent-family scoring and comparability, to a pinned
analysis-run receipt.

An explanation describes archive-derived structured evidence. It does not
assert historical relation, influence, causation, contact, lineage, creator
intent, quality, importance, canonicality, or probability of relation.

## Required result structure

Conceptually, every explained candidate contains:

```text
queryId
candidateId
candidateTitle
retrievalReasons[]
affinityContributions[]
distinctiveFeatures[]
ignoredDuplicateSignals[]
unavailableFamilies[]
comparability
broadContainerAttenuation
sourceBiasNotes[]
interactionEvidence[]
methodId
methodVersion
analysisRunId
researchReleaseId
researchReleaseSha256
contextProjectionSha256
spacetimeProjectionSha256
candidateIndexSha256
diagnosticScore?
scoreOnlyResult=false
probability=false
historicalRelation=false
semanticRelation=false
explanationSha256
```

The query identity and candidate identity are public surface IDs. Internal
UUIDs and held identifiers are prohibited. A diagnostic scalar, if present, is
optional display metadata for analysis and cannot replace the family profile.

## Retrieval reasons

Each reason explains why the candidate generator admitted the record. Required
fields are reason type, family or recall namespace, qualified feature/container
identity, observed support, and corpus denominator. It also records candidate
variant and candidate-index hash at the result level.

Direct governed/approved postings may be named as retrieval reasons. Compound
interaction postings must identify their parent dimensions. Curatorial reasons
must state `scoringAllowed=false` unless a future lineage review establishes a
genuine residual. Round 6 has no such residual.

Retrieval count, posting count, and curatorial co-membership are not affinity
contributions.

## Affinity contributions

Every base contribution exposes:

- affinity family;
- field and lineage `signalId`;
- declared model basis/variant;
- numerator and denominator, or explicit source identity where applicable;
- matched public feature IDs;
- bounded family contribution; and
- any cap or attenuation applied.

The eight independent base signals are the only direct scoring candidates.
Temporal decade, same-value aliases, frequency summaries, raw curation, and
compound cells cannot appear as additional base credit for the same fact.
Geography exact assignment overlap is the only geography scoring fact.
`SIG-GEOGRAPHY-CLASS` is its deterministic candidate/explanation fallback and
adds zero affinity.

## Distinctive features

Distinctive evidence names query-only and candidate-only approved features by
family and field. A difference is descriptive, not negative historical
evidence. In Task C, the explicit contrast request determines which difference
is sought; the explanation must identify that request rather than implying a
relation from the difference.

## Ignored duplicates

`ignoredDuplicateSignals` lists lineage-resolved signals observed or available
for explanation that were intentionally excluded from base scoring because
they duplicate, derive from, or aggregate an already represented source fact.

Examples include same-value aliases, curated folders underlying governed
Context/Spacetime facts, temporal decade beside extent, pair/triple cells beside
parents, and rarity/concentration summaries from the same frequency
population. The explanation must make suppression inspectable; it must not
quietly omit the duplicate and then add it through another label.

## Comparability and unavailable families

The explanation repeats the separately computed profile:

```text
observedFamilyCount
eligibleFamilyCount
ratio
jointlyObservableFamilies
unavailableFamilies
```

Unavailability is not a zero-valued positive feature and comparability is not
confidence. Shared unknown, qualified-unknown, no-published-movement, and
not-governed states may be listed in a dedicated MISSING-D diagnostic but add
zero base affinity.

## Broad-container attenuation

When curation affected retrieval or a future approved residual, the explanation
records:

- container identity/type;
- support and denominator;
- support ratio;
- CG-CUR and CUR-W variants;
- stop threshold, smoothing constant, information weight, and cap as
  applicable;
- whether the posting was stopped or admitted; and
- whether the role was recall, diagnostic, or residual scoring.

For the current zero-residual basis, raw memberships can be recall/provenance
only. Raw curated Jaccard M0 never enters this explanation path as production or
public score evidence.

## Source-bias notes

The explanation declares SOURCE-0 through SOURCE-4 treatment and whether source
was excluded, capped, reported without credit, used as an explicit contrast, or
used only for post-ranking diversification. It records relevant source identity
and result-set concentration diagnostics without implying same-source affinity.

SOURCE-4 notes must state that diversification changed order only and did not
change pair scores. SOURCE-3 is valid only for an explicit contrastive task.

## Interaction evidence

Each interaction explanation is separate from parent contributions and exposes:

- interaction ID;
- parent signal IDs;
- observed support and denominator;
- selected statistic and smoothing/shrinkage parameters;
- support threshold;
- residual method and cap;
- bounded residual value; and
- `parentContributionRepeated=false`.

Raw support, lift, PMI, normalized PMI, and log-likelihood measurements are
diagnostics until an explicitly declared bounded residual policy is used. A
support-1 or support-2 cell cannot become dominant evidence.

## Method and run provenance

The explanation carries the research release, Context projection, Spacetime
projection, and candidate-index SHA-256 values directly. The analysis-run ID
resolves those fields to the complete benchmark receipt, including the signal
registry pin omitted from the compact candidate payload.

Every explanation resolves `analysisRunId` to a release-style receipt with:

- model ID and model family;
- implementation version;
- complete parameter set;
- source commit;
- research release ID and hash;
- Context projection ID and hash;
- Spacetime projection ID and hash;
- Exploration signal registry hash;
- candidate-index hash;
- input public cohort count;
- execution seed where relevant, with zero effect on candidates and affinity;
- output summary hash; and
- bounded top-k artifact hash.

The receipt timestamp is metadata outside deterministic hash material. Receipts
are research artifacts and are not written into the frozen database.

## Deterministic identity and hashing

Explanation arrays use stable family/field/signal ordering. Retrieval reasons
use stable reason/family/token ordering. Duplicate signal IDs are deduplicated
and sorted. The serialized explanation and its run receipt use documented
canonical JSON with stable key order and UTF-8 encoding.

The same source data, projection/registry/index hashes, model parameters, and
candidate pair must reproduce the same explanation hash. Seed values,
timestamps, filesystem paths, process IDs, and memory addresses are excluded
from deterministic result material.

## Validation failures

An explanation is invalid if any of the following occurs:

- no retrieval path exists for a returned candidate;
- a scored signal lacks a 64-row lineage record;
- two base contributions share one source-fact group;
- a parent fact is repeated through an interaction;
- shared unknown state receives positive credit;
- comparability or unavailable families are absent;
- a contribution lacks numerator/denominator or applicable source identity;
- curation appears as historical relation or unreviewed residual score;
- map/layout distance appears as geography affinity;
- a same-source match is automatically positive without SOURCE-1;
- method/version or required release/projection/index hashes are absent;
- a held ID, internal UUID, full pair row, or private value is exposed;
- randomness changes retrieval, affinity, comparability, or ranking;
- probability terminology or a relation flag other than false is emitted; or
- a scalar is presented without its family and comparability context.

Every shortlisted sampled result must pass this validation. The benchmark
reports `UNEXPLAINED_SHORTLIST_RESULT_COUNT`; any nonzero value blocks the
affected architecture.

## Human-review rendering boundary

The blinded review packet may render public IDs/titles, retrieval reasons,
shared and distinctive signals, comparability, source notes, and interaction
evidence. It omits diagnostic score labels where they could bias review and
hides model identity behind deterministic profile slots where practical.

Reviewer response fields remain blank at generation time.
`HUMAN_REVIEW_COMPLETED=false` is mandatory until researchers actually provide
judgments. An intelligible explanation does not convert an exploratory signal
into a historical claim.

## Current status

This contract is ready for analysis validation. It does not declare that every
benchmark result has passed, select a shortlist, choose final weights, expose a
public score, or authorize a route, API, renderer, or template registry.
