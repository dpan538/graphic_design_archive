# Global object Search product contract

## Product position

Global Search and TRACE are parallel homepage-level strategies.

```text
Graphic Design Archive
├── Global Search
│   ├── homepage entry
│   ├── desktop workspace
│   ├── mobile workspace
│   └── public object page
└── TRACE
    ├── Context Canvas
    ├── Spacetime
    └── Exploration
        ├── Validated Exploration
        └── Open Inquiry
```

Search is the high-frequency public-object finding entry. TRACE is a desktop research environment. Search does not index TRACE concepts, associations, compositions, state objects, research controls, or Open Inquiry hypotheses. Direct compact-screen access to TRACE may show a desktop-required message without importing the full TRACE runtime.

## One Search experience

There is one Search experience. There is no Basic/Advanced split, Advanced toggle, popularity order, trending order, personalisation, recommendation order, or AI order.

The default and only implemented order is deterministic relevance. The stable public object ID is the final tie-break. A chronological view remains a future design option and is not implemented by this contract.

## Public corpus

The read model contains exactly the current release objects whose canonical source record has `trace.tier === "source_verified"`.

```text
PUBLIC_SEARCH_DOCUMENT_COUNT=7995
HELD_SEARCH_DOCUMENT_COUNT=0
SOURCE_HELD_RECORD_COUNT=7928
SEARCH_TARGET=PUBLIC_OBJECT_PAGES_ONLY
```

Held records, review-only records, TRACE records, and Open Inquiry records cannot enter the Search document builder. Search results route only to `/surfaces/{surfaceId}`.

## Matching and filters

Text matching is limited to public-safe values:

- exact stable object ID;
- title;
- source-reported public credited designer/studio label where available;
- public place label where available.

The deterministic core preserves Unicode NFC/NFKC normalisation, case folding, punctuation and separator normalisation, safe Latin diacritic folding, exact matching, prefix and substring matching, all-token matching, bounded Optimal String Alignment typo handling, stable tie-breaks, cursor binding, and release/checksum gates.

Hard filters are:

- Year or inclusive year range;
- Object type;
- Theme;
- Movement.

Every selected filter is conjunctive. A record that fails any selected filter is excluded before ranking and cannot remain because of a high relevance score. Theme and movement are accepted public folder memberships; no theme or movement is inferred.

## Result contract

Each card can expose only:

- public stable object ID and title;
- public credited label when available;
- display date and numeric year range;
- public place label;
- object type;
- public theme and movement labels;
- delivery state;
- canonical object-page route;
- a plain-language match explanation.

The API may retain a numeric score for audit. Normal product UI does not show it. Public explanations use bounded phrases such as `Exact title`, `Matched title and year`, `Matched movement`, `Matched all query terms`, and `Matched spelling variation`.

Missing values remain `null` or empty arrays. Search never substitutes `Unknown`, `Unspecified`, synthetic labels, or inferred categories for absent public metadata.

## Workflow and state

The homepage provides a direct form that submits to `/search` and curated starter queries derived from real searchable values. It does not call a language model to populate the empty state and does not import TRACE runtime code.

The `/search` workspace supports desktop and mobile, URL-bound query and filter state, browser back/forward, release-bound cursor pagination, loading, zero results, partial optional metadata, error, retry, and return from an object page to the retained Search URL. Querying remains server-side; the full index is never sent to the browser.

## Guidance boundary

After deterministic results exist, the shared guidance service may add one or two orientation sentences and up to four server-approved next steps under the label `System suggests`. Guidance cannot retrieve candidates, apply filters, rank or include records, change metadata, create categories, generate object IDs, or mutate Search state until the visitor selects a suggestion.

Guidance failure always degrades to a deterministic fallback and never changes the Search response.

## Delivery boundary

This implementation is a functional reference UI, not final visual design. It performs no manual deployment and introduces no production deployment configuration.
