#!/usr/bin/env python3
"""Build the additive TRACE Exploration v3 semantic contract and controls.

This builder is deliberately independent of the Round 16A pair-graph generator.
It emits schemas and synthetic controls only; it does not activate research facts,
modify the v2 contract, or create a production read model.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import io
import json
import re
from pathlib import Path
from typing import Any, Iterable


REPO = Path(__file__).resolve().parents[2]
RAW_REL = Path("docs/audits/v49-exploration-higher-order-association-closure-round16b/raw")
RAW = REPO / RAW_REL
SCHEMA_REL = Path("schemas/trace/exploration/v3")
SCHEMAS = REPO / SCHEMA_REL
RESEARCH_REL = Path("docs/research/trace-v49-exploration-higher-order-association-closure-round16b")
RESEARCH = REPO / RESEARCH_REL
ADR_REL = Path("docs/adr/0005-first-class-higher-order-association-contract.md")

SOURCE_SHA = "5419770959bdb8998b693fb2275b47e29b92367c"
PARENT_CHECKPOINT_SHA = "e5ddbc443c4a0a28004034cba439340ecdeb9a75"
AUTHORITY_CUTOFF_UTC = "2026-08-28T09:18:21Z"
CONTRACT_VERSION = "trace-exploration-v3-semantic-contract-1.0.0"
SCHEMA_BASE = "https://trace.example/schemas/exploration/v3/"


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def tsv_text(fieldnames: list[str], rows: Iterable[dict[str, Any]]) -> str:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=fieldnames,
        dialect="excel-tab",
        lineterminator="\n",
        extrasaction="raise",
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return output.getvalue()


def object_schema(
    properties: dict[str, Any],
    required: Iterable[str] | None = None,
    *,
    title: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": list(required if required is not None else properties),
    }
    if title:
        result["title"] = title
    if extra:
        result.update(extra)
    return result


def array(items: Any, *, minimum: int = 0, unique: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {"type": "array", "items": items, "minItems": minimum}
    if unique:
        result["uniqueItems"] = True
    return result


def enum(*values: str) -> dict[str, Any]:
    return {"type": "string", "enum": list(values)}


STRING = {"type": "string", "minLength": 1}
SHA256 = {"type": "string", "pattern": "^[0-9a-f]{64}$"}


SCOPE_IDENTITY_KEYS = (
    "scope_id",
    "historical_case_ids",
    "time_bounds",
    "geographies",
    "institutions",
    "actors",
    "mechanisms",
)
SCOPE_SET_ARRAY_KEYS = (
    "historical_case_ids",
    "geographies",
    "institutions",
    "actors",
    "mechanisms",
)


def canonical_participant_specs(
    participant_specs: list[tuple[str, str, int | None, str | None]],
    order_semantics: str,
    roles_meaningful: bool,
) -> list[tuple[str, str, int | None, str | None]]:
    """Return the normative stored participant order.

    Unordered associations are stored canonically, so participant permutation
    cannot change association identity or position-derived incidence IDs.
    Ordered associations preserve stored order and must carry contiguous
    zero-based ordinals; meaningful roles participate in canonical ordering.
    """

    rows = list(participant_specs)
    if order_semantics == "UNORDERED":
        return sorted(
            rows,
            key=(
                (lambda row: (row[3] or "", row[1], row[0]))
                if roles_meaningful
                else (lambda row: (row[1], row[0]))
            ),
        )
    return rows


def project_scope_identity(scope: dict[str, Any]) -> dict[str, Any]:
    """Execute the normative ``scope`` -> ``scope_identity`` projection."""

    projected: dict[str, Any] = {}
    for key in SCOPE_IDENTITY_KEYS:
        value = copy.deepcopy(scope[key])
        if key in SCOPE_SET_ARRAY_KEYS:
            value = sorted(value)
        projected[key] = value
    return projected


def schema_document(name: str, title: str, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{SCHEMA_BASE}{name}",
        "title": title,
        **body,
    }


def build_schemas() -> dict[Path, dict[str, Any]]:
    scope = object_schema(
        {
            "scope_id": STRING,
            "historical_case_ids": array(STRING, unique=True),
            "time_bounds": object_schema(
                {"start": {"type": ["string", "null"]}, "end": {"type": ["string", "null"]}}
            ),
            "geographies": array(STRING, unique=True),
            "institutions": array(STRING, unique=True),
            "actors": array(STRING, unique=True),
            "mechanisms": array(STRING, unique=True),
            "context_qualifications": array(STRING),
        }
    )
    participant = object_schema(
        {
            "incidence_id": STRING,
            "concept_id": STRING,
            "sense_id": STRING,
            "ordinal": {"type": ["integer", "null"], "minimum": 0},
            "role_id": {"type": ["string", "null"]},
            "participant_scope_id": STRING,
            "qualifications": array(STRING),
        }
    )
    evidence = object_schema(
        {
            "evidence_item_ids": array(STRING, unique=True),
            "locator_ids": array(STRING, unique=True),
            "support_mode": enum(
                "DIRECT_PAIR", "DIRECT_GROUP", "COHERENT_COMPOSITE", "MIXED", "PAIR_ONLY", "NONE"
            ),
            "same_configuration": {"type": "boolean"},
            "synthesis_steps": array(STRING),
            "negative_or_conflicting_evidence": array(STRING),
            "conflicts_resolved": {"type": "boolean"},
            "conflict_resolution_ids": array(STRING, unique=True),
            "rights_cleared_for_governed_use": {"type": "boolean"},
            "evidence_complete": {"type": "boolean"},
        },
        extra={
            "allOf": [
                {
                    "if": {
                        "properties": {
                            "support_mode": {"enum": ["DIRECT_PAIR", "DIRECT_GROUP"]}
                        }
                    },
                    "then": {"properties": {"synthesis_steps": {"maxItems": 0}}},
                },
                {
                    "if": {
                        "properties": {
                            "support_mode": {"enum": ["COHERENT_COMPOSITE", "MIXED"]}
                        }
                    },
                    "then": {"properties": {"synthesis_steps": {"minItems": 1}}},
                },
            ]
        },
    )
    review = object_schema(
        {
            "review_id": STRING,
            "review_state": enum("PENDING", "NONFINAL", "FINAL"),
            "disposition": enum(
                "DIRECT_PAIRWISE_SUPPORT",
                "DIRECT_HIGHER_ORDER_SUPPORT",
                "COHERENT_COMPOSITE_SUPPORT",
                "MIXED_DIRECT_AND_COMPOSITE_SUPPORT",
                "PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE",
                "INQUIRY_ONLY_OR_UNRESOLVED",
                "INSUFFICIENT_EVIDENCE",
                "COOCCURRENCE_ONLY",
                "BOUNDED_SENSE_OR_SCOPE_CONFLICT",
                "TOPOLOGY_OR_ROLE_CONFLICT",
                "HARD_NEGATIVE",
                "PENDING_GOVERNED_REVIEW",
            ),
            "global_coherence": enum("PASS", "FAIL", "UNRESOLVED"),
            "bounded_senses_compatible": {"type": "boolean"},
            "case_scope_compatible": {"type": "boolean"},
            "roles_and_topology_supported": {"type": "boolean"},
            "unsupported_bridge_count": {"type": "integer", "minimum": 0},
            "review_authority": enum("SYNTHETIC_TEST_AUTHORITY", "RESEARCH_REVIEW", "EXTERNAL_HUMAN_REVIEW"),
            "authority_state": enum("PENDING", "FINAL"),
            "review_version": STRING,
            "qualifications": array(STRING),
            "explicit_non_claims": array(STRING, minimum=1),
        }
    )
    gate = object_schema(
        {
            "requested_state": enum("INACTIVE", "ACTIVE"),
            "decision": enum("ALLOW", "REJECT", "NOT_REQUESTED"),
            "all_gates_pass": {"type": "boolean"},
            "evidence_gate": {"type": "boolean"},
            "final_review_gate": {"type": "boolean"},
            "authority_gate": {"type": "boolean"},
            "coherence_gate": {"type": "boolean"},
            "rights_gate": {"type": "boolean"},
            "conflict_gate": {"type": "boolean"},
            "bounded_scope_gate": {"type": "boolean"},
            "synthesis_gate": {"type": "boolean"},
            "product_policy_gate": {"type": "boolean"},
            "reasons": array(STRING),
        }
    )
    uncertainty = object_schema(
        {
            "status": enum("RESOLVED_BOUNDED", "UNRESOLVED", "UNKNOWN"),
            "level": enum("LOW", "MEDIUM", "HIGH", "UNKNOWN"),
            "rationale": STRING,
            "basis": array(STRING, minimum=1),
            "unresolved_questions": array(STRING),
            "reviewed_in_review_id": STRING,
            "activation_policy": enum("ALLOWED_BOUNDED", "BLOCKS_ACTIVATION"),
        }
    )
    authority = object_schema(
        {
            "authority_id": STRING,
            "authority_kind": enum(
                "SYNTHETIC_TEST_AUTHORITY", "RESEARCH_REVIEW", "EXTERNAL_HUMAN_REVIEW"
            ),
            "authority_state": enum("PENDING", "FINAL"),
            "authority_version": STRING,
        }
    )
    common = schema_document(
        "common.schema.json",
        "TRACE Exploration v3 common semantic structures",
        {
            "$defs": {
                "sha256": SHA256,
                "scope": scope,
                "participantIncidence": participant,
                "evidenceAssessment": evidence,
                "governedReview": review,
                "activationGate": gate,
                "uncertaintyAssessment": uncertainty,
                "governedAuthority": authority,
            }
        },
    )

    concept_product_fields = {
        "product_eligible": {"type": "boolean"},
        "product_path": {"type": ["string", "null"]},
        "product_eligibility_disposition": enum(
            "ELIGIBLE", "INELIGIBLE", "DEFERRED", "NOT_APPLICABLE_SYNTHETIC"
        ),
        "product_ineligibility_reason": {"type": ["string", "null"]},
    }
    concept_record = object_schema(
        {
            "concept_id": STRING,
            "realm": enum("PRODUCTION", "SYNTHETIC_CONTROL"),
            "canonical_label": STRING,
            "semantic_version": STRING,
            "lifecycle_state": enum("INQUIRY_ONLY", "INACTIVE", "ACTIVE", "REJECTED"),
            "association_eligible": {"type": "boolean"},
            "authority": {"$ref": "common.schema.json#/$defs/governedAuthority"},
            **concept_product_fields,
            "semantic_sha256": SHA256,
        },
        extra={
            "allOf": [
                {
                    "if": {"properties": {"lifecycle_state": {"const": "ACTIVE"}}},
                    "then": {
                        "properties": {
                            "association_eligible": {"const": True},
                            "authority": {
                                "properties": {"authority_state": {"const": "FINAL"}}
                            },
                        }
                    },
                },
                {
                    "if": {"properties": {"realm": {"const": "PRODUCTION"}}},
                    "then": {
                        "properties": {
                            "authority": {
                                "properties": {
                                    "authority_kind": {
                                        "enum": ["RESEARCH_REVIEW", "EXTERNAL_HUMAN_REVIEW"]
                                    }
                                }
                            }
                        }
                    },
                },
                {
                    "if": {"properties": {"product_eligible": {"const": True}}},
                    "then": {
                        "properties": {
                            "realm": {"const": "PRODUCTION"},
                            "lifecycle_state": {"const": "ACTIVE"},
                            "association_eligible": {"const": True},
                            "product_path": {"type": "string", "minLength": 1},
                            "product_eligibility_disposition": {"const": "ELIGIBLE"},
                            "product_ineligibility_reason": {"const": None},
                        }
                    },
                    "else": {
                        "properties": {
                            "product_path": {"const": None},
                            "product_eligibility_disposition": {
                                "enum": ["INELIGIBLE", "DEFERRED", "NOT_APPLICABLE_SYNTHETIC"]
                            },
                            "product_ineligibility_reason": {"type": "string", "minLength": 1},
                        }
                    },
                },
            ]
        },
    )
    sense_record = object_schema(
        {
            "sense_id": STRING,
            "concept_id": STRING,
            "realm": enum("PRODUCTION", "SYNTHETIC_CONTROL"),
            "bounded_definition": STRING,
            "vocabulary_crosswalk_ids": array(STRING, minimum=1, unique=True),
            "governed_scope_ids": array(STRING, minimum=1, unique=True),
            "semantic_version": STRING,
            "lifecycle_state": enum("INQUIRY_ONLY", "INACTIVE", "ACTIVE", "REJECTED"),
            "association_eligible": {"type": "boolean"},
            "authority": {"$ref": "common.schema.json#/$defs/governedAuthority"},
            **concept_product_fields,
            "semantic_sha256": SHA256,
        },
        extra={"allOf": copy.deepcopy(concept_record["allOf"])},
    )
    concept_schema = schema_document(
        "concept.schema.json",
        "TRACE Exploration v3 governed vocabulary concepts and bounded senses",
        {"$defs": {"concept": concept_record, "conceptSense": sense_record}},
    )

    association_properties = {
        "association_id": STRING,
        "association_revision_id": STRING,
        "association_kind": enum("PAIR", "HIGHER_ORDER"),
        "realm": enum("PRODUCTION", "SYNTHETIC_CONTROL"),
        "semantic_version": STRING,
        "arity": {"type": "integer", "minimum": 2},
        "order_semantics": enum("UNORDERED", "ORDERED"),
        "roles_meaningful": {"type": "boolean"},
        "scope": {"$ref": "common.schema.json#/$defs/scope"},
        "participants": array({"$ref": "common.schema.json#/$defs/participantIncidence"}, minimum=2),
        "evidence": {"$ref": "common.schema.json#/$defs/evidenceAssessment"},
        "review": {"$ref": "common.schema.json#/$defs/governedReview"},
        "activation": {"$ref": "common.schema.json#/$defs/activationGate"},
        "uncertainty": {"$ref": "common.schema.json#/$defs/uncertaintyAssessment"},
        "lifecycle_state": enum("INQUIRY_ONLY", "INACTIVE", "ACTIVE", "REJECTED"),
        "pair_projection_policy": enum("NOT_APPLICABLE", "NONE"),
        "internal_pair_association_ids": array(STRING, unique=True),
        "internal_pair_links": array(
            object_schema(
                {
                    "pair_association_id": STRING,
                    "pair_association_revision_id": STRING,
                    "participant_incidence_ids": {
                        "type": "array",
                        "items": STRING,
                        "minItems": 2,
                        "maxItems": 2,
                        "uniqueItems": True,
                    },
                    "pair_participant_incidence_ids": {
                        "type": "array",
                        "items": STRING,
                        "minItems": 2,
                        "maxItems": 2,
                        "uniqueItems": True,
                    },
                    "endpoint_sense_ids": {
                        "type": "array",
                        "items": STRING,
                        "minItems": 2,
                        "maxItems": 2,
                        "uniqueItems": True,
                    },
                }
            ),
            unique=True,
        ),
        "product_eligible": {"type": "boolean"},
        "product_path": {"type": ["string", "null"]},
        "product_eligibility_disposition": enum(
            "ELIGIBLE", "INELIGIBLE", "DEFERRED", "NOT_APPLICABLE_SYNTHETIC"
        ),
        "product_ineligibility_reason": {"type": ["string", "null"]},
        "identity_material_sha256": SHA256,
        "semantic_sha256": SHA256,
        "presentation": object_schema(
            {
                "realization_hint": enum("PAIR_EDGE", "HYPEREDGE_HUB"),
                "theme": STRING,
            }
        ),
        "presentation_sha256": SHA256,
    }
    association = schema_document(
        "association.schema.json",
        "TRACE Exploration v3 governed association revision",
        object_schema(
            association_properties,
            extra={
                "allOf": [
                    {
                        "if": {"properties": {"association_kind": {"const": "PAIR"}}},
                        "then": {
                            "properties": {
                                "arity": {"const": 2},
                                "pair_projection_policy": {"const": "NOT_APPLICABLE"},
                            }
                        },
                    },
                    {
                        "if": {"properties": {"association_kind": {"const": "HIGHER_ORDER"}}},
                        "then": {
                            "properties": {
                                "arity": {"minimum": 3},
                                "pair_projection_policy": {"const": "NONE"},
                            }
                        },
                    },
                    {
                        "if": {"properties": {"order_semantics": {"const": "ORDERED"}}},
                        "then": {
                            "properties": {
                                "participants": {
                                    "items": {
                                        "properties": {"ordinal": {"type": "integer", "minimum": 0}}
                                    }
                                }
                            }
                        },
                    },
                    {
                        "if": {"properties": {"order_semantics": {"const": "UNORDERED"}}},
                        "then": {
                            "properties": {
                                "participants": {"items": {"properties": {"ordinal": {"const": None}}}}
                            }
                        },
                    },
                    {
                        "if": {"properties": {"roles_meaningful": {"const": True}}},
                        "then": {
                            "properties": {
                                "participants": {
                                    "items": {"properties": {"role_id": {"type": "string", "minLength": 1}}}
                                }
                            }
                        },
                        "else": {
                            "properties": {
                                "participants": {"items": {"properties": {"role_id": {"const": None}}}}
                            }
                        },
                    },
                    {
                        "if": {"properties": {"lifecycle_state": {"const": "ACTIVE"}}},
                        "then": {
                            "properties": {
                                "review": {
                                    "allOf": [
                                        {"properties": {"review_state": {"const": "FINAL"}}},
                                        {"properties": {"authority_state": {"const": "FINAL"}}},
                                        {"properties": {"global_coherence": {"const": "PASS"}}},
                                        {"properties": {"bounded_senses_compatible": {"const": True}}},
                                        {"properties": {"case_scope_compatible": {"const": True}}},
                                        {"properties": {"roles_and_topology_supported": {"const": True}}},
                                        {"properties": {"unsupported_bridge_count": {"const": 0}}},
                                        {
                                            "properties": {
                                                "disposition": {
                                                    "enum": [
                                                        "DIRECT_PAIRWISE_SUPPORT",
                                                        "DIRECT_HIGHER_ORDER_SUPPORT",
                                                        "COHERENT_COMPOSITE_SUPPORT",
                                                        "MIXED_DIRECT_AND_COMPOSITE_SUPPORT",
                                                    ]
                                                }
                                            }
                                        },
                                    ]
                                },
                                "evidence": {
                                    "properties": {
                                        "evidence_item_ids": {"minItems": 1},
                                        "locator_ids": {"minItems": 1},
                                        "support_mode": {
                                            "enum": [
                                                "DIRECT_PAIR",
                                                "DIRECT_GROUP",
                                                "COHERENT_COMPOSITE",
                                                "MIXED",
                                            ]
                                        },
                                        "same_configuration": {"const": True},
                                        "negative_or_conflicting_evidence": {"maxItems": 0},
                                        "conflicts_resolved": {"const": True},
                                        "rights_cleared_for_governed_use": {"const": True},
                                        "evidence_complete": {"const": True},
                                    }
                                },
                                "activation": {
                                    "properties": {
                                        "requested_state": {"const": "ACTIVE"},
                                        "decision": {"const": "ALLOW"},
                                        "all_gates_pass": {"const": True},
                                        "evidence_gate": {"const": True},
                                        "final_review_gate": {"const": True},
                                        "authority_gate": {"const": True},
                                        "coherence_gate": {"const": True},
                                        "rights_gate": {"const": True},
                                        "conflict_gate": {"const": True},
                                        "bounded_scope_gate": {"const": True},
                                        "synthesis_gate": {"const": True},
                                        "product_policy_gate": {"const": True},
                                    }
                                },
                                "uncertainty": {
                                    "properties": {
                                        "status": {"const": "RESOLVED_BOUNDED"},
                                        "activation_policy": {"const": "ALLOWED_BOUNDED"},
                                    }
                                },
                            }
                        },
                    },
                    {
                        "if": {"properties": {"realm": {"const": "PRODUCTION"}}},
                        "then": {
                            "properties": {
                                "review": {
                                    "properties": {
                                        "review_authority": {
                                            "enum": ["RESEARCH_REVIEW", "EXTERNAL_HUMAN_REVIEW"]
                                        }
                                    }
                                }
                            }
                        },
                    },
                    {
                        "if": {
                            "properties": {
                                "association_kind": {"const": "PAIR"},
                                "lifecycle_state": {"const": "ACTIVE"},
                            },
                            "required": ["association_kind", "lifecycle_state"],
                        },
                        "then": {
                            "properties": {
                                "review": {
                                    "properties": {"disposition": {"const": "DIRECT_PAIRWISE_SUPPORT"}}
                                },
                                "evidence": {"properties": {"support_mode": {"const": "DIRECT_PAIR"}}},
                            }
                        },
                    },
                    {
                        "if": {
                            "properties": {
                                "association_kind": {"const": "HIGHER_ORDER"},
                                "lifecycle_state": {"const": "ACTIVE"},
                            },
                            "required": ["association_kind", "lifecycle_state"],
                        },
                        "then": {
                            "properties": {
                                "review": {
                                    "properties": {
                                        "disposition": {
                                            "enum": [
                                                "DIRECT_HIGHER_ORDER_SUPPORT",
                                                "COHERENT_COMPOSITE_SUPPORT",
                                                "MIXED_DIRECT_AND_COMPOSITE_SUPPORT",
                                            ]
                                        }
                                    }
                                },
                                "evidence": {
                                    "properties": {
                                        "support_mode": {
                                            "enum": ["DIRECT_GROUP", "COHERENT_COMPOSITE", "MIXED"]
                                        }
                                    }
                                },
                            }
                        },
                    },
                    *[
                        {
                            "if": {
                                "properties": {
                                    "association_kind": {"const": "HIGHER_ORDER"},
                                    "lifecycle_state": {"const": "ACTIVE"},
                                    "evidence": {
                                        "properties": {"support_mode": {"const": support_mode}}
                                    },
                                },
                                "required": ["association_kind", "lifecycle_state", "evidence"],
                            },
                            "then": {
                                "properties": {
                                    "review": {
                                        "properties": {"disposition": {"const": disposition}}
                                    }
                                }
                            },
                        }
                        for support_mode, disposition in (
                            ("DIRECT_GROUP", "DIRECT_HIGHER_ORDER_SUPPORT"),
                            ("COHERENT_COMPOSITE", "COHERENT_COMPOSITE_SUPPORT"),
                            ("MIXED", "MIXED_DIRECT_AND_COMPOSITE_SUPPORT"),
                        )
                    ],
                    {
                        "if": {"properties": {"product_eligible": {"const": True}}},
                        "then": {
                            "properties": {
                                "realm": {"const": "PRODUCTION"},
                                "lifecycle_state": {"const": "ACTIVE"},
                                "product_path": {"type": "string", "minLength": 1},
                                "product_eligibility_disposition": {"const": "ELIGIBLE"},
                                "product_ineligibility_reason": {"const": None},
                                "activation": {
                                    "properties": {
                                        "decision": {"const": "ALLOW"},
                                        "all_gates_pass": {"const": True},
                                        "product_policy_gate": {"const": True},
                                    }
                                },
                            }
                        },
                        "else": {
                            "properties": {
                                "product_path": {"const": None},
                                "product_eligibility_disposition": {
                                    "enum": ["INELIGIBLE", "DEFERRED", "NOT_APPLICABLE_SYNTHETIC"]
                                },
                                "product_ineligibility_reason": {"type": "string", "minLength": 1},
                            }
                        },
                    },
                    {
                        "if": {
                            "properties": {
                                "realm": {"const": "PRODUCTION"},
                                "lifecycle_state": {"const": "ACTIVE"},
                                "product_eligible": {"const": False},
                            },
                            "required": ["realm", "lifecycle_state", "product_eligible"],
                        },
                        "then": {
                            "properties": {
                                "product_eligibility_disposition": {"enum": ["INELIGIBLE", "DEFERRED"]}
                            }
                        },
                    },
                ]
            },
        ),
    )

    realization = object_schema(
        {
            "association_realization_id": STRING,
            "association_revision_id": STRING,
            "realization_kind": enum("PAIR_EDGE", "HYPEREDGE_HUB", "HYPEREDGE_CONTOUR", "LIST_GROUP"),
            "realized_incidence_ids": array(STRING, minimum=2, unique=True),
            "semantic_sha256": SHA256,
            "presentation": object_schema({"layout": STRING, "style": STRING}),
            "presentation_sha256": SHA256,
        }
    )
    composition_coherence_review = object_schema(
        {
            "composition_coherence_review_id": STRING,
            "composition_id": STRING,
            "realm": enum("PRODUCTION", "SYNTHETIC_CONTROL"),
            "review_state": enum("PENDING", "NONFINAL", "FINAL"),
            "authority": {"$ref": "common.schema.json#/$defs/governedAuthority"},
            "review_version": STRING,
            "global_coherence": enum("PASS", "FAIL", "UNRESOLVED"),
            "bounded_senses_compatible": {"type": "boolean"},
            "case_scope_compatible": {"type": "boolean"},
            "roles_and_topology_supported": {"type": "boolean"},
            "same_configuration": {"type": "boolean"},
            "unsupported_bridge_count": {"type": "integer", "minimum": 0},
            "association_revision_ids": array(STRING, minimum=1, unique=True),
            "association_realization_ids": array(STRING, minimum=1, unique=True),
            "incidence_ids": array(STRING, minimum=2, unique=True),
            "decision": enum("COHERENT", "INCOHERENT", "UNRESOLVED"),
            "reasons": array(STRING, minimum=1),
            "semantic_sha256": SHA256,
        },
        extra={
            "allOf": [
                {
                    "if": {"properties": {"realm": {"const": "PRODUCTION"}}},
                    "then": {
                        "properties": {
                            "authority": {
                                "properties": {
                                    "authority_kind": {
                                        "enum": ["RESEARCH_REVIEW", "EXTERNAL_HUMAN_REVIEW"]
                                    }
                                }
                            }
                        }
                    },
                },
                {
                    "if": {"properties": {"decision": {"const": "COHERENT"}}},
                    "then": {
                        "properties": {
                            "review_state": {"const": "FINAL"},
                            "authority": {
                                "properties": {"authority_state": {"const": "FINAL"}}
                            },
                            "global_coherence": {"const": "PASS"},
                            "bounded_senses_compatible": {"const": True},
                            "case_scope_compatible": {"const": True},
                            "roles_and_topology_supported": {"const": True},
                            "same_configuration": {"const": True},
                            "unsupported_bridge_count": {"const": 0},
                        }
                    },
                },
            ]
        },
    )
    composition_properties = {
        "composition_id": STRING,
        "composition_revision_id": STRING,
        "realm": enum("PRODUCTION", "SYNTHETIC_CONTROL"),
        "association_realizations": array(realization, minimum=1),
        "composition_node_ids": array(STRING, minimum=2, unique=True),
        "topology_family": STRING,
        "renderability": enum("PASS", "FAIL"),
        "global_coherence_review_id": STRING,
        "association_trace_complete": {"type": "boolean"},
        "product_eligible": {"type": "boolean"},
        "product_path": {"type": ["string", "null"]},
        "product_eligibility_disposition": enum(
            "ELIGIBLE", "INELIGIBLE", "DEFERRED", "NOT_APPLICABLE_SYNTHETIC"
        ),
        "product_ineligibility_reason": {"type": ["string", "null"]},
        "semantic_sha256": SHA256,
        "presentation": object_schema({"layout": STRING, "seed": STRING}),
        "presentation_sha256": SHA256,
    }
    composition = schema_document(
        "composition.schema.json",
        "TRACE Exploration v3 composition and association realization",
        {
            "$defs": {"compositionCoherenceReview": composition_coherence_review},
            **object_schema(
                composition_properties,
                extra={
                "allOf": [
                    {
                        "if": {"properties": {"product_eligible": {"const": True}}},
                        "then": {
                            "properties": {
                                "realm": {"const": "PRODUCTION"},
                                "association_trace_complete": {"const": True},
                                "renderability": {"const": "PASS"},
                                "product_path": {"type": "string", "minLength": 1},
                                "product_eligibility_disposition": {"const": "ELIGIBLE"},
                                "product_ineligibility_reason": {"const": None},
                            }
                        },
                        "else": {
                            "properties": {
                                "product_path": {"const": None},
                                "product_eligibility_disposition": {
                                    "enum": ["INELIGIBLE", "DEFERRED", "NOT_APPLICABLE_SYNTHETIC"]
                                },
                                "product_ineligibility_reason": {"type": "string", "minLength": 1},
                            }
                        },
                    },
                ]
                },
            ),
        },
    )

    nav_node = object_schema(
        {
            "navigation_node_id": STRING,
            "node_kind": enum("CONCEPT", "ASSOCIATION"),
            "concept_id": {"type": ["string", "null"]},
            "association_revision_id": {"type": ["string", "null"]},
        },
        extra={
            "allOf": [
                {
                    "if": {"properties": {"node_kind": {"const": "CONCEPT"}}},
                    "then": {
                        "properties": {
                            "concept_id": {"type": "string", "minLength": 1},
                            "association_revision_id": {"const": None},
                        }
                    },
                    "else": {
                        "properties": {
                            "concept_id": {"const": None},
                            "association_revision_id": {"type": "string", "minLength": 1},
                        }
                    },
                }
            ]
        },
    )
    nav_step = object_schema(
        {
            "from_navigation_node_id": STRING,
            "incidence_id": STRING,
            "to_navigation_node_id": STRING,
        }
    )
    navigation = schema_document(
        "navigation-state.schema.json",
        "TRACE Exploration v3 bipartite navigation state",
        object_schema(
            {
                "state_id": STRING,
                "realm": enum("PRODUCTION", "SYNTHETIC_CONTROL"),
                "composition_revision_id": STRING,
                "nodes": array(nav_node, minimum=3),
                "path": array(nav_step, minimum=1),
                "focus_navigation_node_id": STRING,
                "bipartite_alternation_valid": {"type": "boolean", "const": True},
                "semantic_sha256": SHA256,
                "presentation": object_schema({"focus_style": STRING, "viewport": STRING}),
                "presentation_sha256": SHA256,
            }
        ),
    )

    transition = schema_document(
        "transition.schema.json",
        "TRACE Exploration v3 governed state transition",
        object_schema(
            {
                "transition_id": STRING,
                "realm": enum("PRODUCTION", "SYNTHETIC_CONTROL"),
                "from_state_id": STRING,
                "to_state_id": STRING,
                "transition_kind": enum("FOLLOW_INCIDENCE", "MOVE_FOCUS", "EXPORT"),
                "incidence_id": {"type": ["string", "null"]},
                "association_revision_id": {"type": ["string", "null"]},
                "association_realization_id": {"type": ["string", "null"]},
                "state_mutated": {"type": "boolean"},
                "semantic_sha256": SHA256,
            }
        ),
    )

    workflow = schema_document(
        "workflow.schema.json",
        "TRACE Exploration v3 workflow",
        object_schema(
            {
                "workflow_id": STRING,
                "realm": enum("PRODUCTION", "SYNTHETIC_CONTROL"),
                "initial_state_id": STRING,
                "transition_kind": enum("FOLLOW_INCIDENCE", "MOVE_FOCUS", "EXPORT"),
                "association_revision_ids": array(STRING, minimum=1, unique=True),
                "association_realization_ids": array(STRING, minimum=1, unique=True),
                "state_ids": array(STRING, minimum=1, unique=True),
                "transition_ids": array(STRING, unique=True),
                "reachable": {"type": "boolean"},
                "semantic_sha256": SHA256,
            }
        ),
    )
    export_manifest = schema_document(
        "export-manifest.schema.json",
        "TRACE Exploration v3 export manifest",
        object_schema(
            {
                "export_id": STRING,
                "realm": enum("PRODUCTION", "SYNTHETIC_CONTROL"),
                "workflow_id": STRING,
                "state_id": STRING,
                "association_revision_ids": array(STRING, minimum=1, unique=True),
                "association_realization_ids": array(STRING, minimum=1, unique=True),
                "projection_preservation_records": array(
                    object_schema(
                        {
                            "association_revision_id": STRING,
                            "association_realization_id": STRING,
                            "pair_projection_policy": enum("NOT_APPLICABLE", "NONE"),
                            "realization_kind": enum(
                                "PAIR_EDGE", "HYPEREDGE_HUB", "HYPEREDGE_CONTOUR", "LIST_GROUP"
                            ),
                        }
                    ),
                    minimum=1,
                    unique=True,
                ),
                "composition_revision_id": STRING,
                "semantic_sha256": SHA256,
                "presentation": object_schema({"format": STRING, "theme": STRING}),
                "presentation_sha256": SHA256,
                "pair_projection_policy_preserved": {"type": "boolean", "const": True},
            }
        ),
    )
    adapter = schema_document(
        "v2-pair-adapter.schema.json",
        "TRACE Exploration v2 pair to v3 pair one-way adapter receipt",
        object_schema(
            {
                "adapter_id": STRING,
                "direction": {"const": "V2_PAIR_TO_V3_PAIR_ONLY"},
                "source_contract": {"const": "trace/exploration/v2"},
                "target_contract": {"const": "trace/exploration/v3"},
                "source_pair_id": STRING,
                "source_pair_fixture_sha256": SHA256,
                "source_endpoint_ids": {"type": "array", "items": STRING, "minItems": 2, "maxItems": 2, "uniqueItems": True},
                "target_association_revision_id": STRING,
                "target_incidence_ids": {"type": "array", "items": STRING, "minItems": 2, "maxItems": 2, "uniqueItems": True},
                "endpoint_crosswalk": {
                    "type": "array",
                    "minItems": 2,
                    "maxItems": 2,
                    "items": object_schema(
                        {
                            "source_endpoint_id": STRING,
                            "target_incidence_id": STRING,
                            "target_concept_id": STRING,
                            "target_sense_id": STRING,
                        }
                    ),
                },
                "input_arity": {"const": 2},
                "output_association_kind": {"const": "PAIR"},
                "higher_order_input_allowed": {"const": False},
                "reverse_conversion_allowed": {"const": False},
                "semantic_claims_added": {"const": False},
                "semantic_sha256": SHA256,
            }
        ),
    )
    material_binding = object_schema(
        {
            "material_name": STRING,
            "recipe": enum(
                "DIRECT_FIELD_OBJECT",
                "DIRECT_FIELD_VALUE",
                "ASSOCIATION_IDENTITY",
                "ASSOCIATION_REVISION",
                "REALIZATION_SEMANTIC_ALIASES",
                "COMPOSITION_IDENTITY_ALIASES",
                "COMPOSITION_REVISION",
                "INCIDENCE_IDENTIFIER",
                "STATIC_AUTHORITY_IDENTIFIER",
            ),
            "source_fields": array(STRING),
            "output_keys": array(STRING, unique=True),
            "field_mappings": array(
                object_schema(
                    {
                        "output_key": STRING,
                        "source_pointer": STRING,
                        "operation": enum(
                            "COPY",
                            "MAP_ARRAY_FIELD",
                            "MERGE_OBJECT",
                            "PROJECT_PARTICIPANT_IDENTITY",
                            "PROJECT_SCOPE_IDENTITY",
                        ),
                        "item_field": {"type": ["string", "null"]},
                    }
                )
            ),
            "normalization_rules": array(STRING),
            "wrapper": enum(
                "NONE",
                "MERGE_ASSOCIATION_ID_WITH_SEMANTIC",
                "OBJECT_WITH_SEMANTIC_AND_REVISION_ONE",
            ),
        }
    )
    identifier_binding = object_schema(
        {
            "identifier_field": STRING,
            "prefix": STRING,
            "digest_material_name": {"type": ["string", "null"]},
            "digest_hex_chars": {"type": "integer", "minimum": 0},
            "suffix_rule": enum("NONE", "ONE_BASED_CANONICAL_PARTICIPANT_POSITION_PAD2"),
        }
    )
    hash_binding = object_schema(
        {
            "object_type": STRING,
            "collection_pointer": STRING,
            "materials": array(material_binding, minimum=1),
            "identifiers": array(identifier_binding),
            "hash_fields": array(
                object_schema(
                    {
                        "hash_field": STRING,
                        "material_name": STRING,
                        "representation": {"const": "LOWERCASE_HEX_64"},
                    }
                )
            ),
        }
    )
    hash_binding_contract_schema = schema_document(
        "hash-binding-contract.schema.json",
        "TRACE Exploration v3 normative hash and identifier binding contract",
        object_schema(
            {
                "contract_version": STRING,
                "canonicalization": object_schema(
                    {
                        "digest_algorithm": {"const": "SHA-256"},
                        "text_encoding": {"const": "UTF-8"},
                        "json_ensure_ascii": {"const": False},
                        "object_key_order": {"const": "LEXICOGRAPHIC_ASCENDING"},
                        "item_separators": {"const": [",", ":"]},
                        "trailing_newline_in_digest_material": {"const": False},
                        "array_order_default": {"const": "PRESERVE_STORED_ORDER"},
                        "digest_representation": {"const": "LOWERCASE_HEX_64"},
                    }
                ),
                "bindings": array(hash_binding, minimum=1),
            }
        ),
    )
    nonnegative = {"type": "integer", "minimum": 0}
    count_taxonomy = object_schema(
        {
            "vocabulary": object_schema(
                {
                    "synthetic_scope_count": nonnegative,
                    "synthetic_distinct_concept_count": nonnegative,
                    "synthetic_concept_record_count": nonnegative,
                    "synthetic_active_concept_count": nonnegative,
                    "synthetic_concept_sense_record_count": nonnegative,
                    "synthetic_active_concept_sense_count": nonnegative,
                    "production_active_concept_count": nonnegative,
                }
            ),
            "associations": object_schema(
                {
                    "synthetic_pair_revision_count": nonnegative,
                    "synthetic_higher_order_revision_count": nonnegative,
                    "synthetic_active_pair_revision_count": nonnegative,
                    "synthetic_active_higher_order_revision_count": nonnegative,
                    "production_pair_revision_count": nonnegative,
                    "production_higher_order_revision_count": nonnegative,
                    "production_active_association_count": nonnegative,
                    "production_active_pending_review_count": nonnegative,
                }
            ),
            "incidence": object_schema(
                {
                    "synthetic_incidence_count": nonnegative,
                    "production_incidence_count": nonnegative,
                    "implicit_projected_pair_count": nonnegative,
                }
            ),
            "realizations_and_compositions": object_schema(
                {
                    "synthetic_association_realization_count": nonnegative,
                    "synthetic_composition_count": nonnegative,
                    "synthetic_composition_coherence_review_count": nonnegative,
                    "production_association_realization_count": nonnegative,
                    "production_composition_count": nonnegative,
                    "production_composition_coherence_review_count": nonnegative,
                    "production_product_eligible_composition_count": nonnegative,
                }
            ),
            "interaction": object_schema(
                {
                    "synthetic_state_count": nonnegative,
                    "synthetic_transition_count": nonnegative,
                    "synthetic_workflow_count": nonnegative,
                    "synthetic_export_count": nonnegative,
                    "production_state_count": nonnegative,
                    "production_transition_count": nonnegative,
                    "production_workflow_count": nonnegative,
                    "production_export_count": nonnegative,
                }
            ),
        }
    )
    closure_flags = object_schema(
        {
            "pair_association_closure": {"type": "boolean"},
            "higher_order_association_closure": {"type": "boolean"},
            "global_composition_coherence_closure": {"type": "boolean"},
            "product_association_reachability_closure": {"type": "boolean"},
            "computational_space_closure": {"type": "boolean"},
            "function3_closure": {"type": "boolean"},
        }
    )
    identity_participant = object_schema(
        {
            "concept_id": STRING,
            "sense_id": STRING,
            "ordinal": {"type": ["integer", "null"], "minimum": 0},
            "role_id": {"type": ["string", "null"]},
        }
    )
    scope_identity_schema = object_schema(
        {
            "scope_id": STRING,
            "historical_case_ids": array(STRING, unique=True),
            "time_bounds": object_schema(
                {"start": {"type": ["string", "null"]}, "end": {"type": ["string", "null"]}}
            ),
            "geographies": array(STRING, unique=True),
            "institutions": array(STRING, unique=True),
            "actors": array(STRING, unique=True),
            "mechanisms": array(STRING, unique=True),
        }
    )
    association_identity_schema = object_schema(
        {
            "association_kind": enum("PAIR", "HIGHER_ORDER"),
            "participants": array(identity_participant, minimum=2),
            "scope_identity": scope_identity_schema,
            "order_semantics": enum("UNORDERED", "ORDERED"),
            "roles_meaningful": {"type": "boolean"},
        }
    )
    root = schema_document(
        "semantic-contract.schema.json",
        "TRACE Exploration v3 semantic contract fixture bundle",
        object_schema(
            {
                "contract_version": {"const": CONTRACT_VERSION},
                "api_namespace": {"const": "trace/exploration/v3"},
                "source_sha": {"const": SOURCE_SHA},
                "parent_checkpoint_sha": {"const": PARENT_CHECKPOINT_SHA},
                "hash_binding_contract": {"$ref": "hash-binding-contract.schema.json"},
                "hash_binding_contract_canonical_sha256": SHA256,
                "object_boundaries": object_schema(
                    {
                        "association_is_evidence_bearing_semantic_object": {"const": True},
                        "composition_is_governed_realization_object": {"const": True},
                        "association_and_composition_counts_are_distinct": {"const": True},
                        "implicit_pair_projection_forbidden": {"const": True},
                        "navigation_model": {"const": "BIPARTITE_CONCEPT_ASSOCIATION_INCIDENCE"},
                    }
                ),
                "scopes": array({"$ref": "common.schema.json#/$defs/scope"}, minimum=1),
                "concepts": array({"$ref": "concept.schema.json#/$defs/concept"}, minimum=1),
                "concept_senses": array(
                    {"$ref": "concept.schema.json#/$defs/conceptSense"}, minimum=1
                ),
                "associations": array({"$ref": "association.schema.json"}, minimum=1),
                "composition_coherence_reviews": array(
                    {"$ref": "composition.schema.json#/$defs/compositionCoherenceReview"},
                    minimum=1,
                ),
                "compositions": array({"$ref": "composition.schema.json"}, minimum=1),
                "navigation_states": array({"$ref": "navigation-state.schema.json"}, minimum=1),
                "transitions": array({"$ref": "transition.schema.json"}),
                "workflows": array({"$ref": "workflow.schema.json"}, minimum=1),
                "exports": array({"$ref": "export-manifest.schema.json"}, minimum=1),
                "v2_pair_source_fixtures": array(
                    object_schema(
                        {
                            "source_pair_id": STRING,
                            "endpoints": {
                                "type": "array",
                                "minItems": 2,
                                "maxItems": 2,
                                "items": object_schema(
                                    {
                                        "source_endpoint_id": STRING,
                                        "concept_id": STRING,
                                        "sense_id": STRING,
                                    }
                                ),
                            },
                            "source_pair_fixture_sha256": SHA256,
                        }
                    ),
                    minimum=1,
                ),
                "v2_pair_adapter_receipts": array({"$ref": "v2-pair-adapter.schema.json"}, minimum=1),
                "invalid_attempts": array(
                    object_schema(
                        {
                            "attempt_id": STRING,
                            "attempt_kind": enum("ILLEGAL_PAIR_PROJECTION", "ACTIVE_WITH_NONFINAL_REVIEW"),
                            "association_revision_id": STRING,
                            "requested_value": STRING,
                            "expected_decision": {"const": "REJECT"},
                            "expected_error_code": STRING,
                        }
                    ),
                    minimum=2,
                ),
                "control_expectations": array(
                    object_schema(
                        {
                            "control_id": STRING,
                            "control_class": STRING,
                            "object_refs": array(STRING, minimum=1),
                            "expected_result": enum("PASS", "REJECT", "INACTIVE"),
                            "assertions": array(STRING, minimum=1),
                        }
                    ),
                    minimum=9,
                ),
                "schema_negative_probe_receipts": array(
                    object_schema(
                        {
                            "probe_id": STRING,
                            "target_schema": STRING,
                            "base_object_ref": STRING,
                            "mutation_pointer": STRING,
                            "mutation_value_json": {"type": "string"},
                            "validator": enum(
                                "JSON_SCHEMA", "SEMANTIC_INVARIANT", "FIXTURE_SEMANTIC_INVARIANT"
                            ),
                            "expected_error_code": STRING,
                            "expected_rejected": {"const": True},
                            "observed_rejected": {"const": True},
                            "observed_error_codes": array(STRING, minimum=1),
                        }
                    ),
                    minimum=1,
                ),
                "identity_branch_test_receipts": array(
                    object_schema(
                        {
                            "test_id": STRING,
                            "branch": enum(
                                "UNORDERED_PERMUTATION_INVARIANT",
                                "ORDERED_CONTIGUOUS_ORDINAL_SENSITIVE",
                                "UNORDERED_MEANINGFUL_ROLE_PERMUTATION_INVARIANT",
                                "UNORDERED_MEANINGFUL_ROLE_REASSIGNMENT_SENSITIVE",
                            ),
                            "base_identity_sha256": SHA256,
                            "comparison_identity_sha256": SHA256,
                            "base_identity_material": association_identity_schema,
                            "comparison_identity_material": association_identity_schema,
                            "expected_relation": enum("EQUAL", "NOT_EQUAL"),
                            "observed_relation": enum("EQUAL", "NOT_EQUAL"),
                            "base_canonical_incidence_ids": array(STRING, minimum=2, unique=True),
                            "comparison_canonical_incidence_ids": array(STRING, minimum=2, unique=True),
                            "status": {"const": "PASS"},
                        }
                    ),
                    minimum=4,
                ),
                "count_taxonomy": count_taxonomy,
                "closure_flags": closure_flags,
            }
        ),
    )
    return {
        SCHEMA_REL / "common.schema.json": common,
        SCHEMA_REL / "concept.schema.json": concept_schema,
        SCHEMA_REL / "association.schema.json": association,
        SCHEMA_REL / "composition.schema.json": composition,
        SCHEMA_REL / "navigation-state.schema.json": navigation,
        SCHEMA_REL / "transition.schema.json": transition,
        SCHEMA_REL / "workflow.schema.json": workflow,
        SCHEMA_REL / "export-manifest.schema.json": export_manifest,
        SCHEMA_REL / "v2-pair-adapter.schema.json": adapter,
        SCHEMA_REL / "hash-binding-contract.schema.json": hash_binding_contract_schema,
        SCHEMA_REL / "semantic-contract.schema.json": root,
    }


def make_scope(scope_id: str, case_ids: list[str]) -> dict[str, Any]:
    return {
        "scope_id": scope_id,
        "historical_case_ids": sorted(set(case_ids)),
        "time_bounds": {"start": "SYNTHETIC", "end": "SYNTHETIC"},
        "geographies": sorted(["SYNTHETIC-GEOGRAPHY"]),
        "institutions": sorted(["SYNTHETIC-INSTITUTION"]),
        "actors": sorted(["SYNTHETIC-ACTOR"]),
        "mechanisms": sorted(["SYNTHETIC-MECHANISM"]),
        "context_qualifications": ["Synthetic verification fixture; not historical evidence."],
    }


def build_hash_binding_contract() -> dict[str, Any]:
    """Return the normative, implementation-independent hash/ID projection map."""

    def material(
        name: str,
        recipe: str,
        fields: list[str],
        *,
        output_keys: list[str] | None = None,
        mappings: list[dict[str, Any]] | None = None,
        rules: list[str] | None = None,
        wrapper: str = "NONE",
    ) -> dict[str, Any]:
        return {
            "material_name": name,
            "recipe": recipe,
            "source_fields": fields,
            "output_keys": output_keys if output_keys is not None else list(fields),
            "field_mappings": mappings or [],
            "normalization_rules": rules or [],
            "wrapper": wrapper,
        }

    def identifier(field: str, prefix: str, source: str | None, chars: int, suffix: str = "NONE") -> dict[str, Any]:
        return {
            "identifier_field": field,
            "prefix": prefix,
            "digest_material_name": source,
            "digest_hex_chars": chars,
            "suffix_rule": suffix,
        }

    def hash_field(field: str, source: str) -> dict[str, Any]:
        return {"hash_field": field, "material_name": source, "representation": "LOWERCASE_HEX_64"}

    association_semantic_fields = [
        "association_kind", "realm", "semantic_version", "arity", "order_semantics",
        "roles_meaningful", "identity_material_sha256", "scope", "participants", "evidence",
        "review", "activation", "uncertainty", "lifecycle_state", "pair_projection_policy",
        "internal_pair_association_ids", "internal_pair_links", "product_eligible", "product_path",
        "product_eligibility_disposition", "product_ineligibility_reason",
    ]
    bindings = [
        {
            "object_type": "ASSOCIATION_REVISION",
            "collection_pointer": "/associations/*",
            "materials": [
                material(
                    "association_identity",
                    "ASSOCIATION_IDENTITY",
                    ["association_kind", "participants", "scope", "order_semantics", "roles_meaningful"],
                    output_keys=[
                        "association_kind", "participants", "scope_identity",
                        "order_semantics", "roles_meaningful",
                    ],
                    mappings=[
                        {"output_key": "association_kind", "source_pointer": "/association_kind", "operation": "COPY", "item_field": None},
                        {"output_key": "participants", "source_pointer": "/participants", "operation": "PROJECT_PARTICIPANT_IDENTITY", "item_field": None},
                        {"output_key": "scope_identity", "source_pointer": "/scope", "operation": "PROJECT_SCOPE_IDENTITY", "item_field": None},
                        {"output_key": "order_semantics", "source_pointer": "/order_semantics", "operation": "COPY", "item_field": None},
                        {"output_key": "roles_meaningful", "source_pointer": "/roles_meaningful", "operation": "COPY", "item_field": None},
                    ],
                    rules=[
                        "PROJECT_PARTICIPANTS_TO_CONCEPT_ID_SENSE_ID_ORDINAL_ROLE_ID",
                        "ORDERED_PRESERVES_STORED_PARTICIPANT_ORDER_AND_REQUIRES_CONTIGUOUS_ZERO_BASED_ORDINALS",
                        "UNORDERED_STORED_ORDER_IS_CANONICAL",
                        "UNORDERED_WITHOUT_ROLES_SORTS_BY_SENSE_ID_THEN_CONCEPT_ID",
                        "UNORDERED_WITH_ROLES_SORTS_BY_ROLE_ID_EMPTY_FIRST_THEN_SENSE_ID_THEN_CONCEPT_ID",
                        "SCOPE_TO_SCOPE_IDENTITY_RENAMES_SOURCE_KEY_SCOPE_TO_OUTPUT_KEY_SCOPE_IDENTITY",
                        "SCOPE_IDENTITY_EXACT_KEYS_SCOPE_ID_HISTORICAL_CASE_IDS_TIME_BOUNDS_GEOGRAPHIES_INSTITUTIONS_ACTORS_MECHANISMS",
                        "SCOPE_SET_ARRAYS_SORT_LEXICOGRAPHICALLY",
                    ],
                ),
                material("association_semantic", "DIRECT_FIELD_OBJECT", association_semantic_fields),
                material(
                    "association_revision",
                    "ASSOCIATION_REVISION",
                    ["association_id", "@association_semantic"],
                    mappings=[
                        {"output_key": "association_id", "source_pointer": "/association_id", "operation": "COPY", "item_field": None},
                        {"output_key": "@merge", "source_pointer": "@association_semantic", "operation": "MERGE_OBJECT", "item_field": None},
                    ],
                    wrapper="MERGE_ASSOCIATION_ID_WITH_SEMANTIC",
                ),
                material("association_presentation", "DIRECT_FIELD_VALUE", ["presentation"]),
            ],
            "identifiers": [
                identifier("association_id", "association:v3:", "association_identity", 24),
                identifier("association_revision_id", "association-revision:v3:", "association_revision", 24),
            ],
            "hash_fields": [
                hash_field("identity_material_sha256", "association_identity"),
                hash_field("semantic_sha256", "association_semantic"),
                hash_field("presentation_sha256", "association_presentation"),
            ],
        },
        {
            "object_type": "PARTICIPANT_INCIDENCE",
            "collection_pointer": "/associations/*/participants/*",
            "materials": [
                material(
                    "incidence_identifier",
                    "INCIDENCE_IDENTIFIER",
                    ["@parent.identity_material_sha256", "@canonical_participant_position"],
                    rules=["USE_FIRST_16_HEX_OF_PARENT_IDENTITY_HASH", "APPEND_ONE_BASED_CANONICAL_POSITION_PADDED_TO_TWO_DIGITS"],
                )
            ],
            "identifiers": [
                identifier("incidence_id", "incidence:", "incidence_identifier", 16, "ONE_BASED_CANONICAL_PARTICIPANT_POSITION_PAD2")
            ],
            "hash_fields": [],
        },
        {
            "object_type": "ASSOCIATION_REALIZATION",
            "collection_pointer": "/compositions/*/association_realizations/*",
            "materials": [
                material(
                    "realization_semantic",
                    "REALIZATION_SEMANTIC_ALIASES",
                    ["association_revision_id", "realized_incidence_ids", "realization_kind"],
                    mappings=[
                        {"output_key": "association_revision_id", "source_pointer": "/association_revision_id", "operation": "COPY", "item_field": None},
                        {"output_key": "incidence_ids", "source_pointer": "/realized_incidence_ids", "operation": "COPY", "item_field": None},
                        {"output_key": "realization_kind", "source_pointer": "/realization_kind", "operation": "COPY", "item_field": None},
                    ],
                ),
                material("realization_presentation", "DIRECT_FIELD_VALUE", ["presentation"]),
            ],
            "identifiers": [identifier("association_realization_id", "realization:v3:", "realization_semantic", 24)],
            "hash_fields": [
                hash_field("semantic_sha256", "realization_semantic"),
                hash_field("presentation_sha256", "realization_presentation"),
            ],
        },
        {
            "object_type": "COMPOSITION_REVISION",
            "collection_pointer": "/compositions/*",
            "materials": [
                material(
                    "composition_identity",
                    "COMPOSITION_IDENTITY_ALIASES",
                    ["association_realizations", "composition_node_ids", "topology_family"],
                    mappings=[
                        {"output_key": "association_realization_ids", "source_pointer": "/association_realizations", "operation": "MAP_ARRAY_FIELD", "item_field": "association_realization_id"},
                        {"output_key": "node_ids", "source_pointer": "/composition_node_ids", "operation": "COPY", "item_field": None},
                        {"output_key": "topology_family", "source_pointer": "/topology_family", "operation": "COPY", "item_field": None},
                    ],
                ),
                material(
                    "composition_semantic", "DIRECT_FIELD_OBJECT",
                    ["realm", "association_realizations", "composition_node_ids", "topology_family", "renderability", "global_coherence_review_id", "association_trace_complete", "product_eligible", "product_path", "product_eligibility_disposition", "product_ineligibility_reason"],
                ),
                material(
                    "composition_revision", "COMPOSITION_REVISION", ["@composition_semantic", "revision=1"],
                    wrapper="OBJECT_WITH_SEMANTIC_AND_REVISION_ONE",
                ),
                material("composition_presentation", "DIRECT_FIELD_VALUE", ["presentation"]),
            ],
            "identifiers": [
                identifier("composition_id", "composition:v3:", "composition_identity", 24),
                identifier("composition_revision_id", "composition-revision:v3:", "composition_revision", 24),
            ],
            "hash_fields": [
                hash_field("semantic_sha256", "composition_semantic"),
                hash_field("presentation_sha256", "composition_presentation"),
            ],
        },
    ]
    direct_bindings = [
        ("NAVIGATION_STATE", "/navigation_states/*", "state_id", "state:v3:", ["realm", "composition_revision_id", "nodes", "path", "focus_navigation_node_id", "bipartite_alternation_valid"], "presentation"),
        ("TRANSITION", "/transitions/*", "transition_id", "transition:v3:", ["realm", "from_state_id", "to_state_id", "transition_kind", "incidence_id", "association_revision_id", "association_realization_id", "state_mutated"], None),
        ("WORKFLOW", "/workflows/*", "workflow_id", "workflow:v3:", ["realm", "initial_state_id", "transition_kind", "association_revision_ids", "association_realization_ids", "state_ids", "transition_ids", "reachable"], None),
        ("EXPORT", "/exports/*", "export_id", "export:v3:", ["realm", "workflow_id", "state_id", "association_revision_ids", "association_realization_ids", "projection_preservation_records", "composition_revision_id", "pair_projection_policy_preserved"], "presentation"),
        ("V2_PAIR_ADAPTER_RECEIPT", "/v2_pair_adapter_receipts/*", "adapter_id", "adapter:v3:", ["direction", "source_contract", "target_contract", "source_pair_id", "source_pair_fixture_sha256", "source_endpoint_ids", "target_association_revision_id", "target_incidence_ids", "endpoint_crosswalk", "input_arity", "output_association_kind", "higher_order_input_allowed", "reverse_conversion_allowed", "semantic_claims_added"], None),
    ]
    for object_type, pointer, id_field, prefix, semantic_fields, presentation_field in direct_bindings:
        semantic_name = f"{object_type.lower()}_semantic"
        materials = [material(semantic_name, "DIRECT_FIELD_OBJECT", semantic_fields)]
        hashes = [hash_field("semantic_sha256", semantic_name)]
        if presentation_field:
            presentation_name = f"{object_type.lower()}_presentation"
            materials.append(material(presentation_name, "DIRECT_FIELD_VALUE", [presentation_field]))
            hashes.append(hash_field("presentation_sha256", presentation_name))
        bindings.append(
            {
                "object_type": object_type,
                "collection_pointer": pointer,
                "materials": materials,
                "identifiers": [identifier(id_field, prefix, semantic_name, 24)],
                "hash_fields": hashes,
            }
        )
    governed_record_bindings = [
        (
            "VOCABULARY_CONCEPT", "/concepts/*", "concept_id", "concept:",
            ["realm", "canonical_label", "semantic_version", "lifecycle_state", "association_eligible", "authority", "product_eligible", "product_path", "product_eligibility_disposition", "product_ineligibility_reason"],
            None,
        ),
        (
            "CONCEPT_SENSE", "/concept_senses/*", "sense_id", "sense:",
            ["concept_id", "realm", "bounded_definition", "vocabulary_crosswalk_ids", "governed_scope_ids", "semantic_version", "lifecycle_state", "association_eligible", "authority", "product_eligible", "product_path", "product_eligibility_disposition", "product_ineligibility_reason"],
            None,
        ),
        (
            "COMPOSITION_COHERENCE_REVIEW", "/composition_coherence_reviews/*",
            "composition_coherence_review_id", "composition-review:v3:",
            ["composition_id", "realm", "review_state", "authority", "review_version", "global_coherence", "bounded_senses_compatible", "case_scope_compatible", "roles_and_topology_supported", "same_configuration", "unsupported_bridge_count", "association_revision_ids", "association_realization_ids", "incidence_ids", "decision", "reasons"],
            "DIGEST",
        ),
    ]
    for object_type, pointer, id_field, prefix, semantic_fields, identifier_mode in governed_record_bindings:
        semantic_name = f"{object_type.lower()}_semantic"
        bindings.append(
            {
                "object_type": object_type,
                "collection_pointer": pointer,
                "materials": [material(semantic_name, "DIRECT_FIELD_OBJECT", semantic_fields)],
                "identifiers": [
                    identifier(
                        id_field,
                        prefix,
                        semantic_name if identifier_mode == "DIGEST" else None,
                        24 if identifier_mode == "DIGEST" else 0,
                    )
                ],
                "hash_fields": [hash_field("semantic_sha256", semantic_name)],
            }
        )
    bindings.append(
        {
            "object_type": "V2_PAIR_SOURCE_FIXTURE",
            "collection_pointer": "/v2_pair_source_fixtures/*",
            "materials": [material("v2_pair_source_semantic", "DIRECT_FIELD_OBJECT", ["source_pair_id", "endpoints"])],
            "identifiers": [identifier("source_pair_id", "synthetic-v2-pair:", None, 0)],
            "hash_fields": [hash_field("source_pair_fixture_sha256", "v2_pair_source_semantic")],
        }
    )
    return {
        "contract_version": "trace-exploration-v3-hash-binding-contract-1.0.0",
        "canonicalization": {
            "digest_algorithm": "SHA-256",
            "text_encoding": "UTF-8",
            "json_ensure_ascii": False,
            "object_key_order": "LEXICOGRAPHIC_ASCENDING",
            "item_separators": [",", ":"],
            "trailing_newline_in_digest_material": False,
            "array_order_default": "PRESERVE_STORED_ORDER",
            "digest_representation": "LOWERCASE_HEX_64",
        },
        "bindings": bindings,
    }


def association_identity_material(
    kind: str,
    participant_specs: list[tuple[str, str, int | None, str | None]],
    scope: dict[str, Any],
    order_semantics: str,
    roles_meaningful: bool,
) -> dict[str, Any]:
    canonical_specs = canonical_participant_specs(
        participant_specs, order_semantics, roles_meaningful
    )
    normalized = [
        {
            "concept_id": concept,
            "sense_id": sense,
            "ordinal": ordinal,
            "role_id": role,
        }
        for concept, sense, ordinal, role in canonical_specs
    ]
    return {
        "association_kind": kind,
        "participants": normalized,
        "scope_identity": project_scope_identity(scope),
        "order_semantics": order_semantics,
        "roles_meaningful": roles_meaningful,
    }


def make_association(
    label: str,
    participant_count: int | None = None,
    *,
    kind: str = "HIGHER_ORDER",
    participant_specs: list[tuple[str, str, int | None, str | None]] | None = None,
    governed_scope: dict[str, Any] | None = None,
    order_semantics: str = "UNORDERED",
    roles_meaningful: bool = False,
    review_state: str = "FINAL",
    disposition: str | None = None,
    coherence: str = "PASS",
    senses_compatible: bool = True,
    cases_compatible: bool = True,
    roles_supported: bool = True,
    unsupported_bridges: int = 0,
    authority_state: str = "FINAL",
    support_mode: str | None = None,
    evidence_complete: bool = True,
    rights: bool = True,
    lifecycle: str = "ACTIVE",
    requested_active: bool | None = None,
    case_ids: list[str] | None = None,
) -> dict[str, Any]:
    if disposition is None:
        disposition = "DIRECT_PAIRWISE_SUPPORT" if kind == "PAIR" else "DIRECT_HIGHER_ORDER_SUPPORT"
    if support_mode is None:
        support_mode = "DIRECT_PAIR" if kind == "PAIR" else "DIRECT_GROUP"
    scope = copy.deepcopy(
        governed_scope
        if governed_scope is not None
        else make_scope(f"scope:{label.lower()}", case_ids or [f"case:{label.lower()}"])
    )
    for key in SCOPE_SET_ARRAY_KEYS:
        scope[key] = sorted(scope[key])
    if participant_specs is None:
        if participant_count is None:
            raise ValueError("participant_count or participant_specs is required")
        participant_specs = [
            (
                f"concept:{label.lower()}:{index + 1}",
                f"sense:{label.lower()}:{index + 1}",
                index if order_semantics == "ORDERED" else None,
                f"role:{index + 1}" if roles_meaningful else None,
            )
            for index in range(participant_count)
        ]
    participant_specs = canonical_participant_specs(
        participant_specs, order_semantics, roles_meaningful
    )
    participant_count = len(participant_specs)
    identity_material = association_identity_material(
        kind, participant_specs, scope, order_semantics, roles_meaningful
    )
    identity_hash = digest(identity_material)
    association_id = f"association:v3:{identity_hash[:24]}"
    incidences = [
        {
            "incidence_id": f"incidence:{identity_hash[:16]}:{index + 1:02d}",
            "concept_id": concept,
            "sense_id": sense,
            "ordinal": ordinal,
            "role_id": role,
            "participant_scope_id": scope["scope_id"],
            "qualifications": ["Synthetic exact bounded sense."],
        }
        for index, (concept, sense, ordinal, role) in enumerate(participant_specs)
    ]
    review = {
        "review_id": f"review:{label.lower()}:v1",
        "review_state": review_state,
        "disposition": disposition,
        "global_coherence": coherence,
        "bounded_senses_compatible": senses_compatible,
        "case_scope_compatible": cases_compatible,
        "roles_and_topology_supported": roles_supported,
        "unsupported_bridge_count": unsupported_bridges,
        "review_authority": "SYNTHETIC_TEST_AUTHORITY",
        "authority_state": authority_state,
        "review_version": "1",
        "qualifications": ["Synthetic control result; never production evidence."],
        "explicit_non_claims": [
            "Does not assert causation, direction, chronology, hierarchy, influence, or similarity.",
            "Does not authorize a production research claim.",
        ],
    }
    evidence = {
        "evidence_item_ids": [f"synthetic-evidence:{label.lower()}:group"],
        "locator_ids": [f"synthetic-locator:{label.lower()}:1"],
        "support_mode": support_mode,
        "same_configuration": cases_compatible,
        "synthesis_steps": (
            [] if support_mode in {"DIRECT_PAIR", "DIRECT_GROUP"} else ["Synthetic bounded bundle step."]
        ),
        "negative_or_conflicting_evidence": [] if coherence == "PASS" else ["Synthetic conflict marker."],
        "conflicts_resolved": coherence == "PASS",
        "conflict_resolution_ids": [],
        "rights_cleared_for_governed_use": rights,
        "evidence_complete": evidence_complete,
    }
    uncertainty = {
        "status": "RESOLVED_BOUNDED" if lifecycle == "ACTIVE" else ("UNKNOWN" if review_state == "PENDING" else "UNRESOLVED"),
        "level": "LOW" if lifecycle == "ACTIVE" else ("UNKNOWN" if review_state == "PENDING" else "HIGH"),
        "rationale": (
            "Synthetic expected result is bounded and fully specified."
            if lifecycle == "ACTIVE"
            else "Synthetic negative or pending control remains deliberately non-active."
        ),
        "basis": ["Synthetic control construction and expected-result oracle."],
        "unresolved_questions": [] if lifecycle == "ACTIVE" else ["What governed evidence would resolve this control state?"],
        "reviewed_in_review_id": review["review_id"],
        "activation_policy": "ALLOWED_BOUNDED" if lifecycle == "ACTIVE" else "BLOCKS_ACTIVATION",
    }
    product_disposition = "NOT_APPLICABLE_SYNTHETIC"
    product_reason = "Synthetic-control activation is never product eligibility."
    requested_active = lifecycle == "ACTIVE" if requested_active is None else requested_active
    provisional = {
        "association_kind": kind,
        "realm": "SYNTHETIC_CONTROL",
        "evidence": evidence,
        "review": review,
        "uncertainty": uncertainty,
        "product_eligible": False,
        "product_path": None,
        "product_eligibility_disposition": product_disposition,
        "product_ineligibility_reason": product_reason,
    }
    activation = derive_activation(provisional, requested_active)
    semantic_material = {
        "association_kind": kind,
        "realm": "SYNTHETIC_CONTROL",
        "semantic_version": "1",
        "arity": participant_count,
        "order_semantics": order_semantics,
        "roles_meaningful": roles_meaningful,
        "identity_material_sha256": identity_hash,
        "scope": scope,
        "participants": incidences,
        "evidence": evidence,
        "review": review,
        "activation": activation,
        "uncertainty": uncertainty,
        "lifecycle_state": lifecycle,
        "pair_projection_policy": "NOT_APPLICABLE" if kind == "PAIR" else "NONE",
        "internal_pair_association_ids": [],
        "internal_pair_links": [],
        "product_eligible": False,
        "product_path": None,
        "product_eligibility_disposition": product_disposition,
        "product_ineligibility_reason": product_reason,
    }
    revision_hash = digest({"association_id": association_id, **semantic_material})
    presentation = {
        "realization_hint": "PAIR_EDGE" if kind == "PAIR" else "HYPEREDGE_HUB",
        "theme": "synthetic-neutral",
    }
    return {
        "association_id": association_id,
        "association_revision_id": f"association-revision:v3:{revision_hash[:24]}",
        "association_kind": kind,
        "realm": "SYNTHETIC_CONTROL",
        "semantic_version": "1",
        "arity": participant_count,
        "order_semantics": order_semantics,
        "roles_meaningful": roles_meaningful,
        "scope": scope,
        "participants": incidences,
        "evidence": evidence,
        "review": review,
        "activation": activation,
        "uncertainty": uncertainty,
        "lifecycle_state": lifecycle,
        "pair_projection_policy": "NOT_APPLICABLE" if kind == "PAIR" else "NONE",
        "internal_pair_association_ids": [],
        "internal_pair_links": [],
        "product_eligible": False,
        "product_path": None,
        "product_eligibility_disposition": product_disposition,
        "product_ineligibility_reason": product_reason,
        "identity_material_sha256": identity_hash,
        "semantic_sha256": digest(semantic_material),
        "presentation": presentation,
        "presentation_sha256": digest(presentation),
    }


def product_disposition_valid(row: dict[str, Any]) -> bool:
    if row["product_eligible"]:
        return (
            row["realm"] == "PRODUCTION"
            and isinstance(row["product_path"], str)
            and bool(row["product_path"])
            and row["product_eligibility_disposition"] == "ELIGIBLE"
            and row["product_ineligibility_reason"] is None
        )
    return (
        row["product_path"] is None
        and row["product_eligibility_disposition"]
        in {"INELIGIBLE", "DEFERRED", "NOT_APPLICABLE_SYNTHETIC"}
        and isinstance(row["product_ineligibility_reason"], str)
        and bool(row["product_ineligibility_reason"])
        and (
            row["realm"] != "SYNTHETIC_CONTROL"
            or row["product_eligibility_disposition"] == "NOT_APPLICABLE_SYNTHETIC"
        )
    )


def derive_activation(row: dict[str, Any], requested_active: bool) -> dict[str, Any]:
    evidence = row["evidence"]
    review = row["review"]
    uncertainty = row["uncertainty"]
    support_mode = evidence["support_mode"]
    synthesis_gate = (
        (support_mode in {"DIRECT_PAIR", "DIRECT_GROUP"} and not evidence["synthesis_steps"])
        or (
            support_mode in {"COHERENT_COMPOSITE", "MIXED"}
            and bool(evidence["synthesis_steps"])
        )
    )
    conflicts_cleared = not evidence["negative_or_conflicting_evidence"] or (
        evidence["conflicts_resolved"] and bool(evidence["conflict_resolution_ids"])
    )
    expected_disposition = {
        ("PAIR", "DIRECT_PAIR"): "DIRECT_PAIRWISE_SUPPORT",
        ("HIGHER_ORDER", "DIRECT_GROUP"): "DIRECT_HIGHER_ORDER_SUPPORT",
        ("HIGHER_ORDER", "COHERENT_COMPOSITE"): "COHERENT_COMPOSITE_SUPPORT",
        ("HIGHER_ORDER", "MIXED"): "MIXED_DIRECT_AND_COMPOSITE_SUPPORT",
    }.get((row["association_kind"], support_mode))
    supporting_disposition = review["disposition"] == expected_disposition
    gate_values = {
        "evidence_gate": (
            evidence["evidence_complete"]
            and bool(evidence["evidence_item_ids"])
            and bool(evidence["locator_ids"])
            and support_mode in {"DIRECT_PAIR", "DIRECT_GROUP", "COHERENT_COMPOSITE", "MIXED"}
        ),
        "final_review_gate": review["review_state"] == "FINAL" and supporting_disposition,
        "authority_gate": (
            review["authority_state"] == "FINAL"
            and not (
                row["realm"] == "PRODUCTION"
                and review["review_authority"] == "SYNTHETIC_TEST_AUTHORITY"
            )
        ),
        "coherence_gate": review["global_coherence"] == "PASS",
        "rights_gate": evidence["rights_cleared_for_governed_use"],
        "conflict_gate": conflicts_cleared,
        "bounded_scope_gate": (
            evidence["same_configuration"]
            and review["bounded_senses_compatible"]
            and review["case_scope_compatible"]
            and review["roles_and_topology_supported"]
            and review["unsupported_bridge_count"] == 0
        ),
        "synthesis_gate": synthesis_gate,
        "product_policy_gate": product_disposition_valid(row),
    }
    all_gates_pass = all(gate_values.values()) and (
        uncertainty["status"] == "RESOLVED_BOUNDED"
        and uncertainty["activation_policy"] == "ALLOWED_BOUNDED"
        and uncertainty["reviewed_in_review_id"] == review["review_id"]
    )
    decision = "ALLOW" if requested_active and all_gates_pass else (
        "REJECT" if requested_active else "NOT_REQUESTED"
    )
    failed = [name for name, passed in gate_values.items() if not passed]
    if uncertainty["status"] != "RESOLVED_BOUNDED" or uncertainty["activation_policy"] != "ALLOWED_BOUNDED":
        failed.append("uncertainty_gate")
    return {
        "requested_state": "ACTIVE" if requested_active else "INACTIVE",
        "decision": decision,
        "all_gates_pass": all_gates_pass,
        **gate_values,
        "reasons": (
            ["Synthetic-control activation only; production and product use remain forbidden."]
            if decision == "ALLOW"
            else [f"Fail-closed gate: {name}." for name in sorted(failed)]
            or ["Activation was not requested."]
        ),
    }


def refresh_association_hashes(row: dict[str, Any]) -> None:
    semantic = association_semantic_material_from_record(row)
    row["semantic_sha256"] = digest(semantic)
    row["association_revision_id"] = (
        f"association-revision:v3:{digest({'association_id': row['association_id'], **semantic})[:24]}"
    )


def attach_governed_internal_pairs(
    group: dict[str, Any], pair_indices: list[tuple[int, int]], label: str
) -> list[dict[str, Any]]:
    pairs: list[dict[str, Any]] = []
    links: list[dict[str, Any]] = []
    for left, right in sorted(pair_indices):
        group_endpoints = [group["participants"][left - 1], group["participants"][right - 1]]
        pair = make_association(
            f"{label}-PAIR-{left}-{right}",
            kind="PAIR",
            participant_specs=[
                (item["concept_id"], item["sense_id"], None, None)
                for item in group_endpoints
            ],
            governed_scope=group["scope"],
        )
        pair_by_sense = {item["sense_id"]: item for item in pair["participants"]}
        ordered_group_endpoints = sorted(group_endpoints, key=lambda item: item["sense_id"])
        links.append(
            {
                "pair_association_id": pair["association_id"],
                "pair_association_revision_id": pair["association_revision_id"],
                "participant_incidence_ids": [
                    item["incidence_id"] for item in ordered_group_endpoints
                ],
                "pair_participant_incidence_ids": [
                    pair_by_sense[item["sense_id"]]["incidence_id"]
                    for item in ordered_group_endpoints
                ],
                "endpoint_sense_ids": [item["sense_id"] for item in ordered_group_endpoints],
            }
        )
        pairs.append(pair)
    group["internal_pair_links"] = sorted(links, key=lambda row: row["pair_association_id"])
    group["internal_pair_association_ids"] = [
        row["pair_association_id"] for row in group["internal_pair_links"]
    ]
    refresh_association_hashes(group)
    return pairs


def build_vocabulary_records(
    associations: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    concept_scopes: dict[str, set[str]] = {}
    sense_data: dict[str, dict[str, Any]] = {}
    concept_active: set[str] = set()
    sense_active: set[str] = set()
    for association in associations:
        for participant in association["participants"]:
            concept_id = participant["concept_id"]
            sense_id = participant["sense_id"]
            concept_scopes.setdefault(concept_id, set()).add(association["scope"]["scope_id"])
            sense_data.setdefault(
                sense_id,
                {"concept_id": concept_id, "scope_ids": set()},
            )["scope_ids"].add(association["scope"]["scope_id"])
            if association["lifecycle_state"] == "ACTIVE":
                concept_active.add(concept_id)
                sense_active.add(sense_id)
    authority = {
        "authority_id": "authority:synthetic-v3-controls",
        "authority_kind": "SYNTHETIC_TEST_AUTHORITY",
        "authority_state": "FINAL",
        "authority_version": "1",
    }
    concepts: list[dict[str, Any]] = []
    for concept_id in sorted(concept_scopes):
        active = concept_id in concept_active
        semantic = {
            "realm": "SYNTHETIC_CONTROL",
            "canonical_label": concept_id.removeprefix("concept:").replace(":", " "),
            "semantic_version": "1",
            "lifecycle_state": "ACTIVE" if active else "INQUIRY_ONLY",
            "association_eligible": active,
            "authority": authority,
            "product_eligible": False,
            "product_path": None,
            "product_eligibility_disposition": "NOT_APPLICABLE_SYNTHETIC",
            "product_ineligibility_reason": "Synthetic vocabulary never authorizes product use.",
        }
        concepts.append({"concept_id": concept_id, **semantic, "semantic_sha256": digest(semantic)})
    senses: list[dict[str, Any]] = []
    for sense_id in sorted(sense_data):
        active = sense_id in sense_active
        data = sense_data[sense_id]
        semantic = {
            "concept_id": data["concept_id"],
            "realm": "SYNTHETIC_CONTROL",
            "bounded_definition": f"Synthetic bounded definition for {sense_id}.",
            "vocabulary_crosswalk_ids": [f"crosswalk:synthetic:{digest(sense_id)[:16]}"],
            "governed_scope_ids": sorted(data["scope_ids"]),
            "semantic_version": "1",
            "lifecycle_state": "ACTIVE" if active else "INQUIRY_ONLY",
            "association_eligible": active,
            "authority": authority,
            "product_eligible": False,
            "product_path": None,
            "product_eligibility_disposition": "NOT_APPLICABLE_SYNTHETIC",
            "product_ineligibility_reason": "Synthetic bounded sense never authorizes product use.",
        }
        senses.append({"sense_id": sense_id, **semantic, "semantic_sha256": digest(semantic)})
    return concepts, senses


def incidence_ids_for_identity(material: dict[str, Any]) -> list[str]:
    identity_hash = digest(material)
    return [
        f"incidence:{identity_hash[:16]}:{index + 1:02d}"
        for index in range(len(material["participants"]))
    ]


def build_identity_branch_test_receipts(scope: dict[str, Any]) -> list[dict[str, Any]]:
    unordered = [
        ("concept:test:u:1", "sense:test:u:1", None, None),
        ("concept:test:u:2", "sense:test:u:2", None, None),
        ("concept:test:u:3", "sense:test:u:3", None, None),
    ]
    ordered = [
        ("concept:test:o:1", "sense:test:o:1", 0, None),
        ("concept:test:o:2", "sense:test:o:2", 1, None),
        ("concept:test:o:3", "sense:test:o:3", 2, None),
    ]
    ordered_reversed = [
        (concept_id, sense_id, index, role_id)
        for index, (concept_id, sense_id, _ordinal, role_id) in enumerate(reversed(ordered))
    ]
    roles = [
        ("concept:test:r:1", "sense:test:r:1", None, "role:alpha"),
        ("concept:test:r:2", "sense:test:r:2", None, "role:beta"),
        ("concept:test:r:3", "sense:test:r:3", None, "role:gamma"),
    ]
    tests = [
        ("ID-BRANCH-001", "UNORDERED_PERMUTATION_INVARIANT", unordered, list(reversed(unordered)), "UNORDERED", False, "EQUAL"),
        ("ID-BRANCH-002", "ORDERED_CONTIGUOUS_ORDINAL_SENSITIVE", ordered, ordered_reversed, "ORDERED", False, "NOT_EQUAL"),
        ("ID-BRANCH-003", "UNORDERED_MEANINGFUL_ROLE_PERMUTATION_INVARIANT", roles, [roles[2], roles[0], roles[1]], "UNORDERED", True, "EQUAL"),
        ("ID-BRANCH-004", "UNORDERED_MEANINGFUL_ROLE_REASSIGNMENT_SENSITIVE", roles, [(roles[0][0], roles[0][1], None, "role:beta"), (roles[1][0], roles[1][1], None, "role:alpha"), roles[2]], "UNORDERED", True, "NOT_EQUAL"),
    ]
    receipts = []
    for test_id, branch, base_specs, comparison_specs, order, meaningful, expected in tests:
        base = association_identity_material("HIGHER_ORDER", base_specs, scope, order, meaningful)
        comparison = association_identity_material(
            "HIGHER_ORDER", comparison_specs, scope, order, meaningful
        )
        observed = "EQUAL" if digest(base) == digest(comparison) else "NOT_EQUAL"
        if observed != expected:
            raise ValueError(f"identity branch oracle failed: {test_id}")
        receipts.append(
            {
                "test_id": test_id,
                "branch": branch,
                "base_identity_sha256": digest(base),
                "comparison_identity_sha256": digest(comparison),
                "base_identity_material": base,
                "comparison_identity_material": comparison,
                "expected_relation": expected,
                "observed_relation": observed,
                "base_canonical_incidence_ids": incidence_ids_for_identity(base),
                "comparison_canonical_incidence_ids": incidence_ids_for_identity(comparison),
                "status": "PASS",
            }
        )
    return receipts


def make_realization(association: dict[str, Any]) -> dict[str, Any]:
    semantic = {
        "association_revision_id": association["association_revision_id"],
        "incidence_ids": [row["incidence_id"] for row in association["participants"]],
        "realization_kind": "PAIR_EDGE" if association["association_kind"] == "PAIR" else "HYPEREDGE_HUB",
    }
    presentation = {"layout": "SYNTHETIC_RADIAL", "style": "NEUTRAL_CONTROL"}
    return {
        "association_realization_id": f"realization:v3:{digest(semantic)[:24]}",
        "association_revision_id": association["association_revision_id"],
        "realization_kind": semantic["realization_kind"],
        "realized_incidence_ids": semantic["incidence_ids"],
        "semantic_sha256": digest(semantic),
        "presentation": presentation,
        "presentation_sha256": digest(presentation),
    }


def make_composition(
    label: str,
    traced_associations: list[dict[str, Any]],
    *,
    topology_family: str,
    coherent: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    realizations = sorted(
        [make_realization(row) for row in traced_associations],
        key=lambda row: row["association_realization_id"],
    )
    node_ids = sorted(
        {
            participant["concept_id"]
            for association in traced_associations
            for participant in association["participants"]
        }
    )
    identity = {
        "association_realization_ids": [
            row["association_realization_id"] for row in realizations
        ],
        "node_ids": node_ids,
        "topology_family": topology_family,
    }
    composition_id = f"composition:v3:{digest(identity)[:24]}"
    review_semantic = {
        "composition_id": composition_id,
        "realm": "SYNTHETIC_CONTROL",
        "review_state": "FINAL",
        "authority": {
            "authority_id": "authority:synthetic-v3-controls",
            "authority_kind": "SYNTHETIC_TEST_AUTHORITY",
            "authority_state": "FINAL",
            "authority_version": "1",
        },
        "review_version": "1",
        "global_coherence": "PASS" if coherent else "FAIL",
        "bounded_senses_compatible": coherent,
        "case_scope_compatible": coherent,
        "roles_and_topology_supported": coherent,
        "same_configuration": coherent,
        "unsupported_bridge_count": 0 if coherent else 1,
        "association_revision_ids": sorted(
            row["association_revision_id"] for row in traced_associations
        ),
        "association_realization_ids": [
            row["association_realization_id"] for row in realizations
        ],
        "incidence_ids": sorted(
            {
                incidence_id
                for realization in realizations
                for incidence_id in realization["realized_incidence_ids"]
            }
        ),
        "decision": "COHERENT" if coherent else "INCOHERENT",
        "reasons": [
            "Synthetic composition coherence passes every global fact."
            if coherent
            else "All pair associations are active, but the synthetic group fails global coherence."
        ],
    }
    coherence_review = {
        "composition_coherence_review_id": (
            f"composition-review:v3:{digest(review_semantic)[:24]}"
        ),
        **review_semantic,
        "semantic_sha256": digest(review_semantic),
    }
    semantic = {
        "realm": "SYNTHETIC_CONTROL",
        "association_realizations": realizations,
        "composition_node_ids": node_ids,
        "topology_family": topology_family,
        "renderability": "PASS",
        "global_coherence_review_id": coherence_review[
            "composition_coherence_review_id"
        ],
        "association_trace_complete": True,
        "product_eligible": False,
        "product_path": None,
        "product_eligibility_disposition": "NOT_APPLICABLE_SYNTHETIC",
        "product_ineligibility_reason": (
            "Synthetic composition is never product eligible."
            if coherent
            else "Global composition coherence failed."
        ),
    }
    presentation = {"layout": topology_family, "seed": label}
    composition = {
        "composition_id": composition_id,
        "composition_revision_id": (
            f"composition-revision:v3:{digest({'semantic': semantic, 'revision': 1})[:24]}"
        ),
        **semantic,
        "semantic_sha256": digest(semantic),
        "presentation": presentation,
        "presentation_sha256": digest(presentation),
    }
    return composition, coherence_review


def build_fixture() -> dict[str, Any]:
    hash_binding_contract = build_hash_binding_contract()
    sparse_pair_indices = [(1, 2), (4, 5)]
    clique_pair_indices = [(a, b) for a in range(1, 5) for b in range(a + 1, 5)]
    sparse = make_association("SPARSE-VALID-FIVE", 5)
    sparse_pairs = attach_governed_internal_pairs(
        sparse, sparse_pair_indices, "SPARSE-VALID-FIVE"
    )
    clique = make_association(
        "INVALID-FULL-CLIQUE",
        4,
        disposition="PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE",
        coherence="FAIL",
        unsupported_bridges=1,
        support_mode="PAIR_ONLY",
        lifecycle="INACTIVE",
    )
    clique_pairs = attach_governed_internal_pairs(
        clique, clique_pair_indices, "INVALID-FULL-CLIQUE"
    )
    sense_conflict = make_association(
        "BOUNDED-SENSE-CONFLICT",
        3,
        disposition="BOUNDED_SENSE_OR_SCOPE_CONFLICT",
        coherence="FAIL",
        senses_compatible=False,
        support_mode="NONE",
        lifecycle="INACTIVE",
    )
    cross_case = make_association(
        "CROSS-CASE-BUNDLE",
        4,
        disposition="BOUNDED_SENSE_OR_SCOPE_CONFLICT",
        coherence="FAIL",
        cases_compatible=False,
        unsupported_bridges=2,
        support_mode="COHERENT_COMPOSITE",
        lifecycle="INACTIVE",
        case_ids=["case:cross-case:a", "case:cross-case:b"],
    )
    pending = make_association(
        "PENDING-ACTIVE-ATTEMPT",
        3,
        review_state="PENDING",
        disposition="PENDING_GOVERNED_REVIEW",
        coherence="UNRESOLVED",
        authority_state="PENDING",
        support_mode="NONE",
        evidence_complete=False,
        lifecycle="INACTIVE",
        requested_active=True,
    )
    pair = make_association("V2-PAIR-ADAPTER", 2, kind="PAIR")
    associations = [
        sparse,
        clique,
        sense_conflict,
        cross_case,
        pending,
        pair,
        *sparse_pairs,
        *clique_pairs,
    ]
    associations = sorted(associations, key=lambda row: row["association_revision_id"])
    scopes_by_id = {
        row["scope"]["scope_id"]: copy.deepcopy(row["scope"]) for row in associations
    }
    scopes = [scopes_by_id[key] for key in sorted(scopes_by_id)]
    concepts, concept_senses = build_vocabulary_records(associations)

    sparse_composition, sparse_composition_review = make_composition(
        "SPARSE-VALID-FIVE",
        [sparse, *sparse_pairs],
        topology_family="HYPEREDGE_HUB_WITH_GOVERNED_PAIR_EDGES",
        coherent=True,
    )
    renderable_invalid, invalid_composition_review = make_composition(
        "INVALID-FULL-CLIQUE",
        [clique, *clique_pairs],
        topology_family="FULL_PAIR_CLIQUE_WITH_GROUP_HYPEREDGE",
        coherent=False,
    )
    composition_coherence_reviews = [
        sparse_composition_review,
        invalid_composition_review,
    ]
    sparse_realization = next(
        row
        for row in sparse_composition["association_realizations"]
        if row["association_revision_id"] == sparse["association_revision_id"]
    )

    concept_node = {
        "navigation_node_id": f"nav:concept:{sparse['participants'][0]['concept_id']}",
        "node_kind": "CONCEPT",
        "concept_id": sparse["participants"][0]["concept_id"],
        "association_revision_id": None,
    }
    association_node = {
        "navigation_node_id": f"nav:association:{sparse['association_revision_id']}",
        "node_kind": "ASSOCIATION",
        "concept_id": None,
        "association_revision_id": sparse["association_revision_id"],
    }
    destination_node = {
        "navigation_node_id": f"nav:concept:{sparse['participants'][4]['concept_id']}",
        "node_kind": "CONCEPT",
        "concept_id": sparse["participants"][4]["concept_id"],
        "association_revision_id": None,
    }
    nav_nodes = [concept_node, association_node, destination_node]
    nav_path = [
        {
            "from_navigation_node_id": concept_node["navigation_node_id"],
            "incidence_id": sparse["participants"][0]["incidence_id"],
            "to_navigation_node_id": association_node["navigation_node_id"],
        },
        {
            "from_navigation_node_id": association_node["navigation_node_id"],
            "incidence_id": sparse["participants"][4]["incidence_id"],
            "to_navigation_node_id": destination_node["navigation_node_id"],
        },
    ]
    nav_semantic = {
        "realm": "SYNTHETIC_CONTROL",
        "composition_revision_id": sparse_composition["composition_revision_id"],
        "nodes": nav_nodes,
        "path": nav_path,
        "focus_navigation_node_id": destination_node["navigation_node_id"],
        "bipartite_alternation_valid": True,
    }
    nav_presentation = {"focus_style": "SYNTHETIC_FOCUS", "viewport": "SYNTHETIC"}
    nav_state = {
        "state_id": f"state:v3:{digest(nav_semantic)[:24]}",
        **nav_semantic,
        "semantic_sha256": digest(nav_semantic),
        "presentation": nav_presentation,
        "presentation_sha256": digest(nav_presentation),
    }
    workflow_semantic = {
        "realm": "SYNTHETIC_CONTROL",
        "initial_state_id": nav_state["state_id"],
        "transition_kind": "FOLLOW_INCIDENCE",
        "association_revision_ids": sorted(
            row["association_revision_id"]
            for row in [sparse, *sparse_pairs]
        ),
        "association_realization_ids": sorted(
            row["association_realization_id"]
            for row in sparse_composition["association_realizations"]
        ),
        "state_ids": [nav_state["state_id"]],
        "transition_ids": [],
        "reachable": True,
    }
    workflow = {
        "workflow_id": f"workflow:v3:{digest(workflow_semantic)[:24]}",
        **workflow_semantic,
        "semantic_sha256": digest(workflow_semantic),
    }
    association_by_revision_for_export = {
        row["association_revision_id"]: row for row in associations
    }
    projection_preservation_records = sorted(
        [
            {
                "association_revision_id": realization["association_revision_id"],
                "association_realization_id": realization["association_realization_id"],
                "pair_projection_policy": association_by_revision_for_export[
                    realization["association_revision_id"]
                ]["pair_projection_policy"],
                "realization_kind": realization["realization_kind"],
            }
            for realization in sparse_composition["association_realizations"]
        ],
        key=lambda row: row["association_realization_id"],
    )
    export_semantic = {
        "realm": "SYNTHETIC_CONTROL",
        "workflow_id": workflow["workflow_id"],
        "state_id": nav_state["state_id"],
        "association_revision_ids": workflow["association_revision_ids"],
        "association_realization_ids": workflow["association_realization_ids"],
        "projection_preservation_records": projection_preservation_records,
        "composition_revision_id": sparse_composition["composition_revision_id"],
        "pair_projection_policy_preserved": all(
            (
                row["pair_projection_policy"] == "NOT_APPLICABLE"
                and row["realization_kind"] == "PAIR_EDGE"
            )
            or (
                row["pair_projection_policy"] == "NONE"
                and row["realization_kind"] != "PAIR_EDGE"
            )
            for row in projection_preservation_records
        ),
    }
    export_presentation = {"format": "TRACE_V3_SYNTHETIC_JSON", "theme": "NEUTRAL"}
    export = {
        "export_id": f"export:v3:{digest(export_semantic)[:24]}",
        **export_semantic,
        "semantic_sha256": digest(export_semantic),
        "presentation": export_presentation,
        "presentation_sha256": digest(export_presentation),
    }
    source_pair_core = {
        "source_pair_id": "synthetic-v2-pair:adapter-control",
        "endpoints": [
            {
                "source_endpoint_id": f"synthetic-v2-endpoint:{index + 1}",
                "concept_id": participant["concept_id"],
                "sense_id": participant["sense_id"],
            }
            for index, participant in enumerate(pair["participants"])
        ],
    }
    source_pair_fixture = {
        **source_pair_core,
        "source_pair_fixture_sha256": digest(source_pair_core),
    }
    adapter_semantic = {
        "direction": "V2_PAIR_TO_V3_PAIR_ONLY",
        "source_contract": "trace/exploration/v2",
        "target_contract": "trace/exploration/v3",
        "source_pair_id": source_pair_fixture["source_pair_id"],
        "source_pair_fixture_sha256": source_pair_fixture["source_pair_fixture_sha256"],
        "source_endpoint_ids": [row["source_endpoint_id"] for row in source_pair_fixture["endpoints"]],
        "target_association_revision_id": pair["association_revision_id"],
        "target_incidence_ids": [row["incidence_id"] for row in pair["participants"]],
        "endpoint_crosswalk": [
            {
                "source_endpoint_id": source["source_endpoint_id"],
                "target_incidence_id": target["incidence_id"],
                "target_concept_id": target["concept_id"],
                "target_sense_id": target["sense_id"],
            }
            for source, target in zip(source_pair_fixture["endpoints"], pair["participants"], strict=True)
        ],
        "input_arity": 2,
        "output_association_kind": "PAIR",
        "higher_order_input_allowed": False,
        "reverse_conversion_allowed": False,
        "semantic_claims_added": False,
    }
    adapter_receipt = {
        "adapter_id": f"adapter:v3:{digest(adapter_semantic)[:24]}",
        **adapter_semantic,
        "semantic_sha256": digest(adapter_semantic),
    }
    controls = [
        {
            "control_id": "CTRL-V3-001",
            "control_class": "VALID_SPARSE_DISCONNECTED_HIGHER_ORDER_GROUP",
            "object_refs": [
                sparse["association_revision_id"],
                *sorted(row["association_revision_id"] for row in sparse_pairs),
            ],
            "expected_result": "PASS",
            "assertions": ["arity=5", "internal_pair_count=2", "internal_pair_components=3", "all_internal_pairs=ACTIVE", "pair_projection_policy=NONE", "global_coherence=PASS"],
        },
        {
            "control_id": "CTRL-V3-002",
            "control_class": "INVALID_FULL_PAIR_CLIQUE",
            "object_refs": [
                clique["association_revision_id"],
                *sorted(row["association_revision_id"] for row in clique_pairs),
            ],
            "expected_result": "INACTIVE",
            "assertions": ["arity=4", "internal_pair_count=6", "all_six_pair_revisions=ACTIVE", "global_coherence=FAIL", "lifecycle_state=INACTIVE"],
        },
        {
            "control_id": "CTRL-V3-003",
            "control_class": "BOUNDED_SENSE_CONFLICT",
            "object_refs": [sense_conflict["association_revision_id"]],
            "expected_result": "REJECT",
            "assertions": ["bounded_senses_compatible=false", "global_coherence=FAIL"],
        },
        {
            "control_id": "CTRL-V3-004",
            "control_class": "CROSS_CASE_SOURCE_BUNDLE",
            "object_refs": [cross_case["association_revision_id"]],
            "expected_result": "REJECT",
            "assertions": ["case_scope_compatible=false", "historical_case_count=2", "unsupported_bridge_count=2"],
        },
        {
            "control_id": "CTRL-V3-005",
            "control_class": "ISOLATED_ACTIVE_TERM_IN_VALID_HYPEREDGE",
            "object_refs": [
                sparse["association_revision_id"],
                sparse["participants"][2]["concept_id"],
                sparse["participants"][2]["sense_id"],
            ],
            "expected_result": "PASS",
            "assertions": ["participant_has_internal_pair_degree=0", "concept_lifecycle_state=ACTIVE", "sense_lifecycle_state=ACTIVE", "association_lifecycle_state=ACTIVE", "realm=SYNTHETIC_CONTROL"],
        },
        {
            "control_id": "CTRL-V3-006",
            "control_class": "RENDERABLE_COMPOSITION_WITHOUT_VALID_GROUP",
            "object_refs": [renderable_invalid["composition_revision_id"], clique["association_revision_id"]],
            "expected_result": "REJECT",
            "assertions": ["renderability=PASS", "group_global_coherence=FAIL", "product_eligible=false"],
        },
        {
            "control_id": "CTRL-V3-007",
            "control_class": "ILLEGAL_HYPEREDGE_PAIR_PROJECTION",
            "object_refs": [sparse["association_revision_id"], "attempt:v3:illegal-projection"],
            "expected_result": "REJECT",
            "assertions": ["higher_order_projection_must_equal=NONE", "implicit_pair_creation_count=0"],
        },
        {
            "control_id": "CTRL-V3-008",
            "control_class": "ACTIVE_WITH_PENDING_OR_NONFINAL_REVIEW",
            "object_refs": [pending["association_revision_id"], "attempt:v3:pending-active"],
            "expected_result": "REJECT",
            "assertions": ["review_state=PENDING", "activation_decision=REJECT", "lifecycle_state=INACTIVE"],
        },
        {
            "control_id": "CTRL-V3-009",
            "control_class": "ACTIVE_ARITY_FIVE_PROJECTION_NONE",
            "object_refs": [sparse["association_revision_id"]],
            "expected_result": "PASS",
            "assertions": ["lifecycle_state=ACTIVE", "arity=5", "pair_projection_policy=NONE", "realm=SYNTHETIC_CONTROL"],
        },
        {
            "control_id": "CTRL-V3-010",
            "control_class": "ONE_WAY_V2_PAIR_ADAPTER",
            "object_refs": [adapter_receipt["adapter_id"], pair["association_revision_id"]],
            "expected_result": "PASS",
            "assertions": ["direction=V2_PAIR_TO_V3_PAIR_ONLY", "reverse_conversion_allowed=false", "higher_order_input_allowed=false"],
        },
    ]
    fixture = {
        "contract_version": CONTRACT_VERSION,
        "api_namespace": "trace/exploration/v3",
        "source_sha": SOURCE_SHA,
        "parent_checkpoint_sha": PARENT_CHECKPOINT_SHA,
        "hash_binding_contract": hash_binding_contract,
        "hash_binding_contract_canonical_sha256": digest(hash_binding_contract),
        "object_boundaries": {
            "association_is_evidence_bearing_semantic_object": True,
            "composition_is_governed_realization_object": True,
            "association_and_composition_counts_are_distinct": True,
            "implicit_pair_projection_forbidden": True,
            "navigation_model": "BIPARTITE_CONCEPT_ASSOCIATION_INCIDENCE",
        },
        "scopes": scopes,
        "concepts": concepts,
        "concept_senses": concept_senses,
        "associations": associations,
        "composition_coherence_reviews": composition_coherence_reviews,
        "compositions": [sparse_composition, renderable_invalid],
        "navigation_states": [nav_state],
        "transitions": [],
        "workflows": [workflow],
        "exports": [export],
        "v2_pair_source_fixtures": [source_pair_fixture],
        "v2_pair_adapter_receipts": [adapter_receipt],
        "invalid_attempts": [
            {
                "attempt_id": "attempt:v3:illegal-projection",
                "attempt_kind": "ILLEGAL_PAIR_PROJECTION",
                "association_revision_id": sparse["association_revision_id"],
                "requested_value": "PROJECT_COMPLETE_GRAPH",
                "expected_decision": "REJECT",
                "expected_error_code": "HIGHER_ORDER_PAIR_PROJECTION_FORBIDDEN",
            },
            {
                "attempt_id": "attempt:v3:pending-active",
                "attempt_kind": "ACTIVE_WITH_NONFINAL_REVIEW",
                "association_revision_id": pending["association_revision_id"],
                "requested_value": "ACTIVE",
                "expected_decision": "REJECT",
                "expected_error_code": "ACTIVE_REQUIRES_FINAL_GOVERNED_REVIEW",
            },
        ],
        "control_expectations": controls,
        "schema_negative_probe_receipts": [],
        "identity_branch_test_receipts": build_identity_branch_test_receipts(sparse["scope"]),
        "count_taxonomy": {},
        "closure_flags": {
            "pair_association_closure": False,
            "higher_order_association_closure": False,
            "global_composition_coherence_closure": False,
            "product_association_reachability_closure": False,
            "computational_space_closure": False,
            "function3_closure": False,
        },
    }
    production = [row for row in associations if row["realm"] == "PRODUCTION"]
    fixture["count_taxonomy"] = {
        "vocabulary": {
            "synthetic_scope_count": len(scopes),
            "synthetic_distinct_concept_count": len({p["concept_id"] for a in associations for p in a["participants"]}),
            "synthetic_concept_record_count": len(concepts),
            "synthetic_active_concept_count": sum(
                row["lifecycle_state"] == "ACTIVE" for row in concepts
            ),
            "synthetic_concept_sense_record_count": len(concept_senses),
            "synthetic_active_concept_sense_count": sum(
                row["lifecycle_state"] == "ACTIVE" for row in concept_senses
            ),
            "production_active_concept_count": 0,
        },
        "associations": {
            "synthetic_pair_revision_count": sum(row["association_kind"] == "PAIR" for row in associations),
            "synthetic_higher_order_revision_count": sum(row["association_kind"] == "HIGHER_ORDER" for row in associations),
            "synthetic_active_pair_revision_count": sum(row["association_kind"] == "PAIR" and row["lifecycle_state"] == "ACTIVE" for row in associations),
            "synthetic_active_higher_order_revision_count": sum(row["association_kind"] == "HIGHER_ORDER" and row["lifecycle_state"] == "ACTIVE" for row in associations),
            "production_pair_revision_count": sum(row["association_kind"] == "PAIR" for row in production),
            "production_higher_order_revision_count": sum(row["association_kind"] == "HIGHER_ORDER" for row in production),
            "production_active_association_count": sum(row["lifecycle_state"] == "ACTIVE" for row in production),
            "production_active_pending_review_count": 0,
        },
        "incidence": {
            "synthetic_incidence_count": sum(len(row["participants"]) for row in associations),
            "production_incidence_count": 0,
            "implicit_projected_pair_count": 0,
        },
        "realizations_and_compositions": {
            "synthetic_association_realization_count": sum(len(row["association_realizations"]) for row in fixture["compositions"]),
            "synthetic_composition_count": len(fixture["compositions"]),
            "synthetic_composition_coherence_review_count": len(
                fixture["composition_coherence_reviews"]
            ),
            "production_association_realization_count": 0,
            "production_composition_count": 0,
            "production_composition_coherence_review_count": 0,
            "production_product_eligible_composition_count": 0,
        },
        "interaction": {
            "synthetic_state_count": len(fixture["navigation_states"]),
            "synthetic_transition_count": len(fixture["transitions"]),
            "synthetic_workflow_count": len(fixture["workflows"]),
            "synthetic_export_count": len(fixture["exports"]),
            "production_state_count": 0,
            "production_transition_count": 0,
            "production_workflow_count": 0,
            "production_export_count": 0,
        },
    }
    return fixture


def reconstruct_count_taxonomy(fixture: dict[str, Any]) -> dict[str, Any]:
    associations = fixture["associations"]
    concepts = fixture["concepts"]
    senses = fixture["concept_senses"]
    production_associations = [row for row in associations if row["realm"] == "PRODUCTION"]
    return {
        "vocabulary": {
            "synthetic_scope_count": sum(
                all(
                    association["realm"] == "SYNTHETIC_CONTROL"
                    for association in associations
                    if association["scope"]["scope_id"] == scope["scope_id"]
                )
                for scope in fixture["scopes"]
            ),
            "synthetic_distinct_concept_count": len(
                {
                    participant["concept_id"]
                    for association in associations
                    if association["realm"] == "SYNTHETIC_CONTROL"
                    for participant in association["participants"]
                }
            ),
            "synthetic_concept_record_count": sum(
                row["realm"] == "SYNTHETIC_CONTROL" for row in concepts
            ),
            "synthetic_active_concept_count": sum(
                row["realm"] == "SYNTHETIC_CONTROL" and row["lifecycle_state"] == "ACTIVE"
                for row in concepts
            ),
            "synthetic_concept_sense_record_count": sum(
                row["realm"] == "SYNTHETIC_CONTROL" for row in senses
            ),
            "synthetic_active_concept_sense_count": sum(
                row["realm"] == "SYNTHETIC_CONTROL" and row["lifecycle_state"] == "ACTIVE"
                for row in senses
            ),
            "production_active_concept_count": sum(
                row["realm"] == "PRODUCTION" and row["lifecycle_state"] == "ACTIVE"
                for row in concepts
            ),
        },
        "associations": {
            "synthetic_pair_revision_count": sum(
                row["realm"] == "SYNTHETIC_CONTROL" and row["association_kind"] == "PAIR"
                for row in associations
            ),
            "synthetic_higher_order_revision_count": sum(
                row["realm"] == "SYNTHETIC_CONTROL" and row["association_kind"] == "HIGHER_ORDER"
                for row in associations
            ),
            "synthetic_active_pair_revision_count": sum(
                row["realm"] == "SYNTHETIC_CONTROL" and row["association_kind"] == "PAIR"
                and row["lifecycle_state"] == "ACTIVE"
                for row in associations
            ),
            "synthetic_active_higher_order_revision_count": sum(
                row["realm"] == "SYNTHETIC_CONTROL" and row["association_kind"] == "HIGHER_ORDER"
                and row["lifecycle_state"] == "ACTIVE"
                for row in associations
            ),
            "production_pair_revision_count": sum(
                row["association_kind"] == "PAIR" for row in production_associations
            ),
            "production_higher_order_revision_count": sum(
                row["association_kind"] == "HIGHER_ORDER" for row in production_associations
            ),
            "production_active_association_count": sum(
                row["lifecycle_state"] == "ACTIVE" for row in production_associations
            ),
            "production_active_pending_review_count": sum(
                row["lifecycle_state"] == "ACTIVE" and row["review"]["review_state"] != "FINAL"
                for row in production_associations
            ),
        },
        "incidence": {
            "synthetic_incidence_count": sum(
                len(row["participants"])
                for row in associations if row["realm"] == "SYNTHETIC_CONTROL"
            ),
            "production_incidence_count": sum(
                len(row["participants"])
                for row in associations if row["realm"] == "PRODUCTION"
            ),
            "implicit_projected_pair_count": 0,
        },
        "realizations_and_compositions": {
            "synthetic_association_realization_count": sum(
                len(row["association_realizations"])
                for row in fixture["compositions"] if row["realm"] == "SYNTHETIC_CONTROL"
            ),
            "synthetic_composition_count": sum(
                row["realm"] == "SYNTHETIC_CONTROL" for row in fixture["compositions"]
            ),
            "synthetic_composition_coherence_review_count": sum(
                row["realm"] == "SYNTHETIC_CONTROL"
                for row in fixture["composition_coherence_reviews"]
            ),
            "production_association_realization_count": sum(
                len(row["association_realizations"])
                for row in fixture["compositions"] if row["realm"] == "PRODUCTION"
            ),
            "production_composition_count": sum(
                row["realm"] == "PRODUCTION" for row in fixture["compositions"]
            ),
            "production_composition_coherence_review_count": sum(
                row["realm"] == "PRODUCTION"
                for row in fixture["composition_coherence_reviews"]
            ),
            "production_product_eligible_composition_count": sum(
                row["realm"] == "PRODUCTION" and row["product_eligible"]
                for row in fixture["compositions"]
            ),
        },
        "interaction": {
            "synthetic_state_count": sum(
                row["realm"] == "SYNTHETIC_CONTROL" for row in fixture["navigation_states"]
            ),
            "synthetic_transition_count": sum(
                row["realm"] == "SYNTHETIC_CONTROL" for row in fixture["transitions"]
            ),
            "synthetic_workflow_count": sum(
                row["realm"] == "SYNTHETIC_CONTROL" for row in fixture["workflows"]
            ),
            "synthetic_export_count": sum(
                row["realm"] == "SYNTHETIC_CONTROL" for row in fixture["exports"]
            ),
            "production_state_count": sum(
                row["realm"] == "PRODUCTION" for row in fixture["navigation_states"]
            ),
            "production_transition_count": sum(
                row["realm"] == "PRODUCTION" for row in fixture["transitions"]
            ),
            "production_workflow_count": sum(
                row["realm"] == "PRODUCTION" for row in fixture["workflows"]
            ),
            "production_export_count": sum(
                row["realm"] == "PRODUCTION" for row in fixture["exports"]
            ),
        },
    }


def validate_schema_documents(schemas: dict[Path, dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    by_name = {path.name: payload for path, payload in schemas.items()}
    seen_ids: set[str] = set()

    def walk(value: Any, pointer: str, owner: str) -> None:
        if isinstance(value, dict):
            if "required" in value:
                properties = value.get("properties", {})
                if not isinstance(value["required"], list) or not set(value["required"]).issubset(properties):
                    failures.append(f"{owner}:{pointer}:required_not_in_properties")
            ref = value.get("$ref")
            if isinstance(ref, str):
                filename = ref.split("#", 1)[0]
                if filename and filename not in by_name:
                    failures.append(f"{owner}:{pointer}:missing_ref:{filename}")
            for key, child in value.items():
                walk(child, f"{pointer}/{key}", owner)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{pointer}/{index}", owner)

    for path, payload in schemas.items():
        if payload.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            failures.append(f"{path.name}:draft")
        schema_id = payload.get("$id")
        if not isinstance(schema_id, str) or not schema_id.startswith(SCHEMA_BASE):
            failures.append(f"{path.name}:id")
        elif schema_id in seen_ids:
            failures.append(f"{path.name}:duplicate_id")
        else:
            seen_ids.add(schema_id)
        walk(payload, "#", path.name)
    return failures


def validate_json_schema_instance(
    instance: Any,
    schema_name: str,
    schemas: dict[Path, dict[str, Any]],
) -> list[str]:
    """Validate the contract's used Draft 2020-12 keyword subset.

    The validator intentionally supports every assertion keyword emitted by this
    builder. Cross-property arithmetic and cross-record references are validated
    separately by ``validate_fixture``.
    """

    by_name = {path.name: payload for path, payload in schemas.items()}

    def pointer(document: Any, fragment: str) -> Any:
        current = document
        if fragment in {"", "#"}:
            return current
        if not fragment.startswith("#/"):
            raise ValueError(f"unsupported JSON pointer fragment: {fragment}")
        for token in fragment[2:].split("/"):
            token = token.replace("~1", "/").replace("~0", "~")
            current = current[token]
        return current

    def resolve(ref: str, owner_name: str) -> tuple[Any, str]:
        filename, separator, fragment = ref.partition("#")
        target_name = filename or owner_name
        if target_name not in by_name:
            raise KeyError(target_name)
        target = by_name[target_name]
        return pointer(target, f"#{fragment}" if separator else ""), target_name

    def type_matches(value: Any, expected: str) -> bool:
        return {
            "null": value is None,
            "boolean": isinstance(value, bool),
            "integer": isinstance(value, int) and not isinstance(value, bool),
            "number": isinstance(value, (int, float)) and not isinstance(value, bool),
            "string": isinstance(value, str),
            "array": isinstance(value, list),
            "object": isinstance(value, dict),
        }.get(expected, False)

    def errors(value: Any, schema: Any, value_path: str, owner_name: str) -> list[str]:
        if not isinstance(schema, dict):
            return [f"{value_path}:SCHEMA_NOT_OBJECT"]
        found: list[str] = []
        if "$ref" in schema:
            target, target_owner = resolve(schema["$ref"], owner_name)
            found.extend(errors(value, target, value_path, target_owner))
        expected_type = schema.get("type")
        if expected_type is not None:
            allowed = expected_type if isinstance(expected_type, list) else [expected_type]
            if not any(type_matches(value, item) for item in allowed):
                return [f"{value_path}:TYPE"]
        if "const" in schema and value != schema["const"]:
            found.append(f"{value_path}:CONST")
        if "enum" in schema and value not in schema["enum"]:
            found.append(f"{value_path}:ENUM")
        if isinstance(value, str):
            if len(value) < int(schema.get("minLength", 0)):
                found.append(f"{value_path}:MIN_LENGTH")
            if "pattern" in schema and re.fullmatch(schema["pattern"], value) is None:
                found.append(f"{value_path}:PATTERN")
        if isinstance(value, int) and not isinstance(value, bool):
            if "minimum" in schema and value < schema["minimum"]:
                found.append(f"{value_path}:MINIMUM")
        if isinstance(value, list):
            if len(value) < int(schema.get("minItems", 0)):
                found.append(f"{value_path}:MIN_ITEMS")
            if "maxItems" in schema and len(value) > int(schema["maxItems"]):
                found.append(f"{value_path}:MAX_ITEMS")
            if schema.get("uniqueItems") and len({canonical_bytes(item) for item in value}) != len(value):
                found.append(f"{value_path}:UNIQUE_ITEMS")
            if "items" in schema:
                for index, item in enumerate(value):
                    found.extend(errors(item, schema["items"], f"{value_path}/{index}", owner_name))
        if isinstance(value, dict):
            properties = schema.get("properties", {})
            for field in schema.get("required", []):
                if field not in value:
                    found.append(f"{value_path}/{field}:REQUIRED")
            for field, child_schema in properties.items():
                if field in value:
                    found.extend(errors(value[field], child_schema, f"{value_path}/{field}", owner_name))
            if schema.get("additionalProperties") is False:
                for field in sorted(set(value) - set(properties)):
                    found.append(f"{value_path}/{field}:ADDITIONAL_PROPERTY")
        for child in schema.get("allOf", []):
            found.extend(errors(value, child, value_path, owner_name))
        if "if" in schema:
            condition_passes = not errors(value, schema["if"], value_path, owner_name)
            branch = schema.get("then") if condition_passes else schema.get("else")
            if branch is not None:
                found.extend(errors(value, branch, value_path, owner_name))
        return found

    filename, separator, fragment = schema_name.partition("#")
    if filename not in by_name:
        return [f"$:UNKNOWN_SCHEMA:{schema_name}"]
    target = pointer(by_name[filename], f"#{fragment}" if separator else "")
    return errors(instance, target, "$", filename)


def apply_pointer_mutation(value: Any, pointer_text: str, replacement: Any) -> None:
    if not pointer_text.startswith("/"):
        raise ValueError(pointer_text)
    tokens = [token.replace("~1", "/").replace("~0", "~") for token in pointer_text[1:].split("/")]
    current = value
    for token in tokens[:-1]:
        current = current[int(token)] if isinstance(current, list) else current[token]
    final = tokens[-1]
    if isinstance(current, list):
        current[int(final)] = replacement
    else:
        current[final] = replacement


def build_negative_probe_receipts(
    fixture: dict[str, Any],
    schemas: dict[Path, dict[str, Any]],
) -> list[dict[str, Any]]:
    active_higher = next(
        row
        for row in fixture["associations"]
        if row["association_kind"] == "HIGHER_ORDER" and row["lifecycle_state"] == "ACTIVE"
    )
    invalid_group = next(
        row
        for row in fixture["associations"]
        if row["review"]["disposition"] == "PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE"
    )
    invalid_composition = next(
        row
        for row in fixture["compositions"]
        if any(
            realization["association_revision_id"] == invalid_group["association_revision_id"]
            for realization in row["association_realizations"]
        )
    )
    valid_composition = next(
        row for row in fixture["compositions"] if row is not invalid_composition
    )
    associations_by_revision = {
        row["association_revision_id"]: row for row in fixture["associations"]
    }
    active_pair_realization = next(
        realization
        for realization in valid_composition["association_realizations"]
        if associations_by_revision[realization["association_revision_id"]]["association_kind"] == "PAIR"
    )
    active_pair = associations_by_revision[active_pair_realization["association_revision_id"]]
    active_higher_realization = next(
        realization
        for realization in valid_composition["association_realizations"]
        if realization["association_revision_id"] == active_higher["association_revision_id"]
    )
    active_higher_realization_index = valid_composition["association_realizations"].index(
        active_higher_realization
    )
    state = fixture["navigation_states"][0]
    workflow = fixture["workflows"][0]
    export = fixture["exports"][0]
    active_sense = next(
        row
        for row in fixture["concept_senses"]
        if row["sense_id"] == active_higher["participants"][0]["sense_id"]
    )
    active_concept = next(
        row for row in fixture["concepts"]
        if row["concept_id"] == active_sense["concept_id"]
    )
    coherent_composition_review = next(
        row for row in fixture["composition_coherence_reviews"]
        if row["decision"] == "COHERENT"
    )
    probe_specs: list[dict[str, Any]] = [
        {
            "probe_id": "PROBE-V3-SCHEMA-001",
            "target_schema": "association.schema.json",
            "base": active_higher,
            "base_ref": active_higher["association_revision_id"],
            "pointer": "/evidence/rights_cleared_for_governed_use",
            "value": False,
            "validator": "JSON_SCHEMA",
            "expected_error": "$/evidence/rights_cleared_for_governed_use:CONST",
        },
        {
            "probe_id": "PROBE-V3-SCHEMA-002",
            "target_schema": "association.schema.json",
            "base": active_higher,
            "base_ref": active_higher["association_revision_id"],
            "pointer": "/review/disposition",
            "value": "HARD_NEGATIVE",
            "validator": "JSON_SCHEMA",
            "expected_error": "$/review/disposition:ENUM",
        },
        {
            "probe_id": "PROBE-V3-SCHEMA-003",
            "target_schema": "association.schema.json",
            "base": active_higher,
            "base_ref": active_higher["association_revision_id"],
            "pointer": "/evidence/evidence_complete",
            "value": False,
            "validator": "JSON_SCHEMA",
            "expected_error": "$/evidence/evidence_complete:CONST",
        },
        {
            "probe_id": "PROBE-V3-SCHEMA-004",
            "target_schema": "association.schema.json",
            "base": active_higher,
            "base_ref": active_higher["association_revision_id"],
            "pointer": "/pair_projection_policy",
            "value": "PROJECT_COMPLETE_GRAPH",
            "validator": "JSON_SCHEMA",
            "expected_error": "$/pair_projection_policy:ENUM",
        },
        {
            "probe_id": "PROBE-V3-SCHEMA-005",
            "target_schema": "association.schema.json",
            "base": active_higher,
            "base_ref": active_higher["association_revision_id"],
            "pointer": "/review/review_state",
            "value": "PENDING",
            "validator": "JSON_SCHEMA",
            "expected_error": "$/review/review_state:CONST",
        },
        {
            "probe_id": "PROBE-V3-SCHEMA-006",
            "target_schema": "association.schema.json",
            "base": active_higher,
            "base_ref": active_higher["association_revision_id"],
            "pointer": "/order_semantics",
            "value": "ORDERED",
            "validator": "JSON_SCHEMA",
            "expected_error": "$/participants/0/ordinal:TYPE",
        },
        {
            "probe_id": "PROBE-V3-SCHEMA-007",
            "target_schema": "association.schema.json",
            "base": active_higher,
            "base_ref": active_higher["association_revision_id"],
            "pointer": "/roles_meaningful",
            "value": True,
            "validator": "JSON_SCHEMA",
            "expected_error": "$/participants/0/role_id:TYPE",
        },
        {
            "probe_id": "PROBE-V3-SCHEMA-008",
            "target_schema": "association.schema.json",
            "base": active_higher,
            "base_ref": active_higher["association_revision_id"],
            "pointer": "/product_eligible",
            "value": True,
            "validator": "JSON_SCHEMA",
            "expected_error": "$/realm:CONST",
        },
        {
            "probe_id": "PROBE-V3-SCHEMA-009",
            "target_schema": "composition.schema.json",
            "base": invalid_composition,
            "base_ref": invalid_composition["composition_revision_id"],
            "pointer": "/product_eligible",
            "value": True,
            "validator": "FIXTURE_SEMANTIC_INVARIANT",
            "collection": "compositions",
            "id_field": "composition_revision_id",
            "expected_error": f"{invalid_composition['composition_revision_id']}:PRODUCT_COMPOSITION_TRACE_INVALID",
        },
        {
            "probe_id": "PROBE-V3-SEMANTIC-010",
            "target_schema": "association.schema.json",
            "base": active_higher,
            "base_ref": active_higher["association_revision_id"],
            "pointer": "/arity",
            "value": 4,
            "validator": "SEMANTIC_INVARIANT",
            "expected_error": f"{active_higher['association_revision_id']}:ARITY_INCIDENCE_MISMATCH",
        },
        {
            "probe_id": "PROBE-V3-SEMANTIC-011",
            "target_schema": "association.schema.json",
            "base": active_higher,
            "base_ref": active_higher["association_revision_id"],
            "pointer": "/participants/1",
            "value": active_higher["participants"][0],
            "validator": "SEMANTIC_INVARIANT",
            "expected_error": f"{active_higher['association_revision_id']}:INCIDENCE_ID_DUPLICATE",
        },
        {
            "probe_id": "PROBE-V3-SCHEMA-012",
            "target_schema": "association.schema.json",
            "base": active_higher,
            "base_ref": active_higher["association_revision_id"],
            "pointer": "/evidence/evidence_item_ids",
            "value": [],
            "validator": "JSON_SCHEMA",
            "expected_error": "$/evidence/evidence_item_ids:MIN_ITEMS",
        },
        {
            "probe_id": "PROBE-V3-SCHEMA-013",
            "target_schema": "association.schema.json",
            "base": active_higher,
            "base_ref": active_higher["association_revision_id"],
            "pointer": "/evidence/locator_ids",
            "value": [],
            "validator": "JSON_SCHEMA",
            "expected_error": "$/evidence/locator_ids:MIN_ITEMS",
        },
        {
            "probe_id": "PROBE-V3-SCHEMA-014",
            "target_schema": "association.schema.json",
            "base": active_higher,
            "base_ref": active_higher["association_revision_id"],
            "pointer": "/evidence/negative_or_conflicting_evidence",
            "value": ["unresolved synthetic conflict"],
            "validator": "JSON_SCHEMA",
            "expected_error": "$/evidence/negative_or_conflicting_evidence:MAX_ITEMS",
        },
        {
            "probe_id": "PROBE-V3-SCHEMA-015",
            "target_schema": "association.schema.json",
            "base": active_higher,
            "base_ref": active_higher["association_revision_id"],
            "pointer": "/review/bounded_senses_compatible",
            "value": False,
            "validator": "JSON_SCHEMA",
            "expected_error": "$/review/bounded_senses_compatible:CONST",
        },
        {
            "probe_id": "PROBE-V3-SCHEMA-016",
            "target_schema": "association.schema.json",
            "base": active_higher,
            "base_ref": active_higher["association_revision_id"],
            "pointer": "/review/case_scope_compatible",
            "value": False,
            "validator": "JSON_SCHEMA",
            "expected_error": "$/review/case_scope_compatible:CONST",
        },
        {
            "probe_id": "PROBE-V3-SCHEMA-017",
            "target_schema": "association.schema.json",
            "base": active_higher,
            "base_ref": active_higher["association_revision_id"],
            "pointer": "/review/roles_and_topology_supported",
            "value": False,
            "validator": "JSON_SCHEMA",
            "expected_error": "$/review/roles_and_topology_supported:CONST",
        },
        {
            "probe_id": "PROBE-V3-SCHEMA-018",
            "target_schema": "association.schema.json",
            "base": active_higher,
            "base_ref": active_higher["association_revision_id"],
            "pointer": "/review/unsupported_bridge_count",
            "value": 1,
            "validator": "JSON_SCHEMA",
            "expected_error": "$/review/unsupported_bridge_count:CONST",
        },
        {
            "probe_id": "PROBE-V3-SCHEMA-019",
            "target_schema": "association.schema.json",
            "base": active_higher,
            "base_ref": active_higher["association_revision_id"],
            "pointer": "/evidence/synthesis_steps",
            "value": ["unsupported direct-evidence synthesis"],
            "validator": "JSON_SCHEMA",
            "expected_error": "$/evidence/synthesis_steps:MAX_ITEMS",
        },
        {
            "probe_id": "PROBE-V3-SCHEMA-020",
            "target_schema": "association.schema.json",
            "base": active_higher,
            "base_ref": active_higher["association_revision_id"],
            "pointer": "/activation/evidence_gate",
            "value": False,
            "validator": "JSON_SCHEMA",
            "expected_error": "$/activation/evidence_gate:CONST",
        },
        {
            "probe_id": "PROBE-V3-SEMANTIC-021",
            "target_schema": "association.schema.json",
            "base": active_higher,
            "base_ref": active_higher["association_revision_id"],
            "pointer": "/uncertainty/reviewed_in_review_id",
            "value": "review:foreign",
            "validator": "SEMANTIC_INVARIANT",
            "expected_error": f"{active_higher['association_revision_id']}:UNCERTAINTY_REVIEW_REFERENCE_MISMATCH",
        },
        {
            "probe_id": "PROBE-V3-SEMANTIC-022",
            "target_schema": "association.schema.json",
            "base": active_higher,
            "base_ref": active_higher["association_revision_id"],
            "pointer": "/participants/0/participant_scope_id",
            "value": "scope:foreign",
            "validator": "SEMANTIC_INVARIANT",
            "expected_error": f"{active_higher['association_revision_id']}:PARTICIPANT_SCOPE_MISMATCH",
        },
        {
            "probe_id": "PROBE-V3-SCHEMA-023",
            "target_schema": "association.schema.json",
            "base": active_higher,
            "base_ref": active_higher["association_revision_id"],
            "pointer": "/realm",
            "value": "PRODUCTION",
            "validator": "JSON_SCHEMA",
            "expected_error": "$/review/review_authority:ENUM",
        },
        {
            "probe_id": "PROBE-V3-SCHEMA-024",
            "target_schema": "association.schema.json",
            "base": active_higher,
            "base_ref": active_higher["association_revision_id"],
            "pointer": "/product_path",
            "value": "/invalid/synthetic-path",
            "validator": "JSON_SCHEMA",
            "expected_error": "$/product_path:CONST",
        },
        {
            "probe_id": "PROBE-V3-FIXTURE-025",
            "target_schema": "composition.schema.json",
            "base": valid_composition,
            "base_ref": valid_composition["composition_revision_id"],
            "pointer": f"/association_realizations/{active_higher_realization_index}/realization_kind",
            "value": "PAIR_EDGE",
            "validator": "FIXTURE_SEMANTIC_INVARIANT",
            "collection": "compositions",
            "id_field": "composition_revision_id",
            "expected_error": "HIGHER_ORDER_PAIR_EDGE_FORBIDDEN",
        },
        {
            "probe_id": "PROBE-V3-FIXTURE-026",
            "target_schema": "composition.schema.json",
            "base": valid_composition,
            "base_ref": valid_composition["composition_revision_id"],
            "pointer": f"/association_realizations/{active_higher_realization_index}/realized_incidence_ids",
            "value": active_higher_realization["realized_incidence_ids"][:2],
            "validator": "FIXTURE_SEMANTIC_INVARIANT",
            "collection": "compositions",
            "id_field": "composition_revision_id",
            "expected_error": "REALIZATION_TRACE_MISMATCH",
        },
        {
            "probe_id": "PROBE-V3-FIXTURE-027",
            "target_schema": "composition.schema.json",
            "base": valid_composition,
            "base_ref": valid_composition["composition_revision_id"],
            "pointer": f"/association_realizations/{valid_composition['association_realizations'].index(active_pair_realization)}/realization_kind",
            "value": "HYPEREDGE_HUB",
            "validator": "FIXTURE_SEMANTIC_INVARIANT",
            "collection": "compositions",
            "id_field": "composition_revision_id",
            "expected_error": "PAIR_REALIZATION_NOT_EDGE",
        },
        {
            "probe_id": "PROBE-V3-SCHEMA-028",
            "target_schema": "workflow.schema.json",
            "base": workflow,
            "base_ref": workflow["workflow_id"],
            "pointer": "/association_realization_ids",
            "value": [],
            "validator": "JSON_SCHEMA",
            "expected_error": "$/association_realization_ids:MIN_ITEMS",
        },
        {
            "probe_id": "PROBE-V3-SCHEMA-029",
            "target_schema": "navigation-state.schema.json",
            "base": state,
            "base_ref": state["state_id"],
            "pointer": "/nodes/0/association_revision_id",
            "value": active_higher["association_revision_id"],
            "validator": "JSON_SCHEMA",
            "expected_error": "$/nodes/0/association_revision_id:CONST",
        },
        {
            "probe_id": "PROBE-V3-FIXTURE-030",
            "target_schema": "navigation-state.schema.json",
            "base": state,
            "base_ref": state["state_id"],
            "pointer": "/path/0/to_navigation_node_id",
            "value": "nav:missing",
            "validator": "FIXTURE_SEMANTIC_INVARIANT",
            "collection": "navigation_states",
            "id_field": "state_id",
            "expected_error": "NAVIGATION_PATH_ENDPOINT_MISSING",
        },
        {
            "probe_id": "PROBE-V3-FIXTURE-031",
            "target_schema": "navigation-state.schema.json",
            "base": state,
            "base_ref": state["state_id"],
            "pointer": "/path/0/incidence_id",
            "value": active_higher["participants"][2]["incidence_id"],
            "validator": "FIXTURE_SEMANTIC_INVARIANT",
            "collection": "navigation_states",
            "id_field": "state_id",
            "expected_error": "NAVIGATION_INCIDENCE_OWNERSHIP_MISMATCH",
        },
        {
            "probe_id": "PROBE-V3-SCHEMA-032",
            "target_schema": "export-manifest.schema.json",
            "base": export,
            "base_ref": export["export_id"],
            "pointer": "/pair_projection_policy_preserved",
            "value": False,
            "validator": "JSON_SCHEMA",
            "expected_error": "$/pair_projection_policy_preserved:CONST",
        },
        {
            "probe_id": "PROBE-V3-FIXTURE-033",
            "target_schema": "concept.schema.json",
            "base": active_sense,
            "base_ref": active_sense["sense_id"],
            "pointer": "/lifecycle_state",
            "value": "INQUIRY_ONLY",
            "validator": "FIXTURE_SEMANTIC_INVARIANT",
            "collection": "concept_senses",
            "id_field": "sense_id",
            "expected_error": "ACTIVE_PARTICIPANT_NOT_ELIGIBLE",
        },
        {
            "probe_id": "PROBE-V3-SCHEMA-034",
            "target_schema": "association.schema.json",
            "base": active_higher,
            "base_ref": active_higher["association_revision_id"],
            "pointer": "/review/disposition",
            "value": "COHERENT_COMPOSITE_SUPPORT",
            "validator": "JSON_SCHEMA",
            "expected_error": "$/review/disposition:CONST",
        },
        {
            "probe_id": "PROBE-V3-FIXTURE-035",
            "target_schema": "composition.schema.json#/$defs/compositionCoherenceReview",
            "base": coherent_composition_review,
            "base_ref": coherent_composition_review["composition_coherence_review_id"],
            "pointer": "/authority/authority_state",
            "value": "PENDING",
            "validator": "FIXTURE_SEMANTIC_INVARIANT",
            "collection": "composition_coherence_reviews",
            "id_field": "composition_coherence_review_id",
            "expected_error": "COHERENT_REVIEW_NOT_FAIL_CLOSED",
        },
        {
            "probe_id": "PROBE-V3-SCHEMA-036",
            "target_schema": "concept.schema.json#/$defs/concept",
            "base": active_concept,
            "base_ref": active_concept["concept_id"],
            "pointer": "/association_eligible",
            "value": False,
            "validator": "JSON_SCHEMA",
            "expected_error": "$/association_eligible:CONST",
        },
        {
            "probe_id": "PROBE-V3-SCHEMA-037",
            "target_schema": "concept.schema.json#/$defs/conceptSense",
            "base": active_sense,
            "base_ref": active_sense["sense_id"],
            "pointer": "/authority/authority_state",
            "value": "PENDING",
            "validator": "JSON_SCHEMA",
            "expected_error": "$/authority/authority_state:CONST",
        },
    ]
    receipts: list[dict[str, Any]] = []
    for spec in probe_specs:
        mutant = copy.deepcopy(spec["base"])
        apply_pointer_mutation(mutant, spec["pointer"], copy.deepcopy(spec["value"]))
        if spec["validator"] == "JSON_SCHEMA":
            observed_errors = validate_json_schema_instance(mutant, spec["target_schema"], schemas)
        elif spec["validator"] == "SEMANTIC_INVARIANT":
            observed_errors = validate_association_semantics(mutant)
        else:
            mutant_fixture = copy.deepcopy(fixture)
            collection = mutant_fixture[spec["collection"]]
            index = next(
                index
                for index, row in enumerate(collection)
                if row[spec["id_field"]] == spec["base_ref"]
            )
            collection[index] = mutant
            observed_errors = validate_fixture(mutant_fixture)
        if not observed_errors:
            raise ValueError(f"negative probe unexpectedly passed: {spec['probe_id']}")
        expected_error = spec["expected_error"]
        if not any(
            error == expected_error or error.endswith(f":{expected_error}")
            for error in observed_errors
        ):
            raise ValueError(
                f"negative probe missed intended error: {spec['probe_id']}:{expected_error}:{observed_errors}"
            )
        receipts.append(
            {
                "probe_id": spec["probe_id"],
                "target_schema": spec["target_schema"],
                "base_object_ref": spec["base_ref"],
                "mutation_pointer": spec["pointer"],
                "mutation_value_json": json.dumps(spec["value"], sort_keys=True, separators=(",", ":")),
                "validator": spec["validator"],
                "expected_error_code": expected_error,
                "expected_rejected": True,
                "observed_rejected": True,
                "observed_error_codes": sorted(set(observed_errors)),
            }
        )
    return receipts


def validate_association_semantics(row: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    revision_id = row.get("association_revision_id", "UNKNOWN")
    participants = row.get("participants", [])
    if row.get("arity") != len(participants):
        failures.append(f"{revision_id}:ARITY_INCIDENCE_MISMATCH")
    if len({participant.get("incidence_id") for participant in participants}) != len(participants):
        failures.append(f"{revision_id}:INCIDENCE_ID_DUPLICATE")
    concept_senses = [(participant.get("concept_id"), participant.get("sense_id")) for participant in participants]
    if len(set(concept_senses)) != len(concept_senses):
        failures.append(f"{revision_id}:CONCEPT_SENSE_PARTICIPANT_DUPLICATE")
    ordinals = [participant.get("ordinal") for participant in participants]
    if row.get("order_semantics") == "ORDERED":
        if any(not isinstance(value, int) or isinstance(value, bool) for value in ordinals):
            failures.append(f"{revision_id}:ORDERED_ORDINAL_MISSING")
        elif len(set(ordinals)) != len(ordinals):
            failures.append(f"{revision_id}:ORDERED_ORDINAL_DUPLICATE")
        elif ordinals != list(range(len(participants))):
            failures.append(f"{revision_id}:ORDERED_ORDINAL_NOT_CONTIGUOUS")
    elif any(value is not None for value in ordinals):
        failures.append(f"{revision_id}:UNORDERED_ORDINAL_PRESENT")
    else:
        specs = [
            (
                participant.get("concept_id"), participant.get("sense_id"),
                participant.get("ordinal"), participant.get("role_id"),
            )
            for participant in participants
        ]
        if specs != canonical_participant_specs(
            specs, row.get("order_semantics"), bool(row.get("roles_meaningful"))
        ):
            failures.append(f"{revision_id}:UNORDERED_STORED_ORDER_NOT_CANONICAL")
    roles = [participant.get("role_id") for participant in participants]
    if row.get("roles_meaningful") and any(not isinstance(value, str) or not value for value in roles):
        failures.append(f"{revision_id}:MEANINGFUL_ROLE_MISSING")
    if not row.get("roles_meaningful") and any(value is not None for value in roles):
        failures.append(f"{revision_id}:NONMEANINGFUL_ROLE_PRESENT")
    incidence_ids = {participant.get("incidence_id") for participant in participants}
    if any(
        participant.get("participant_scope_id") != row.get("scope", {}).get("scope_id")
        for participant in participants
    ):
        failures.append(f"{revision_id}:PARTICIPANT_SCOPE_MISMATCH")
    if row.get("uncertainty", {}).get("reviewed_in_review_id") != row.get("review", {}).get("review_id"):
        failures.append(f"{revision_id}:UNCERTAINTY_REVIEW_REFERENCE_MISMATCH")
    pair_ids = set(row.get("internal_pair_association_ids", []))
    links = row.get("internal_pair_links", [])
    if {link.get("pair_association_id") for link in links} != pair_ids:
        failures.append(f"{revision_id}:PAIR_LINK_ID_MISMATCH")
    for link in links:
        endpoints = link.get("participant_incidence_ids", [])
        if len(endpoints) != 2 or len(set(endpoints)) != 2 or not set(endpoints).issubset(incidence_ids):
            failures.append(f"{revision_id}:PAIR_LINK_ENDPOINT_INVALID")
            continue
        group_by_incidence = {
            participant["incidence_id"]: participant for participant in participants
        }
        endpoint_senses = [group_by_incidence[value]["sense_id"] for value in endpoints]
        if endpoint_senses != link.get("endpoint_sense_ids"):
            failures.append(f"{revision_id}:PAIR_LINK_ENDPOINT_SENSE_MISMATCH")
        if len(link.get("pair_participant_incidence_ids", [])) != 2:
            failures.append(f"{revision_id}:PAIR_LINK_PAIR_INCIDENCE_WIDTH")
    return failures


def validate_hash_binding_reconstruction(fixture: dict[str, Any]) -> list[str]:
    """Reconstruct governed hashes and IDs from the committed binding data."""

    failures: list[str] = []
    contract = fixture["hash_binding_contract"]
    if fixture["hash_binding_contract_canonical_sha256"] != digest(contract):
        failures.append("HASH_BINDING_CONTRACT_DIGEST_MISMATCH")
    bindings = {row["object_type"]: row for row in contract["bindings"]}
    if len(bindings) != len(contract["bindings"]):
        failures.append("HASH_BINDING_OBJECT_TYPE_DUPLICATE")

    def source_value(record: dict[str, Any], pointer_text: str) -> Any:
        current: Any = record
        for token in pointer_text.strip("/").split("/") if pointer_text.strip("/") else []:
            current = current[token]
        return current

    def reconstruct_materials(binding: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
        resolved: dict[str, Any] = {}
        for spec in binding["materials"]:
            recipe = spec["recipe"]
            if recipe == "DIRECT_FIELD_OBJECT":
                value = {field: record[field] for field in spec["source_fields"]}
            elif recipe == "DIRECT_FIELD_VALUE":
                if len(spec["source_fields"]) != 1:
                    raise ValueError(f"DIRECT_FIELD_VALUE arity: {spec['material_name']}")
                value = record[spec["source_fields"][0]]
            elif recipe == "ASSOCIATION_IDENTITY":
                value = {}
                for mapping in spec["field_mappings"]:
                    source = source_value(record, mapping["source_pointer"])
                    operation = mapping["operation"]
                    if operation == "COPY":
                        projected = copy.deepcopy(source)
                    elif operation == "PROJECT_PARTICIPANT_IDENTITY":
                        specs = [
                            (
                                item["concept_id"], item["sense_id"],
                                item["ordinal"], item["role_id"],
                            )
                            for item in source
                        ]
                        projected = [
                            {
                                "concept_id": concept_id,
                                "sense_id": sense_id,
                                "ordinal": ordinal,
                                "role_id": role_id,
                            }
                            for concept_id, sense_id, ordinal, role_id in canonical_participant_specs(
                                specs, record["order_semantics"], record["roles_meaningful"]
                            )
                        ]
                    elif operation == "PROJECT_SCOPE_IDENTITY":
                        projected = project_scope_identity(source)
                    else:
                        raise ValueError(
                            f"unsupported association identity operation: {operation}"
                        )
                    value[mapping["output_key"]] = projected
            elif recipe in {"REALIZATION_SEMANTIC_ALIASES", "COMPOSITION_IDENTITY_ALIASES"}:
                value = {}
                for mapping in spec["field_mappings"]:
                    source = source_value(record, mapping["source_pointer"])
                    if mapping["operation"] == "MAP_ARRAY_FIELD":
                        source = [item[mapping["item_field"]] for item in source]
                    value[mapping["output_key"]] = source
            elif recipe == "ASSOCIATION_REVISION":
                value = {"association_id": record["association_id"], **resolved["association_semantic"]}
            elif recipe == "COMPOSITION_REVISION":
                value = {"semantic": resolved["composition_semantic"], "revision": 1}
            else:
                raise ValueError(f"unsupported material recipe for top-level reconstruction: {recipe}")
            if (
                recipe == "ASSOCIATION_IDENTITY"
                and isinstance(value, dict)
                and set(value) != set(spec["output_keys"])
            ):
                raise ValueError(f"material output key mismatch: {spec['material_name']}")
            resolved[spec["material_name"]] = value
        return resolved

    def check_record(binding: dict[str, Any], record: dict[str, Any], label: str) -> None:
        materials = reconstruct_materials(binding, record)
        for item in binding["hash_fields"]:
            if record[item["hash_field"]] != digest(materials[item["material_name"]]):
                failures.append(f"{label}:{item['hash_field']}:CONTRACT_HASH_MISMATCH")
        for item in binding["identifiers"]:
            source_name = item["digest_material_name"]
            if source_name is None:
                if not record[item["identifier_field"]].startswith(item["prefix"]):
                    failures.append(f"{label}:{item['identifier_field']}:STATIC_PREFIX_MISMATCH")
                continue
            expected = item["prefix"] + digest(materials[source_name])[: item["digest_hex_chars"]]
            if record[item["identifier_field"]] != expected:
                failures.append(f"{label}:{item['identifier_field']}:CONTRACT_ID_MISMATCH")

    for association in fixture["associations"]:
        check_record(bindings["ASSOCIATION_REVISION"], association, association["association_revision_id"])
        incidence_binding = bindings["PARTICIPANT_INCIDENCE"]
        identifier_spec = incidence_binding["identifiers"][0]
        for index, participant in enumerate(association["participants"], 1):
            expected = (
                identifier_spec["prefix"]
                + association["identity_material_sha256"][: identifier_spec["digest_hex_chars"]]
                + f":{index:02d}"
            )
            if participant["incidence_id"] != expected:
                failures.append(f"{participant['incidence_id']}:CONTRACT_INCIDENCE_ID_MISMATCH")
    for composition in fixture["compositions"]:
        check_record(bindings["COMPOSITION_REVISION"], composition, composition["composition_revision_id"])
        for realization in composition["association_realizations"]:
            check_record(
                bindings["ASSOCIATION_REALIZATION"],
                realization,
                realization["association_realization_id"],
            )
    collection_map = {
        "VOCABULARY_CONCEPT": fixture["concepts"],
        "CONCEPT_SENSE": fixture["concept_senses"],
        "COMPOSITION_COHERENCE_REVIEW": fixture["composition_coherence_reviews"],
        "NAVIGATION_STATE": fixture["navigation_states"],
        "TRANSITION": fixture["transitions"],
        "WORKFLOW": fixture["workflows"],
        "EXPORT": fixture["exports"],
        "V2_PAIR_ADAPTER_RECEIPT": fixture["v2_pair_adapter_receipts"],
        "V2_PAIR_SOURCE_FIXTURE": fixture["v2_pair_source_fixtures"],
    }
    for object_type, records in collection_map.items():
        for record in records:
            label = next(
                (record[field] for field in record if field.endswith("_id")),
                object_type,
            )
            check_record(bindings[object_type], record, label)
    return failures


def association_semantic_material_from_record(row: dict[str, Any]) -> dict[str, Any]:
    return {
        key: row[key]
        for key in (
            "association_kind", "realm", "semantic_version", "arity", "order_semantics",
            "roles_meaningful", "identity_material_sha256", "scope", "participants",
            "evidence", "review", "activation", "uncertainty", "lifecycle_state",
            "pair_projection_policy", "internal_pair_association_ids", "internal_pair_links",
            "product_eligible", "product_path", "product_eligibility_disposition",
            "product_ineligibility_reason",
        )
    }


def pair_graph_component_count(row: dict[str, Any]) -> int:
    incidence_ids = [participant["incidence_id"] for participant in row["participants"]]
    parent = {incidence_id: incidence_id for incidence_id in incidence_ids}

    def find(value: str) -> str:
        while parent[value] != value:
            parent[value] = parent[parent[value]]
            value = parent[value]
        return value

    for link in row["internal_pair_links"]:
        left, right = link["participant_incidence_ids"]
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parent[right_root] = left_root
    return len({find(value) for value in incidence_ids})


def validate_fixture(fixture: dict[str, Any]) -> list[str]:
    failures: list[str] = validate_hash_binding_reconstruction(fixture)
    associations = fixture["associations"]
    by_revision = {row["association_revision_id"]: row for row in associations}
    if len(by_revision) != len(associations):
        failures.append("ASSOCIATION_REVISION_IDS_NOT_UNIQUE")
    if len({row["association_id"] for row in associations}) != len(associations):
        failures.append("ASSOCIATION_IDS_NOT_UNIQUE")
    scopes = fixture["scopes"]
    scope_by_id = {row["scope_id"]: row for row in scopes}
    if len(scope_by_id) != len(scopes):
        failures.append("GOVERNED_SCOPE_IDS_NOT_UNIQUE")
    for scope in scopes:
        for key in SCOPE_SET_ARRAY_KEYS:
            if scope[key] != sorted(set(scope[key])):
                failures.append(f"{scope['scope_id']}:SCOPE_SET_ARRAY_NOT_CANONICAL:{key}")
    concepts = fixture["concepts"]
    concept_by_id = {row["concept_id"]: row for row in concepts}
    senses = fixture["concept_senses"]
    sense_by_id = {row["sense_id"]: row for row in senses}
    if len(concept_by_id) != len(concepts):
        failures.append("CONCEPT_IDS_NOT_UNIQUE")
    if len(sense_by_id) != len(senses):
        failures.append("CONCEPT_SENSE_IDS_NOT_UNIQUE")
    for concept in concepts:
        semantic = {
            key: concept[key]
            for key in (
                "realm", "canonical_label", "semantic_version", "lifecycle_state",
                "association_eligible", "authority", "product_eligible", "product_path",
                "product_eligibility_disposition", "product_ineligibility_reason",
            )
        }
        if concept["semantic_sha256"] != digest(semantic):
            failures.append(f"{concept['concept_id']}:CONCEPT_SEMANTIC_HASH_MISMATCH")
        if not product_disposition_valid(concept):
            failures.append(f"{concept['concept_id']}:CONCEPT_PRODUCT_TUPLE_INVALID")
        if concept["realm"] == "PRODUCTION" and concept["authority"]["authority_kind"] == "SYNTHETIC_TEST_AUTHORITY":
            failures.append(f"{concept['concept_id']}:PRODUCTION_SYNTHETIC_AUTHORITY")
        if concept["lifecycle_state"] == "ACTIVE" and not (
            concept["association_eligible"]
            and concept["authority"]["authority_state"] == "FINAL"
        ):
            failures.append(f"{concept['concept_id']}:ACTIVE_CONCEPT_NOT_GOVERNED")
    for sense in senses:
        semantic = {
            key: sense[key]
            for key in (
                "concept_id", "realm", "bounded_definition", "vocabulary_crosswalk_ids",
                "governed_scope_ids", "semantic_version", "lifecycle_state",
                "association_eligible", "authority", "product_eligible", "product_path",
                "product_eligibility_disposition", "product_ineligibility_reason",
            )
        }
        if sense["semantic_sha256"] != digest(semantic):
            failures.append(f"{sense['sense_id']}:SENSE_SEMANTIC_HASH_MISMATCH")
        if sense["concept_id"] not in concept_by_id:
            failures.append(f"{sense['sense_id']}:SENSE_CONCEPT_REFERENCE_MISSING")
        if not set(sense["governed_scope_ids"]).issubset(scope_by_id):
            failures.append(f"{sense['sense_id']}:SENSE_SCOPE_REFERENCE_MISSING")
        if not product_disposition_valid(sense):
            failures.append(f"{sense['sense_id']}:SENSE_PRODUCT_TUPLE_INVALID")
        if sense["realm"] == "PRODUCTION" and sense["authority"]["authority_kind"] == "SYNTHETIC_TEST_AUTHORITY":
            failures.append(f"{sense['sense_id']}:PRODUCTION_SYNTHETIC_AUTHORITY")
        if sense["lifecycle_state"] == "ACTIVE" and not (
            sense["association_eligible"]
            and sense["authority"]["authority_state"] == "FINAL"
        ):
            failures.append(f"{sense['sense_id']}:ACTIVE_SENSE_NOT_GOVERNED")

    higher_support = {
        "DIRECT_HIGHER_ORDER_SUPPORT", "COHERENT_COMPOSITE_SUPPORT",
        "MIXED_DIRECT_AND_COMPOSITE_SUPPORT",
    }
    gate_names = (
        "evidence_gate", "final_review_gate", "authority_gate", "coherence_gate",
        "rights_gate", "conflict_gate", "bounded_scope_gate", "synthesis_gate",
        "product_policy_gate",
    )
    for row in associations:
        failures.extend(validate_association_semantics(row))
        revision_id = row["association_revision_id"]
        if row["association_kind"] == "PAIR":
            if row["arity"] != 2 or row["pair_projection_policy"] != "NOT_APPLICABLE":
                failures.append(f"{revision_id}:PAIR_CONTRACT")
        elif row["arity"] < 3 or row["pair_projection_policy"] != "NONE":
            failures.append(f"{revision_id}:HIGHER_ORDER_PROJECTION_CONTRACT")
        gates = row["activation"]
        if gates["all_gates_pass"] != all(gates[name] for name in gate_names):
            failures.append(f"{revision_id}:GATE_CONJUNCTION_MISMATCH")
        expected_activation = derive_activation(
            row, gates["requested_state"] == "ACTIVE"
        )
        if gates != expected_activation:
            failures.append(f"{revision_id}:ACTIVATION_NOT_DERIVED_FROM_FACTS")
        expected_lifecycle_active = gates["decision"] == "ALLOW" and gates["all_gates_pass"]
        if (row["lifecycle_state"] == "ACTIVE") != expected_lifecycle_active:
            failures.append(f"{revision_id}:LIFECYCLE_ACTIVATION_MISMATCH")
        if row["scope"]["scope_id"] not in scope_by_id or row["scope"] != scope_by_id.get(row["scope"]["scope_id"]):
            failures.append(f"{revision_id}:ASSOCIATION_SCOPE_NOT_GOVERNED")
        for participant in row["participants"]:
            concept = concept_by_id.get(participant["concept_id"])
            sense = sense_by_id.get(participant["sense_id"])
            if concept is None or sense is None or sense.get("concept_id") != participant["concept_id"]:
                failures.append(f"{revision_id}:PARTICIPANT_VOCABULARY_REFERENCE_MISSING")
                continue
            if row["scope"]["scope_id"] not in sense["governed_scope_ids"]:
                failures.append(f"{revision_id}:PARTICIPANT_SENSE_SCOPE_MISMATCH")
            if row["lifecycle_state"] == "ACTIVE" and not (
                concept["lifecycle_state"] == "ACTIVE"
                and concept["association_eligible"]
                and sense["lifecycle_state"] == "ACTIVE"
                and sense["association_eligible"]
            ):
                failures.append(f"{revision_id}:ACTIVE_PARTICIPANT_NOT_ELIGIBLE")
        if row["lifecycle_state"] == "ACTIVE":
            supporting = (
                row["review"]["disposition"] == "DIRECT_PAIRWISE_SUPPORT"
                if row["association_kind"] == "PAIR"
                else row["review"]["disposition"] in higher_support
            )
            support_mode_valid = (
                row["evidence"]["support_mode"] == "DIRECT_PAIR"
                if row["association_kind"] == "PAIR"
                else row["evidence"]["support_mode"] in {"DIRECT_GROUP", "COHERENT_COMPOSITE", "MIXED"}
            )
            if not (
                row["review"]["review_state"] == "FINAL"
                and row["review"]["authority_state"] == "FINAL"
                and row["review"]["global_coherence"] == "PASS"
                and supporting and support_mode_valid
                and row["evidence"]["same_configuration"]
                and bool(row["evidence"]["evidence_item_ids"])
                and bool(row["evidence"]["locator_ids"])
                and row["evidence"]["evidence_complete"]
                and row["evidence"]["rights_cleared_for_governed_use"]
                and row["evidence"]["conflicts_resolved"]
                and not row["evidence"]["negative_or_conflicting_evidence"]
                and row["review"]["bounded_senses_compatible"]
                and row["review"]["case_scope_compatible"]
                and row["review"]["roles_and_topology_supported"]
                and row["review"]["unsupported_bridge_count"] == 0
                and row["uncertainty"]["status"] == "RESOLVED_BOUNDED"
                and row["uncertainty"]["activation_policy"] == "ALLOWED_BOUNDED"
                and gates["requested_state"] == "ACTIVE"
                and gates["decision"] == "ALLOW"
                and gates["all_gates_pass"]
            ):
                failures.append(f"{revision_id}:ILLEGAL_ACTIVE_STATE")
            if not row["product_eligible"] and not (
                row["product_eligibility_disposition"] in {
                    "INELIGIBLE", "DEFERRED", "NOT_APPLICABLE_SYNTHETIC"
                } and row["product_ineligibility_reason"]
            ):
                failures.append(f"{revision_id}:ACTIVE_NONPRODUCT_REASON_MISSING")
        if row["product_eligible"] and not (
            row["realm"] == "PRODUCTION" and row["lifecycle_state"] == "ACTIVE"
            and isinstance(row["product_path"], str) and bool(row["product_path"])
            and row["product_eligibility_disposition"] == "ELIGIBLE"
            and row["product_ineligibility_reason"] is None
            and gates["product_policy_gate"]
        ):
            failures.append(f"{revision_id}:ILLEGAL_PRODUCT_ELIGIBILITY")
        if not product_disposition_valid(row):
            failures.append(f"{revision_id}:PRODUCT_DISPOSITION_TUPLE_INVALID")
        if row["realm"] == "PRODUCTION" and row["review"]["review_authority"] == "SYNTHETIC_TEST_AUTHORITY":
            failures.append(f"{revision_id}:PRODUCTION_SYNTHETIC_AUTHORITY")

        for link in row["internal_pair_links"]:
            pair_record = by_revision.get(link["pair_association_revision_id"])
            group_endpoints = {
                participant["incidence_id"]: participant for participant in row["participants"]
            }
            group_senses = [
                group_endpoints[incidence_id]["sense_id"]
                for incidence_id in link["participant_incidence_ids"]
                if incidence_id in group_endpoints
            ]
            if not (
                pair_record is not None
                and pair_record["association_kind"] == "PAIR"
                and pair_record["association_id"] == link["pair_association_id"]
                and pair_record["lifecycle_state"] == "ACTIVE"
                and pair_record["review"]["disposition"] == "DIRECT_PAIRWISE_SUPPORT"
                and pair_record["evidence"]["support_mode"] == "DIRECT_PAIR"
                and [item["incidence_id"] for item in pair_record["participants"]]
                == link["pair_participant_incidence_ids"]
                and [item["sense_id"] for item in pair_record["participants"]]
                == link["endpoint_sense_ids"]
                and group_senses == link["endpoint_sense_ids"]
            ):
                failures.append(f"{revision_id}:GOVERNED_PAIR_LINK_NOT_RESOLVED")

        identity_specs = [
            (item["concept_id"], item["sense_id"], item["ordinal"], item["role_id"])
            for item in row["participants"]
        ]
        identity_material = association_identity_material(
            row["association_kind"], identity_specs, row["scope"],
            row["order_semantics"], row["roles_meaningful"],
        )
        identity_hash = digest(identity_material)
        if row["identity_material_sha256"] != identity_hash:
            failures.append(f"{revision_id}:IDENTITY_HASH_MISMATCH")
        if row["association_id"] != f"association:v3:{identity_hash[:24]}":
            failures.append(f"{revision_id}:ASSOCIATION_ID_MISMATCH")
        semantic = association_semantic_material_from_record(row)
        if row["semantic_sha256"] != digest(semantic):
            failures.append(f"{revision_id}:SEMANTIC_HASH_MISMATCH")
        if row["association_revision_id"] != f"association-revision:v3:{digest({'association_id': row['association_id'], **semantic})[:24]}":
            failures.append(f"{revision_id}:REVISION_ID_MISMATCH")
        if row["presentation_sha256"] != digest(row["presentation"]):
            failures.append(f"{revision_id}:PRESENTATION_HASH_MISMATCH")

    controls = {row["control_class"]: row for row in fixture["control_expectations"]}
    required_controls = {
        "VALID_SPARSE_DISCONNECTED_HIGHER_ORDER_GROUP", "INVALID_FULL_PAIR_CLIQUE",
        "BOUNDED_SENSE_CONFLICT", "CROSS_CASE_SOURCE_BUNDLE",
        "ISOLATED_ACTIVE_TERM_IN_VALID_HYPEREDGE",
        "RENDERABLE_COMPOSITION_WITHOUT_VALID_GROUP", "ILLEGAL_HYPEREDGE_PAIR_PROJECTION",
        "ACTIVE_WITH_PENDING_OR_NONFINAL_REVIEW", "ACTIVE_ARITY_FIVE_PROJECTION_NONE",
        "ONE_WAY_V2_PAIR_ADAPTER",
    }
    if set(controls) != required_controls:
        failures.append("CONTROL_CLASS_SET_MISMATCH")
    sparse = next(row for row in associations if row["arity"] == 5 and row["lifecycle_state"] == "ACTIVE")
    if not (
        sparse["association_kind"] == "HIGHER_ORDER" and sparse["pair_projection_policy"] == "NONE"
        and len(sparse["internal_pair_links"]) == 2 and pair_graph_component_count(sparse) == 3
        and sparse["review"]["global_coherence"] == "PASS"
        and all(
            by_revision[link["pair_association_revision_id"]]["lifecycle_state"] == "ACTIVE"
            for link in sparse["internal_pair_links"]
        )
    ):
        failures.append("SPARSE_ACTIVE_ARITY_FIVE_CONTROL_FAILED")
    clique = next(
        row for row in associations
        if row["review"]["disposition"] == "PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE"
    )
    if not (
        clique["arity"] == 4 and len(clique["internal_pair_links"]) == 6
        and pair_graph_component_count(clique) == 1 and clique["lifecycle_state"] == "INACTIVE"
        and all(
            by_revision[link["pair_association_revision_id"]]["lifecycle_state"] == "ACTIVE"
            for link in clique["internal_pair_links"]
        )
    ):
        failures.append("FULL_CLIQUE_INVALID_CONTROL_FAILED")
    isolated_incidence = sparse["participants"][2]["incidence_id"]
    if isolated_incidence in {
        incidence for link in sparse["internal_pair_links"] for incidence in link["participant_incidence_ids"]
    }:
        failures.append("ISOLATED_TERM_CONTROL_NOT_ISOLATED")
    isolated_participant = next(
        row for row in sparse["participants"] if row["incidence_id"] == isolated_incidence
    )
    if not (
        concept_by_id[isolated_participant["concept_id"]]["lifecycle_state"] == "ACTIVE"
        and sense_by_id[isolated_participant["sense_id"]]["lifecycle_state"] == "ACTIVE"
    ):
        failures.append("ISOLATED_TERM_VOCABULARY_NOT_ACTIVE")

    coherence_reviews = fixture["composition_coherence_reviews"]
    coherence_review_by_id = {
        row["composition_coherence_review_id"]: row for row in coherence_reviews
    }
    if len(coherence_review_by_id) != len(coherence_reviews):
        failures.append("COMPOSITION_COHERENCE_REVIEW_IDS_NOT_UNIQUE")
    for review in coherence_reviews:
        semantic = {
            key: review[key]
            for key in (
                "composition_id", "realm", "review_state", "authority", "review_version",
                "global_coherence", "bounded_senses_compatible", "case_scope_compatible",
                "roles_and_topology_supported", "same_configuration",
                "unsupported_bridge_count", "association_revision_ids",
                "association_realization_ids", "incidence_ids", "decision", "reasons",
            )
        }
        if review["semantic_sha256"] != digest(semantic) or review[
            "composition_coherence_review_id"
        ] != f"composition-review:v3:{digest(semantic)[:24]}":
            failures.append(
                f"{review['composition_coherence_review_id']}:COMPOSITION_REVIEW_HASH_MISMATCH"
            )
        if review["realm"] == "PRODUCTION" and review["authority"]["authority_kind"] == "SYNTHETIC_TEST_AUTHORITY":
            failures.append(
                f"{review['composition_coherence_review_id']}:PRODUCTION_SYNTHETIC_AUTHORITY"
            )
        if review["decision"] == "COHERENT" and not (
            review["review_state"] == "FINAL"
            and review["authority"]["authority_state"] == "FINAL"
            and review["global_coherence"] == "PASS"
            and review["bounded_senses_compatible"]
            and review["case_scope_compatible"]
            and review["roles_and_topology_supported"]
            and review["same_configuration"]
            and review["unsupported_bridge_count"] == 0
        ):
            failures.append(
                f"{review['composition_coherence_review_id']}:COHERENT_REVIEW_NOT_FAIL_CLOSED"
            )

    for composition in fixture["compositions"]:
        semantic = {
            key: composition[key]
            for key in (
                "realm", "association_realizations", "composition_node_ids", "topology_family",
                "renderability", "global_coherence_review_id", "association_trace_complete",
                "product_eligible", "product_path", "product_eligibility_disposition",
                "product_ineligibility_reason",
            )
        }
        identity = {
            "association_realization_ids": [
                row["association_realization_id"] for row in composition["association_realizations"]
            ],
            "node_ids": composition["composition_node_ids"],
            "topology_family": composition["topology_family"],
        }
        if composition["composition_id"] != f"composition:v3:{digest(identity)[:24]}":
            failures.append(f"{composition['composition_revision_id']}:COMPOSITION_ID_MISMATCH")
        if composition["composition_revision_id"] != f"composition-revision:v3:{digest({'semantic': semantic, 'revision': 1})[:24]}":
            failures.append(f"{composition['composition_revision_id']}:COMPOSITION_REVISION_MISMATCH")
        if composition["semantic_sha256"] != digest(semantic):
            failures.append(f"{composition['composition_revision_id']}:COMPOSITION_SEMANTIC_HASH_MISMATCH")
        if composition["presentation_sha256"] != digest(composition["presentation"]):
            failures.append(f"{composition['composition_revision_id']}:COMPOSITION_PRESENTATION_HASH_MISMATCH")
        review = coherence_review_by_id.get(composition["global_coherence_review_id"])
        if review is None or review["composition_id"] != composition["composition_id"]:
            failures.append(
                f"{composition['composition_revision_id']}:COMPOSITION_REVIEW_REFERENCE_MISMATCH"
            )
        traced_revision_ids: set[str] = set()
        traced_realization_ids: set[str] = set()
        traced_incidence_ids: set[str] = set()
        traced_concept_ids: set[str] = set()
        for realization in composition["association_realizations"]:
            realization_semantic = {
                "association_revision_id": realization["association_revision_id"],
                "incidence_ids": realization["realized_incidence_ids"],
                "realization_kind": realization["realization_kind"],
            }
            if realization["association_realization_id"] != f"realization:v3:{digest(realization_semantic)[:24]}":
                failures.append(f"{realization['association_realization_id']}:REALIZATION_ID_MISMATCH")
            if realization["semantic_sha256"] != digest(realization_semantic):
                failures.append(f"{realization['association_realization_id']}:REALIZATION_SEMANTIC_HASH_MISMATCH")
            if realization["presentation_sha256"] != digest(realization["presentation"]):
                failures.append(f"{realization['association_realization_id']}:REALIZATION_PRESENTATION_HASH_MISMATCH")
            association = by_revision.get(realization["association_revision_id"])
            if association is None:
                failures.append(f"{realization['association_realization_id']}:REALIZATION_TRACE_MISMATCH")
                continue
            expected_incidences = {
                item["incidence_id"] for item in association["participants"]
            }
            if set(realization["realized_incidence_ids"]) != expected_incidences:
                failures.append(f"{realization['association_realization_id']}:REALIZATION_TRACE_MISMATCH")
            if association["association_kind"] == "PAIR" and realization["realization_kind"] != "PAIR_EDGE":
                failures.append(f"{realization['association_realization_id']}:PAIR_REALIZATION_NOT_EDGE")
            if association["association_kind"] == "HIGHER_ORDER" and realization["realization_kind"] == "PAIR_EDGE":
                failures.append(f"{realization['association_realization_id']}:HIGHER_ORDER_PAIR_EDGE_FORBIDDEN")
            traced_revision_ids.add(association["association_revision_id"])
            traced_realization_ids.add(realization["association_realization_id"])
            traced_incidence_ids.update(realization["realized_incidence_ids"])
            traced_concept_ids.update(
                item["concept_id"] for item in association["participants"]
            )
        if set(composition["composition_node_ids"]) != traced_concept_ids:
            failures.append(
                f"{composition['composition_revision_id']}:COMPOSITION_NODE_TRACE_MISMATCH"
            )
        if review is not None and not (
            set(review["association_revision_ids"]) == traced_revision_ids
            and set(review["association_realization_ids"]) == traced_realization_ids
            and set(review["incidence_ids"]) == traced_incidence_ids
            and review["realm"] == composition["realm"]
        ):
            failures.append(
                f"{composition['composition_revision_id']}:COMPOSITION_REVIEW_TRACE_MISMATCH"
            )
        if composition["product_eligible"]:
            if not (
                review is not None
                and review["review_state"] == "FINAL"
                and review["global_coherence"] == "PASS"
                and review["decision"] == "COHERENT"
                and all(
                    by_revision[revision_id]["lifecycle_state"] == "ACTIVE"
                    and by_revision[revision_id]["review"]["global_coherence"] == "PASS"
                    and by_revision[revision_id]["product_eligible"]
                    for revision_id in traced_revision_ids
                )
            ):
                failures.append(
                    f"{composition['composition_revision_id']}:PRODUCT_COMPOSITION_TRACE_INVALID"
                )
        if not product_disposition_valid(composition):
            failures.append(
                f"{composition['composition_revision_id']}:COMPOSITION_PRODUCT_TUPLE_INVALID"
            )
    if not any(
        row["renderability"] == "PASS"
        and not row["product_eligible"]
        and coherence_review_by_id[row["global_coherence_review_id"]]["global_coherence"] == "FAIL"
        for row in fixture["compositions"]
    ):
        failures.append("RENDERABLE_INVALID_GROUP_CONTROL_FAILED")

    composition_by_revision = {
        row["composition_revision_id"]: row for row in fixture["compositions"]
    }
    realization_by_id = {
        realization["association_realization_id"]: realization
        for composition in fixture["compositions"]
        for realization in composition["association_realizations"]
    }
    for state in fixture["navigation_states"]:
        semantic = {
            key: state[key]
            for key in (
                "realm", "composition_revision_id", "nodes", "path",
                "focus_navigation_node_id", "bipartite_alternation_valid",
            )
        }
        if state["state_id"] != f"state:v3:{digest(semantic)[:24]}" or state["semantic_sha256"] != digest(semantic):
            failures.append(f"{state['state_id']}:STATE_SEMANTIC_BINDING_MISMATCH")
        if state["presentation_sha256"] != digest(state["presentation"]):
            failures.append(f"{state['state_id']}:STATE_PRESENTATION_HASH_MISMATCH")
        composition = composition_by_revision.get(state["composition_revision_id"])
        nodes = {row["navigation_node_id"]: row for row in state["nodes"]}
        if len(nodes) != len(state["nodes"]):
            failures.append(f"{state['state_id']}:NAVIGATION_NODE_ID_DUPLICATE")
        if state["focus_navigation_node_id"] not in nodes:
            failures.append(f"{state['state_id']}:NAVIGATION_FOCUS_MISSING")
        if composition is None or composition["realm"] != state["realm"]:
            failures.append(f"{state['state_id']}:NAVIGATION_COMPOSITION_REALM_MISMATCH")
            continue
        composition_realizations = {
            row["association_revision_id"]: row
            for row in composition["association_realizations"]
        }
        derived_bipartite = True
        previous_to: str | None = None
        for node in state["nodes"]:
            exactly_one = (node["concept_id"] is None) != (
                node["association_revision_id"] is None
            )
            if not exactly_one or (
                node["node_kind"] == "CONCEPT"
                and (node["concept_id"] is None or node["association_revision_id"] is not None)
            ) or (
                node["node_kind"] == "ASSOCIATION"
                and (node["concept_id"] is not None or node["association_revision_id"] is None)
            ):
                failures.append(f"{state['state_id']}:NAVIGATION_NODE_REFERENCE_SHAPE")
            if node["node_kind"] == "CONCEPT" and node["concept_id"] not in composition["composition_node_ids"]:
                failures.append(f"{state['state_id']}:NAVIGATION_CONCEPT_NOT_IN_COMPOSITION")
            if node["node_kind"] == "ASSOCIATION" and node["association_revision_id"] not in composition_realizations:
                failures.append(f"{state['state_id']}:NAVIGATION_ASSOCIATION_NOT_REALIZED")
        for step in state["path"]:
            left = nodes.get(step["from_navigation_node_id"])
            right = nodes.get(step["to_navigation_node_id"])
            if left is None or right is None:
                failures.append(f"{state['state_id']}:NAVIGATION_PATH_ENDPOINT_MISSING")
                derived_bipartite = False
                continue
            if previous_to is not None and step["from_navigation_node_id"] != previous_to:
                failures.append(f"{state['state_id']}:NAVIGATION_PATH_NOT_CONTIGUOUS")
            previous_to = step["to_navigation_node_id"]
            if left["node_kind"] == right["node_kind"]:
                failures.append(f"{state['state_id']}:BIPARTITE_ALTERNATION_FAILED")
                derived_bipartite = False
                continue
            association_node = left if left["node_kind"] == "ASSOCIATION" else right
            concept_node = left if left["node_kind"] == "CONCEPT" else right
            association = by_revision.get(association_node["association_revision_id"])
            participant = None if association is None else next(
                (
                    item for item in association["participants"]
                    if item["incidence_id"] == step["incidence_id"]
                ),
                None,
            )
            if association is None or participant is None or participant["concept_id"] != concept_node["concept_id"]:
                failures.append(f"{state['state_id']}:NAVIGATION_INCIDENCE_OWNERSHIP_MISMATCH")
        if previous_to != state["focus_navigation_node_id"]:
            failures.append(f"{state['state_id']}:NAVIGATION_TERMINAL_FOCUS_MISMATCH")
        if state["bipartite_alternation_valid"] != derived_bipartite:
            failures.append(f"{state['state_id']}:BIPARTITE_FLAG_NOT_DERIVED")
    state_by_id = {row["state_id"]: row for row in fixture["navigation_states"]}
    transition_by_id: dict[str, dict[str, Any]] = {}
    for transition in fixture["transitions"]:
        transition_semantic = {
            key: transition[key]
            for key in (
                "realm", "from_state_id", "to_state_id", "transition_kind",
                "incidence_id", "association_revision_id",
                "association_realization_id", "state_mutated",
            )
        }
        transition_id = transition["transition_id"]
        if transition_id in transition_by_id:
            failures.append(f"{transition_id}:TRANSITION_ID_DUPLICATE")
        transition_by_id[transition_id] = transition
        if (
            transition_id != f"transition:v3:{digest(transition_semantic)[:24]}"
            or transition["semantic_sha256"] != digest(transition_semantic)
        ):
            failures.append(f"{transition_id}:TRANSITION_SEMANTIC_BINDING_MISMATCH")
        source = state_by_id.get(transition["from_state_id"])
        target = state_by_id.get(transition["to_state_id"])
        if source is None or target is None:
            failures.append(f"{transition_id}:TRANSITION_ENDPOINT_MISSING")
            continue
        if not (
            source["realm"] == transition["realm"] == target["realm"]
            and transition["state_mutated"]
            is (transition["from_state_id"] != transition["to_state_id"])
        ):
            failures.append(f"{transition_id}:TRANSITION_REALM_OR_MUTATION_MISMATCH")
    selected_transition_ids: set[str] = set()
    for workflow in fixture["workflows"]:
        semantic = {
            key: workflow[key]
            for key in (
                "realm", "initial_state_id", "transition_kind", "association_revision_ids",
                "association_realization_ids", "state_ids", "transition_ids", "reachable",
            )
        }
        if workflow["workflow_id"] != f"workflow:v3:{digest(semantic)[:24]}" or workflow["semantic_sha256"] != digest(semantic):
            failures.append(f"{workflow['workflow_id']}:WORKFLOW_SEMANTIC_BINDING_MISMATCH")
        workflow_states = [state_by_id.get(state_id) for state_id in workflow["state_ids"]]
        if workflow["initial_state_id"] not in workflow["state_ids"] or any(
            row is None for row in workflow_states
        ):
            failures.append(f"{workflow['workflow_id']}:WORKFLOW_STATE_REFERENCE_MISSING")
            continue
        if len(workflow["state_ids"]) != len(set(workflow["state_ids"])):
            failures.append(f"{workflow['workflow_id']}:WORKFLOW_STATE_ID_DUPLICATE")
        if len(workflow["transition_ids"]) != len(set(workflow["transition_ids"])):
            failures.append(f"{workflow['workflow_id']}:WORKFLOW_TRANSITION_ID_DUPLICATE")
        selected_transitions = [
            transition_by_id.get(transition_id)
            for transition_id in workflow["transition_ids"]
        ]
        selected_transition_ids.update(workflow["transition_ids"])
        if any(row is None for row in selected_transitions):
            failures.append(f"{workflow['workflow_id']}:WORKFLOW_TRANSITION_REFERENCE_MISSING")
            selected_transitions = []
        state_id_set = set(workflow["state_ids"])
        if any(
            transition is not None
            and (
                transition["realm"] != workflow["realm"]
                or transition["transition_kind"] != workflow["transition_kind"]
                or transition["from_state_id"] not in state_id_set
                or transition["to_state_id"] not in state_id_set
            )
            for transition in selected_transitions
        ):
            failures.append(f"{workflow['workflow_id']}:WORKFLOW_SELECTED_TRANSITION_MISMATCH")
        workflow_compositions = {
            composition_by_revision[row["composition_revision_id"]]["composition_revision_id"]
            for row in workflow_states if row is not None
        }
        allowed_realizations = {
            realization["association_realization_id"]
            for composition_revision_id in workflow_compositions
            for realization in composition_by_revision[composition_revision_id]["association_realizations"]
        }
        if set(workflow["association_realization_ids"]) != allowed_realizations:
            failures.append(f"{workflow['workflow_id']}:WORKFLOW_REALIZATION_SET_MISMATCH")
        derived_associations = {
            realization_by_id[realization_id]["association_revision_id"]
            for realization_id in workflow["association_realization_ids"]
            if realization_id in realization_by_id
        }
        if set(workflow["association_revision_ids"]) != derived_associations:
            failures.append(f"{workflow['workflow_id']}:WORKFLOW_ASSOCIATION_SET_MISMATCH")
        reached = {workflow["initial_state_id"]}
        pending_states = [workflow["initial_state_id"]]
        while pending_states:
            current = pending_states.pop()
            for transition in selected_transitions:
                if (
                    transition is not None
                    and transition["from_state_id"] == current
                    and transition["to_state_id"] not in reached
                ):
                    reached.add(transition["to_state_id"])
                    pending_states.append(transition["to_state_id"])
        if workflow["reachable"] is not state_id_set.issubset(reached):
            failures.append(f"{workflow['workflow_id']}:WORKFLOW_REACHABILITY_NOT_DERIVED")
    for transition_id in sorted(set(transition_by_id) - selected_transition_ids):
        failures.append(f"{transition_id}:TRANSITION_UNLISTED_BY_WORKFLOW")
    workflow_by_id = {row["workflow_id"]: row for row in fixture["workflows"]}
    for export in fixture["exports"]:
        semantic = {
            key: export[key]
            for key in (
                "realm", "workflow_id", "state_id", "association_revision_ids",
                "association_realization_ids", "projection_preservation_records",
                "composition_revision_id",
                "pair_projection_policy_preserved",
            )
        }
        if export["export_id"] != f"export:v3:{digest(semantic)[:24]}" or export["semantic_sha256"] != digest(semantic):
            failures.append(f"{export['export_id']}:EXPORT_SEMANTIC_BINDING_MISMATCH")
        if export["presentation_sha256"] != digest(export["presentation"]):
            failures.append(f"{export['export_id']}:EXPORT_PRESENTATION_HASH_MISMATCH")
        workflow = workflow_by_id.get(export["workflow_id"])
        state = state_by_id.get(export["state_id"])
        composition = composition_by_revision.get(export["composition_revision_id"])
        if workflow is None or state is None or composition is None or export["state_id"] not in workflow["state_ids"]:
            failures.append(f"{export['export_id']}:EXPORT_REFERENCE_MISSING")
            continue
        expected_records = sorted(
            [
                {
                    "association_revision_id": realization["association_revision_id"],
                    "association_realization_id": realization["association_realization_id"],
                    "pair_projection_policy": by_revision[
                        realization["association_revision_id"]
                    ]["pair_projection_policy"],
                    "realization_kind": realization["realization_kind"],
                }
                for realization in composition["association_realizations"]
            ],
            key=lambda row: row["association_realization_id"],
        )
        derived_preserved = all(
            (
                row["pair_projection_policy"] == "NOT_APPLICABLE"
                and row["realization_kind"] == "PAIR_EDGE"
            )
            or (
                row["pair_projection_policy"] == "NONE"
                and row["realization_kind"] != "PAIR_EDGE"
            )
            for row in expected_records
        )
        if not (
            export["association_revision_ids"] == workflow["association_revision_ids"]
            and export["association_realization_ids"] == workflow["association_realization_ids"]
            and export["projection_preservation_records"] == expected_records
            and export["pair_projection_policy_preserved"] == derived_preserved
            and state["composition_revision_id"] == export["composition_revision_id"]
        ):
            failures.append(f"{export['export_id']}:EXPORT_TRACE_NOT_DERIVED")

    sources = {row["source_pair_id"]: row for row in fixture["v2_pair_source_fixtures"]}
    adapter = fixture["v2_pair_adapter_receipts"][0]
    target = by_revision[adapter["target_association_revision_id"]]
    source = sources.get(adapter["source_pair_id"])
    source_core = None if source is None else {
        "source_pair_id": source["source_pair_id"], "endpoints": source["endpoints"]
    }
    crosswalk_valid = source is not None and all(
        source_item["source_endpoint_id"] == crosswalk["source_endpoint_id"]
        and source_item["concept_id"] == crosswalk["target_concept_id"]
        and source_item["sense_id"] == crosswalk["target_sense_id"]
        and target_item["incidence_id"] == crosswalk["target_incidence_id"]
        and target_item["concept_id"] == crosswalk["target_concept_id"]
        and target_item["sense_id"] == crosswalk["target_sense_id"]
        for source_item, target_item, crosswalk in zip(
            source["endpoints"] if source else [], target["participants"],
            adapter["endpoint_crosswalk"], strict=True,
        )
    )
    if not (
        adapter["direction"] == "V2_PAIR_TO_V3_PAIR_ONLY" and adapter["input_arity"] == 2
        and target["association_kind"] == "PAIR"
        and target["review"]["disposition"] == "DIRECT_PAIRWISE_SUPPORT"
        and source_core is not None and source["source_pair_fixture_sha256"] == digest(source_core)
        and adapter["source_pair_fixture_sha256"] == source["source_pair_fixture_sha256"]
        and adapter["source_endpoint_ids"] == [row["source_endpoint_id"] for row in source["endpoints"]]
        and adapter["target_incidence_ids"] == [row["incidence_id"] for row in target["participants"]]
        and crosswalk_valid and not adapter["higher_order_input_allowed"]
        and not adapter["reverse_conversion_allowed"] and not adapter["semantic_claims_added"]
    ):
        failures.append("ONE_WAY_V2_PAIR_ADAPTER_FAILED")

    expected_identity_branches = {
        "UNORDERED_PERMUTATION_INVARIANT",
        "ORDERED_CONTIGUOUS_ORDINAL_SENSITIVE",
        "UNORDERED_MEANINGFUL_ROLE_PERMUTATION_INVARIANT",
        "UNORDERED_MEANINGFUL_ROLE_REASSIGNMENT_SENSITIVE",
    }
    receipts = fixture["identity_branch_test_receipts"]
    if {row["branch"] for row in receipts} != expected_identity_branches or len(receipts) != 4:
        failures.append("IDENTITY_BRANCH_RECEIPT_SET_MISMATCH")
    for receipt in receipts:
        base = receipt["base_identity_material"]
        comparison = receipt["comparison_identity_material"]
        observed = "EQUAL" if digest(base) == digest(comparison) else "NOT_EQUAL"
        if not (
            receipt["base_identity_sha256"] == digest(base)
            and receipt["comparison_identity_sha256"] == digest(comparison)
            and receipt["observed_relation"] == observed
            and receipt["expected_relation"] == observed
            and receipt["base_canonical_incidence_ids"] == incidence_ids_for_identity(base)
            and receipt["comparison_canonical_incidence_ids"] == incidence_ids_for_identity(comparison)
            and receipt["status"] == "PASS"
        ):
            failures.append(f"{receipt['test_id']}:IDENTITY_BRANCH_RECEIPT_INVALID")
        if receipt["branch"] == "ORDERED_CONTIGUOUS_ORDINAL_SENSITIVE":
            for material in (base, comparison):
                if [row["ordinal"] for row in material["participants"]] != list(
                    range(len(material["participants"]))
                ):
                    failures.append(f"{receipt['test_id']}:ORDERED_BRANCH_NOT_CONTIGUOUS")
    permuted_scope = copy.deepcopy(sparse["scope"])
    for key in SCOPE_SET_ARRAY_KEYS:
        permuted_scope[key] = list(reversed(permuted_scope[key]))
    if project_scope_identity(permuted_scope) != project_scope_identity(sparse["scope"]):
        failures.append("SCOPE_SET_PERMUTATION_CHANGED_IDENTITY")

    pending = next(row for row in associations if row["review"]["review_state"] != "FINAL")
    if pending["lifecycle_state"] == "ACTIVE" or pending["activation"]["decision"] != "REJECT":
        failures.append("PENDING_ACTIVE_REJECTION_FAILED")
    if any(row["realm"] == "PRODUCTION" for row in associations):
        failures.append("PRODUCTION_ASSOCIATION_PRESENT")
    counts = fixture["count_taxonomy"]
    if counts != reconstruct_count_taxonomy(fixture):
        failures.append("COUNT_TAXONOMY_RECONSTRUCTION_MISMATCH")
    production_counts = [
        counts["vocabulary"]["production_active_concept_count"],
        *[value for key, value in counts["associations"].items() if key.startswith("production_")],
        counts["incidence"]["production_incidence_count"],
        counts["incidence"]["implicit_projected_pair_count"],
        *[value for key, value in counts["realizations_and_compositions"].items() if key.startswith("production_")],
        *[value for key, value in counts["interaction"].items() if key.startswith("production_")],
    ]
    if any(production_counts):
        failures.append("PRODUCTION_COUNTS_NONZERO")
    if any(fixture["closure_flags"].values()):
        failures.append("CLOSURE_FLAG_TRUE")
    if not fixture["schema_negative_probe_receipts"] or not all(
        row["expected_rejected"] and row["observed_rejected"] and row["observed_error_codes"]
        for row in fixture["schema_negative_probe_receipts"]
    ):
        failures.append("NEGATIVE_PROBE_RECEIPTS_INCOMPLETE")
    return failures


def input_manifest() -> str:
    paths = [
        "schemas/trace/exploration/v2/common.schema.json",
        "schemas/trace/exploration/v2/production-read-model.schema.json",
        "docs/audits/v49-exploration-full-space-closure-round1/raw/validated-association-graph-v2.json",
        "docs/audits/v49-exploration-full-space-closure-round1/raw/canonical-composition-registry-v2.json",
        "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/higher-order-association-method-v1.json",
        "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/family-evidence-disposition-tranche-c-v1.tsv",
        "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/scoped-association-hypothesis-ledger-shard-1-v1.tsv",
        "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/adaptive-source-review-census-shard-1-v1.json",
    ]
    rows = []
    for rel in paths:
        path = REPO / rel
        if not path.is_file():
            raise FileNotFoundError(rel)
        rows.append(
            {
                "path": rel,
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
                "authority_use": (
                    "PAIR_ONLY_COMPATIBILITY_INPUT"
                    if "/v2/" in rel or "full-space-closure" in rel
                    else "ROUND16B_GOVERNED_METHOD_OR_REVIEW_INPUT"
                ),
                "mutation_policy": "READ_ONLY_PIN",
            }
        )
    return tsv_text(["path", "sha256", "bytes", "authority_use", "mutation_policy"], rows)


def fixture_expectations(fixture: dict[str, Any]) -> str:
    rows = []
    for row in fixture["control_expectations"]:
        rows.append(
            {
                "control_id": row["control_id"],
                "control_class": row["control_class"],
                "object_refs_json": json.dumps(row["object_refs"], separators=(",", ":")),
                "expected_result": row["expected_result"],
                "assertions_json": json.dumps(row["assertions"], separators=(",", ":")),
                "production_activation_authorized": "false",
                "product_eligibility_authorized": "false",
                "closure_authorized": "false",
            }
        )
    return tsv_text(
        [
            "control_id",
            "control_class",
            "object_refs_json",
            "expected_result",
            "assertions_json",
            "production_activation_authorized",
            "product_eligibility_authorized",
            "closure_authorized",
        ],
        rows,
    )


def gap_ledger() -> str:
    rows = [
        {
            "gap_id": "GAP-R16B-008-001",
            "gap_class": "PRODUCTION_IDENTITY_POPULATION",
            "status": "OPEN_CLOSURE_BLOCKING",
            "finding": "The v3 contract is populated only with synthetic controls; no historical association revision is production-active.",
            "required_action": "Complete external review and human authority before populating production association revisions.",
            "owner_phase": "EVIDENCE_REVIEW_AND_PRODUCTION_POPULATION",
        },
        {
            "gap_id": "GAP-R16B-008-002",
            "gap_class": "ROUND16A_GLOBAL_RECONCILIATION",
            "status": "OPEN_CLOSURE_BLOCKING",
            "finding": "The 58 subgraphs, 81 topology compositions, 228 production compositions, and 11 legacy compositions are not yet mapped through v3 association realizations.",
            "required_action": "Reconcile every prior object with an independently governed global-coherence decision.",
            "owner_phase": "GLOBAL_COMPOSITION_RECONCILIATION",
        },
        {
            "gap_id": "GAP-R16B-008-003",
            "gap_class": "RUNTIME_AND_DATABASE_IMPLEMENTATION",
            "status": "OPEN_CLOSURE_BLOCKING",
            "finding": "Schemas establish the additive semantic boundary but no v3 runtime, API route, PostgreSQL migration, generated production read model, or transition engine exists.",
            "required_action": "Implement forward-only v3 persistence and runtime without modifying frozen v49 or v2.",
            "owner_phase": "V3_RUNTIME_IMPLEMENTATION",
        },
        {
            "gap_id": "GAP-R16B-008-004",
            "gap_class": "PRODUCT_ARITY_BOUND",
            "status": "OPEN_CLOSURE_BLOCKING",
            "finding": "The research contract supports arity three and above, but the governed product maximum remains unaudited.",
            "required_action": "Derive and justify a product bound from product paths, accessibility, performance, and evidence rather than Round 16A precedent.",
            "owner_phase": "PRODUCT_REACHABILITY_AND_BOUND_AUDIT",
        },
        {
            "gap_id": "GAP-R16B-008-005",
            "gap_class": "INDEPENDENT_IMPLEMENTATION",
            "status": "OPEN_CHECKPOINT_GATE",
            "finding": "The primary builder must be checked by an independently implemented verifier that does not import its enumeration or validation functions.",
            "required_action": "Run and commit the separate checkpoint-008 independent verification receipt.",
            "owner_phase": "CHECKPOINT008_INDEPENDENT_VERIFICATION",
        },
    ]
    for row in rows:
        row["parent_checkpoint_sha"] = PARENT_CHECKPOINT_SHA
        row["last_reviewed_checkpoint"] = "CHECKPOINT-008"
        row["closure_authorized"] = "false"
        row["record_sha256"] = digest(row)
    return tsv_text(
        [
            "gap_id",
            "gap_class",
            "status",
            "finding",
            "required_action",
            "owner_phase",
            "parent_checkpoint_sha",
            "last_reviewed_checkpoint",
            "closure_authorized",
            "record_sha256",
        ],
        rows,
    )


def adr_text() -> str:
    return f"""# ADR 0005: First-class higher-order association contract

