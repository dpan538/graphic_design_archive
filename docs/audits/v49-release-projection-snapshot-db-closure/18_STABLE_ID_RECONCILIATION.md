# Stable-ID reconciliation

The reconciler recomputes the 190,067,852-byte Candidate hash, verifies the staging ledger descriptor hashes, and compares every surface ID plus deterministic ledger/source/object/delta UUID across Candidate-derived ledger, Fresh A, and Fresh B. It writes explicit missing, unexpected, duplicate, remapped, source-mismatch, and quarantined ledgers; empty ledgers retain headers.

Held/quarantined accounting is expected to contain 7,928 IDs and is not an unexplained delta. Final result: `FINAL_PENDING`.
