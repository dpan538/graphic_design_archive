# DML permission 36/36

Twelve guarded release tables × INSERT/UPDATE/DELETE form the 36 cases. Companion assertions cover migration ownership; API view-only access; core/research/release base-table denial; publisher canonical-write denial; v5 wrapper/internal separation; reviewer-only v5 verification; PUBLIC/default DML absence; and cleanup index keep/drop state.

All 36 DML cases and companion role/object assertions passed; the transaction rolled back with zero matrix residue. `FINAL_36_36_DML_PERMISSION=PASS`.
