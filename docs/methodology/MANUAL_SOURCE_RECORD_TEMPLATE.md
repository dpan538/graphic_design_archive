# Manual Source Record Template v0

**Purpose:** Provide a strict template for manually entering the first real source records before any automated crawling or ingestion begins.

Manual records are the first controlled test of the database skeleton. They must prove that source, citation, rights, classification, and provenance can be captured without scraping.

## Rule

Do not enter a record unless the following minimum fields are known:

- source;
- source record URL;
- access date;
- title or label;
- capture method;
- rights state or rights note;
- citation text;
- at least one classification or historical node candidate.

If image rights are unclear, use `link_only` or `metadata_only`.

## Record Header

```yaml
record_status: candidate
capture_method: manual
entered_by:
entered_date:
review_status: pending
```

## Source

```yaml
source_id:
source_name:
source_record_url:
source_identifier:
access_date:
source_terms_review_id:
```

## Source Metadata As Found

These fields should preserve the source language and source wording where possible.

```yaml
source_title:
source_creator:
source_creator_role:
source_date_text:
source_place_text:
source_medium_text:
source_object_type:
source_dimensions:
source_holding_institution:
source_collection:
source_description:
source_rights_text:
source_rights_uri:
source_credit_line:
```

## Normalized Local Metadata

These fields are local normalized values and must remain separable from source metadata.

```yaml
normalized_title:
normalized_date_start:
normalized_date_end:
normalized_place:
normalized_creator_entity_id:
normalized_institution_entity_id:
normalized_medium_ids:
normalized_object_type_ids:
historical_node_ids:
movement_ids:
theme_terms:
language:
```

## Rights Review

```yaml
rights_state: unknown
image_use_policy: link_only
metadata_policy:
thumbnail_policy:
full_image_policy:
iiif_embed_policy:
local_copy_permitted: false
rights_basis:
rights_review_required: true
rights_reviewer:
rights_review_date:
rights_notes:
```

Allowed `rights_state` values:

- `metadata_open`
- `metadata_limited`
- `image_open`
- `image_embed_only`
- `thumbnail_only`
- `link_only`
- `unknown`
- `do_not_ingest`

## Citation

```yaml
citation_text:
citation_style:
citation_url:
access_date:
```

Minimum citation pattern:

```text
Source name, "Record title," source record URL, accessed YYYY-MM-DD.
```

## Image / Digital Surrogate

Do not fill these fields unless rights allow display or source-hosted embedding.

```yaml
source_image_url:
iiif_manifest_url:
iiif_canvas_id:
thumbnail_url:
image_rights_uri:
image_rights_label:
credit_line:
local_copy_permitted: false
```

## Classification

Each classification must identify its basis.

```yaml
classifications:
  - classification_type:
    classification_value:
    source: source_metadata | controlled_vocabulary | editorial_judgment
    confidence: high | medium | low | unknown
    reviewer:
    note:
```

Examples:

```yaml
classifications:
  - classification_type: historical_node
    classification_value: HN008
    source: editorial_judgment
    confidence: medium
    reviewer:
    note: Associated with Bauhaus/New Typography node because source describes Bauhaus publication context.
```

## Relations

Do not create relation assertions unless evidence is explicit.

```yaml
relations:
  - subject_entity_id:
    predicate:
    object_entity_id:
    evidence_source_record_url:
    citation_id:
    assertion_type: source_statement | editorial_inference
    confidence: high | medium | low | unknown
    note:
```

Important:

- `visually_resembles` is not evidence of influence.
- `created_by` requires explicit source evidence.
- `associated_with_movement` can be editorial, but must be marked as such.

## Uncertainty

```yaml
uncertainty_notes:
  - field:
    issue:
    display_note:
    internal_note:
```

Use uncertainty notes for:

- attributed creator;
- approximate date;
- conflicting source dates;
- unknown designer;
- ambiguous place;
- uncertain movement association;
- unclear rights status.

## Review Checklist

Before publication:

- [ ] Source exists in `source_registry`.
- [ ] Source URL works or stable source identifier is recorded.
- [ ] Access date is recorded.
- [ ] Citation text is present.
- [ ] Rights state is assigned.
- [ ] Image policy is assigned.
- [ ] Source metadata and normalized metadata are separated.
- [ ] At least one classification is present.
- [ ] Editorial inference is labeled as inference.
- [ ] No image is copied unless rights explicitly allow it.
- [ ] Record can be searched.
- [ ] Record has a workflow status.

## Publication Rule

A manual source record may become public only when:

- source review is approved;
- rights review is approved or safely link-only;
- citation is present;
- classification is reviewed;
- uncertainty notes are displayed where needed.
