# 09 — Stable ID and URI policy

- Package: v49 Phase 1D B4
- Status: **LOCKED PRE-DDL IDENTITY POLICY; HTTPS RESOLVER ORIGIN PENDING**
- Applies to: object, semantic relation, research claim, citable source, external visual reference, release occurrences, and machine problem identifiers

## 1. Decision

Stable identity is domain-independent. It does not wait for a production hostname and does not change when a route, release, visual registry, provider locator, label, merge/split state, or deployment changes.

Each public resource has:

1. a class-specific immutable internal UUID;
2. a class-specific canonical project URN;
3. zero or more HTTPS resolver aliases after a production canonical origin is approved;
4. zero or more release-pinned occurrence URNs for exact scholarly/release citation.

The URN is the canonical machine identifier until a resolvable HTTPS origin is approved. HTTPS URLs are resolvers for the same identity, not replacement identity. `.example` placeholders are never emitted as final stable identifiers.

## 2. Canonical project URNs

The project-controlled namespace is `urn:gdarchive`. It is domain-independent and uses lowercase ASCII kind tokens plus lowercase hyphenated UUID text:

```text
urn:gdarchive:object:<uuid>
urn:gdarchive:relation:<uuid>
urn:gdarchive:claim:<uuid>
urn:gdarchive:source:<uuid>
urn:gdarchive:visual-reference:<uuid>
```

Closed kind tokens for v1 are `object`, `relation`, `claim`, `source`, and `visual-reference`. Adding a kind requires a reviewed registry/contract version; arbitrary user-provided kind strings are invalid.

Normative lexical rules:

- UUIDs serialize as 36 lowercase ASCII characters with hyphens and compare by UUID value.
- URNs compare as the exact canonical string after validation; consumers do not case-fold or Unicode-normalize them.
- IDs and URNs contain no label, title, provider name, URL, filename, release date, mutable slug, or delivery state.
- IDs are never reused after merge, split, withdrawal, rejection, or takedown.
- A database table name is not part of the public identity.

`surfaceId` remains a durable legacy/public route identifier and crosswalk. It is not the canonical object UUID or URN. Provider object IDs, source locators, URLs, TRACE node/edge IDs, and visual-reference source literals likewise remain typed crosswalk/locator values, not substitutes for these IDs.

## 3. Identifier classes and mappings

| Resource | Internal ID | Canonical URN | Important non-identity values |
|---|---|---|---|
| Operational archive object | `archive_object_id` UUID | `urn:gdarchive:object:<uuid>` | `surfaceId`, title, provider/source keys, TRACE root |
| Semantic relation | `semantic_relation_id` UUID | `urn:gdarchive:relation:<uuid>` | relation type, claimant wording, TRACE edge/layout |
| Research claim | `claim_id` UUID | `urn:gdarchive:claim:<uuid>` | evidence/locator, confidence, acceptance/publication state |
| Citable source document | `source_document_id` UUID | `urn:gdarchive:source:<uuid>` | canonical/source URL, raw artifact or record ID |
| External visual reference | `external_visual_reference_id` UUID | `urn:gdarchive:visual-reference:<uuid>` | provider object ID, locator URL, image bytes, delivery mode |

Raw artifacts, raw source-record occurrences, evidence items, TRACE nodes/projection edges, folders, representations, workflow cases, and releases retain their own typed identities. They are not silently promoted into one of the five public classes.

## 4. Release-pinned occurrence identity

Canonical URNs are version-independent. Exact release citations add immutable occurrence identity rather than changing the canonical ID:

```text
urn:gdarchive:research-snapshot:<researchReleaseId>:sha256:<researchManifestSha256>:<kind>:<uuid>
urn:gdarchive:visual-snapshot:<visualRegistryVersion>:sha256:<visualRegistrySha256>:visual-reference:<uuid>
```

Release/version tokens are restricted to lowercase ASCII `[a-z0-9][a-z0-9._-]{0,127}`. Digests are exactly 64 lowercase hexadecimal characters. The kind and UUID rules are those in section 2.

The research-snapshot URN identifies one resource projection inside one exact research pair. The visual-snapshot URN identifies one visual-reference projection/decision inside one exact visual pair. A composed response carries both occurrence identities when applicable; it does not manufacture one synthetic combined release ID.

An active post-seal takedown overlay is not folded into either sealed occurrence URN. Effective-response reproducibility additionally records `takedownOverlaySha256`, preserving sealed identity and restrictive overlay identity separately.

## 5. Future HTTPS resolver rule

No production canonical origin is locked in Phase 1D. Before any HTTPS identifier is advertised as canonical, a later promotion decision must approve one `PUBLIC_CANONICAL_ORIGIN` satisfying all of:

- scheme exactly `https`;
- host under project control and documented operational ownership;
- no user info, query, fragment, wildcard, environment suffix, or path component in the origin value;
- TLS, redirect persistence, backup/restore, takedown, and long-term resolver ownership receipts;
- startup failure when the configured origin is absent, malformed, or differs from the sealed deployment receipt.

The deterministic mapping is then:

