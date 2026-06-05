# Rights-First Crawler Decision Engine v0

Date: 2026-06-05

This document translates the proposed advanced crawler ideas into project
constraints. The goal is not to make image acquisition more aggressive. The
goal is to make every crawler decide image state before storing pixels, and to
preserve a reviewable evidence trail for `IMG00` through `IMG04`.

## Core Rule

No crawler may write image binary data to the repository unless the item has
explicit `IMG03` evidence at item level.

The crawler may store:

- source URL;
- source identifier;
- source title/date/creator/medium/place;
- source rights text;
- license URI or rights-statement URI;
- IIIF manifest URL;
- source-hosted viewer URL;
- thumbnail URL as a remote pointer;
- parser status;
- decision reason.

The crawler must not store:

- full image pixels for `IMG00`, `IMG01`, `IMG02`, or `IMG04`;
- local screenshots used as substitute evidence;
- generated substitute images;
- visual surrogates for missing images;
- raw unredacted HTML/JSON that may contain API keys, tokens, or private
  tracking strings.

## IMG State Ladder

1. Decide whether the surface expects an image.
2. If no image is expected, use `IMG04`.
3. If a visual object exists but rights are unclear, use `IMG00`.
4. If source policy explicitly permits only controlled thumbnail display, use
   `IMG01`.
5. If a source-hosted viewer, embed, or IIIF manifest exists but local display
   rights are not explicit, use `IMG02`.
6. If item-level rights explicitly allow local display/reuse, use `IMG03`.

`IMG04` is not parser failure. Parser failure for a visual object remains
`IMG00` with an internal parser diagnostic.

## Evidence Hierarchy

Evidence should be evaluated in this order:

| Level | Evidence | May upgrade to IMG03? |
|---|---|---|
| 1 | item-level license URI, rights URI, or explicit open/public-domain statement | Yes |
| 2 | source-level policy registry with record-level rights field | Only when item-level evidence also confirms it |
| 3 | source-hosted viewer, IIIF manifest, embed, or official preview service | No; usually `IMG02` |
| 4 | JSON-LD, Open Graph image, sitemap, robots, page metadata | No; discovery only |
| 5 | visible copyright text, watermark, CC logo detected by OCR/CV | No; downgrade or review signal only |
| 6 | LLM summary of Terms of Use | No; review signal only |
| 7 | pHash/CLIP similarity to an open image elsewhere | No; candidate source-discovery only |
| 8 | IPFS/NFT/Wayback/decentralized trace | No; provenance/discovery signal only |

The only automatic positive rights transition to `IMG03` is explicit
item-level open evidence. All other signals can route to review, source
registry entries, or `IMG00`/`IMG02`.

## Advanced Modules: Allowed Use

### IIIF Discovery

Allowed:

- Parse manifest URLs from HTML `<link>` headers, JSON-LD, API payloads, and
  known IIIF collection structures.
- Store manifest URL and source viewer URL.
- Treat manifest availability as `IMG02` unless the manifest also carries
  explicit open rights.

Not allowed:

- Using the IIIF image service URL as proof that local display is permitted.
- Downloading full canvases before rights decision.

### JSON-LD / OpenGraph Parsing

Allowed:

- Extract `ImageObject`, `license`, `creator`, `datePublished`,
  `sameAs`, and source identifiers.
- Use these fields as structured evidence or review hints.

Not allowed:

- Treating `og:image` as display permission.
- Promoting platform preview images to local archive images.

### Headless Browser Rendering

Allowed:

- Use Playwright/browser rendering to discover final source URLs, JSON payloads,
  visible rights text, viewer links, and JavaScript-rendered metadata.
- Store only text/metadata/link evidence unless rights state is already
  `IMG03`.

Not allowed:

- Screenshotting source pages as substitute images.
- Capturing canvas pixels for `IMG00`, `IMG01`, or `IMG02`.

### Visual Rights Detection

Allowed:

- OCR or CV may detect watermarks, copyright symbols, copyright lines, or
  visible CC badges.
