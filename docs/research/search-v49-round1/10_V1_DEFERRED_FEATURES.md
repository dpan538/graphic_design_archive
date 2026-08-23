# V1 Deferred Features

## Explicitly out of scope

- AI search, LLM APIs, local SLM inference, or model-based query rewriting;
- embeddings, vector databases, semantic similarity, RAG, or chatbots;
- automatic historical question answering or AI result summaries;
- AI related-record suggestions;
- visual similarity or image search;
- natural-language SQL;
- semantic, historical-relatedness, or institution-prestige ranking;
- Lucene-style Boolean grammar, regex, wildcards, or arbitrary `field:value` lookup;
- autocomplete and “did you mean”;
- PostgreSQL extension/index/schema changes;
- a persistent external search service.

No provider scaffolding is included for any of these features.

## Deferred because public v49 data does not support them

| Feature | v1 result | Requirement before implementation |
|---|---|---|
| alias search | `NOT_SUPPORTED_BY_DATA` | explicit public alternate-label/appellation field |
| transliteration search | `NOT_SUPPORTED_BY_DATA` | explicit public transliteration with language/script provenance |
| creator search | `NOT_SUPPORTED_BY_DATA` | non-placeholder creator in sealed public projection |
| place/date/medium/type/source search | `NOT_SUPPORTED_BY_DATA` | corresponding verified public fields |
| Japanese kana validation | `NOT_SUPPORTED_BY_DATA` | real public kana label |
| Korean Hangul validation | `NOT_SUPPORTED_BY_DATA` | real public Hangul label |
| TRACE / relation UI scope | deferred | accepted public TRACE objects/relations |

These fields must not be backfilled from the 7,928 held records, the deleted legacy mock index, or richer canonical candidate metadata.

## Architecture deferred until scale justifies it

- token/prefix posting lists;
- character bigram/trigram posting lists;
- deletion-signature typo candidates;
- a custom two-stage candidate/ranker pipeline;
- SQLite FTS5, PostgreSQL trigram, or third-party JavaScript search library;
- deployment-level runtime cache.

Re-evaluate only with deployed CPU telemetry, substantial public-field growth, or a public cohort large enough to push P95 beyond 200 ms.

## Research still needed

A small human-reviewed relevance panel should assess ambiguous short queries, alternative-language expectations, and acceptable tail noise. That study must remain separate from the reproducible mechanical known-item benchmark.
