# Graphic Design Archive

A rights-aware archive index and research framework for modern graphic design history.

## Status

- Status: research prototype / public backup
- Dataset: seed and candidate data only
- Frontend: static archive-box prototype
- Images: rights-aware display states only
- Publication status: not final publication data

## Project Scope

Graphic Design Archive is a public archive index and research framework for organizing distributed material related to modern graphic design history. It connects source records, texts, designers, institutions, media, regions, movements, themes, rights notes, citations, and source links into a static, inspectable archive-box interface.

The project is a metadata, citation, and source-link layer. It is designed to point back to source institutions, archives, catalogues, publications, and stable URLs rather than locally absorbing or republishing their materials. The archive-box interface is a prototype for reading and testing this structure, not a declaration that the current records are complete or publication-ready.

## What This Project Is Not

- Not a museum collection
- Not an image gallery
- Not an inspiration board
- Not a textbook or course
- Not a replacement for source archives
- Not a claim of final scholarly authority
- Not a repository of locally copied copyrighted images

## Repository Structure

- `frontend/` - Next.js static archive-box interface prototype.
- `data/` - seed data, candidate data, source registry, rights strategy, capture summaries, staged source records, and related implementation data.
- `generated/` - generated public-surface payloads consumed by the frontend prototype.
- `db/` - schema, read models, validation queries, and database validation work.
- `scripts/` - capture, normalization, generation, validation, export, and audit scripts.
- `docs/` - methodology notes, system contracts, frontend contracts, capture notes, and review documents.
- `reports/deep-research/` - research reports and review material, where included.
- `prompts/` - research prompts used to develop and test the framework.
- `PROJECT_LOG.md` - implementation log and collaboration notes, not a public scholarly record.

## Frontend Quick Start

```bash
cd frontend
npm install
npm run dev -- -p 3000
```

Build check:

```bash
cd frontend
npm run build
```

The frontend consumes static generated payloads. The main prototype payloads currently include:

- `generated/public_surfaces_v1.json`
- `frontend/src/data/public_surface_mock_v0.json`
- `frontend/public/data/public_surface_mock_v0.json`

These payloads support interface testing and archive-box rendering. Their presence in the frontend does not mean the records are final, complete, or publication-ready.

## Data and Publication Status

The files in `data/`, `generated/`, and related prototype folders are implementation-stage materials. Seed files are implementation seeds. Source records may be candidates, drafts, fallback stubs, staged capture rows, generated summaries, or prototype views.

Candidate data should not be cited as final evidence unless each record has source terms review, rights review, field provenance, and citation review. Generated public-surface payloads are test and prototype outputs unless they are explicitly marked as publication-ready.

The repository may contain raw capture summaries or local reproducibility evidence for development. These materials exist to make the pipeline inspectable; they are not source mirrors and they do not imply permission to republish source material.

## Rights-Aware Image Policy

Image handling is governed by rights-aware display states:

- `IMG00`: image evidence exists or is expected, but the interface renders an empty rights-aware frame only. No source image, thumbnail, screenshot, preview, or local copy should be displayed.
- `IMG01`: a controlled thumbnail or limited display may be possible when source terms and project policy support it.
- `IMG02`: source-hosted viewer, IIIF, or similar source-return display is preferred; the project points users back to the source rather than taking possession of the image.
- `IMG03`: open or reusable image state based on explicit rights evidence, source metadata, or reviewed source terms.
- `IMG04`: genuine no-image text, appendix, bibliography, authority, or context page. It is not a failed image state.

Parser failure is not an image state. Failed capture, blocked access, missing parser support, or ambiguous rights should be recorded separately and should not be converted into `IMG04`.

Do not locally copy, scrape, or republish source images unless rights fields and source terms clearly permit it. When evidence is unclear, default to source links and rights-aware empty frames.

## Source and Citation Policy

Public records should point users back to source institutions, archives, catalogues, publications, or stable source URLs. The project should preserve provenance rather than collapse conflicting sources into unsupported certainty.

Interpretive text must be traceable to source records, reviewed references, or explicitly marked research notes. AI-generated or exploratory research text must not be treated as evidence by itself.

## Backup Boundary

This repository is a public code and research backup, not the sole preservation copy and not a publication release. GitHub backup does not equal rights clearance, source permission, scholarly publication, or institutional approval.

Do not commit secrets, credentials, private notes, browser sessions, cookies, API keys, local tokens, or private machine paths. Do not commit large local caches, `node_modules`, `.next` builds, local model caches, temporary browser downloads, or downloaded copyrighted source files.

## License / Reuse

License and reuse terms are not finalized. Code, data, documentation, and visual assets may require separate licensing decisions.

If a license is later added, distinguish between:

- Code license
- Data license
- Documentation license
- Third-party source and image rights

## Suggested Citation

For now, cite this repository as a research prototype, not as a completed archive or authoritative dataset.

Suggested form:

> Dai Pan / dpan538. `Graphic Design Archive`. Research prototype and public backup for a rights-aware graphic design history archive index. GitHub repository.

## Contributing

External contributions are not currently open unless explicitly invited. Issues or pull requests may be used for technical corrections, source corrections, or documentation improvements later.

Do not submit copyrighted images, copied archive materials, private research notes, credentials, or source files that cannot be redistributed.

## Maintenance Note

Maintainer: Dai / dpan538.

This is an active research and development repository. Major changes should update `README.md`, `data/README.md`, and `PROJECT_LOG.md` consistently.
