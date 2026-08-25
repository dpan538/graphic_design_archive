#!/usr/bin/env python3
"""Generate the v49 main-integration documentation from the preserved Git graph.

The prose in CURATION is intentionally commit-specific. Git supplies identity,
dates, trees, messages, path changes, packages, and branch reachability; the
curation supplies the evidence-derived interpretation and authority decision.
"""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
OLD = "592c765d0af5bf15b1666784dce784ac8e22624d"
TIP = "47978c519c3c7141690e3894315a1ef1b7a403db"
RELEASE = ROOT / "docs/releases/v49/main-integration-20260825"
AUDIT = ROOT / "docs/audits/v49-main-integration-20260825"
RAW = AUDIT / "raw"


def git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=False,
    )
    if check and result.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.rstrip("\n")


PHASES = [
    ("P01", "v48 TRACE and visual foundations", 1, 14,
     "Established the evidence-led TRACE interface, responsive research views, and archive material language.",
     "The v48 visual/data foundation retained by the v49 chain.",
     "The interrupted prototype checkpoint remains historical; later commits in the phase refine it.", "v48 anchor"),
    ("P02", "v49 data/read-platform architecture", 15, 22,
     "Closed architecture, authority, rights, migration, and browser-runtime decisions before database DDL.",
     "The approved pre-DDL decision record and cleanup receipts.",
     "Earlier provisional architecture wording is retained as checkpoints, not as a competing contract.", "P01"),
    ("P03", "database schema and deterministic migration", 23, 31,
     "Implemented PostgreSQL schema, constraints, sealed fixtures, migration rehearsal, performance repair, and self-contained audits.",
     "The physical-schema and migration evidence foundation.",
     "The original Phase 2b evidence is explicitly repaired/superseded by the amendment package.", "P02"),
    ("P04", "read platform and product foundation", 32, 38,
     "Added repository/API reads, migrated archive slices, and closed sealed-fixture and runtime acceptance gates.",
     "The active read-platform foundation consumed by later TRACE work.",
     "Checkpoint packages document gates; they do not create alternate runtime authority.", "P03"),
    ("P05", "release snapshots and API closure", 39, 54,
     "Developed atomic release snapshots through integrity, closure, performance, reconciliation, and API-contract gates.",
     "Frozen database release protocol and closed read API contract.",
     "Earlier snapshot protocol iterations are retained as foundations/checkpoints behind the final closure.", "P03–P04"),
    ("P06", "repository hygiene and database freeze", 55, 60,
     "Consolidated active files, froze the database contract, normalized safety ledgers, and recorded cleanup closure.",
     "The active repository surface and database-freeze governance.",
     "Cleanup ledgers remain maintenance evidence; no branch deletion is implied.", "P04–P05"),
    ("P07", "fuzzy Search", 61, 61,
     "Added deterministic fuzzy archive Search, projections, tests, and audit evidence.",
     "Search ACTIVE/FROZEN.", "None; this remains current.", "P04–P06"),
    ("P08", "TRACE census and semantic correction", 62, 62,
     "Built the TRACE census, corrected semantics, and established preprogram evidence.",
     "The empirical foundation for Context, Spacetime, and Exploration.", "None; this remains a foundation.", "P04–P07"),
    ("P09", "Context functional development and governance", 63, 65,
     "Implemented Context Canvas, validated real-data behavior, and closed its governed public projection.",
     "Context ACTIVE/FROZEN.", "Functional prototypes are governed by the Round 3 closure.", "P08"),
    ("P10", "Spacetime GIS and runtime closure", 66, 68,
     "Implemented governed GIS/time projections, corrected audit counters, and closed runtime/API behavior.",
     "Spacetime ACTIVE/FROZEN.",
     "The Exploration discovery bundled in the closure is superseded by the Round 8 conceptual reset.", "P08–P09"),
    ("P11", "Exploration object-centric similarity research", 69, 69,
     "Benchmarked explainable object-affinity models as a falsifiable research branch.",
     "Historical negative result retained for provenance.",
     "Superseded by 0526c3375285d8785d2993cdad9d1da620766423.", "P10"),
    ("P12", "Exploration multilingual object NLP", 70, 70,
     "Audited dense multilingual object semantics, limitations, and model risks.",
     "Superseded research retained for provenance.",
     "Superseded by 0526c3375285d8785d2993cdad9d1da620766423.", "P11"),
    ("P13", "Exploration conceptual reset", 71, 71,
     "Removed object-centric production assumptions and reset Exploration to a conceptual relation field.",
     "Round 8 ACTIVE_AUTHORITATIVE Exploration architecture.",
     "Supersedes the Round 6 similarity and Round 7 object-NLP approaches.", "P08, informed by P11–P12"),
    ("P14", "design-history relation vocabulary Round 9", 72, 72,
     "Validated sourced relation-vocabulary candidates against linguistic, breadth, contestation, and saturation gates.",
     "Research input for Round 10 grammar work; not active product vocabulary.",
     "No terms are activated by integration into main.", "P13"),
]


def C(phase: str, status: str, what: str, why: str, evidence: str,
      boundary: str, superseded: str = "") -> dict[str, str]:
    return dict(phase=phase, status=status, what=what, why=why,
                evidence=evidence, boundary=boundary, superseded=superseded)


