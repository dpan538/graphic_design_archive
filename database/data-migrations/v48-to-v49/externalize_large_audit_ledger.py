#!/usr/bin/env python3
"""Replace an oversized Git audit copy with verified cache provenance/sample."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, NoReturn


class ExternalizationError(RuntimeError):
    """A no-large-duplicate audit invariant failure."""


def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ExternalizationError(f"DUPLICATE_JSON_KEY:{key}")
        value[key] = item
    return value


def reject_constant(value: str) -> NoReturn:
    raise ExternalizationError(f"UNSUPPORTED_JSON_CONSTANT:{value}")


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=strict_object, parse_constant=reject_constant)
    if not isinstance(value, dict):
        raise ExternalizationError("JSON_NOT_OBJECT")
    return value


def stream_descriptor(path: Path) -> tuple[int, str, list[str], list[list[str]]]:
    digest = hashlib.sha256()
    with path.open("rb") as raw:
        while chunk := raw.read(1024 * 1024):
            digest.update(chunk)
    rows = 0
    header: list[str] | None = None
    samples: list[list[str]] = []
    tail: list[list[str]] = []
    wanted = {1, 2, 3, 4, 5, 100000, 200000, 300000, 400000, 500000, 600000, 700000, 800000, 900000, 1000000, 1100000, 1200000, 1300000}
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle, delimiter="\t")
        for index, row in enumerate(reader):
            if index == 0:
                header = row
                continue
            rows += 1
            if index in wanted:
                samples.append(row)
            tail.append(row)
            if len(tail) > 5:
                tail.pop(0)
    if header is None or not header or len(header) != len(set(header)):
        raise ExternalizationError("LEDGER_HEADER_INVALID")
    for row in tail:
        if row not in samples:
            samples.append(row)
    return rows, digest.hexdigest(), header, samples


def tsv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-ledger", type=Path, required=True)
    parser.add_argument("--cache-ledger", type=Path, required=True)
    parser.add_argument("--cache-manifest", type=Path, required=True)
    parser.add_argument("--audit-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    audit_ledger = args.audit_ledger.resolve()
    cache_ledger = args.cache_ledger.resolve()
    audit_dir = args.audit_dir.resolve()
    if not str(audit_ledger).endswith("/docs/audits/v49-phase2b-migration/22_ROOT_RECONCILIATION_LEDGER.tsv"):
        raise ExternalizationError("AUDIT_LEDGER_TARGET_INVALID")
    if not str(cache_ledger).startswith("/Users/jarlgiovanni/Library/Caches/gda_v49_phase2b/") or not cache_ledger.name == "root-reconciliation-ledger.tsv":
        raise ExternalizationError("CACHE_LEDGER_TARGET_INVALID")
    manifest = read_json(args.cache_manifest.resolve())
    descriptor = manifest.get("files", {}).get("root-reconciliation-ledger.tsv")
    if not isinstance(descriptor, dict):
        raise ExternalizationError("CACHE_LEDGER_DESCRIPTOR_MISSING")
    audit_rows, audit_sha, header, samples = stream_descriptor(audit_ledger)
    cache_rows, cache_sha, cache_header, _ = stream_descriptor(cache_ledger)
    if header != cache_header or audit_rows != cache_rows or audit_sha != cache_sha or audit_ledger.stat().st_size != cache_ledger.stat().st_size:
        raise ExternalizationError("AUDIT_CACHE_LEDGER_MISMATCH")
    if descriptor.get("bytes") != cache_ledger.stat().st_size or descriptor.get("sha256") != cache_sha:
        raise ExternalizationError("CACHE_MANIFEST_LEDGER_MISMATCH")
    sample_path = audit_dir / "22_ROOT_RECONCILIATION_LEDGER_SAMPLE.tsv"
    receipt_path = audit_dir / "22_ROOT_RECONCILIATION_LEDGER_PROVENANCE.md"
    evidence_path = audit_dir / "evidence" / "root-ledger-externalization.json"
    if sample_path.exists() or receipt_path.exists() or evidence_path.exists():
        raise ExternalizationError("EXTERNALIZATION_OUTPUT_EXISTS")
    tsv(sample_path, header, samples)
    payload = {
        "schema": "gda-v49-phase2b-externalized-ledger/v1",
        "status": "PASS",
        "sourceAuditCopy": str(audit_ledger),
        "cachePath": str(cache_ledger),
        "rows": audit_rows,
        "bytes": cache_ledger.stat().st_size,
        "sha256": cache_sha,
        "columns": header,
        "samplePath": str(sample_path),
        "sampleRows": len(samples),
        "regeneration": "Use the mapping-pinned extract.py with the frozen Candidate JSON only after separately authorized resume; do not regenerate during this performance-block checkpoint.",
    }
    receipt_path.write_text("# Root reconciliation ledger provenance\n\nThe full 1,317,982-row ledger is preserved only in the verified non-Git staging cache. It is intentionally not duplicated in this recovery branch.\n\n```json\n" + json.dumps(payload, sort_keys=True, indent=2) + "\n```\n\nThe committed sample preserves the header and deterministic first/periodic/tail rows; the cache descriptor above is the complete evidence commitment.\n", encoding="utf-8")
    evidence_path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    provenance_path = audit_dir / "STAGING_PROVENANCE.json"
    provenance = read_json(provenance_path)
    copied = provenance.get("copiedLedgers")
    if not isinstance(copied, dict) or "22_ROOT_RECONCILIATION_LEDGER.tsv" not in copied:
        raise ExternalizationError("STAGING_PROVENANCE_COPY_ENTRY_MISSING")
    copied.pop("22_ROOT_RECONCILIATION_LEDGER.tsv")
    provenance["externalizedLargeLedgers"] = {"22_ROOT_RECONCILIATION_LEDGER.tsv": payload}
    provenance_path.write_text(json.dumps(provenance, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    audit_ledger.unlink()
    if audit_ledger.exists():
        raise ExternalizationError("AUDIT_LEDGER_DELETE_FAILED")
    print(json.dumps({"status": "PASS", "rows": audit_rows, "sha256": cache_sha, "auditLedgerDeleted": True}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ExternalizationError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)
