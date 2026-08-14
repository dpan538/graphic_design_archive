# Performance block checkpoint

The backend was live but operationally unhealthy: it remained in one `SET CONSTRAINTS ALL IMMEDIATE` invocation beyond the bounded completion window. Liveness counters were not treated as completion evidence.

## Bounded-window record

```text
WINDOW_BASELINE_UTC=2026-08-14T10:44:34Z
WINDOW_DEADLINE_UTC=2026-08-14T10:54:34Z
LIVE_SNAPSHOT_CAPTURED_AT_UTC=2026-08-14T11:06:20Z
WINDOW_RESULT=INCOMPLETE
```

The additional checkpoint-capture interval is recorded as controller overhead, not as an extension or a successful completion. No Fresh B was started; the resolved backend was cancelled after the live snapshot and its transaction was subsequently proved rolled back.

## CPU and database samples

```json
{
  "final": {
    "backendPid": 50121,
    "capturedAtUtc": "2026-08-14T11:06:20Z",
    "cpuPercent": "8.5",
    "cpuTime": "97:57.35",
    "databaseStats": {
      "blksHit": 598354,
      "blksRead": 2974,
      "database": "gda_v49_phase2a_phase2b_replay_a",
      "numBackends": 2,
      "statsResetUtc": null,
      "tempBytes": 0,
      "tempFiles": 0,
      "xactCommit": 3807,
      "xactRollback": 1
    },
    "elapsed": "01-06:58:03",
    "state": "Rs"
  },
  "initial": {
    "backendPid": 50121,
    "capturedAtUtc": "2026-08-14T10:44:34Z",
    "cpuPercent": "2.1",
    "cpuTime": "96:53.37",
    "elapsed": "01-06:36:23",
    "source": "controller bounded-window baseline captured from the resolved task-owned backend",
    "state": "Rs"
  }
}
```

## Resolved transaction