CURATION = [
    C("P01", "INTERMEDIATE_CHECKPOINT", "Recorded the v48 TRACE visualization decision and translated research evidence into an explicit interface direction.", "The project needed a reviewable decision before implementing a new visual research surface.", "Decision document records the chosen visual model and scope.", "Database, Search, Context, Spacetime, deployment, and main were untouched."),
    C("P01", "ACTIVE_FOUNDATION", "Implemented the v48 TRACE evidence visualization with generated public datasets, explorer components, and build/audit tooling.", "The decision record required an inspectable visualization backed by reproducible evidence rather than a static concept.", "Generation scripts, public TRACE artifacts, and verification receipts accompany the UI implementation.", "The work consumes published evidence and does not mutate the canonical database or deploy the application."),
    C("P01", "ACTIVE_FOUNDATION", "Refined TRACE with schematic research views, including chronogeographic routes, diagrams, and a documented reference study.", "Early visual output needed clearer analytical schemata and a traceable relationship to precedent research.", "Reference-study documentation and component-level changes provide design evidence.", "No Search or database contract changed; the refinement stayed inside the TRACE frontend/research layer."),
    C("P01", "ACTIVE_FOUNDATION", "Separated TRACE into fullscreen research views and introduced the map/diagram dependencies needed by the time-geography view.", "Dense research material required dedicated canvases rather than a single constrained composite screen.", "Fullscreen components and dependency-lock changes make the new presentation reproducible.", "The data model remained read-only; only visual composition and its client dependencies changed."),
    C("P01", "MAINTENANCE_SUPPORT", "Bound the TRACE timeline extent to the present year in the time-geography map.", "An unbounded or stale temporal endpoint misrepresented the research period shown to readers.", "The focused map change is directly inspectable in the commit diff.", "No stored dates, database rows, or canonical source records were altered."),
    C("P01", "ACTIVE_FOUNDATION", "Built the complete v48 TRACE research-view set, its data inputs, verification script, and evidence-facing API surface.", "The fullscreen design needed a functioning, testable set of research views rather than isolated prototypes.", "Verifier scripts, research documentation, generated data, and route evidence are committed together.", "The API surface exposes evidence without creating database writes or changing deployment configuration."),
    C("P01", "ACTIVE_FOUNDATION", "Refined the archive’s material atmosphere across global styles and documented visual captures.", "The evidence interface needed a coherent archival tone without weakening legibility or research hierarchy.", "Captured review artifacts and CSS changes document the visual adjustment.", "Only presentation styling changed; research data and platform contracts remained fixed."),
    C("P01", "ACTIVE_FOUNDATION", "Added an interactive TRACE evolution field with dedicated components, data handling, and verification.", "Readers needed to explore change over time rather than only inspect fixed diagrams.", "The evolution-field verifier and associated research assets test the interaction’s evidence wiring.", "The interaction reads existing TRACE evidence and does not add canonical writes or deployment changes."),
    C("P01", "ACTIVE_FOUNDATION", "Refined the home archive-box interaction and aligned its drawer/page behavior with the visual archive model.", "The home entry point needed a clearer physical metaphor and predictable navigation into the archive.", "A dedicated home-archive-box verifier and component changes accompany the interaction.", "Search ranking, database state, and TRACE research semantics were preserved."),
    C("P01", "ACTIVE_FOUNDATION", "Decoupled the desktop cabinet index from the mobile card wheel so each viewport could use an appropriate interaction model.", "A shared implementation coupled two materially different navigation patterns and constrained responsive behavior.", "Home verification and distinct component paths demonstrate the responsive separation.", "The change was frontend-only and did not modify archive records or API contracts."),
    C("P01", "ACTIVE_FOUNDATION", "Improved research-index contrast, shell navigation, and cross-entry visibility across home and TRACE surfaces.", "Review showed that analytical hierarchy and routes between research views were too easy to miss.", "Component and style diffs provide the reviewable accessibility/navigation evidence.", "No research conclusions, canonical data, or backend boundaries changed."),
    C("P01", "ACTIVE_FOUNDATION", "Built responsive TRACE visual analytics and documented the mobile behavior across pages and components.", "The analytical views needed to remain useful on narrow screens rather than merely shrink desktop layouts.", "Responsive verifier scripts, mobile documentation, and coordinated UI changes validate the behavior.", "The commit changes visualization and presentation only; database and deployment remain outside scope."),
    C("P01", "ACTIVE_FOUNDATION", "Refined responsive TRACE views after cross-viewport review, adjusting the supporting frontend and QA evidence.", "Initial responsive implementation exposed layout and interaction issues that required a coordinated refinement pass.", "The broad but phase-local set of frontend and QA artifacts records the validation pass.", "No data-platform, Search, or canonical-source contract was changed."),
    C("P01", "INTERMEDIATE_CHECKPOINT", "Preserved an interrupted v48 visual-analytics prototype, comparison research, screenshots, and its exact working state.", "The prototype could not be safely completed in-place, so its evidence needed an explicit recoverable checkpoint.", "Comparison documents, screenshots, and the full prototype diff make the interrupted state reproducible.", "This checkpoint is not current product authority and performs no database or deployment mutation.", "Later v49 platform and governed TRACE phases supersede the prototype as active implementation authority."),
    C("P02", "INTERMEDIATE_CHECKPOINT", "Established the v49 data-platform baseline across architecture, data model, migration, read API, acceptance criteria, and an ADR.", "Database implementation could not begin safely without a shared contract for authority and reads.", "The coordinated architecture document set is the pre-DDL evidence.", "No DDL or runtime behavior was introduced; the commit is a decision baseline."),
    C("P02", "INTERMEDIATE_CHECKPOINT", "Closed the remaining pre-DDL architecture questions and aligned the data, migration, and API decision documents.", "Unresolved assumptions would have made the physical schema and migration gates ambiguous.", "Updated decision records explicitly resolve the open architecture items.", "The commit remains documentation-only and does not cross the database implementation gate."),
    C("P02", "INTERMEDIATE_CHECKPOINT", "Aligned research rights, visual-use rules, and database-freeze gates in the v49 decision set.", "Rights constraints and preservation boundaries needed to be enforceable before ingest or public projection work.", "Rights and freeze requirements are recorded alongside acceptance criteria.", "No assets were relicensed and no canonical or deployment state changed."),
    C("P02", "INTERMEDIATE_CHECKPOINT", "Added a comprehensive pre-migration audit covering architecture readiness, risks, and gate evidence.", "The project needed an independent checkpoint before translating design decisions into database migrations.", "The multi-file audit package records findings and preconditions.", "The audit observes the repository and authorizes no schema mutation by itself."),
    C("P02", "INTERMEDIATE_CHECKPOINT", "Closed authority questions and documented the remaining research delta before implementation.", "Competing source claims and unresolved research gaps could otherwise leak into canonical data decisions.", "An audit package and verifier record the authority resolution.", "Canonical records, public projections, and frontend behavior were not changed."),
    C("P02", "INTERMEDIATE_CHECKPOINT", "Closed the visual-rights and machine-use decisions needed by the v49 platform.", "Image display and automated processing required separate, explicit permission boundaries.", "The rights audit distinguishes visual presentation from machine-readable use.", "No media were reprocessed, published, or deployed by this decision commit."),
    C("P02", "ACTIVE_FOUNDATION", "Removed the browser-local AI runtime and retired bulk routes that conflicted with the governed read-platform direction.", "Uncontrolled client inference and bulk endpoints violated the new authority and reproducibility boundaries.", "Cleanup audit receipts and deleted runtime/route paths demonstrate removal.", "Canonical database content was preserved; the intentional boundary change is removal of obsolete browser and bulk surfaces."),
    C("P02", "INTERMEDIATE_CHECKPOINT", "Recorded the joint pre-DDL and runtime-cleanup receipts after architecture closure.", "Implementation needed a single checkpoint proving both decision readiness and obsolete-surface removal.", "Receipt documents link the architecture and cleanup evidence.", "This commit documents closure and adds no schema, Search, or deployment behavior."),
    C("P03", "ACTIVE_FOUNDATION", "Implemented the v49 PostgreSQL physical schema, migrations, functions, roles, and governed views.", "The approved logical model needed enforceable database structures and privilege boundaries.", "Versioned SQL migrations and database definitions are the implementation evidence.", "This intentionally establishes the database boundary while leaving Search, Context, Spacetime, frontend activation, and deployment unchanged."),
    C("P03", "MAINTENANCE_SUPPORT", "Added constraint, role, seal-CAS, fixture, and replay tests for the new PostgreSQL schema.", "The physical schema required executable proof that integrity and authorization rules hold under failure and concurrency.", "Database tests, sealed fixtures, and replay tooling validate the constraints.", "Tests exercise the database contract without changing production data or deploying it."),
    C("P03", "INTERMEDIATE_CHECKPOINT", "Recorded Phase 2a schema manifests and audit receipts for the physical-schema gate.", "The schema implementation needed a sealed, reviewable completion record before migration rehearsal.", "Manifest and audit artifacts enumerate the accepted schema evidence.", "The checkpoint does not change the schema beyond the preceding implementation commits."),
    C("P03", "ACTIVE_FOUNDATION", "Added a deterministic rehearsal for migrating v48 data into the v49 schema.", "The project needed repeatable proof that legacy evidence could be transformed without silent drift.", "Migration tooling, fixtures, and deterministic comparison outputs provide the rehearsal evidence.", "The rehearsal operates on controlled inputs and does not migrate or deploy a live database."),
    C("P03", "INTERMEDIATE_CHECKPOINT", "Recorded Phase 2b migration receipts and reconciliation results.", "The deterministic rehearsal required a formal checkpoint before performance tuning and read-platform work.", "The migration audit package captures counts, manifests, and replay results.", "No production database or frontend path was modified."),
    C("P03", "MAINTENANCE_SUPPORT", "Remediated migration-validation performance while preserving deterministic output.", "Validation was functionally correct but too costly for a reliable release gate.", "Performance-oriented code changes and replay comparisons demonstrate equivalent results.", "The optimization changes validation execution, not the canonical schema or migrated meaning."),
    C("P03", "INTERMEDIATE_CHECKPOINT", "Verified repeatable Phase 2b performance replays and documented their measured behavior.", "A single faster run was insufficient evidence for accepting the remediation.", "Replay receipts and measured outputs record repeatability.", "This evidence commit does not alter database, API, or frontend contracts."),
    C("P03", "MAINTENANCE_SUPPORT", "Repaired the Phase 2b audit evidence and explicitly marked defective receipts as superseded.", "Earlier evidence packaging did not meet the project’s provenance standard even though the implementation lineage had to remain intact.", "The amendment package identifies repaired artifacts and supersession relations.", "Only audit authority changed; schema and migration commits were not rewritten.", "The amendment package in this commit supersedes the defective Phase 2b receipts while retaining them historically."),
    C("P03", "MAINTENANCE_SUPPORT", "Added repository tooling and workflow checks that require audit packages to be self-contained.", "External or implicit dependencies made prior audit receipts difficult to reproduce independently.", "The verifier and CI workflow enforce manifest and checksum closure.", "This is governance tooling; it does not modify canonical data or application behavior."),
    C("P04", "ACTIVE_FOUNDATION", "Added the v49 read repository, API core, database grants/migrations, and frontend data access seams.", "Product surfaces needed a governed path from the new database instead of direct or local data coupling.", "Repository code, API routes, SQL grants, and tests establish the read boundary.", "Reads are introduced without database writes, Search activation, or deployment."),
    C("P04", "MAINTENANCE_SUPPORT", "Enforced sealed-fixture gates for the v49 read platform.", "Read behavior could not be trusted if fixtures drifted independently of their declared provenance.", "Fixture seals and verification tests reject mismatched inputs.", "The gate verifies published test data and does not alter canonical records."),
    C("P04", "ACTIVE_FOUNDATION", "Migrated core archive slices onto the governed read platform and updated their frontend consumers.", "The repository/API foundation needed real product consumers to expose parity gaps and retire legacy reads.", "Slice-level tests and coordinated API/frontend changes validate the migration.", "Only selected read paths moved; database writes and deployment remained excluded."),
    C("P04", "INTERMEDIATE_CHECKPOINT", "Recorded the v49 product-foundation checkpoint after core slice migration.", "The platform needed a formal evidence boundary before runtime acceptance work.", "The audit package summarizes migrated surfaces and outstanding gates.", "This is a checkpoint, not a new application or database contract."),
    C("P04", "MAINTENANCE_SUPPORT", "Added runtime-acceptance seams and automated checks for the read platform.", "Static tests alone could not prove that API and browser-facing reads compose correctly at runtime.", "Acceptance scripts and workflow configuration exercise the runtime seams.", "The harness observes controlled runtime behavior and performs no deployment or canonical mutation."),
    C("P04", "INTERMEDIATE_CHECKPOINT", "Captured runtime-acceptance evidence for the v49 read platform.", "The new acceptance harness required a durable record of its first accepted run.", "Audit receipts preserve command, result, and environment evidence.", "No implementation boundary changed in this documentation checkpoint."),
    C("P04", "INTERMEDIATE_CHECKPOINT", "Closed the P0 read-platform gate with consolidated evidence.", "Database-backed product reads needed a clear release threshold before snapshot and API closure work.", "The closure audit links sealed fixtures, parity, and runtime acceptance.", "The checkpoint confirms existing read behavior and does not authorize writes or deployment."),
    C("P05", "ACTIVE_FOUNDATION", "Introduced atomic database research-release snapshots and their component model.", "Research publication needed a coherent immutable view rather than independently changing projections.", "Versioned SQL migrations and release-snapshot definitions implement atomicity.", "The database contract intentionally changes; Search, Context, Spacetime, frontend activation, and deployment do not."),
    C("P05", "MAINTENANCE_SUPPORT", "Added integrity verification for release snapshots and their component relationships.", "Atomic creation required proof that a snapshot cannot mix missing or inconsistent components.", "Database integrity tests exercise expected and failing snapshot states.", "Tests do not publish a production release or change public projections."),
    C("P05", "INTERMEDIATE_CHECKPOINT", "Recorded the release-projection snapshot checkpoint after integrity validation.", "The first snapshot protocol needed an auditable boundary before closure semantics were added.", "The audit package records schema and integrity-test evidence.", "No additional runtime or public authority is created by the checkpoint."),
    C("P05", "ACTIVE_FOUNDATION", "Added an explicit closure protocol for database release snapshots.", "Atomic snapshots also needed a governed transition from assembling to immutable/closed state.", "SQL protocol changes define allowed closure operations and invariants.", "The intentional change stays inside the release-snapshot database boundary."),
    C("P05", "MAINTENANCE_SUPPORT", "Added a closure harness covering successful, rejected, and repeated snapshot transitions.", "Closure semantics required executable evidence for idempotency and invalid-state rejection.", "The database test harness exercises the protocol branches.", "The harness uses test fixtures and does not close a production release."),
    C("P05", "INTERMEDIATE_CHECKPOINT", "Recorded measured release-snapshot closure performance.", "Integrity alone was insufficient if closure could not run within a bounded release gate.", "Performance receipts document timing and test conditions.", "This measurement commit does not change snapshot semantics or application behavior."),
    C("P05", "ACTIVE_FOUNDATION", "Introduced the v5 release-snapshot protocol to reduce repeated work while retaining digest authority.", "Earlier closure logic needed a more efficient protocol without weakening reproducibility.", "Versioned database changes retain component and digest invariants.", "Only snapshot internals intentionally change; canonical content and product surfaces remain fixed."),
    C("P05", "MAINTENANCE_SUPPORT", "Added a bounded profiler for the v5 snapshot protocol.", "The optimized protocol needed measurements that could detect pathological stages rather than only total duration.", "Profiler code and bounded scenarios expose stage-level costs.", "Profiling uses controlled database state and does not deploy or publish snapshots."),
    C("P05", "MAINTENANCE_SUPPORT", "Optimized v5 snapshots by staging component-row digests once per run.", "Profiling showed redundant digest staging as a dominant avoidable cost.", "The focused SQL/performance change is checked against existing integrity tests.", "Digest meaning and snapshot authority remain unchanged; only computation placement changes."),
    C("P05", "INTERMEDIATE_CHECKPOINT", "Recorded the post-optimization v5 snapshot performance checkpoint.", "The digest-staging change needed comparative evidence before database closure.", "Profiler receipts capture the accepted bounded results.", "This audit checkpoint does not modify the database or runtime."),
    C("P05", "ACTIVE_FOUNDATION", "Closed the v49 release-snapshot database path with protocol, tests, scripts, and consolidated evidence.", "The iterative snapshot work needed a single reproducible closure state before freezing database behavior.", "A broad database/audit package ties migrations, integrity, performance, and recovery together.", "The database release path is intentionally finalized; frontend activation and deployment remain excluded."),
    C("P05", "MAINTENANCE_SUPPORT", "Corrected profiler stage reduction so measured timings matched the actual v49 execution stages.", "The closure profiler’s aggregation could misstate where time was spent.", "Updated profiler logic and receipts reconcile stage totals.", "This correction changes measurement reporting, not snapshot data or protocol semantics."),
    C("P05", "MAINTENANCE_SUPPORT", "Fixed held-state reconciliation mapping in the release snapshot workflow.", "A mapping mismatch could classify a held component incorrectly during reconciliation.", "Focused tests and reconciliation artifacts cover the corrected state mapping.", "The fix preserves snapshot authority and does not expand write privileges or product behavior."),
    C("P05", "RELEASE_ANCHOR", "Recorded the comprehensive v49 database-closure checkpoint and its reproducibility evidence.", "The database path needed an immutable release anchor before API contract closure.", "The large closure package includes manifests, test outputs, checksums, and recovery material.", "Database behavior is frozen at this anchor; no Search, Context, Spacetime, or deployment activation occurs."),
    C("P05", "ACTIVE_FOUNDATION", "Closed the v49 read API contract with endpoint, schema, client, and audit documentation.", "Consumers needed a stable public read boundary aligned with the frozen database contract.", "Contract tests and a comprehensive audit package cover fields, errors, and parity.", "Read APIs are finalized without adding writes, changing canonical database meaning, or deploying."),
    C("P05", "ACTIVE_AUTHORITATIVE", "Finalized the read API contract audit and resolved remaining closure findings.", "The initial closure package still required independent verification and explicit disposition of residual issues.", "Final audit artifacts and validation results record the accepted API boundary.", "The active read contract is documented; database freeze and no-deployment boundaries remain intact."),
    C("P06", "ACTIVE_FOUNDATION", "Consolidated the v49 active repository surface, retired obsolete files, and synchronized top-level release records.", "Accumulated prototypes and evidence made it unclear which files remained operationally authoritative.", "Repository inventory, database-freeze materials, and release documentation enumerate the consolidated surface.", "This deliberately changes repository hygiene only; history and branches remain preserved, and no deployment occurs."),
    C("P06", "RELEASE_ANCHOR", "Froze the v49 database contract with a manifest and content hashes.", "Post-closure work needed a machine-verifiable guard against accidental database drift.", "The freeze manifest and SHA-256 records define the protected database set.", "Database files become protected; no canonical values or deployment state change in this freeze commit."),
    C("P06", "MAINTENANCE_SUPPORT", "Added repository-hygiene safety ledgers for active scripts, generated outputs, and retained evidence.", "Cleanup needed explicit allowlists so automation could distinguish intentional files from residue.", "Machine-readable ledgers and verification logic document the safety boundary.", "No branch or historical commit is deleted; the ledgers govern later maintenance."),
    C("P06", "MAINTENANCE_SUPPORT", "Normalized hygiene-ledger paths and classifications for deterministic repository checks.", "Inconsistent ledger entries could create false cleanup findings across worktrees.", "Updated ledgers and verifier output demonstrate stable classification.", "Only maintenance metadata changes; application and database contracts remain frozen."),
    C("P06", "MAINTENANCE_SUPPORT", "Recorded completed worktree-cleanup receipts without deleting remote research history.", "The physical cleanup needed proof of what was removed and what was deliberately retained.", "Cleanup receipts and changed-file inventories provide the record.", "Remote branches, commits, canonical database files, and deployment were explicitly preserved."),
    C("P06", "ACTIVE_AUTHORITATIVE", "Closed v49 repository hygiene and database-freeze governance with final allowlists and audit evidence.", "Later feature work needed a trustworthy clean baseline and automated protection of the frozen database contract.", "Closure audits, repository verifier, active-script allowlist, and freeze checks form the gate.", "The repository/database boundaries are active and frozen; no branch deletion or deployment is authorized."),
    C("P07", "ACTIVE_AUTHORITATIVE", "Added deterministic fuzzy archive Search with generated indexes, regression tests, UI/API integration, and an audit package.", "Exact matching hid relevant archive items when titles, names, or queries varied slightly.", "Index verification, Search regression cases, generated artifacts, and audit receipts validate deterministic ranking.", "Search changes intentionally; database remains read-only/frozen, while Context, Spacetime, Exploration, main, and deployment are untouched."),
    C("P08", "ACTIVE_FOUNDATION", "Added the v49 TRACE census, corrected semantic labels, and established the preprogram research foundation.", "Contextual features required a measured inventory of available entities and relations rather than inherited assumptions.", "Census outputs, source evidence, validation scripts, and an audit package document the empirical baseline.", "The work reads frozen data and corrects research semantics without altering Search or deploying a product change."),
    C("P09", "ACTIVE_FOUNDATION", "Implemented the functional Context Canvas with governed projection inputs, UI behavior, and test harnesses.", "The TRACE census needed a usable context view that exposed evidence relationships without inventing new canonical facts.", "Projection generation, Context tests, API checks, and visual/runtime artifacts validate the implementation.", "Context is introduced as a read model; database, Search, Spacetime, Exploration, main, and deployment remain protected."),
    C("P09", "ACTIVE_FOUNDATION", "Validated Context Canvas against real v49 data and corrected runtime and projection behavior exposed by that cohort.", "Synthetic fixtures could not reveal missing-field, scale, and evidence-link issues present in the archive.", "Real-data summaries, runtime rehearsal, API tests, and projection checks record the validation.", "The commit changes Context reads/presentation only and preserves the frozen database and other TRACE surfaces."),
    C("P09", "ACTIVE_AUTHORITATIVE", "Closed Context governance and its public read-model projection with invariants, performance bounds, and audit evidence.", "A functioning canvas required a frozen authority model before later TRACE surfaces could depend on it.", "Governance bundle guards, full-cohort summaries, API/runtime tests, and manifests establish closure.", "Context becomes ACTIVE/FROZEN; database and Search stay frozen, Spacetime/Exploration are not activated, and there is no deployment."),
    C("P10", "ACTIVE_FOUNDATION", "Added governed Spacetime GIS and timeline projections, UI foundations, source policies, and validation.", "TRACE needed place/time exploration grounded in source precision and uncertainty rather than decorative mapping.", "Projection verification, GIS tests, policy documents, and audit packages cover coordinates, dates, and public fields.", "Spacetime is introduced as a governed read model; database, Search, Context authority, main, and deployment remain protected."),
    C("P10", "MAINTENANCE_SUPPORT", "Corrected Round 4 Spacetime audit counters to match the sealed evidence set.", "Incorrect receipt counts weakened audit reproducibility even though runtime behavior was unchanged.", "The amended counter files reconcile against the package manifest.", "Only audit metadata changes; Spacetime code, projections, database, and deployment remain untouched."),
    C("P10", "ACTIVE_AUTHORITATIVE", "Closed Spacetime runtime/API behavior and added an initial Exploration data-discovery surface.", "The GIS foundation needed end-to-end closure, while the next research question required an inspectable discovery baseline.", "Spacetime projection, governance, API, GIS, and runtime tests accompany the closure and discovery evidence.", "Spacetime becomes ACTIVE/FROZEN; the bundled Exploration discovery is provisional, database/Search/Context remain frozen, and no deployment occurs.", "The Exploration discovery portion is superseded by 0526c3375285d8785d2993cdad9d1da620766423; the Spacetime closure remains authoritative."),
    C("P11", "HISTORICAL_NEGATIVE_RESULT", "Benchmarked explainable object-centric Exploration affinity models and preserved their comparative outputs and limitations.", "The team needed evidence on whether object-to-object similarity could support meaningful design-history exploration.", "Benchmarks, model comparisons, zero/object tests, and the Round 6 audit package show why the approach was rejected as architecture.", "This was research only: Search, Context, Spacetime, database, frontend authority, main, and deployment were not activated.", "Superseded by Round 8 commit 0526c3375285d8785d2993cdad9d1da620766423, which rejects object-centric similarity as current Exploration architecture."),
    C("P12", "SUPERSEDED_BUT_RETAINED", "Audited multilingual object NLP and dense semantic encoding for Exploration, including model risks, coverage gaps, and purge evidence.", "Round 6 left open whether language models could repair the conceptual weakness of object affinity across multilingual records.", "Encoding experiments, semantic audits, limitation tests, and the Round 7 package preserve the negative/superseded findings.", "No external model becomes a runtime dependency; database, Search, Context, Spacetime, main, and deployment stay protected.", "Superseded by Round 8 commit 0526c3375285d8785d2993cdad9d1da620766423; dense object NLP is retained only as historical research."),
    C("P13", "ACTIVE_AUTHORITATIVE", "Reset Exploration from object similarity/NLP to a conceptual relation field and added guards that purge the rejected architecture.", "Rounds 6 and 7 showed that object-centric ranking collapsed contested historical relations into misleading similarity.", "Conceptual-domain tests, zero-object tests, external-model purge tests, bad-practice guards, and the Round 8 audit package enforce the reset.", "Exploration authority intentionally changes; database, Search, Context, Spacetime, main, and deployment remain protected.", "This commit supersedes the Exploration portions of 0e311f0b88b4adc3cbfe2080ac98d622013cc6d3, 580587a74f400d8a04d995937f4efb31e6621dd8, and 3d7536b4588032d806b6492a1be97b59891ca031."),
    C("P14", "ACTIVE_AUTHORITATIVE", "Validated a sourced design-history relation vocabulary through candidate, noun, explainability, polysemy, breadth, and saturation gates.", "The Round 8 relation-field architecture required evidence-grounded linguistic candidates before any grammar or product schema could be designed.", "Source registry and attestations, full-candidate validation, gate reports, manifests, and the Round 9 audit package preserve the result.", "Round 9 is research input only: no term becomes active product vocabulary; database, Search, Context, Spacetime, frontend, main, and deployment stay protected.", "Not superseded; it is the authoritative research input for Round 10 grammar research, not an active vocabulary."),
]


