# Runtime schema hardening

Round 11 constraint-package and build-request inputs now receive exact-field runtime checks, duplicate identity checks, dangling-reference checks, activation consistency checks, arity/party-role checks, non-empty provenance and label checks, and explicit origin-policy enforcement. Recursive structural inspection rejects archive-object, Context, Spacetime, model, and vector shapes even if `forbiddenInputKinds` is empty.

Flow origins are distinct (`EVIDENCE_BACKED`, `GENERATIVE_COMPOSITION`, `USER_COMPOSED`, `RESEARCH_INQUIRY`) and a pair policy explicitly declares allowed origins. Inquiry links, evidence flows, structural conditions, contrast links, qualification links, and gap links remain epistemically distinct. Schema-aware canonicalization sorts only declared unordered arrays and preserves ordered flow/tree arrays; unknown array ordering fails.
