# Build contract

Every request binds a constraint-package hash and returns exactly one receipt. Rejection receipts contain precise failure codes, request hash, package hash, and compiler version, with no partial Image. Synthetic success receipts contain immutable content-addressed Image identity, version, compiler/package/request/Image hashes, seed, and `syntheticTestOnly=true`. Production research TSV reads and fallback authorization are absent.
