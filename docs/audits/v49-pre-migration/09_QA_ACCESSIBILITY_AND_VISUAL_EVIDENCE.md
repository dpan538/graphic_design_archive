# A9 — QA, accessibility, and visual-evidence audit

## Audit disposition

| Field | Result |
|---|---|
| Audit package | A9 |
| Scope status | **PARTIAL** |
| File-level metadata coverage | **COMPLETE — 60/60 files** |
| Byte-duplicate coverage | **COMPLETE — SHA-256 over 60/60 files** |
| Subjective pixel/content review | **NOT PERFORMED** |
| Third-party pixel-rights determination | **HOLD_UNKNOWN** |
| Accessibility acceptance evidence | **FAIL / not sufficient for promotion** |
| Recovery reference | `0404c7f96f9189f576c4c5b1368061e4082e436b` |

The 60 tracked files are useful historical prototype evidence, but they are not a
release-grade QA evidence set. The byte inventory is complete. The overall package
is `PARTIAL` because no capture manifest, checksum sidecar, scenario assertions,
accessibility evidence, or pixel-provenance/rights record exists, and the permitted
scope did not include subjective per-image visual review.

This result must not be read as a claim that any third-party image is or is not
present. File signatures and filenames cannot establish that fact.

## Scope and boundaries

In scope:

- every file under `docs/qa/screenshots/`;
- actual MIME/signature, filename extension, byte size, dimensions, color-profile
  metadata, Git state, and byte-identical duplication;
- explicit before/after naming and mobile/desktop dimension consistency;
- presence of a screenshot manifest and checksum ledger;
- evidence coverage for keyboard, screen reader, reduced motion, touch/swipe,
  scrolling, source drawer, Search, map/geography, error states, typography,
  color, focus, and contrast;
- whether the available metadata can prove third-party visual provenance or rights.

### Actions explicitly not performed

- browser startup or browser automation;
- new screenshots, screenshot regeneration, or subjective per-frame visual review;
- image download, proxying, re-encoding, pHash, blurhash, OCR, or image-derived
  fingerprint generation;
- modification, deletion, or renaming of any existing QA file;
- frontend, data, package, CI, deployment, database, shard, manifest, or frozen-v48
  changes;
- keyboard, assistive-technology, gesture, color-contrast, or runtime test execution.

## Evidence commands

Commands were run from
`/Users/jarlgiovanni/Desktop/modern_GD_history_v49_data_platform`. They are
read-only except for writing this report.

```sh
find docs/qa -maxdepth 2 -type f -print | LC_ALL=C sort
find docs/qa -maxdepth 2 -type f -print | wc -l
/usr/bin/file --mime-type docs/qa/screenshots/*
/usr/bin/file docs/qa/screenshots/*
/usr/bin/sips -g pixelWidth -g pixelHeight docs/qa/screenshots/*
/usr/bin/sips -g format -g space -g profile docs/qa/screenshots/*
find docs/qa/screenshots -maxdepth 1 -type f -exec stat -f '%z %N' {} \;
shasum -a 256 docs/qa/screenshots/*
git ls-files docs/qa
git status --porcelain=v1 -- docs/qa
git ls-tree -r --name-only 0404c7f96f9189f576c4c5b1368061e4082e436b -- docs/qa
git diff --name-status 0404c7f96f9189f576c4c5b1368061e4082e436b..HEAD -- docs/qa
git log --oneline --decorate -- docs/qa
git grep -n -i -E 'docs/qa|qa/screenshots|screenshot manifest|screenshot checksum' -- ':!docs/qa/screenshots/*'
find docs/qa -type f \( -iname '*manifest*' -o -iname '*checksum*' -o -iname '*.md' -o -iname '*.json' -o -iname '*.sha256' \) -print
ps -axo pid=,ppid=,etime=,command=
```

No command printed an environment variable or credential value.

## Measured inventory

### Repository and storage facts

- Files: **60**, all regular tracked files and all clean at audit time.
- Current QA tree contents: **60 images and no other file**.
- Origin: all 60 paths first appear in checkpoint `0404c7f`; `git log -- docs/qa`
  reports that checkpoint only.
- Drift: `git diff 0404c7f..HEAD -- docs/qa` is empty.
- Total bytes: **2,860,448 B** (about 2.73 MiB).
- Smallest file: **5,744 B**, `round5-mobile-medium-max-b.png`.
- Largest file: **137,790 B**, `round8-desktop-global-atlas.jpg`.
- Git attributes: no special attribute or LFS rule was returned for representative
  `.png` and `.jpg` paths. Repository-wide LFS governance is owned by A1.
