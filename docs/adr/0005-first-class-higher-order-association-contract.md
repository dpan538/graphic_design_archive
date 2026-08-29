# ADR 0005: First-class higher-order association contract

- Status: Accepted for additive contract implementation
- Date: 2026-08-28
- Authority: Round 16B checkpoint parent `e5ddbc443c4a0a28004034cba439340ecdeb9a75`
- Scope: `trace/exploration/v3` semantic contract only

## Context

The v2 Exploration read model is binary: it treats pair associations as edges and derives compositions from the pair graph. That model cannot preserve an evidence-supported group when some internal pairs are absent, and pair connectivity cannot prove global historical coherence. Association and composition identity are also materially different: an association is an evidence-bearing semantic object, while a composition is a visual or navigational realization.

## Decision

Introduce a parallel, additive v3 contract. A governed association has a stable identity plus append-only revision; exact bounded participant senses are represented by incidence records. Pair associations have arity two. Higher-order associations have arity three or greater and **must** set `pair_projection_policy=NONE`. A higher-order record never manufactures pair associations.

Identity material includes association kind, normalized participant concept and sense identities, meaningful order and roles, and bounded historical/contextual scope. The executable projection maps stored `/scope` to the exact `scope_identity` keys `scope_id`, `historical_case_ids`, `time_bounds`, `geographies`, `institutions`, `actors`, and `mechanisms`; every set-valued scope array is sorted before hashing. Unordered participant storage is canonical, while ordered participants retain contiguous zero-based ordinals. Four committed identity-branch receipts expose both full identity materials and independently recomputable incidence identifiers for permutation, order, and role reassignment tests. Revision material additionally binds evidence, review, authority, activation, qualifications, conflicts, and version. Semantic and presentation hashes are separate so a layout change cannot change the claim identity and a claim change cannot hide behind a rendering hash.

The normative canonicalization, field projections, aliases, array-order rules, identifier prefixes, digest truncation, and revision wrappers are machine-readable in `v3-semantic-hash-binding-contract-v1.json` and embedded in the fixture bundle. Implementations and independent verifiers must reconstruct hashes from that committed contract rather than infer them from generator code.

Governed scopes, vocabulary concepts, and bounded concept senses are first-class records. An `ACTIVE` concept or sense must be association-eligible and carry final governed authority; every association incidence resolves the exact concept, sense, and governed scope. Evidence review, global-coherence review, rights, final authority, conflict resolution, bounded-scope compatibility, synthesis validity, and product policy are separate fact-derived, fail-closed activation gates. `ACTIVE` requires nonempty evidence and locators, no unresolved conflicts, zero unsupported bridges, exact support-mode/disposition provenance, a final supporting disposition, and a passing global-coherence decision. Synthetic controls can exercise `ACTIVE` in the `SYNTHETIC_CONTROL` realm but never create a production fact or product path.

Every internal pair claim resolves an independently governed active `PAIR` revision, its exact two endpoint senses, and both parent and pair incidence identities. The invalid-clique control therefore contains six actual active pair revisions while its four-term group remains globally invalid; the sparse valid group contains only its two governed pair claims and invents no others.

Compositions contain explicit association realizations and trace each realization to an association revision. A first-class composition-coherence review binds the composition, association revisions, realization identities, incidences, final authority, and the global decision. A `PAIR` must realize as `PAIR_EDGE`; a `HIGHER_ORDER` association cannot realize as a pair edge or a participant subset. Product eligibility is allowed only when the composition review and every traced association are active, coherent, production-authorized, and product-eligible. Renderability is not evidence. Navigation derives bipartite validity from unique, referentially complete concept/association nodes and incidence-owned path steps. Workflows preserve both association revision and realization identifiers; exports derive and bind their projection-preservation records.

The only compatibility adapter is one-way: a governed v2 binary pair can be represented as a v3 `PAIR`. Higher-order inputs and reverse v3-to-v2 conversion are forbidden because either would erase or invent semantics.

## API and persistence boundary

The reserved namespace is `/api/trace/exploration/v3`. This checkpoint defines schemas but does not create routes, runtime code, database tables, or production records. Any later database work must be forward-only (v50 or later), reuse governed provenance identities, leave frozen v49 artifacts unchanged, and store association identity/revision, incidence, review, realization, composition, state, workflow, and export as distinguishable records.

## Consequences

- Scope, concept, bounded-sense, pair, higher-order, incidence, association-realization, composition-coherence-review, composition, state, workflow, and export counts are reported separately.
- Sparse or disconnected internal pair graphs are representable without projection.
- A complete pair clique can fail global coherence.
- A renderable composition can remain product-ineligible.
- Pending or non-final review cannot become active.
- Existing v2 behavior and frozen v49 artifacts remain unchanged.

## Non-authorizations

This ADR does not authorize production association activation, product eligibility, closure, v2 mutation, v49 mutation, database migration, deployment, main updates, tags, or history rewriting.
