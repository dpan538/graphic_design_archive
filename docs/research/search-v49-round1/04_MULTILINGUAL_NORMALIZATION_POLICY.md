# Multilingual Normalization Policy

## Principles

The archival display label is immutable. Normalized channels exist only for retrieval and are never written back into source data or displayed in place of the title.

The generator and runtime are pinned to Node 22 and Unicode data version 16.0. Artifact generation fails under a different Unicode version. Unicode normalization can establish canonical and compatibility equivalence, but compatibility mappings can erase meaningful distinctions; therefore NFKC is a lower-ranked fallback, not the display form.

## Channels

| Channel | Transformation | Use | Rank |
|---|---|---|---|
| display | original trimmed public title | rendering and strongest exact equality | highest |
| primary | NFC; deterministic lowercase channel; `ß→ss`, final sigma `ς→σ`; punctuation/symbol separators collapsed; whitespace collapsed | ordinary case/punctuation/space matching | primary |
| compatibility | NFKC plus the same case/separator rules | full/half-width and compatibility forms | below primary |
| Latin diacritic | primary → NFD → remove combining marks only when attached to a Latin starter → NFC | `Haïti` / `Haiti`-style fallback | below compatibility |
| compact | remove normalized separators | punctuation/spacing variants such as `A.M.` / `AM` | below phrase substring |

Hyphen variants, apostrophe variants, slashes, non-breaking spaces, Unicode punctuation, and repeated whitespace become separators. The code does not confusable-fold between scripts and does not map distinct letters such as `ø`, `ł`, `đ`, or `æ` speculatively.

The v1 case channel is deliberately documented as a limited deterministic policy, not as a claim of complete Unicode case folding.

## CJK and segmentation

The public v49 cohort has one title containing Han characters and no titles containing Japanese kana or Korean Hangul. The verified Han record is `SURF-MDA2026V2R0448`, “没有子宫就给我闭嘴 (No uterus, no opinion)”. Queries `没有` and `子宫` are tested as direct Unicode substring matches.

Whitespace tokenization is not required for that path because phrase/substring checks operate directly over the normalized code-point string. `Intl.Segmenter` is intentionally absent from ranking: ECMA-402 permits implementation-dependent locale behavior, and UAX #29 notes that default word boundaries need tailoring for many languages. No large tokenizer is justified by the public cohort.

Queries such as `上海`, `東京`, `グラフィック`, `서울`, and `포스터` return no result because no corresponding public v49 label exists. Tests do not fabricate positives from held or legacy records.

## Unsupported transformations

- no automatic transliteration;
- no romanization tables;
- no cross-script confusable mapping;
- no inferred aliases;
- no stemming, lemmatization, or language detection;
- no semantic or embedding similarity.

Stored source-language labels, transliterations, or aliases can be added only after the sealed public projection exposes them as explicit fields and the field-policy hash/version changes.

## References

The policy follows Unicode normalization and text-segmentation standards recorded in `SOURCE_REGISTER.tsv`, especially UAX #15, UTS #18, UAX #29, ECMA-262, ECMA-402, and UTS #39.