- Source/operator/owner, capture tool, route, browser, operating system, DPR,
  capture time, expected assertion, data release, and visual-registry identity are
  not recorded in `docs/qa`.

### Round, extension, signature, and dimensions

All 60 files have a JPEG/JFIF signature, report `image/jpeg`, use baseline 8-bit
three-component JPEG, and report RGB with the `sRGB IEC61966-2.1` profile.

| Round | Files | Filename extension | Actual MIME | Dimensions | Unique within round |
|---|---:|---|---|---|---:|
| 5 | 4 | 4 `.png` | 4 `image/jpeg` | 4 × 390×844 | 4 |
| 6 | 6 | 6 `.png` | 6 `image/jpeg` | 6 × 390×844 | 6 |
| 7 | 3 | 3 `.png` | 3 `image/jpeg` | 3 × 390×844 | 3 |
| 8 | 14 | 14 `.jpg` | 14 `image/jpeg` | 10 × 390×844; 4 × 1440×1000 | 14 |
| 9 | 12 | 12 `.jpg` | 12 `image/jpeg` | 12 × 390×844 | 12 |
| 10 | 8 | 8 `.jpg` | 8 `image/jpeg` | 8 × 390×844 | 7 |
| 11 | 8 | 8 `.png` | 8 `image/jpeg` | 8 × 390×844 | 8 |
| 12 | 5 | 5 `.png` | 5 `image/jpeg` | 4 × 390×844; 1 × 1280×720 | 5 |
| **Total** | **60** | **34 `.jpg`; 26 `.png`** | **60 `image/jpeg`** | **55 × 390×844; 4 × 1440×1000; 1 × 1280×720** | — |

Consequences:

1. Every `.png` path is mislabeled: **26 extension/MIME mismatches**.
2. Of 56 filenames containing `-mobile-`, 55 are 390×844. The exception is
   `docs/qa/screenshots/round12-mobile-region-wheel-ready.png`, which is 1280×720.
3. The collection represents one valid portrait-mobile raster size and one desktop
   raster size. It does not establish small-phone, tablet, landscape, zoom, high
   contrast, or multiple-DPR behavior.
4. JFIF density metadata is `1x1`; it is not a browser DPR receipt.

### Byte-identical groups

The 60 paths resolve to **50 unique SHA-256 values**. There are **7 duplicate
groups**, involving 17 filenames and therefore **10 redundant byte copies**.

| SHA-256 | Count | Paths | Audit interpretation |
|---|---:|---|---|
| `a00cb215320f8ae28d46e340cfd2d64f6e02ce29fbd94c1322ade1dc5514f98b` | 2 | `round10-mobile-global-atlas.jpg`; `round11-mobile-trace-atlas-ready.png` | Different round/semantic label, identical bytes |
| `8f60b66f0696a8dfbba9f83cb4687e4466cd6e9257e76c14b1cac5da42fe38aa` | 2 | `round8-mobile-trace-two-level-controls.jpg`; `round9-mobile-object-current.jpg` | Different semantic label, identical bytes |
| `8c584b485ebd27335e20512807f847fdd47c089e5afc880a316bce0ce9d36d0b` | 2 | `round11-mobile-trace-constellation-selected.png`; `round9-mobile-evidence-selected.jpg` | Different semantic label, identical bytes |
| `ae8fe8cda6d826c7f3dc6d26543371821e2f30a8700e5153b8b497fe50782468` | 4 | `round10-mobile-menu-icon-only.jpg`; `round7-mobile-icon-menu.png`; `round8-mobile-menu-icon-only.jpg`; `round9-mobile-menu-icon-only.jpg` | Cross-round reused frame |
| `c42ab56bff75c923bfa861fc342e8bd526b79e921a099a114cfda528c6a6d21a` | 2 | `round11-mobile-trace-constellation.png`; `round9-mobile-evidence-dots.jpg` | Different semantic label, identical bytes |
| `cbc8d5e8507824654458df3fe387e4bf2a59aa235f7746d210d0ef1cd7b280de` | 3 | `round10-mobile-root.jpg`; `round7-mobile-home-top-gap-fixed.png`; `round9-mobile-root-before-menu.jpg` | Cross-round reused frame |
| `6fcc12866e11d904f4694920c36ce6b7faefea5fab85c0251e70cddde30ef4aa` | 2 | `round10-mobile-region-stack-after-swipe.jpg`; `round10-mobile-region-stack-before-swipe.jpg` | Explicit before/after pair is byte-identical |

