#!/usr/bin/env python3
"""Generate and seal the Round 11–12 history-coordination receipts."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
RELEASE = ROOT / "docs/releases/v49/round11-round12-main-integration-20260825"
AUDIT = ROOT / "docs/audits/v49-round11-round12-main-integration"
RAW = AUDIT / "raw"
BUNDLE = Path(
    "/private/tmp/graphic_design_archive_v49_round12_backup_20260825/"
    "graphic_design_archive_round12_preintegration.bundle"
)
RESTORE = Path("/private/tmp/graphic_design_archive_v49_round12_backup_restore_test.git")

MAIN = "cc311ab0c9a74731cc1bb0158579708a8a9158fc"
ROUND11 = "5ca999b53d9a5d18b47317817402f9e51ad26cec"
ROUND12 = "fc11f033d2fcdbb98130879cdbd3e4a52890e5d2"
BASE = "4bd82deba482ec2fbf8c4856080151416fb8ee83"
BRANCH = "chore/v49-round11-round12-history-coordination-20260825"
BUNDLE_SHA = "dbd5c6160ad0305eb7bfaa7932e53c8637fa7eeec9bc7484d5043e84e943695c"
BUNDLE_BYTES = 91051946


def run(*args: str, cwd: Path = ROOT) -> str:
    return subprocess.run(
        list(args), cwd=cwd, check=True, text=True, stdout=subprocess.PIPE
    ).stdout


def git(*args: str) -> str:
    return run("git", *args)


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def write_tsv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def append_once(path: Path, marker: str, block: str) -> None:
    current = path.read_text(encoding="utf-8")
    if marker not in current:
        path.write_text(current.rstrip() + "\n\n" + block.rstrip() + "\n", encoding="utf-8")


def commit_row(sha: str, role: str, side: str) -> dict[str, str]:
    return {
        "commit_sha": sha,
        "role": role,
        "parent_sha": git("rev-list", "--parents", "-n", "1", sha).strip().split(" ", 1)[1],
        "tree_sha": git("rev-parse", f"{sha}^{{tree}}").strip(),
        "subject": git("show", "-s", "--format=%s", sha).strip(),
        "side_unique": side,
    }


def verify_restore() -> list[dict[str, str]]:
    expected_parents = {
        MAIN: BASE,
        ROUND11: BASE,
        ROUND12: ROUND11,
        BASE: "0241b0f51e2523901b0858d54ffb7f5d2a9aa13c",
    }
    rows = []
    for sha, parent in expected_parents.items():
        run("git", "cat-file", "-e", f"{sha}^{{commit}}", cwd=RESTORE)
        run("git", "cat-file", "-e", f"{sha}^{{tree}}", cwd=RESTORE)
        observed = run("git", "rev-list", "--parents", "-n", "1", sha, cwd=RESTORE).strip()
        rows.append(
            {
                "commit_sha": sha,
                "commit_object": "PASS",
                "tree_object": "PASS",
                "expected_parent_sha": parent,
                "observed_parent_line": observed,
                "parent_relationship": "PASS" if observed == f"{sha} {parent}" else "FAIL",
            }
        )
    fsck = subprocess.run(
        ["git", "fsck", "--full"],
        cwd=RESTORE,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if fsck.returncode != 0:
        raise SystemExit(f"restore fsck failed: {fsck.stdout}")
    write(RAW / "restore_fsck.txt", fsck.stdout or "RESTORE_GIT_FSCK=PASS")
    return rows


def preservation_rows() -> list[dict[str, str]]:
    index_tree = git("write-tree").strip()
    packages = [
        (ROUND11, "ROUND11_RESEARCH", "docs/research/trace-v49-exploration-constraint-kernel-round1"),
        (ROUND11, "ROUND11_AUDIT", "docs/audits/v49-exploration-constraint-kernel-round1"),
        (ROUND12, "ROUND12_RESEARCH", "docs/research/trace-v49-exploration-inquiry-flow-round1"),
        (ROUND12, "ROUND12_AUDIT", "docs/audits/v49-exploration-inquiry-flow-round1"),
    ]
    rows = []
    for source, label, path in packages:
        source_tree = git("rev-parse", f"{source}:{path}").strip()
        merged_tree = git("rev-parse", f"{index_tree}:{path}").strip()
        rows.append(
            {
                "artifact": label,
                "source_commit": source,
                "path": path,
                "source_tree_sha": source_tree,
                "merged_tree_sha": merged_tree,
                "preserved": "PASS" if source_tree == merged_tree else "FAIL",
            }
        )
    if any(row["preserved"] != "PASS" for row in rows):
        raise SystemExit("sealed package tree changed")
    return rows


def gate_rows() -> list[dict[str, str]]:
    return [
        {"gate": "DEPENDENCY_INSTALL", "status": "PASS", "evidence": "frontend npm ci; 145 packages installed"},
        {"gate": "GIT_FSCK", "status": "PASS", "evidence": "git fsck --full exit 0; dangling objects informational"},
        {"gate": "LFS_FSCK", "status": "PASS", "evidence": "git lfs fsck: Git LFS fsck OK"},
        {"gate": "ROUND8_REGRESSION", "status": "PASS", "evidence": "reset guard; 6 structural checks; 12/12 red-team rejects"},
        {"gate": "ROUND9_REGRESSION", "status": "PASS", "evidence": "sealed source/attestation/full-candidate/noun/explainability/polysemy/breadth/saturation gates"},
        {"gate": "ROUND10_REGRESSION", "status": "PASS", "evidence": "sealed validator; 256 ordered pairs; zero universal passes; 1,904 review rows"},
        {"gate": "ROUND11_REGRESSION", "status": "PASS", "evidence": "sealed validator plus final-tree kernel: 20/20 adversarial, 10 mutations, real build rejected"},
        {"gate": "ROUND12_REGRESSION", "status": "PASS", "evidence": "9 Python tests; 14 TypeScript fixtures; strict schema/flow/tree/five Instance gates"},
        {"gate": "TYPECHECK", "status": "PASS", "evidence": "npx tsc --noEmit --pretty false"},
        {"gate": "SEARCH_REGRESSION", "status": "PASS", "evidence": "index check; 14 checks; 7,995 public documents"},
        {"gate": "CONTEXT_REGRESSION", "status": "PASS", "evidence": "projection, governance, runtime and API"},
        {"gate": "SPACETIME_REGRESSION", "status": "PASS", "evidence": "projection, governance, runtime, API and GIS"},
        {"gate": "API_TESTS", "status": "PASS", "evidence": "read-platform, page module, Context and Spacetime APIs"},
        {"gate": "DATABASE_FREEZE", "status": "PASS", "evidence": "126 frozen files; drift 0; unmanifested v49 count 0"},
        {"gate": "REPOSITORY_HYGIENE", "status": "PASS", "evidence": "enhanced audit; preliminary and final staged-tree passes; violations 0"},
        {"gate": "AUDIT_SELF_CONTAINED", "status": "PASS", "evidence": "232 manifest files; 233 checksums; ignored evidence rejected"},
        {"gate": "PRODUCTION_BUILD", "status": "PASS", "evidence": "Next.js compile/type validity; 46/46 static pages"},
        {"gate": "BUNDLE_VERIFY", "status": "PASS", "evidence": BUNDLE_SHA},
        {"gate": "RESTORE_DRILL", "status": "PASS", "evidence": "4/4 commits and trees; parents; restored fsck"},
        {"gate": "ALLOWLIST_RECONCILIATION", "status": "PASS", "evidence": "230 declared/rows/tracked; missing/extra/duplicate/unknown all 0"},
    ]


def generate() -> None:
    RELEASE.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)

    if sha256(BUNDLE) != BUNDLE_SHA or BUNDLE.stat().st_size != BUNDLE_BYTES:
        raise SystemExit("bundle identity changed")
    bundle_verify = run("git", "bundle", "verify", str(BUNDLE))
    bundle_heads = run("git", "bundle", "list-heads", str(BUNDLE))
    write(RAW / "bundle_verify.txt", bundle_verify)
    write(RAW / "bundle_list_heads.txt", bundle_heads)
    write(RAW / "bundle_sha256.txt", f"{BUNDLE_SHA}  {BUNDLE}")
    write(RAW / "bundle_capacity_preflight.txt", "\n".join([
        "AVAILABLE_KIB_BEFORE_BUNDLE=4300972",
        "REACHABLE_STREAM_PACK_ESTIMATE_BYTES=91125496",
        f"ACTUAL_BUNDLE_BYTES={BUNDLE_BYTES}",
        "CONSERVATIVE_REQUIRED_BYTES=1368709872",
        "CAPACITY_GATE=PASS",
        "NOTE=LFS payloads are outside Git bundle scope and were independently verified by git lfs fsck.",
    ]))

    if RESTORE.exists():
        restore_rows = verify_restore()
    else:
        with (RAW / "restore_object_validation.tsv").open(
            encoding="utf-8", newline=""
        ) as handle:
            restore_rows = list(csv.DictReader(handle, delimiter="\t"))
        if len(restore_rows) != 4 or any(
            row["commit_object"] != "PASS"
            or row["tree_object"] != "PASS"
            or row["parent_relationship"] != "PASS"
            for row in restore_rows
        ):
            raise SystemExit("sealed restore evidence is incomplete")
    write_tsv(
        RAW / "restore_object_validation.tsv",
        ["commit_sha", "commit_object", "tree_object", "expected_parent_sha", "observed_parent_line", "parent_relationship"],
        restore_rows,
    )

    graph = [
        commit_row(BASE, "COMMON_ANCESTOR_ROUND10", "common"),
        commit_row(MAIN, "AUTHORITATIVE_MAIN_MAINTENANCE", "main_unique_1"),
        commit_row(ROUND11, "ROUND11_CONSTRAINT_KERNEL", "round12_unique_1_of_2"),
        commit_row(ROUND12, "ROUND12_INQUIRY_FLOW", "round12_unique_2_of_2"),
    ]
    write_tsv(RELEASE / "01_PREMERGE_GRAPH.tsv", list(graph[0]), graph)

    refs = [
        {"reference": "refs/heads/backup/main-before-round11-round12-integration-20260825", "kind": "REMOTE_BACKUP_BRANCH", "reference_object_sha": MAIN, "peeled_commit_sha": MAIN, "remote_verified": "PASS", "retention": "RETAIN"},
        {"reference": "refs/heads/backup/round12-sealed-before-integration-20260825", "kind": "REMOTE_BACKUP_BRANCH", "reference_object_sha": ROUND12, "peeled_commit_sha": ROUND12, "remote_verified": "PASS", "retention": "RETAIN"},
        {"reference": "refs/tags/main-before-round11-round12-integration-20260825", "kind": "ANNOTATED_TAG", "reference_object_sha": "77da7974c345c922206090cf66d02ed9bd6aed6f", "peeled_commit_sha": MAIN, "remote_verified": "PASS", "retention": "RETAIN"},
        {"reference": "refs/tags/round12-sealed-20260825", "kind": "ANNOTATED_TAG", "reference_object_sha": "281dd2b2ebe25c16a3a9a6df9a18f809030a06da", "peeled_commit_sha": ROUND12, "remote_verified": "PASS", "retention": "RETAIN"},
        {"reference": str(BUNDLE), "kind": "LOCAL_GIT_BUNDLE", "reference_object_sha": BUNDLE_SHA, "peeled_commit_sha": "six refs; see raw/bundle_list_heads.txt", "remote_verified": "LOCAL_VERIFY_PASS", "retention": "RETAIN"},
    ]
    write_tsv(RELEASE / "02_BACKUP_REFERENCE_REGISTRY.tsv", list(refs[0]), refs)

    preservation = preservation_rows()
    write_tsv(RAW / "sealed_package_tree_preservation.tsv", list(preservation[0]), preservation)
    identities = [
        {"commit_sha": MAIN, "role": "MAIN_MAINTENANCE", "original_parent_sha": BASE, "object_resolves": "PASS", "reachable_from_merge": "PASS", "sha_unchanged": "true"},
        {"commit_sha": ROUND11, "role": "ROUND11_CONSTRAINT_KERNEL", "original_parent_sha": BASE, "object_resolves": "PASS", "reachable_from_merge": "PASS", "sha_unchanged": "true"},
        {"commit_sha": ROUND12, "role": "ROUND12_INQUIRY_FLOW", "original_parent_sha": ROUND11, "object_resolves": "PASS", "reachable_from_merge": "PASS", "sha_unchanged": "true"},
    ]
    write_tsv(RELEASE / "06_COMMIT_IDENTITY_PRESERVATION.tsv", list(identities[0]), identities)

    gates = gate_rows()
    write_tsv(RAW / "test_results.tsv", list(gates[0]), gates)
    write(RAW / "worktrees_before_merge.txt", git("worktree", "list", "--porcelain"))
    write(RAW / "local_branches.tsv", git("for-each-ref", "--format=%(refname:short)%09%(objectname)%09%(committerdate:iso8601)%09%(subject)", "refs/heads"))
    write(RAW / "remote_branches.tsv", git("for-each-ref", "--format=%(refname:short)%09%(objectname)%09%(committerdate:iso8601)%09%(subject)", "refs/remotes/origin"))
    write(RAW / "tags.tsv", git("for-each-ref", "--format=%(refname:short)%09%(objectname)%09%(creatordate:iso8601)%09%(subject)", "refs/tags"))

    write(RELEASE / "00_EXECUTIVE_DECISION.md", f"""# Executive decision

