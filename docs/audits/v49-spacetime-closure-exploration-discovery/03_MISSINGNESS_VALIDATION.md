# Missingness validation

## Taxonomy and cohort

The generator/verifier freeze ten supported classes and 7,995 public object vectors. No held object enters the vectors or aggregate statistics. Movement absence is `NO_PUBLISHED_MOVEMENT_CONTEXT`, not generic missingness; source-collection absence remains `NOT_GOVERNED`.

| Receipt | Value |
| --- | ---: |
| Taxonomy classes | 10 |
| Object vectors | 7,995 |
| Active state events | 11,075 |
| Co-occurrence cells | 19 |
| Creator observed / explicit unknown / qualified unknown | 5,806 / 2,027 / 162 |
| Movement observed / no published context | 110 / 7,885 |
| Temporal approximate / range | 305 / 33 |
| Geography mapped / aggregate-only / unmapped | 7,800 / 194 / 1 |
| Qualified / multi-region geography | 467 / 1 |
| Source-collection diagnostic present / absent | 7,980 / 15 |

Creator null-missing count is zero. The explicit unknown categories remain source semantics. Rights/delivery and image state are deferred rather than guessed.

## Determinism and safety

| Artifact | SHA-256 |
| --- | --- |
| Missingness deterministic payload | `0ad7438e700abb9bb2f395e307251b4a2032a37a45f00698386fd2fc168d2178` |
| Object vectors | `da439396aa1782ee616929ca70d451d822fe748dac5e8f622e342286ed644603` |
| Field matrix | `725d58b7e52ef36d0a945bf45efdbeca0a444553565945993e729b6019e07041` |
| Co-occurrences | `9c237e41005265780be1a285952fe49835b2b88d30d313c5d1b39558c11e96bd` |

Object vectors are hashed but not committed. The 38-row census is rectangular, denominator-bearing, and contains ten taxonomy rows, nine field rows, and 19 observed co-occurrence rows.

All missingness-specific invariants pass: generic movement missing 0, creator null missing 0, held included 0, single uncertainty score false, historical relation false, and semantic relation false.
