# ADR 0001: Canonical PostgreSQL and read-only releases

- Status: Accepted for the v49 architecture baseline; implementation pending
- Date: 2026-08-10
- Scope: v49 data platform and frontend read boundary

## Context

v48 has two frozen representations with different authority:

- `generated/public_surfaces_prefreeze_candidate_v48.json` is the canonical v48 candidate.
- `data/prefreeze_candidate_v48.sqlite` is a read-only query snapshot and does not supersede the JSON.

The authority decision is stricter for migration: the JSON is the only v48 migration input. SQLite is reconciliation-only; transfer and TRACE manifests are integrity evidence; Search, atlas, catalogs, and shards are derived products and cannot supply canonical rows.

The current frontend imports the large public JSON as its binding contract, builds additional search data separately, and fetches TRACE atlas/catalog/shards inside UI components. This couples storage shape, release packaging, and presentation code. It also makes it possible to mix resources from different versions.

v49 needs a canonical transactional model for normalized data, while preserving deterministic, inspectable, cacheable read releases.

## Decision

PostgreSQL is the canonical system of record for v49 after a candidate has passed the migration and promotion gates. This decision does not retroactively change v48 authority: the frozen v48 JSON, SQLite snapshot, TRACE assets, and receipts remain immutable inputs and rollback evidence.

The database is divided into these schemas:

| Schema | Responsibility |
|---|---|
| `raw` | Immutable source bytes, source payloads, capture metadata, and content hashes. |
| `core` | Normalized objects, agents, places, concepts, dates, collections, and their joins. |
| `provenance` | Source records, field assertions, evidence locators, transformations, citations, and lineage. |
| `rights` | Digital representations, rights statements, display policy, license, credit, and access constraints. |
| `research` | Registered predicates/relation types, epistemic claims, semantic relations, corpora/missingness, analysis runs, TRACE projections, trees, folders, dossiers, and memberships. |
| `workflow` | Import runs, review queues, decisions, gate results, promotions, and idempotency records. |
| `release` | Sealed release identities, manifests, projections, asset inventory, and reconciliation receipts. |
| `api_v1` | Versioned read views/materializations consumed by the read API; no canonical writes. |

Writes flow inward through `raw`, explicit transformation/provenance records, reviewed normalized tables, and promotion gates. Frontend reads flow outward only through `ArchiveRepository`, backed by `api_v1` or a validated immutable release. Browser code never connects to PostgreSQL and never treats a database row as a UI contract.

An immutable research release is a reproducible projection of one accepted PostgreSQL state and one declared corpus. It is not a second writable database. The rights-safe external-visual delivery view is carried by a separately sealed visual registry so a takedown or endpoint-health change never mutates or forces resealing of research claims. Once either boundary is sealed:

- its release ID, manifest bytes, asset bytes, row counts, and hashes cannot change;
- `UPDATE` and `DELETE` are denied for sealed `release` rows;
- any content change creates a new release ID;
- the consumer always pins `(researchReleaseId,researchManifestSha256)` and atomically pins a compatible `(visualRegistryVersion,visualRegistrySha256)` when visual composition is selected;
- each boundary has its own manifest, detached sidecar, lifecycle, and CAS-protected `current` pointer;
- a `current` alias may resolve once, but is never embedded in evidence, citations, manifests, or shard references.

`api_v1` exposes only accepted, research-release-scoped projections, optionally combined with a compatible rights-safe visual-registry projection. Registry absence is a normal research-only state; an explicit mismatch is reported and never falls back. It cannot trigger ingestion, review, promotion, or mutation and never exposes a held/link-only pixel URL.

`core.entity` is a closed UUID supertype whose subtype row is enforced by FK and entity kind. Semantically specific links target subtype FKs; deliberately multi-kind links target `core.entity` plus an allowed-kind constraint. Canonical tables never use unconstrained `target_type + target_id`.