```json
{
  "backend": {
    "applicationName": "psql",
    "backendStartUtc": "2026-08-13T04:08:16.974455Z",
    "blockingPids": [],
    "database": "gda_v49_phase2a_phase2b_replay_a",
    "pid": 50121,
    "query": "SET CONSTRAINTS ALL IMMEDIATE;",
    "queryStartUtc": "2026-08-13T05:41:07.649169Z",
    "state": "active",
    "stateChangeUtc": "2026-08-13T05:41:07.649170Z",
    "user": "gda_v49_phase2a_migrator",
    "waitEvent": "none",
    "waitEventType": "none",
    "xactStartUtc": "2026-08-13T04:08:17.156611Z"
  },
  "locks": {
    "clusterLocksGranted": 529,
    "clusterLocksWaiting": 0,
    "locks": [
      {
        "granted": true,
        "locktype": "object",
        "mode": "AccessShareLock",
        "relation": null,
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "object",
        "mode": "AccessShareLock",
        "relation": null,
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418505",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418512",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418471",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418560",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418550",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418582",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418502",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418561",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418521",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418556",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418575",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418486",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418470",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418555",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418495",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418552",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418522",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418482",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418542",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418520",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418501",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418475",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418532",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418516",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418565",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418465",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418585",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418531",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418487",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418562",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418472",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418570",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418546",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418510",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418467",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418455",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418492",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418456",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418536",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418466",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418497",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418517",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418576",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418496",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418506",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418547",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418551",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418567",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418461",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418511",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418545",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418541",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418447",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418566",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418577",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418491",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418537",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418485",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418477",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418515",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418530",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418507",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418527",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418572",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418500",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418462",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418581",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418460",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418526",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418481",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418480",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418535",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418451",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418571",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418540",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418457",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418452",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418557",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418525",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418450",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418476",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418490",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418586",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessExclusiveLock",
        "relation": "418580",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.delivery_policy_evaluation_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_object_place_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "raw.field_literal",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.source_version",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "418457",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "raw.source_asset_lexical_identity_unique",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "raw.source_asset_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.evidence_item_source_triplet_unique",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.evidence_item_source_record_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.endpoint_health_observation_visual_locator_id_checked_at_me_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.external_visual_reference_source_asset_id_source_record_id__key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_decision_evidence",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.evidence_item_supersedes_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.takedown_event",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.rights_observation_provider_object",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_object_source_record_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_review_decision_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.delivery_locator_qualificatio_delivery_assessment_id_allowl_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.provider_policy_evaluation_version_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.rights_assessment_provider_object_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "418467",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.rights_observation_visual_reference_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "418517",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.rights_assessment_visual_reference",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "raw.legacy_surface_archive_object_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "core.archive_object",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "418567",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.object_visual_reference_review_decis_supersedes_decision_id_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.rights_observation_representation_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "raw.source_record_legacy_id_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "418477",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_decision_evidence_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.rights_observation_state_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "418577",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "418462",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.object_source_record_source_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.rights_observation_visual_reference",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.evidence_item",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_object_type_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.rights_assessment_representation",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "research.corpus_membership_queue_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "418557",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "raw.legacy_surface_disposition_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "research.folder_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "raw.fail_closed_delta_queue_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assertion_review_decision_supersedes_decision_id_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "raw.source_asset_id_sha_unique",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.canonical_assignment_kind_status_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_object_place_archive_object_id_place_id_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "418502",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_assertion",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "raw.field_literal_source_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_object_subject_archive_object_id_subject_concept_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_identity_resolutio_legacy_identity_resolution_id_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.delivery_rights_assessment_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "raw.migration_batch",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "418482",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.object_visual_reference_review_decision",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_object_source_record",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_folder_membership_folder_id_membership_role_memb_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.provider_policy_evaluation_supersedes_provider_policy_evalu_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_object_representat_archive_object_id_digital_rep_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "raw.legacy_surface_batch_surface_unique",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.rights_observation_provider_object_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "418497",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.provider_object",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "raw.migration_batch_batch_token_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.delivery_assessment_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.rights_assessment",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_object_collection_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "418447",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.rights_assessment_supersedes_rights_assessment_id_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "research.corpus_membership_object_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assertion_review_decision",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "raw.source_record_asset_identity_unique",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "raw.migration_batch_mapping_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.rights_assessment_locator_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.rights_observation_locator",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_object_place",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "418527",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "raw.source_record_fingerprint_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.delivery_assessment_reference_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.rights_assessment_state_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "raw.migration_batch_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.provider_policy_evaluation_reference_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.rights_assessment_locator",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.provider_policy_evaluation_version_reverse_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.takedown_override",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "418452",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.evidence_item_content_hash_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "raw.source_asset",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.takedown_override_supersedes_takedown_override_id_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.endpoint_health_observation_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "research.folder",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.object_visual_reference_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_object_tree_membership",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "418582",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_object_subject",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.rights_assessment_observation_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.visual_locator",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assertion_predicate_status_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "raw.source_record_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "core.agent_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "418522",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_object_temporal_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_object_source_reco_archive_object_id_source_reco_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.external_visual_reference_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.object_source_record_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "418532",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "418547",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.object_visual_reference_reverse_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.delivery_policy_evaluation",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_object_temporal_archive_object_id_temporal_exten_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.source_version_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.visual_locator_reference_identity_unique",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.source_version_supersedes_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "418487",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_review_effective_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "core.collection_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.external_visual_reference",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.external_visual_reference_visual_reference_urn_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.evidence_item_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "raw.legacy_surface_batch_source_occurrence_unique",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_object_tree_member_archive_object_id_trace_node__key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.source_version_asset_identity_unique",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.rights_assessment_observation_reverse_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "research.corpus_membership",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "core.concept",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "raw.fail_closed_delta_source_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "raw.legacy_surface_fingerprint_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "raw.migration_batch_input_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "core.entity",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_entity_name_entity_id_field_literal_id_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.visual_locator_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assertion_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "core.collection",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_object_agent_credit",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.delivery_assessment_mode_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.provider_object_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.rights_assessment_provider_object",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "core.entity_kind_state_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.rights_observation_representation",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.object_visual_reference_review_decision_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "research.corpus_membership_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.takedown_override_takedown_scope_id_overlay_sha256_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_object_type",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.provider_policy_evaluation_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.object_visual_reference_decision_current_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_folder_membership_folder_id_archive_object_id_me_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_entity_name_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.delivery_assessment",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "core.temporal_extent",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_identity_resolution",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.takedown_event_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_identity_resolution_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.provider_object_provider_id_provider_record_key_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assertion_review_effective_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_assertion_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "core.agent",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.source_version_source_document_id_content_sha256_byte_lengt_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.object_visual_reference",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "core.entity_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "raw.fail_closed_delta",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "research.folder_folder_token_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.rights_observation",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "418512",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.takedown_override_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.delivery_assessment_supersedes_delivery_assessment_id_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.rights_assessment_visual_reference_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.visual_locator_representation_reverse_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_folder_membership_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_object_collection_archive_object_id_collection_i_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.visual_reference_provider_object_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.visual_locator_fingerprint_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.rights_observation_supersedes_rights_observation_id_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "core.place",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.visual_locator_external_visual_reference_id_locator_role_so_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "core.place_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_folder_membership",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.takedown_event_effective_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.delivery_locator_qualification_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "core.concept_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.provider_policy_evaluation_version",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "raw.field_literal_occurrence_unique",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "core.archive_object_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_entity_name",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "raw.legacy_surface_batch_ordinal_unique",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.takedown_scope_event_ordinal_unique",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.source_version_source_document_id_version_token_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assertion_review_decision_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_object_collection",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.object_visual_reference_archive_object_id_external_visual_r_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.visual_locator_reference_role_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.provider_policy_evaluation",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.rights_assessment_representation_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "raw.source_asset_authority_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "core.archive_object_urn_uidx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "418542",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.rights_assessment_observation",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "core.temporal_extent_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.takedown_scope_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_object_type_archive_object_id_type_concept_id_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_object_temporal",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.endpoint_health_locator_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.evidence_item_source_identity_unique",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_object_representation_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_object_medium_archive_object_id_medium_concept_i_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "418537",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assertion",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assertion_supersedes_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_object_medium_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_object_subject_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.takedown_override_scope_version_unique",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.object_source_record",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "raw.source_record_occurrence_unique",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.rights_observation_locator_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "418562",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "raw.fail_closed_delta_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "418472",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "raw.legacy_surface_ledger",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_object_medium",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.delivery_locator_qualification",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_object_tree_membership_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.delivery_rights_assessment",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "raw.source_record",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.canonical_assignment",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_object_agent_credit_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.rights_observation_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_object_agent_credi_archive_object_id_agent_id_cr_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "418572",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_review_decision",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_decision_evidence_reverse_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.canonical_assignment_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.endpoint_health_observation",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "418552",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_object_representation",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.visual_locator_representation",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "raw.field_literal_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.object_visual_reference_archive_object_id_reference_role_or_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "provenance.assignment_assertion_assertion_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "418492",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.visual_reference_fingerprint_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.visual_locator_representation_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.rights_assessment_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "raw.legacy_surface_source_record_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.takedown_scope_event_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "raw.legacy_surface_ledger_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "AccessShareLock",
        "relation": "rights.takedown_scope",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "418470",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "raw.legacy_surface_ledger",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "core.archive_object",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "pg_toast.pg_toast_412933_index",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "pg_toast.pg_toast_412933",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "core.entity",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "raw.source_record",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "raw.migration_batch",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "raw.mapping_version",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "raw.source_asset",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "rights.rights_assessment_visual_reference",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "418466",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "418507",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "418547",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "418537",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "provenance.object_source_record",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "418472",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "rights.delivery_rights_assessment",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "418451",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "418552",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "418492",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "raw.field_literal",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "418457",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "core.legacy_identity",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "418467",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "418517",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "418477",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "418462",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "rights.rights_observation_visual_reference",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "rights.legacy_visual_surface_classification",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "418557",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "418471",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "rights.legacy_visual_surface_disposition",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "research.corpus_version",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "research.trace_node",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "418497",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "418447",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "418527",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "research.corpus",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "418452",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "pg_toast.pg_toast_412987_index",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "418582",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "rights.visual_locator",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "pg_toast.pg_toast_413008",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "418522",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "418532",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "raw.fail_closed_delta",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "research.corpus_membership",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "rights.delivery_assessment",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "rights.object_visual_reference",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "418512",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "rights.provider_policy_evaluation",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "rights.rights_assessment_observation",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "418542",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "pg_toast.pg_toast_412987",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "provenance.assignment_folder_membership",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "rights.rights_observation",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "rights.external_visual_reference",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "418487",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "418465",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "rights.delivery_policy_evaluation",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "research.folder",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "research.object_trace_node",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "pg_toast.pg_toast_413008_index",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "rights.rights_assessment",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "418482",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "418502",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "418450",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "418577",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "418567",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "418572",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "provenance.canonical_assignment",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "relation": "418562",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "research.folder_folder_token_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "rights.object_visual_reference",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "core.entity_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "rights.delivery_assessment",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "raw.source_record_legacy_id_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "core.archive_object",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "raw.source_asset_authority_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "raw.legacy_surface_archive_object_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "rights.external_visual_reference_source_asset_id_source_record_id__key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "rights.legacy_visual_surface_disposition_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "raw.legacy_surface_ledger_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "rights.rights_assessment_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "raw.legacy_surface_source_record_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "rights.object_visual_reference_archive_object_id_reference_role_or_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "research.corpus_version_corpus_id_policy_sha256_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "provenance.canonical_assignment_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "raw.mapping_version_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "raw.source_record",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "provenance.canonical_assignment",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "raw.source_record_occurrence_unique",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "research.corpus_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "raw.mapping_version_version_token_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "core.archive_object_urn_uidx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "research.corpus_version_policy_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "rights.provider_policy_evaluation",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "rights.object_visual_reference_archive_object_id_external_visual_r_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "raw.legacy_surface_batch_ordinal_unique",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "core.archive_object_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "rights.delivery_assessment_reference_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "rights.rights_observation_supersedes_rights_observation_id_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "rights.visual_reference_provider_object_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "rights.delivery_assessment_supersedes_delivery_assessment_id_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "rights.rights_observation",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "provenance.canonical_assignment_kind_status_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "rights.provider_policy_evaluation_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "core.entity_kind_state_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "rights.delivery_assessment_mode_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "core.entity",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "raw.legacy_surface_fingerprint_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "raw.migration_batch_input_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "raw.legacy_surface_batch_source_occurrence_unique",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "rights.external_visual_reference_visual_reference_urn_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "research.trace_node_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "rights.external_visual_reference",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "raw.legacy_surface_disposition_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "rights.visual_reference_fingerprint_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "research.corpus_version_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "rights.object_visual_reference_reverse_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "rights.rights_observation_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "rights.external_visual_reference_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "raw.source_record_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "rights.object_visual_reference_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "research.folder",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "raw.source_asset",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "raw.legacy_surface_ledger",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "rights.provider_policy_evaluation_reference_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "rights.rights_assessment_state_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "raw.migration_batch_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "research.corpus",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "raw.source_record_fingerprint_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "raw.migration_batch_mapping_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "research.trace_node_entity_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "raw.source_record_asset_identity_unique",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "research.corpus_version_corpus_id_version_token_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "research.corpus_corpus_token_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "rights.delivery_assessment_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "rights.rights_assessment",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "raw.mapping_version",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "raw.migration_batch_batch_token_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "raw.legacy_surface_batch_surface_unique",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "rights.provider_policy_evaluation_supersedes_provider_policy_evalu_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "raw.migration_batch",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "raw.source_asset_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "research.trace_node",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "research.corpus_version",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "research.trace_node_canonical_key_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "research.corpus_version_exact_policy_pair",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "rights.rights_assessment_supersedes_rights_assessment_id_key",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "rights.legacy_visual_surface_disposition",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "raw.source_asset_lexical_identity_unique",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "research.folder_pkey",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "rights.rights_observation_state_idx",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "RowShareLock",
        "relation": "raw.source_asset_id_sha_unique",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "ShareLock",
        "relation": "418460",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "ShareLock",
        "relation": "418545",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "ShareLock",
        "relation": "418555",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "ShareLock",
        "relation": "418570",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "ShareLock",
        "relation": "418495",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "ShareLock",
        "relation": "418565",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "ShareLock",
        "relation": "418450",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "ShareLock",
        "relation": "418540",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "ShareLock",
        "relation": "418525",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "ShareLock",
        "relation": "418580",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "ShareLock",
        "relation": "418535",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "ShareLock",
        "relation": "418500",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "ShareLock",
        "relation": "418515",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "ShareLock",
        "relation": "418510",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "ShareLock",
        "relation": "418550",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "ShareLock",
        "relation": "418475",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "ShareLock",
        "relation": "418465",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "ShareLock",
        "relation": "418585",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "ShareLock",
        "relation": "418455",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "ShareLock",
        "relation": "418520",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "ShareLock",
        "relation": "418575",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "ShareLock",
        "relation": "418470",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "ShareLock",
        "relation": "418560",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "ShareLock",
        "relation": "418480",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "ShareLock",
        "relation": "418505",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "ShareLock",
        "relation": "418530",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "ShareLock",
        "relation": "418485",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "relation",
        "mode": "ShareLock",
        "relation": "418490",
        "transactionid": null
      },
      {
        "granted": true,
        "locktype": "transactionid",
        "mode": "ExclusiveLock",
        "relation": null,
        "transactionid": "4324"
      },
      {
        "granted": true,
        "locktype": "virtualxid",
        "mode": "ExclusiveLock",
        "relation": null,
        "transactionid": null
      }
    ]
  },
  "runtimeLog": {
    "bytes": 62,
    "path": "/private/tmp/gda_v49_phase2b_stage_final.eVALvR/replay1-runtime.log",
    "sha256": "4a0ce67f30c5bfcbb2857e89db61a20294cf93857fd96b10b54336f72a1835ed",
    "tail": "REPLAY_OK database=gda_v49_phase2a_phase2b_replay_a schemas=9"
  },
  "serverLog": {
    "bytes": 44542,
    "path": "/private/tmp/gda_v49_phase2b.0rUT9y/postgresql.log",
    "sha256": "c484322157fb1451e12073635acb8d7141327d2ca44e78107d717d8d5666deb9",
    "tail": "2026-08-12 22:57:16.392 AEST [6046] LOG:  checkpoint complete: wrote 6321 buffers (38.6%); 0 WAL file(s) added, 0 removed, 25 recycled; write=269.236 s, sync=0.093 s, total=269.636 s; sync files=217, longest=0.032 s, average=0.001 s; distance=409558 kB, estimate=487529 kB; lsn=2/9C54BF20, redo lsn=2/94719DE0\n2026-08-12 22:57:46.072 AEST [6046] LOG:  checkpoint starting: time\n2026-08-12 23:02:16.767 AEST [6046] LOG:  checkpoint complete: wrote 4071 buffers (24.8%); 0 WAL file(s) added, 3 removed, 6 recycled; write=269.943 s, sync=0.500 s, total=270.695 s; sync files=162, longest=0.062 s, average=0.004 s; distance=141377 kB, estimate=452914 kB; lsn=2/A7FFDAF0, redo lsn=2/9D12A498\n2026-08-12 23:02:46.694 AEST [6046] LOG:  checkpoint starting: time\n2026-08-12 23:07:08.827 AEST [31526] LOG:  automatic vacuum of table \"gda_v49_phase2a_phase2b_failure.raw.field_literal\": index scans: 1\n\tpages: 53177 removed, 0 remain, 53177 scanned (100.00% of total)\n\ttuples: 3559820 removed, 0 remain, 0 are dead but not yet removable\n\tremovable cutoff: 3137, which was 20 XIDs old when operation ended\n\tnew relfrozenxid: 3137, which is 24 XIDs ahead of previous value\n\tfrozen: 0 pages from table (0.00% of total) had 0 tuples frozen\n\tindex scan needed: 53177 pages from table (100.00% of total) had 3559820 dead item identifiers removed\n\tindex \"field_literal_pkey\": pages: 33788 in total, 18015 newly deleted, 33784 currently deleted, 18747 reusable\n\tindex \"field_literal_occurrence_unique\": pages: 77907 in total, 38951 newly deleted, 77902 currently deleted, 38951 reusable\n\tindex \"field_literal_source_idx\": pages: 8548 in total, 4272 newly deleted, 8544 currently deleted, 4272 reusable\n\tavg read rate: 2.741 MB/s, avg write rate: 1.691 MB/s\n\tbuffer usage: 643371 hits, 284563 misses, 175541 dirtied\n\tWAL usage: 342361 records, 181390 full page images, 343067038 bytes\n\tsystem usage: CPU: user: 4.41 s, system: 4.28 s, elapsed: 810.97 s\n2026-08-12 23:07:16.469 AEST [6046] LOG:  checkpoint complete: wrote 7534 buffers (46.0%); 0 WAL file(s) added, 2 removed, 9 recycled; write=269.403 s, sync=0.071 s, total=269.775 s; sync files=8, longest=0.069 s, average=0.009 s; distance=194759 kB, estimate=427098 kB; lsn=2/AE6EA900, redo lsn=2/A8F5C428\n2026-08-12 23:17:46.518 AEST [6046] LOG:  checkpoint starting: time\n2026-08-12 23:21:02.905 AEST [6046] LOG:  checkpoint complete: wrote 1161 buffers (7.1%); 0 WAL file(s) added, 5 removed, 1 recycled; write=195.719 s, sync=0.173 s, total=196.388 s; sync files=76, longest=0.045 s, average=0.003 s; distance=90393 kB, estimate=393428 kB; lsn=2/CC3AE510, redo lsn=2/AE7A2B98\n2026-08-12 23:21:14.154 AEST [6046] LOG:  checkpoint starting: wal\n2026-08-12 23:23:29.435 AEST [6046] LOG:  checkpoint complete: wrote 7192 buffers (43.9%); 0 WAL file(s) added, 0 removed, 33 recycled; write=135.199 s, sync=0.062 s, total=135.281 s; sync files=11, longest=0.021 s, average=0.006 s; distance=533087 kB, estimate=533087 kB; lsn=2/ECC19B50, redo lsn=2/CF03A970\n2026-08-12 23:23:47.337 AEST [6046] LOG:  checkpoint starting: wal\n2026-08-12 23:26:22.064 AEST [6046] LOG:  checkpoint complete: wrote 11999 buffers (73.2%); 0 WAL file(s) added, 0 removed, 33 recycled; write=154.454 s, sync=0.118 s, total=154.727 s; sync files=8, longest=0.059 s, average=0.015 s; distance=540829 kB, estimate=540829 kB; lsn=3/DBD1CB8, redo lsn=2/F0062140\n2026-08-12 23:26:44.675 AEST [6046] LOG:  checkpoint starting: wal\n2026-08-12 23:31:14.556 AEST [6046] LOG:  checkpoint complete: wrote 5770 buffers (35.2%); 0 WAL file(s) added, 0 removed, 33 recycled; write=269.336 s, sync=0.122 s, total=269.881 s; sync files=12, longest=0.053 s, average=0.011 s; distance=540545 kB, estimate=540801 kB; lsn=3/2DCC4C80, redo lsn=3/11042920\n2026-08-12 23:31:44.577 AEST [6046] LOG:  checkpoint starting: time\n2026-08-12 23:31:59.124 AEST [6046] LOG:  checkpoint complete: wrote 114 buffers (0.7%); 0 WAL file(s) added, 0 removed, 28 recycled; write=14.026 s, sync=0.001 s, total=14.548 s; sync files=1, longest=0.001 s, average=0.001 s; distance=472428 kB, estimate=533964 kB; lsn=3/2DE03F38, redo lsn=3/2DD9D950\n2026-08-12 23:34:31.047 AEST [31925] ERROR:  PHASE2B_INJECTED_FAILURE:after_parity\n2026-08-12 23:34:31.047 AEST [31925] CONTEXT:  PL/pgSQL function pg_temp_3.gda_inject(text) line 4 at RAISE\n2026-08-12 23:34:31.047 AEST [31925] STATEMENT:  SELECT pg_temp.gda_inject('after_parity');\n2026-08-12 23:36:44.331 AEST [6046] LOG:  checkpoint starting: time\n2026-08-12 23:41:14.153 AEST [6046] LOG:  checkpoint complete: wrote 6224 buffers (38.0%); 0 WAL file(s) added, 0 removed, 15 recycled; write=269.682 s, sync=0.123 s, total=269.823 s; sync files=266, longest=0.049 s, average=0.001 s; distance=244295 kB, estimate=504997 kB; lsn=3/47BBC208, redo lsn=3/3CC2F7E0\n2026-08-12 23:41:44.986 AEST [6046] LOG:  checkpoint starting: time\n2026-08-12 23:46:14.158 AEST [6046] LOG:  checkpoint complete: wrote 7424 buffers (45.3%); 0 WAL file(s) added, 1 removed, 13 recycled; write=269.056 s, sync=0.031 s, total=269.172 s; sync files=7, longest=0.031 s, average=0.005 s; distance=219613 kB, estimate=476458 kB; lsn=3/4EED91B8, redo lsn=3/4A2A6CE8\n2026-08-13 10:29:35.006 AEST [46911] FATAL:  role \"jarlgiovanni\" does not exist\n2026-08-13 10:41:01.907 AEST [6046] LOG:  checkpoint starting: time\n2026-08-13 10:45:34.821 AEST [6046] LOG:  checkpoint complete: wrote 6039 buffers (36.9%); 0 WAL file(s) added, 4 removed, 1 recycled; write=269.105 s, sync=1.554 s, total=272.914 s; sync files=1404, longest=0.168 s, average=0.002 s; distance=92435 kB, estimate=438056 kB; lsn=3/4FCEDBA8, redo lsn=3/4FCEBC90\n2026-08-13 14:08:04.158 AEST [6046] LOG:  checkpoint starting: time\n2026-08-13 14:08:19.062 AEST [6046] LOG:  checkpoint complete: wrote 102 buffers (0.6%); 0 WAL file(s) added, 0 removed, 0 recycled; write=14.744 s, sync=0.053 s, total=14.904 s; sync files=18, longest=0.049 s, average=0.003 s; distance=226 kB, estimate=394273 kB; lsn=3/4FDA7C58, redo lsn=3/4FD24600\n2026-08-13 14:13:04.133 AEST [6046] LOG:  checkpoint starting: time\n2026-08-13 14:13:19.302 AEST [6046] LOG:  checkpoint complete: wrote 106 buffers (0.6%); 0 WAL file(s) added, 0 removed, 0 recycled; write=14.461 s, sync=0.536 s, total=15.170 s; sync files=35, longest=0.134 s, average=0.016 s; distance=662 kB, estimate=354912 kB; lsn=3/4FDCA4B8, redo lsn=3/4FDCA068\n2026-08-13 14:18:04.310 AEST [6046] LOG:  checkpoint starting: time\n2026-08-13 14:18:04.541 AEST [6046] LOG:  checkpoint complete: wrote 0 buffers (0.0%); 0 WAL file(s) added, 0 removed, 0 recycled; write=0.165 s, sync=0.001 s, total=0.232 s; sync files=0, longest=0.000 s, average=0.000 s; distance=3 kB, estimate=319421 kB; lsn=3/4FDCB240, redo lsn=3/4FDCADF0\n2026-08-13 14:23:04.707 AEST [6046] LOG:  checkpoint starting: time\n2026-08-13 14:23:05.122 AEST [6046] LOG:  checkpoint complete: wrote 0 buffers (0.0%); 0 WAL file(s) added, 0 removed, 0 recycled; write=0.145 s, sync=0.001 s, total=0.481 s; sync files=0, longest=0.000 s, average=0.000 s; distance=3 kB, estimate=287479 kB; lsn=3/4FDCBFC8, redo lsn=3/4FDCBB78\n2026-08-13 14:28:04.188 AEST [6046] LOG:  checkpoint starting: time\n2026-08-13 14:28:04.756 AEST [6046] LOG:  checkpoint complete: wrote 0 buffers (0.0%); 0 WAL file(s) added, 0 removed, 0 recycled; write=0.027 s, sync=0.001 s, total=0.569 s; sync files=0, longest=0.000 s, average=0.000 s; distance=3 kB, estimate=258732 kB; lsn=3/4FDCCD68, redo lsn=3/4FDCC918\n2026-08-13 14:33:04.759 AEST [6046] LOG:  checkpoint starting: time\n2026-08-13 14:33:05.079 AEST [6046] LOG:  checkpoint complete: wrote 0 buffers (0.0%); 0 WAL file(s) added, 0 removed, 0 recycled; write=0.001 s, sync=0.001 s, total=0.320 s; sync files=0, longest=0.000 s, average=0.000 s; distance=3 kB, estimate=232859 kB; lsn=3/4FDCDAF0, redo lsn=3/4FDCD6A0\n2026-08-13 14:38:04.162 AEST [6046] LOG:  checkpoint starting: time\n2026-08-13 14:42:35.651 AEST [6046] LOG:  checkpoint complete: wrote 2008 buffers (12.3%); 0 WAL file(s) added, 14 removed, 6 recycled; write=269.781 s, sync=0.154 s, total=271.489 s; sync files=34, longest=0.032 s, average=0.005 s; distance=325899 kB, estimate=325899 kB; lsn=3/74C64728, redo lsn=3/63C103F0\n2026-08-13 14:43:04.694 AEST [6046] LOG:  checkpoint starting: time\n2026-08-13 14:47:34.787 AEST [6046] LOG:  checkpoint complete: wrote 10109 buffers (61.7%); 0 WAL file(s) added, 0 removed, 19 recycled; write=269.282 s, sync=0.044 s, total=270.067 s; sync files=8, longest=0.028 s, average=0.006 s; distance=311544 kB, estimate=324463 kB; lsn=3/83E7FB20, redo lsn=3/76C4E6F8\n2026-08-13 14:48:04.844 AEST [6046] LOG:  checkpoint starting: time\n2026-08-13 14:52:34.243 AEST [6046] LOG:  checkpoint complete: wrote 10294 buffers (62.8%); 0 WAL file(s) added, 2 removed, 13 recycled; write=269.162 s, sync=0.010 s, total=269.400 s; sync files=8, longest=0.007 s, average=0.002 s; distance=237976 kB, estimate=315815 kB; lsn=3/9087F548, redo lsn=3/854B4798\n2026-08-13 14:53:04.282 AEST [6046] LOG:  checkpoint starting: time\n2026-08-13 14:57:34.688 AEST [6046] LOG:  checkpoint complete: wrote 11751 buffers (71.7%); 0 WAL file(s) added, 1 removed, 13 recycled; write=269.768 s, sync=0.055 s, total=270.407 s; sync files=5, longest=0.040 s, average=0.011 s; distance=230472 kB, estimate=307280 kB; lsn=3/A47AA2E8, redo lsn=3/935C6910\n2026-08-13 14:58:04.802 AEST [6046] LOG:  checkpoint starting: time\n2026-08-13 15:02:34.388 AEST [6046] LOG:  checkpoint complete: wrote 12604 buffers (76.9%); 0 WAL file(s) added, 0 removed, 19 recycled; write=269.215 s, sync=0.010 s, total=269.586 s; sync files=5, longest=0.005 s, average=0.002 s; distance=313880 kB, estimate=313880 kB; lsn=3/B56E9F78, redo lsn=3/A684CA48\n2026-08-13 15:03:04.483 AEST [6046] LOG:  checkpoint starting: time\n2026-08-13 15:07:34.090 AEST [6046] LOG:  checkpoint complete: wrote 10052 buffers (61.4%); 0 WAL file(s) added, 0 removed, 16 recycled; write=269.454 s, sync=0.005 s, total=269.607 s; sync files=5, longest=0.003 s, average=0.001 s; distance=263453 kB, estimate=308837 kB; lsn=3/C2FF0AF0, redo lsn=3/B6993E48\n2026-08-13 15:08:04.135 AEST [6046] LOG:  checkpoint starting: time\n2026-08-13 15:12:34.449 AEST [6046] LOG:  checkpoint complete: wrote 8409 buffers (51.3%); 0 WAL file(s) added, 1 removed, 13 recycled; write=269.873 s, sync=0.168 s, total=270.315 s; sync files=5, longest=0.162 s, average=0.034 s; distance=223007 kB, estimate=300254 kB; lsn=3/CDFB4FD8, redo lsn=3/C435BA68\n2026-08-13 15:13:04.477 AEST [6046] LOG:  checkpoint starting: time\n2026-08-13 15:17:34.575 AEST [6046] LOG:  checkpoint complete: wrote 8050 buffers (49.1%); 0 WAL file(s) added, 2 removed, 8 recycled; write=269.439 s, sync=0.207 s, total=270.098 s; sync files=8, longest=0.097 s, average=0.026 s; distance=165480 kB, estimate=286777 kB; lsn=3/D7373078, redo lsn=3/CE4F5C20\n2026-08-13 15:18:04.389 AEST [6046] LOG:  checkpoint starting: time\n2026-08-13 15:22:34.503 AEST [6046] LOG:  checkpoint complete: wrote 5012 buffers (30.6%); 0 WAL file(s) added, 1 removed, 9 recycled; write=269.667 s, sync=0.003 s, total=270.115 s; sync files=5, longest=0.002 s, average=0.001 s; distance=165851 kB, estimate=274684 kB; lsn=3/E3F74E30, redo lsn=3/D86EC838\n2026-08-13 15:23:04.559 AEST [6046] LOG:  checkpoint starting: time\n2026-08-13 15:27:34.121 AEST [6046] LOG:  checkpoint complete: wrote 7014 buffers (42.8%); 0 WAL file(s) added, 1 removed, 11 recycled; write=269.530 s, sync=0.012 s, total=269.563 s; sync files=5, longest=0.007 s, average=0.002 s; distance=193496 kB, estimate=266565 kB; lsn=3/EC81BC60, redo lsn=3/E43E2960\n2026-08-13 15:28:04.235 AEST [6046] LOG:  checkpoint starting: time\n2026-08-13 15:32:34.129 AEST [6046] LOG:  checkpoint complete: wrote 7214 buffers (44.0%); 0 WAL file(s) added, 1 removed, 7 recycled; write=269.794 s, sync=0.003 s, total=269.895 s; sync files=5, longest=0.002 s, average=0.001 s; distance=138416 kB, estimate=253750 kB; lsn=3/F4B7E948, redo lsn=3/ECB0E978\n2026-08-13 15:33:04.201 AEST [6046] LOG:  checkpoint starting: time\n2026-08-13 15:37:34.643 AEST [6046] LOG:  checkpoint complete: wrote 937 buffers (5.7%); 0 WAL file(s) added, 2 removed, 6 recycled; write=269.641 s, sync=0.005 s, total=270.440 s; sync files=6, longest=0.003 s, average=0.001 s; distance=131777 kB, estimate=241553 kB; lsn=3/F4F00988, redo lsn=3/F4BBF008\n2026-08-13 15:38:04.660 AEST [6046] LOG:  checkpoint starting: time\n2026-08-13 15:42:34.442 AEST [6046] LOG:  checkpoint complete: wrote 1229 buffers (7.5%); 0 WAL file(s) added, 2 removed, 0 recycled; write=269.340 s, sync=0.213 s, total=269.782 s; sync files=133, longest=0.045 s, average=0.002 s; distance=32928 kB, estimate=220690 kB; lsn=4/2CD1130, redo lsn=3/F6BE71B8\n2026-08-14 00:49:09.908 AEST [67881] ERROR:  operator does not exist: text || integer[] at character 117\n2026-08-14 00:49:09.908 AEST [67881] HINT:  No operator matches the given name and argument types. You might need to add explicit type casts.\n2026-08-14 00:49:09.908 AEST [67881] STATEMENT:  BEGIN READ ONLY; SELECT state || E'\\t' || COALESCE(wait_event_type,'') || E'\\t' || COALESCE(wait_event,'') || E'\\t' || pg_blocking_pids(pid) FROM pg_stat_activity WHERE pid=50121; COMMIT;"
  },
  "temporaryDiskKiB": {
    "pgdata": 4465084,
    "stage": 4752748
  }
}
```

At the hard stop, `pg_cancel_backend` was invoked only for the resolved task-owned backend. The runner then exited nonzero and the post-cancel read-only verifier proved atomic rollback.
