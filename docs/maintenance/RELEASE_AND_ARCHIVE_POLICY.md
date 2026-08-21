# Release and archive policy

Release history is preserved through verified annotated tags, not by copying obsolete trees into an active `archive/` directory. The v49 source anchor is `v49-data-api-closure-20260821`, pointing to commit `d78f496bcdf2cd6941791986007cd7a885c4c532` and tree `f0549c319d1e0b0cf5e0aab5a2b297361675b701`.

Before branch, worktree, or tracked historical content is removed, its exact commit must be reachable from a pushed immutable tag or retained branch. Remote object SHA and peeled commit are verified independently. No history rewrite, force-push, BFG, filter-repo, LFS migration, or aggressive GC is permitted.

Active release inputs and evidence remain in place. Historical raw sources and rights-sensitive captures are not duplicated into a new archive. Recovery uses `git show <tag>:<path>` or a detached worktree at the tag.