- Status: Accepted for additive contract implementation
- Date: 2026-08-28
- Authority: Round 16B checkpoint parent `{PARENT_CHECKPOINT_SHA}`
- Scope: `trace/exploration/v3` semantic contract only

## Context

The v2 Exploration read model is binary: it treats pair associations as edges and derives compositions from the pair graph. That model cannot preserve an evidence-supported group when some internal pairs are absent, and pair connectivity cannot prove global historical coherence. Association and composition identity are also materially different: an association is an evidence-bearing semantic object, while a composition is a visual or navigational realization.

## Decision

Introduce a parallel, additive v3 contract. A governed association has a stable identity plus append-only revision; exact bounded participant senses are represented by incidence records. Pair associations have arity two. Higher-order associations have arity three or greater and **must** set `pair_projection_policy=NONE`. A higher-order record never manufactures pair associations.

Identity material includes association kind, normalized participant concept and sense identities, meaningful order and roles, and bounded historical/contextual scope. The executable projection maps stored `/scope` to the exact `scope_identity` keys `scope_id`, `historical_case_ids`, `time_bounds`, `geographies`, `institutions`, `actors`, and `mechanisms`; every set-valued scope array is sorted before hashing. Unordered participant storage is canonical, while ordered participants retain contiguous zero-based ordinals. Four committed identity-branch receipts expose both full identity materials and independently recomputable incidence identifiers for permutation, order, and role reassignment tests. Revision material additionally binds evidence, review, authority, activation, qualifications, conflicts, and version. Semantic and presentation hashes are separate so a layout change cannot change the claim identity and a claim change cannot hide behind a rendering hash.

