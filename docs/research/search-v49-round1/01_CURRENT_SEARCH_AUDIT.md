# Current Search Audit

## Audited baseline

The baseline is source branch `chore/v49-repository-hygiene-database-freeze-20260821` at `c0ca9a1d4745cfd1054b924c648e57887830960d`, tree `f8ecd0046a4b8e3c1be657b2a31ac0b863f08ad0`.

## Current API flow before this round

```text
/search form
  → HttpArchiveRepositoryProvider opens /api/v1/releases/current
  → exact release pair is resolved
  → GET /api/v1/releases/{release}/search?q=…&scope=…
  → Read API controller
  → ArchiveRepository.search
  → PostgreSQL lower(title) literal substring
  → title + stable-ID alphabetical keyset page
```

The verified PostgreSQL predicate was equivalent to `strpos(lower(coalesce(title, '')), lower($query)) > 0`. It was not fuzzy, did not calculate relevance, and searched only the public title. Query text was trimmed, required to be non-empty, and limited to 120 characters. `%` and `_` were literal because the implementation did not use `LIKE` wildcards.

The endpoint accepted `archive`, `trace`, `relation`, and `all`. The public v49 TRACE and relation sets are empty, so those scopes added no useful results.

### Baseline behavior

| Property | Baseline |
|---|---|
| Searchable fields | title only |
| Normalization | database lowercase only |
| Exact / substring | yes |
| Prefix | incidentally, as substring |
| Punctuation / whitespace tolerance | no |
| Diacritic fallback | no |
| Typo tolerance | no |
| Ranking | title ascending, then stable ID |
| Pagination | release-bound alphabetical keyset cursor |
| Explanation | none |
| Result schema | archive hit, route, highlight, surface summary |
| Observed API latency | 31.539 ms median, 68.190 ms P95, 71.294 ms maximum |

The latency values come from `docs/statistics/v49-api-runtime-profile.csv`; they describe the existing end-to-end literal endpoint, not the new scorer.

## Separate legacy shell path

The global shell independently loaded `frontend/public/data/archive-search-v1.json` after typing. That asset was 22,695,973 bytes, contained 8,636 rows generated from `public_surface_mock_v0`, and used client substring/prefix/subsequence scoring. It rejected all query terms shorter than two code units and therefore mishandled single-character CJK queries.

Only 80 of its IDs intersected the 7,995 public v49 records. Most hits could therefore lead to a current-release 404. This round removes the asset, its generator, its dead client, and both legacy consumers. Shell search is now an explicit-submit entry point to the release-pinned workspace.

## Production composition failure

The baseline composition root returned the fixture only when explicitly selected outside production and otherwise threw. Although a PostgreSQL repository class existed, it was not wired. A production request could therefore return 503 before dispatching search. This round makes the validated derived-v49 provider the production default; fixture mode remains explicit and forbidden in production.

## Release and field boundary

`database/FREEZE_V49.json` records 15,923 canonical objects, 7,995 eligible objects, and 7,928 held objects. The release projection builder includes only `corpus_membership.disposition = 'eligible'`. The audited API closure likewise records `API_VISIBLE_OBJECT_COUNT=7995` and `SEARCHABLE_RECORD_COUNT=7995`.

The sealed public surface presentation contains usable stable IDs and titles. Creator, date, place, medium, type, source, alternate appellations, and transliterations are missing or public placeholders. Recovering richer values from held/canonical candidate fields would cross the release boundary, so v1 does not do it.

## Deficiencies closed by this round

- literal-only matching replaced by versioned normalized/prefix/substring/token/typo ranking;
- old alphabetical cursor replaced by an index/query/algorithm-bound relevance cursor;
- result explanations added;
- one-character Han substring supported without a language tokenizer;
- production provider wired;
- stale browser corpus removed;
- URL persistence, load-more, empty/error/loading states, and accessible announcements implemented.
