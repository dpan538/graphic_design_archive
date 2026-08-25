# v49 release index

The immutable source release is annotated tag `v49-data-api-closure-20260821` at `d78f496bcdf2cd6941791986007cd7a885c4c532` (tree `f0549c319d1e0b0cf5e0aab5a2b297361675b701`). It preserves the complete pre-hygiene database closure, API closure, historical data, audit evidence, and repository state.

- Release manifest: `docs/releases/v49/RELEASE_MANIFEST.json`
- Source checksums: `docs/releases/v49/SOURCE_TREE_FILES.sha256`
- Data inputs: `docs/releases/v49/DATA_INPUT_MANIFEST.json`
- Audit index: `docs/releases/v49/AUDIT_INDEX.md`
- Active database root: `database/`
- Historical database skeleton: `db/` at `v49-data-api-closure-20260821` only

The active tip may remove anchored historical captures, prompts, reports, generated intermediates, and `db/`; retrieve them with `git show v49-data-api-closure-20260821:<path>` without rewriting history.

## Main integration — 2026-08-25

- Old main anchor: `592c765d0af5bf15b1666784dce784ac8e22624d` and annotated rollback tag `main-pre-v49-research-integration-20260825`.
- Preserved Round 9 tip: `47978c519c3c7141690e3894315a1ef1b7a403db`.
- New main anchor: the single integration commit identified by annotated tag `v49-research-main-integration-20260825`.
- Integration package: `docs/releases/v49/main-integration-20260825/`.
- Audit package: `docs/audits/v49-main-integration-20260825/`.
- History policy: all 72 incoming commit SHAs are preserved; detailed descriptions live in the versioned ledger and narratives rather than rewritten messages.
- Authority policy: Round 6 object similarity and Round 7 object NLP remain superseded; Round 8 remains authoritative; Round 9 provides research candidates, not active product vocabulary.
- Next research gate: Round 10 `DESIGN_HISTORY_RELATION_GRAMMAR_ROUND1`.

The integration is documentation and reachability closure only. It performs no deployment and no branch cleanup.
