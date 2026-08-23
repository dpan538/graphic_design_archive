# Context semantic red-team review

The review attempted to read the governed interface more strongly than its evidence supports. No P0/P1 semantic ambiguity remains after the mitigations below.

| Misreading | Risk source | Mitigation in interface | Method boundary |
| --- | --- | --- | --- |
| A connection proves a historical relation | Graph connector and spatial proximity | Neutral `context_representation` connection; category-specific project-classification wording; zero semantic edges | Context classifications are not historical relations. |
| Shared Context means two records are related | Repeated term nodes or labels | Explanations state that a term describes each selected record independently | Shared Context does not establish a relation between records. |
| Movement means definitive historical membership | Familiar movement names and “within” wording | “Curated movement context for research navigation”; project-curated epistemic role; prohibited membership/affiliation inference | Stronger membership requires separately published evidence. |
| Theme proves creator intent | Thematic label | “The archive assigns … as a thematic research category”; explicit creator-intent prohibition | Theme is project curation, not an intentionality claim. |
| Medium caused style or relation | Medium/format category | “Classified as”; explanation says medium/format category and prohibits causal inference | Medium is controlled description only. |
| Node order or distance is chronology or importance | Layout lanes and proximity | Deterministic functional layout; no chronology, rank, or weight encoding | Spatial layout carries no historical order or importance. |
| Multiple values imply uncertainty or rank | Same-kind multi-value records | Preserve each governed value equally; no ranking; explain record/group scope | Multi-value classifications are parallel project assignments. |
| Publication means source acceptance or fact | Published badge/state | Show frozen source state `proposed` separately from Context publication | Publication authorizes interface exposure, not historical truth. |
| Root creator/type/source metadata are relations | Metadata near the graph | Keep fields on root/inspector only, without edges or draggable nodes | Root metadata is source-reported descriptive orientation. |
| Region is missing data | No geographic node | Explicit Spacetime handoff in explanation/method | Geography is intentionally governed in another TRACE domain. |

Machine tests additionally reject prohibited causal or definitive-membership language from rendered governed explanation examples except where it appears as an explicit “must not infer” statement.
