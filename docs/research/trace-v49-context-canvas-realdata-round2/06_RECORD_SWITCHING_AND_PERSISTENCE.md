# Record Switching and Persistence

## Isolation mechanism

`ContextCanvas` derives a React session key from data mode, release manifest SHA-256, and selected public stable ID. A record or release change therefore unmounts the old `ContextCanvasSession` and mounts a fresh session for the new dataset.

The unmount cleanup:

- aborts pending export work;
- persists the current drag baseline if a node drag is active;
- removes session-local pointer, pan, selection, focus, history, and export state with the unmounted component.

This is the structural enforcement for `CTX-REAL-INV-008` and `CTX-REAL-INV-009`: a selected or interacting entity cannot survive into a differently keyed dataset session.

## Persistence identity

`contextCanvasPersistenceKey(dataset)` is:

```text
trace-context-canvas:
schema-<CONTEXT_CANVAS_SCHEMA_VERSION>:
templates-<TEMPLATE_CATALOG_VERSION>:
<release.manifestSha256>:
<URL-encoded selected public stable ID>
```

The persisted payload additionally records the chosen template ID and that template's version. Deserialization rejects:

- a Canvas schema mismatch;
- a template-catalog mismatch;
- an unknown template;
- an incompatible template version;
- duplicate visible entity IDs;
- any entity absent from the current dataset;
- a missing root entity;
- missing or non-finite positions;
- extra position keys;
- malformed JSON;
- invalid viewport values.

Storage exceptions are caught. A failed or corrupt restore returns `null` and initializes the deterministic template instead of mounting a partially restored workspace.

## Required A → B → A behavior

```text
Object A → edit composition → persist A
Object B → new keyed session → restore only B or initialize B
Object A → new keyed session → restore only A
```

The release manifest participates in both the session and persistence identity. An older release cannot read a new release's key, and a new release cannot read an older release's key. Held and unavailable records fail before the Canvas mounts, so the route neither reads nor writes a usable workspace for them.

## Verification matrix

The real-data state verifier exercised record isolation, release isolation, corrupt payload rejection, and every version discriminator. The synthetic core regression additionally covered node-drag history and export cancellation behavior.

| Case | Required result | Evidence status |
| --- | --- | --- |
| Same record, same release | exact valid workspace restore | `PASS` |
| Different public record | no composition, viewport, selection, or history crossover | `PASS` |
| Different release manifest | old state not read | `PASS` |
| Different Canvas schema | payload rejected | `PASS` |
| Different template catalog/version | payload rejected or safely reset | `PASS` |
| Corrupt localStorage | ignored; deterministic initialization | `PASS` |
| Record switch after drag | drag/session state does not enter the new record | `PASS` |
| Record switch during export | cancellation path restores ready state; keyed unmount aborts old work | `PASS` |
| Template/undo/redo/fit/reset after switch | all referenced entities belong to current dataset | `PASS` |
| Held/unknown/malformed route | fail-closed lookup; no usable Canvas dataset or persistence key | `PASS` |

```text
PERSISTENCE_KEY_COUNT=7995
PERSISTENCE_KEY_COLLISION_COUNT=0
PERSISTENCE_ROUND_TRIP_MISMATCH_COUNT=0
RECORD_SWITCH_STATE_LEAK_COUNT=0
PERSISTENCE_ROUNDTRIP_P50_MS=0.022
PERSISTENCE_ROUNDTRIP_P95_MS=0.033
PERSISTENCE_ROUNDTRIP_P99_MS=0.051
```
