# v49 active script allowlist

All tracked files under `scripts/` are enumerated in the adjacent CSV and JSON ledgers. The allowlist is conservative: repository-maintenance and v49 API verification scripts remain executable current tooling; the remaining small research/capture scripts are retained only as provenance/reproduction methods for indexed audit evidence. They are not canonical inputs, database entry points, runtime dependencies, or authorization to recapture rights-sensitive material.

The immutable source anchor `v49-data-api-closure-20260821` preserves every original script and its historical inputs. A later v50 change may remove the provenance-only group after the dependent audit packages are independently repackaged; this v49 closure does not rewrite those packages or their historical checksums.

Machine fields include path, category, current runtime/API/database/CI use, retained audit role, and decision. There are no unclassified scripts.

Round 12 reconciles the CSV with the previously authoritative JSON ledger and adds twelve stdlib-only inquiry-engine scripts plus their shared cross-runtime fixture under `CURRENT_V49_EXPLORATION_INQUIRY_ENGINE_VERIFICATION`. These are governed research/audit reproduction tools; they do not become runtime, API, database, or CI entry points.