Only round 10 has an intra-round duplicate. All other duplicate relationships span
rounds. Exact equality is stronger than perceived similarity: the files contain
the same compressed byte sequence.

The explicit round-10 `before-swipe` and `after-swipe` files cannot prove that the
swipe changed state. They may document a failed/no-op gesture, a mislabeled frame,
or a reused capture; without a scenario receipt the cause is unknown.

No duplicate should be deleted solely from this table. Distinct filenames may be
the only surviving record of intended scenarios, even when the captured bytes are
the same. All have a Git recovery source, but semantic intent is not recoverable
from Git bytes alone.

## Manifest, checksum, and provenance findings

`docs/qa` contains no README, capture manifest, JSON/CSV ledger, checksum sidecar,
rights receipt, test assertion, or accessibility transcript. `git grep` finds no
tracked reference elsewhere that supplies those fields for these 60 paths.

The comprehensive audit's own `AUDIT_CHECKSUMS.sha256` can protect this report; it
does **not** retroactively make the screenshot corpus a governed QA release. A
release-grade screenshot manifest needs, per evidence item:

- immutable evidence ID, path, byte SHA-256, byte length, actual MIME, dimensions,
  and duplicate-group policy;
- source commit, application route, scenario/action, expected state, observed
  state, viewport, DPR, browser/tool version, OS, and capture timestamp;
- research release ID plus manifest SHA-256 and, independently, visual registry
  version plus registry SHA-256;
- whether external pixels are present; provider object/reference IDs; rights
  decision; allowed QA-storage purpose; attribution/required statement; review due;
  and takedown status;
- operator/reviewer identities and an explicit result (`PASS`, `FAIL`, or `HELD`).

Until such a record is reviewed, all 60 current images should be classified
`HOLD_UNKNOWN`, preserved unchanged, and excluded from release/freeze acceptance
evidence. After provenance resolution they can move to `ARCHIVE_READ_ONLY` or a
governed evidence release. They are not proven `GENERATED_REPRODUCIBLE`: the
capture inputs and environment are absent.

## Third-party visual and rights assessment

### Measured result: PARTIAL / HOLD_UNKNOWN

Neither JPEG metadata nor the repository tree records the source or rights of pixels
inside these composite screenshots. There is no evidence connecting a screenshot
to a `researchReleaseId`, `researchManifestSha256`, `visualRegistryVersion`,
`registrySha256`, provider object ID, delivery mode, or rights observation.

Therefore:

- the audit cannot assert that the images contain no third-party visual;
- the audit cannot assert that any contained visual was authorized for copying into
  Git, even if it was visible through an API, IIIF endpoint, redirect, or webpage;
- the images must not be used to infer `INLINE_ALLOWED` or `PROXY_ALLOWED`;
- unknown/missing/conflicting rights remain compatible only with `LINK_ONLY` or
  `CITATION_ONLY` at runtime, but that runtime rule does not itself authorize an
  already-captured composite screenshot;
- takedown and review-due decisions cannot be enforced because there is no
  screenshot-to-visual-reference crosswalk.

No subjective pixel inspection was performed under the A9 metadata-only boundary.
Even a subjective inspection would not establish legal authority; a provider and
rights receipt is required.

## Accessibility and interaction evidence matrix

Filename-token counts below are discovery aids, not accessibility assertions. A
still image generally cannot prove focus order, semantics, keyboard reachability,
screen-reader output, reduced-motion behavior, gesture handling, or scrolling.

