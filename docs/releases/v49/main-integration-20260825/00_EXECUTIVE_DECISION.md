# v49 main integration — executive decision

Date: 2026-08-25
Strategy: **FAST_FORWARD_ONLY**

`main` remained at `592c765d0af5bf15b1666784dce784ac8e22624d` while the authoritative linear v49 chain advanced to Round 9 at `47978c519c3c7141690e3894315a1ef1b7a403db`. The verified merge base is the old-main commit; the incoming range is exactly 72 commits ahead and zero behind. The decision is therefore to preserve all 72 commit objects and add one documentation-only integration commit before a non-force fast-forward update of `main`.

Detailed descriptions are recorded in the ledger and narrative documents instead of rewriting old messages. The pre-integration annotated rollback tag `main-pre-v49-research-integration-20260825` was pushed and remotely verified at `592c765d0af5bf15b1666784dce784ac8e22624d` before any main update.

## Authority decision

- Search, Context, and Spacetime remain ACTIVE/FROZEN.
- Round 6 object-centric similarity and Round 7 object NLP remain superseded research, retained for provenance.
- Round 8 conceptual reset is the active authoritative Exploration architecture.
- Round 9 relation terms are research candidates for Round 10 grammar work; they are not active product vocabulary.

## Prohibited outcomes

No rebase, squash, cherry-pick reconstruction, amend, filter operation, merge commit, force push, branch deletion, deployment, database change, or activation of Round 9 terms is authorized. The containing integration commit documents history; it does not begin Round 10.

## Counts

- Incoming preserved commits: 72
- Integration commits: 1
- Expected final advance from old main: 73
- Existing SHA preservation: 72/72
- Authority distribution: {'ACTIVE_AUTHORITATIVE': 7, 'ACTIVE_FOUNDATION': 26, 'HISTORICAL_NEGATIVE_RESULT': 1, 'INTERMEDIATE_CHECKPOINT': 18, 'MAINTENANCE_SUPPORT': 17, 'RELEASE_ANCHOR': 2, 'SUPERSEDED_BUT_RETAINED': 1}
