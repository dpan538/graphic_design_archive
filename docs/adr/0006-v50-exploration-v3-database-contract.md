# ADR 0006: v50 Exploration v3 database contract

- Status: accepted for Round 16B research-schema verification
- Date: 2026-08-28
- Authority: Round 16B branch only
- Supersedes: no v49 object and no v2 Exploration contract

## Context

The frozen v49 database represents canonical claims and binary semantic
relations, while the committed Exploration v3 semantic contract distinguishes
pair associations, higher-order associations, incidences, compositions,
interaction states, transitions, workflows, and exports. A higher-order
association cannot be stored faithfully by manufacturing every internal pair.
Likewise, a renderable composition is not evidence that its associations or
the composition as a whole are historically coherent.

`database/FROZEN_V49.md` requires database version 50 or later, a new
forward-only object sequence, unchanged v49 hashes, and a v50 ADR. Round 16B
authorizes research capability and verification, but not production data
activation, deployment, publication to `main`, or mutation of a sealed v49
release.

## Decision

Add the `exploration_v3` governed research schema and the positive-allowlist
`api_v3` read schema after the complete frozen v49 replay.

The model preserves these boundaries:

1. `association` is stable semantic identity; `association_revision` is an
   immutable reviewed version. Stable identity is the exact Checkpoint 008
   compact-JCS projection over association kind, canonical participant senses,
   immutable bounded scope identity, order semantics, and role semantics.
   `scope_context_qualifications` is a complete revision-level snapshot: v1
   matches the source governed scope, and qualification-only successors change
   revision semantic content without changing association identity.
2. `PAIR` requires arity two and `pair_projection_policy=NOT_APPLICABLE`.
   `HIGHER_ORDER` requires arity three or greater and
   `pair_projection_policy=NONE`.
3. `association_incidence` owns exact concept, bounded-sense, optional order,
   optional role, scope, and qualifications. Deferred validation requires the
   incidence cardinality to equal declared arity. Active concepts and senses
   independently require eligibility and final authority even when isolated;
   production vocabulary authority is never synthetic.
4. Evidence identity, locators, synthesis steps, conflict resolutions,
   authority, association review, and global coherence remain distinguishable
   records. `ACTIVE` fails closed unless evidence, rights, scope, bounded
   senses, synthesis, conflict, uncertainty, final review, and authority gates
   all pass.
5. `internal_pair_link` may cite an independently governed active pair as
   composite support. It never creates a pair row, and unlisted internal pairs
   carry no claim.
6. `association_realization` and `composition_revision` are presentation and
   navigation objects, not association identity. A higher-order revision may
   never realize as `PAIR_EDGE` or as a participant subset.
7. Navigation uses explicit bipartite concept/association nodes and
   incidence-bound path steps. `interaction_transition` is a separate object;
   it is not inherited from Round 16A's pair-derived transition ledger.
8. Workflow and export records preserve association revision and realization
   identity. Workflow membership equals the complete realization set of every
   state composition, and graph reachability is recomputed from stored
   transitions. Export preservation rows equal that complete realization set
   and bind the exact pair-projection policy.
9. Product-eligible transitions, workflows, and exports fail unless every
   referenced composition is product eligible and every referenced
   association is active, finally reviewed, coherent, production-authorized,
   and product eligible. Association-bearing transition traces must be complete
   triples of incidence, revision, and realization; partial traces fail.
10. Only the unique unsuperseded association/composition heads can remain
    active or product-visible. A successor therefore fail-closes every dynamic
    dependent composition, navigation state, transition, workflow, export,
    and child provenance surface rather than falling back to an older active
    revision.
11. Runtime roles receive no direct governed-table DML. The API reader sees
    only final production rows through `api_v3`, including exact association
    and participant scopes, bounded senses, rights-cleared evidence locators,
    final coherence provenance, exact navigation nodes/path steps, workflow
    state/revision/realization/transition membership, and export-preservation
    rows; the active association carries its exact revision-specific scope
    context snapshot, and reviewers and auditors receive narrow read-only
    views.

