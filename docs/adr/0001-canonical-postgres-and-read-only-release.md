# ADR 0001: Canonical PostgreSQL and read-only releases

- Status: Accepted for the v49 architecture baseline; implementation pending
- Date: 2026-08-10
- Scope: v49 data platform and frontend read boundary

## Context

v48 has two frozen representations with different authority:

- `generated/public_surfaces_prefreeze_candidate_v48.json` is the canonical v48 candidate.
- `data/prefreeze_candidate_v48.sqlite` is a read-only query snapshot and does not supersede the JSON.

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
| `research` | Taxonomy, registered relation types, nodes, edges, trees, folders, dossiers, and memberships. |
| `workflow` | Import runs, review queues, decisions, gate results, promotions, and idempotency records. |
| `release` | Sealed release identities, manifests, projections, asset inventory, and reconciliation receipts. |
| `api_v1` | Versioned read views/materializations consumed by the read API; no canonical writes. |

Writes flow inward through `raw`, explicit transformation/provenance records, reviewed normalized tables, and promotion gates. Frontend reads flow outward only through `ArchiveRepository`, backed by `api_v1` or a validated immutable release. Browser code never connects to PostgreSQL and never treats a database row as a UI contract.

An immutable release is a reproducible projection of one accepted PostgreSQL state. It is not a second writable database. Once sealed:

- its release ID, manifest bytes, asset bytes, row counts, and hashes cannot change;
- `UPDATE` and `DELETE` are denied for sealed `release` rows;
- any content change creates a new release ID;
- the consumer pins the exact release ID and manifest SHA-256;
- a `current` alias may resolve a release once, but is never embedded in evidence or shard references.

`api_v1` exposes only accepted, rights-safe, release-scoped projections. It cannot trigger ingestion, review, promotion, or mutation.

## Authority rules

1. v48 artifacts stay byte-for-byte read-only. Migration imports reference their hashes and never rewrite them.
2. Raw source literals are preserved even when a normalized value is created.
3. PostgreSQL becomes canonical for v49 only after all cutover gates pass. Before then, v48 remains the production rollback source.
4. Queryable domain relationships are represented by typed tables and joins, not opaque JSONB.
5. JSONB is permitted for immutable raw payloads, provider-specific extensions, and non-authoritative diagnostics only.
6. `release` and `api_v1` are derived layers; they cannot be used to write back into `core`, `research`, or other canonical schemas.

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

## Follow-up boundary

This ADR authorizes architecture only. It does not authorize schema creation, data import, export, frontend rewiring, deployment, or v48 mutation. Those actions require the gates in `ACCEPTANCE_GATES.md`.
