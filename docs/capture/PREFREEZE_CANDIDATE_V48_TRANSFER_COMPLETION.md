# Prefreeze candidate v48 — supervised main transfer completion

## Outcome and boundary

The v48 candidate freeze was transferred to `origin/main` in four ordered data
batches and independently read back before this completion receipt was
created. It is frozen for TRACE visualization and interface validation; it is
**not** the official public-release layer. The active total remains 15,923,
which is 4,077 below the minimum 20,000-object target.

The pre-existing v46/main history through `7ef26d6` was not overwritten,
rebased or rewritten. Every push was a normal fast-forward; no force-push was
used.

## Frozen identity

- Isolated branch receipt: `f2cf492b480139776ae674d5c26ccfd845e45e45`.
- Freeze commit: `d592566`.
- Source data/audit commit: `1d919fb`.
- Candidate JSON: 190,067,852 bytes,
  `b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48`.
- SQLite snapshot: 421,801,984 bytes,
  `ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e`.
- Transfer manifest: 65 declared files, 613,077,245 bytes, two LFS files;
  SHA-256 `865358db84c15d960b3535969a32521c0ffec177f7455d21db86cd131f787d5b`.
- The manifest JSON, CSV and freeze receipt are three self-referential control
  artifacts outside the manifest's own file hash list: 36,487 bytes. Total
  transferred before this completion receipt: 68 files, 613,113,732 bytes.

## Ordered main batches

| Batch | Commit | Files | Content |
| --- | --- | ---: | --- |
| A | `b243a34` | 16 | freeze contract, builders, audit, manifest and freeze receipts |
| B | `d83204b` | 1 | canonical v48 JSON through Git LFS |
| C | `ecfeb93` | 1 | frozen v48 SQLite through Git LFS |
| D | `5e7a478` | 50 | selected AIC/LOC evidence and saved validation artifacts |
| E | this commit | 2 | remote-verification JSON and this completion receipt |

Before each next batch, a remote `main` readback confirmed the preceding
commit. Batch D was not started until the remote SQLite content hash and SQL
gates passed.

## Independent remote readback

A fresh shallow clone of `origin/main` retrieved both current v48 LFS payloads
and verified all 65 manifest-listed files:

- Manifest hash mismatches: 0.
- SQLite `PRAGMA integrity_check`: `ok`.
- Active objects: 15,923.
- Active unresolved geography: 0.
- Active authority-uncertain leakage: 0.
- Active TRACE unlinked: 0.
- Historical `influenced_by` edges: 0.
- LOC `TRB167 associated_with_place` repair edges: 18.
- Count-isolated TRACE adjunct search documents: 11.
- 200-object audit: 200 pass, 0 fail.
- Saved independent freeze gate: 55 PASS, 0 HOLD.

The machine-readable receipt is
`generated/prefreeze_candidate_v48_remote_verification.json`.

## Evidence and exclusion boundary

The main transfer includes the exact 12 committed v47 AIC evidence payloads
and 18 committed v48 LOC item responses used by the candidate. It excludes the
uncommitted DigitalNZ, Cooper Hewitt, Smithsonian, Norway, AIC and LOC
exploration files in the working data branch. It also excludes the derived v47
candidate JSON and SQLite intermediate snapshots; their branch lineage remains
available on `codex/v47-data-expansion`, while main contains only the canonical
v48 JSON and its read-only query snapshot.

The 18 geography repairs are limited to official object-level LOC
`item.place[].title` evidence. Repository location, search terms and creator
nationality are not object geography. The 11 photography/printmaking adjuncts
remain `countEligible=false`; auxiliary association does not become historical
influence. AIC IIIF URLs that failed Cloudflare validation remain evidence
metadata only and are not active image display routes.

## Immutability rule

The v48 JSON and SQLite files are frozen. Further data work must create a new
candidate version and regenerate all gates, hashes and transfer records. TRACE
visualization may read these files but must not modify them or collapse active,
review/hold, authority-uncertain and auxiliary layers.
