# Failure Analysis

## Method and important caveat

NEW produced no Top-1 failures on the mechanically derived held-out positives. To satisfy noise review without inventing failures, the review inspected the highest-volume held-out queries with non-target results, then added the two largest ambiguous-short stress queries. “False-positive candidate” below means a non-target lexical result requiring human relevance judgment; it does not mean the expected record was displaced. In every positive row, the expected record remained rank 1.

The review inspected titles for all 25 candidates in `benchmark-results.json` and classified the main risk using the requested taxonomy.

| # | Query ID | Query | Results | Classification | Manual finding |
|---:|---|---|---:|---|---|
| 1 | Q115 | `froh` | 204 | typo overreach | expected `Frohe…` ranks first; distance-1 token matches such as “from” add severe noise |
| 2 | Q113 | `alle` | 172 | substring overreach | `Alle…` ranks first; `Alles…` is linguistically plausible, while later partials broaden quickly |
| 3 | Q119 | `the ow` | 108 | generic-token dominance | expected phrase prefix ranks first; common `the` plus two-letter prefix admits long unrelated titles |
| 4 | Q126 | `pan` | 69 | short-query noise | correct `Pan American…` ranks first; three-letter substring is inherently broad |
| 5 | Q130 | `pend` | 34 | substring overreach | correct `Pendant` ranks first; `independence`-like substrings add lexical but weak matches |
| 6 | Q133 | `stori` | 33 | substring overreach | correct `Storian…` ranks first; `Estoril` is a mechanically valid but irrelevant containment |
| 7 | Q123 | `don t t` | 25 | generic-token dominance | punctuation normalization is correct; repeated one-letter `t` contributes little discrimination |
| 8 | Q125 | `9 75` | 19 | date ambiguity | target percentage ranks first; dates containing 1975 create weak numeric overlap |
| 9 | Q127 | `arun` | 14 | typo overreach | target `Arundel…` ranks first; distance-1 token comparisons produce unrelated candidates |
| 10 | Q114 | `the bra` | 14 | generic-token dominance | target phrase prefix ranks first; `the` and short `bra` are broad |
| 11 | Q124 | `masc` | 13 | typo overreach | target `Mascoutah…` ranks first; one-edit matches broaden the tail |
| 12 | Q142 | `an never` | 9 | generic-token dominance | expected middle phrase ranks first; common `an` and `never` match many political titles |
| 13 | Q117 | `techni` | 6 | substring overreach | expected `Technique…` ranks first; “technical” titles are plausible lexical alternatives |
| 14 | Q182 | `komemt` | 5 | typo overreach | intended Norwegian `kommet` ranks first; German `kommt`-like forms are near spellings |
| 15 | Q190 | `strkening` | 4 | typo overreach | intended `trekning` record ranks first; related Norwegian loan titles are arguably relevant |
| 16 | Q170 | `strexning` | 4 | typo overreach | same source family as Q190; multiple distance-1/2 variants survive |
| 17 | Q131 | `elna` | 4 | typo overreach | `Elna…` ranks first; `CELNA` is a cross-language near-string, not a script collision |
| 18 | Q231 | `forf brei` | 3 | substring overreach | two incomplete prefixes identify target first but also collide with other Norwegian titles |
| 19 | Q233 | `cosi post` | 3 | substring overreach | `Cosi fan tutte poster` ranks first; `post` is broad and `cosi` can fuzzy-match |
| 20 | Q196 | `nous commun` | 2 | generic-token dominance | intended French title ranks first; political `communes` is a plausible lexical alternative |
| 21 | Q158 | `spixle` | 2 | typo overreach | intended `spille` ranks first; `Spiele` is a real cross-language edit neighbor |
| 22 | Q172 | `selxes` | 2 | typo overreach | intended `selges` ranks first; “Sexes” is a real edit neighbor |
| 23 | Q171 | `obligaxjonene` | 2 | typo overreach | two closely related Norwegian bond titles match; both are arguably useful |
| 24 | Q264 | `1` | 3,392 | short-query noise | exact one-character support is deterministic but far too broad for high precision |
| 25 | Q258 | `an` | 1,966 | short-query noise | two-letter English fragment is intrinsically ambiguous; alphabetical tie-break is stable, not relevance-rich |

## Taxonomy coverage

Observed: short-query noise, generic-token dominance, date ambiguity, typo overreach, and substring overreach.

Not observed in these 25: alias collision (no alias data), creator/title collision (creator not indexed), place ambiguity (place not indexed), cross-script collision, normalization error, or a ranking-weight error that displaced the target.

## Explicit tuning changes

Two rule changes were made before freezing `v49-lexical-fuzzy-1`:

1. Require full query-token coverage. This eliminated permissive no-result false positives in the architecture probe.
2. Disable typo edits for every token containing a digit, and require exact token equality for one-code-point Latin/numeric token matching outside a direct phrase. This removed near-code noise such as `O1162014` matching other object codes.

The algorithm version did not ship before these changes; `v49-lexical-fuzzy-1` names the final frozen rule set.

## Accepted launch limitation

Very short queries may return broad sets, but they do not trigger typo correction below four code points and ordering is stable. Adding a minimum query length would break legitimate single-Han and identifier/title use. V1 therefore accepts broad short-query recall and relies on visible counts, result reasons, and user refinement. Telemetry should determine whether a future stop-word or minimum-Latin-length policy is warranted.
