# B3 — Legacy Visual Disposition Receipt

**Exit status: PASS**

## Task boundary

B3 produced a deterministic, read-only typed baseline for the legacy v48 visual-related population. It did not adjudicate positive rights, contact providers, probe endpoints, infer permission from technical availability, or decide delivery modes.

Exclusive outputs:

- `docs/audits/v49-rights-machine/05_LEGACY_VISUAL_DISPOSITION_BASELINE.tsv`
- `docs/audits/v49-rights-machine/06_LEGACY_VISUAL_DISPOSITION_SUMMARY.json`
- `docs/audits/v49-rights-machine/agents/B3_LEGACY_VISUAL_DISPOSITION_RECEIPT.md`

No other repository file was modified by B3.

## Authority and classification unit

| Asset | B3 use | Authority boundary |
| --- | --- | --- |
| `generated/public_surfaces_prefreeze_candidate_v48.json` | Parsed exactly once; every `/surfaces/<ordinal>` raw visual bundle was enumerated | Sole canonical migration input; raw bytes are lexical authority |
| `data/prefreeze_candidate_v48.sqlite` | Aggregate reconciliation query through `mode=ro&immutable=1` | Immutable reconciliation evidence only; never creates, promotes, or fills canonical rows |
| `docs/audits/v49-pre-migration/06_RIGHTS_AND_VISUAL_FEDERATION.md` | Prior-risk context only | Audit evidence, not row authority |
| `frontend/src/types/archive.ts` | Legacy field-shape context only | Runtime type evidence, not rights authority |

The committed classification unit is one exact candidate `/surfaces/<ordinal>` raw visual bundle, comprising `surface.image`, optional `surface.images[]`, `surface.rights`, and `surface.reviewGates.rightsReviewed`. Every one of the 15,923 input surfaces contributes exactly once. There is no deduplication, merge, delimiter split, or derived-to-canonical backfill.

A visual locator occurrence is a nonblank value under a URL/URI/manifest/viewer/thumbnail/service/canvas/infoJson/imageId-keyed field inside an image object. Only syntactically valid absolute HTTP(S) values count as external visual locators. `surface.sourceUrl` is a source/canonical-record locator, not a visual locator, and is excluded from this count.

## Closed status semantics

The baseline carries independent rights-evidence, provider-policy and provider-mapping columns plus an overall fail-closed disposition. The closed registry covers:

- `EVIDENCE_PRESENT`: raw structured evidence exists; never a permission grant;
- `RIGHTS_UNKNOWN`: legacy candidate/review labels are not adjudicated rights evidence;
- `POLICY_UNKNOWN`: no versioned provider-policy snapshot exists in the candidate;
- `CONFLICT`: explicit structured conflict/dispute token;
- `STALE`: explicit structured stale/expired/review-overdue token only;
- `NO_VISUAL_REFERENCE`: no valid external visual locator exists in the raw visual bundle;
- `TAKEDOWN_HOLD`: explicit structured takedown/withdrawal/suppression token;
- `MALFORMED`: invalid image/rights shape or invalid locator;
- `UNMAPPED_PROVIDER`: the candidate contains no stable provider foreign key; host and `sourceName` remain raw tokens.

Zero-count states remain in `closedStatusCounts`; a zero does not remove the state from the closed vocabulary. Unknown is classified and legal. Unclassified is not.

## Commands and process receipt

Representative commands, all local and bounded:

```text
head -c 600 generated/public_surfaces_prefreeze_candidate_v48.json
sed -n '1,230p' frontend/src/types/archive.ts
sqlite3 'file:.../data/prefreeze_candidate_v48.sqlite?mode=ro&immutable=1' '<aggregate SELECT only>'
/Users/jarlgiovanni/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --check /private/tmp/v49_phase1d_b3_scan.mjs
/usr/bin/time -lp <bundled-node> --max-old-space-size=4096 /private/tmp/v49_phase1d_b3_scan.mjs generated/public_surfaces_prefreeze_candidate_v48.json /private/tmp/v49_phase1d_b3_scan_output.json
NODE_PATH=<loader-provided-node_modules> <bundled-node> /private/tmp/v49_phase1d_b3_artifact/build_outputs.mjs /private/tmp/v49_phase1d_b3_scan_output.json docs/audits/v49-rights-machine
<bundled-python> -c '<strict UTF-8 TSV and JSON validation; row/column/count/hash assertions>'
git diff --check -- <B3 outputs>
```

Candidate scanner process receipt:

