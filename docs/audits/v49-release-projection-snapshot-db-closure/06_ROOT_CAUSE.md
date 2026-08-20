# Root cause

The exact semantic and performance defect was the final v5 membership parity anti-join in historical function 018:

```sql
r.folder_id=e.folder_id
AND r.archive_object_id=e.archive_object_id
AND r.membership_role=e.membership_role
```

The published tuple also contains `member_ordinal`; omitting it made the folder/order unique index only a prefix candidate and forced a many-to-many join/filter pattern. Baseline parity time rose from 238.566 ms at 1k to 963.142 ms at 2k (stage exponent about 2.015), becoming the first and dominant superlinear stage. This is neither a generic “database slow” diagnosis nor a hardware-budget issue.
