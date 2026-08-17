# Fixed start and boundary

| Item | Value |
| --- | --- |
| Source branch | `fix/v49-release-projection-snapshot-20260816` |
| Source SHA | `dc76920e3d843c9128e73dcec7ce7f26da7cfa51` |
| Closure branch | `fix/v49-release-projection-snapshot-closure-20260816` |
| Historical migrations/functions edited | false |
| Frontend/API/browser run | false |
| Staging/full population/extractor accessed | false |
| Production database touched | false |
| Feature/stable/main advanced | false |

Commands used for the fixed start were `git fetch origin`, exact `rev-parse`
checks, `merge-base --is-ancestor`, and a clean new worktree check.  The
previous partial checkpoint and its audit package were never modified.
