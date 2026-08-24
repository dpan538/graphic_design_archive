# Duplication and boilerplate audit

## Evidence state

`DOCUMENT_STATE=SEALED_PRECOMMIT_PASS`

This audit distinguishes object identity, repeated text, and source/provider
templates. A repeated string is never sufficient evidence for a semantic or
historical relation.

## Identity boundary

All 7,995 public IDs remain distinct. Exact title equality, case equality,
punctuation equality, whitespace equality, or source-template equality cannot
merge records or create a positive pair.

The current title census contains 155 duplicated normalized-title groups
covering 520 public objects. Those groups generate 4,346 same-title unordered
pairs. Only two of those pairs independently qualify for Task A because an
immutable institutional item key establishes duplicate-import identity; title
equality itself did no verification. The remaining 4,344 pairs are leakage
stress controls, not negative historical judgments.

The sealed exact census covers normalized governed titles. It does not provide
a separately sealed cross-field, case-only, punctuation-only, whitespace-only,
or near-duplicate aggregate; those absent measurements remain `N/A` rather
than being inferred from field-level duplicate rates:

```text
EXACT_DUPLICATE_TEXT_GROUP_COUNT=155
CROSS_OBJECT_DUPLICATE_TEXT_GROUP_COUNT=155
DUPLICATE_TITLE_DIFFERENT_ID_COUNT=4344
CASE_ONLY_VARIANT_GROUP_COUNT=N/A_NOT_RUN
PUNCTUATION_ONLY_VARIANT_GROUP_COUNT=N/A_NOT_RUN
WHITESPACE_ONLY_VARIANT_GROUP_COUNT=N/A_NOT_RUN
NEAR_DUPLICATE_DIAGNOSTIC_GROUP_COUNT=N/A_NOT_RUN
```

Near-duplicate analysis is diagnostic only. Its thresholds and normalization
views must be declared; no result may be converted to identity or a positive
semantic pair.

## Deterministic discovery method

The registry groups public values by source and field role. It records:

- exact NFC/whitespace-normalized template hashes with at least three rows and
  at least five percent within-source/role support;
- source-conditioned 5- and 8-token prefixes and suffixes with support at least
  `max(5, ceil(0.20 * denominator))`; and
- one explicit source-literal mask rule per observed source.

One document contributes at most once to a prefix/suffix support count. Phrase
material is represented by SHA-256 rather than committed raw provider prose.

## Frozen boilerplate registry result

```text
NLP_BOILERPLATE_REGISTRY_VERSION=trace-nlp-boilerplate-v1
BOILERPLATE_RULE_COUNT=105
BOILERPLATE_AFFECTED_OBJECT_COUNT=6563
MASK_SOURCE_IDENTITY_RULE_COUNT=15
HOLD_RULE_COUNT=90
REMOVE_FOR_NLP_INPUT_RULE_COUNT=0
HIDDEN_PHRASE_BLACKLIST=false
BOILERPLATE_REGISTRY_SHA256=790b17b2e473190f7efd6051dec09590d50fdb7956933bfd452099e21a90eee6
```

“Affected” means that the object participates in at least one repeated
source-conditioned candidate. It does not establish that the whole value is
boilerplate. High document frequency alone leaves a rule at `HOLD`.

## Decisions and mutation boundary

Allowed decisions are `REMOVE_FOR_NLP_INPUT`, `MASK_SOURCE_IDENTITY`,
`KEEP_SEMANTIC`, `KEEP_DIAGNOSTIC`, and `HOLD`. Each rule records source, field
role, phrase hash, support, denominator, decision, reason, removal scope, rule
type, token count, and version.

The current registry authorizes only source-name/URL masking in an explicit
source-leakage variant. It authorizes no automatic boilerplate deletion.
`HOLD` rules never mutate text. Repeated object titles stay semantic inputs
unless a future governed decision says otherwise; their repetition does not
establish identity.

## Robustness requirements

Every shortlisted model/aspect must compare the approved input with applicable
variants for markup cleaning, registered boilerplate handling, and source-name
masking. The final report must include top-10/top-20 overlap, rank correlation,
source-leakage change, and hubness change where supported.

```text
BOILERPLATE_REMOVAL_TOP20_OVERLAP=N/A
SOURCE_MASKING_TOP20_OVERLAP=1
SOURCE_LEAKAGE_CHANGE=0
HUBNESS_CHANGE=0
```

If no removal rule is authorized, the boilerplate-removed variant must state
that it is unchanged or `N/A`; it must not pretend that held candidates were
removed.

The numeric source-mask comparison above is the executed lexical title
variant. Dense source-mask re-encodings were not authorized or run, so the
values do not describe dense-model robustness. Boilerplate removal is `N/A`
because the registry authorizes no `REMOVE_FOR_NLP_INPUT` rule.

## Interpretation

Provider repetition and duplicate imports can make a retrieval method look
consistent while measuring source style. High duplicate/known-item recall is
therefore labeled `IDENTITY_RETRIEVAL`. It cannot be combined with metadata
proxy, cross-language, or semantic review outcomes into one accuracy score.
