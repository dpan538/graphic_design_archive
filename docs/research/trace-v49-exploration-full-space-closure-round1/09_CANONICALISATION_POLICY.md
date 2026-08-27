# Canonicalisation Policy

Canonical identity is layered and deterministic:

1. an association-subgraph hash covers sorted admitted vocabulary and association IDs;
2. a topology hash adds the evaluated topology family and governed gate values;
3. a seed hash adds one admitted seed node;
4. a category-entry hash adds one database-authoritative category;
5. state identity adds focus and the sorted expansion subset;
6. semantic and presentation hashes remain separate;
7. export identity adds the preset and theme-token set without changing semantic identity.

Input ordering, labels used only for presentation, and runtime request order cannot change semantic identity. Hash collision and duplicate-canonicalisation counts must remain zero. All IDs in downstream state, transition, workflow, and export ledgers chain back to the frozen graph and database snapshot `v49:ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e`.

The registry hash is `0eadfc020e7a97cb0f9eb4b2c82bd119337ca580bdcc0e297d8f137db0bb372b`. The production read-model SHA-256 is `53eaf59c95446eeb3781a7153183c54b3ff59fd52f21744cc917053959dfdcc9` and its audit equivalence mismatch count is `0`.

Round 16 legacy reconciliation covers all 11 legacy compositions with distribution `{"PRESERVED_CANONICAL":7,"REJECTED_WITH_REASON":4}`. A rejected triangle is explained as a stricter v2 topology correction, not silently relabelled.

Sources: `docs/audits/v49-exploration-full-space-closure-round1/raw/canonical-composition-registry-v2.json` and `docs/audits/v49-exploration-full-space-closure-round1/raw/production-read-model-metadata-v2.json`.