A `core.archive_object` is operationally one catalogued design-object record in a governed cohort. It does not, by identity alone, assert a unique intellectual work. Possible identity equivalence, merge, and split are evidence-bearing curator decisions with persistent crosswalk/redirect history.

A source assertion, accepted canonical assignment, evidence item, curator decision, epistemic research claim, semantic relation, and TRACE projection are different records with typed bridges. TRACE is a release presentation of eligible claims/relations for a declared corpus; it is never canonical relation or claim identity. The four initial epistemic classes are `documented_source_statement`, `scholarly_claim`, `computed_association`, and `causal_interpretation`.

## Authority rules

1. v48 artifacts stay byte-for-byte read-only. Only the canonical JSON supplies migration records; all other frozen/read products are reconciliation or integrity evidence.
2. Raw artifact bytes, length, and SHA-256 are lexical authority. JSONB is a versioned parsed projection and cannot reproduce or certify source bytes.
3. Raw source literals are preserved even when a normalized value is created.
4. PostgreSQL becomes canonical for v49 only after all cutover gates pass. Before then, v48 remains the production rollback source.
5. Queryable domain relationships are represented by typed tables and joins, not opaque JSONB.
6. JSONB is permitted for parsed raw payloads, provider-specific extensions, and non-authoritative diagnostics only.
7. `release` and `api_v1` are derived layers; they cannot be used to write back into `core`, `research`, or other canonical schemas.
8. Search is a release projection, never a second canonical database or a source for missing migration rows.
9. Rights observations/assessments, provider-policy versions/evaluations, delivery decisions, endpoint-health observations, and takedown state are independent records. Unknown, missing, conflicting, or stale rights/policy defaults to `LINK_ONLY` or `CITATION_ONLY`; only `REMOTE_IMAGE` may expose an allowlisted v1 remote-pixel locator, and HTTP/API/IIIF accessibility never establishes authorization.

## Consequences

Positive consequences:

- storage, release packaging, API DTOs, and visual presentation can evolve independently;
- relationships, evidence, rights, and review state gain enforceable foreign keys and gates;
- release artifacts remain static, hash-verifiable, and CDN-cacheable;
- frontend CI can run against a pinned fixture without a live database.

Costs and constraints:

- migrations and projection queries become reviewed product artifacts;
- releases need deterministic export, reconciliation, and seal procedures;
- PostgreSQL backup/restore, row-level privileges, and operational monitoring are required before cutover;
- dual-read parity is mandatory; an architecture document alone is not migration completion.

## Alternatives rejected

- Keep the large JSON as the permanent canonical model: rejected because it conflates raw, canonical, release, and UI concerns and cannot enforce relational integrity.
- Make SQLite the v49 writable canonical store: rejected because the current SQLite file is explicitly a frozen read snapshot and does not provide the intended multi-writer workflow boundary.
- Let the frontend query PostgreSQL directly: rejected because it exposes internal schemas, bypasses release/rights gates, and couples UI deployment to database migrations.
- Store all multi-value fields as JSONB: rejected because canonical queryable relations require provenance-bearing joins and constraints.
- Reuse the legacy `db/*.sql` public-schema chain as v49 DDL: rejected because it lacks the v49 subtype, typed-FK, role, seal/CAS, research-claim, and visual-registry invariants.

## Follow-up boundary

This ADR authorizes architecture only. It does not authorize schema creation, data import, export, frontend rewiring, deployment, or v48 mutation. Those actions require the gates in `ACCEPTANCE_GATES.md`.

Identity, cardinality, state, release-seal, and privilege decisions are normative in `docs/architecture/DDL_DECISION_PACK_V49.md`. Research claims/corpora and visual-registry decisions are normative in `docs/adr/0004-research-claims-corpora-and-visual-registry.md`. Phase 1C and Phase 1D provide decision-closure evidence for the Phase 1B findings, but only the independent joint receipt may mark pre-DDL readiness; no database or release implementation is claimed here.