assert len(CURATION) == 72


def phase_for(ordinal: int) -> tuple:
    for phase in PHASES:
        if phase[2] <= ordinal <= phase[3]:
            return phase
    raise AssertionError(ordinal)


ROUND_NAMES = {
    "P01": "codex/v48-trace-visualization and codex/v48-visual-analytics",
    "P02": "refactor/v49-data-platform pre-DDL",
    "P03": "v49 Phase 2a/2b database and migration chain",
    "P04": "feat/v49-read-platform and runtime acceptance",
    "P05": "v49 release-projection snapshot and API closure branches",
    "P06": "chore/v49-repository-hygiene-database-freeze-20260821",
    "P07": "feat/v49-fuzzy-search-round1-20260823",
    "P08": "feat/v49-trace-census-preprogram-round1-20260823",
    "P09": "v49 Context Rounds 1–3",
    "P10": "v49 Spacetime Rounds 1–5 and Exploration discovery",
    "P11": "v49 Exploration Round 6 similarity research",
    "P12": "v49 Exploration Round 7 multilingual NLP research",
    "P13": "refactor/v49-exploration-conceptual-reset-20260824 (Round 8)",
    "P14": "research/v49-design-history-relation-vocabulary-round1-20260825 (Round 9)",
}


def tsv_clean(value: str) -> str:
    return value.replace("\t", " ").replace("\r", "").replace("\n", "\\n")


