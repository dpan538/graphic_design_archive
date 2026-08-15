# Public-boundary runtime receipt

The held-sentinel source in `frontend/src/lib/read-platform/test-fixtures.ts` was read only to calculate this SHA-256, which is the only recorded sentinel representation:

`HELD_SENTINEL_SHA256=0c39ab13f4285b5da8baad3722ca39ed392af9e1dbd091b790c3ef77eae2649c`

The full five-layer dynamic verification did not run to completion: the adapter vector stopped before complete API scanning and the browser page realm has no `window.fetch`. No zero count is inferred from a static code review.

```text
HELD_SENTINEL_API_MATCH_COUNT=UNVERIFIED
HELD_SENTINEL_HTML_MATCH_COUNT=UNVERIFIED
HELD_SENTINEL_DOM_MATCH_COUNT=UNVERIFIED
HELD_SENTINEL_BUNDLE_MATCH_COUNT=UNVERIFIED
HELD_SENTINEL_NETWORK_MATCH_COUNT=UNVERIFIED
PUBLIC_DTO_FORBIDDEN_KEY_COUNT=UNVERIFIED
REMOTE_VISUAL_DOM_ATTRIBUTE_COUNT=UNVERIFIED
REMOTE_PIXEL_NETWORK_REQUEST_COUNT=UNVERIFIED
UNEXPECTED_NON_LOCAL_NETWORK_REQUEST_COUNT=UNVERIFIED
FAILED_REQUIRED_REQUEST_COUNT=UNVERIFIED
REAL_TRACE_TOTAL_EXACT=0
TRACE_GHOST_NODE_COUNT=UNVERIFIED
TRACE_DEFAULT_RELATION_LINE_COUNT=UNVERIFIED
TRACE_INFLUENCE_CLAIM_COUNT=UNVERIFIED
SYNTHETIC_TRACE_PUBLIC_MATCH_COUNT=UNVERIFIED
```

The source-level fixture still declares zero positive visual rights and an unavailable visual registry; this receipt does not elevate that static fact into runtime public-boundary acceptance.
