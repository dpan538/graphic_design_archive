# v49 Search Round 1 — Executive Decision

## Decision

`GO_WITH_CONDITIONS`

Ship `v49-lexical-fuzzy-1`: a deterministic, server-only lexical scorer over one compact, release-pinned document set. It has no AI, external search service, database mutation, or new dependency.

The critical scope correction is that v49 contains 15,923 canonical objects, but only 7,995 are eligible for the sealed public/API projection. The remaining 7,928 are held. Search indexes exactly the 7,995 public records and only the two verified public fields: stable ID and title.

## Why this architecture

At this public scale, a bounded full scan is simpler and more recall-safe than serialized postings. On the final 271-query benchmark it measured 41.90 ms P50, 56.73 ms P95, and 189.31 ms maximum ranking time on Node 22.21.0 / Apple arm64. The 1,435,371-byte document artifact compresses to 256,941 bytes and remains in the server bundle, not the initial browser bundle.

On the 197-case held-out split, 173 mechanically derived positive queries improved from 31.79% to 100% Top-1 and from 32.37% to 100% Top-5. Typo recovery improved from 0% to 100%. These figures validate known-item retrieval transformations, not subjective historical relevance; a human relevance panel remains future work.

## Conditions

The release is acceptable only while all of these remain true:

- document count is exactly 7,995 and held count is exactly 7,928;
- runtime release ID, research manifest SHA, index SHA, format, algorithm, Unicode version, and field policy pass together;
- every query token is covered by a permitted lexical signal;
- edit distance remains Optimal String Alignment, at most 2, disabled below four code points and for tokens containing digits;
- only stable ID and title are indexed until the public projection exposes more fields;
- aliases and transliterations report `NOT_SUPPORTED_BY_DATA` rather than being inferred;
- the obsolete 8,636-row browser index remains deleted and no full corpus enters the initial browser bundle;
- performance and deterministic-rebuild gates continue to pass.

## Capability receipt

| Capability | Result |
|---|---|
| Exact / normalized exact | PASS |
| Prefix / partial / substring | PASS |
| Multi-token, including out-of-order | PASS |
| Bounded spelling error / adjacent transposition | PASS |
| Case, punctuation, spacing, compatibility width | PASS |
| Conservative Latin diacritic fallback | PASS |
| Stable identifier | PASS |
| Han exact and substring on a real public record | PASS |
| Japanese kana / Korean Hangul | NOT_SUPPORTED_BY_DATA |
| Aliases / transliterations | NOT_SUPPORTED_BY_DATA |
| Creator / date / place / medium | NOT_SUPPORTED_BY_DATA in sealed v49 projection |
| Explainable, pagination-safe relevance ranking | PASS |

Detailed evidence is in `08_SEARCH_EVALUATION_REPORT.md` and `../../audits/v49-search-fuzzy-round1/benchmark-results.json`.
