# Data Security and Fail-Closed Contract

## Threat model

The chief risk is not a conventional SQL write: it is accidental publication of the 7,928 held objects or of ungoverned candidate context through a permissive filter, client bundle, error message, export, persistence key, or regression artifact.

## Controls present

| Boundary | Control | Evidence status |
| --- | --- | --- |
| Eligibility | Audited ledger `research_disposition=eligible` is the sole allow-list | `PASS_SOURCE_AUDIT` |
| Misleading SQLite flags | `objects.count_eligible` and `objects.trace_tier` are not filters | `PASS_CODE_INSPECTION` |
| Database access | `node:sqlite`, read-only immutable URI, `readOnly=true`, `PRAGMA query_only=ON` | `PASS_CODE_INSPECTION` |
| Server boundary | Loader imports `server-only`; no browser database access | `PASS_CODE_INSPECTION` |
| Runtime activation | Explicit `CONTEXT_CANVAS_REAL_VALIDATION` gate; default is synthetic/unavailable | `PASS_CODE_INSPECTION` |
| Lookup oracle | Held and well-formed unknown values both return `RECORD_NOT_AVAILABLE` | `PASS_CODE_INSPECTION` |
| Query shape | Only eligible IDs are queried, in bounded deterministic chunks | `PASS_CODE_INSPECTION` |
| Client payload | Only one selected public dataset plus a small sample picker is passed | `PASS_CODE_INSPECTION` |
| Internal identifiers | Public root stable ID plus `ctxv49` SHA-256 validation identities | `PASS_CODE_INSPECTION` |
| Epistemic state | `not_published`, `governedPublicRelease=false`, every real connection `proposed` | `PASS_CODE_INSPECTION` |
| Semantic relations | Real `semanticEdges=[]` and empty predicate registry | `PASS_CODE_INSPECTION` |
| Failure rendering | Invalid/unavailable/projection errors do not mount an empty Canvas | `PASS_CODE_INSPECTION` |
| Persistence | Manifest and selected public ID partition keys; unavailable records never mount | `PASS_CODE_INSPECTION` |
| Export | XML escaping, UUID redaction, sanitized public-ID filename, abort on switch | `PASS` — 31,980 SVG preparations; zero failures or UUID exposures |
| Committed evidence | Aggregate reports plus public sample only; no candidate-label dump | `PASS_PACKAGE_INSPECTION` |
| Frozen-input integrity | Runtime SHA-256 checks for freeze receipt, ledger, and immutable SQLite | `PASS` |
| Client bundle | 47 bundle files and 73 reachable client modules inspected | `PASS` — zero forbidden matches |

## Privacy-critical source finding

All 15,923 SQLite objects have `count_eligible=1`. Filtering that field would disclose all 7,928 held records. Of the 12,952 objects with `trace_tier=source_verified`, 4,957 are held. Neither field can participate in public eligibility.

Held aggregate folder-row counts were used only to audit the boundary: medium 7,928, theme 7,928, movement 96, region 7,928, total 23,880. This package contains no held stable ID, title, candidate label, UUID, or URL.

## Fail-closed rules

1. If the gate is disabled, do not touch the real candidate source.
2. If the source counts, row identity, or mapping invariants disagree, return an integrity/projection error and do not mount the Canvas.
3. If an input is held or unknown, return the same generic unavailable response.
4. If an input is malformed, return only the grammar error; do not probe the source.
5. Never fall back from the ledger to SQLite eligibility flags.
6. Never emit a full-corpus dataset, held enumeration, raw candidate-label register, UUID, or source URL.
7. Never call a validation candidate accepted, governed, historical evidence, or publicly released.
8. Production default remains synthetic/unavailable even when a development build exists.

## Validation evidence

```text
HELD_LOOKUPS_TESTED=7928
HELD_OBJECTS_EXPOSED=0
UNKNOWN_HELD_RESPONSE_PARITY=PASS
REAL_VALIDATION_CORPUS_IN_CLIENT_BUNDLE=false
CLIENT_BUNDLE_FORBIDDEN_MATCH_COUNT=0
CLIENT_SOURCE_FORBIDDEN_MATCH_COUNT=0
INTERNAL_UUID_CLIENT_EXPOSURE_COUNT=0
PRODUCTION_REAL_CANDIDATE_EXPOSURE=false
SOURCE_RUNTIME_CHECKSUM_VERIFICATION=PASS
FROZEN_INPUTS_RUNTIME_VERIFIED=3
```

The source manifest is `c07de2b6531f5f17cd31f705b6e42443277bf837ce9e13225ae684001da17363`. It binds mapping version `trace-context-realdata-v1` to the sorted path/hash entries for the three runtime-verified frozen inputs.
