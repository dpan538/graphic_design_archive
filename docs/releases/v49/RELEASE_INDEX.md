# v49 release index

The immutable source release is annotated tag `v49-data-api-closure-20260821` at `d78f496bcdf2cd6941791986007cd7a885c4c532` (tree `f0549c319d1e0b0cf5e0aab5a2b297361675b701`). It preserves the complete pre-hygiene database closure, API closure, historical data, audit evidence, and repository state.

- Release manifest: `docs/releases/v49/RELEASE_MANIFEST.json`
- Source checksums: `docs/releases/v49/SOURCE_TREE_FILES.sha256`
- Data inputs: `docs/releases/v49/DATA_INPUT_MANIFEST.json`
- Audit index: `docs/releases/v49/AUDIT_INDEX.md`
- Active database root: `database/`
- Historical database skeleton: `db/` at `v49-data-api-closure-20260821` only

The active tip may remove anchored historical captures, prompts, reports, generated intermediates, and `db/`; retrieve them with `git show v49-data-api-closure-20260821:<path>` without rewriting history.
