#!/usr/bin/env python3
"""Build, verify, and deterministically archive the bounded TRACE handoff."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import sys
import tarfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HANDOFF_ROOT = ROOT / "docs/frontend/trace-v49-handoff"
TREE_PATH = HANDOFF_ROOT / "trace-function-tree.v1.json"
MANIFEST_PATH = HANDOFF_ROOT / "SOURCE_MANIFEST.json"
REPORT_PATH = HANDOFF_ROOT / "HANDOFF_INTEGRITY_REPORT.md"
CATALOG_PATH = ROOT / "docs/api/trace/trace-api-catalog.v1.json"

REQUIRED_HANDOFF_PATHS = [
    "START_HERE.md",
    "TRACE_FUNCTION_TREE.md",
    "trace-function-tree.v1.json",
    "FRONTEND_STATE_MATRIX.md",
    "OPEN_INQUIRY_UX_CONTRACT.md",
    "DATA_CONTRACTS_AND_EXAMPLES.md",
    "EXPORT_CONTRACT.md",
    "NAVIGATION_AND_CROSS_FUNCTION_STATE.md",
    "ACCESSIBILITY_AND_RESPONSIVE_CONSTRAINTS.md",
    "TERMINOLOGY_AND_UI_COPY.md",
    "KNOWN_LIMITATIONS_AND_OPEN_DESIGN_QUESTIONS.md",
    "SOURCE_MANIFEST.json",
    "HANDOFF_INTEGRITY_REPORT.md",
]

HANDOFF_SOURCE_FILES = [
    "START_HERE.md",
    "TRACE_FUNCTION_TREE.md",
    "FRONTEND_STATE_MATRIX.md",
    "OPEN_INQUIRY_UX_CONTRACT.md",
    "DATA_CONTRACTS_AND_EXAMPLES.md",
    "EXPORT_CONTRACT.md",
    "NAVIGATION_AND_CROSS_FUNCTION_STATE.md",
    "ACCESSIBILITY_AND_RESPONSIVE_CONSTRAINTS.md",
    "TERMINOLOGY_AND_UI_COPY.md",
    "KNOWN_LIMITATIONS_AND_OPEN_DESIGN_QUESTIONS.md",
]

SOURCE_PATHS = [
    ("docs/api/trace/trace-api-catalog.v1.json", "complete machine API catalog"),
    ("docs/api/trace/TRACE_API_CATALOG.md", "complete human API catalog"),
    ("frontend/src/app/api/v1/[...path]/route.ts", "Context, Spacetime, and shared read route"),
    ("frontend/src/features/trace-v49/context/governed/read-api-runtime.server.ts", "Context API handler"),
    ("frontend/src/features/trace-v49/context/governed/reader.server.ts", "Context governed reader"),
    ("frontend/src/features/trace-v49/context/governed/types.ts", "Context data contracts"),
    ("frontend/scripts/verify-context-api-v1.mjs", "Context API test"),
    ("frontend/src/features/trace-v49/spacetime/governed/read-api-runtime.server.ts", "Spacetime API handler"),
    ("frontend/src/features/trace-v49/spacetime/governed/reader.server.ts", "Spacetime governed reader"),
    ("frontend/src/features/trace-v49/spacetime/governed/types.ts", "Spacetime data contracts"),
    ("frontend/scripts/verify-spacetime-api-v1.mjs", "Spacetime API test"),
    ("frontend/src/app/api/trace/v1/exploration/route.ts", "retired Exploration v1 root"),
    ("frontend/src/app/api/trace/v1/exploration/[...path]/route.ts", "retired Exploration v1 catch-all"),
    ("frontend/src/app/api/trace/v2/exploration/route.ts", "Validated Exploration v2 root"),
    ("frontend/src/app/api/trace/v2/exploration/[...path]/route.ts", "Validated Exploration v2 resources"),
    ("frontend/src/features/trace-v49/exploration-v2/types.ts", "Validated Exploration v2 data contracts"),
    ("frontend/src/features/trace-v49/exploration-v2/controller.server.ts", "Validated Exploration v2 handler"),
    ("frontend/src/features/trace-v49/exploration-v2/service.server.ts", "Validated Exploration v2 service"),
    ("frontend/src/features/trace-v49/exploration-v2/read-model.server.ts", "Validated Exploration v2 read model"),
    ("frontend/src/features/trace-v49/exploration-v2/renderer.server.ts", "Validated Exploration SVG/PNG renderer"),
    ("frontend/src/features/trace-v49/exploration-v2/transition.server.ts", "Validated Exploration state transitions"),
    ("frontend/src/features/trace-v49/exploration-v2/client.ts", "Validated Exploration typed client"),
    ("frontend/generated/trace-exploration-v2/production-read-model.json", "Validated Exploration canonical product model"),
    ("frontend/scripts/test-trace-exploration-v2.mjs", "Validated Exploration v2 test"),
    ("frontend/scripts/validate-trace-exploration-v2-http.mjs", "Validated Exploration v2 HTTP test"),
    ("frontend/src/app/api/trace/v3/exploration/route.ts", "Exploration v3 fail-closed root"),
    ("frontend/src/app/api/trace/v3/exploration/[...path]/route.ts", "Exploration v3 collection resources"),
    ("frontend/src/features/trace-v49/exploration-v3/types.ts", "Exploration v3 data contracts"),
    ("frontend/src/features/trace-v49/exploration-v3/controller.server.ts", "Exploration v3 handler"),
    ("frontend/src/features/trace-v49/exploration-v3/service.server.ts", "Exploration v3 service"),
    ("frontend/src/features/trace-v49/exploration-v3/read-model.server.ts", "Exploration v3 read-model validator"),
    ("frontend/generated/trace-exploration-v3/read-model.json", "Exploration v3 fail-closed read model"),
    ("frontend/scripts/test-trace-exploration-v3.mjs", "Exploration v3 API test"),
    ("frontend/src/app/api/trace/v1/open-inquiry/route.ts", "Open Inquiry inventory route"),
    ("frontend/src/app/api/trace/v1/open-inquiry/[inquiryId]/route.ts", "Open Inquiry detail route"),
    ("frontend/src/features/trace-v49/open-inquiry-v1/types.ts", "Open Inquiry data contracts"),
    ("frontend/src/features/trace-v49/open-inquiry-v1/registry.server.ts", "Open Inquiry registry validator"),
    ("frontend/src/features/trace-v49/open-inquiry-v1/service.server.ts", "Open Inquiry service"),
    ("frontend/src/features/trace-v49/open-inquiry-v1/controller.server.ts", "Open Inquiry handler"),
    ("frontend/generated/trace-open-inquiry-v1/open-inquiry-registry.v1.json", "canonical Open Inquiry registry"),
    ("schemas/trace/exploration/open-inquiry/v1/registry.schema.json", "Open Inquiry registry schema"),
    ("schemas/trace/exploration/open-inquiry/v1/list-response.schema.json", "Open Inquiry list schema"),
    ("schemas/trace/exploration/open-inquiry/v1/detail-response.schema.json", "Open Inquiry detail schema"),
    ("schemas/trace/exploration/open-inquiry/v1/error.schema.json", "Open Inquiry error schema"),
    ("frontend/scripts/test-trace-open-inquiry-v1.mjs", "Open Inquiry API/isolation test"),
    ("frontend/src/lib/read-platform/server/read-api-controller.ts", "shared TRACE read handler"),
    ("frontend/src/lib/read-platform/repository.ts", "shared TRACE repository contract"),
    ("frontend/src/lib/read-platform/types.ts", "shared TRACE data contracts"),
    ("frontend/scripts/run-v49-api-read-contract-closure.mjs", "shared TRACE API test"),
]

CLOSURE_FLAGS = {
    "PAIR_ASSOCIATION_CLOSURE": False,
    "HIGHER_ORDER_ASSOCIATION_CLOSURE": False,
    "GLOBAL_COMPOSITION_COHERENCE_CLOSURE": False,
    "PRODUCT_ASSOCIATION_REACHABILITY_CLOSURE": False,
    "COMPUTATIONAL_SPACE_CLOSURE": False,
    "FUNCTION3_CLOSURE": False,
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def file_row(path: Path, role: str, relative: str) -> dict[str, Any]:
    data = path.read_bytes()
    return {"path": relative, "role": role, "bytes": len(data), "sha256": sha256(data), "required": True}


def build_tree() -> dict[str, Any]:
    return {
        "schema_version": "trace-function-tree/v1",
        "trace_top_level_function_count": 3,
        "functions": [
            {
                "function": "TRACE_FUNCTION_1",
                "name": "Context Canvas",
                "api_references": ["trace.f1.context.object-context.v1"],
                "children": ["selected public record", "governed context representations", "provenance and explanations"],
            },
            {
                "function": "TRACE_FUNCTION_2",
                "name": "Spacetime",
                "api_references": [
                    "trace.f2.spacetime.periods.v1",
                    "trace.f2.spacetime.atlas.v1",
                    "trace.f2.spacetime.geography-records.v1",
                ],
                "children": ["period inventory", "period atlas", "geography record pages"],
            },
            {
                "function": "TRACE_FUNCTION_3",
                "name": "Exploration",
                "api_references": [
                    "trace.f3.validated.v2.capabilities.get",
                    "trace.f3.open-inquiry.v1.list",
                    "trace.f3.open-inquiry.v1.detail",
                ],
                "children": [
                    {
                        "name": "Validated Exploration",
                        "children": [
                            "validated vocabulary and associations",
                            "composition and map state",
                            "plain-text tree",
                            "validated PNG export",
                        ],
                    },
                    {
                        "name": "Open Inquiry",
                        "children": [
                            "inquiry inventory",
                            "inquiry detail",
                            "evidence-incomplete disclosure",
                            "provenance access",
                            "no validated-layer contamination",
                        ],
                    },
                ],
            },
        ],
        "excluded_top_level_products": ["Search", "legacy Evidence Atlas"],
        "frontend_visual_design_implemented": False,
        "deployment_performed": False,
        "closure_flags": CLOSURE_FLAGS,
    }


def verify_tree_references(tree: dict[str, Any], catalog: dict[str, Any]) -> list[str]:
    catalog_ids = {record["api_id"] for record in catalog["routes"]}
    references = [api_id for function in tree["functions"] for api_id in function["api_references"]]
    return sorted(set(references) - catalog_ids)


def build_manifest(tree_bytes: bytes) -> dict[str, Any]:
    missing = [relative for relative, _ in SOURCE_PATHS if not (ROOT / relative).is_file()]
    if missing:
        raise ValueError("missing required source paths: " + ", ".join(missing))
    sources = [file_row(ROOT / relative, role, relative) for relative, role in SOURCE_PATHS]
    handoff_files = [
        file_row(HANDOFF_ROOT / name, "bounded handoff document", f"docs/frontend/trace-v49-handoff/{name}")
        for name in HANDOFF_SOURCE_FILES
    ]
    handoff_files.append(
        {
            "path": "docs/frontend/trace-v49-handoff/trace-function-tree.v1.json",
            "role": "canonical machine function tree",
            "bytes": len(tree_bytes),
            "sha256": sha256(tree_bytes),
            "required": True,
        }
    )
    return {
        "schema_version": "trace-frontend-handoff-source-manifest/v1",
        "handoff_version": "TRACE_V49_ROUND16B_FRONTEND_HANDOFF_V1",
        "bounded_instruction": "Do not scan the entire repository. Begin with this bounded handoff package. Expand to implementation source only through the paths listed in SOURCE_MANIFEST.json.",
        "trace_top_level_function_count": 3,
        "required_source_count": len(sources),
        "required_handoff_source_file_count": len(handoff_files),
        "sources_sha256": sha256(json.dumps(sources, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")),
        "handoff_files_sha256": sha256(json.dumps(handoff_files, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")),
        "sources": sources,
        "handoff_files": handoff_files,
        "catalog_binding": {
            "path": "docs/api/trace/trace-api-catalog.v1.json",
            "sha256": sha256(CATALOG_PATH.read_bytes()),
            "logical_route_template_count": 75,
            "expanded_method_route_pair_count": 228,
        },
        "closure_flags": CLOSURE_FLAGS,
        "external_human_review_status": "PENDING",
        "frontend_visual_design_implemented": False,
        "deployment_performed": False,
    }


def verify_manifest(manifest: dict[str, Any]) -> tuple[list[str], list[str]]:
    missing: list[str] = []
    mismatches: list[str] = []
    for row in manifest["sources"]:
        path = ROOT / row["path"]
        if not path.is_file():
            missing.append(row["path"])
            continue
        data = path.read_bytes()
        if len(data) != row["bytes"] or sha256(data) != row["sha256"]:
            mismatches.append(row["path"])
    return sorted(missing), sorted(mismatches)


def report_bytes(
    manifest: dict[str, Any],
    dangling: list[str],
    missing: list[str],
    mismatches: list[str],
) -> bytes:
    required_missing = [
        name
        for name in REQUIRED_HANDOFF_PATHS
        if name
        not in {
            "SOURCE_MANIFEST.json",
            "HANDOFF_INTEGRITY_REPORT.md",
            "trace-function-tree.v1.json",
        }
        and not (HANDOFF_ROOT / name).is_file()
    ]
    lines = [
        "# TRACE v49 frontend handoff integrity report",
        "",
        "The bounded handoff package is complete and is verified only against the source paths enumerated by `SOURCE_MANIFEST.json`. No whole-repository scan is required for frontend use.",
        "",
        "## Result",
        "",
        "`HANDOFF_INTEGRITY_STATUS=PASS`",
        "",
        "`TRACE_TOP_LEVEL_FUNCTION_COUNT=3`",
        "",
        f"`FUNCTION_TREE_DANGLING_API_REFERENCE_COUNT={len(dangling)}`",
        "",
        f"`HANDOFF_REQUIRED_DOCUMENT_MISSING_COUNT={len(required_missing)}`",
        "",
        f"`HANDOFF_REQUIRED_SOURCE_MISSING_COUNT={len(missing)}`",
        "",
        f"`HANDOFF_SOURCE_HASH_MISMATCH_COUNT={len(mismatches)}`",
        "",
        f"`HANDOFF_REQUIRED_SOURCE_COUNT={manifest['required_source_count']}`",
        "",
        f"`HANDOFF_BOUND_SOURCE_SET_SHA256={manifest['sources_sha256']}`",
        "",
        f"`HANDOFF_SOURCE_DOCUMENT_SET_SHA256={manifest['handoff_files_sha256']}`",
        "",
        "## Boundaries",
        "",
        "The package contains no frontend visual implementation, Search design, deployment action, stochastic inquiry display, or validated-layer contamination. Open Inquiry remains unresolved and external human review remains pending.",
        "",
        "```text",
        "PAIR_ASSOCIATION_CLOSURE=false",
        "HIGHER_ORDER_ASSOCIATION_CLOSURE=false",
        "GLOBAL_COMPOSITION_COHERENCE_CLOSURE=false",
        "PRODUCT_ASSOCIATION_REACHABILITY_CLOSURE=false",
        "COMPUTATIONAL_SPACE_CLOSURE=false",
        "FUNCTION3_CLOSURE=false",
        "```",
        "",
        "## Deterministic rebuild",
        "",
        "Run:",
        "",
        "```bash",
        "python3 docs/audits/v49-exploration-round16b-main-integration/build_frontend_handoff.py --check",
        "```",
        "",
        "An external deterministic archive may be produced with `--archive <external-path>`. The archive is intentionally not a repository file.",
        "",
    ]
    return "\n".join(lines).encode("utf-8")


def build_outputs() -> dict[Path, bytes]:
    tree = build_tree()
    tree_bytes = json_bytes(tree)
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    dangling = verify_tree_references(tree, catalog)
    manifest = build_manifest(tree_bytes)
    manifest_bytes = json_bytes(manifest)
    missing, mismatches = verify_manifest(manifest)
    report = report_bytes(manifest, dangling, missing, mismatches)
    if dangling or missing or mismatches:
        raise ValueError("handoff integrity failed")
    return {TREE_PATH: tree_bytes, MANIFEST_PATH: manifest_bytes, REPORT_PATH: report}


def write_archive(destination: Path) -> tuple[str, int]:
    if destination.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError("handoff archive must be external to the repository")
    memory = io.BytesIO()
    with tarfile.open(fileobj=memory, mode="w", format=tarfile.PAX_FORMAT) as archive:
        for source in sorted(HANDOFF_ROOT.iterdir(), key=lambda item: item.name):
            if not source.is_file():
                continue
            data = source.read_bytes()
            info = tarfile.TarInfo(name=f"trace-v49-handoff/{source.name}")
            info.size = len(data)
            info.mode = 0o644
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            info.mtime = 0
            archive.addfile(info, io.BytesIO(data))
    compressed = gzip.compress(memory.getvalue(), compresslevel=9, mtime=0)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(compressed)
    return sha256(compressed), len(compressed)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--archive", type=Path)
    args = parser.parse_args()
    outputs = build_outputs()
    if args.check:
        stale = [str(path.relative_to(ROOT)) for path, output in outputs.items() if not path.is_file() or path.read_bytes() != output]
        if stale:
            print("FAIL: stale handoff outputs: " + ", ".join(stale), file=sys.stderr)
            return 1
        required_missing = [name for name in REQUIRED_HANDOFF_PATHS if not (HANDOFF_ROOT / name).is_file()]
        if required_missing:
            print("FAIL: missing required handoff files: " + ", ".join(required_missing), file=sys.stderr)
            return 1
        print("PASS: bounded TRACE handoff / 3 functions / 0 dangling APIs / 0 missing sources / 0 hash mismatches")
    else:
        for path, output in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(output)
        print("PASS: wrote bounded TRACE handoff tree, source manifest, and integrity report")
    if args.archive:
        digest, size = write_archive(args.archive)
        print(f"PASS: archive={args.archive} bytes={size} sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
