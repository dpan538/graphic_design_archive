# Image Zone Rendering Rules v0

**Status:** Binding clarification for frontend and ingest planning.

Image zones are not image sizes and not a measure of image quality. They describe the image-presence state of a publication surface.

`IMG00` through `IMG03` apply when a page has an image frame. Their behavior is defined by copyright/display permission.

`IMG04` is different: it is an algorithm/layout signal that the page has no image frame at all.

Image size, crop, paper tier, and frame dimensions are controlled separately by sheet tier, layout ID, and template rules. Every image zone can have multiple sizes.

| Code | Rendering rule |
|------|----------------|
| `IMG00` | Image frame exists, but no source image is shown. Render an empty archive frame only: linework, shadow/hatch if needed, short rights/source text, and source link. Use when rights evidence is missing, infringement risk is high, terms are unclear, or protocol-sensitive material should not show image content. |
| `IMG01` | Image frame exists and renders a constrained thumbnail only when thumbnail display is explicitly permitted or terms-reviewed. Do not upscale or substitute a larger image. |
| `IMG02` | Image frame exists and renders an embedded/IIIF source-served image only when embed/IIIF use is terms-reviewed and item-level rights do not block display. Store source/manifest/credit evidence. |
| `IMG03` | Image frame exists and renders an open image only when item-level OA/CC0/PD/open-license evidence is recorded. Credit/license/source must remain visible. |
| `IMG04` | No image frame. Pure text page, appendix page, continuation page, citation page, registry page, or other page whose layout intentionally has no image area. This is a script/template signal, not a copyright level. |

## Default

Unknown image rights default to `IMG00`.

`IMG00` means:

- the record is still complete as an archive record;
- the image frame stays in the template;
- the visual area is intentionally empty of the source image;
- the frame may contain only neutral linework/shadow, rights text, and a source action;
- frontend must not infer display permission from a raw image URL.

## IMG04

`IMG04` is different from `IMG00`.

`IMG00` has an image frame but no image content. `IMG04` has no image frame at all.

Use `IMG04` for pure text pages, especially second or later pages of a record where the first sheet may contain image/name/category information but continuation pages contain only tables, citations, relations, notes, or textual appendices.

Scripts should treat `IMG04` as `has_image_frame = false`.

## Separation of Concerns

Image zone controls image-presence state.

Image size and frame dimensions are controlled by the paper template, sheet tier, and layout ID. The same image zone can appear in different fixed paper sizes, but it must obey the same rendering rule.
