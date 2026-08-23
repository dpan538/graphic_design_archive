# Context public projection specification

## Identity and source binding

The governed derived read layer is `trace-context-v1`; its DTO schema is `trace-context/v1`. It is built deterministically from the frozen v49 SQLite artifact, freeze receipt, authoritative eligibility ledger, governance policy, explanation registry, exception register, and public-ID/mapping rules. The manifest binds every input and governed payload by SHA-256 without implying that the v49 database changed.

## Artifacts

The server-only projection lives under `frontend/generated/trace-context-v1/` and contains the governance policy, explanation registry, exception register, public term registry, compact selected-record data, manifest, and checksum ledger. Generation writes deterministic UTF-8 JSON with no timestamp or environment-dependent field. `--check` performs two fresh rebuilds and requires byte identity with each other and the committed artifacts.

## Record model

Each of 7,995 eligible records contains safe root metadata and compact representation references. Each representation resolves a public term, explanation, publication state, epistemic role, and public provenance ID. Curated memberships and semantic edges are absent. Region is absent. Held rows, internal source identifiers, UUIDs, source URLs, private locators, and validation IDs are absent.

## Runtime boundary

A `server-only` reader validates the manifest and artifact integrity before building a compact by-ID lookup. It returns one frozen public DTO per lookup. The exhaustive Round 2 source index remains available for validation but is not imported by governed public runtime. The full projection and corpus marker are forbidden from client-reachable source graphs and production client chunks.