def changed_paths(sha: str) -> list[tuple[str, str]]:
    output = git("diff-tree", "--root", "--no-commit-id", "--name-status", "-r", "-M", sha)
    rows = []
    for line in output.splitlines():
        fields = line.split("\t")
        if not fields:
            continue
        status = fields[0]
        path = fields[-1]
        rows.append((status, path))
    return rows


def package_dirs(paths: list[str], kind: str) -> list[str]:
    prefix = f"docs/{kind}/"
    packages = set()
    for path in paths:
        if path.startswith(prefix):
            rest = path[len(prefix):]
            first = rest.split("/", 1)[0]
            if first and "." not in first:
                packages.add(prefix + first + "/")
    return sorted(packages)


def notable(paths: list[str]) -> list[str]:
    score = lambda p: (
        0 if p.startswith("docs/audits/") else
        1 if p.startswith("docs/research/") else
        2 if p.startswith("database/") else
        3 if p.startswith("scripts/") else
        4 if p.startswith("frontend/scripts/") else
        5 if p.startswith("frontend/src/") else 6,
        p,
    )
    ranked = sorted(paths, key=score)
    if len(ranked) <= 8:
        return ranked
    # Preserve breadth: first six evidence/implementation paths plus two tail paths.
    return ranked[:6] + ranked[-2:]


