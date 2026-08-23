# Governed public projection validation

## Projection identity

| Field | Value |
| --- | --- |
| Projection ID | `trace-context-v1` |
| DTO schema | `trace-context/v1` |
| Governance policy | `context-governance-v1` |
| Governance policy SHA-256 | `aa13eaff6d42533a37777e546b8976bdad7d2be3a4ab4d405a77ce1aa61c7a0c` |
| Projection SHA-256 | `825f6ecaa9ae1496c8a00ea0fefa5c90319046cf9c1f08a2ef76b9b02df4baeb` |
| Public-ID policy | `trace-context-public-id-v1` |
| Mapping version | `trace-context-governance-mapping-v1` |
| Generator version | `trace-context-projection-generator-v1` |
| Explanation registry | `trace-context-explanations-v1` |

The manifest binds the source research pair, frozen SQLite artifact, freeze receipt, authoritative public/held ledger, governance policy, explanation registry, exception register, term registry, record payload, exact census, identity namespaces, mapping/generator versions, and canonical serialization contract.

## Frozen input bindings

| Input | SHA-256 |
| --- | --- |
| Frozen v49 SQLite source | `ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e` |
| `database/FREEZE_V49.json` | `f0dda59dd515ba243eaf213bce9f42513727f1ab0a44685635921c3759a7d22e` |
| Public/held surface ledger | `48f98f68ca2ec0cef96c82ecc9c01e4129eb9a3f91e08b07ad9a59644a9d4e01` |
| Source research manifest | `4addfdb3cb9314587908096572242b9d63e9cef9e6e1be68c0c646491a43a90a` |

No database, migration, freeze receipt, canonical release input, or historical API snapshot was modified.

## Payload integrity

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `governance-policy.json` | 5,969 | `aa13eaff6d42533a37777e546b8976bdad7d2be3a4ab4d405a77ce1aa61c7a0c` |
| `explanation-registry.json` | 5,590 | `5b45f938b98d662e1c4d76712b5bc0dac05298e859f63a40a0cc071f67663dfe` |
| `exception-register.json` | 2,415 | `3e561fdddda341ce40b1910da43b94b10f0f07c9659be239c3c5839c036019d7` |
| `terms.json` | 5,966 | `89b14153d9ebfc1f620b4e20e6ead3ba7ff935df5c23b71d7a6b7d84bd2a9d23` |
| `records.json` | 13,109,622 | `c767b9661e4cb417cfaae3948d7ed2b974fc88e1dcc9a3686eae90ae8610a9e7` |

The five core payloads total 13,129,562 raw bytes and 1,661,608 deterministic gzip bytes under the manifest definition. Manifest and checksum ledgers are excluded from those two size totals.

## Determinism and references

The projection check performs two independent in-memory builds and demands byte equality with each other and the committed files. It validates every artifact hash, exact count, public term reference, explanation reference, representation identity, provenance identity, publication state, eligibility decision, source-state preservation, and release pin.

```text
CONTEXT_PUBLIC_PROJECTION_DETERMINISTIC=true
PUBLIC_OBJECTS_GOVERNED=7995
GOVERNED_DATASET_FAILURE_COUNT=0
PUBLIC_ID_COLLISION_COUNT=0
VALIDATION_ID_IN_GOVERNED_DTO_COUNT=0
INTERNAL_ID_EXPOSURE_COUNT=0
```

## Server boundary and performance

The projection reader is marked server-only. It validates integrity before building its by-public-ID lookup and returns only the selected record’s public DTO. It does not import the exhaustive source-index loader. Client-reachable source and built-chunk guards reject the full corpus and its marker.

```text
GOVERNED_RUNTIME_HEAP_BYTES=18203424
GOVERNED_RECORD_LOOKUP_P95_MS=0.012
HEAVY_VALIDATION_SOURCE_INDEX_USED_BY_PUBLIC_RUNTIME=false
FULL_CONTEXT_CORPUS_IN_CLIENT_BUNDLE=false
```

The authoritative post-build guard scanned 51 production static files totaling 92,360,030 bytes and found no governed-corpus marker. Its final status is `PRODUCTION_STATIC_PASS`.
