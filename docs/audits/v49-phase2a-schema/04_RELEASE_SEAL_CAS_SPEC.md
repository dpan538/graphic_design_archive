# v49 Phase 2A — Release, seal and CAS physical specification

## Two independent boundaries

Research releases and visual-registry releases each use the closed lifecycle
`draft → candidate → validated → sealed`. A visual registry stores the exact
compatible research release ID and manifest SHA; it does not mutate the
research release. Each boundary has a separately locked current pointer and
generation.

## Candidate and validation

Draft builders are controlled `SECURITY DEFINER` routines with
`search_path=pg_catalog`. Closing a candidate computes a canonical JCS
fingerprint over copied projections, inventories, policies, evidence and
required receipt profiles. Candidate children, copied manifests and inventory
rows are guarded from later mutation.

Named receipt profiles declare the complete required receipt set. Reviewers
record typed receipts; validation checks the exact required set, typed source
copy invariants, evidence/review gates, registry activity, zero-unclassified
baselines and stored fingerprint. A single arbitrary PASS row cannot satisfy
validation.

## Seal

Seal executes only in a `SERIALIZABLE` transaction. It revalidates the stored
candidate, builds canonical JCS manifest bytes, checks the supplied SHA-256,
inserts the immutable manifest and seal event, and transitions the parent to
`sealed` in the same transaction. Sealed parents, entries, memberships,
manifests and metadata reject `INSERT`, `UPDATE` and `DELETE` by runtime roles.

Detached verification recomputes immutable copied bytes and does not join
mutable working decisions. The sidecar binds boundary ID, seal identity,
candidate fingerprint, manifest SHA, verifier version and receipt digest.

## Compare-and-swap

Promotion functions lock the pointer row, require non-null expected generation
and exact expected ID/hash, require a sealed and independently verified target,
and append both successful and failed CAS attempts. A mismatch returns a
failed structured result without changing the pointer. Research and visual
pointers are updated independently; visual promotion additionally locks and
checks the compatible research pointer pair.

## Post-seal sidecars

Endpoint health and takedown changes append sidecar events instead of changing
sealed registry rows. Health can only reduce the base delivery mode. Active or
latched takedown is more restrictive and always wins. Takedown creation and
stricter correction share the visual-release advisory lock and atomically
append every affected sealed-entry sidecar plus audit event. The public view
starts from an empty allowlist DTO: pixel/source/canonical locators are
structurally absent unless the effective mode permits them.

## Executable oracles

The exact negative and positive tests are registered in
[05_NEGATIVE_TEST_REGISTER.tsv](05_NEGATIVE_TEST_REGISTER.tsv). They cover
post-seal mutation, stale/NULL CAS, unsealed promotion, pointer independence,
rights/policy/health caps, takedown precedence, hostile role calls,
serializable seal and zero TRACE/rights states.
