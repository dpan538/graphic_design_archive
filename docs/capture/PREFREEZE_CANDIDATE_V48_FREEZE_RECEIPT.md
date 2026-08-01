# Prefreeze candidate v48 — freeze receipt

- Frozen version: `v48`
- Freeze commit: `d592566` (`freeze v48 candidate baseline`)
- Source data commit: `1d919fb` (`repair v48 AIC display routes and add freeze audit`)
- Freeze date: `2026-08-01` (Australia/Brisbane)
- Active object count: `15,923`
- Remaining to minimum 20,000: `4,077`
- Candidate JSON SHA-256: `b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48`
- SQLite SHA-256: `ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e`
- Transfer manifest SHA-256: `865358db84c15d960b3535969a32521c0ffec177f7455d21db86cd131f787d5b`
- Transfer manifest CSV SHA-256: `694a60657077bcab8888c4a4ef1daf6059706e544606d4862e46c57dcf6ddc18`

## Gate receipt

- Independent freeze audit: 55 PASS, 0 HOLD.
- SQLite integrity: `ok`.
- Active unresolved geography: 0.
- Active authority-uncertain leakage: 0.
- Active TRACE unlinked: 0.
- Active objects without indexed TRACE edges: 0.
- Historical `influenced_by` edges: 0.
- Filename-extension titles: 0.
- Search object/title/region mismatches: 0.
- 200-object sample: 200 pass, 0 fail.
- LOC `item.place` repairs: 18 evidence-bounded rows and 18
  `associated_with_place` edges.
- AIC unstable direct display routes: 0; two active objects and 11 auxiliary
  items return to source pages.

## Isolated, not counted

- Authority-uncertain review/search layer: 4,425 records.
- AIC photography/printmaking TRACE auxiliary branch: 11 records.
- Auxiliary promotions: 0.
- Historical influence edges: 0.
- Uncommitted DigitalNZ, Cooper Hewitt, Smithsonian, Norway, AIC and LOC
  exploration files: excluded from the freeze and transfer manifest.

This receipt freezes a candidate/reference layer, not the official release.
The next data change must create a new candidate version. Neither the v48 JSON
nor its SQLite query snapshot may be modified in place.
