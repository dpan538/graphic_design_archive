#!/usr/bin/env python3
"""Deterministic, network-free verifier for the Phase 1D runtime cleanup.

The verifier is intentionally read-only: it reads the worktree and Git objects,
emits one JSON receipt to stdout, and never writes a cache, report, database, or
generated asset.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any, Iterable


BASELINE = "f75ded85000749beb4735fbbddcce99e9395b0b2"
ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
PROTECTED_MAIN = Path("/Users/jarlgiovanni/Desktop/modern_GD_history")

EXPECTED_MAIN_HEAD = "7ef26d66b6ad671fdcc5e11bfa831699a39426bc"
EXPECTED_MAIN_TRACKED_FINGERPRINT = (
    "57ecff59270460a769b743781ecd09ca191b867201991a260785985689f6d568"
)
EXPECTED_MAIN_UNTRACKED_FINGERPRINT = (
    "c1c1c00968cadf25a549cd6776fe05676c1f7029dfa92759e26afea4adfc4730"
)
EXPECTED_QA_FINGERPRINT = (
    "287289be2f58cae02f8746290c37ebec8880cd1bf461f112a64733b1cb499220"
)

ARCHIVE_MOVES = {
    "frontend/scripts/probe-qwen35-runtime.mjs": (
        "archive/ai-rag-slm/qwen35-browser-local-probes/runners/"
        "probe-qwen35-runtime.mjs",
        6_372,
        "4c1cd1ca7e219d2a4ea4c0634474bda37bd1a3aa1985acf6cc9c18537300bda7",
    ),
    "frontend/scripts/probe-qwen35-generation.mjs": (
        "archive/ai-rag-slm/qwen35-browser-local-probes/runners/"
        "probe-qwen35-generation.mjs",
        14_078,
        "6beeae595eff4e200cca082557443393d3794f2d6f62b6590f901535c5965616",
    ),
    "frontend/scripts/probe-qwen35-rag-policy.js": (
        "archive/ai-rag-slm/qwen35-browser-local-probes/runners/"
        "probe-qwen35-rag-policy.js",
        5_046,
        "9951d67c86aab508ad378dbdde7c442f6d0ddefe89a070bbccffcd6e9e557f79",
    ),
    "generated/qwen35_runtime_probe_v0.json": (
        "archive/ai-rag-slm/qwen35-browser-local-probes/results/"
        "qwen35_runtime_probe_v0.json",
        3_572,
        "dfeaaca5aa1509b8c0f50a1cc15e66004d10e15f748a0b68fd3aaed924c1cdb6",
    ),
    "generated/qwen35_generation_probe_v0.json": (
        "archive/ai-rag-slm/qwen35-browser-local-probes/results/"
        "qwen35_generation_probe_v0.json",
        3_141,
        "1e11428a88e5c70445f6b0ee2733134d4f521eef36469a3c8a0bf05529853643",
    ),
    "generated/qwen35_rag_policy_probe_v0.json": (
        "archive/ai-rag-slm/qwen35-browser-local-probes/results/"
        "qwen35_rag_policy_probe_v0.json",
        25_321,
        "2d163202c5a6c281d069da938393fff71a3d71e1b6348c7d857016e804eec682",
    ),
    "generated/archive_assistant_primer_v0.json": (
        "archive/ai-rag-slm/qwen35-browser-local-probes/results/"
        "archive_assistant_primer_v0.json",
        1_272,
        "b189bca6593c83a674595665b415b0df749bd1364fee56c9850109552b564b06",
    ),
}

A4_HASHES = {
    "frontend/src/components/archive/layouts.tsx": (
        "033f631ba4b8dc5dbbb4f71eebae76fc5aa0616622d4f9cd67e90ac154269847"
    ),
    "frontend/src/components/archive/blocks.tsx": (
        "85e6bd377541baf2e1762cbb2a84d3c68294203dc639dd7cecdbb22907fb4a46"
    ),
    "frontend/src/components/archive/reader/LeafFrame.tsx": (
        "a7726ba872a556c121f8dff767f6e8eebfaf12f1cd1ccd9187183f9077f0cae9"
    ),
    "frontend/src/lib/paginate.ts": (
        "94f3e4522440ce90cabee54e972043f45aa6131f081a35e5ae1dd1b2be2a77c6"
    ),
}

REMOVED_RUNTIME_PATHS = {
    "frontend/src/app/api/archive-assistant-evidence/route.ts",
    "frontend/src/lib/assistant-memory.ts",
    "frontend/src/lib/assistant-retrieval.ts",
    "frontend/src/lib/qwen35-adapter.ts",
    *ARCHIVE_MOVES.keys(),
}

REQUIRED_CLEANUP_CHANGED_PATHS = {
    *ARCHIVE_MOVES.keys(),
    *(entry[0] for entry in ARCHIVE_MOVES.values()),
    "archive/ai-rag-slm/qwen35-browser-local-probes/README.md",
    "frontend/package-lock.json",
    "frontend/package.json",
    "frontend/src/app/api/archive-assistant-evidence/route.ts",
    "frontend/src/app/globals.css",
    "frontend/src/components/archive/reader/Reader.tsx",
    "frontend/src/components/archive/shell/ArchiveShell.tsx",
    "frontend/src/components/archive/shell/search.tsx",
    "frontend/src/lib/archive-data.ts",
    "frontend/src/lib/assistant-memory.ts",
    "frontend/src/lib/assistant-retrieval.ts",
    "frontend/src/lib/qwen35-adapter.ts",
    "docs/audits/v49-runtime-cleanup/agents/C1_AI_RUNTIME_RETIREMENT_RECEIPT.md",
    "docs/audits/v49-runtime-cleanup/agents/C2_ARCHIVE_BULK_QA_RECEIPT.md",
    "docs/qa/README.md",
    "docs/qa/SCREENSHOT_MANIFEST.schema.json",
    "scripts/verify_v49_runtime_cleanup.py",
}

OPTIONAL_CLEANUP_CHANGED_PATHS = {
    "docs/audits/v49-runtime-cleanup/agents/"
    "C3_INDEPENDENT_CLEANUP_VERIFIER_RECEIPT.md",
}

FROZEN_ASSETS = {
    "generated/public_surfaces_prefreeze_candidate_v48.json",
    "data/prefreeze_candidate_v48.sqlite",
    "generated/prefreeze_candidate_v48_transfer_manifest.json",
    "data/prefreeze_candidate_v48_transfer_manifest.csv",
    "frontend/public/data/trace-v48/manifest.json",
}


def run(
    args: list[str],
    *,
    cwd: Path = ROOT,
    text: bool = False,
    check: bool = True,
) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(
        args,
        cwd=cwd,
        check=check,
        capture_output=True,
        text=text,
    )


def git_bytes(*args: str, cwd: Path = ROOT) -> bytes:
    return run(["git", *args], cwd=cwd).stdout


def git_text(*args: str, cwd: Path = ROOT) -> str:
    return run(["git", *args], cwd=cwd, text=True).stdout


def baseline_bytes(path: str) -> bytes:
    return git_bytes("show", f"{BASELINE}:{path}")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def source_files() -> list[Path]:
    suffixes = {".ts", ".tsx", ".js", ".jsx", ".css", ".mjs", ".cjs"}
    return sorted(
        path
        for path in (FRONTEND / "src").rglob("*")
        if path.is_file() and path.suffix.lower() in suffixes
    )


def count_regex(pattern: str, texts: Iterable[str], flags: int = 0) -> int:
    regex = re.compile(pattern, flags)
    return sum(len(regex.findall(text)) for text in texts)


def main() -> int:
    checks: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}

    def record(
        check_id: str,
        passed: bool,
        observed: Any,
        expected: Any,
        detail: str = "",
    ) -> None:
        checks.append(
            {
                "id": check_id,
                "status": "PASS" if passed else "FAIL",
                "observed": observed,
                "expected": expected,
                "detail": detail,
            }
        )

    head = git_text("rev-parse", "HEAD").strip()
    record("baseline_head", head == BASELINE, head, BASELINE)

    production_paths = source_files()
    production_text_by_path = {
        str(path.relative_to(ROOT)): read_text(path) for path in production_paths
    }
    production_texts = list(production_text_by_path.values())

    qwen_runtime_imports = count_regex(
        r"(?:from\s+|import\s*\(|require\s*\()\s*['\"][^'\"]*"
        r"(?:qwen|@huggingface/transformers)[^'\"]*['\"]",
        production_texts,
        re.IGNORECASE,
    )
    model_runtime_imports = count_regex(
        r"(?:from\s+|import\s*\(|require\s*\()\s*['\"][^'\"]*"
        r"(?:@huggingface/transformers|onnxruntime|qwen|assistant-memory|"
        r"assistant-retrieval)[^'\"]*['\"]",
        production_texts,
        re.IGNORECASE,
    )
    assistant_event_refs = count_regex(
        r"archive:open-assistant", production_texts, re.IGNORECASE
    )
    assistant_route_refs = count_regex(
        r"archive-assistant-evidence", production_texts, re.IGNORECASE
    )
    assistant_lib_refs = count_regex(
        r"assistant-(?:memory|retrieval)|qwen35-adapter",
        production_texts,
        re.IGNORECASE,
    )
    assistant_css_refs = count_regex(
        r"btn-turn--assistant|assistant__(?:answer|body|citation|empty|error|"
        r"evidence|eyebrow|label|loading|memory|prompt|result|status)|"
        r"archive-assistant",
        production_texts,
        re.IGNORECASE,
    )
    assistant_reference_files = sum(
        1
        for text in production_texts
        if re.search(
            r"qwen|@huggingface/transformers|assistant-memory|"
            r"assistant-retrieval|archive-assistant-evidence|"
            r"archive:open-assistant|btn-turn--assistant|archive-assistant",
            text,
            re.IGNORECASE,
        )
    )
    assistant_route_files = sorted(
        str(path.relative_to(ROOT))
        for path in (FRONTEND / "src" / "app" / "api").rglob("route.*")
        if "assistant" in str(path).lower()
    )
    removed_runtime_present = sorted(
        path for path in REMOVED_RUNTIME_PATHS if (ROOT / path).exists()
    )

    metrics.update(
        {
            "QWEN_RUNTIME_IMPORTS": qwen_runtime_imports,
            "ACTIVE_ASSISTANT_ROUTES": len(assistant_route_files),
            "MODEL_RUNTIME_PRODUCTION_IMPORTS": model_runtime_imports,
            "ASSISTANT_EVENT_REFS": assistant_event_refs,
            "ASSISTANT_ROUTE_REFS": assistant_route_refs,
            "ASSISTANT_LIB_REFS": assistant_lib_refs,
            "ASSISTANT_CSS_REFS": assistant_css_refs,
            "ASSISTANT_RUNTIME_REFERENCE_FILES": assistant_reference_files,
            "REMOVED_RUNTIME_PATHS_PRESENT": len(removed_runtime_present),
        }
    )
    record("qwen_runtime_imports_zero", qwen_runtime_imports == 0, qwen_runtime_imports, 0)
    record(
        "active_assistant_routes_zero",
        not assistant_route_files,
        assistant_route_files,
        [],
    )
    record(
        "model_runtime_production_imports_zero",
        model_runtime_imports == 0,
        model_runtime_imports,
        0,
    )
    record("assistant_event_refs_zero", assistant_event_refs == 0, assistant_event_refs, 0)
    record("assistant_route_refs_zero", assistant_route_refs == 0, assistant_route_refs, 0)
    record("assistant_lib_refs_zero", assistant_lib_refs == 0, assistant_lib_refs, 0)
    record("assistant_css_refs_zero", assistant_css_refs == 0, assistant_css_refs, 0)
    record(
        "assistant_reference_files_zero",
        assistant_reference_files == 0,
        assistant_reference_files,
        0,
    )
    record(
        "removed_runtime_paths_absent",
        not removed_runtime_present,
        removed_runtime_present,
        [],
    )

    package = json.loads(read_text(FRONTEND / "package.json"))
    lock = json.loads(read_text(FRONTEND / "package-lock.json"))
    baseline_lock = json.loads(baseline_bytes("frontend/package-lock.json"))
    package_text = read_text(FRONTEND / "package.json")
    lock_text = read_text(FRONTEND / "package-lock.json")
    transformers_package_refs = package_text.count("@huggingface/transformers")
    transformers_lock_refs = lock_text.count("@huggingface/transformers")
    dependency_groups = (
        "dependencies",
        "devDependencies",
        "optionalDependencies",
        "peerDependencies",
    )
    lock_root = lock.get("packages", {}).get("", {})
    package_lock_parity = all(
        package.get(group, {}) == lock_root.get(group, {}) for group in dependency_groups
    )
    baseline_packages = baseline_lock.get("packages", {})
    current_packages = lock.get("packages", {})
    retained_identity_drift: list[dict[str, Any]] = []
    for package_path in sorted(set(baseline_packages) & set(current_packages)):
        before = baseline_packages[package_path]
        after = current_packages[package_path]
        changed = {
            field: {"before": before.get(field), "after": after.get(field)}
            for field in ("version", "resolved", "integrity")
            if before.get(field) != after.get(field)
        }
        if changed:
            retained_identity_drift.append(
                {"packagePath": package_path, "changed": changed}
            )
    node_modules_paths = [
        str(path.relative_to(ROOT))
        for path in (ROOT / "node_modules", FRONTEND / "node_modules")
        if path.exists()
    ]
    metrics.update(
        {
            "TRANSFORMERS_PACKAGE_REFS": transformers_package_refs,
            "TRANSFORMERS_LOCK_REFS": transformers_lock_refs,
            "PACKAGE_ROOT_LOCK_PARITY": package_lock_parity,
            "BASELINE_LOCK_PACKAGE_ENTRIES": len(baseline_packages),
            "CURRENT_LOCK_PACKAGE_ENTRIES": len(current_packages),
            "RETAINED_PACKAGE_IDENTITY_DRIFT": len(retained_identity_drift),
            "NODE_MODULES_PATHS_PRESENT": len(node_modules_paths),
        }
    )
    record(
        "transformers_package_refs_zero",
        transformers_package_refs == 0,
        transformers_package_refs,
        0,
    )
    record(
        "transformers_lock_refs_zero",
        transformers_lock_refs == 0,
        transformers_lock_refs,
        0,
    )
    record("package_root_lock_parity", package_lock_parity, package_lock_parity, True)
    record(
        "retained_package_identity_drift_zero",
        not retained_identity_drift,
        retained_identity_drift,
        [],
    )
    record("node_modules_absent", not node_modules_paths, node_modules_paths, [])

    search_component_path = (
        FRONTEND / "src" / "components" / "archive" / "shell" / "search.tsx"
    )
    search_client_path = FRONTEND / "src" / "lib" / "archive-search-client.ts"
    search_route_path = FRONTEND / "src" / "app" / "search" / "page.tsx"
    search_component = read_text(search_component_path)
    search_imports = len(
        re.findall(
            r"from\s+['\"]@/lib/archive-search-client['\"]", search_component
        )
    )
    search_calls = len(re.findall(r"searchArchiveSurfaces\s*\(\s*trimmed\s*,\s*30\s*\)", search_component))
    full_search_links = len(re.findall(r"href=\{`/search", search_component))
    full_search_labels = search_component.count("Open full archive + TRACE search")
    search_core_unchanged: dict[str, bool] = {}
    for path in (search_client_path, search_route_path):
        relative = str(path.relative_to(ROOT))
        search_core_unchanged[relative] = path.read_bytes() == baseline_bytes(relative)
    deterministic_search_preserved = all(
        (
            search_component_path.exists(),
            search_client_path.exists(),
            search_route_path.exists(),
            search_imports == 1,
            search_calls == 1,
            full_search_links == 1,
            full_search_labels == 1,
            all(search_core_unchanged.values()),
        )
    )
    metrics.update(
        {
            "SEARCH_CLIENT_IMPORTS": search_imports,
            "SEARCH_ARCHIVE_CALLS": search_calls,
            "FULL_SEARCH_ROUTE_LINKS": full_search_links,
            "FULL_SEARCH_ROUTE_LABELS": full_search_labels,
            "DETERMINISTIC_SEARCH_PRESERVED": deterministic_search_preserved,
        }
    )
    record(
        "deterministic_search_contract",
        deterministic_search_preserved,
        {
            "componentExists": search_component_path.exists(),
            "clientExists": search_client_path.exists(),
            "routeExists": search_route_path.exists(),
            "imports": search_imports,
            "calls": search_calls,
            "links": full_search_links,
            "labels": full_search_labels,
            "coreFilesUnchanged": search_core_unchanged,
        },
        {
            "componentExists": True,
            "clientExists": True,
            "routeExists": True,
            "imports": 1,
            "calls": 1,
            "links": 1,
            "labels": 1,
            "coreFilesUnchanged": "all true",
        },
    )

    all_source_text = "\n".join(production_texts)
    dormant_bulk_refs = len(re.findall(r"\b(?:allFolderParams|allSurfaceParams)\b", all_source_text))
    archive_data_text = read_text(FRONTEND / "src" / "lib" / "archive-data.ts")
    folder_route_text = read_text(
        FRONTEND / "src" / "app" / "folders" / "[type]" / "page.tsx"
    )
    folder_type_definitions = len(
        re.findall(r"export\s+function\s+allFolderTypeParams\s*\(", archive_data_text)
    )
    folder_type_imports = len(
        re.findall(r"\ballFolderTypeParams\b", folder_route_text)
    )
    folder_type_calls = len(re.findall(r"allFolderTypeParams\s*\(\s*\)", folder_route_text))
    active_low_cardinality_generator = bool(
        re.search(r"export\s+function\s+generateStaticParams\s*\(", folder_route_text)
        and folder_type_calls == 1
    )
    metrics.update(
        {
            "DORMANT_BULK_ROUTE_GENERATORS": dormant_bulk_refs,
            "ALL_FOLDER_TYPE_DEFINITIONS": folder_type_definitions,
            "ALL_FOLDER_TYPE_ROUTE_REFS": folder_type_imports,
            "ALL_FOLDER_TYPE_CALLS": folder_type_calls,
            "LOW_CARDINALITY_GENERATOR_PRESERVED": active_low_cardinality_generator,
        }
    )
    record("dormant_bulk_helpers_absent", dormant_bulk_refs == 0, dormant_bulk_refs, 0)
    record(
        "low_cardinality_folder_generator_preserved",
        folder_type_definitions == 1
        and folder_type_imports == 2
        and folder_type_calls == 1
        and active_low_cardinality_generator,
        {
            "definitions": folder_type_definitions,
            "routeRefs": folder_type_imports,
            "calls": folder_type_calls,
            "generateStaticParams": active_low_cardinality_generator,
        },
        {"definitions": 1, "routeRefs": 2, "calls": 1, "generateStaticParams": True},
    )

    a4_observed: dict[str, dict[str, Any]] = {}
    for relative, expected_hash in A4_HASHES.items():
        current = (ROOT / relative).read_bytes()
        baseline = baseline_bytes(relative)
        current_hash = sha256(current)
        a4_observed[relative] = {
            "sha256": current_hash,
            "expectedSha256": expected_hash,
            "matchesBaseline": current == baseline,
        }
    a4_preserved = all(
        row["sha256"] == row["expectedSha256"] and row["matchesBaseline"]
        for row in a4_observed.values()
    )
    metrics["A4_VISUAL_COMPONENTS_PRESERVED"] = a4_preserved
    record("a4_exact_hashes_preserved", a4_preserved, a4_observed, "all exact")

    archive_observed: dict[str, dict[str, Any]] = {}
    archive_matches = 0
    archived_json_valid = 0
    for original, (archived, expected_bytes, expected_hash) in ARCHIVE_MOVES.items():
        current = (ROOT / archived).read_bytes()
        baseline = baseline_bytes(original)
        current_hash = sha256(current)
        matches = (
            current == baseline
            and len(current) == expected_bytes
            and current_hash == expected_hash
        )
        if matches:
            archive_matches += 1
        if archived.endswith(".json"):
            json.loads(current)
            archived_json_valid += 1
        archive_observed[archived] = {
            "original": original,
            "bytes": len(current),
            "sha256": current_hash,
            "matchesOriginalBaseline": current == baseline,
            "matchesReceipt": matches,
        }
    production_plus_manifests = production_texts + [package_text, lock_text]
    archived_production_refs = sum(
        count_regex(re.escape(Path(archived).name), production_plus_manifests)
        for archived, _, _ in ARCHIVE_MOVES.values()
    )
    archive_readme = read_text(
        ROOT / "archive" / "ai-rag-slm" / "qwen35-browser-local-probes" / "README.md"
    ).lower()
    archive_boundary_phrases = {
        "historical research only": "historical research only" in archive_readme,
        "non-authoritative": "non-authoritative" in archive_readme,
        "not imported by production": "not imported by production" in archive_readme,
        "not part of v49 data platform": (
            "not part of the v49 data platform" in archive_readme
        ),
    }
    metrics.update(
        {
            "ARCHIVED_PROBE_FILE_COUNT": len(ARCHIVE_MOVES),
            "ARCHIVED_PROBE_BASELINE_MATCHES": archive_matches,
            "ARCHIVED_JSON_VALID": archived_json_valid,
            "ARCHIVED_PROBE_PRODUCTION_IMPORTS": archived_production_refs,
            "ARCHIVE_README_BOUNDARIES": sum(archive_boundary_phrases.values()),
        }
    )
    record(
        "archive_bytes_and_hashes_match_originals",
        archive_matches == len(ARCHIVE_MOVES),
        archive_observed,
        "7 exact baseline matches",
    )
    record(
        "archive_production_imports_zero",
        archived_production_refs == 0,
        archived_production_refs,
        0,
    )
    record(
        "archive_readme_boundaries_declared",
        all(archive_boundary_phrases.values()),
        archive_boundary_phrases,
        "all true",
    )
    record("archived_json_valid", archived_json_valid == 4, archived_json_valid, 4)

    qa_paths = sorted(
        path
        for path in git_text("ls-files", "docs/qa/screenshots").splitlines()
        if path
    )
    qa_filesystem_paths = sorted(
        str(path.relative_to(ROOT))
        for path in (ROOT / "docs" / "qa" / "screenshots").rglob("*")
        if path.is_file()
    )
    qa_fingerprint_hasher = hashlib.sha256()
    for relative in qa_paths:
        file_hash = sha256((ROOT / relative).read_bytes())
        qa_fingerprint_hasher.update(f"{file_hash}  {relative}\n".encode("utf-8"))
    qa_fingerprint = qa_fingerprint_hasher.hexdigest()
    qa_diff = run(
        ["git", "diff", "--quiet", BASELINE, "--", "docs/qa/screenshots"],
        check=False,
    )
    schema_path = ROOT / "docs" / "qa" / "SCREENSHOT_MANIFEST.schema.json"
    qa_schema = json.loads(read_text(schema_path))
    top_required = {
        "schemaVersion",
        "captureSetId",
        "researchReleaseId",
        "researchManifestSha256",
        "visualRegistry",
        "generatedAt",
        "entries",
    }
    entry_required = {
        "evidenceId",
        "path",
        "sha256",
        "bytes",
        "fileExtension",
        "actualMimeType",
        "width",
        "height",
        "rightsProvenance",
        "oracle",
        "interactionCoverage",
        "accessibility",
    }
    rights_required = {"pixelOrigin", "evidenceLocator", "effectiveDisposition"}
    oracle_required = {"oracleId", "oracleVersion", "expected", "observed", "status"}
    accessibility_required = {
        "keyboard",
        "screenReader",
        "reducedMotion",
        "contrast",
        "touchTargets",
    }
    interaction_expected = {
        "KEYBOARD",
        "SCREEN_READER",
        "REDUCED_MOTION",
        "TOUCH",
        "SWIPE",
        "SCROLL",
        "SOURCE_DRAWER",
        "SEARCH",
        "MAP",
        "ERROR_STATE",
    }
    evidence = qa_schema.get("$defs", {}).get("evidenceEntry", {})
    evidence_properties = evidence.get("properties", {})
    schema_required_observed = {
        "top": set(qa_schema.get("required", [])),
        "entry": set(evidence.get("required", [])),
        "rights": set(
            evidence_properties.get("rightsProvenance", {}).get("required", [])
        ),
        "oracle": set(evidence_properties.get("oracle", {}).get("required", [])),
        "accessibility": set(
            evidence_properties.get("accessibility", {}).get("required", [])
        ),
        "interaction": set(
            evidence_properties.get("interactionCoverage", {})
            .get("items", {})
            .get("enum", [])
        ),
    }
    schema_required_ok = (
        top_required <= schema_required_observed["top"]
        and entry_required <= schema_required_observed["entry"]
        and rights_required <= schema_required_observed["rights"]
        and oracle_required <= schema_required_observed["oracle"]
        and accessibility_required <= schema_required_observed["accessibility"]
        and interaction_expected <= schema_required_observed["interaction"]
        and qa_schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema"
    )
    qa_readme = read_text(ROOT / "docs" / "qa" / "README.md")
    qa_readme_ok = (
        "contains 60 tracked legacy QA files" in qa_readme
        and EXPECTED_QA_FINGERPRINT in qa_readme
        and "does not promote them" in qa_readme
    )
    metrics.update(
        {
            "QA_TRACKED_SCREENSHOTS": len(qa_paths),
            "QA_FILESYSTEM_SCREENSHOTS": len(qa_filesystem_paths),
            "QA_PATH_CONTENT_FINGERPRINT": qa_fingerprint,
            "QA_IMAGE_DIFF": qa_diff.returncode,
            "QA_SCHEMA_REQUIRED_FIELDS_PRESENT": schema_required_ok,
            "QA_README_GOVERNANCE_PRESENT": qa_readme_ok,
        }
    )
    record("qa_tracked_count", len(qa_paths) == 60, len(qa_paths), 60)
    record(
        "qa_filesystem_matches_tracked",
        qa_filesystem_paths == qa_paths,
        {"filesystem": len(qa_filesystem_paths), "tracked": len(qa_paths)},
        {"filesystem": 60, "tracked": 60},
    )
    record(
        "qa_path_content_fingerprint",
        qa_fingerprint == EXPECTED_QA_FINGERPRINT,
        qa_fingerprint,
        EXPECTED_QA_FINGERPRINT,
    )
    record("qa_images_unchanged_from_baseline", qa_diff.returncode == 0, qa_diff.returncode, 0)
    record(
        "qa_schema_required_fields",
        schema_required_ok,
        {key: sorted(value) for key, value in schema_required_observed.items()},
        "all required field sets present",
    )
    record("qa_readme_governance", qa_readme_ok, qa_readme_ok, True)

    ds_store_exists = (ROOT / "docs" / ".DS_Store").exists()
    metrics["DOCS_DS_STORE_PRESENT"] = ds_store_exists
    record("approved_ds_store_absent", not ds_store_exists, ds_store_exists, False)

    tracked_diff_paths = set(
        path
        for path in git_text(
            "diff", "--name-only", "--no-renames", BASELINE, "--"
        ).splitlines()
        if path
    )
    untracked_paths = set(
        path
        for path in git_text("ls-files", "--others", "--exclude-standard").splitlines()
        if path
    )
    changed_paths = tracked_diff_paths | untracked_paths
    allowlist = REQUIRED_CLEANUP_CHANGED_PATHS | OPTIONAL_CLEANUP_CHANGED_PATHS
    unexpected_paths = sorted(changed_paths - allowlist)
    required_missing = sorted(REQUIRED_CLEANUP_CHANGED_PATHS - changed_paths)
    forbidden_diff_paths = sorted(
        path
        for path in changed_paths
        if path in FROZEN_ASSETS
        or path.startswith("data/")
        or path.startswith("frontend/public/data/")
        or path.startswith("docs/qa/screenshots/")
        or (
            path.startswith("generated/")
            and path not in ARCHIVE_MOVES
        )
        or "node_modules/" in path
    )
    frozen_diff = run(
        ["git", "diff", "--quiet", BASELINE, "--", *sorted(FROZEN_ASSETS)],
        check=False,
    )
    metrics.update(
        {
            "CLEANUP_CHANGED_PATHS": len(changed_paths),
            "CLEANUP_UNEXPECTED_PATHS": len(unexpected_paths),
            "CLEANUP_REQUIRED_PATHS_MISSING": len(required_missing),
            "FORBIDDEN_DATA_OR_QA_DIFF_PATHS": len(forbidden_diff_paths),
            "FROZEN_ASSET_DIFF": frozen_diff.returncode,
        }
    )
    record("cleanup_changed_file_allowlist", not unexpected_paths, unexpected_paths, [])
    record("cleanup_required_files_present", not required_missing, required_missing, [])
    record("forbidden_data_search_trace_qa_diff_zero", not forbidden_diff_paths, forbidden_diff_paths, [])
    record("frozen_assets_unchanged_from_baseline", frozen_diff.returncode == 0, frozen_diff.returncode, 0)

    current_json_paths = sorted(
        path for path in changed_paths if path.endswith(".json") and (ROOT / path).is_file()
    )
    json_parse_failures: dict[str, str] = {}
    for relative in current_json_paths:
        try:
            json.loads(read_text(ROOT / relative))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            json_parse_failures[relative] = str(exc)
    metrics["CHANGED_JSON_FILES_PARSED"] = len(current_json_paths)
    metrics["CHANGED_JSON_PARSE_FAILURES"] = len(json_parse_failures)
    record("changed_json_parse", not json_parse_failures, json_parse_failures, {})

    diff_check = run(["git", "diff", "--check", BASELINE, "--"], check=False, text=True)
    metrics["GIT_DIFF_CHECK"] = diff_check.returncode
    record(
        "git_diff_check",
        diff_check.returncode == 0,
        diff_check.stdout.strip(),
        "",
    )

    main_head = git_text("rev-parse", "HEAD", cwd=PROTECTED_MAIN).strip()
    main_tracked = git_bytes(
        "diff", "--name-status", "--no-renames", cwd=PROTECTED_MAIN
    )
    main_untracked = git_bytes(
        "ls-files", "--others", "--exclude-standard", cwd=PROTECTED_MAIN
    )
    main_staged = git_text("diff", "--cached", "--name-only", cwd=PROTECTED_MAIN).splitlines()
    main_tracked_fingerprint = sha256(main_tracked)
    main_untracked_fingerprint = sha256(main_untracked)
    protected_main_ok = (
        main_head == EXPECTED_MAIN_HEAD
        and main_tracked_fingerprint == EXPECTED_MAIN_TRACKED_FINGERPRINT
        and main_untracked_fingerprint == EXPECTED_MAIN_UNTRACKED_FINGERPRINT
        and not main_staged
    )
    metrics.update(
        {
            "PROTECTED_MAIN_HEAD": main_head,
            "PROTECTED_MAIN_TRACKED_FINGERPRINT": main_tracked_fingerprint,
            "PROTECTED_MAIN_TRACKED_PATHS": len(main_tracked.splitlines()),
            "PROTECTED_MAIN_UNTRACKED_FINGERPRINT": main_untracked_fingerprint,
            "PROTECTED_MAIN_UNTRACKED_PATHS": len(main_untracked.splitlines()),
            "PROTECTED_MAIN_STAGED_PATHS": len(main_staged),
        }
    )
    record(
        "protected_main_exact_baseline",
        protected_main_ok,
        {
            "head": main_head,
            "trackedFingerprint": main_tracked_fingerprint,
            "trackedPaths": len(main_tracked.splitlines()),
            "untrackedFingerprint": main_untracked_fingerprint,
            "untrackedPaths": len(main_untracked.splitlines()),
            "stagedPaths": len(main_staged),
        },
        {
            "head": EXPECTED_MAIN_HEAD,
            "trackedFingerprint": EXPECTED_MAIN_TRACKED_FINGERPRINT,
            "trackedPaths": 59,
            "untrackedFingerprint": EXPECTED_MAIN_UNTRACKED_FINGERPRINT,
            "untrackedPaths": 10_937,
            "stagedPaths": 0,
        },
    )

    local_tsc = FRONTEND / "node_modules" / ".bin" / "tsc"
    system_tsc = shutil.which("tsc")
    tsc_available = local_tsc.is_file() or system_tsc is not None
    metrics["TSC_AVAILABLE"] = tsc_available
    metrics["TSC_NOT_RUN"] = (
        "independent_static_verifier_scope" if tsc_available else "toolchain_absent"
    )

    residual_patterns = re.compile(
        r"(?:npm|next(?:\.js)?|tsc|typescript|playwright|puppeteer|"
        r"chrom(?:e|ium)|qwen|huggingface|data[-_ ]?(?:generator|export))",
        re.IGNORECASE,
    )
    task_residuals: list[str] = []
    process_scan_status = "IN_PROCESS_PASS"
    try:
        process_scan = run(
            ["ps", "-axo", "pid=,ppid=,etime=,command="], text=True
        ).stdout.splitlines()
        for line in process_scan:
            stripped = line.strip()
            if not stripped:
                continue
            first = stripped.split(maxsplit=1)[0]
            try:
                pid = int(first)
            except ValueError:
                continue
            if pid == os.getpid():
                continue
            if str(ROOT) in stripped and residual_patterns.search(stripped):
                task_residuals.append(stripped)
    except PermissionError:
        # Managed sandboxes may deny ps from a child process even when the
        # controller can run the same sanitized read-only scan. Do not invent a
        # zero: require the external process receipt instead.
        process_scan_status = "EXTERNAL_REQUIRED"
    metrics["PROCESS_SCAN"] = process_scan_status
    metrics["TASK_OWNED_RESIDUAL_PROCESSES"] = (
        len(task_residuals) if process_scan_status == "IN_PROCESS_PASS" else None
    )
    record(
        "task_owned_residual_process_boundary",
        not task_residuals,
        {
            "processScan": process_scan_status,
            "taskOwnedResiduals": (
                len(task_residuals)
                if process_scan_status == "IN_PROCESS_PASS"
                else "EXTERNAL_REQUIRED"
            ),
        },
        {"taskOwnedResiduals": 0},
        "EXTERNAL_REQUIRED must be closed by the controller's sanitized ps receipt.",
    )

    failures = [check for check in checks if check["status"] == "FAIL"]
    report = {
        "schema": "v49-runtime-cleanup-verifier/v1",
        "baselineCommit": BASELINE,
        "worktree": str(ROOT),
        "verifierMode": "read-only-network-free-stdout-only",
        "status": "PASS" if not failures else "FAIL",
        "checksPassed": len(checks) - len(failures),
        "checksFailed": len(failures),
        "metrics": metrics,
        "checks": checks,
        "actionsExplicitlyNotPerformed": [
            "npm or dependency installation",
            "Next dev/build/start",
            "TypeScript compilation",
            "browser automation or screenshots",
            "network access",
            "database access, data export, or generation",
            "file mutation, staging, commit, push, merge, PR, or deployment",
        ],
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # Keep the verifier's only channel as stdout.
        print(
            json.dumps(
                {
                    "schema": "v49-runtime-cleanup-verifier/v1",
                    "status": "ERROR",
                    "errorType": type(exc).__name__,
                    "error": str(exc),
                },
                indent=2,
                sort_keys=True,
            )
        )
        raise SystemExit(2)
