# Reproducible Census Method

Run from repository root:

```bash
python3 -u scripts/trace-v49-analysis/generate_trace_v49_round1.py
python3 -u scripts/trace-v49-analysis/generate_trace_v49_round1.py --check
```

The generator validates the recorded input hashes and v49 freeze/replay metrics before analysis. It obtains the exact public/held set from the audited `18_SURFACE_ROW_LEDGER.tsv`, never from legacy fallback eligibility. SQLite is opened as:

```text
file:data/prefreeze_candidate_v48.sqlite?mode=ro&immutable=1
PRAGMA query_only=ON
PRAGMA integrity_check=ok
```

Percentiles use linear interpolation at `(n-1) × p`. Counts preserve their units: archive objects, root nodes, folder assignments, semantic relations, projection edges, relation memberships, legacy memberships, source bridges, and evidence rows are never added or renamed as generic relations.

Legacy local graph diagnostics join `object_trace_edges.edge_id` to `trace_edges`. The generator never positional-zips canonical `edgeIds` and `edgeLabels`; their lengths differ on 9,393 objects. Legacy results are classified solely as layout/performance evidence.

`CHECKSUMS.sha256` covers all generator-owned artifacts. The final audit manifest additionally covers manual reports, raw browser/validation receipts, scripts, and the renderer-neutral TypeScript package.
