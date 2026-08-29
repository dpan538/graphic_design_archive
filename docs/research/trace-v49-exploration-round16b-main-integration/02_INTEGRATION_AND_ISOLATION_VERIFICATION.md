# Integration and isolation verification

## Result

The clean integration tree passes the inherited Round 16B verification, fresh
database reproduction, frontend and API contracts, production build,
production HTTP exercises, validated PNG export validation, repository
integrity checks, and deterministic handoff reconstruction.

The dedicated integration verifier reports:

```text
OPEN_INQUIRY_REGISTRY_COUNT=11
OPEN_INQUIRY_IMPLICIT_PAIR_PROJECTION_COUNT=0
OPEN_INQUIRY_LEAK_INTO_VALIDATED_ASSOCIATION_COUNT=0
OPEN_INQUIRY_LEAK_INTO_VALIDATED_COMPOSITION_COUNT=0
OPEN_INQUIRY_VALIDATED_TOPOLOGY_MUTATION_COUNT=0
OPEN_INQUIRY_VALIDATED_EXPORT_LEAK_COUNT=0
OPEN_INQUIRY_VALIDATED_METRIC_CONTAMINATION_COUNT=0
VALIDATED_PAIR_ASSOCIATION_COUNT=21
TRACE_TOP_LEVEL_FUNCTION_COUNT=3
IMPLEMENTED_TRACE_API_UNCATALOGUED_COUNT=0
FUNCTION_TREE_DANGLING_API_REFERENCE_COUNT=0
HANDOFF_REQUIRED_SOURCE_MISSING_COUNT=0
HANDOFF_SOURCE_HASH_MISMATCH_COUNT=0
```

## Isolation method

`verify_clean_integration.py` reads the canonical Open Inquiry registry, the
Validated Exploration v2 model, the API catalog, the function tree, and the
bounded handoff manifest. It independently reconstructs inquiry membership and
all possible inquiry-node pair projections, then proves that those identifiers
do not occur in validated associations, compositions, topology, exports, or
metrics. It also proves that each inquiry carries the required false validation
and topology permissions and contains none of the prohibited probability
fields.

The production HTTP verifier exercises the independent list and detail routes,
their `HEAD` and `OPTIONS` contracts, error behavior, content hashes, cache and
layer headers, unsupported query rejection, deterministic ordering, and the
absence of Open Inquiry data in validated responses. It sends traffic only to
an ephemeral loopback server and leaves no server process behind.

## Full inherited and runtime evidence

The inherited v3 runtime, semantic, recursive-gap, source-review, disposition,
method, deferred-surface, candidate-census, v50-manifest, portability, and
Round 16A reconciliation checks all passed without reducing their historical
case counts. The exhaustive v2 static run passed 1,598,649 cases. Production
HTTP verification passed 755,855 v2 cases, 1,168 v3 cases, and 27 independent
Open Inquiry cases. The validated PNG export run passed all 11,520 variants and
69,120 HTTP requests.

Both fresh PostgreSQL 16.13 databases replayed the frozen v49 and v50 inputs,
passed the higher-order and race contracts, and produced byte-identical
1,090,058-byte normalized schemas with SHA-256
`1152a494e6b64595c9f9291c1d314a9434cb763c7f2a02512d2768e286f571b4`.
The target databases and the private cluster were removed after verification;
no race fixture or database process remained.

The production build passed on Next.js 15.5.18 with 46 static pages. The first
sandboxed attempt could not resolve the configured Google Fonts endpoint; the
identical build passed when network access was allowed. Likewise, loopback HTTP
verification passed after the sandbox's initial port-allocation denial was
removed. Neither retry was a deployment.

## Repository and package integrity

Database freeze, repository hygiene, secret scanning, `git diff --check`,
`git fsck --strict`, `git lfs fsck`, protected v2 path comparison, ordinary
blob boundary fixtures, and the large-blob policy all passed. Git reported
unreachable dangling objects during strict fsck; those are permitted inventory,
not integrity failures, and fsck exited successfully. No tracked or staged
verification hydration remains.

Two deterministic frontend-handoff rebuilds produced byte-identical
33,269-byte archives with SHA-256
`1993415b03760fb9e9e36e7104feacdf3dd3d627aa2b01458b56790c7056c70a`.
Those test archives are external and are not committed.

## Evidence boundary

The historical Checkpoint 016 final-clean verifier passed its 24 checks and 20
adversarial controls with no mismatch, but it is intentionally identity-pinned
to the published `d40ec811c2b60cfcbf6892ba79741d2ee0fec95b`
reproduction. It validates the preserved historical receipt bytes; the fresh
database and HTTP runs above are the current-tree evidence. A final external
postpublication receipt remains necessary because a commit cannot contain its
own final object identity.

These results establish an evidence-bounded functional baseline. They do not
establish pair, higher-order, global-composition, product-reachability,
computational-space, or Function 3 closure. No frontend visual design, Search
work, or deployment was performed.
