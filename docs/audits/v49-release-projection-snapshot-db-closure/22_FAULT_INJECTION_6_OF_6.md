# Fault injection 6/6

The six v5 builder fault points are after release objects, folders, memberships, component hashes, build receipt, and before candidate transition. Each must raise `P0001` and leave zero release, projection, receipt, and event residue. Additional assertions cover wrong digest, publisher denial of the internal fault surface, and candidate non-publication.

Final result: `FINAL_PENDING`.
