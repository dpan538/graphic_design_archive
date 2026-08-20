# Stable-ID reconciliation

The reconciler recomputes the 190,067,852-byte Candidate hash, verifies the staging ledger descriptor hashes, and compares every surface ID plus deterministic ledger/source/object/delta UUID across Candidate-derived ledger, Fresh A, and Fresh B. It writes explicit missing, unexpected, duplicate, remapped, source-mismatch, and quarantined ledgers; empty ledgers retain headers.

Held/quarantined accounting contains exactly 7,928 IDs and is not an unexplained delta. Source, Fresh A, and Fresh B each contain 15,923 stable IDs. Missing, unexpected, duplicate, remapped, source-mismatch, unexplained, rights-widening, unknown-coercion, silent-drop, and silent-split counts are all zero. `STABLE_ID_RECONCILIATION=PASS`.
