# Digest and schema parity

The verifier records count-vector, stable-key-set, normalized-content, schema, migration manifest, asset/data, and release fingerprints for both independent destinations. All A/B values required by their contract must match exactly.

Both destinations matched exactly:

- count vector: `92eda020d2ac9b2e60bb364f63758700df793e43fdc30dcf065120ee9b1ff66b`;
- stable-key set: `9bf3491b9c6603f3a7f8f141f2d9abac915ec1b91cd442b9248190263a8835a0`;
- normalized content: `a0fa7aaeb84b383371c20340afa2c2a5c7f12408102767de189225cc93e478b9`;
- post-import schema: `df1e7741e59e5e6bf1ca80f2a33edfad1abb2fc6d95b57d4d6993b49917020dd`.

The independent full projection A/B digest also matched at `11d92b70bd3a87113d4daabac2b5e4e38a3416cc55be894b42b0dd3d072ca640`. `FULL_A_B_DIGEST_PARITY=PASS`, `SCHEMA_HASH_A_B_PARITY=PASS`, and `FINAL_SCHEMA_HASH=PASS`.
