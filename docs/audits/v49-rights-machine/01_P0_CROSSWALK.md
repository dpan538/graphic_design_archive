# Phase 1D rights / visual / machine P0 crosswalk

- Package: v49 Phase 1D B1
- Scope: merge duplicate Phase 1B P0 findings into one ownership and gate map
- B1 result: **PASS** for crosswalk completeness and the rights/delivery decision rule
- Overall Phase 1D gate: **not asserted by B1**; B2–B5, normative calibration, and the joint verifier remain authoritative

## Authority and interpretation

This crosswalk reads the Phase 1C authority/research receipt as a prerequisite, not as visual-rights evidence. Phase 1C proves `AUTHORITY_RESEARCH_DELTA_CLOSED=true`, `UNCLASSIFIED_GRAPH_FACT=0`, and `UNCLASSIFIED_RAW_SOURCE=0`; it explicitly leaves provider policy, visual rights, endpoint health, delivery, takedown, and public field exposure to Phase 1D.

The findings below merge the overlapping P0 contributions in the Phase 1B A6 and A10 reports. A source finding may be split when part is a pre-DDL decision and part is a later implementation gate. This prevents missing OpenAPI, CI, deployment, JSON-LD, or frontend wiring from being mislabeled as an empty-schema blocker.

## Unique crosswalk

| Unique ID | Consolidated decision or implementation theme | Source findings merged | Pre-DDL decision? | Closure artifact / owner | Acceptance boundary |
|---|---|---|---|---|---|
| `RM-P0-01` | Independent authority: sealed research release and sealed visual-registry version, each with manifest SHA, post-seal receipt, immutable projection, compatibility declaration, and separate CAS `current` pointer. | A6-P0-01; A10-P0-02; DDL decision pack §§10,12; ADR 0004 decision 5 | **YES** | Phase 1D decision pack and dual-release seal/CAS spec (B2) | No shared identity, manifest, seal transition, or pointer mutation; a visual change does not reseal research and a research change does not inherit visual authorization. |
| `RM-P0-02` | Typed visual identity/cardinality: provider, provider object, external visual reference, object↔visual bridge, typed locator, policy version/evaluation, observations, assessments, delivery decision, health observation, takedown event/scope/override, and visual-registry entry. | A6-P0-02; the identity/cardinality part of A10-P0-02 | **YES** | Phase 1D entity/cardinality matrix and decision pack (B2) | Every target has a real FK or closed typed bridge; URL, redirect, IIIF resource, or provider key is never visual identity or permission. |
| `RM-P0-03` | Orthogonal decision axes and obligations: rights evidence/assessment, provider-policy evaluation, delivery decision, endpoint health, and takedown remain separate; attribution/required statement is an explicit prerequisite for positive delivery. | A6-P0-03; A6-P0-05; rights-state part of A10-P0-04 | **YES** | `04_RIGHTS_DELIVERY_TRUTH_TABLE.tsv` (B1), entity model (B2), negative oracle (B5) | Exactly one ordered fail-closed rule selects delivery without changing any evidence, policy, health, or takedown record. Health can only retain or lower delivery. |
| `RM-P0-04` | Stable identity and public serializer boundary: stable object/claim/relation/source/visual-reference IDs, dual-version response identity, safe/public/internal/held fields, explicit mismatch, and omission of unapproved pixel/thumbnail/image-service locators. | A6-P0-04; DDL-leakage part of A6-P0-06; A10-P0-01; decision portion of A10-P0-03; decision portion of A10-P0-04 | **YES** | Machine exposure contract and stable-ID/URI policy (B4), negative oracle (B5) | Fail-closed behavior must be expressible as schema/serializer rules before physical columns are fixed. A healthy URL, API, IIIF, redirect, or HTTP success never supplies authorization. |
| `RM-P0-05` | Legacy external-visual population is inventoried and assigned one closed typed disposition, including legal `UNKNOWN` states; zero completely unclassified references. | Measured A6 legacy population; evidence-disposition portion of A6-P0-07; Phase 1D task gate | **YES** | Legacy visual disposition TSV/summary (B3) | `LEGACY_VISUAL_REFERENCE_INVENTORIED=100%`, `LEGACY_VISUAL_REFERENCE_TYPED=100%`, and `UNCLASSIFIED_VISUAL_REFERENCE=0`; positive permission is not required. |
| `RM-LATER-01` | Executable machine-publication artifacts: actual Read API, OpenAPI, JSON Schema, JSON-LD, Linked Art/PROV-O, DCAT, sitemap/robots, change feed, and crawlability tests. | Implementation portion of A10-P0-03 and related A10 P1/P2 findings | **NO** | Pre-freeze / pre-promotion machine-contract implementation | Their absence keeps `FREEZE_READY` or `PROMOTION_READY` false, but does not block physical schema after `RM-P0-01`–`RM-P0-05` are decision-complete. |
| `RM-LATER-02` | Artifact-level third-party rights/license/redaction/retention disposition and positive authorization review. | Freeze portion of A6-P0-07; A10-P0-06 | **NO**, except the typed legacy baseline in `RM-P0-05` | Pre-freeze artifact/provider disposition ledger | Unknown records stay typed and fail closed. Full positive-rights coverage and redistribution clearance are not empty-schema prerequisites. |
| `RM-LATER-03` | Current runtime leakage removal, frontend Repository/API adoption, independent data/frontend CI, security/deployment configuration, production health service, and visual/browser verification. | Runtime portion of A6-P0-06 and A10-P0-04; A10-P0-05; A10-P0-07 | **NO** | Reversible cleanup where authorized, then later frontend/CI/deployment work | These keep promotion/deployment false. They must not be used to delay DDL once the normative identity/cardinality/state/version/serialization contract passes. |