- These signals may downgrade to `IMG00` or create a review note.

Not allowed:

- A detected CC logo cannot by itself upgrade an image to `IMG03`. The crawler
  must find the linked license and item-level source context.

### Terms-of-Use NLP

Allowed:

- A local model may summarize ToS text into a review queue.
- The result may propose a source-policy entry with `needs_human_review=true`.

Not allowed:

- LLM ToS interpretation cannot become legal proof.
- It cannot set `source_terms_allow_thumbnail=true` without human/source
  registry confirmation.

### Similar Open Image Search

Allowed:

- pHash/CLIP similarity may find candidate Wikimedia Commons, museum, or
  public-domain records.
- Similarity may create `possibly_same_as` or source-discovery candidates.

Not allowed:

- Similarity cannot prove same work, authorship, influence, or rights.
- It cannot replace source-specific image rights.

## Required Capture Fields

Each crawler should populate or leave explicit blanks for:

```text
image_presence_code
image_expectation
parser_status
image_frame_behavior
display_mode
image_url_detected
thumbnail_url
iiif_manifest_url
source_viewer_url
license_uri
rights_uri
rights_basis
rights_text
rights_evidence_url
rights_decision_reason
rights_evidence_level
rights_review_required
local_copy_permitted
source_terms_policy_id
source_terms_review_required
discovery_signals
raw_json_path
access_date
```

The current helper for this is:

```text
scripts/rights_decision_engine.py
```

Existing capture scripts can continue using their local `image_fields()`
helpers, but new crawlers should call `decide_image_state()` first and then
write compatible CSV fields from `ImageDecision.capture_fields()`.

## Production Modules

The current production-safe helpers are:

```text
scripts/rights_decision_engine.py
scripts/source_policy_registry.py
scripts/iiif_discovery.py
scripts/discovery_signal_policy.py
```

`rights_decision_engine.py` is the only component that should assign final
`IMG00`-`IMG04` values for new crawlers. `source_policy_registry.py` reads the
project source registry and only returns `IMG01`-eligible thumbnail evidence
when the policy has been explicitly reviewed. `iiif_discovery.py` may discover
a source-hosted IIIF manifest, but that result is display-route evidence only
and normally supports `IMG02`, not reuse. `discovery_signal_policy.py` encodes
which CV/OCR/LLM/pHash/Wayback signals are allowed to downgrade, queue review,
or discover related records; none of those signals may upgrade an image state.

Do not add broad domain allowlists such as `flickr.com`, `unsplash.com`, or
`commons.wikimedia.org` directly to crawler code. Even when a platform often
contains open material, the crawler must still preserve item-level evidence and
source-specific context. A domain match can create a review hint, but it is not
an archive rights decision.

## Source Policy Registry Direction

The project should add a small source-policy registry before treating any
source as `IMG01` by default. The registry should include:

```text
source_id
domain
policy_url
thumbnail_allowed
local_copy_allowed
iiif_allowed
open_license_scope
requires_item_level_rights
protocol_sensitive
reviewed_by
reviewed_at
review_note
```

Until this registry exists and is reviewed, unknown source thumbnails remain
`IMG00` or `IMG02`, not `IMG01`.

For this project, `manual_review` means "review still required"; it is not an
approval state. Automatic `IMG01` requires an explicit reviewed-policy state
and a clear `thumbnail_allowed=yes` field in the source registry. If
`record_level_rights_required=yes`, source-level policy alone is insufficient.

## Secret Safety

All raw payload capture must pass:

```text
scripts/audit_secret_patterns.py
```

before a GitHub push. Third-party public HTML can contain token-like strings;
the project must redact before committing.

## Frontend Contract Consequence

- `IMG00`: render an empty rights/source frame.
- `IMG01`: render only constrained thumbnail behavior.
- `IMG02`: render source-hosted viewer/source-return behavior.
- `IMG03`: render open image with credit/license/source return.
- `IMG04`: render no image bay at all.

If frontend templates reserve an image frame for `IMG04`, that is a violation
of the data contract, not a data-layer permission problem.
