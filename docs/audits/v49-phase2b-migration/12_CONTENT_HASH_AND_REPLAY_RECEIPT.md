# Fresh replay and content hash

Fresh A entered `SET CONSTRAINTS ALL IMMEDIATE` but did not commit; Fresh B was never created. A population content hash would misrepresent an uncommitted transaction, so none is issued.

```text
FRESH_POPULATION_REPLAY_COUNT=0
FRESH_A_STARTED=true
FRESH_A_COMMITTED=false
FRESH_B_STARTED=false
POPULATION_CONTENT_HASH_DETERMINISTIC=false
```