The normative canonicalization, field projections, aliases, array-order rules, identifier prefixes, digest truncation, and revision wrappers are machine-readable in `v3-semantic-hash-binding-contract-v1.json` and embedded in the fixture bundle. Implementations and independent verifiers must reconstruct hashes from that committed contract rather than infer them from generator code.

Governed scopes, vocabulary concepts, and bounded concept senses are first-class records. An `ACTIVE` concept or sense must be association-eligible and carry final governed authority; every association incidence resolves the exact concept, sense, and governed scope. Evidence review, global-coherence review, rights, final authority, conflict resolution, bounded-scope compatibility, synthesis validity, and product policy are separate fact-derived, fail-closed activation gates. `ACTIVE` requires nonempty evidence and locators, no unresolved conflicts, zero unsupported bridges, exact support-mode/disposition provenance, a final supporting disposition, and a passing global-coherence decision. Synthetic controls can exercise `ACTIVE` in the `SYNTHETIC_CONTROL` realm but never create a production fact or product path.

Every internal pair claim resolves an independently governed active `PAIR` revision, its exact two endpoint senses, and both parent and pair incidence identities. The invalid-clique control therefore contains six actual active pair revisions while its four-term group remains globally invalid; the sparse valid group contains only its two governed pair claims and invents no others.

