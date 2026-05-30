# Graphic Design Archive

A rights-aware archive index and research framework for modern graphic design history.

The project does not attempt to replace original archives or publish a single historical narrative. It organizes distributed source records, texts, designers, institutions, media, regions, movements, themes, rights notes, and source links into a static, inspectable archive-box interface.

## Current Structure

- `frontend/` — Next.js archive-box public interface prototype.
- `data/` — normalized seed data, capture CSVs, raw capture snapshots, source registry, and SQLite snapshot.
- `generated/` — generated public surface payloads consumed by the frontend.
- `db/` — SQL skeleton, read models, validation queries, and schema references.
- `scripts/` — capture, normalization, generation, validation, and data export scripts.
- `docs/` — methodology, system contracts, frontend contracts, capture notes, and research reviews.
- `reports/deep-research/` — source Deep Research outputs and generated `.docx` research reports.
- `prompts/` — Deep Research prompts used during framework development.
- `PROJECT_LOG.md` — running project log and collaboration notes.

## Frontend

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

The current frontend payload is generated statically at:

- `generated/public_surfaces_v1.json`
- `frontend/src/data/public_surface_mock_v0.json`
- `frontend/public/data/public_surface_mock_v0.json`

## Current Research Rules

- Public folders are filter views: `region`, `theme`, `medium`, and `movement`.
- Time remains the sorting axis.
- `IMG00` means image evidence exists or is expected, but the project should render an empty rights-aware image frame.
- `IMG01` / `IMG02` / `IMG03` indicate increasingly displayable image states.
- `IMG04` is reserved for genuinely no-image text, appendix, bibliography, authority, or context pages.
- Parser failure is not an image state.
- Main sheets, cards, and appendices must remain visually and semantically distinct.

## Repository Status

This repository currently contains the research framework, database skeleton, capture scripts, generated payloads, and the first static frontend prototype. The dataset is not final publication data.
