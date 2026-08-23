# Search UX Contract

## Scope

The v1 UI presents one scope: Archive. TRACE and Relations are not shown because the sealed public release contains no accepted records in those scopes.

The workspace is a neutral researcher-facing list, not an archive-box-specific component. It uses the Read API through `HttpArchiveRepositoryProvider`; ranking remains a pure server function.

## Required flow

1. The input accepts plain text only.
2. Search runs on explicit submit, never on every keystroke.
3. The submitted query is stored as `/search?q=…`.
4. Direct load, refresh, back, and forward restore and execute the URL query.
5. The first page contains 25 results; “Load more results” uses the relevance cursor.
6. Clear removes the query and returns to the idle state.

There is no Lucene syntax, regex, wildcard behavior, Boolean grammar, autocomplete, or “did you mean” in v1. `%` and `_` are ordinary punctuation and do not become wildcards.

## States

| State | Public behavior |
|---|---|
| idle | instructions, empty input, no result list |
| loading | live “Searching the frozen public release…” status; submit disabled |
| ready with results | exact result count, dense ordered list, load-more when available |
| ready empty | distinct no-match guidance using the submitted query |
| error | alert beginning “Search failed”, retry guidance, no false empty claim |
| loading more | existing results remain; button announces loading |

Requests are abortable. A later query cancels the earlier request so stale responses cannot overwrite current results.

## Result row

Rows show only verified or contractually safe values:

- unchanged public title;
- stable ID;
- delivery state;
- visible lexical match reason and integer score;
- keyboard-openable link to the surface route.

Creator, date, place, medium, source, alias, and transliteration are omitted because v49 does not publish usable values for search. No decorative empty placeholders are rendered.

## Accessibility

- semantic `role="search"` forms and explicit labels;
- keyboard submission and standard links;
- result/loading/empty states announced through live regions;
- errors use `role="alert"`;
- match reason is text, not color-only;
- 48 px minimum input/button targets through existing read-platform styles;
- shell trigger exposes `aria-expanded` and `aria-controls`;
- Escape closes shell search and restores trigger focus;
- mobile layout wraps controls instead of shrinking them below usable width.

## Shell entry point

The shell panel is only a small explicit-submit form linking to `/search`. It performs no local search and downloads no archive corpus. Its wording accurately limits search to public titles and stable IDs.