Compositions contain explicit association realizations and trace each realization to an association revision. A first-class composition-coherence review binds the composition, association revisions, realization identities, incidences, final authority, and the global decision. A `PAIR` must realize as `PAIR_EDGE`; a `HIGHER_ORDER` association cannot realize as a pair edge or a participant subset. Product eligibility is allowed only when the composition review and every traced association are active, coherent, production-authorized, and product-eligible. Renderability is not evidence. Navigation derives bipartite validity from unique, referentially complete concept/association nodes and incidence-owned path steps. Workflows preserve both association revision and realization identifiers; exports derive and bind their projection-preservation records.

The only compatibility adapter is one-way: a governed v2 binary pair can be represented as a v3 `PAIR`. Higher-order inputs and reverse v3-to-v2 conversion are forbidden because either would erase or invent semantics.

## API and persistence boundary

The reserved namespace is `/api/trace/exploration/v3`. This checkpoint defines schemas but does not create routes, runtime code, database tables, or production records. Any later database work must be forward-only (v50 or later), reuse governed provenance identities, leave frozen v49 artifacts unchanged, and store association identity/revision, incidence, review, realization, composition, state, workflow, and export as distinguishable records.

## Consequences

- Scope, concept, bounded-sense, pair, higher-order, incidence, association-realization, composition-coherence-review, composition, state, workflow, and export counts are reported separately.
- Sparse or disconnected internal pair graphs are representable without projection.
- A complete pair clique can fail global coherence.
- A renderable composition can remain product-ineligible.
- Pending or non-final review cannot become active.
- Existing v2 behavior and frozen v49 artifacts remain unchanged.

