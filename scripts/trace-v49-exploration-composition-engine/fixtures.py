"""Frozen-association composition fixtures for TRACE v49 Round 15."""

from __future__ import annotations

from typing import Any


def fixture(
    fixture_id: str,
    family: str,
    seeds: list[str],
    nodes: list[str],
    associations: list[str],
    topology: str,
    description: str,
    *,
    gaps: list[str] | None = None,
    qualification: bool = False,
    navigation_return: bool = False,
    visual_seed: str = "round15-default",
) -> dict[str, Any]:
    return {
        "fixtureId": fixture_id,
        "fixtureFamily": family,
        "seedNodeIds": seeds,
        "nodeIds": nodes,
        "associationIds": associations,
        "topologyRequest": topology,
        "evidenceGapNodeIds": gaps or [],
        "qualificationGate": qualification,
        "navigationReturn": navigation_return,
        "synthetic": False,
        "visualSeed": visual_seed,
        "description": description,
    }


FIXTURES = [
    fixture("R15-COMP-001", "SINGLE_VALID_PATH", ["professionalization"], ["professionalization", "institutionalization"], ["R14-ASSOC-001"], "LINEAR_PATH", "Two-node clean pass from the frozen professionalization assessment."),
    fixture("R15-COMP-002", "DENSE_NEIGHBOURHOOD", ["design diplomacy"], ["design diplomacy", "exhibition", "propaganda", "trade"], ["R14-ASSOC-005", "R14-ASSOC-006", "R14-ASSOC-007", "R14-ASSOC-008", "R14-ASSOC-009"], "BINARY_FORK", "Dense exposition neighbourhood tests topology-derived degree control."),
    fixture("R15-COMP-003", "MULTIPLE_COMPETING_BRANCHES", ["design diplomacy"], ["design diplomacy", "exhibition", "propaganda"], ["R14-ASSOC-005", "R14-ASSOC-006", "R14-ASSOC-008"], "BINARY_FORK", "Three equally supported associations form a bounded three-node composition."),
    fixture("R15-COMP-004", "MULTIPLE_VALID_TOPOLOGIES", ["mediation"], ["production", "mediation", "consumption"], ["R14-ASSOC-002", "R14-ASSOC-003", "R14-ASSOC-004"], "AUTO", "The same three-node association graph supports several inquiry topologies, so selection remains unresolved."),
    fixture("R15-COMP-005", "UNSUPPORTED_BRIDGE", ["gendering", "design education"], ["gendering", "commodification", "design education", "institutionalization"], ["R14-ASSOC-016", "R14-ASSOC-021", "R14-ASSOC-024"], "AUTO", "A failed bridge is an invariant negative control and cannot join two qualified components."),
    fixture("R15-COMP-006", "HARD_NEGATIVE_INTRUSION", ["material displacement"], ["material displacement", "supply chain", "professionalization"], ["R14-ASSOC-010", "R14-ASSOC-026"], "LINEAR_PATH", "A hard negative is retained only as an audit control."),
    fixture("R15-COMP-007", "ALL_PASS_LOCAL_CLUSTER", ["adaptation"], ["cultural negotiation", "adaptation", "rejection"], ["R14-ASSOC-013", "R14-ASSOC-014", "R14-ASSOC-015"], "BINARY_CONVERGENCE", "All three source-bounded associations pass without claiming convergence as history."),
    fixture("R15-COMP-008", "MIXED_SUPPORT_CLASS", ["professionalization", "photography"], ["professionalization", "institutionalization", "photography", "typography"], ["R14-ASSOC-001", "R14-ASSOC-018"], "AUTO", "Externally and source-supported components remain distinct and unranked."),
    fixture("R15-COMP-009", "SPLIT_PRODUCING_GRAPH", ["gendering", "design education"], ["gendering", "commodification", "design education", "institutionalization"], ["R14-ASSOC-016", "R14-ASSOC-021", "R14-ASSOC-024", "R14-ASSOC-033", "R14-ASSOC-034"], "AUTO", "No qualified bridge exists; split means separate composition components, not historical separation."),
    fixture("R15-COMP-010", "GAP_PRODUCING_GRAPH", ["imitation"], ["imitation", "piracy", "cultural transformation"], ["R14-ASSOC-017", "R14-ASSOC-023", "R14-ASSOC-035"], "EVIDENCE_GAP_TREE", "The unsupported node is represented as an explicit evidence gap rather than a negative claim.", gaps=["cultural transformation"]),
    fixture("R15-COMP-011", "HIGH_DEGREE_SEED", ["design diplomacy"], ["design diplomacy", "exhibition", "propaganda", "trade"], ["R14-ASSOC-005", "R14-ASSOC-006", "R14-ASSOC-009"], "BINARY_FORK", "Strictly weaker evidence is pruned after the two-branch topology bound is satisfied."),
    fixture("R15-COMP-012", "PERMUTATION_EQUIVALENT", ["supply chain"], ["production site", "material displacement", "supply chain"], ["R14-ASSOC-011", "R14-ASSOC-010"], "LINEAR_PATH", "Deliberately permuted input tests canonical semantic output."),
    fixture("R15-COMP-013", "DUPLICATE_ASSOCIATION_INPUT", ["supply chain"], ["material displacement", "supply chain", "production site"], ["R14-ASSOC-010", "R14-ASSOC-011", "R14-ASSOC-010"], "LINEAR_PATH", "Duplicate association input is idempotently deduplicated."),
    fixture("R15-COMP-014", "TOPOLOGY_LINEAR", ["supply chain"], ["material displacement", "supply chain", "production site"], ["R14-ASSOC-010", "R14-ASSOC-011"], "LINEAR_PATH", "Linear topology conformance fixture."),
    fixture("R15-COMP-015", "TOPOLOGY_BINARY_FORK", ["design diplomacy"], ["design diplomacy", "exhibition", "propaganda"], ["R14-ASSOC-005", "R14-ASSOC-006", "R14-ASSOC-008"], "BINARY_FORK", "Binary fork is an inquiry shape, not historical branching."),
    fixture("R15-COMP-016", "TOPOLOGY_BINARY_CONVERGENCE", ["supply chain"], ["material displacement", "supply chain", "production site"], ["R14-ASSOC-010", "R14-ASSOC-011"], "BINARY_CONVERGENCE", "Binary convergence is an inquiry shape, not historical direction."),
    fixture("R15-COMP-017", "TOPOLOGY_QUALIFIED_PATH", ["mediation"], ["production", "mediation", "consumption"], ["R14-ASSOC-002", "R14-ASSOC-003"], "QUALIFIED_PATH", "Continuation is gated by an explicit inquiry qualification.", qualification=True),
    fixture("R15-COMP-018", "TOPOLOGY_REFLEXIVE_RETURN", ["adaptation"], ["cultural negotiation", "adaptation", "rejection"], ["R14-ASSOC-013", "R14-ASSOC-014"], "REFLEXIVE_RETURN", "Return is navigational only and creates no semantic self-loop.", navigation_return=True),
    fixture("R15-COMP-019", "TOPOLOGY_EVIDENCE_GAP_TREE", ["imitation"], ["imitation", "piracy", "cultural transformation"], ["R14-ASSOC-017", "R14-ASSOC-023", "R14-ASSOC-035"], "EVIDENCE_GAP_TREE", "Evidence-gap topology conformance fixture.", gaps=["cultural transformation"]),
    fixture("R15-COMP-020", "SOURCE_SUPPORTED_COMPOSITION", ["photography", "advertising", "craft"], ["photography", "typography", "advertising", "consumer culture", "craft", "education"], ["R14-ASSOC-018", "R14-ASSOC-019", "R14-ASSOC-020"], "AUTO", "All three source-supported associations remain visible as unranked separate components."),
    fixture("R15-COMP-021", "CLOSURE_ASSOCIATION", ["material displacement"], ["material displacement", "supply chain", "production site"], ["R14-ASSOC-010", "R14-ASSOC-011", "R14-ASSOC-012"], "BINARY_CONVERGENCE", "The moderate closure association is admitted because the triangle stays within degree two."),
    fixture("R15-COMP-022", "FAILED_CONTROL_SET_A", ["cultural transfer"], ["cultural transfer", "cultural negotiation", "cultural transformation", "piracy", "design education", "commodification"], ["R14-ASSOC-022", "R14-ASSOC-023", "R14-ASSOC-024"], "AUTO", "Qualified-but-inactive and insufficient controls remain structurally ineligible."),
    fixture("R15-COMP-023", "FAILED_CONTROL_SET_B", ["gendering"], ["gendering", "mobile object", "photography", "institutionalization", "craft", "design diplomacy"], ["R14-ASSOC-025", "R14-ASSOC-027", "R14-ASSOC-028"], "AUTO", "Hard-negative controls cannot enter composition."),
    fixture("R15-COMP-024", "FAILED_CONTROL_SET_C", ["Bauhaus"], ["Bauhaus", "desktop publishing", "Arts and Crafts", "digital interface", "Swiss typography", "Brazilian exposition"], ["R14-ASSOC-029", "R14-ASSOC-030", "R14-ASSOC-031"], "AUTO", "Temporal-near-neighbour controls cannot enter composition without a qualified association."),
    fixture("R15-COMP-025", "FAILED_CONTROL_SET_D", ["photomontage", "gendering", "imitation"], ["photomontage", "professionalization", "gendering", "design education", "commodification", "institutionalization", "imitation", "cultural transformation"], ["R14-ASSOC-032", "R14-ASSOC-033", "R14-ASSOC-034", "R14-ASSOC-035"], "AUTO", "Remaining hard negatives are exercised together without producing an edge."),
]
