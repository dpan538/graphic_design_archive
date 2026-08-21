# Retention classification

The source-tree ledger classifies every file. Actions: `{'KEEP_ACTIVE': 1094, 'KEEP_CURRENT_DOCUMENTATION': 350, 'ARCHIVE_BY_IMMUTABLE_REF': 2121, 'KEEP_RELEASE_INPUT': 4, 'KEEP_RELEASE_EVIDENCE': 879, 'DELETE_REGENERABLE': 10}`. Exactly 2,121 files are removed from the active tip but recoverable by immutable ref, and 10 are deleted as reproducible outputs. Four release inputs remain byte-identical. Top-level scripts are covered by `docs/maintenance/V49_ACTIVE_SCRIPT_ALLOWLIST.json`; none are unclassified.