## Non-authorizations

This ADR does not authorize production association activation, product eligibility, closure, v2 mutation, v49 mutation, database migration, deployment, main updates, tags, or history rewriting.
"""


def research_note_text(fixture: dict[str, Any], schema_count: int) -> str:
    counts = fixture["count_taxonomy"]
    return f"""# Round 16B v3 semantic contract and synthetic controls

Parent checkpoint: `{PARENT_CHECKPOINT_SHA}`
Source authority: `{SOURCE_SHA}`
Contract: `{CONTRACT_VERSION}`

This checkpoint establishes an additive `trace/exploration/v3` semantic boundary. It leaves every v2 file, generated v2 artifact, frozen v49 database artifact, main ref, and tag untouched. It does not implement a production runtime or activate a historical claim.

## Implemented boundary

The {schema_count} Draft 2020-12 schemas distinguish governed scopes, vocabulary concepts, bounded concept senses, pair and higher-order association revisions, participant incidences, evidence and governed review, fact-derived activation, uncertainty, first-class composition-coherence review, association realizations, compositions, bipartite navigation, workflows, exports, the normative hash-binding contract, and the one-way v2-pair adapter. Higher-order projection is explicitly `NONE`.

Association semantic hashes and presentation hashes are independently bound. Composition and association counts are separate. The input manifest pins the v2 compatibility surface and the checkpoint-007 method and review evidence used to define this contract.