| Requirement | Existing filename evidence | Readiness | Gap / required evidence |
|---|---|---|---|
| Keyboard | 0 files name keyboard or focus | **FAIL** | Tab order, skip links, activation, escape/close, focus return, visible focus, and trap tests with step receipts |
| Screen reader | 0 files name screen reader or ARIA; no transcript/tree | **FAIL** | Accessibility-tree snapshot and VoiceOver/NVDA-style task transcript with names, roles, states, live regions, and reading order |
| Reduced motion | 0 files | **FAIL** | `prefers-reduced-motion` scenario proving animations/transitions are removed or safely reduced |
| Touch / swipe | 5 filenames contain `swipe`/`swiped`, representing 4 unique byte frames because one before/after pair is identical | **PARTIAL** | Recorded action, start/end coordinates or semantic gesture, expected state change, observed state, and device/touch environment |
| Scroll | 0 filenames and no event/position receipt | **FAIL** | Page and nested-region scroll reachability, restoration, overscroll, sticky controls, and drawer-body scroll evidence |
| Source drawer | 0 files contain `source`; one `object-info-drawer` frame is not source-drawer proof | **FAIL** | Open/close, focus management, source/locator rendering, rights-held behavior, keyboard, touch, and scroll evidence |
| Search | 2 files (`icon-menu-search`, `search-ready`) | **PARTIAL** | Query/result/error/empty/loading states, keyboard and screen-reader behavior, stable route/URI, and data-release identity |
| Map / geography | 0 files contain `map`; 5 contain `atlas` (4 unique bytes), 1 `globe`, 1 `geography`, and 8 `region` | **PARTIAL** | Map semantics, non-pointer alternative, keyboard pan/zoom, textual equivalent, focus behavior, error/offline state, and rights-safe external visual behavior |
| Error states | 0 files | **FAIL** | Route/data/network/image/provider/rights-held failures and recovery actions |
| Typography | 0 files or receipts name font; no rendered-font inventory | **FAIL** | Loaded/fallback font evidence, text resize/reflow, minimum size, weight, line-height, and missing-font behavior |
| Color and contrast | 0 files or measurement receipts name color/contrast | **FAIL** | Token/source values plus measured text, icon, focus, and non-text contrast; high-contrast/forced-colors behavior |
| Responsive/mobile | 56 `mobile` filenames, but only 55 are the expected 390×844; no governed viewport matrix | **PARTIAL** | Small-phone, large-phone, tablet, portrait/landscape, zoom/reflow, safe-area, and multiple-DPR coverage |
| Object TRACE | 11 filenames contain `object`; 14 contain `trace` | **PARTIAL** | Scenario assertions linking rendered relation/claim state to a sealed release and proving semantic/nonvisual alternatives |

Additional limitations:

- There is no evidence of 200%/400% zoom, text-only zoom, reflow, forced colors,
  high contrast, localization, or long-label overflow.
- There is no test identity for pointer type, touch target size, hover-only content,
  gesture alternatives, or drag cancellation.
- `selected`, `ready`, and `current` in filenames are author labels, not observed
  assertions with a pass/fail oracle.
- The four desktop images all use 1440×1000; this is not a desktop viewport matrix.
- JPEG artifacts and a screenshot's sRGB profile cannot substitute for source color
  tokens or computed contrast measurements.

## Findings and priorities

| ID | Priority | Finding | Affected paths/state | Risk | Recommended action |
|---|---|---|---|---|---|
| A9-P0-01 | P0 | No pixel provenance or rights/capture receipt exists | All `docs/qa/screenshots/*`; rights and public-repository review | Unauthorized third-party pixels cannot be ruled out or taken down selectively | Keep all 60 as `HOLD_UNKNOWN`; perform provider/reference crosswalk and rights review before treating any image as publishable evidence |
| A9-P0-02 | P0 | No screenshot manifest, checksum sidecar, release/registry identity, or test oracle exists | QA freeze and machine-verifiable evidence | Frames cannot prove what release, route, state, or assertion they represent | Define and validate the evidence-manifest contract; bind each frame to both release identities and a reviewer outcome |
| A9-P0-03 | P0 | Core accessibility acceptance areas have no executable or semantic evidence | Frontend promotion/freeze, not physical DDL execution | A visually plausible UI could remain unusable by keyboard, screen reader, reduced-motion, or error-recovery users | Add a separate accessibility gate with keyboard, tree/transcript, reduced-motion, gesture, scroll, source-drawer, Search, map, error, font, and contrast receipts |
| A9-P1-01 | P1 | 26 `.png` paths contain JPEG bytes | Rounds 5, 6, 7, 11, and 12 | MIME serving, tooling, content negotiation, and human review can disagree | Preserve current evidence; plan governed rename/re-encode policy only after manifest/path-impact review. Do not re-encode historical bytes in place |
| A9-P1-02 | P1 | One mobile-named frame is 1280×720 | `round12-mobile-region-wheel-ready.png` | Mobile acceptance claim is misleading | Mark scenario invalid/held until capture context identifies whether the name or viewport is wrong |
| A9-P1-03 | P1 | Seven exact duplicate groups; before/after swipe is identical | 17 paths; especially round-10 pair | Scenario labels may overstate tested state transitions | Record duplicate groups in future manifest, hold the explicit before/after assertion, and recapture only in a later authorized QA phase |
| A9-P1-04 | P1 | No owner, retention rule, capture environment, route list, or acceptance matrix | Entire QA tree | Evidence cannot be maintained, retired, or reproduced responsibly | Assign owner/reviewer and retention status; make missing required fields fail closed |
| A9-P1-05 | P1 | Viewport and accessibility coverage is narrow or absent | QA acceptance | Regressions outside 390×844 and 1440×1000 can pass unnoticed | Establish a risk-based viewport/accessibility matrix separate from bulk visual capture |
| A9-P2-01 | P2 | Ten byte copies are storage-redundant | Duplicate groups | Minor Git size and review noise | Do not delete now; after provenance resolution, archive a canonical blob plus scenario-to-blob mapping or list explicit delete candidates with recovery references |

