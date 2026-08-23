# TRACE v49 Round 4 executive decision

## Outcome at the documentation checkpoint

Round 4 closes the research and governance questions needed for a governed Spacetime functional foundation. Context v1 also passes its production-like runtime rehearsal without reopening Context semantics.

| Area | Decision |
| --- | --- |
| Context runtime | `PASS`; pre-generated, preverified, read-only at runtime |
| Context engineering logic | `FROZEN` |
| Spacetime geography governance | `READY` on the generated projection candidate |
| Spacetime temporal governance | `READY` on the generated projection candidate |
| GIS geometry | Natural Earth Admin 0 Countries 5.1.1, 50m, committed immutable asset |
| Default projection | Equal Earth |
| Alternative projection | Natural Earth 1 |
| World Atlas | `REPLACE_WITH_PINNED_NATURAL_EARTH_ARTIFACT`; package retention `LEGACY_AND_TEST_REFERENCE_ONLY` |
| Dot density | Deterministic aggregate-only projected-grid method |
| Texture | Reject Texture.js for runtime; retain the deterministic native SVG-pattern helper |
| Public read model | Three governed resources: periods, one-period atlas, selected-geography record page |
| Visual design | Deferred to the next visual-design round |
| Exploration Field | Remains `OPEN_ENDED_DATA_MINING` |

Final npm install, typechecks, Context/Search/Read Platform/TRACE regressions, Spacetime projection/governance/GIS/API/cohort gates, production build, built-output API guard, functional benchmark, bundle attribution, and whitespace QA all pass. The Round 4 audit package records and seals these results.

## Verified source census

The public release contains 7,995 objects; 7,928 held identities are excluded. Geography contains 7,996 typed assignments covering all 7,995 public objects, 94 distinct raw display labels, 93 typed governed labels, and one multi-region object. The geography registry contains 93 entries: 81 mapped, 11 aggregate-only, one explicitly unmapped, and zero held entries. At object level, 7,800 objects have mapped geography, 194 are aggregate-only, and one is unmapped.

Temporal coverage is 7,995 of 7,995. Precision is retained as 7,552 year, 305 approximate, 78 day, 27 month, 33 range, and zero unknown observations. The governed extent is 1800 through 2026. Twenty-three decade buckets use `INTERVAL_OVERLAP`; the default bucket is the densest bucket, the 1980s.

## Semantic boundary

Spacetime answers: **when and in what recorded geographic context do records appear in the selected public release?** It does not assert exact creation coordinates, travel, diffusion, influence, or causal movement.

All point-like positions are typed aggregate layout derivations. Density dots are synthetic aggregate positions. Map marks are selectors and never become TRACE semantic edges. Broad, transnational, subnational-without-geometry, and unmapped records remain visible in numerical equivalents.

## Artifact decision

The selected immutable geometry asset contains 242 features and has SHA-256 `01a926cc82cda561692eeefcdde8d52310730c08919fd9f73e679c79a9fa718d`. It is served once as a stable static asset; period changes use small aggregate responses and never re-fetch or reconstruct governance.

The installed `world-atlas` package remains solely to preserve legacy/test compatibility; it is not a Spacetime geometry authority.

The generated Spacetime projection is `trace-spacetime-v1` with final SHA-256 `f751b0f432ff684fd1000201b910aa397a4d9965468c2f7dd5022d6a4ae01c06`.
