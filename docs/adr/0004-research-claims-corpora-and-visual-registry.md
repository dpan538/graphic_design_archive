# ADR 0004: research claims, corpora, and independent visual registry

- Status: Accepted semantic contract; physical DDL remains blocked by the evidence gates below
- Date: 2026-08-11
- Decision scope: operational object meaning, epistemic claims, semantic relations, TRACE projections, research corpora, missingness, external visual federation, and machine identity

## Context

The v49 Phase 1B audit found that the frozen v48 products are strong operational and reconciliation evidence but do not justify three shortcuts:

1. one canonical row is not proof of one globally unique intellectual work;
2. a frozen TRACE triple is not simultaneously a source statement, scholarly claim, normalized semantic relation, and timeless graph fact;
3. an accessible URL, IIIF endpoint, healthy redirect, or permissive metadata statement is not authorization to deliver pixels.

The audit also found that the 15,923-object Browse Index is not a declared strict research corpus, and that external visual policy/health/takedown must change independently of a citable research release. These distinctions affect physical keys, foreign keys, state vocabularies, manifests, cursors, caches, and API envelopes, so they must be normative before DDL.

## Decision 1: operational archive object

`core.archive_object` means an **operational catalogued design object**: the stable subject around which this archive binds source descriptions, public surface identifiers, representations, classifications, research claims, and release projections.

For the v48 seed, one deterministic archive object is created per canonical JSON row. This preserves source accounting and makes no automatic identity merge. It does **not** assert that:

- the row is the unique intellectual work;
- two rows necessarily describe different works;
- work, design concept, manifestation, edition, physical item, digital surrogate, and source record are identical;
- title, provider key, image similarity, or shared metadata proves identity.

Work/manifestation/item/surrogate identity is represented later by typed entities and evidence-bearing claims or assignments. Merge and split require an effective curator decision with evidence; they never arise from import similarity.

## Decision 2: evidence, claims, semantic relations, and TRACE projections

The model has four independent layers:

1. **Evidence item** — immutable source artifact/record plus locator/span/content hash. Evidence can support, challenge, or qualify many claims.
2. **Claim** — one claimant-bound statement with preserved wording or structured proposition, epistemic class, source/citation, locator, stance, and review state. Many claims may discuss one semantic relation; competing claims remain separate.
3. **Semantic relation** — a normalized typed subject–predicate–object proposition independent of claimant wording and independent of TRACE layout. Initial semantic endpoints use real FKs to `core.entity`; material that cannot be typed remains a claim or assertion in workflow hold.
4. **TRACE projection** — a release- and corpus-specific selection/rendering of eligible entities, relations, and claims as nodes, edges, tree/branch placements, and publication layers.

The assertion predicate registry is distinct from the TRACE display registry. Every registered predicate records stable ID, domain/range or typed subject/value rules, epistemic/evidence requirements, lifecycle status, and registry version.

`provenance.canonical_assignment` is a closed identity supertype for normalized joins. Its initial subtype codes are `entity_name`, `object_source_record`, `object_agent_credit`, `object_medium`, `object_type`, `object_subject`, `object_collection`, `object_temporal`, `object_place`, `folder_membership`, `object_tree_membership`, `object_representation`, and `identity_resolution`. Each subtype shares its PK/FK with the assignment row and has an enforced typed natural key. Semantic relations, relation/claim support, and corpus membership are typed research records with their own identities, not assignment subtypes.

Evidence reaches a claim directly through a stance-bearing N:M claim/evidence bridge. A semantic relation is supported or challenged through claims; it does not maintain a second competing direct-evidence path. An evidence-bearing curator decision may accept/reject/supersede an assignment, but the decision does not erase its supporting or challenging claims.

The v48 directed TRACE triple remains a frozen projection/reconciliation key. It is not the universal natural identity of a claim or semantic relation. Before graph migration, every legacy node, edge, evidence tuple, membership, placement, review row, and adjunct fact is classified exactly once as:

- `REGENERABLE` from the canonical JSON and governed configuration;
- `GOVERNED_EXTERNAL_EVIDENCE` with preserved authoritative evidence and an explicit ingest decision; or
- `HOLD`.

Zero unclassified graph facts is a precondition for research-schema migration.

## Decision 3: epistemic classes

Every research claim uses one registered epistemic class. The initial closed classes are:

