# Listener root cause

Attempt 1 failed before Next route compilation with `listen EPERM` on the requested loopback port. A localhost listener/socket inspection confirmed that nothing was listening on 3107. This isolates the cause to the managed execution sandbox's bind permission, not fixture configuration, a database, hydration, or application source.

After one permitted correction—the same foreground PTY command in the localhost-capable context—Attempt 2 held the only task-owned listener and served the required API and page probes. No additional dev server was started. Other pre-existing listeners on ports 3000 and 4000 belonged to unrelated work and were not changed.
