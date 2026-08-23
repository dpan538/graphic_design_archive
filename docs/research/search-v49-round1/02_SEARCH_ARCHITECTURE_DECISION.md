# Search Architecture Decision

## Decision matrix

| Architecture | Quality | Typo | CJK / multilingual | Measured latency | Memory / bundle | DB mutation | Dependency | Determinism / explanation | Effort / operations | Decision |
|---|---|---|---|---|---|---|---|---|---|---|
| A. Existing PostgreSQL read layer | literal title substring only | none | literal substring only | existing API median 31.539 ms, P95 68.190 ms | no new artifact; requires live DB | no new mutation, but no evidenced trigram index | none | deterministic but no relevance explanation | low code; production provider was unwired | NO-GO |
| B. Compact document set + bounded full scan | recall-safe across every public title/ID | bounded token OSA | exact CJK substring; Unicode channels | final P50 41.90 ms, P95 56.73 ms | 1.44 MB raw / 0.257 MB gzip; ~38.0 MB measured process heap after benchmark | none | none | release/checksum pinned; integer score and stable tie-break | low-medium; one generated artifact | **GO_WITH_CONDITIONS** |
| C. Derived inverted index | fast candidates but candidate design can lose recall | deletion/ngram support needed | CJK n-grams possible | probe P95 about 34 ms | prototype ~2.00 MB raw / 0.670 MB gzip in addition to documents | none | none | deterministic, more moving pieces | medium | DEFER |
| D. Lightweight library | library-dependent | library-dependent | library-dependent | not benchmarked; no library installed | new client/server code and supply-chain surface | none | yes | configuration-dependent | medium | NO-GO |
| E. Custom two-stage postings + ranking | flexible, but probe candidate misses reduced Top-5 | yes | yes | probe P95 about 34 ms | postings plus documents | none | none | explainable but more complex | medium-high | DEFER |

## Selected design

```text
frozen v49 candidate + freeze receipt
  → verify canonical checksum and eligibility counts
  → extract only public stable ID + title for source_verified/eligible rows
  → serialize deterministic normalized retrieval channels
  → manifest + SHA-256 checksums
  → lazy server-only validation/hydration
  → bounded full-corpus lexical ranker
  → relevance-bound keyset page + explanation
```

Option B won because 7,995 documents and one searchable text field make full-corpus comparison cheap enough. It avoids the recall risk and operational surface of a candidate index. The final P95 is far below the provisional 200 ms computation target.

## Full-scan justification and bounds

This is not an unbounded scan over user-controlled payloads. The generated artifact rejects release drift and fixes these maxima: 7,995 documents, 1,024 title code points, 128 title tokens, 64 code points per title token, 160 query code points, 24 query tokens, edit distance 2, and page size 100. The actual largest v49 public title is 806 code points / 124 tokens and the largest token is 26 code points.

Edit distance is skipped for query tokens below four code points and for every token containing a digit. Every query token must match a permitted signal before a record can be returned.

## Rejected details

- `pg_trgm` was researched but is not evidenced as an enabled/indexed production capability; this round cannot mutate the frozen DB to add it.
- `Intl.Segmenter` is not ranking-critical because its locale data and boundaries are implementation-dependent and the public cohort does not justify a language tokenizer.
- Character n-gram postings improved speed in a probe but lost candidate recall, especially around short transpositions. They are unnecessary at current scale.
- No fuzzy-search package was already installed, and adding one did not dominate the simpler measured implementation.

## Conditions for revisiting

Reconsider a postings/two-stage architecture if searchable public fields expand materially, the public cohort grows several-fold, P95 exceeds 200 ms in deployed telemetry, or sustained concurrency makes per-request CPU unacceptable. Bump both algorithm and index format when ranking semantics change.
