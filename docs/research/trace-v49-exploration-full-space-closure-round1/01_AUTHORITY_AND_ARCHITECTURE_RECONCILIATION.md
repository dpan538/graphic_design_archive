# Authority and architecture reconciliation

## Versioned authority decision

This Round 16A clarification is `trace-exploration-authority-v2`. It supersedes contradictory *active* Round 16 statements but does not rewrite or invalidate the preserved Round 8–16 research and audit packages. The Round 8 conceptual boundary remains the governing product definition. Round 16 remains a real-data preprocessing and implementation baseline, not a closure proof.

There is one active authority for the user-facing Exploration Field: a conceptual vocabulary-and-generic-association field whose public unit is a governed conceptual vocabulary node, not an archive object. A generic association permits evidence-qualified proximity only. It does not encode a typed, causal, directional, temporal, hierarchical, quantitative, similarity, or importance claim.

## Data-authority matrix

| Question | Governing answer |
|---|---|
| What may generate the candidate vocabulary universe? | The preserved Round 9–16 scholarly vocabulary, grammar, inquiry, gap, association, and Round 16 addition registries. All dispositions are included before final classification. |
| What may activate product vocabulary? | Exact attestation, academic support, a bounded sense and scope note, ambiguity handling, complete provenance, and at least one governed category-entry binding. Association pass/fail status is not a vocabulary-eligibility rule. |
| What may generate an association? | Only the uniform Round 14-derived evidence protocol applied to every unordered pair in the frozen active vocabulary. Database occurrence, metadata, co-occurrence, Search, Context, and Spacetime cannot create or upgrade an association. |
| What may determine category entry? | The four folder types verified directly in the frozen database plus term-level scholarly/category provenance. The database proves that each navigation type is real; it does not invent historical semantics. |
| What may appear in the public API/export? | Concept IDs and labels, generic association IDs/endpoints and evidence summaries, canonical compositions, category navigation IDs, state/action data, hashes, bounded source/provenance summaries, and presentation tokens. |
| What remains internal only? | Database row IDs/titles, object/folder witness rows, eligibility-ledger rows, complete source-review material, query diagnostics, rejected evidence, Context/Spacetime IDs, and full census ledgers. |

## Search boundary

Search is a separate project block and is not a TRACE function. Round 16A neither evaluates nor changes Search. Search results, DTOs, indexes, routes, ranking, and manifests are prohibited semantic and runtime inputs.

Round 16's use of `frontend/generated/search-v49/manifest.json` to identify the database is removed in the versioned Round 16A path. Database identity comes directly from `database/FREEZE_V49.json`, `database/FREEZE_V49.sha256`, `docs/releases/v49/RELEASE_MANIFEST.json`, the frozen SQLite content hash, the canonical release JSON hash, and the Phase 2B eligibility ledger. No Search file is needed to generate or serve Round 16A.

## Context and Spacetime boundary

Context Canvas and Spacetime are independent TRACE functions. Round 16A does not read their manifests, generated records, identifiers, projections, or APIs. They cannot affect vocabulary eligibility, evidence, association qualification, composition, topology, pruning, splitting, seed selection, category entry, focus, ranking, state, workflow, or export.

## Real-database grounding without object exposure

The frozen database has four permitted uses:

1. certify the snapshot/schema/content identity and 7,995-public/7,928-held boundary;
2. verify the exact folder-type set `region`, `theme`, `medium`, and `movement`;
3. verify that each type and any retained internal anchor folder exists and binds eligible rows;
4. retain internal reproducibility witnesses for those checks.

Neither object text nor folder co-occurrence supplies vocabulary or association evidence. Internal witness rows are never copied into the compact production model, public API, SVG, or PNG.

## Round 16 field disposition

| Round 16 field/input | Round 16A treatment |
|---|---|
| Search manifest identity fields | Removed from v2 generation and runtime. |
| Context/Spacetime manifests and record indexes | Removed from v2 generation and runtime. |
| `archive_object_refs`, object IDs and titles | Retained only in frozen Round 16 history and new internal database-authority receipts; prohibited from v2 production/public artifacts. |
| `context_refs`, `spacetime_refs`, `include_context`, `include_spacetime` | Removed from v2 API and production read model. |
| Round 16 26-term vocabulary | Retained as one input source and legacy reconciliation set, not treated as the final universe. |
| Round 16 11 compositions, 52 states, 816 transitions, 5 workflows | Retained as regression examples and reconciled to the new census; not treated as final counts. |
| Database snapshot/schema/content/freezing fields | Retained, renamed where needed to identify the direct canonical sources, and independently verified. |
| Source/evidence summaries | Retained after removal of archive-object, Context, and Spacetime references. |
| API v1 | Preserved as historical contract evidence; the public production contract is explicitly versioned v2. An unchanged leaking v1 endpoint cannot remain a live public route. |

## Reconciliation gates

- `ACTIVE_EXPLORATION_AUTHORITY_COUNT=1`
- `AUTHORITY_CONTRADICTION_COUNT=0` only after `EXPLORATION_CURRENT.md`, `PROJECT_LOG.md`, v2 code, and reachable routes agree with this document.
- `SEARCH_RUNTIME_DEPENDENCY_COUNT=0`
- `SEARCH_SEMANTIC_INPUT_COUNT=0`
- `CONTEXT_SEMANTIC_INPUT_COUNT=0`
- `SPACETIME_SEMANTIC_INPUT_COUNT=0`
- public archive-object, Context, and Spacetime reference counts must all be zero.

