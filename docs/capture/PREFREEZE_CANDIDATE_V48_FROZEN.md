# Prefreeze candidate v48 — frozen TRACE-visualization baseline

## Freeze identity and status

- Version: `v48`
- Freeze date: `2026-08-01` (Australia/Brisbane)
- Source data commit: `1d919fb` (`repair v48 AIC display routes and add freeze audit`)
- Freeze commit: the commit containing this report and the versioned transfer manifest; its immutable Git ID is recorded by the following freeze receipt and by the supervised main-transfer completion receipt.
- State: candidate frozen for TRACE visualization and interface validation.
- Release status: **not the official public-release layer**.
- Active objects: **15,923**.
- Remaining to the minimum 20,000-object target: **4,077**.

No count, geography, authority, image or TRACE standard was relaxed to reduce
the gap. Any later data change must create a new candidate version; the v48
payload and SQLite snapshot must not be edited in place.

## Exact frozen payloads

| Role | Path | Bytes | SHA-256 | Git storage |
| --- | --- | ---: | --- | --- |
| Canonical candidate | `generated/public_surfaces_prefreeze_candidate_v48.json` | 190,067,852 | `b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48` | Git LFS |
| Read-only query snapshot | `data/prefreeze_candidate_v48.sqlite` | 421,801,984 | `ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e` | Git LFS |

The JSON is canonical for the v48 candidate. SQLite is a preprocessed search
and TRACE snapshot and cannot supersede or mutate the JSON.

## Quality and layer gates

- Independent freeze audit: **55/55 PASS**, 0 HOLD.
- SQLite `PRAGMA integrity_check`: `ok`.
- Active object count: 15,923 in both JSON and SQLite.
- Active unresolved geography: 0.
- Active authority-uncertain leakage: 0.
- Accepted TRACE coverage: 15,923 / 15,923 (100%).
- Active objects without indexed TRACE edges: 0.
- Orphan TRACE endpoints and broken object-edge references: 0.
- Historical `influenced_by` edges: 0.
- Titles ending in common image/document filename extensions: 0.
- Active search documents: 15,923; object/search title or region mismatches: 0.
- Saved 200-object audit: 200 rows, 200 `audit_status=pass`; all 18 v48 repairs are forced into the sample.

The authority-uncertain review layer remains visible and searchable as 4,425
count-isolated records. It is not merged with the active main layer.

## TRACE coverage and auxiliary media branch

All 15,923 active objects retain accepted TRACE state and indexed evidence
edges. The v47 auxiliary branch contains 11 documented photography or
printmaking records. Each has an official source page, explicit medium, object
year and object place; each is `countEligible=false`, remains searchable as a
TRACE adjunct, has zero promotions, and carries no `influenced_by` relation.
Future planar-animation material may enter only a new auxiliary candidate under
the same evidence contract.

## Geography and the 18 LOC repairs

The v48 geography change is limited to 18 previously unresolved active LOC
objects. Each repair is backed by a saved official LOC item response and the
object-level field `item.place[].title`; each adds one
`associated_with_place` edge in branch `TRB167`. The audit confirms the parent
and v48 active object sets are identical and that exactly these 18 surface IDs
changed `placeText`.

This evidence does not use the Library of Congress repository location,
capture search terms, collection co-occurrence, or creator nationality as
object geography. It does not create historical influence.

## Image routing, search and sample boundaries

The two active AIC additions and all 11 auxiliary AIC records use their stable
Art Institute object pages for return/display. Direct AIC IIIF URLs that
returned Cloudflare 403 remain evidence metadata only: active display URL fields
are null and the route is `source_viewer_only`. No image body was downloaded.

SQLite identifies `prefreeze_candidate_v48_sqlite_v1`, points to the exact v48
JSON, preserves 15,923 active search documents, and keeps the 11 auxiliary
TRACE documents and 4,425 authority-review documents outside the active count.

## Excluded working material and transfer rule

The current exploration worktree contains uncommitted DigitalNZ, Cooper
Hewitt, Smithsonian, Norway, AIC and LOC probe changes. None is part of the
freeze. The selected main-transfer package is enumerated, byte-sized and
SHA-256 hashed in
`generated/prefreeze_candidate_v48_transfer_manifest.json`; raw evidence is
included only for the 12 committed v47 AIC payloads and 18 committed v48 LOC
item responses used directly by this candidate.

Main transfer is ordered as A (contract/reproducibility), B (canonical JSON),
C (frozen SQLite), D (evidence/validation), then E (remote retrieval receipt).
Every batch must be pushed and independently read back before the next starts.
Any mismatch stops the sequence. Force-push and history rewriting are
prohibited.
