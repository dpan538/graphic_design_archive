# Browser runtime receipt

One local in-app-browser tab was attached to the retained 3107 listener. At its fixed available viewport (1280×720, DPR 2), `/search` and `/folders/region` loaded hydrated controls without a populated Next error portal or browser runtime/hydration error. An actual click on the Archive `Next folder` button changed the active folder from Africa to Americas.

The browser-control surface did not expose a viewport-resize facility, so the required mobile/desktop viewport matrix, 900/901 heat test, menu geometry, touch CDP sequence, reduced-motion matrix, and eight specified screenshot dimensions could not be verified.

Most importantly, inside the actual rendered TRACE page, `window.fetch` is not a function. TRACE showed `release descriptor is unavailable` while retaining its loading text. This is a real browser-environment limitation and makes the browser unable to exercise dynamic API-dependent slices; it is not classified as an honest empty state. No final screenshot was saved, because loading/error output may not serve as acceptance evidence.

```text
BROWSER_CONTEXT_COUNT=1
BROWSER_CORE_ROUTE_COUNT=2
BROWSER_VERIFIED=false
VALID_SCREENSHOT_COUNT=0
SCREENSHOT_UNIQUE_HASHES=0/8
ARCHIVE_BEFORE_AFTER_OBJECT_ID_DIFFERENT=UNVERIFIED
TOUCH_POINTER_TYPE=UNVERIFIED
SWIPE_CONTINUOUS_FEEDBACK_SAMPLES=0/3
SWIPE_SNAP_SETTLED=UNVERIFIED
KEYBOARD_FLOW_PASS=0/3
ESCAPE_CLOSE_FOCUS_RETURN=UNVERIFIED
FOCUS_TRAP_COUNT=UNVERIFIED
ACCESSIBILITY_GATE_STATUS=UNVERIFIED
REDUCED_MOTION_ROUTES_PASS=0/3
BREAKPOINT_900_901_STATUS=UNVERIFIED
```
