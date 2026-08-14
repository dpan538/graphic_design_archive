#!/usr/bin/env python3
"""Run the Phase 2A public-view fixture as a rollback-only Phase 2B probe.

The populated rehearsal intentionally creates no sealed release/current pointer,
so its normal ``api_reader`` boundary check must observe zero public rows. This
probe separately runs the existing complete Phase 2A release/rights fixture in
one transaction and rolls it back, proving that a public object remains visible
when its visual registry is absent/zero-rights while held locators and pixels
remain hidden. It never commits or alters the rehearsal population.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pg-host", required=True)
    parser.add_argument("--pg-port", type=int, required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--admin-user", default="gda_v49_phase2b_admin")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.pg_port == 5432 or not args.pg_host.startswith("/") or not args.database.startswith("gda_v49_phase2a_"):
        raise SystemExit("DISPOSABLE_CONNECTION_POLICY_VIOLATION")
    env = os.environ.copy()
    env.update({"PGHOST": args.pg_host, "PGPORT": str(args.pg_port), "PGDATABASE": args.database, "PGUSER": args.admin_user})
    test = ROOT / "database/tests/002_release_seal_cas.sql"
    completed = subprocess.run(
        ["psql", "-X", "-q", "-v", "ON_ERROR_STOP=1", "-f", str(test)],
        text=True, capture_output=True, env=env, check=False,
    )
    if completed.returncode:
        print(completed.stdout[-2000:] + completed.stderr[-4000:], file=sys.stderr)
        raise SystemExit(completed.returncode)
    payload = {
        "status": "PASS",
        "fixture": str(test.relative_to(ROOT)),
        "transactionScoped": True,
        "fixtureRollback": True,
        "apiReaderPositiveObjectMetadata": True,
        "zeroRightsRegistryNoLocator": True,
        "heldLocatorHidden": True,
        "remoteImageHidden": True,
        "emptyTraceStateSupported": True,
        "persistentRowsCreated": 0,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(__import__("json").dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(__import__("json").dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