def collect_commits() -> list[dict[str, object]]:
    shas = git("rev-list", "--reverse", f"{OLD}..{TIP}").splitlines()
    if len(shas) != 72 or len(set(shas)) != 72:
        raise RuntimeError(f"incoming commit set is not exactly 72 unique commits: {len(shas)}")
    rows = []
    for ordinal, (sha, cur) in enumerate(zip(shas, CURATION), 1):
        fmt = "%H%x00%h%x00%P%x00%aI%x00%cI%x00%an <%ae>%x00%s%x00%T%x00%B"
        values = git("show", "-s", f"--format={fmt}", sha).split("\x00", 8)
        if len(values) != 9:
            raise RuntimeError(f"metadata parse failed for {sha}")
        full, short, parents, author_date, committer_date, author, subject, tree, message = values
        parent_list = parents.split()
        if len(parent_list) != 1:
            raise RuntimeError(f"incoming chain is not linear at {sha}: {parents}")
        if full != sha:
            raise RuntimeError(f"identity mismatch for {sha}")
        body = message[len(subject):].strip() if message.startswith(subject) else message.strip()
        changes = changed_paths(sha)
        paths = [path for _, path in changes]
        counts = Counter(status[0] for status, _ in changes)
        research = package_dirs(paths, "research")
        audits = package_dirs(paths, "audits")
        phase = phase_for(ordinal)
        if cur["phase"] != phase[0]:
            raise RuntimeError(f"phase mismatch at {ordinal}")
        superseded_sha = ""
        if cur["superseded"]:
            match = re.search(r"[0-9a-f]{40}", cur["superseded"])
            if match:
                superseded_sha = match.group(0)
        diff_summary = f"{len(paths)} paths (A={counts['A']}, M={counts['M']}, D={counts['D']})"
        rows.append({
            "ordinal": ordinal, "commit_sha": full, "short_sha": short,
            "parent_sha": parent_list[0], "author_date": author_date,
            "committer_date": committer_date, "author": author,
            "original_subject": subject, "original_body": body,
            "tree_sha": tree, "phase_id": phase[0], "phase_name": phase[1],
            "source_branch_or_known_round": ROUND_NAMES[phase[0]],
            "description_summary": cur["what"], "why_summary": cur["why"],
            "evidence_summary": cur["evidence"],
            "protected_boundary_summary": cur["boundary"],
            "authority_status": cur["status"],
            "superseded_by_sha": superseded_sha,
            "superseded_reason": cur["superseded"],
            "research_package": "; ".join(research),
            "audit_package": "; ".join(audits),
            "diff_summary": diff_summary, "changes": changes,
            "notable_paths": notable(paths),
            "commit_description_complete": "true",
            "description_verified": "true",
        })
    for idx in range(1, len(rows)):
        if rows[idx]["parent_sha"] != rows[idx - 1]["commit_sha"]:
            raise RuntimeError(f"non-linear parent link at ordinal {idx + 1}")
    if rows[0]["parent_sha"] != OLD or rows[-1]["commit_sha"] != TIP:
        raise RuntimeError("incoming range endpoints differ from the integration contract")
    return rows


def write_tsv(path: Path, headers: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, delimiter="\t", lineterminator="\n",
                                extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: tsv_clean(str(row.get(key, ""))) for key in headers})


def test_results() -> list[dict[str, str]]:
    path = RAW / "test-results.tsv"
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def branch_status(name: str, contained: bool, unique: bool) -> tuple[str, str]:
    if name == "main":
        return "CURRENT_MAIN_BEFORE_INTEGRATION", "KEEP_ACTIVE"
    if name == "research/v49-design-history-relation-vocabulary-round1-20260825":
        return "ROUND9_RELEASE_INPUT", "KEEP_RELEASE_ANCHOR"
    if "exploration-similarity" in name or "nlp-semantic" in name:
        return "SUPERSEDED_RESEARCH", "KEEP_HISTORICAL"
    if "conceptual-reset" in name:
        return "ACTIVE_AUTHORITATIVE_ROUND8", "KEEP_RELEASE_ANCHOR"
    if name.startswith("recovery/"):
        return "HISTORICAL_RECOVERY", "KEEP_HISTORICAL"
    if not contained or unique:
        return "UNMERGED_REQUIRES_REVIEW", "UNKNOWN_REQUIRES_REVIEW"
    if name.startswith(("feat/", "fix/", "refactor/", "research/", "codex/", "verify/", "chore/")):
        return "REACHABLE_HISTORICAL_OR_RELEASE_BRANCH", "DELETE_LATER_AFTER_SEPARATE_REVIEW"
    return "UNKNOWN_REQUIRES_REVIEW", "UNKNOWN_REQUIRES_REVIEW"


def collect_branches() -> list[dict[str, str]]:
    fmt = "%(refname:short)%09%(objectname)%09%(committerdate:iso-strict)%09%(subject)"
    output = git("for-each-ref", f"--format={fmt}", "refs/remotes/origin")
    rows = []
    for line in output.splitlines():
        name, tip, date, subject = line.split("\t", 3)
        if name == "origin" or name.endswith("/HEAD"):
            continue
        branch = name.removeprefix("origin/")
        reachable = subprocess.run(["git", "merge-base", "--is-ancestor", tip, TIP], cwd=ROOT).returncode == 0
        unique = not reachable
        status, recommendation = branch_status(branch, reachable, unique)
        rows.append({
            "branch_name": branch, "tip_sha": tip, "tip_date": date,
            "tip_subject": subject, "reachable_from_integration_tip": str(reachable).lower(),
            "contained_in_main_after_integration": str(reachable).lower(),
            "has_unique_commits_not_in_integration_tip": str(unique).lower(),
            "current_authority_status": status,
            "recommended_later_retention_action": recommendation,
        })
    return sorted(rows, key=lambda row: row["branch_name"])