| Item | Result |
| --- | --- |
| candidate parses | exactly 1 |
| child scanner result | completed successfully and wrote the deterministic compact intermediate |
| unified shell session | `49157` |
| PID | unavailable after completion because the sandbox denied `ps`; no PID is guessed |
| elapsed / user / system | 44.15 s / 2.74 s / 0.47 s |
| wrapper exit | `/usr/bin/time` returned 1 only because sandbox blocked `sysctl kern.clockrate`; scanner output, SHA and counts completed |
| max RSS | unavailable because the same `sysctl` restriction prevented a complete time receipt |
| candidate SHA reruns | 0 |
| SQLite integrity checks | 0; the prior shared integrity receipt was not repeated |
| SQLite writes or sidecars | 0 |

The artifact-tool builder used the loader-provided Node runtime and `@oai/artifact-tool`, with a temporary `node_modules` symlink under `/private/tmp/v49_phase1d_b3_artifact`. It constructed the full 72-row by 29-column workbook projection, inspected it, scanned for formula errors, and rendered a bounded temporary preview. The first preview exposed a Metal shader timeout and an unreadable white-on-white header; one focused style repair removed the white text dependency and rerendered a readable header. The renderer retained one non-fatal pipeline timeout warning, while workbook inspection, the zero-formula-error scan, TSV output and strict parsers all completed successfully.

## Measured results

| Metric | Result |
| --- | ---: |
| candidate bytes | 190,067,852 |
| candidate SHA-256 | `b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48` |
| candidate surface visual bundles | 15,923 |
| accounted surface visual bundles | 15,923 |
| unaccounted surface visual bundles | 0 |
| reference-bearing surface visual bundles | 15,788 |
| no-reference surface visual bundles | 135 |
| external locator occurrences | 15,790 |
| distinct external locator values | 15,788 |
| compact disposition groups | 71 |
| unclassified visual references | 0 |
| positive-rights-qualified bundles | 0 |
| legacy positive-rights coverage | 0.0000% |

Locator roles are measured separately:

| Exact candidate role | Occurrences |
| --- | ---: |
| `image.url` | 15,621 |
| `image.viewerUrl` | 165 |
| `image.sourceViewerUrl` | 2 |
| `image.evidenceImageUrl` | 2 |

The 15,788 reference-bearing surface bundles are therefore not the same unit as SQLite's 15,621 nonblank `image_url` rows. SQLite reconciles the primary `image.url` role only. The immutable reconciliation query returned 15,923 object rows, 15,621 nonblank `image_url` rows, and 15,620 distinct `image_url` values; the primary candidate role matches exactly.

Legacy state populations also reconcile exactly:

| Legacy state pair | Count |
| --- | ---: |
| `IMG00` / `rights_review_required` | 36 |
| `IMG00` / `source_link_only` | 2 |
| `IMG01` / `thumbnail_candidate` | 30 |
| `IMG02` / `source_viewer_candidate` | 8,388 |
| `IMG03` / `open_candidate` | 7,370 |
| `IMG04` / `compound_member_rights` | 2 |
| `IMG04` / `rights_review_required` | 95 |

Overall dispositions are 15,788 `RIGHTS_UNKNOWN` and 135 `NO_VISUAL_REFERENCE`. Independently, all 15,788 reference-bearing bundles are `POLICY_UNKNOWN` and `UNMAPPED_PROVIDER`, because the candidate has neither a versioned provider-policy snapshot nor a stable provider FK. No explicit structured conflict, stale, takedown or malformed condition was observed; all remain valid zero-count registry states.

Deterministic hashes:

| Evidence | SHA-256 |
| --- | --- |
| surface ordinal/ID sequence | `0ded26112f66e9b269dd6f7ca5978d9454e254e52241ca121f63c56368eab418` |
| surface ID set | `7bae71cb2915a6ea6a9c9c43024a0a84bab5200edffad96298f398a7b8053d46` |
| source-record ID set | `16795db4223fd1e00ef362ba0a29b7a521a38ccf56638e9928d70a3343112f2e` |
| raw visual-bundle sequence | `265cc790ffcc5b4c4dddf5ddbb29a894f35f92e166df474a744dafa0b7e8743e` |
| external locator occurrence sequence | `1bbd68dfaf8661a1976fea56a2d121d807a42b5ed8a735094dda9868dcec5812` |
| external locator value set | `434dafb489119676615a6cd604a65286f17e2d8f2f18e48bf5e06943b6439e28` |
| classified surface sequence | `2ba50afc2175e350895f9b7b76615ba72cf2175cf4599b13b49f5ee107242abc` |
| compact TSV | `ca802327787821c5d9f0a0a1d3a818b3f6534a92361319fdfbcf7373d6e24e24` |

