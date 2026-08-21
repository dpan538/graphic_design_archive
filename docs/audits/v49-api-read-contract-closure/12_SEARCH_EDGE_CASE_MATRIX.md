# Search edge-case matrix

The machine result contains 49 search-labelled cases. Coverage includes exact known title, `Poster`, no result, empty/whitespace, trim equivalence, case equivalence, Unicode, punctuation, URL encoding, repeated `q`, ignored unimplemented `page`, invalid/zero/negative/decimal/over-max `first`, 121-character input, SQL metacharacters, literal `%`/`_`, invalid/trace/relation scopes, malformed/cross-filter cursors, deterministic repeat, detail resolution, and all five exhaustive pages.

```text
SEARCH_EDGE_CASE_MATRIX=PASS
CANONICAL_QUERY=Poster
EXPECTED_API_VIEW_ROWS=486
OBSERVED_PAGED_ROWS=486
DUPLICATE_RESULT_COUNT=0
OMITTED_RESULT_COUNT=0
FINAL_PAGE_HAS_NEXT=false
FINAL_PAGE_CURSOR=null
SEARCH_HTTP_503_COUNT=0
```
