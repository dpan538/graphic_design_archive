# Scope and method

The engine replays only sealed Round 9–11 TSV and JSON receipts. It freezes exact IDs, senses, labels, decisions, roles, evidence references, qualifications, contestation, and gap participation before executing seed, flow, tree, or instance functions.

The pipeline is `FrozenCandidatePackage → InquirySeed → PrimaryInquiryFlowPlan → InquiryTreeStrategy → BoundedInquiryTree → ResearchInquiryInstance`. Python standard-library functions are the reference implementation; JSON Schemas are normative; TypeScript only loads, rejects, canonicalizes, hashes, and checks shared fixtures.

Coverage is computed as distinct unions at corpus, candidate, candidate-class, pair-question, and instance levels. No unrelated corpus row is attributed to an Instance. Trees have one root and one primary inquiry flow, at most two semantic Nodes, two siblings, depth four, and seven total items.