| Class | Required provenance | Prohibited implication |
|---|---|---|
| `documented_source_statement` | source/claimant, source record, preserved wording or exact structured value, locator, observation context, predicate mapping | A provider statement does not become universal truth merely because it is documented. |
| `scholarly_claim` | claimant agent, cited work/source, exact locator, preserved wording or licensed excerpt/hash, claim date/version, stance | Acceptance does not erase competing scholarship or make the claim causal. |
| `computed_association` | analysis-run ID, method/software version and hash, deterministic parameters, exact research release and corpus hashes, score/unit/uncertainty/threshold, output hash | Score, similarity, co-occurrence, layout, or clustering never becomes documented fact or causation. |
| `causal_interpretation` | named claimant, wording, source/citation and locator, causal predicate, scope/qualifiers, evidence chain, competing claims, heightened review | No causal or influence relation may be manufactured from chronology, geography, medium, source, similarity, cluster, or score alone. |

Epistemic class, acceptance state, confidence/score, evidence tier, workflow state, publication layer, and metric eligibility are orthogonal.

Any influence claim additionally retains claimant, wording, source, locator, direction, scope, temporal qualification, stance, reviewer decision, and policy version. The frozen v48 value of zero accepted influence edges is evidence of the current no-inference policy, not evidence that historical influence never occurred.

## Decision 4: Browse Index, research corpora, and missingness

The full 15,923-object v48 cohort is the operational Browse Index boundary. It remains important portfolio and corpus-scale evidence, but it is not automatically a strict research corpus.

A research corpus is a versioned, immutable N:M selection with:

- corpus ID/version and policy hash;
- research question and population frame;
- inclusion and exclusion rules;
- membership decision, reason, evidence, actor/run, and validity;
- exact input `researchReleaseId + researchManifestSha256`;
- treatment of review, auxiliary, withdrawn, unavailable, and rights-limited records;
- count/query/method hashes and a sealed membership snapshot.

Multiple corpora may overlap. There is no universal `in_research_corpus` or universal count-eligible boolean.

Missingness is an evidence-bounded observation against a named population frame. Initial reason classes distinguish at least: not collected/unknown, not digitized, not discovered, source unavailable/endpoint failure, metadata insufficient, authority/language unresolved, rights restricted/display withheld, excluded by scope, excluded by quality rule, duplicate/identity unresolved, not geometrically mappable, and unknown cause. Every observation records release/corpus, denominator/unit, date, method/run, evidence, and confidence.

Source concentration and coverage are release- and corpus-scoped analyses. They name provider/source-family registry, dimensions, denominator, method/parameters, query/input hashes, missingness rates, and sensitivity analysis. No opaque composite coverage score is a promotion gate.

## Decision 5: research release and visual registry are independent

Every successful research response binds the exact research pair and atomically carries either an exact compatible visual pair or two null visual fields:

```text
researchReleaseId
researchManifestSha256
visualRegistryVersion
visualRegistrySha256
```

The research release contains scholarly object, claim, semantic relation, corpus, TRACE, Search, and non-visual read projections. The visual registry contains external visual references and object-reference bridges, provider objects and typed locators, rights observations and assessments, provider-policy versions and evaluations, delivery decisions, endpoint-health observations, attribution/required statements, review due/stale state, and takedown overlays. Third-party pixel locators never enter the research release.

Each has its own `draft → candidate → validated → sealed` lifecycle, canonical manifest bytes/hash, detached post-seal receipt, immutable assets/projections, and `current` pointer updated only by CAS. A visual registry declares exactly one compatible research pair. Runtime resolves pointers once and uses exact pairs. A missing compatible registry yields a normal research-only response with no locator; an explicitly selected incompatible pair is a typed mismatch. Cross-pair fallback is prohibited.

A visual-policy, health, or takedown change never rewrites a sealed research release. A research release never treats a mutable visual locator as content authority.

## Decision 6: external visual identity and five orthogonal decision records

An external visual reference is a provenance-occurrence identity, unique on source artifact, record, field/JSON pointer and occurrence ordinal. It has a typed N:M bridge to archive objects and zero or one resolved provider object. Typed immutable locators distinguish canonical record, source viewer, provider embed, IIIF manifest/canvas/Image API/info, thumbnail, direct image and governed local asset roles. URLs and redirects are locators/observations, not identity or permission. Observation/assessment/takedown subjects use closed exactly-one subtype families with real FKs; arbitrary `target_type + target_id` is prohibited.

The five independent decision records are:

1. **Rights evidence and assessment** — immutable observations plus a reviewed assessment, including `unknown`, `missing`, `conflict`, `stale`, restrictive states and positively evidenced permissions.
2. **Provider policy and evaluation** — immutable policy-version evidence plus its application to one object–visual use; it is not folded into rights assessment.
3. **Delivery decision** — the project return mode: `BLOCKED`, `CITATION_ONLY`, `LINK_ONLY`, `SOURCE_VIEWER`, or `REMOTE_IMAGE`, with explicit support and reason code.
4. **Endpoint health** — time-bound technical observation for one typed locator; it can only retain or reduce delivery.
5. **Takedown state** — append-only event, typed scope and monotonic restrictive override; an active override always wins.

