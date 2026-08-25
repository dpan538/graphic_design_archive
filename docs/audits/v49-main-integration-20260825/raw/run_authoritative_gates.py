#!/usr/bin/env python3
"""Run current authoritative v49 gates and preserve plain-text receipts."""

from __future__ import annotations

import csv
import os
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
FRONTEND = ROOT / "frontend"
RAW = Path(__file__).resolve().parent
TMP_EVIDENCE = Path("/private/tmp/graphic_design_archive_v49_main_integration_gate_evidence")


GATES = [
    ("DEPENDENCY_INSTALL", FRONTEND, ["npm", "ci"]),
    ("TYPECHECK", FRONTEND, ["npx", "tsc", "--noEmit", "--pretty", "false"]),
    ("SEARCH_INDEX", FRONTEND, ["npm", "run", "verify:search-v49-index"]),
    ("SEARCH_REGRESSION", FRONTEND, ["npm", "run", "test:search-v49"]),
    ("CONTEXT_PROJECTION", FRONTEND, ["npm", "run", "verify:context-v1-projection"]),
    ("CONTEXT_GOVERNANCE", FRONTEND, [
        "node", "--expose-gc", "--conditions=react-server", "scripts/verify-context-governance-v1.mjs",
        "--evidence-dir", str(TMP_EVIDENCE / "context-governance"),
    ]),
    ("CONTEXT_RUNTIME", FRONTEND, [
        "node", "--expose-gc", "--conditions=react-server", "scripts/rehearse-context-runtime-v1.mjs",
        "--evidence-dir", str(TMP_EVIDENCE / "context-runtime"),
    ]),
    ("CONTEXT_API", FRONTEND, ["npm", "run", "test:context-api-v1"]),
    ("SPACETIME_PROJECTION", FRONTEND, ["npm", "run", "verify:spacetime-v1-projection"]),
    ("SPACETIME_GOVERNANCE", FRONTEND, ["npm", "run", "test:spacetime-governance-v1"]),
    ("SPACETIME_RUNTIME", FRONTEND, ["npm", "run", "test:spacetime-runtime-v1"]),
    ("SPACETIME_API", FRONTEND, ["npm", "run", "test:spacetime-api-v1"]),
    ("SPACETIME_GIS", FRONTEND, ["npm", "run", "test:spacetime-gis-v1"]),
    ("ROUND8_RESET_GUARD", FRONTEND, ["npm", "run", "verify:exploration-reset"]),
    ("ROUND8_ZERO_OBJECT_AND_BAD_PRACTICE", FRONTEND, ["npm", "run", "test:exploration-domain"]),
    ("ROUND9_RESEARCH_GATES", ROOT, ["python3", "scripts/validate_trace_v49_relation_vocabulary_round1.py"]),
    ("READ_PLATFORM_API", FRONTEND, ["npm", "run", "test:read-platform"]),
    ("PAGE_MODULE_API_CONTRACT", FRONTEND, ["node", "scripts/verify-page-by-key-module-contract.mjs"]),
    ("PRODUCTION_BUILD", FRONTEND, ["npm", "run", "build"]),
    ("DATABASE_FREEZE", ROOT, ["python3", "scripts/repository/verify_v49_database_freeze.py", "--repo", "."]),
    ("REPOSITORY_HYGIENE", ROOT, ["python3", "scripts/repository/audit_repository_hygiene.py", "--repo", "."]),
    ("EXISTING_AUDIT_SELF_CONTAINED", ROOT, [
        "python3", "database/scripts/verify_audit_package_self_contained.py",
        "--package", "docs/audits/v49-phase2b-evidence-amendment", "--require-index",
    ]),
    ("GIT_DIFF_CHECK", ROOT, ["git", "diff", "--check"]),
]


def command_text(command: list[str], cwd: Path) -> str:
    rendered = " ".join(command)
    return rendered if cwd == ROOT else f"(cd frontend && {rendered})"


def evidence_line(output: str) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in output.splitlines() if line.strip()]
    preferred = [line for line in lines if "=PASS" in line or '"status": "PASS"' in line]
    chosen = preferred[-1] if preferred else (lines[-1] if lines else "command completed with no output")
    return chosen[:600]


def write_results(rows: list[dict[str, str]]) -> None:
    path = RAW / "test-results.tsv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["gate", "result", "command", "evidence"],
                                delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    TMP_EVIDENCE.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []
    failures = 0
    env = dict(os.environ)
    env["CI"] = "1"
    for ordinal, (gate, cwd, command) in enumerate(GATES, 1):
        print(f"[{ordinal:02d}/{len(GATES):02d}] {gate} ...", flush=True)
        completed = subprocess.run(command, cwd=cwd, env=env, text=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   timeout=900, check=False)
        output = completed.stdout
        (RAW / f"gate-{ordinal:02d}-{gate.lower().replace('_', '-')}.log").write_text(
            output, encoding="utf-8"
        )
        result = "PASS" if completed.returncode == 0 else "FAIL"
        rows.append({
            "gate": gate,
            "result": result,
            "command": command_text(command, cwd),
            "evidence": evidence_line(output),
        })
        write_results(rows)
        print(f"[{ordinal:02d}/{len(GATES):02d}] {gate}={result}", flush=True)
        if completed.returncode:
            failures += 1
    print(f"AUTHORITATIVE_GATE_COUNT={len(rows)} FAILURES={failures}", flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