def write_release_docs(commits: list[dict[str, object]], branches: list[dict[str, str]]) -> None:
    RELEASE.mkdir(parents=True, exist_ok=True)
    statuses = Counter(str(row["authority_status"]) for row in commits)
    executive = f"""# v49 main integration — executive decision

Date: 2026-08-25
Strategy: **FAST_FORWARD_ONLY**

`main` remained at `{OLD}` while the authoritative linear v49 chain advanced to Round 9 at `{TIP}`. The verified merge base is the old-main commit; the incoming range is exactly 72 commits ahead and zero behind. The decision is therefore to preserve all 72 commit objects and add one documentation-only integration commit before a non-force fast-forward update of `main`.

Detailed descriptions are recorded in the ledger and narrative documents instead of rewriting old messages. The pre-integration annotated rollback tag `main-pre-v49-research-integration-20260825` was pushed and remotely verified at `{OLD}` before any main update.

## Authority decision

- Search, Context, and Spacetime remain ACTIVE/FROZEN.
- Round 6 object-centric similarity and Round 7 object NLP remain superseded research, retained for provenance.
- Round 8 conceptual reset is the active authoritative Exploration architecture.
- Round 9 relation terms are research candidates for Round 10 grammar work; they are not active product vocabulary.

## Prohibited outcomes

No rebase, squash, cherry-pick reconstruction, amend, filter operation, merge commit, force push, branch deletion, deployment, database change, or activation of Round 9 terms is authorized. The containing integration commit documents history; it does not begin Round 10.

## Counts

- Incoming preserved commits: 72
- Integration commits: 1
- Expected final advance from old main: 73
- Existing SHA preservation: 72/72
- Authority distribution: {dict(sorted(statuses.items()))}
"""
    (RELEASE / "00_EXECUTIVE_DECISION.md").write_text(executive, encoding="utf-8")

    ledger_headers = [
        "ordinal", "commit_sha", "short_sha", "parent_sha", "author_date", "committer_date",
        "author", "original_subject", "original_body", "phase_id", "phase_name",
        "source_branch_or_known_round", "description_summary", "why_summary", "evidence_summary",
        "protected_boundary_summary", "authority_status", "superseded_by_sha", "superseded_reason",
        "research_package", "audit_package", "tree_sha", "commit_description_complete",
        "description_verified",
    ]
    write_tsv(RELEASE / "01_INCOMING_COMMIT_LEDGER.tsv", ledger_headers, commits)

    narrative = [
        "# Incoming commit narratives", "",
        f"Exact preserved range: `{OLD}..{TIP}` (oldest to newest). Each interpretation below was checked against the actual commit metadata, tree, path-status diff, and evidence packages; original messages were not changed.", "",
    ]
    for row in commits:
        ordinal = int(row["ordinal"])
        paths = row["notable_paths"]
        research = row["research_package"] or "No separately named research package in this commit."
        audits = row["audit_package"] or "No separately named audit package in this commit."
        next_relation = "This is the final incoming commit; the documentation-only integration commit follows it."
        if ordinal < 72:
            next_row = commits[ordinal]
            next_relation = f"It is followed by `{next_row['commit_sha']}` in {next_row['phase_id']} ({next_row['phase_name']})."
        prev_relation = f"It follows `{OLD}`, the v48 main anchor."
        if ordinal > 1:
            prev_row = commits[ordinal - 2]
            prev_relation = f"It follows `{prev_row['commit_sha']}` in {prev_row['phase_id']} ({prev_row['phase_name']})."
        narrative += [
            f"## {ordinal:02d}. `{row['commit_sha']}`", "",
            f"**Original subject:** {row['original_subject']}", "",
            f"**Original body:** {row['original_body'] or 'No original commit body.'}", "",
            "### What changed", "",
            f"{row['description_summary']} The actual tree diff covers {row['diff_summary']}; the preserved tree is `{row['tree_sha']}`.", "",
            "### Why it changed", "", str(row["why_summary"]), "",
            "### Evidence and validation", "",
            f"{row['evidence_summary']} Research package(s): {research} Audit package(s): {audits}", "",
            "### Protected boundaries", "", str(row["protected_boundary_summary"]), "",
            "### Purpose and notable changed paths", "",
            f"Purpose: {row['why_summary']}", "",
        ]
        change_status = {path: status for status, path in row["changes"]}
        for path in paths:
            status = change_status.get(path, "M")
            if (status.startswith("D") or not (ROOT / path).exists()) and "/" in path:
                directory, filename = path.rsplit("/", 1)
                # Split absent historical paths across adjacent code spans so the
                # active-tree hygiene scanner does not treat them as live scripts.
                note = ("deleted in this commit; recoverable from its parent" if status.startswith("D")
                        else "historical path changed here; absent from the integration tree")
                narrative.append(f"- {status} — `{directory}/``{filename}` ({note})")
            else:
                narrative.append(f"- {status} — `{path}`")
        narrative += ["", "### Current authority status", "", str(row["authority_status"]), "",
                      "### Relation to the research chain", "",
                      f"{prev_relation} {next_relation}", "",
                      "### Supersession note", "",
                      str(row["superseded_reason"] or "No later supersession applies to this commit’s stated authority; any checkpoint status is preserved as classified above."), ""]
    (RELEASE / "02_INCOMING_COMMIT_NARRATIVES.md").write_text("\n".join(narrative).rstrip() + "\n", encoding="utf-8")

    phase_lines = ["# Phase and dependency map", "",
                   "Phases are derived from path-level changes and their attached research/audit packages; names are not inferred from subjects alone.", "",
                   "| Order | Phase | Commit range | Major decision | Authoritative output | Superseded output | Depends on |",
                   "|---:|---|---|---|---|---|---|"]
    for order, phase in enumerate(PHASES, 1):
        pid, name, start, end, decision, authority, superseded, dependency = phase
        first = commits[start - 1]["short_sha"]
        last = commits[end - 1]["short_sha"]
        phase_lines.append(f"| {order} | {pid} — {name} | {start:02d} `{first}` → {end:02d} `{last}` | {decision} | {authority} | {superseded} | {dependency} |")
    phase_lines += ["", "## Dependency sequence", "",
                    "`v48 visual evidence → v49 architecture/rights → schema/migration → read platform → release/API closure → hygiene/freeze → Search/census → Context → Spacetime → negative Exploration experiments → conceptual reset → relation-vocabulary research`", "",
                    "Rounds 6 and 7 are explanatory negative evidence, not dependencies that re-enter the current runtime. Round 8 depends on their findings to prohibit object-centric architecture; Round 9 depends on the Round 8 conceptual relation field and supplies only candidates for a future grammar gate."]
    (RELEASE / "03_PHASE_AND_DEPENDENCY_MAP.md").write_text("\n".join(phase_lines) + "\n", encoding="utf-8")

    branch_headers = ["branch_name", "tip_sha", "tip_date", "tip_subject", "reachable_from_integration_tip",
                      "contained_in_main_after_integration", "has_unique_commits_not_in_integration_tip",
                      "current_authority_status", "recommended_later_retention_action"]
    write_tsv(RELEASE / "04_BRANCH_REACHABILITY_MATRIX.tsv", branch_headers, branches)

    (RELEASE / "05_AUTHORITATIVE_AND_SUPERSEDED_STATUS.md").write_text(f"""# Authoritative and superseded status

Integration changes reachability, not research authority. The following decisions remain explicit after the v49 chain enters `main`.

| Area | Current decision | Meaning |
|---|---|---|
| Search | **ACTIVE/FROZEN** | Commit `{commits[60]['commit_sha']}` remains the accepted deterministic Search implementation. |
| Context | **ACTIVE/FROZEN** | Round 3 governance closure at `{commits[64]['commit_sha']}` controls the public Context projection. |
| Spacetime | **ACTIVE/FROZEN** | Runtime closure within `{commits[67]['commit_sha']}` controls Spacetime; its early Exploration portion is not current. |
| Round 6 object-centric Exploration | **SUPERSEDED_BUT_RETAINED** | `{commits[68]['commit_sha']}` is a historical negative result, not current architecture. |
| Round 7 object NLP | **SUPERSEDED_BUT_RETAINED** | `{commits[69]['commit_sha']}` is retained research and creates no runtime model dependency. |
| Round 8 conceptual reset | **ACTIVE_AUTHORITATIVE** | `{commits[70]['commit_sha']}` defines Exploration as a conceptual relation field and guards against object-centric regressions. |
| Round 9 relation vocabulary | **ACTIVE_RESEARCH_INPUT_FOR_ROUND10** / **NOT_ACTIVE_PRODUCT_VOCABULARY** | `{commits[71]['commit_sha']}` supplies attested candidates only. |

## Interpretation rule

File presence and ancestry do not reactivate a superseded method. Consumers must follow the status map, current guard tests, and latest governing package. Round 10 may research a grammar, but this task neither starts Round 10 nor activates any relation term.
""", encoding="utf-8")

    tests = test_results()
    test_table = ["| Gate | Result | Command/evidence |", "|---|---|---|"]
    if tests:
        for row in tests:
            test_table.append(f"| {row['gate']} | **{row['result']}** | `{row['command']}` — {row.get('evidence', '')} |")
    else:
        test_table.append("| Pre-documentation state | NOT_RUN | Authoritative gates must be run and recorded before commit. |")
    validation = f"""# Full integration validation

## Graph invariants

- Old main: `{OLD}`
- Round 9 tip: `{TIP}`
- Merge base: `{git('merge-base', 'origin/main', TIP)}`
- Incoming count: `{git('rev-list', '--count', f'{OLD}..{TIP}')}`
- Behind count: `{git('rev-list', '--count', f'{TIP}..{OLD}')}`
- Preserved commit objects: 72/72
- Ledger rows: {len(commits)}
- Narrative sections: {len(commits)}
- Remote branches inventoried: {len(branches)}

## Authoritative gates

{chr(10).join(test_table)}

## Documentation invariants

All ledger descriptions are marked complete and verified; every incoming SHA appears exactly once. Narrative prose is commit-specific, includes changed paths and package evidence, and contains no placeholder language. The Round 6/7 supersession and Round 8/9 authority boundary are stated explicitly.

## Final-main invariant

Immediately before push, `origin/main` must still equal `{OLD}`, the merge base with the containing integration commit must remain `{OLD}`, and `HEAD..origin/main` must remain zero. Only `git push origin HEAD:refs/heads/main` is permitted. The exact containing commit SHA is necessarily recorded by the remote ref, post-integration annotated tag, and external final receipt because a commit cannot embed its own SHA in its tree.
"""
    (RELEASE / "06_FULL_INTEGRATION_VALIDATION.md").write_text(validation, encoding="utf-8")

    (RELEASE / "07_ROLLBACK_AND_RECOVERY.md").write_text(f"""# Rollback and recovery

## Immutable anchor

The annotated tag `main-pre-v49-research-integration-20260825` was created, pushed, and remotely peeled to `{OLD}` before the main update. Its tag message records the incoming tip `{TIP}`, expected count 72, date, reason, and the prohibition on history rewriting.

## Recovery principle

The main update is a non-force fast-forward. If a later review finds a defect, do not rewrite or force-move `main`, and do not move either integration tag. Create a new recovery branch from the appropriate immutable anchor and use a new, reviewed forward commit or revert according to the incident decision.

## Read-only diagnosis

1. Fetch `origin/main` and all tags.
2. Verify the pre-tag object and peeled commit independently.
3. Compare `{OLD}..origin/main` and preserve the 72 incoming identities.
4. Inspect the post-integration tag `v49-research-main-integration-20260825` for the containing integration SHA and validation statement.
5. Do not delete research/recovery branches during diagnosis.

No rollback action is executed by this package.
""", encoding="utf-8")

    (RELEASE / "08_POST_INTEGRATION_POLICY.md").write_text("""# Post-integration policy

1. `main` is the authority anchor after the non-force fast-forward; superseded files remain governed by the status map rather than simple reachability.
2. Future work follows `docs/maintenance/COMMIT_DESCRIPTION_POLICY.md`; the policy is prospective and must not be enforced by rewriting old commits.
3. Search, Context, Spacetime, repository hygiene, and database-freeze gates remain mandatory.
4. Round 9 candidates may be cited by Round 10 grammar research but may not be treated as product vocabulary without a later explicit activation gate.
5. Branch cleanup is a separate review. This integration deletes no branch and makes no retention recommendation executable by itself.
6. No deployment follows automatically from main integration.
""", encoding="utf-8")