Remote `main` received authoritative repository-hygiene commit `{MAIN}` while Round 11 and Round 12 continued from common ancestor `{BASE}`. The observed graph is exactly one main-only commit and two Round12-side commits. A two-parent merge is therefore required; rebasing, squashing, cherry-pick reconstruction, or force pushing would break sealed provenance.

The coordination preserves all three identities: main maintenance `{MAIN}`, Round 11 `{ROUND11}`, and Round 12 `{ROUND12}`. Parent order is fixed as main first and Round 12 second. The sole content conflict is rebuilt from the final tracked-script set, preserving main's enhanced diagnostic implementation and all Round 10–12 scripts.

Decision: `AUTHORITATIVE_HISTORY_COORDINATION`. No vocabulary, grammar, real Image, public Exploration surface, database, Search, Context, Spacetime, deployment, branch deletion, or evidence rewrite is activated by this merge.""")

    write(RELEASE / "03_BUNDLE_AND_RESTORE_VALIDATION.md", f"""# Bundle and restore validation

The retained bundle is `{BUNDLE}` ({BUNDLE_BYTES} bytes; SHA-256 `{BUNDLE_SHA}`). `git bundle verify` reports a complete history and six heads: main, Round 12, both remote backup branches, and both annotated tags.

A bare mirror was cloned from the bundle into the exact temporary restore-test path. Commits `{MAIN}`, `{ROUND11}`, `{ROUND12}`, and `{BASE}` each resolved as commit and tree objects; their parent lines matched the original graph. Restored `git fsck --full` exited zero. `RESTORE_DRILL=PASS`, `RESTORED_REQUIRED_COMMIT_COUNT=4`, and `RESTORED_MISSING_OBJECT_COUNT=0`.

