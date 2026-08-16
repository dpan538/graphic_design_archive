# Audience, education and machine positioning

## Audience order

1. **Primary — design-history researchers.** They need bounded discovery plus a route to source, scope, contradiction, qualification and provenance. The release should be judged by whether they can audit a statement rather than whether a graphic feels comprehensive.
2. **Secondary — research-active curators/archive operators; educators and students; informed design-history readers.** Curators use provenance/rights/missingness to assess discovery value; teaching can use the explicit distinction between context and evidence; readers gain guided access.
3. **Infrastructure audience — API/machine clients, including AI agents.** They need stable release identity, identifiers, source/right state, schema and explicit `UNKNOWN`/`HELD`; they do not need a visual graph and must not be given implied relations.
4. **Tertiary — general visitors.** A welcome public audience, but not a basis to compromise evidence boundaries or turn visual affinity into historical claim [SR22][SR25].

**Education is secondary, not core.** It becomes a research contribution only with a defined learning objective, co-design/evaluation and evidence of interpretation; absent that, it is honest public-communication value [SR18][SR25].

## Machine/read-only value

A read-only API and machine-readable release improve reproducibility, citation, re-use, independent checking and longitudinal maintenance. Their defensible value is **C. infrastructure**: release ID, stable identifiers, source/provider path, rights/access state, missingness and evidence status prevent downstream consumers from mistaking an interface projection for source truth. FAIR supports such practice but makes it common research stewardship, not novelty [SR07][SR22].

Minimum machine contract: release/manifest ID; object ID; source and provider URI; field-level `UNKNOWN`/`HELD`/`NOT_APPLICABLE`; date and geographic precision; rights statement exactly as supplied; evidence/claim/relation state; relation count zero; policy/schema version; and a citation/download route. Do not return old v48 edges, automated scores or “related” results as relations.

Suggested API description:

> A read-only, release-pinned research index API. It exposes catalogued records, source/provenance and availability states, coverage/missingness metadata, and explicit evidence status. It publishes no accepted semantic TRACE relations in this release; consumers must not infer historical influence from co-occurrence, membership, metadata or layout.

## Visual federation: advantage and limit

Its real advantage is discovery without pretending to take custodial control: retain the upstream provider, direct-record path, supplied rights statement and access date; avoid copying files into a local image collection. It can reduce duplicated hosting and make source attribution visible. It **does not** confer copyright permission, a licence to display/frame/cache/crop, AI-training permission, preservation custody, institutional endorsement, or an assurance that the provider link will persist. Rights need an item-level assessment; `UNKNOWN` must remain `UNKNOWN` [SR12][SR23][SR24]. This is product-governance guidance, not legal advice.

## Per-audience phrasing

| Audience | Lead with | Never lead with |
|---|---|---|
| Researcher | release, sources, provenance, evidence threshold and coverage limits | influence discovery or a complete history |
| Curator | provider attribution, non-custody federation, correction/takedown path and held state | stewardship/preservation or rights clearance |
| Educator/student | source literacy: coverage ≠ relation; membership ≠ influence | a decorative “history graph” |
| Machine client | stable release contract and explicit unknowns | opaque confidence/derived relationships |
| Public reader | guided exploration with uncertainty visible | authority, comprehensiveness or hidden-connection rhetoric |
