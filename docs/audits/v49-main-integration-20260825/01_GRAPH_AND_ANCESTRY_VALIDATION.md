# Graph and ancestry validation

- Expected and observed old main: `592c765d0af5bf15b1666784dce784ac8e22624d`
- Expected and observed Round 9 tip: `47978c519c3c7141690e3894315a1ef1b7a403db`
- Merge base: `592c765d0af5bf15b1666784dce784ac8e22624d`
- `rev-list --count 592c765d0af5bf15b1666784dce784ac8e22624d..47978c519c3c7141690e3894315a1ef1b7a403db`: 72
- `rev-list --count 47978c519c3c7141690e3894315a1ef1b7a403db..592c765d0af5bf15b1666784dce784ac8e22624d`: 0
- Incoming parent topology: one parent per commit, first parent old main, every later parent the preceding incoming SHA.
- Existing commit identity preservation: 72/72.
- Pre-integration tag peeled commit: `592c765d0af5bf15b1666784dce784ac8e22624d`.

Raw proof is preserved in `raw/preflight-validation.tsv` and `raw/incoming-commit-metadata.tsv`.
