# Public Surface Payload Sharding v1

## Purpose

The generated public surface payload has crossed the point where a single static JSON file is a safe build primitive. This pass creates deterministic sidecar shards while keeping the legacy monolithic payload in place for existing audits and frontend routes.

## Current Payload

- Source payload: `generated/public_surfaces_v1.json`
- Source payload size: 135.98 MiB
- Output roots: `generated/public_surfaces_v1_shards`, `frontend/public/data/public_surface_shards_v1`
- Metrics CSV: `data/public_surface_payload_sharding_v1.csv`

## Shard Result

- Maximum section/shard size: 4.52 MiB
- `surfaces`: 13680 rows across 28 shards; largest shard 4.52 MiB
- `researchDossiers`: 13680 rows across 28 shards; largest shard 1.02 MiB

## Contract

- This is a sidecar export. It does not change `frontend/src/data/public_surface_mock_v0.json` or the current frontend import path.
- `manifest.json` records section counts, shard files, byte sizes, and SHA-256 hashes.
- `indexes/surfaces_by_id.json` maps each `surfaceId` to its shard path and offset.
- `indexes/research_dossiers_by_anchor.json` maps dossier/anchor ids for later lazy loading.
- The shard directories are generated artifacts and are ignored in git until the frontend data layer is migrated to consume them directly.
- Local image files, thumbnails, screenshots, cookies, sessions, and raw third-party payloads are not created.

## Next Use

The next frontend optimization can replace the static import with manifest-driven loading, starting from folder/index views before migrating surface detail pages. Until that migration is complete, release audits should continue treating the monolithic payload as canonical.