The embedded and standalone machine-readable hash-binding contract freezes UTF-8 canonical JSON rules, exact semantic and presentation field projections, the executable `/scope` to `scope_identity` projection, sorted scope set arrays, canonical unordered participant storage, ordered contiguous ordinals, field aliases, revision wrappers, ID prefixes, and digest truncation for concepts, senses, associations, revisions, incidences, composition-coherence reviews, realizations, compositions, states, workflows, exports, the adapter, and its synthetic v2 source fixture. Four identity-branch receipts commit both full materials and canonical incidence IDs so an independent verifier can recompute permutation, order, and role semantics.

## Synthetic control census

- synthetic pair revisions: {counts['associations']['synthetic_pair_revision_count']}
- synthetic active pair revisions: {counts['associations']['synthetic_active_pair_revision_count']}
- synthetic higher-order revisions: {counts['associations']['synthetic_higher_order_revision_count']}
- synthetic active higher-order revisions: {counts['associations']['synthetic_active_higher_order_revision_count']}
- governed synthetic scopes: {counts['vocabulary']['synthetic_scope_count']}
- governed synthetic concepts: {counts['vocabulary']['synthetic_concept_record_count']}
- governed synthetic bounded senses: {counts['vocabulary']['synthetic_concept_sense_record_count']}
- governed active synthetic concepts: {counts['vocabulary']['synthetic_active_concept_count']}
- governed active synthetic bounded senses: {counts['vocabulary']['synthetic_active_concept_sense_count']}
- synthetic incidences: {counts['incidence']['synthetic_incidence_count']}
- synthetic association realizations: {counts['realizations_and_compositions']['synthetic_association_realization_count']}
- synthetic composition-coherence reviews: {counts['realizations_and_compositions']['synthetic_composition_coherence_review_count']}
- synthetic compositions: {counts['realizations_and_compositions']['synthetic_composition_count']}
- production active associations: {counts['associations']['production_active_association_count']}
- production product-eligible compositions: {counts['realizations_and_compositions']['production_product_eligible_composition_count']}
- implicit projected pairs: {counts['incidence']['implicit_projected_pair_count']}

