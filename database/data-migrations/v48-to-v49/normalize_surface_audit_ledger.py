#!/usr/bin/env python3
"""Make the committed surface-ledger TSV whitespace-safe without hiding origin.

The staging source uses an empty final ``quarantine_id`` column, which is a
valid TSV but produces a trailing tab on every row and fails ``git diff
--check``.  This utility changes only empty final audit-copy values to the
explicit audit token ``NONE`` and records the original staging descriptor.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, NoReturn


class NormalizeError(RuntimeError):
    """A whitespace-safe audit ledger invariant failure."""


def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise NormalizeError(f"DUPLICATE_JSON_KEY:{key}")
        result[key] = value
    return result


def reject_constant(value: str) -> NoReturn:
    raise NormalizeError(f"UNSUPPORTED_JSON_CONSTANT:{value}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=strict_object, parse_constant=reject_constant)
    if not isinstance(value, dict):
        raise NormalizeError("JSON_NOT_OBJECT")
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--provenance", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ledger = args.ledger.resolve()
    provenance_path = args.provenance.resolve()
    receipt = args.receipt.resolve(strict=False)
    if not str(ledger).endswith("/docs/audits/v49-phase2b-migration/18_SURFACE_ROW_LEDGER.tsv") or receipt.exists():
        raise NormalizeError("AUDIT_TARGET_INVALID")
    with ledger.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle, delimiter="\t"))
    expected_header = ["source_ordinal", "json_pointer", "surface_id_exact", "source_record_id_exact", "record_semantic_sha256", "archive_object_uuid", "raw_record_uuid", "trace_root_legacy_id", "tier_presence", "tier_exact_value", "research_disposition", "workflow_reason", "import_disposition", "parse_error", "quarantine_id"]
    if not rows or rows[0] != expected_header or len(rows) != 15924 or any(len(row) != len(expected_header) for row in rows[1:]):
        raise NormalizeError("SURFACE_LEDGER_SHAPE_INVALID")
    provenance = read_json(provenance_path)
    copied = provenance.get("copiedLedgers")
    if not isinstance(copied, dict) or "18_SURFACE_ROW_LEDGER.tsv" not in copied:
        raise NormalizeError("SOURCE_DESCRIPTOR_MISSING")
    source_descriptor = copied.pop("18_SURFACE_ROW_LEDGER.tsv")
    original_bytes = ledger.stat().st_size
    original_sha = sha256_file(ledger)
    changed = 0
    for row in rows[1:]:
        if row[-1] == "":
            row[-1] = "NONE"
            changed += 1
    with ledger.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerows(rows)
    transformed = {"path": str(ledger), "bytes": ledger.stat().st_size, "sha256": sha256_file(ledger), "rows": len(rows) - 1, "quarantineIdEmptyValuesEncodedAs": "NONE", "convertedRows": changed}
    provenance["normalizedAuditLedgers"] = provenance.get("normalizedAuditLedgers", {})
    provenance["normalizedAuditLedgers"]["18_SURFACE_ROW_LEDGER.tsv"] = {"rawStagingDescriptor": source_descriptor, "rawAuditCopy": {"bytes": original_bytes, "sha256": original_sha}, "transformedAuditCopy": transformed}
    provenance_path.write_text(json.dumps(provenance, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    receipt.write_text("# Surface-row ledger normalization\n\nThe staging ledger's 15,923 empty final `quarantine_id` cells used trailing TSV tabs. To satisfy the repository whitespace gate, the committed audit copy encodes only those empty final cells as the explicit audit token `NONE`.\n\n```json\n" + json.dumps({"rawStagingDescriptor": source_descriptor, "rawAuditCopy": {"bytes": original_bytes, "sha256": original_sha}, "transformedAuditCopy": transformed}, sort_keys=True, indent=2) + "\n```\n\nAll source ordinals, identity fields, presence/tier fields, disposition fields, and nonempty values are unchanged. The raw descriptor remains bound to the retained staging cache.\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "convertedRows": changed, "sha256": transformed["sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (NormalizeError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)