## Gate boundary resolution

The pre-DDL blocker set is exactly `RM-P0-01` through `RM-P0-05`. It concerns decisions that determine physical keys, FKs, state columns, immutable version boundaries, and public-field suppression. The later set is intentionally still important, but its acceptance evidence requires code, schemas, CI, deployment, or provider/legal review that this phase prohibits.

The split findings resolve the main ambiguity in A10:

- stable internal IDs/URNs, future URL mapping rules, exact dual-version identity, and serializer redaction are pre-DDL decisions;
- a production domain, routable API, OpenAPI, JSON Schema files, JSON-LD/RDF/DCAT artifacts, CI, and deployment are later implementation gates;
- current legacy remote-pixel rendering remains a frontend-promotion risk, while the pre-DDL obligation is that the future public serializer cannot emit a locator unless the visual-registry decision allows it;
- 100% typed legacy disposition is pre-DDL; positive licensing/authorization coverage is measured but is not a PASS threshold.

## Locked rights/delivery rule

`04_RIGHTS_DELIVERY_TRUTH_TABLE.tsv` is ordered by numeric precedence; the first matching rule wins. The five records remain independent:

1. immutable rights evidence and a reviewed `rights_assessment`;
2. immutable `provider_policy_version` evidence and one `provider_policy_evaluation`;
3. one resulting `delivery_decision` with exact supporting-record bridges;
4. per-locator `endpoint_health_observation` values;
5. an append-only effective takedown overlay.

Attribution completeness and typed-locator availability are additional explicit prerequisites. They are not folded into `rights_assessment`. `QUALIFIED` in the table means the selected typed locator has a fresh `HEALTHY` observation; `UNKNOWN`, `STALE`, `REDIRECTED`, `DEGRADED`, `UNREACHABLE`, `BLOCKED`, and `ERROR` are not qualified. A redirect may become a new typed locator only through separate identity/policy review; redirect success itself never qualifies the original locator.

The closed delivery vocabulary is:

```text
BLOCKED
CITATION_ONLY
LINK_ONLY
SOURCE_VIEWER
REMOTE_IMAGE
```

Only `REMOTE_IMAGE` may expose an allowlisted remote-pixel locator. `SOURCE_VIEWER` may expose only an allowlisted provider viewer locator; it never exposes a pixel, thumbnail, canvas, or image-service locator. `LINK_ONLY` may expose only an allowlisted canonical provider-record locator. `CITATION_ONLY` and `BLOCKED` expose no external locator URL. Absence of a registry entry or qualified lower-mode locator yields a normal research record with citation metadata, never an error page and never a permissive fallback.

## Evidence read

B1 read the relevant normative corpus and evidence completely: the five root v49 documents, `docs/architecture/DDL_DECISION_PACK_V49.md`, all four ADRs, Phase 1B A6 and A10, the cleanup/freeze matrices, and the Phase 1C executive/authority/gate/manifest/independent-verifier evidence. No Phase 1B inference was promoted without checking the Phase 1C receipt.

## Explicit non-actions

No network or provider endpoint was accessed. No image, HTTP health probe, PostgreSQL, Docker, npm, Next.js, TypeScript, browser, data export, migration, API, OpenAPI, JSON Schema, JSON-LD, CI, deployment, frontend, package, frozen asset, QA file, or dirty-main path was created or changed by B1.