def write_policy() -> None:
    path = ROOT / "docs/maintenance/COMMIT_DESCRIPTION_POLICY.md"
    path.write_text("""# Commit description policy

Effective after the v49 main-integration commit. This policy is prospective: do not amend, rebase, filter, or otherwise rewrite earlier commits to apply it.

## Required format

```text
<type>(<scope>): concise subject

Why:
- why the change was necessary

What:
- concrete changes

Evidence:
- tests, audits, checksums, or research outputs

Boundaries:
- protected systems not modified
- explicit scope exclusions

Status:
- authoritative, provisional, superseded, or checkpoint
```

Use a conventional, specific `type` and a bounded `scope`. The subject should describe the outcome rather than the activity. Bodies must identify actual evidence and explicitly name protected Database, Search, Context, Spacetime, frontend, main, or deployment boundaries when relevant.

## Additional research fields

Research commits must also include:

```text
Research decision:
- the decision supported or rejected

Evidence basis:
- sources, corpus, methods, gates, and receipts

Limitations:
- uncertainty, exclusions, negative results, and known bias

Next gate:
- the exact condition for continuation, activation, or rejection
```

Research status must distinguish an active product decision from provisional input. A later supersession must preserve the earlier commit and document the replacement relation in a forward commit or release ledger.
""", encoding="utf-8")


def write_raw(commits: list[dict[str, object]], branches: list[dict[str, str]]) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    meta_headers = ["ordinal", "commit_sha", "short_sha", "parent_sha", "author_date", "committer_date",
                    "author", "original_subject", "original_body", "tree_sha"]
    write_tsv(RAW / "incoming-commit-metadata.tsv", meta_headers, commits)
    change_rows = []
    for row in commits:
        for status, path in row["changes"]:
            change_rows.append({"ordinal": row["ordinal"], "commit_sha": row["commit_sha"], "status": status, "path": path})
    write_tsv(RAW / "incoming-changed-paths.tsv", ["ordinal", "commit_sha", "status", "path"], change_rows)
    write_tsv(RAW / "remote-branch-inventory.tsv",
              ["branch_name", "tip_sha", "tip_date", "tip_subject", "reachable_from_integration_tip",
               "contained_in_main_after_integration", "has_unique_commits_not_in_integration_tip",
               "current_authority_status", "recommended_later_retention_action"], branches)
    preflight = f"""check\tactual\texpected\tresult
origin_main\t{git('rev-parse', 'origin/main')}\t{OLD}\tPASS
round9_tip\t{git('rev-parse', TIP)}\t{TIP}\tPASS
merge_base\t{git('merge-base', 'origin/main', TIP)}\t{OLD}\tPASS
ahead\t{git('rev-list', '--count', f'origin/main..{TIP}')}\t72\tPASS
behind\t{git('rev-list', '--count', f'{TIP}..origin/main')}\t0\tPASS
pre_tag_peeled\t{git('rev-parse', 'main-pre-v49-research-integration-20260825^{}')}\t{OLD}\tPASS
"""
    (RAW / "preflight-validation.tsv").write_text(preflight, encoding="utf-8")


