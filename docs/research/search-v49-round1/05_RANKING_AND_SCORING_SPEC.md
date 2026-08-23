# Ranking and Scoring Specification

`SEARCH_ALGORITHM_VERSION=v49-lexical-fuzzy-1`

## Retrieval signals

| Signal | v1 status | Meaning |
|---|---|---|
| EXACT | implemented | byte-identical display title |
| EXACT_NORMALIZED | implemented | equality in primary, compatibility, or Latin fallback channel |
| PHRASE | implemented | whole normalized query prefix/substring |
| TOKEN_EXACT | implemented | query token equals a title token |
| PREFIX / WORD_PREFIX | implemented | title phrase or token begins with query |
| SUBSTRING | implemented | title phrase or token contains query |
| TOKEN_OVERLAP | implemented as full coverage | every query token must match |
| TYPO_EDIT_DISTANCE | implemented | bounded token Optimal String Alignment |
| IDENTIFIER_MATCH | implemented | exact stable ID only |
| CHARACTER_NGRAM | benchmarked, not selected | candidate probe lost recall |
| ALIAS / TRANSLITERATION | `NOT_SUPPORTED_BY_DATA` | never inferred |
| DATE_MATCH | `NOT_SUPPORTED_BY_DATA` | no public date field |

Semantic similarity, embedding similarity, historical relatedness, and visual similarity are outside search. A lexical match never creates or implies a TRACE relation.

## Score tiers

All scores are integers.

| Match | Score |
|---|---:|
| exact stable ID | 30,000 |
| exact display title | 29,000 |
| primary normalized title exact | 28,000 |
| NFKC compatibility title exact | 27,500 |
| Latin-diacritic fallback exact | 27,000 |
| primary phrase prefix | 21,000 |
| compatibility phrase prefix | 20,500 |
| Latin fallback phrase prefix | 20,000 |
| primary phrase substring | 18,500 |
| compatibility phrase substring | 18,000 |
| Latin fallback phrase substring | 17,500 |
| compact punctuation/spacing substring | 16,500 |

Token-mode score is `6,000 + Σ token score + 800 when multi-token`:

| Token signal | Score |
|---|---:|
| exact | 1,800 |
| prefix | 1,450 |
| substring | 1,100 |
| OSA distance 1 | 720 |
| OSA distance 2 | 540 |

Phrase tiers intentionally outrank token aggregation. Stable ID outranks every text match, and exact title outranks every typo-only match.

## Typo policy

The implementation uses bounded Optimal String Alignment distance, so one adjacent transposition counts as one edit. It does not claim unrestricted Damerau-Levenshtein.

- fewer than 4 code points: no typo;
- 4–8 code points: maximum distance 1;
- 9 or more code points: maximum distance 2;
- any token containing a digit: no typo;
- one-code-point Latin/numeric tokens require token equality outside direct phrase matching;
- at most 24 query tokens and 64 code points per indexed title token.

Length-difference and row-minimum checks terminate impossible edit comparisons early.

## Coverage and order

If no whole-query phrase signal matches, every query token must match at least one title token in one normalization channel. This gate prevents one matching word from admitting a document that misses the rest of the query.

Order is:

1. score descending;
2. primary normalized title ascending by deterministic string/code-point order;
3. stable ID ascending.

`localeCompare` and random ordering are not used in production ranking.

## Explanation

Every new result carries `algorithmVersion`, integer `score`, `matchType`, `matchedFields`, `signals`, and `normalizedQuery`. The public UI shows a short reason and score; tests can inspect the full machine-readable object.