```text
<PUBLIC_CANONICAL_ORIGIN>/id/object/<uuid>
<PUBLIC_CANONICAL_ORIGIN>/id/relation/<uuid>
<PUBLIC_CANONICAL_ORIGIN>/id/claim/<uuid>
<PUBLIC_CANONICAL_ORIGIN>/id/source/<uuid>
<PUBLIC_CANONICAL_ORIGIN>/id/visual-reference/<uuid>
```

An HTTPS resolver returns or redirects to a representation while preserving the canonical URN and stable UUID in machine metadata. It may offer current and release-pinned representations, but must never infer a visual registry, silently change a research release, or expose a held locator. Environment hosts such as localhost, preview deployments, temporary Vercel URLs, and `.example` domains are never canonical.

Until that origin is approved, machine outputs emit the URNs and relative API routes only; an absent absolute HTTPS canonical URL is truthful and is not filled with a placeholder.

## 6. Release-pinned HTTPS representations

After origin approval, exact research representations use an exact-pair path or selector whose response still declares both research fields:

```text
<PUBLIC_CANONICAL_ORIGIN>/api/v1/releases/<researchReleaseId>/<resource-kind>/<uuid>
```

The request also pins `researchManifestSha256`. A visual selector is optional but atomic and pins `visualRegistryVersion + visualRegistrySha256`. The response's four version fields, not path text alone, are the reproducibility authority. Query parameters, headers, and route layout are transport details fixed later by the API implementation/schema; they cannot alter the underlying URN or exact-pair rules.

Version-independent `/id/...` resolvers may resolve to an exact current research representation only as mutable discovery. They are not evidence-level release citations. Citations and caches use the exact response pair and occurrence URN.

## 7. Alias, merge, split, and withdrawal

- **Alias/redirect:** a legacy `surfaceId` or old HTTPS alias may resolve to the same object URN. Alias history is release-projected and append-only.
- **Merge:** losing object IDs/URNs are never deleted or reassigned. Their resolver returns an identity-resolution record naming the survivor and effective release. Assertions and source history remain addressable.
- **Split:** the old object/route becomes a split landing identity with an ordered list of successor object URNs. It never chooses one successor implicitly.
- **Withdrawal:** the ID/URN remains a tombstone with a rights-safe reason/status. It is never reused and does not reveal held evidence.
- **Unresolved identity:** the resolver returns the unresolved status; no redirect, merge, or split is invented.

An exact release-snapshot URI returns the resolution state sealed in that release. A version-independent resolver may expose a newer state, clearly identifying the exact release used.

## 8. Visual-reference identity and locator separation

`urn:gdarchive:visual-reference:<uuid>` identifies the provenance-bound external visual reference. It never embeds or redirects directly to a third-party pixel URL.

Provider record, source viewer, IIIF manifest/canvas/Image API, thumbnail, direct image, and governed local asset are typed locators owned by a sealed visual registry. Their public URL exposure is controlled only by the Phase 1D truth table and machine serializer. A visual URN remains valid when every locator is absent, stale, held, blocked, or subject to takedown.

The research object URN remains resolvable when no visual registry exists. A visual-registry change does not change the object, relation, claim, or source URN.

## 9. Historical `.example` strings

The v48 seed UUIDv5 recipe currently contains names such as:

```text
https://modern-gd-history.example/identity/v49/v48/surface/<surfaceId>
```

Those exact UTF-8 strings are frozen **UUID namespace inputs only**. They are never dereferenced, never advertised as canonical URLs, and never interpreted as proof that the `.example` host is project-owned. This policy does not change the seed recipe or the 15,923 deterministic UUIDs established by Phase 1C.

Existing documentation examples such as `https://modern-gd.example/problems/...` and ADR 0004's `.example` canonical templates are not final stable URIs. Normative integration must replace their public-identity role with the URNs in this policy or explicitly label a seed string as non-resolvable historical input. No runtime/API/schema/JSON-LD output may emit them as final identifiers.

Until an HTTPS origin exists, problem identifiers use:

```text
urn:gdarchive:problem:<stable-lowercase-code>
```

## 10. Persistence and resolver acceptance

```text
STABLE_ID_CONTAINS_HOST=false
CANONICAL_URN_CHANGES_WITH_RELEASE=false
CANONICAL_URN_CHANGES_WITH_VISUAL_REGISTRY=false
CANONICAL_URN_CHANGES_WITH_LOCATOR=false
SURFACE_ID_IS_OBJECT_ID=false
URL_IS_VISUAL_REFERENCE_ID=false
MERGED_OR_WITHDRAWN_ID_REUSED=false
SPLIT_AUTO_REDIRECTS_TO_ONE_SUCCESSOR=false
EXAMPLE_DOMAIN_IS_FINAL_IDENTITY=false
REGISTRY_ABSENT_BREAKS_OBJECT_RESOLUTION=false
```

Implementation later must test URN grammar, duplicate IDs across public kinds, exact release occurrence parsing, resolver redirects/tombstones, origin validation, alias persistence, and non-disclosure. No production domain, resolver, route, JSON-LD context, sitemap, or deployment configuration is created in this phase.
