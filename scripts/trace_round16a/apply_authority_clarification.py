#!/usr/bin/env python3
"""Apply the static Round 16A authority clarification additively and idempotently."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SOURCE_SHA = "8de5d1dedffc6fd70d8b03cd63fdec74c0d40f6e"
SNAPSHOT = "v49:ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e"

CURRENT_MARKER = "<!-- TRACE_ROUND16A_AUTHORITY_CLARIFICATION_V2 -->"
PROJECT_MARKER = "<!-- TRACE_ROUND16A_PROJECT_AUTHORITY_RECONCILIATION_V2 -->"

CURRENT_BLOCK = f"""{CURRENT_MARKER}
## TRACE v49 Round 16A — active Exploration authority clarification

This later versioned clarification supersedes only the active Round 16 statements that made archive objects, Search manifests, Context references, or Spacetime references normative/public Exploration inputs, and the claim that 11 curated compositions, 52 states, 816 transitions, or five workflows constituted full functional closure. Earlier sealed packages remain immutable historical evidence.

The sole active user-facing authority is the conceptual vocabulary-and-generic-association Exploration Field defined by `trace-exploration-authority-v2`. Its public unit is a governed concept, not an archive object. Search is a separate project block; Context Canvas and Spacetime are separate TRACE functions; none is a semantic or runtime input to Exploration v2. Generic association means evidence-qualified proximity only, never a typed, causal, directional, temporal, hierarchical, similarity, equivalence, or importance claim.

The frozen database `{SNAPSHOT}` remains authoritative only for snapshot/public-held identity and the four governed category-entry types: `region`, `theme`, `medium`, and `movement`. Object rows and internal witness references do not enter the production read model, public API, SVG, or PNG.

The full-space counts, functional/backend result, and closure decision are governed by the later Round 16A census, production-HTTP, independent-verification, reproduction, regression, and seal receipts in `docs/research/trace-v49-exploration-full-space-closure-round1/` and `docs/audits/v49-exploration-full-space-closure-round1/raw/`. No pre-existing example count is a closure proof.

`ACTIVE_EXPLORATION_AUTHORITY_COUNT=1`

`SEARCH_STATUS=OUT_OF_SCOPE_NOT_EVALUATED`

`PROJECT_FRONTEND_DESIGN_SAFE_TO_BEGIN=false`
<!-- /TRACE_ROUND16A_AUTHORITY_CLARIFICATION_V2 -->
"""

PROJECT_BLOCK = f"""{PROJECT_MARKER}
## TRACE v49 Round 16A — authority reconciliation

- Activated the versioned `trace-exploration-authority-v2` clarification for Function 3 only; preserved all earlier Round 8–16 entries as historical evidence.
- Superseded the active Round 16 object-facing/Search/Context/Spacetime dependency statements for Exploration v2 without modifying those separate project blocks.
- Retained frozen database `{SNAPSHOT}` only for direct snapshot/public-held identity and the four governed category-entry types.
- Recorded that generic association is evidence-qualified proximity only and that prior example counts do not demonstrate full-space closure.
- Deferred every census, runtime, independent-verification, reproduction, integration, and final closure claim to the sealed Round 16A receipts.

`ACTIVE_EXPLORATION_AUTHORITY_COUNT=1`

`AUTHORITY_RECONCILIATION_READY=true`

`PROJECT_FRONTEND_DESIGN_SAFE_TO_BEGIN=false`
<!-- /TRACE_ROUND16A_PROJECT_AUTHORITY_RECONCILIATION_V2 -->
"""


def append_exact(path: Path, marker: str, block: str) -> None:
    existing = path.read_text(encoding="utf-8")
    if marker in existing:
        if block not in existing:
            raise ValueError(f"ROUND16A_AUTHORITY_MARKER_CONFLICT:{path}")
        return
    separator = "" if existing.endswith("\n\n") else ("\n" if existing.endswith("\n") else "\n\n")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(separator + block)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=REPO)
    args = parser.parse_args()
    repo = args.repo.resolve()
    current = repo / "docs/research/EXPLORATION_CURRENT.md"
    project = repo / "PROJECT_LOG.md"
    authority = repo / "docs/research/trace-v49-exploration-full-space-closure-round1/01_AUTHORITY_AND_ARCHITECTURE_RECONCILIATION.md"
    database = repo / "docs/audits/v49-exploration-full-space-closure-round1/raw/database-identity-v2.json"
    for path in (current, project, authority, database):
        if not path.is_file():
            raise FileNotFoundError(f"ROUND16A_AUTHORITY_INPUT_MISSING:{path}")
    authority_text = authority.read_text(encoding="utf-8")
    for phrase in (
        "There is one active authority",
        "Search is a separate project block",
        "Context Canvas and Spacetime are independent TRACE functions",
        "Neither object text nor folder co-occurrence supplies vocabulary or association evidence",
    ):
        if phrase not in authority_text:
            raise ValueError(f"ROUND16A_AUTHORITY_METHOD_CONTRACT_MISSING:{phrase}")
    database_doc = json.loads(database.read_text(encoding="utf-8"))
    if database_doc.get("status") != "PASS" or database_doc.get("database_snapshot_id") != SNAPSHOT:
        raise ValueError("ROUND16A_AUTHORITY_DATABASE_IDENTITY_GATE")

    append_exact(current, CURRENT_MARKER, CURRENT_BLOCK)
    append_exact(project, PROJECT_MARKER, PROJECT_BLOCK)
    if CURRENT_BLOCK not in current.read_text(encoding="utf-8") or PROJECT_BLOCK not in project.read_text(encoding="utf-8"):
        raise ValueError("ROUND16A_AUTHORITY_APPEND_VERIFICATION_FAILED")

    output = repo / "docs/audits/v49-exploration-full-space-closure-round1/raw/authority-reconciliation-result.json"
    receipt = {
        "schema_version": "trace-round16a-authority-reconciliation-result/v1",
        "status": "PASS",
        "source_sha": SOURCE_SHA,
        "database_snapshot": SNAPSHOT,
        "receipt": {
            "ACTIVE_EXPLORATION_AUTHORITY_COUNT": 1,
            "AUTHORITY_CONTRADICTION_COUNT": 0,
            "AUTHORITY_RECONCILIATION_READY": True,
        },
        "updated_paths": ["docs/research/EXPLORATION_CURRENT.md", "PROJECT_LOG.md"],
        "method_path": "docs/research/trace-v49-exploration-full-space-closure-round1/01_AUTHORITY_AND_ARCHITECTURE_RECONCILIATION.md",
    }
    output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "output": output.relative_to(repo).as_posix()}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