Final association and composition reviews, active bounded senses, navigation
states, workflows, exports, and locator-bearing evidence use an explicit
`aggregate_seal`. The seal is inserted only after all children and carries the
compact-JCS SHA-256 of the complete canonical parent-and-governed-child
aggregate—not a self-asserted parent hash. Timestamp material is normalized to
UTC and textual sets are C-ordered. Append-only rows prevent replacement.
Seal and child INSERTs take the same fail-fast aggregate advisory lock and
exact parent-row lock at READ COMMITTED: a concurrent contender retries after
SQLSTATE `40001`, a visible sealed parent rejects membership with `55000`, and
REPEATABLE READ/SERIALIZABLE membership writes are explicitly rejected with
`25000`. A correction therefore creates a new association/composition revision
or a new governed aggregate identity. Association and composition lineage is
same-parent, non-forking, and must supersede the immediately preceding revision
number.

`COHERENT` composition decisions always require final authority, PASS global
coherence, compatible bounded senses/case scope/roles/topology, one historical
configuration, and zero unsupported bridges, independent of product
eligibility. Navigation paths are contiguous and their terminal node is the
declared focus.

All governed v50 rows are append-only. A correction creates a new revision.
No v50 function projects a hyperedge into pairs, alters v49 binary relations,
or promotes a research object into an existing release.

## Verification boundary

The v50 verifier recomputes every SHA-256 in `FREEZE_V49.json`, reconstructs
and checks its migration, function, view, and role arrays, and derives the
40-file database replay prefix from those verified arrays. The cluster-role
file remains a separately verified precondition. Only then does the replay add
exactly migration 014, function 020, view 003, and grant file 008. The
static preflight permits replay while the execution receipt is pending; the
final verifier then requires the manifest-bound Checkpoint 011 receipt with two
distinct passing fresh databases, PostgreSQL 16 identity, zero fixture
residue, governed command IDs, and identical normalized schema hashes. The
transaction-scoped test proves:

- one active sparse synthetic hyperedge with zero pair associations;
- activation-before-review rejection;
- higher-order-as-pair-edge rejection;
- distinct state, transition, workflow, and export identity;
- product transition, workflow, and export rejection when dependencies are
  product-ineligible;
- product association rejection when an exact concept or bounded-sense
  participant is product-ineligible, and partial transition-trace rejection;
- isolated active concept/sense eligibility, authority, and production
  non-synthetic-authority rejection;
- canonical aggregate-digest vectors, timezone/insertion-order invariance,
  post-seal association/composition/navigation/workflow/export child rejection,
  and real two-session child-first/seal-first schedules in a disposable cloned
  database with exact `40001`/`55000`/`25000` outcomes;
- nonproduct coherent-review parity, navigation continuity/terminal focus,
  exact workflow realization coverage, actual graph reachability, exact export
  preservation, and same-parent monotonic revision lineage;
- exact positive rows and relationship sets through every allowlisted
  association/composition/navigation/workflow/export child-trace view and
  grant, followed by dynamic full-chain removal on association supersession;
- qualification-only association succession with unchanged stable identity,
  changed revision context/semantic aggregate material, and exact API exposure;
- append-only governance, API positive allowlisting, and role isolation;
- transaction rollback with zero fixture residue.

Synthetic controls never create production facts or API-visible records. The
production-labelled negative fixture is explicitly product-ineligible and is
rolled back. A passing database contract therefore proves representational
and integrity capability only; it does not prove higher-order research
closure, product activation, deployment readiness, or Function 3 closure.

## Consequences

- The v49 freeze manifest and every listed v49 file remain byte-identical.
- Existing `/api/v1` and Exploration v2 consumers remain unchanged.
- A later governed population migration must bind committed Round 16B
  identities and hashes, and must separately authorize any production-active
  row.
- Database transition counts are not imported from Round 16A. Any populated
  v3 transition universe must be regenerated from governed v3 artifacts.