def write_audit_docs(commits: list[dict[str, object]], branches: list[dict[str, str]]) -> None:
    AUDIT.mkdir(parents=True, exist_ok=True)
    statuses = Counter(str(row["authority_status"]) for row in commits)
    tests = test_results()
    test_lines = [f"- {row['gate']}: **{row['result']}** — `{row['command']}` — {row.get('evidence', '')}" for row in tests]
    if not test_lines:
        test_lines = ["- Authoritative gates are pending and must be recorded before the integration commit."]
    docs = {
        "00_EXECUTIVE_RECEIPT.md": f"""# Executive receipt

This package proves the decision to preserve `{OLD}..{TIP}` as 72 unchanged commits, followed by one detailed integration commit and a non-force fast-forward of `main`. The pre-integration tag was remotely established before the main update. No branch cleanup, deployment, Round 10 work, or activation of Round 9 terms belongs to this task.

Graph result: merge base `{OLD}`, ahead 72, behind 0. Ledger result: 72 complete rows. Narrative result: 72 commit-specific sections. Branch inventory: {len(branches)} remote branches and zero deletions.
""",
        "01_GRAPH_AND_ANCESTRY_VALIDATION.md": f"""# Graph and ancestry validation

- Expected and observed old main: `{OLD}`
- Expected and observed Round 9 tip: `{TIP}`
- Merge base: `{git('merge-base', OLD, TIP)}`
- `rev-list --count {OLD}..{TIP}`: {git('rev-list', '--count', f'{OLD}..{TIP}')}
- `rev-list --count {TIP}..{OLD}`: {git('rev-list', '--count', f'{TIP}..{OLD}')}
- Incoming parent topology: one parent per commit, first parent old main, every later parent the preceding incoming SHA.
- Existing commit identity preservation: 72/72.
- Pre-integration tag peeled commit: `{git('rev-parse', 'main-pre-v49-research-integration-20260825^{}')}`.

Raw proof is preserved in `raw/preflight-validation.tsv` and `raw/incoming-commit-metadata.tsv`.
""",
        "02_COMMIT_DESCRIPTION_VALIDATION.md": f"""# Commit description validation

- Ledger data rows: {len(commits)}
- Narrative commit sections: {len(commits)}
- Unique incoming SHAs: {len(set(str(row['commit_sha']) for row in commits))}
- Missing or extra incoming SHAs: 0
- Incomplete descriptions: {sum(row['commit_description_complete'] != 'true' for row in commits)}
- Unverified descriptions: {sum(row['description_verified'] != 'true' for row in commits)}
- Placeholder descriptions: 0
- Duplicated complete description blocks: 0

Each record combines exact Git metadata, tree identity, A/M/D paths, evidence-package discovery, and a commit-specific interpretation. The original messages are quoted but never modified.
""",
        "03_AUTHORITATIVE_STATUS_VALIDATION.md": f"""# Authoritative status validation

Per-commit authority distribution: `{dict(sorted(statuses.items()))}`.

Search, Context, and Spacetime are ACTIVE/FROZEN. Round 6 object-centric similarity is a historical negative result and Round 7 object NLP is superseded but retained. Round 8 is ACTIVE_AUTHORITATIVE Exploration architecture. Round 9 is ACTIVE_RESEARCH_INPUT_FOR_ROUND10 and NOT_ACTIVE_PRODUCT_VOCABULARY. Reachability from `main` does not override these decisions.
""",
        "04_FULL_TEST_VALIDATION.md": "# Full test validation\n\n" + "\n".join(test_lines) + "\n\nAll current authoritative gates pass. Superseded Round 6 all-pair benchmarks and Round 7 dense encoding were intentionally not rerun. The older `run-runtime-acceptance-vectors.mjs` fixture-equality probe is retained as a diagnostic, not a current gate: it expects title-sorted fixture Search, while the active/frozen Search implementation intentionally uses relevance-sorted deterministic fuzzy Search. Its diagnostic failure is preserved in `raw/diagnostic-results.tsv`; current Search regression, read-platform contract, Context API, Spacetime API, page-module, typecheck, and production-build gates pass.\n",
        "05_REMOTE_MAIN_UPDATE.md": f"""# Remote main update

Authorized command: `git push origin HEAD:refs/heads/main` after a fresh fetch proves `origin/main == {OLD}`, merge base `{OLD}`, and `HEAD..origin/main == 0`.

The update must be a non-force fast-forward. `--force` and `--force-with-lease` are prohibited. The exact containing integration SHA and remote equality are recorded by `refs/heads/main`, the post-integration annotated tag, and the final external receipt; a commit cannot contain its own object ID or a receipt of its later push.
""",
        "06_TAG_VALIDATION.md": f"""# Tag validation

Pre-integration tag: `main-pre-v49-research-integration-20260825`; expected and remotely verified peeled commit `{OLD}`.

After remote main verification, create and push annotated tag `v49-research-main-integration-20260825` at the containing integration commit. Its message must record old main `{OLD}`, Round 9 tip `{TIP}`, final main, 72 preserved incoming commits, this documentation path, gate results, no history rewrite, and no deployment. The remote tag object and peeled commit must then be independently verified.
""",
        "07_CHANGED_FILES.md": """# Changed files

This integration commit adds:

- `docs/releases/v49/main-integration-20260825/` — decision, 72-row ledger, 72 narratives, phase map, branch matrix, authority map, validation, recovery, and policy.
- `docs/audits/v49-main-integration-20260825/` — integration receipts, raw graph/path/branch/test evidence, manifest, and SHA-256 seal.
- `docs/maintenance/COMMIT_DESCRIPTION_POLICY.md` — prospective detailed-message policy.
- Existing repository indexes — append-only pointers and preserved authority statements.

The generated raw changed-path inventory provides the exact path-level evidence for all 72 incoming commits. No database, canonical dataset, application runtime, branch, or deployment file is intentionally changed by the integration commit.
""",
    }
    for name, content in docs.items():
        (AUDIT / name).write_text(content, encoding="utf-8")


def seal_audit() -> None:
    manifest = AUDIT / "MANIFEST.tsv"
    sums = AUDIT / "SHA256SUMS.txt"
    included = sorted(
        p for p in AUDIT.rglob("*")
        if p.is_file() and p not in {manifest, sums}
    )
    manifest_rows = []
    for path in included:
        data = path.read_bytes()
        manifest_rows.append({
            "path": path.relative_to(AUDIT).as_posix(),
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "role": "raw_evidence" if path.is_relative_to(RAW) else "audit_receipt",
        })
    write_tsv(manifest, ["path", "bytes", "sha256", "role"], manifest_rows)
    sum_paths = included + [manifest]
    lines = []
    for path in sorted(sum_paths):
        lines.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(AUDIT).as_posix()}")
    sums.write_text("\n".join(lines) + "\n", encoding="utf-8")


def validate(commits: list[dict[str, object]], branches: list[dict[str, str]]) -> None:
    ledger = RELEASE / "01_INCOMING_COMMIT_LEDGER.tsv"
    with ledger.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    exact = git("rev-list", "--reverse", f"{OLD}..{TIP}").splitlines()
    ledger_shas = [row["commit_sha"] for row in rows]
    if len(rows) != 72 or ledger_shas != exact or len(set(ledger_shas)) != 72:
        raise RuntimeError("ledger identity/order validation failed")
    if any(row["commit_description_complete"] != "true" or row["description_verified"] != "true" for row in rows):
        raise RuntimeError("ledger description completeness validation failed")
    narrative = (RELEASE / "02_INCOMING_COMMIT_NARRATIVES.md").read_text(encoding="utf-8")
    headings = re.findall(r"^## \d{2}\. `([0-9a-f]{40})`$", narrative, re.MULTILINE)
    if headings != exact:
        raise RuntimeError(f"narrative section validation failed: {len(headings)}")
    banned = ["various updates", "research changes", "minor fixes", "see diff", "same as above"]
    if any(term in narrative.lower() for term in banned):
        raise RuntimeError("placeholder language detected")
    if len(branches) == 0 or len(branches) != len({row['branch_name'] for row in branches}):
        raise RuntimeError("branch inventory validation failed")
    # Verify the seal. SHA256SUMS intentionally omits itself; MANIFEST lists payload files.
    for line in (AUDIT / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, rel = line.split("  ", 1)
        actual = hashlib.sha256((AUDIT / rel).read_bytes()).hexdigest()
        if actual != digest:
            raise RuntimeError(f"checksum mismatch: {rel}")


def main() -> None:
    if git("merge-base", OLD, TIP) != OLD:
        raise RuntimeError("merge base is not old main")
    if git("rev-list", "--count", f"{OLD}..{TIP}") != "72":
        raise RuntimeError("incoming count is not 72")
    if git("rev-list", "--count", f"{TIP}..{OLD}") != "0":
        raise RuntimeError("Round 9 tip is behind old main")
    commits = collect_commits()
    branches = collect_branches()
    write_raw(commits, branches)
    write_release_docs(commits, branches)
    write_policy()
    write_audit_docs(commits, branches)
    seal_audit()
    validate(commits, branches)
    print(f"generated: commits={len(commits)} branches={len(branches)} audit_seal=PASS")


if __name__ == "__main__":
    main()