No axis implies another. API availability, IIIF presence, redirect success, endpoint health, metadata openness, source reputation, discovery signal, LLM summary, or visual similarity never grants pixel delivery.

`unknown`, `missing`, `conflict`, or `stale` rights/provider-policy state fails closed to `LINK_ONLY` or `CITATION_ONLY`. Only `REMOTE_IMAGE` may expose the v1 allowlisted remote-pixel locator; lower modes structurally omit pixel, thumbnail, image-service and embed fields. Positive remote delivery also requires complete attribution and qualified locator health. An active takedown forces `BLOCKED` or `CITATION_ONLY`, overlays sealed delivery with a deterministic digest, and is incorporated into the next registry version without rewriting old bytes.

## Decision 7: stable machine identity

Canonical project identity is domain-independent, version-independent and class-specific:

```text
urn:gdarchive:object:<lowercase-uuid>
urn:gdarchive:relation:<lowercase-uuid>
urn:gdarchive:claim:<lowercase-uuid>
urn:gdarchive:source:<lowercase-uuid>
urn:gdarchive:visual-reference:<lowercase-uuid>
```

Public routes are resolvers/aliases and do not replace canonical URNs. Exact release occurrences use the `urn:gdarchive:research-snapshot:...` or `urn:gdarchive:visual-snapshot:...` grammar fixed by the Phase 1D stable-ID policy. Merge, split, withdrawal and redirect history remains addressable and release-projected. The frozen `.example` strings in the v48 UUIDv5 recipe remain exact non-resolvable seed inputs only. Until one governed `PUBLIC_CANONICAL_ORIGIN` is approved, output uses URNs and relative routes rather than pretending that a placeholder is final.

The pre-DDL contract requires a GET/HEAD/OPTIONS-only boundary, exact pair identity, class-specific stable IDs, `SAFE`/`PUBLIC`/`INTERNAL`/`HELD` field classes, a positive serializer allowlist and structural omission of held locators. Actual JSON Schemas, OpenAPI, JSON-LD/canonical alternates, Linked Art/PROV-O, DCAT, diff/change feed, sitemap/robots and crawlability are later pre-freeze or pre-promotion implementation gates.

## Decision 8: count taxonomy

Counts are classified as:

- **canonical parity** — exact sole-input rows, IDs, raw bytes, and governed deterministic projections;
- **graph parity** — separately named v48 TRACE projection nodes/edges, object-membership projections, trees, and observed labels; v49 semantic relations and claims receive separately named counts and are never inferred from v48 projection totals;
- **derived reconciliation** — Search/TRACE/read-product populations, manifests, shards, review/auxiliary layers, and saved historical QA/freeze receipts;
- **historical aspiration** — portfolio planning such as 20,000 and remaining 4,077.

Historical aspiration is preserved in frozen evidence but is never a migration, freeze, promotion, coverage, or quality gate.

## Readiness and consequences

Phase 1C supplies passing authority/count/research evidence: all 15,923 inputs are accounted, the stale metadata scalar is reconciled without inventing a row delta, and unclassified graph/raw counts are zero. Phase 1D supplies the typed 100% legacy visual baseline, identities/cardinalities, five-record rights model, dual release/CAS rules, stable URNs, field classes and fail-closed serializer contract. Physical DDL remains blocked only until the independent joint receipt verifies that those decision packages and normative documents have no unresolved authority, identity, cardinality, state, version or serialization conflict and that the legacy runner remains excluded.

Positive provider authorization, complete artifact-level redistribution clearance, actual DDL/API/OpenAPI/JSON Schema/JSON-LD/DCAT, CI, deployment, frontend Repository adoption, production health service and browser QA are later implementation gates. Their absence keeps freeze/promotion/deployment false but is not an empty-schema blocker.

Until then:

```text
ENGINEERING_PRE_DDL_READY=false
RESEARCH_SEMANTICS_PRE_DDL_READY=false
RIGHTS_VISUAL_PRE_DDL_READY=false
MACHINE_CONTRACT_PRE_DDL_READY=false
OVERALL_PRE_DDL_READY=false
DATABASE_IMPLEMENTED=false
DATABASE_FREEZE_READY=false
FRONTEND_PROMOTION_READY=false
DEPLOYMENT_READY=false
```

No decision in this ADR authorizes migration, database creation, API/frontend implementation, image acquisition, cleanup, freeze, promotion, or deployment.
