# v49 audit index

All listed packages are recoverable at `v49-data-api-closure-20260821`. Final authoritative packages remain active; supporting packages remain indexed evidence unless a later maintenance revision proves them redundant.

| Package | Classification | Files | Bytes |
|---|---|---:|---:|
| `docs/audits/v49-api-read-contract-closure` | FINAL_AUTHORITATIVE | 87 | 12406417 |
| `docs/audits/v49-authority-research-delta` | INDEXED_SUPPORTING_EVIDENCE | 25 | 6635970 |
| `docs/audits/v49-phase1d-final` | INDEXED_SUPPORTING_EVIDENCE | 4 | 31047 |
| `docs/audits/v49-phase2a-schema` | INDEXED_SUPPORTING_EVIDENCE | 23 | 6705560 |
| `docs/audits/v49-phase2b-evidence-amendment` | INDEXED_SUPPORTING_EVIDENCE | 234 | 768438 |
| `docs/audits/v49-phase2b-migration` | FINAL_AUTHORITATIVE | 52 | 18555617 |
| `docs/audits/v49-phase2b-performance` | INDEXED_SUPPORTING_EVIDENCE | 62 | 7121592 |
| `docs/audits/v49-pre-migration` | INDEXED_SUPPORTING_EVIDENCE | 18 | 7115048 |
| `docs/audits/v49-product-foundation` | INDEXED_SUPPORTING_EVIDENCE | 9 | 35972 |
| `docs/audits/v49-release-projection-snapshot` | INDEXED_SUPPORTING_EVIDENCE | 11 | 48451 |
| `docs/audits/v49-release-projection-snapshot-closure` | INDEXED_SUPPORTING_EVIDENCE | 13 | 38797 |
| `docs/audits/v49-release-projection-snapshot-db-closure` | FINAL_AUTHORITATIVE | 259 | 33759563 |
| `docs/audits/v49-release-projection-snapshot-performance` | INDEXED_SUPPORTING_EVIDENCE | 27 | 61661 |
| `docs/audits/v49-rights-machine` | INDEXED_SUPPORTING_EVIDENCE | 22 | 272791 |
| `docs/audits/v49-runtime-acceptance` | INDEXED_SUPPORTING_EVIDENCE | 15 | 27310 |
| `docs/audits/v49-runtime-acceptance-closure` | INDEXED_SUPPORTING_EVIDENCE | 9 | 26530 |
| `docs/audits/v49-runtime-cleanup` | INDEXED_SUPPORTING_EVIDENCE | 9 | 50092 |

## Main integration audit — 2026-08-25

| Package | Classification | Scope |
|---|---|---|
| `docs/audits/v49-main-integration-20260825` | FINAL_AUTHORITATIVE_INTEGRATION_RECEIPT | Old-main/Round-9 ancestry, 72 complete commit descriptions, authority/supersession, current gates, branch reachability, rollback tags, and non-force main update policy. |

The paired release package is `docs/releases/v49/main-integration-20260825/`. It preserves the 72-commit history from old main `592c765d0af5bf15b1666784dce784ac8e22624d` through Round 9 `47978c519c3c7141690e3894315a1ef1b7a403db`; the new main anchor is the integration commit identified by `v49-research-main-integration-20260825`.

Round 6 object similarity and Round 7 object NLP remain superseded despite becoming reachable from main. Round 9 is research input for Round 10 grammar research and is not active product vocabulary. No branch deletion or deployment is part of this audit.

## Round 11–12 history-coordination audit — 2026-08-25

| Package | Classification | Scope |
|---|---|---|
| `docs/audits/v49-round11-round12-main-integration` | FINAL_AUTHORITATIVE_HISTORY_COORDINATION | 1/2 graph divergence, three preserved commit identities, remote/tag/bundle backups, restore drill, sealed Round 11/12 preservation, allowlist rebuild, protected systems, and full validation. |

The paired release package is `docs/releases/v49/round11-round12-main-integration-20260825/`. The post-integration main identity is established by `v49-round12-main-integration-20260825` and the remote final receipt because a commit cannot contain its own SHA.