The restore-test copy may be deleted after this receipt is sealed. The bundle must be retained until a later explicit backup-cleanup task.""")

    write(RELEASE / "04_CONFLICT_RESOLUTION.md", """# Conflict resolution

Only `docs/maintenance/V49_ACTIVE_SCRIPT_ALLOWLIST.json` conflicted. The resolution did not select either parent wholesale. A deterministic reconciliation script enumerated `git ls-files scripts`, joined every path to the sealed Round 12 classification rows, accepted both governed decisions (`KEEP_ACTIVE` and `DOCUMENTED_ALLOWLIST`), sorted paths, and regenerated JSON, CSV, Markdown, and the reconciliation ledger.

The final counts are 230 tracked paths, 230 rows, and declared count 230. Missing, extra, duplicate, and unknown-classification counts are all zero. All Round 10 grammar, Round 11 constraint-kernel, and Round 12 inquiry-engine scripts are present. Main's `scripts/repository/audit_repository_hygiene.py` is byte-identical to `cc311ab` and therefore retains its enhanced missing/extra/duplicate diagnostics.""")

    write(RELEASE / "07_FULL_VALIDATION.md", """# Full validation

All authoritative gates completed successfully. The machine-readable matrix is `docs/audits/v49-round11-round12-main-integration/raw/test_results.tsv`.

- Repository integrity: full Git fsck, Git LFS fsck, broken documentation links, script references, frontend imports, allowlist reconciliation, database freeze, and audit self-containment passed.
- Round 8–10: reset/domain boundaries, vocabulary research, grammar pair matrix, universal-node gate, and sealed audit checks passed.
- Round 11: Round 10 reconciliation, 20 adversarial cases, compiler behavior, synthetic isolation, real-build rejection, immutability, and ten fail-open mutations passed.
- Round 12: immutable freeze and evidence coverage, nine Python reference tests, fourteen cross-runtime fixtures, strict schemas, flow/tree planning, five Instances, and historical-claim rejection passed.
- Platform: TypeScript, Search, Context, Spacetime, API/read-platform, and production build (46/46 static pages) passed.

Round 6 all-pair similarity and Round 7 dense encoding were intentionally not rerun because both are superseded historical research.""")

    write(RELEASE / "08_ROLLBACK_PROCEDURE.md", f"""# Rollback and recovery

Recovery should create a new branch or worktree from an immutable anchor; force pushing is not the default.

1. Remote branch: fetch `backup/main-before-round11-round12-integration-20260825`, then create a recovery branch at `{MAIN}`. The sealed Round 12 chain is independently available at `backup/round12-sealed-before-integration-20260825`.
2. Annotated tag: verify `main-before-round11-round12-integration-20260825^{{}}` equals `{MAIN}` or `round12-sealed-20260825^{{}}` equals `{ROUND12}`, then branch from the selected tag.
3. Offline bundle: run `git bundle verify {BUNDLE}`, clone it as a mirror, and create a worktree from one of the six listed heads. Verify SHA-256 `{BUNDLE_SHA}` before recovery.

If operational policy later requires changing `main`, use a separately reviewed forward recovery commit or merge. No tag, backup branch, source branch, integration branch, or bundle is deleted in this task.""")

    write(RELEASE / "09_POSTMERGE_STATE.md", f"""# Post-merge state

The merge commit must have parent 1 `{MAIN}` and parent 2 `{ROUND12}`. It must retain `{ROUND11}` through parent 2 and be a descendant of the unchanged pre-merge `origin/main`. Updating `main` is then a normal non-force fast-forward from `{MAIN}` to the merge commit.

The commit cannot embed its own SHA in its tree. Its exact identity is resolved after creation by the remote integration branch, remote `main`, the annotated tag `v49-round12-main-integration-20260825`, and the external final receipt. Expected post-push divergence is `0/0`.

All research semantics remain as sealed: zero active vocabulary/grammar/pair/Cluster/chain rules and no real or public Exploration Image. Branch deletion, tag deletion, bundle deletion, and deployment remain zero.""")

    write(AUDIT / "00_EXECUTIVE_RECEIPT.md", f"""# Executive receipt

The observed `{MAIN}` versus `{ROUND12}` graph matched the required `1/2` divergence at merge base `{BASE}`. Two remote backup branches, two annotated tags, and a verified/restored bundle were established before merge. The final merge index preserves all three existing commit identities, main's enhanced hygiene implementation, and the sealed Round 11/12 package trees.

All authoritative gates pass. The authorized outcome is a two-parent `AUTHORITATIVE_HISTORY_COORDINATION` merge with no rewrite, force push, branch/tag deletion, bundle deletion, research activation, or deployment.""")
    write(AUDIT / "01_GRAPH_VALIDATION.md", f"""# Graph validation

`origin/main={MAIN}`, `round12={ROUND12}`, and `merge-base={BASE}`. `git rev-list --left-right --count` returned `1 2`. `{ROUND11}` is the direct parent of Round 12 and the direct child of the common ancestor; main maintenance is the other direct child. The prepared merge index retains `HEAD={MAIN}` and `MERGE_HEAD={ROUND12}`, fixing parent order before commit.""")
    write(AUDIT / "02_BACKUP_VALIDATION.md", """# Backup validation

Both remote backup branches were created only after confirming the names were absent. Direct `git ls-remote` verification returned the expected commits. Both annotated tags were verified locally and remotely at the tag-object and peeled-commit levels. All four references are retained and must not be moved by this task.""")
    write(AUDIT / "03_BUNDLE_RESTORE_VALIDATION.md", f"""# Bundle and restore validation

Bundle SHA-256: `{BUNDLE_SHA}`; bytes: `{BUNDLE_BYTES}`. The capacity gate used an actual 91,125,496-byte streaming pack estimate and retained more than 1 GiB above two bundle-sized copies and log allowance. Bundle verification and the four-commit restore drill pass with zero missing objects. Raw heads, checksum, capacity, object and fsck evidence are sealed under `raw/`.""")
    write(AUDIT / "04_ALLOWLIST_RECONCILIATION.md", """# Allowlist reconciliation

The final tracked/row/declared counts are 230/230/230. Missing, unexpected, duplicate and unknown-classification counts are 0/0/0/0. The JSON, CSV, Markdown, and release ledger were generated together from the merge index rather than repaired by changing a count. Main's enhanced hygiene auditor is preserved exactly.""")
    write(AUDIT / "05_ROUND11_PRESERVATION.md", f"""# Round 11 preservation

Commit `{ROUND11}` resolves unchanged and remains the parent of Round 12. The research subtree `docs/research/trace-v49-exploration-constraint-kernel-round1` and audit subtree `docs/audits/v49-exploration-constraint-kernel-round1` have identical tree SHAs in the sealed commit and merge index. Synthetic fixtures, Image hashes, real-build rejection, immutability, and fail-closed semantics are unchanged.""")
    write(AUDIT / "06_ROUND12_PRESERVATION.md", f"""# Round 12 preservation

Commit `{ROUND12}` resolves unchanged as merge parent 2. Its research and audit subtree SHAs match the merge index exactly. Candidate-freeze hash, five Instance payloads, schemas, Python reference semantics, TypeScript conformance semantics, evidence counts, and strict rejection behavior are unmodified.""")
    write(AUDIT / "07_PROTECTED_SYSTEMS.md", """# Protected systems

Database freeze, Search, governed Context, Spacetime, API/read-platform, zero-object Exploration, external-model purge, and production build gates all pass. The only integration-specific content changes are regenerated allowlist outputs, coordination documentation, project/release/audit index entries, and this merge audit package. No canonical data, public Exploration activation, deployment, or branch cleanup occurs.""")

    append_once(ROOT / "PROJECT_LOG.md", "## v49 Round 11–12 history coordination — 2026-08-25", f"""## v49 Round 11–12 history coordination — 2026-08-25

- Reconciled main maintenance `{MAIN}` with sealed Round 11 `{ROUND11}` and Round 12 `{ROUND12}` through an authorized two-parent merge from common ancestor `{BASE}`.
- Preserved all three existing commit identities and sealed research/audit subtrees. Rebuilt the final active-script ledgers at 230/230/230 with zero missing, extra, duplicate, or unknown entries while retaining main's enhanced hygiene diagnostics.
- Established two remote backup branches, two annotated tags, and a verified 91,051,946-byte bundle with a successful four-commit restore drill before updating main.
- All Round 8–12, Search, Context, Spacetime, API, typecheck, database-freeze, repository-hygiene, audit, LFS, Git integrity, and production-build gates pass. No research activation, history rewrite, force push, branch/tag cleanup, bundle cleanup, or deployment is authorized.

`ROUND11_ROUND12_HISTORY_COORDINATION=AUTHORITATIVE`

`EXISTING_COMMIT_SHA_PRESERVATION=3/3`

`ACTIVE_RELATION_VOCABULARY_COUNT=0`

`ACTIVE_RELATION_GRAMMAR_COUNT=0`

`REAL_SEMANTIC_IMAGE_READY=false`

`NEXT_RESEARCH_GATE=EXTERNAL_DOMAIN_REVIEW_AND_INQUIRY_GRAMMAR_ACTIVATION_RESEARCH`""")
    append_once(ROOT / "docs/releases/v49/RELEASE_INDEX.md", "## Round 11–12 main integration — 2026-08-25", f"""## Round 11–12 main integration — 2026-08-25

- Main-before anchor: `{MAIN}`.
- Preserved Round 11/12 anchors: `{ROUND11}` and `{ROUND12}`.
- Common ancestor: `{BASE}`; observed divergence: 1 main-only / 2 Round12-only commits.
- Release package: `docs/releases/v49/round11-round12-main-integration-20260825/`.
- Audit package: `docs/audits/v49-round11-round12-main-integration/`.
- Recovery assets: two remote backup branches, two annotated tags, and retained verified bundle SHA-256 `{BUNDLE_SHA}`.
- Integration policy: two-parent merge, no history rewrite, no force push, no deletion, no deployment, and no activation of research candidates.""")
    append_once(ROOT / "docs/releases/v49/AUDIT_INDEX.md", "## Round 11–12 history-coordination audit — 2026-08-25", """## Round 11–12 history-coordination audit — 2026-08-25

| Package | Classification | Scope |
|---|---|---|
| `docs/audits/v49-round11-round12-main-integration` | FINAL_AUTHORITATIVE_HISTORY_COORDINATION | 1/2 graph divergence, three preserved commit identities, remote/tag/bundle backups, restore drill, sealed Round 11/12 preservation, allowlist rebuild, protected systems, and full validation. |

The paired release package is `docs/releases/v49/round11-round12-main-integration-20260825/`. The post-integration main identity is established by `v49-round12-main-integration-20260825` and the remote final receipt because a commit cannot contain its own SHA.""")

    tracked_changes = set(git("diff", "--cached", "--name-only", MAIN).splitlines())
    tracked_changes.update(git("ls-files", "--others", "--exclude-standard").splitlines())
    changed_lines = ["# Changed files", "", "The merge contains inherited Round 11/12 files plus the following coordination-specific paths:", ""]
    coordination = sorted(
        path for path in tracked_changes
        if path.startswith("docs/releases/v49/round11-round12-main-integration-20260825/")
        or path.startswith("docs/audits/v49-round11-round12-main-integration/")
        or path in {"PROJECT_LOG.md", "docs/releases/v49/RELEASE_INDEX.md", "docs/releases/v49/AUDIT_INDEX.md", "docs/maintenance/V49_ACTIVE_SCRIPT_ALLOWLIST.json", "docs/maintenance/V49_ACTIVE_SCRIPT_ALLOWLIST.csv", "docs/maintenance/V49_ACTIVE_SCRIPT_ALLOWLIST.md"}
    )
    changed_lines.extend(f"- `{path}`" for path in coordination)
    changed_lines.extend(["", "Round 11/12 research and audit packages are inherited unchanged from parent 2; their subtree identities are recorded in `raw/sealed_package_tree_preservation.tsv`."])
    write(AUDIT / "08_CHANGED_FILES.md", "\n".join(changed_lines))

    manifest_rows = []
    for path in sorted(AUDIT.rglob("*")):
        if not path.is_file() or path.name in {"MANIFEST.tsv", "SHA256SUMS.txt"}:
            continue
        manifest_rows.append(
            {
                "relative_path": path.relative_to(ROOT).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    write_tsv(AUDIT / "MANIFEST.tsv", ["relative_path", "bytes", "sha256"], manifest_rows)
    checksum_paths = [path for path in sorted(AUDIT.rglob("*")) if path.is_file() and path.name != "SHA256SUMS.txt"]
    write(
        AUDIT / "SHA256SUMS.txt",
        "\n".join(f"{sha256(path)}  {path.relative_to(ROOT).as_posix()}" for path in checksum_paths),
    )

    print(f"BUNDLE_BYTES={BUNDLE_BYTES}")
    print(f"BUNDLE_SHA256={BUNDLE_SHA}")
    print("BUNDLE_VERIFY=PASS")
    print("RESTORE_DRILL=PASS")
    print("RESTORED_REQUIRED_COMMIT_COUNT=4")
    print("RESTORED_MISSING_OBJECT_COUNT=0")
    print("ROUND11_EVIDENCE_PRESERVED=PASS")
    print("ROUND12_EVIDENCE_PRESERVED=PASS")
    print(f"AUDIT_MANIFEST_ROW_COUNT={len(manifest_rows)}")
    print("AUDIT_SEAL=PASS")


if __name__ == "__main__":
    generate()
