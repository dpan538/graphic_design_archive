# State machine

Supported actions: SELECT_CATEGORY, FOCUS_NODE, EXPAND_NODE, COLLAPSE_NODE, MOVE_FOCUS, SELECT_COMPOSITION, RESET_CATEGORY, EXPORT_CURRENT_STATE. Always use the complete returned state; treat a stale-state 409 as a prompt to retrieve the map/state again.
