# Pruning and restructuring contract

Repair order is deterministic: evaluate all direct pairs; prune a failing terminal/branch leaf (canonical maximum identity resolves a two-leaf tie); remove a failing internal edge and split; then re-evaluate failing skip-one pairs within the repaired component and remove the canonical later edge of the two-step path. Recompute components after every repair. Semantic validity outranks node retention.

No failed direct edge, failed skip-one implication, orphaned active branch, or over-budget composition survives. Reflexive navigation and evidence notes are not counted as semantic edges. Frozen historical evidence is read-only throughout pruning.
