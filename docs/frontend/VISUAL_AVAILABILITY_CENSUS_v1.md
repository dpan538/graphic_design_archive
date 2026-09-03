# Visual Availability Census v1 — the 7,995 public records of v49

Date: 2026-09-03 · Release: `v49-api-contract-fresh-c` · Artifacts:
`frontend/generated/visual-availability-v49/` (`endpoint-verification.json`,
`census.json`, `manifest.json`) · Scripts: `npm run verify:visual-endpoints`,
`npm run generate:visual-availability`, `npm run verify:visual-availability`.

Why: before the Index's eligibility is adjusted any further, the question
that decides whether MGDA is a visually readable archive had to be answered
with evidence — how many public records can actually be remote-rendered on an
Object page once policy, rights and the endpoint are checked. The answer is
not 0 (the v49 visual registry), not 155 (the Search `REMOTE_IMAGE` label),
and not 7,370 (the legacy IMG03 candidates).

## Four statuses, kept apart

```
PUBLIC STATUS     public / held                       — the Search v2 projection
READING STATUS    reader-facing / record-only         — reader-eligibility projection (§3b)
VISUAL STATUS     displayable / remote candidate / source-viewer-only / link only / citation only / no route — this census
EVIDENCE STATUS   source verified / …                 — trace.tier (every public record: source_verified)
```

None of these implies another. *Affiches d'Angers* (Gallica): public · yes ·
reader-facing · yes · visual · source-viewer-only · source verified · yes.
*O1167144* (V&A): public · yes · reader-facing · **no** (record-only: its title
is the V&A system number) · visual · source-viewer-only · source verified · yes.
Index eligibility is "meaningful object identity + sufficient reader-facing
content"; visual availability is a separate dimension and never an eligibility
criterion.

## The census

| VISUAL STATUS | public | of which reader-facing |
|---|---:|---:|
| `MGDA_DISPLAYABLE_VISUAL` — listed in the v49 visual registry | **0** | 0 |
| `REMOTE_VISUAL_CANDIDATE_VERIFIED` — `REMOTE_IMAGE`, endpoint returns an image | **128** | 116 |
| `REMOTE_VISUAL_CANDIDATE_UNVERIFIED` — `REMOTE_IMAGE`, endpoint refused / rate-limited / missing | 27 | 27 |
| `SOURCE_VIEWER_AVAILABLE` — a verified source record page (`View visual at source ↗`) | 7,763 | 5,203 |
| `SOURCE_LINK_ONLY` | 27 | 27 |
| `CITATION_ONLY` | 50 | 50 |
| `NO_VALID_VISUAL_ROUTE` | 0 | 0 |
| **Total** | **7,995** | **5,423** |

The number the redesign can plan around today is **128 verified remote-visual
candidates** — a pool, not a permission. Every one of them still passes
through the promotion gate below before it becomes `MGDA_DISPLAYABLE_VISUAL`,
and that decision belongs to the visual registry, not to the frontend.

## Priority 1 — the 155 `REMOTE_IMAGE` records, one by one

Endpoint verification: HEAD, then GET with `Range: bytes=0-0` where HEAD is
refused; 20 s timeout; a second pass one request at a time with a browser-like
agent for everything that failed the first pass (`endpoint-verification.json`
carries both passes and their dates).

| host (source) | records | endpoint OK | item rights reviewed | attribution recorded | image state | gate result |
|---|---:|---:|---:|---:|---|---|
| `framemark.vam.ac.uk` (V&A Collections API) | 82 | 82 | 0 | 82 | IMG02 | endpoint passes; **blocked at item-level rights** — "image presence is not reuse permission"; `rightsReviewed=false` on every record |
| `ms01.nasjonalmuseet.no` (Nasjonalmuseet / DigitaltMuseum) | 41 | 40 | 41 | 41 | IMG03 | 40 pass every recorded gate — **pending the registry** (per-item licence and attribution to be confirmed); 1 × 404 |
| `www.artic.edu` (Art Institute of Chicago API) | 25 | 0 | 25 | 25 | IMG03 | **blocked at the endpoint** — 403 on both passes; remote embedding is not available as recorded ("IIIF identifiers alone do not authorize display") |
| `upload.wikimedia.org` (Commons, LOC-derived) | 7 | 6 | 7 | 7 | IMG03 | 6 pass every recorded gate — pending the registry; attribution + source link required; 1 × 429 (rate-limited) |

Of the 155, 12 are record-only (V&A records titled by system number) — they
would never appear in the Index even if displayable.

Gate, in order: endpoint works → provider terms recorded → item-level rights
reviewed → attribution recorded → **registry listing** (`MGDA_DISPLAYABLE`).
The first four are evidence the census can hold; the fifth is a decision.

## Priority 2 — legacy IMG03 ∩ public ∩ reader-facing

The legacy pool of 7,370 IMG03 open-image candidates intersects the v49
public projection in **73 records** (all reader-facing, all already inside
the 155 above: Nasjonalmuseet 41, AIC 25, Commons 7). The other 7,297 are
HELD. There is no larger candidate pool hiding behind the 155 in this release;
enlarging it means promoting held records, which is a release decision.

## Priority 3 — `SOURCE_VIEWER` (7,763)

Every one of these has a verified source record URL. Whatever pixel-embedding
turns out to permit, an Object page for these is never "dead": it carries a
`View visual at source ↗` route. Object pages already say "Held by [source].
No image is displayed for any object in this release"; the link itself is not
yet in the public projection (the Search v2 DTO carries no URL) and is the
next field to project.

## Count scope

The Index's counts are bound to the `INDEX_ELIGIBLE` projection (5,423; the
filter's 5,203 / 143 / 77). The census counts above are the public
population (7,995; 7,763 / 155 / 50 / 27). They are two series and are never
shown together as one.

## What the Index can say now, and later

Now — interim labels on a "Visual access" filter (shipped 2026-09-03, drawer
and mobile sheet): **All · Viewable at source · Remote visual candidate ·
Citation / link only**. These map to the Search delivery state and make no
claim that MGDA has an image. Not final user copy.

Later, once the visual registry exists — **Visual: All objects · Visual
available · Source view only**, where "Visual available" is strictly
`MGDA_DISPLAYABLE_VISUAL = true` and "Source view only" is "MGDA cannot
render, but a verified source viewer exists". Never "Has image".

## Sources of the counts

Governed fields read: `image.state` (IMG00–IMG04, presence only — never a
rights level), `rights.state`, `rights.displayPolicy`, `reviewGates.rightsReviewed`,
`image.licenseLabel`, `image.credit`, `sourceUrl`, `trace.tier`; the Search v2
delivery state; the reader-eligibility projection; the dated endpoint
verification. The census decides nothing about rights.
