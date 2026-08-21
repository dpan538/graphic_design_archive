# API/database crosscheck

```text
API_DATABASE_CROSSCHECK=PASS
API_STABLE_ID_CROSSCHECK=PASS
API_RELEASE_ID_CROSSCHECK=PASS
API_PAGINATION_NO_DUPLICATES=PASS
API_PAGINATION_NO_OMISSIONS=PASS
API_HELD_DATA_EXPOSURE_COUNT=0
API_QUARANTINED_DATA_EXPOSURE_COUNT=0
API_RIGHTS_WIDENING_COUNT=0
API_VISIBLE_OBJECT_COUNT=7995
API_VISIBLE_RELATIONSHIP_COUNT=0
```

The HTTP envelope, overview, detail, search keys, total count, ordering set, and public counts were checked against the exact-pair `api_v1` views as `gda_v49_phase2a_api_reader`. Search result keys resolved through the detail endpoint. Held stable ID `SURF-CSPTRACE2026R0093` returned 404. Before/after API-visible fingerprints were identical: `953eb350c00d8fc1f145076ad5b1857070433ce7ca862b6fb33f115361a14b3c`.
