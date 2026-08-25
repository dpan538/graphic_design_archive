# Commit description policy

Effective after the v49 main-integration commit. This policy is prospective: do not amend, rebase, filter, or otherwise rewrite earlier commits to apply it.

## Required format

```text
<type>(<scope>): concise subject

Why:
- why the change was necessary

What:
- concrete changes

Evidence:
- tests, audits, checksums, or research outputs

Boundaries:
- protected systems not modified
- explicit scope exclusions

Status:
- authoritative, provisional, superseded, or checkpoint
```

Use a conventional, specific `type` and a bounded `scope`. The subject should describe the outcome rather than the activity. Bodies must identify actual evidence and explicitly name protected Database, Search, Context, Spacetime, frontend, main, or deployment boundaries when relevant.

## Additional research fields

Research commits must also include:

```text
Research decision:
- the decision supported or rejected

Evidence basis:
- sources, corpus, methods, gates, and receipts

Limitations:
- uncertainty, exclusions, negative results, and known bias

Next gate:
- the exact condition for continuation, activation, or rejection
```

Research status must distinguish an active product decision from provisional input. A later supersession must preserve the earlier commit and document the replacement relation in a forward commit or release ledger.
