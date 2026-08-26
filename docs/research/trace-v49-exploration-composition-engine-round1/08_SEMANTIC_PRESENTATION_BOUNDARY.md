# Semantic/presentation boundary

`semantic_core` contains image identity, seeds, nodes, frozen-qualified and admitted associations, all composition states, topology and candidate topologies, depth, gap nodes, split components, and semantic version. Changing admission, pruning, split, gap, or topology changes `SEMANTIC_CORE_HASH`.

`evidence_core` contains support status, strength, confidence, mandatory D1/D5/D7 results, provenance references, and qualification. `provenance` resolves every admitted connection from assessment to evidence records, source records, and stable URLs.

`presentation_hints` contains circular peer positions, branch slots, fixed node radius, fixed undirected edge width, gap hint, cosmetic order, and optional seed. Coordinates, rotation, spacing, and seed change only `PRESENTATION_HASH`. `semantic_mutation_permitted=false` is mandatory.

Allowed seeded variation: circular rotation, equivalent peer order, small spacing jitter, and branch placement. Forbidden seeded variation: qualification, admission, pruning, split, topology selection, and gap classification.

The research renderer uses no causal/temporal arrowheads, no strength-weighted lines, no importance sizing, no vertical hierarchy, no historically central position, and no distance-to-strength mapping. Support class is available as text provenance only; it is not a visual credibility or importance rank.
