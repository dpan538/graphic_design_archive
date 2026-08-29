#!/usr/bin/env python3
"""Verify the Round 16A repository and public-contract boundary.

This verifier is intentionally diagnostic only.  It does not invoke a test,
generator, package manager, build, server, or network client.  Its repository
operations are read-only.  By default the deterministic JSON receipt is
written to stdout; ``--output`` may additionally persist that one receipt.

Mutation counts use changed *path records* relative to SOURCE_SHA, not changed
lines.  A rename is one mutation record and is tested against both its old and
new path.  Untracked, non-ignored files are included.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Iterable


DEFAULT_SOURCE_SHA = "8de5d1dedffc6fd70d8b03cd63fdec74c0d40f6e"
SCHEMA_VERSION = "trace-round16a-repository-boundary-receipt/v1"
WITHHELD_SENTINEL = "source_locators_withheld_from_public_export"


def git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {detail}")
    return completed.stdout


def changed_records(repo: Path, source_sha: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    represented: set[str] = set()
    output = git(repo, "diff", "--name-status", "--find-renames", source_sha, "--")
    for line in output.splitlines():
        if not line:
            continue
        fields = line.split("\t")
        if len(fields) < 2:
            raise RuntimeError(f"unexpected git diff --name-status row: {line!r}")
        status = fields[0]
        paths = fields[1:]
        represented.update(paths)
        records.append({"status": status, "paths": paths})

    untracked = git(repo, "ls-files", "--others", "--exclude-standard", "-z")
    for path in sorted(item for item in untracked.split("\0") if item):
        if path not in represented:
            records.append({"status": "UNTRACKED", "paths": [path]})

    return sorted(records, key=lambda row: (tuple(row["paths"]), row["status"]))


def any_path(record: dict[str, Any], predicate: Callable[[str], bool]) -> bool:
    return any(predicate(path) for path in record["paths"])


def is_shared_v1_read_api(path: str) -> bool:
    return path.startswith("frontend/src/app/api/v1/") or path.startswith(
        "frontend/src/lib/read-platform/"
    )


def is_search_code(path: str) -> bool:
    return (
        path.startswith("frontend/src/features/search-v49/")
        or path.startswith("frontend/src/app/search/")
        or path == "frontend/src/components/archive/shell/search.tsx"
        or bool(
            re.fullmatch(
                r"frontend/scripts/(?:generate|benchmark|test)-search-v49\.mjs", path
            )
        )
        or bool(re.fullmatch(r"scripts/(?:search_seed|build_prefreeze_candidate_v\d+_search_sqlite)\.py", path))
    )


def is_search_schema(path: str) -> bool:
    return path.startswith("schemas/search/") or (
        path.startswith("database/") and "search" in path.lower()
    )


def is_search_api(path: str) -> bool:
    return is_shared_v1_read_api(path) or path.startswith(
        "frontend/src/features/search-v49/server/"
    )


def is_search_index(path: str) -> bool:
    return path.startswith("frontend/generated/search-v49/") or path.startswith(
        "data/derived/search-v49/"
    )


def is_context_code(path: str) -> bool:
    return (
        path.startswith("frontend/src/features/trace-v49/context/")
        or path.startswith("frontend/src/app/trace/context-canvas/")
        or bool(re.fullmatch(r"frontend/scripts/[^/]*context[^/]*\.mjs", path))
    )


def is_context_schema(path: str) -> bool:
    return path.startswith("schemas/trace/context/") or (
        path.startswith("database/") and "context" in path.lower()
    )


def is_context_api(path: str) -> bool:
    return is_shared_v1_read_api(path) or (
        path.startswith("frontend/src/features/trace-v49/context/")
        and ("/governed/" in path or path.endswith(".server.ts"))
    )


def is_context_index(path: str) -> bool:
    return path.startswith("frontend/generated/trace-context-v1/")


def is_spacetime_code(path: str) -> bool:
    return (
        path.startswith("frontend/src/features/trace-v49/spacetime/")
        or path.startswith("frontend/src/app/trace/spacetime/")
        or bool(re.fullmatch(r"frontend/scripts/[^/]*spacetime[^/]*\.mjs", path))
    )


def is_spacetime_schema(path: str) -> bool:
    return path.startswith("schemas/trace/spacetime/") or (
        path.startswith("database/") and "spacetime" in path.lower()
    )


def is_spacetime_api(path: str) -> bool:
    return is_shared_v1_read_api(path) or (
        path.startswith("frontend/src/features/trace-v49/spacetime/")
        and ("/governed/" in path or path.endswith(".server.ts"))
    )


def is_spacetime_index(path: str) -> bool:
    return path.startswith("frontend/generated/trace-spacetime-v1/")


PROTECTED_CLASSIFIERS: dict[str, Callable[[str], bool]] = {
    "SEARCH_CODE": is_search_code,
    "SEARCH_SCHEMA": is_search_schema,
    "SEARCH_API": is_search_api,
    "SEARCH_INDEX": is_search_index,
    "CONTEXT_CODE": is_context_code,
    "CONTEXT_SCHEMA": is_context_schema,
    "CONTEXT_API": is_context_api,
    "CONTEXT_INDEX": is_context_index,
    "SPACETIME_CODE": is_spacetime_code,
    "SPACETIME_SCHEMA": is_spacetime_schema,
    "SPACETIME_API": is_spacetime_api,
    "SPACETIME_INDEX": is_spacetime_index,
}


def mutation_receipt(records: list[dict[str, Any]]) -> tuple[dict[str, int], dict[str, Any]]:
    details: dict[str, list[dict[str, Any]]] = {}
    counts: dict[str, int] = {}
    for name, predicate in PROTECTED_CLASSIFIERS.items():
        selected = [record for record in records if any_path(record, predicate)]
        details[name] = selected
        counts[f"{name}_MUTATION_COUNT"] = len(selected)

    for domain in ("SEARCH", "CONTEXT", "SPACETIME"):
        selected_ids = {
            (record["status"], tuple(record["paths"]))
            for kind in ("CODE", "SCHEMA", "API", "INDEX")
            for record in details[f"{domain}_{kind}"]
        }
        counts[f"{domain}_MUTATION_COUNT"] = len(selected_ids)

    return counts, details


PUBLIC_RUNTIME_ROOTS = (
    "frontend/src/app/api/trace/v2/exploration",
    "frontend/src/features/trace-v49/exploration-v2",
)
PUBLIC_MODEL_ROOTS = ("frontend/generated/trace-exploration-v2",)
PUBLIC_SCHEMA_ROOTS = ("schemas/trace/exploration/v2",)
PUBLIC_DOC_GLOB = "trace-exploration-v2-*"


def public_v2_files(repo: Path) -> list[Path]:
    paths: set[Path] = set()
    for relative in (*PUBLIC_RUNTIME_ROOTS, *PUBLIC_MODEL_ROOTS, *PUBLIC_SCHEMA_ROOTS):
        root = repo / relative
        if root.is_file():
            paths.add(root)
        elif root.is_dir():
            paths.update(path for path in root.rglob("*") if path.is_file())
    api_docs = repo / "docs/api"
    if api_docs.is_dir():
        paths.update(path for path in api_docs.glob(PUBLIC_DOC_GLOB) if path.is_file())
    return sorted(paths, key=lambda path: path.relative_to(repo).as_posix())


FORBIDDEN_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "search_reference",
        re.compile(
            r"(?ix)(?:\bsearch[-_ ](?:v49|result|results|hit|hits|manifest|document|documents|dto|dtos|index)\b|"
            r"features[/\\]search-v49|(?:^|[/\\])search(?:[/\\]|$))"
        ),
    ),
    (
        "context_reference",
        re.compile(
            r"(?ix)(?:\bcontext[-_ ](?:canvas|id|ids|record|records|reference|references|dto|dtos|input|inputs)\b|"
            r"\btrace[-_]context\b|features[/\\]trace-v49[/\\]context|/trace/context(?:/|\b))"
        ),
    ),
    (
        "spacetime_reference",
        re.compile(r"(?ix)(?:\bspacetime(?:[-_ ](?:id|ids|record|records|reference|references|dto|dtos|input|inputs))?\b|\btrace[-_]spacetime\b)"),
    ),
    (
        "archive_object_id",
        re.compile(r"(?ix)\b(?:archive[-_ ]?object|object|record|surface)[-_ ](?:id|ids|urn|urns|identifier|identifiers)\b"),
    ),
    (
        "archive_object_title",
        re.compile(r"(?ix)\b(?:archive[-_ ]?object|object|record|surface)[-_ ](?:title|titles)\b"),
    ),
    (
        "record_link",
        re.compile(
            r"(?ix)\b(?:archive[-_ ]?object|object|record|surface|related[-_ ]?record)[-_ ]"
            r"(?:url|urls|link|links|href|detail[-_ ]?url)\b|\brelated[-_ ]?records?\b"
        ),
    ),
    ("thumbnail", re.compile(r"(?ix)\bthumbnail(?:[-_ ](?:url|urls|href))?\b")),
    (
        "held_data",
        re.compile(
            r"(?ix)\bheld[-_ ](?:data|object|objects|record|records|row|rows|count|layer)\b|"
            r"\bpublication[-_ ]layer\b.{0,40}\bheld\b"
        ),
    ),
    (
        "database_internal_reference",
        re.compile(
            r"(?ix)\b(?:folder[-_ ](?:id|ids|ref|refs|reference|references)|object[-_ ]folder|"
            r"database[-_ ]row[-_ ](?:id|ids|ref|refs|reference|references))\b"
        ),
    ),
    (
        "source_locator",
        re.compile(
            r"(?ix)\bsource[-_ ]locators?\b|\b(?:source|evidence)[-_ ](?:url|urls|doi|dois|locator|locators)\b|"
            r"https?://(?:dx\.)?doi\.org/"
        ),
    ),
    (
        "source_internal_reference",
        re.compile(r"(?ix)\bsource[-_ ](?:id|ids|ref|refs|reference|references)\b"),
    ),
)


def negative_contract_statement(value: str) -> bool:
    compact = " ".join(value.lower().split())
    return bool(
        re.search(
            r"\b(?:does|do|must|will|shall) not (?:contain|include|expose|return|publish|emit|use)\b|"
            r"\b(?:no|never|without|excluded)\b.{0,240}\b(?:search|context (?:id|record)|spacetime|"
            r"archive object|object (?:id|title)|record (?:link|url)|thumbnail|held data|source locator)\b|"
            r"\bsource locators? (?:are |is )?withheld\b",
            compact,
        )
    )


def has_safe_sentinel_contract(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if key == WITHHELD_SENTINEL and (
                child is True or (isinstance(child, dict) and child.get("const") is True)
            ):
                return True
            if has_safe_sentinel_contract(child):
                return True
    elif isinstance(value, list):
        return any(has_safe_sentinel_contract(child) for child in value)
    return False


def finding(
    relative: str,
    concept: str,
    token: str,
    location: str,
    excerpt: str,
    allowed: bool,
    allowance: str | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "path": relative,
        "location": location,
        "concept": concept,
        "token": token,
        "excerpt": " ".join(excerpt.split())[:240],
        "allowed": allowed,
    }
    if allowance is not None:
        row["allowance"] = allowance
    return row


def scan_json_file(repo: Path, path: Path) -> list[dict[str, Any]]:
    relative = path.relative_to(repo).as_posix()
    value = json.loads(path.read_text(encoding="utf-8"))
    safe_sentinel = has_safe_sentinel_contract(value)
    rows: list[dict[str, Any]] = []

    def walk(node: Any, parts: tuple[str, ...] = ()) -> None:
        if isinstance(node, dict):
            for key in sorted(node):
                child = node[key]
                location = "/" + "/".join((*parts, str(key)))
                if key == WITHHELD_SENTINEL:
                    allowed = child is True or (
                        isinstance(child, dict) and child.get("const") is True
                    )
                    rows.append(
                        finding(
                            relative,
                            "source_locator",
                            key,
                            location,
                            f"{key}={child!r}",
                            allowed,
                            "Exact negative boolean sentinel; it confirms locators are withheld and carries no locator value."
                            if allowed
                            else None,
                        )
                    )
                else:
                    rows.extend(scan_token(relative, key, location, key, False))
                walk(child, (*parts, str(key)))
        elif isinstance(node, list):
            for index, child in enumerate(node):
                walk(child, (*parts, str(index)))
        elif isinstance(node, str):
            location = "/" + "/".join(parts)
            if node == WITHHELD_SENTINEL and safe_sentinel:
                rows.append(
                    finding(
                        relative,
                        "source_locator",
                        node,
                        location,
                        node,
                        True,
                        "Schema required-list reference to the exact negative boolean sentinel whose property is const true.",
                    )
                )
            else:
                rows.extend(
                    scan_token(
                        relative,
                        node,
                        location,
                        node,
                        negative_contract_statement(node),
                    )
                )

    walk(value)
    return rows


def scan_token(
    relative: str,
    value: str,
    location: str,
    excerpt: str,
    negative_documentation: bool,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    masked = value.replace(WITHHELD_SENTINEL, "")
    for concept, pattern in FORBIDDEN_PATTERNS:
        for match in pattern.finditer(masked):
            allowed = relative.startswith("docs/api/") and negative_documentation
            rows.append(
                finding(
                    relative,
                    concept,
                    match.group(0),
                    location,
                    excerpt,
                    allowed,
                    "Public API documentation may name a forbidden concept only in an explicit non-exposure statement."
                    if allowed
                    else None,
                )
            )
    return rows


def scan_text_file(repo: Path, path: Path) -> list[dict[str, Any]]:
    relative = path.relative_to(repo).as_posix()
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    rows: list[dict[str, Any]] = []
    for index, line in enumerate(lines):
        if WITHHELD_SENTINEL in line:
            masked = line.replace(WITHHELD_SENTINEL, "")
            sentinel_is_true = bool(
                re.search(
                    rf"{re.escape(WITHHELD_SENTINEL)}[^\n]{{0,80}}(?:const\s*[:=]\s*true|[:=]\s*true|readonly[^;]*:\s*true)",
                    line,
                )
            )
            rows.append(
                finding(
                    relative,
                    "source_locator",
                    WITHHELD_SENTINEL,
                    f"line:{index + 1}",
                    line,
                    sentinel_is_true,
                    "Exact negative boolean sentinel; it confirms locators are withheld and carries no locator value."
                    if sentinel_is_true
                    else None,
                )
            )
        else:
            masked = line

        window = "\n".join(lines[max(0, index - 3) : min(len(lines), index + 4)])
        rows.extend(
            scan_token(
                relative,
                masked,
                f"line:{index + 1}",
                line,
                negative_contract_statement(window),
            )
        )
    return rows


def scan_public_v2(repo: Path) -> dict[str, Any]:
    files = public_v2_files(repo)
    findings: list[dict[str, Any]] = []
    decode_failures: list[dict[str, str]] = []
    for path in files:
        try:
            if path.suffix.lower() == ".json":
                findings.extend(scan_json_file(repo, path))
            else:
                findings.extend(scan_text_file(repo, path))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            decode_failures.append(
                {"path": path.relative_to(repo).as_posix(), "error": str(error)}
            )

    findings.sort(
        key=lambda row: (row["path"], row["location"], row["concept"], row["token"])
    )
    forbidden = [row for row in findings if not row["allowed"]]
    allowed = [row for row in findings if row["allowed"]]
    required = (
        "frontend/src/app/api/trace/v2/exploration/[...path]/route.ts",
        "frontend/generated/trace-exploration-v2/production-read-model.json",
        "schemas/trace/exploration/v2/common.schema.json",
        "schemas/trace/exploration/v2/production-read-model.schema.json",
        "docs/api/trace-exploration-v2-openapi.yaml",
        "docs/api/trace-exploration-v2-error-catalog.md",
        "docs/api/trace-exploration-v2-examples.json",
    )
    missing = [relative for relative in required if not (repo / relative).is_file()]
    concept_counts = {
        concept: sum(1 for row in forbidden if row["concept"] == concept)
        for concept, _ in FORBIDDEN_PATTERNS
    }
    return {
        "scanned_file_count": len(files),
        "scanned_files": [path.relative_to(repo).as_posix() for path in files],
        "required_public_file_missing_count": len(missing),
        "missing_required_public_files": missing,
        "decode_failure_count": len(decode_failures),
        "decode_failures": decode_failures,
        "forbidden_finding_count": len(forbidden),
        "forbidden_findings": forbidden,
        "allowed_negative_reference_count": len(allowed),
        "allowed_negative_references": allowed,
        "forbidden_concept_counts": concept_counts,
        "internal_audit_scope_allowances": [
            {
                "path_prefix": "docs/audits/v49-exploration-full-space-closure-round1/",
                "allowed_material": "database row, folder, evidence, and source locators",
                "reason": "Append-only internal audit evidence is not served by the public Exploration v2 route.",
            },
            {
                "path_prefix": "docs/research/trace-v49-exploration-full-space-closure-round1/",
                "allowed_material": "methodological discussion of excluded Search, Context, Spacetime, object, and held-data inputs",
                "reason": "Research authority and boundary documentation is not a public Exploration response surface.",
            },
            {
                "path_prefix": "scripts/trace_round16a/",
                "allowed_material": "internal census inputs, database references, and explicit forbidden-field assertions",
                "reason": "Build and verification scripts are not imported by the production v2 route.",
            },
            {
                "path_prefix": "frontend/scripts/*trace-exploration-v2*",
                "allowed_material": "negative exposure assertions and test-only expected failures",
                "reason": "Validation and benchmark drivers are not production route dependencies or response payloads.",
            },
        ],
    }


PAGE_PATTERN = re.compile(r"^frontend/src/app/(?:.+/)?page\.(?:ts|tsx|js|jsx)$")
NAVIGATION_PATHS = re.compile(
    r"^frontend/src/(?:app/(?:layout|page|trace/page)\.(?:ts|tsx|js|jsx)|components/archive/shell/)"
)
UI_SUFFIXES = {".css", ".jsx", ".scss", ".tsx"}


def target_paths(record: dict[str, Any]) -> list[str]:
    if record["status"].startswith("D"):
        return []
    if record["status"].startswith("R") and len(record["paths"]) > 1:
        return [record["paths"][-1]]
    return [record["paths"][-1]]


def frontend_boundary(repo: Path, records: list[dict[str, Any]]) -> dict[str, Any]:
    page_mutations = [record for record in records if any_path(record, lambda p: bool(PAGE_PATTERN.match(p)))]
    navigation_mutations = [
        record for record in records if any_path(record, lambda p: bool(NAVIGATION_PATHS.match(p)))
    ]
    added_pages: list[str] = []
    exploration_pages: list[str] = []
    ui_findings: list[dict[str, str]] = []

    for record in records:
        for relative in target_paths(record):
            path = repo / relative
            if record["status"] in {"A", "UNTRACKED"} and PAGE_PATTERN.match(relative):
                added_pages.append(relative)
            if not path.is_file():
                continue
            suffix = path.suffix.lower()
            if suffix not in UI_SUFFIXES and not PAGE_PATTERN.match(relative):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            lower = text.lower()
            page_is_exploration = PAGE_PATTERN.match(relative) and (
                "exploration" in relative.lower()
                or "trace-v49/exploration-v2" in lower
                or "/api/trace/v2/exploration" in lower
            )
            if record["status"] in {"A", "UNTRACKED"} and page_is_exploration:
                exploration_pages.append(relative)
            if (
                relative.startswith("frontend/src/features/trace-v49/exploration-v2/")
                and suffix in UI_SUFFIXES
            ):
                ui_findings.append(
                    {"path": relative, "reason": "Exploration v2 UI/style module was changed or added."}
                )
            if ("href" in lower or "navigation" in lower) and re.search(
                r"/trace/(?:exploration|explore)|/api/trace/v2/exploration", lower
            ):
                ui_findings.append(
                    {"path": relative, "reason": "Changed frontend source links to an Exploration route."}
                )

    def unique_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[tuple[str, tuple[str, ...]]] = set()
        result: list[dict[str, Any]] = []
        for row in rows:
            identity = (row["status"], tuple(row["paths"]))
            if identity not in seen:
                seen.add(identity)
                result.append(row)
        return result

    ui_findings = sorted(
        {json.dumps(row, sort_keys=True): row for row in ui_findings}.values(),
        key=lambda row: (row["path"], row["reason"]),
    )
    return {
        "frontend_page_mutation_count": len(unique_rows(page_mutations)),
        "frontend_page_mutations": unique_rows(page_mutations),
        "added_public_page_count": len(set(added_pages)),
        "added_public_pages": sorted(set(added_pages)),
        "public_exploration_page_added_count": len(set(exploration_pages)),
        "public_exploration_pages_added": sorted(set(exploration_pages)),
        "public_navigation_mutation_count": len(unique_rows(navigation_mutations)),
        "public_navigation_mutations": unique_rows(navigation_mutations),
        "exploration_frontend_ui_finding_count": len(ui_findings),
        "exploration_frontend_ui_findings": ui_findings,
    }


def build_receipt(repo: Path, source_sha: str) -> dict[str, Any]:
    source_sha = git(repo, "rev-parse", "--verify", f"{source_sha}^{{commit}}").strip()
    source_tree_sha = git(repo, "rev-parse", f"{source_sha}^{{tree}}").strip()
    head_sha = git(repo, "rev-parse", "HEAD").strip()
    records = changed_records(repo, source_sha)
    mutation_counts, mutation_details = mutation_receipt(records)
    public_scan = scan_public_v2(repo)
    frontend = frontend_boundary(repo, records)
    concepts = public_scan["forbidden_concept_counts"]

    archive_reference_count = sum(
        concepts[name]
        for name in (
            "archive_object_id",
            "archive_object_title",
            "record_link",
            "thumbnail",
        )
    )
    product_boundary_pass = (
        all(value == 0 for value in mutation_counts.values())
        and public_scan["required_public_file_missing_count"] == 0
        and public_scan["decode_failure_count"] == 0
        and public_scan["forbidden_finding_count"] == 0
        and frontend["frontend_page_mutation_count"] == 0
        and frontend["public_navigation_mutation_count"] == 0
        and frontend["public_exploration_page_added_count"] == 0
        and frontend["exploration_frontend_ui_finding_count"] == 0
    )

    flat: dict[str, Any] = {
        **mutation_counts,
        "SEARCH_STATUS": "OUT_OF_SCOPE_NOT_EVALUATED",
        "SEARCH_SEMANTIC_INPUT_COUNT": concepts["search_reference"],
        "SEARCH_RUNTIME_DEPENDENCY_COUNT": sum(
            1
            for row in public_scan["forbidden_findings"]
            if row["concept"] == "search_reference"
            and row["path"].startswith(PUBLIC_RUNTIME_ROOTS)
        ),
        "CONTEXT_SEMANTIC_INPUT_COUNT": concepts["context_reference"],
        "SPACETIME_SEMANTIC_INPUT_COUNT": concepts["spacetime_reference"],
        "CONTEXT_RUNTIME_DEPENDENCY_COUNT": sum(
            1
            for row in public_scan["forbidden_findings"]
            if row["concept"] == "context_reference"
            and row["path"].startswith(PUBLIC_RUNTIME_ROOTS)
        ),
        "SPACETIME_RUNTIME_DEPENDENCY_COUNT": sum(
            1
            for row in public_scan["forbidden_findings"]
            if row["concept"] == "spacetime_reference"
            and row["path"].startswith(PUBLIC_RUNTIME_ROOTS)
        ),
        "PUBLIC_EXPLORATION_SEARCH_REFERENCE_COUNT": concepts["search_reference"],
        "PUBLIC_EXPLORATION_CONTEXT_REFERENCE_COUNT": concepts["context_reference"],
        "PUBLIC_EXPLORATION_SPACETIME_REFERENCE_COUNT": concepts["spacetime_reference"],
        "PUBLIC_EXPLORATION_ARCHIVE_OBJECT_ID_COUNT": concepts["archive_object_id"],
        "PUBLIC_EXPLORATION_ARCHIVE_OBJECT_TITLE_COUNT": concepts["archive_object_title"],
        "PUBLIC_EXPLORATION_RECORD_LINK_COUNT": concepts["record_link"],
        "PUBLIC_EXPLORATION_THUMBNAIL_COUNT": concepts["thumbnail"],
        "PUBLIC_EXPLORATION_ARCHIVE_OBJECT_REFERENCE_COUNT": archive_reference_count,
        "PUBLIC_EXPLORATION_HELD_DATA_COUNT": concepts["held_data"],
        "PUBLIC_EXPLORATION_DATABASE_INTERNAL_REFERENCE_COUNT": concepts[
            "database_internal_reference"
        ],
        "PUBLIC_EXPLORATION_SOURCE_LOCATOR_COUNT": concepts["source_locator"],
        "PUBLIC_EXPLORATION_SOURCE_INTERNAL_REFERENCE_COUNT": concepts[
            "source_internal_reference"
        ],
        "PUBLIC_V2_FORBIDDEN_EXPOSURE_COUNT": public_scan["forbidden_finding_count"],
        "PUBLIC_V2_ALLOWED_NEGATIVE_REFERENCE_COUNT": public_scan[
            "allowed_negative_reference_count"
        ],
        "PUBLIC_EXPLORATION_PAGE_ADDED": frontend[
            "public_exploration_page_added_count"
        ]
        > 0,
        "PUBLIC_NAVIGATION_MUTATION_COUNT": frontend["public_navigation_mutation_count"],
        "FINAL_EXPLORATION_FRONTEND_IMPLEMENTED": frontend[
            "exploration_frontend_ui_finding_count"
        ]
        > 0,
        "PROJECT_FRONTEND_DESIGN_SAFE_TO_BEGIN": False,
        "REPOSITORY_BOUNDARY": "PASS" if product_boundary_pass else "FAIL",
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "source_sha": source_sha,
        "source_tree_sha": source_tree_sha,
        "head_sha": head_sha,
        "comparison_method": {
            "unit": "changed path record relative to source_sha",
            "rename_rule": "one record classified against old and new paths",
            "untracked_rule": "include non-ignored untracked paths",
            "test_execution_count": 0,
            "generator_execution_count": 0,
            "network_request_count": 0,
        },
        "worktree_change_record_count": len(records),
        "protected_mutation_counts": mutation_counts,
        "protected_mutation_details": mutation_details,
        "public_v2_contract_scan": public_scan,
        "frontend_boundary": frontend,
        "receipt": flat,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Repository worktree to inspect")
    parser.add_argument("--source-sha", default=DEFAULT_SOURCE_SHA)
    parser.add_argument(
        "--output",
        help="Optional JSON receipt path. Stdout is always emitted; no other file is written.",
    )
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    actual_root = Path(git(repo, "rev-parse", "--show-toplevel").strip()).resolve()
    if actual_root != repo:
        raise RuntimeError(f"--repo must be the worktree root: expected {actual_root}, got {repo}")

    receipt = build_receipt(repo, args.source_sha)
    rendered = json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        output = Path(args.output)
        if not output.is_absolute():
            output = repo / output
        output = output.resolve()
        if not output.parent.is_dir():
            raise RuntimeError(f"output parent does not exist: {output.parent}")
        output.write_text(rendered, encoding="utf-8")
    sys.stdout.write(rendered)
    return 0 if receipt["receipt"]["REPOSITORY_BOUNDARY"] == "PASS" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError) as error:
        print(f"REPOSITORY_BOUNDARY_VERIFIER_ERROR={error}", file=sys.stderr)
        raise SystemExit(2)