## Positive-rights coverage definition

The numerator requires a reference-bearing surface bundle with all of the following: independently adjudicated rights evidence, a versioned provider policy permitting remote display, complete attribution obligations, and no restrictive or takedown condition. The denominator is all 15,788 reference-bearing candidate surface visual bundles.

The candidate supplies no versioned provider-policy snapshot or sealed visual-registry assessment. Consequently, `IMG03`, `open_candidate`, `rightsReviewed=true`, an HTTP(S) locator, an IIIF-like field, a credit string, or a license label cannot qualify. The measured numerator is zero and coverage is 0.0000%. This is a conservative evidence measurement, not a statement that zero visuals could ever be authorized after review.

## Compact-ledger reproducibility

The TSV uses one row per exact disposition signature rather than committing a 15,923-row repetition. Each of its 71 rows carries:

- the exact status axes and legacy field values defining the group;
- surface and locator-occurrence counts;
- a member surface-ID set SHA-256;
- a member locator-occurrence-hash set SHA-256;
- up to three representative surface IDs;
- candidate hash, authority role, and recovery checkpoint.

Strict validation passed with 71 data rows, 29 unique columns, no CR bytes, no ragged row, a `surface_count` sum of 15,923, a locator-occurrence sum of 15,790, a positive-rights numerator of zero, and a TSV SHA matching the JSON summary. The committed outputs contain provider hostnames and hashes but no raw locator URL.

## Findings and gates

| Finding | Priority | Result |
| --- | --- | --- |
| B3-P0-01 | P0 | `LEGACY_VISUAL_REFERENCE_INVENTORIED=100%`; every candidate surface visual bundle and every detected locator role is accounted. |
| B3-P0-02 | P0 | `LEGACY_VISUAL_REFERENCE_TYPED=100%`; `UNCLASSIFIED_VISUAL_REFERENCE=0`. |
| B3-P0-03 | P0 | `open_candidate` and all other legacy composite states remain fail-closed; measured positive-rights coverage is 0.0000%. |
| B3-P1-01 | P1 | 15,788 reference-bearing bundles lack a versioned provider-policy snapshot and stable provider FK. They are typed unknown/unmapped migration work, not unclassified rows. |
| B3-P1-02 | P1 | 135 bundles have no external visual locator but remain retained and typed `NO_VISUAL_REFERENCE`; they do not disappear. |
| B3-P2-01 | P2 | The visual locator population has four distinct candidate roles. A future migration must preserve roles rather than collapsing them into one `image_url`. |

## Unresolved and downstream boundary

B3 has no unclassified legacy visual row. It deliberately leaves positive rights adjudication, provider mapping, provider-policy snapshots, delivery assessments, endpoint health, takedown decisions, and visual-registry release membership to governed v49 implementation. Unknown and unmapped states are complete typed dispositions and must fail closed; they are not permission to backfill from SQLite, Search, TRACE, runtime caches, or provider reachability.

## Actions explicitly not performed

- no network request, provider contact, HTTP probe, redirect check, image download, IIIF request, pHash, blurhash, screenshot, or media processing;
- no rights promotion, provider inference, policy inference, delivery decision, or positive authorization judgment;
- no PostgreSQL, DDL, migration, Docker, npm, Next.js, TypeScript, browser, frontend, API, fixture, or data import;
- no candidate JSON, SQLite, manifest, shard, QA asset, protected main, package, CI, or deployment modification;
- no SQLite write, integrity recheck, `VACUUM`, sidecar, or derived-to-canonical path;
- no commit, push, PR, merge, or deploy.

## Files, exit, and residual processes

| Output | Status |
| --- | --- |
| `05_LEGACY_VISUAL_DISPOSITION_BASELINE.tsv` | PASS; strict parse and aggregate reconciliation passed |
| `06_LEGACY_VISUAL_DISPOSITION_SUMMARY.json` | PASS; strict JSON parse and gate assertions passed |
| `agents/B3_LEGACY_VISUAL_DISPOSITION_RECEIPT.md` | PASS |

The candidate scanner and artifact-tool builder have exited. No B3-owned Node, Python, SQLite, browser, server, or generator process remains. Temporary scanner, aggregate JSON and preview files under `/private/tmp` are non-authoritative audit intermediates; no process owns them. The root task owns the final repository-wide residual-process scan, manifest/checksum generation, commit, and push.

**B3 result: PASS.**
