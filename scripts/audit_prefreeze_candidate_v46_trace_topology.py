#!/usr/bin/env python3
"""Run the active-layer root-and-branch topology gate for v46."""

from __future__ import annotations

import audit_prefreeze_candidate_v36_trace_topology as base


base.PAYLOAD = base.GENERATED / "public_surfaces_prefreeze_candidate_v46.json"
base.EXTRA_TRACE_FILES = (
    (base.DATA / "prefreeze_candidate_v36_wellcome_trace_nodes.csv", base.DATA / "prefreeze_candidate_v36_wellcome_trace_edges.csv"),
    (base.DATA / "prefreeze_candidate_v37_source_root_nodes.csv", base.DATA / "prefreeze_candidate_v37_source_root_edges.csv"),
    (base.DATA / "prefreeze_candidate_v40_gallica_1810_trace_nodes.csv", base.DATA / "prefreeze_candidate_v40_gallica_1810_trace_edges.csv"),
    (base.DATA / "prefreeze_candidate_v42_loc_direct_reattach_trace_nodes.csv", base.DATA / "prefreeze_candidate_v42_loc_direct_reattach_trace_edges.csv"),
    (base.DATA / "prefreeze_candidate_v43_loc_verified_batch_trace_nodes.csv", base.DATA / "prefreeze_candidate_v43_loc_verified_batch_trace_edges.csv"),
    (base.DATA / "capture_batch_trace_first_gallica_1804_1817_2026_v1_trace_nodes.csv", base.DATA / "capture_batch_trace_first_gallica_1804_1817_2026_v1_trace_edges.csv"),
    (base.DATA / "prefreeze_candidate_v46_loc_duplicate_resolution_trace_nodes.csv", base.DATA / "prefreeze_candidate_v46_loc_duplicate_resolution_trace_edges.csv"),
)
base.AUDIT = base.DATA / "prefreeze_candidate_v46_trace_topology_audit.csv"
base.SUMMARY = base.DATA / "prefreeze_candidate_v46_trace_topology_summary.csv"
base.REPORT = base.DOCS / "PREFREEZE_CANDIDATE_v46_TRACE_TOPOLOGY.md"


if __name__ == "__main__":
    base.main()
    base.REPORT.write_text(base.REPORT.read_text(encoding="utf-8").replace("v36", "v46"), encoding="utf-8")
