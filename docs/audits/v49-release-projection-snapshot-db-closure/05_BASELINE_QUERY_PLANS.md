# Baseline query plans

Raw 1k and 2k expanded plans, nested statements, BUFFERS, WAL, SETTINGS, timing, sort/hash details, loop counts, and query fingerprints are preserved under `raw/baseline/stage-1000/` and `raw/baseline/stage-2000/`.

At 2k the parity fingerprint joined projected rows by folder, object, and role but omitted ordinal. The plan used a prefix merge/index path and evaluated the remaining object predicate as a join filter, removing 6,002,671 rows. It had 260,512 shared hits and 6,002,675 inner heap fetches. No disk spill or JIT transition explained the regression.
