# Neighbourhood governance

A candidate is eligible only when its frozen Round 14 record has `activeForProximity=true`. Direct and skip-one eligibility are copied, not recalculated. Relative to the seed, an incident candidate is a direct neighbour and an edge reached after one admitted step is skip-one. Depth beyond two is outside the bounded semantic image.

The node budget remains eight, inherited from the Round 14 inspectability contract. Larger 10-, 20-, and 40-node synthetic graphs are deterministically decomposed into bounded windows before image composition. This is composition partitioning, not historical grouping.

Governance order:

1. canonicalize node, seed, and association identities;
2. remove duplicate association inputs idempotently;
3. structurally exclude every frozen failure;
4. group eligible candidates by ordinal evidence vector;
5. admit full groups while the topology-derived degree bound remains satisfied;
6. preserve a tied cutoff as unresolved and prune only strictly weaker or already capacity-blocked candidates;
7. compute split, gap, and topology states;
8. construct provenance and semantic hash;
9. add seeded presentation hints and the separate presentation hash.

Input permutation, pair reversal, duplicate input, failed-control injection, and visual-seed changes cannot alter the semantic result.