P0 findings block treating this collection as rights-cleared, freeze-ready, or
promotion-ready evidence. They do not assert that PostgreSQL has or has not been
implemented, and A9 alone does not decide engineering pre-DDL readiness.

## Proposed acceptance boundary for a future QA evidence release

A future QA package may pass only when all of the following are machine-checkable:

1. every evidence path exists and its actual MIME matches the manifest and filename;
2. byte size, dimensions, SHA-256, source commit, route, scenario, expected state,
   viewport, DPR, tool/browser, and reviewer result are present;
3. duplicate bytes are either prohibited or explicitly mapped to each intentional
   scenario; a before/after state-change assertion requires unequal, correctly
   contextualized evidence or a recorded expected no-op;
4. research release and visual registry identities are independently recorded;
5. every composite containing external pixels has a rights/provenance crosswalk and
   QA-storage decision, with takedown propagation;
6. keyboard, screen-reader, reduced-motion, touch, scroll, source-drawer, Search,
   map, and error-state gates have non-screenshot semantic/action receipts;
7. font loading/fallback and color/contrast measurements are recorded separately
   from raster screenshots;
8. checksums cover the final manifest and every referenced evidence file.

## Cleanup classification and deletion risk

| Scope | Current classification | Reason | Proposed action | Deletion risk |
|---|---|---|---|---|
| All 60 existing screenshots | `HOLD_UNKNOWN` | Provenance, rights, owner, scenario truth, and capture inputs are absent | Preserve unchanged; resolve manifest/rights/semantics, then move to `ARCHIVE_READ_ONLY` or governed evidence | **High**: removal can erase the only record of intended scenarios |
| Ten redundant byte copies | Remain `HOLD_UNKNOWN`; not yet `DELETE_CANDIDATE` | Byte duplication is proven, but scenario intent is not | Prepare scenario-to-hash mapping first; deletion may be proposed in a later cleanup task | **Medium/high** |
| Round-10 identical before/after pair | `HOLD_UNKNOWN` | Could be failed gesture evidence, mislabeled capture, or accidental copy | Mark acceptance assertion held; preserve both paths until reviewed | **High** |

No cleanup command was executed. The checkpoint provides byte recovery, but not the
missing semantic/provenance context.

## Process and non-action receipt

- A9 started no Node, Next, TypeScript, PostgreSQL, Docker, browser, screenshot,
  model, or data-generation process.
- All `file`, `sips`, `stat`, `shasum`, `find`, `git`, and process-inspection
  commands exited; A9 retained no PID or shell session.
- A residual process snapshot showed pre-existing processes that substantially
  predate A9: agent-browser PID 97877 (about 11 days), headless Chrome PID 5488
  (about 1 day), PostgreSQL PID 1554 (about 20 days), Docker vmnet helper PID 842
  (about 20 days), plus ordinary Chrome and Codex/ChatGPT Node processes. A9 did
  not start, inspect through, terminate, or otherwise use them. No `next` or `tsc`
  process was identified in the snapshot.
- No screenshot was opened in a browser, generated, modified, re-encoded, copied,
  downloaded, or deleted.
- No secret value was read or emitted.

## Readiness impact

| State | A9 conclusion |
|---|---|
| `AUDIT_COVERAGE: QA/accessibility` | **PARTIAL** — byte/metadata audit complete; subjective content and legal provenance unresolved |
| `QA_METADATA_AUDIT_COMPLETE` | `true` |
| `QA_VISUAL_SUBJECTIVE_REVIEW_COMPLETE` | `false` |
| `QA_RIGHTS_PROVENANCE_READY` | `false` |
| `QA_ACCESSIBILITY_EVIDENCE_READY` | `false` |
| `DATABASE_FREEZE_READY` | `false` from this evidence boundary |
| `FRONTEND_PROMOTION_READY` | `false` from this evidence boundary |

The next safe action is evidence governance, not deletion or recapture: define the
manifest, resolve rights/provenance, and establish an accessibility acceptance
matrix before any future authorized browser-based QA run.