The controls cover a valid arity-five hyperedge with a sparse, disconnected internal pair graph backed by two governed active pair revisions; a globally invalid four-node clique backed by all six governed active pair revisions; a bounded-sense conflict; a cross-case bundle; a genuinely governed isolated active synthetic term in a valid hyperedge; a renderable but globally invalid composition; forbidden hyperedge projection and subset realization; rejected activation under pending review; an active synthetic arity-five association whose projection policy remains `NONE`; and the one-way pair adapter. The {len(fixture['schema_negative_probe_receipts'])} negative probes exercise fail-closed evidence, locator, conflict, scope, synthesis, support-provenance, authority, product, realization, navigation, workflow, and export boundaries.

## Evidence boundary and remaining work

`ACTIVE` in this fixture means only that the synthetic validator can exercise the valid state-machine branch. All fixture records live in `SYNTHETIC_CONTROL`; their production activation, product eligibility, and closure authority are false. No historical association is promoted.

The checkpoint gap ledger keeps production identity population, Round 16A global reconciliation, v3 runtime/database implementation, and the product arity bound open. Function 3 and every named closure dimension remain false.
"""


def output_manifest_text(outputs: dict[Path, str]) -> str:
    rows = []
    for path in sorted(outputs, key=lambda item: item.as_posix()):
        content = outputs[path].encode("utf-8")
        rows.append(
            {
                "path": path.as_posix(),
                "sha256": hashlib.sha256(content).hexdigest(),
                "bytes": len(content),
                "artifact_class": (
                    "JSON_SCHEMA"
                    if path.parts[:4] == ("schemas", "trace", "exploration", "v3")
                    else "GOVERNED_DOCUMENTATION"
                    if path.suffix == ".md"
                    else "GOVERNED_MACHINE_ARTIFACT"
                ),
            }
        )
    return tsv_text(["path", "sha256", "bytes", "artifact_class"], rows)


def build_outputs() -> tuple[dict[Path, str], dict[str, Any]]:
    schemas = build_schemas()
    schema_failures = validate_schema_documents(schemas)
    if schema_failures:
        raise ValueError(f"schema validation failed: {schema_failures}")
    fixture = build_fixture()
    fixture["schema_negative_probe_receipts"] = build_negative_probe_receipts(fixture, schemas)
    hash_binding_schema_failures = validate_json_schema_instance(
        fixture["hash_binding_contract"], "hash-binding-contract.schema.json", schemas
    )
    if hash_binding_schema_failures:
        raise ValueError(f"hash-binding contract JSON Schema validation failed: {hash_binding_schema_failures}")
    fixture_schema_failures = validate_json_schema_instance(
        fixture, "semantic-contract.schema.json", schemas
    )
    if fixture_schema_failures:
        raise ValueError(f"fixture JSON Schema validation failed: {fixture_schema_failures}")
    fixture_failures = validate_fixture(fixture)
    if fixture_failures:
        raise ValueError(f"fixture validation failed: {fixture_failures}")

    counts = fixture["count_taxonomy"]
    production_active_concept_sense_count = sum(
        row["realm"] == "PRODUCTION" and row["lifecycle_state"] == "ACTIVE"
        for row in fixture["concept_senses"]
    )
    production_product_eligible_count = sum(
        row["realm"] == "PRODUCTION" and row["product_eligible"]
        for collection in (
            fixture["concepts"], fixture["concept_senses"], fixture["associations"],
            fixture["compositions"],
        )
        for row in collection
    )
    closure_true_count = sum(fixture["closure_flags"].values())

    outputs: dict[Path, str] = {path: json_text(payload) for path, payload in schemas.items()}
    fixture_path = RAW_REL / "v3-semantic-contract-fixtures-v1.json"
    hash_binding_path = RAW_REL / "v3-semantic-hash-binding-contract-v1.json"
    expectation_path = RAW_REL / "v3-semantic-contract-fixture-expectations-v1.tsv"
    input_path = RAW_REL / "v3-semantic-contract-input-manifest-v1.tsv"
    census_path = RAW_REL / "v3-semantic-contract-census-v1.json"
    gaps_path = RAW_REL / "recursive-gap-ledger-checkpoint008-v1.tsv"
    outputs[fixture_path] = json_text(fixture)
    outputs[hash_binding_path] = json_text(fixture["hash_binding_contract"])
    outputs[expectation_path] = fixture_expectations(fixture)
    outputs[input_path] = input_manifest()
    outputs[gaps_path] = gap_ledger()
    census = {
        "contract_version": CONTRACT_VERSION,
        "source_sha": SOURCE_SHA,
        "parent_checkpoint_sha": PARENT_CHECKPOINT_SHA,
        "authority_cutoff_utc": AUTHORITY_CUTOFF_UTC,
        "schema_document_count": len(schemas),
        "hash_binding_count": len(fixture["hash_binding_contract"]["bindings"]),
        "hash_binding_contract_canonical_sha256": fixture["hash_binding_contract_canonical_sha256"],
        "schema_validation_status": "PASS",
        "schema_validation_failure_count": 0,
        "fixture_json_schema_validation_status": "PASS",
        "fixture_json_schema_validation_failure_count": 0,
        "synthetic_fixture_validation_status": "PASS",
        "synthetic_fixture_validation_failure_count": 0,
        "control_count": len(fixture["control_expectations"]),
        "control_class_count": len({row["control_class"] for row in fixture["control_expectations"]}),
        "invalid_attempt_count": len(fixture["invalid_attempts"]),
        "negative_probe_count": len(fixture["schema_negative_probe_receipts"]),
        "negative_probe_rejection_count": sum(
            row["observed_rejected"] for row in fixture["schema_negative_probe_receipts"]
        ),
        "identity_branch_test_receipt_count": len(fixture["identity_branch_test_receipts"]),
        "governed_scope_count": len(fixture["scopes"]),
        "governed_concept_count": len(fixture["concepts"]),
        "governed_concept_sense_count": len(fixture["concept_senses"]),
        "composition_coherence_review_count": len(fixture["composition_coherence_reviews"]),
        "count_taxonomy": counts,
        "count_taxonomy_canonical_sha256": digest(counts),
        "count_taxonomy_reconstruction_status": "PASS",
        "production_activation_count": counts["associations"]["production_active_association_count"],
        "production_active_concept_count": counts["vocabulary"]["production_active_concept_count"],
        "production_active_concept_sense_count": production_active_concept_sense_count,
        "production_active_pending_review_count": counts["associations"]["production_active_pending_review_count"],
        "production_product_eligible_count": production_product_eligible_count,
        "implicit_pair_projection_count": counts["incidence"]["implicit_projected_pair_count"],
        "closure_true_count": closure_true_count,
        "open_closure_blocking_gap_count": 4,
        "independent_verification_status": "PENDING_SEPARATE_IMPLEMENTATION",
    }
    outputs[census_path] = json_text(census)
    outputs[ADR_REL] = adr_text()
    outputs[RESEARCH_REL / "15_V3_SEMANTIC_CONTRACT.md"] = research_note_text(fixture, len(schemas))

    manifest_path = RAW_REL / "v3-semantic-contract-output-manifest-v1.tsv"
    outputs[manifest_path] = output_manifest_text(outputs)
    manifest_rows = list(csv.DictReader(io.StringIO(outputs[manifest_path]), dialect="excel-tab"))
    aggregate_material = [
        {"path": row["path"], "sha256": row["sha256"], "bytes": int(row["bytes"])}
        for row in manifest_rows
    ]
    receipt = {
        "receipt_version": "trace-round16b-v3-semantic-contract-build-receipt-v1",
        "contract_version": CONTRACT_VERSION,
        "source_sha": SOURCE_SHA,
        "parent_checkpoint_sha": PARENT_CHECKPOINT_SHA,
        "authority_cutoff_utc": AUTHORITY_CUTOFF_UTC,
        "builder_path": "scripts/trace_round16b/build_v3_semantic_contract.py",
        "schema_document_count": len(schemas),
        "hash_binding_count": len(fixture["hash_binding_contract"]["bindings"]),
        "hash_binding_contract_path": hash_binding_path.as_posix(),
        "hash_binding_contract_canonical_sha256": fixture["hash_binding_contract_canonical_sha256"],
        "hash_binding_contract_validation": "PASS",
        "schema_syntax_and_reference_validation": "PASS",
        "fixture_json_schema_validation": "PASS",
        "fixture_semantic_validation": "PASS",
        "negative_probe_validation": "PASS",
        "negative_probe_count": len(fixture["schema_negative_probe_receipts"]),
        "negative_probe_rejection_count": sum(
            row["observed_rejected"] for row in fixture["schema_negative_probe_receipts"]
        ),
        "identity_branch_test_receipt_count": len(fixture["identity_branch_test_receipts"]),
        "control_expectation_validation": "PASS",
        "control_count": len(fixture["control_expectations"]),
        "governed_scope_count": len(fixture["scopes"]),
        "governed_concept_count": len(fixture["concepts"]),
        "governed_concept_sense_count": len(fixture["concept_senses"]),
        "composition_coherence_review_count": len(fixture["composition_coherence_reviews"]),
        "count_taxonomy_canonical_sha256": digest(counts),
        "count_taxonomy_reconstruction_status": "PASS",
        "output_manifest_path": manifest_path.as_posix(),
        "output_manifest_sha256": hashlib.sha256(outputs[manifest_path].encode("utf-8")).hexdigest(),
        "output_artifact_count_excluding_receipt": len(outputs),
        "output_aggregate_sha256": digest(aggregate_material),
        "production_activation_count": counts["associations"]["production_active_association_count"],
        "production_active_concept_count": counts["vocabulary"]["production_active_concept_count"],
        "production_active_concept_sense_count": production_active_concept_sense_count,
        "production_active_pending_review_count": counts["associations"]["production_active_pending_review_count"],
        "production_product_eligible_count": production_product_eligible_count,
        "implicit_pair_projection_count": counts["incidence"]["implicit_projected_pair_count"],
        "closure_true_count": closure_true_count,
        "v2_files_modified": 0,
        "frozen_v49_artifacts_modified": 0,
        "database_implemented": False,
        "runtime_implemented": False,
        "deployment_performed": False,
        "history_rewritten": False,
        "force_push_used": False,
        "status": "PASS",
    }
    receipt_path = RAW_REL / "v3-semantic-contract-build-receipt-v1.json"
    outputs[receipt_path] = json_text(receipt)
    return outputs, receipt


def write_or_check(outputs: dict[Path, str], check: bool) -> list[str]:
    differences: list[str] = []
    for rel, content in sorted(outputs.items(), key=lambda item: item[0].as_posix()):
        path = REPO / rel
        if check:
            if not path.is_file():
                differences.append(f"missing:{rel}")
            elif path.read_text(encoding="utf-8") != content:
                differences.append(f"content:{rel}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    return differences


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs, receipt = build_outputs()
    differences = write_or_check(outputs, args.check)
    summary = {
        "status": "PASS" if not differences else "FAIL",
        "mode": "check" if args.check else "write",
        "contract_version": CONTRACT_VERSION,
        "artifact_count": len(outputs),
        "output_aggregate_sha256": receipt["output_aggregate_sha256"],
        "differences": differences,
    }
    print(json.dumps(summary, sort_keys=True))
    return 0 if not differences else 1


if __name__ == "__main__":
    raise SystemExit(main())
