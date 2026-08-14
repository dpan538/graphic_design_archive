# Surface-row ledger normalization

The staging ledger's 15,923 empty final `quarantine_id` cells used trailing TSV tabs. To satisfy the repository whitespace gate, the committed audit copy encodes only those empty final cells as the explicit audit token `NONE`.

```json
{
  "rawAuditCopy": {
    "bytes": 4640510,
    "sha256": "b18acf47c73b852a9be9bcbbb7b030b32850fc4a459d7bf080027c3fe55e5eff"
  },
  "rawStagingDescriptor": {
    "bytes": 4640510,
    "sha256": "b18acf47c73b852a9be9bcbbb7b030b32850fc4a459d7bf080027c3fe55e5eff",
    "stagePath": "surface-row-ledger.tsv"
  },
  "transformedAuditCopy": {
    "bytes": 4704202,
    "convertedRows": 15923,
    "path": "/Users/jarlgiovanni/Desktop/modern_GD_history_v49_data_platform/docs/audits/v49-phase2b-migration/18_SURFACE_ROW_LEDGER.tsv",
    "quarantineIdEmptyValuesEncodedAs": "NONE",
    "rows": 15923,
    "sha256": "48f98f68ca2ec0cef96c82ecc9c01e4129eb9a3f91e08b07ad9a59644a9d4e01"
  }
}
```

All source ordinals, identity fields, presence/tier fields, disposition fields, and nonempty values are unchanged. The raw descriptor remains bound to the retained staging cache.
