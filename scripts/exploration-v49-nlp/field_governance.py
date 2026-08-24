#!/usr/bin/env python3
"""Unified text-field roles and corpus decisions for TRACE NLP round 1."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from types import MappingProxyType
from typing import Any

from common import (
    BOILERPLATE_REGISTRY_VERSION,
    CORPUS_POLICY_VERSION,
    NORMALIZATION_VERSION,
    REGISTRY_VERSION,
    sha256_json,
)


ALLOWED_ROLES = frozenset(
    {
        "OBJECT_TITLE",
        "OBJECT_ALTERNATE_TITLE",
        "OBJECT_DESCRIPTION",
        "OBJECT_SUBJECT_TERMS",
        "OBJECT_CAPTION",
        "CREATOR_ATTRIBUTION",
        "OBJECT_TYPE_LABEL",
        "SOURCE_RECORD_TITLE",
        "SOURCE_NARRATIVE",
        "SOURCE_COLLECTION_DESCRIPTION",
        "CURATORIAL_NOTE",
        "READING_NOTE",
        "DOSSIER_TEXT",
        "REGISTRATION_TEXT",
        "PROVENANCE_TEXT",
        "RIGHTS_TEXT",
        "BOILERPLATE",
        "INTERNAL_CONTROL_TEXT",
        "UNCLASSIFIED_UNSAFE",
    }
)

ALLOWED_DECISIONS = frozenset(
    {
        "INCLUDE_TITLE_CHANNEL",
        "INCLUDE_SUBJECT_CHANNEL",
        "INCLUDE_OBJECT_DESCRIPTION_CHANNEL",
        "INCLUDE_SOURCE_NARRATIVE_DIAGNOSTIC",
        "INCLUDE_CREATOR_METADATA_ONLY",
        "INCLUDE_OBJECT_TYPE_METADATA_ONLY",
        "EXPLANATION_ONLY",
        "SOURCE_LEAKAGE_DIAGNOSTIC_ONLY",
        "HOLD",
        "EXCLUDE",
    }
)


@dataclass(frozen=True)
class FieldDecision:
    field_id: str
    source_artifact: str
    source_structure: str
    source_field: str
    primary_role: str
    public_safe: str
    rights_safe: str
    governance_decision: str
    reason: str
    prohibited_use: str
    aspect_id: str = ""
    authoritative_for_aspect: bool = False


def _field(
    field_id: str,
    source_artifact: str,
    source_structure: str,
    source_field: str,
    role: str,
    decision: str,
    reason: str,
    prohibited: str,
    *,
    public_safe: str = "TRUE",
    rights_safe: str = "TRUE",
    aspect: str = "",
    authoritative: bool = False,
) -> FieldDecision:
    return FieldDecision(
        field_id=field_id,
        source_artifact=source_artifact,
        source_structure=source_structure,
        source_field=source_field,
        primary_role=role,
        public_safe=public_safe,
        rights_safe=rights_safe,
        governance_decision=decision,
        reason=reason,
        prohibited_use=prohibited,
        aspect_id=aspect,
        authoritative_for_aspect=authoritative,
    )


FIELDS: tuple[FieldDecision, ...] = (
    _field(
        "NLP-FIELD-001",
        "frontend/generated/trace-context-v1/records.json",
        "records[].selectedRecord",
        "title",
        "OBJECT_TITLE",
        "INCLUDE_TITLE_CHANNEL",
        "Governed Context supplies exactly one public-safe title for every eligible object.",
        "Same title must not establish identity, semantic truth, or historical relation.",
        aspect="NLP_TITLE",
        authoritative=True,
    ),
    _field(
        "NLP-FIELD-002",
        "generated/public_surfaces_prefreeze_candidate_v48.json",
        "surfaces[]",
        "title",
        "OBJECT_TITLE",
        "EXCLUDE",
        "Frozen canonical mirror is reconciled to the governed Context title.",
        "Do not double-index a duplicate title source.",
    ),
    _field(
        "NLP-FIELD-003",
        "generated/public_surfaces_prefreeze_candidate_v48.json",
        "surfaces[]",
        "sourceSubjects",
        "OBJECT_SUBJECT_TERMS",
        "INCLUDE_SUBJECT_CHANNEL",
        "Source subject terms are a separate, leakage-measured aspect.",
        "Never use unmasked in metadata holdout; never enter the v1 composite before leakage review.",
        rights_safe="REVIEW_REQUIRED",
        aspect="NLP_SUBJECT",
        authoritative=True,
    ),
    _field(
        "NLP-FIELD-004",
        "generated/public_surfaces_prefreeze_candidate_v48.json",
        "surfaces[]",
        "sourceDescription",
        "SOURCE_NARRATIVE",
        "INCLUDE_SOURCE_NARRATIVE_DIAGNOSTIC",
        "Provider narrative is retained as an isolated source-leakage and retrieval diagnostic.",
        "Never treat as object description or merge into the object-semantic composite.",
        rights_safe="REVIEW_REQUIRED",
        aspect="NLP_SOURCE_NARRATIVE",
        authoritative=True,
    ),
    _field(
        "NLP-FIELD-005",
        "generated/public_surfaces_prefreeze_candidate_v48.json",
        "surfaces[]",
        "descriptionSummary",
        "CURATORIAL_NOTE",
        "EXCLUDE",
        "This seam mixes provider description, fallback notes, and editorial synthesis.",
        "Do not present as an independently governed object description.",
        rights_safe="REVIEW_REQUIRED",
    ),
    _field(
        "NLP-FIELD-006",
        "generated/public_surfaces_prefreeze_candidate_v48.json",
        "surfaces[]",
        "sourceNotes",
        "PROVENANCE_TEXT",
        "SOURCE_LEAKAGE_DIAGNOSTIC_ONLY",
        "Notes contain provider templates, identifiers, provenance, and rights language.",
        "Adds zero object-semantic affinity.",
        rights_safe="FALSE",
    ),
    _field(
        "NLP-FIELD-007",
        "frontend/generated/trace-context-v1/records.json",
        "records[].selectedRecord.rootMetadata",
        "creatorAttribution",
        "CREATOR_ATTRIBUTION",
        "INCLUDE_CREATOR_METADATA_ONLY",
        "Governed creator attribution is comparison metadata, not semantic prose.",
        "Do not add positive text affinity or infer creator intent.",
    ),
    _field(
        "NLP-FIELD-008",
        "frontend/generated/trace-context-v1/records.json",
        "records[].selectedRecord.rootMetadata",
        "objectType",
        "OBJECT_TYPE_LABEL",
        "INCLUDE_OBJECT_TYPE_METADATA_ONLY",
        "Governed object type is a proxy target and leakage label.",
        "Do not include in text input for object-type holdout.",
    ),
    _field(
        "NLP-FIELD-009",
        "generated/public_surfaces_prefreeze_candidate_v48.json",
        "surfaces[]",
        "medium",
        "INTERNAL_CONTROL_TEXT",
        "SOURCE_LEAKAGE_DIAGNOSTIC_ONLY",
        "Medium is structured archive metadata with heterogeneous display strings.",
        "Do not include in semantic text or unmasked medium holdout.",
    ),
    _field(
        "NLP-FIELD-010",
        "frontend/generated/trace-spacetime-v1/record-index.json",
        "records[]",
        "rawRegionDisplay",
        "INTERNAL_CONTROL_TEXT",
        "EXCLUDE",
        "Recorded geography is governed Spacetime metadata.",
        "Do not treat geography wording as object semantics.",
    ),
    _field(
        "NLP-FIELD-011",
        "frontend/generated/trace-context-v1/records.json",
        "records[].selectedRecord.rootMetadata",
        "sourceName",
        "SOURCE_RECORD_TITLE",
        "SOURCE_LEAKAGE_DIAGNOSTIC_ONLY",
        "Provider identity is required for source-leakage measurement and masking.",
        "Adds zero object-semantic affinity.",
    ),
    _field(
        "NLP-FIELD-012",
        "generated/public_surfaces_prefreeze_candidate_v48.json",
        "surfaces[]",
        "historicalContextNote",
        "CURATORIAL_NOTE",
        "EXPLANATION_ONLY",
        "Bounded editorial context is not source-authored object text.",
        "Do not embed, index, or use as relation evidence.",
    ),
    _field(
        "NLP-FIELD-013",
        "generated/public_surfaces_prefreeze_candidate_v48.json",
        "surfaces[]",
        "classificationRationale",
        "INTERNAL_CONTROL_TEXT",
        "EXCLUDE",
        "Classification rationale directly leaks governed labels and workflow rules.",
        "Do not index or use in proxy evaluation.",
    ),
    _field(
        "NLP-FIELD-014",
        "generated/public_surfaces_prefreeze_candidate_v48.json",
        "surfaces[]",
        "citationBasis",
        "PROVENANCE_TEXT",
        "EXPLANATION_ONLY",
        "Citation basis documents source verification rather than object meaning.",
        "Adds zero object-semantic affinity.",
    ),
    _field(
        "NLP-FIELD-015",
        "generated/public_surfaces_prefreeze_candidate_v48.json",
        "surfaces[]",
        "uncertaintyNote",
        "INTERNAL_CONTROL_TEXT",
        "EXCLUDE",
        "Workflow uncertainty text is an internal decision aid.",
        "Do not expose or index as public semantic text.",
        public_safe="FALSE",
        rights_safe="FALSE",
    ),
    _field(
        "NLP-FIELD-016",
        "generated/public_surfaces_prefreeze_candidate_v48.json",
        "surfaces[].compoundChildren[]",
        "title",
        "DOSSIER_TEXT",
        "HOLD",
        "Child-record titles describe components of a compound surface, not the parent object.",
        "Do not collapse child identity into parent semantic text.",
        rights_safe="REVIEW_REQUIRED",
    ),
    _field(
        "NLP-FIELD-017",
        "generated/public_surfaces_prefreeze_candidate_v48.json",
        "surfaces[].compoundChildren[]",
        "note",
        "DOSSIER_TEXT",
        "HOLD",
        "Child-record notes are long source/dossier narratives with separate identity.",
        "Do not merge with parent or emit in review rows.",
        rights_safe="FALSE",
    ),
    _field(
        "NLP-FIELD-018",
        "generated/public_surfaces_prefreeze_candidate_v48.json",
        "surfaces[].folders[]",
        "title",
        "INTERNAL_CONTROL_TEXT",
        "SOURCE_LEAKAGE_DIAGNOSTIC_ONLY",
        "Folder titles are governed structured labels and candidate-generation metadata.",
        "Do not treat folder membership or label text as free-text semantics.",
    ),
    _field(
        "NLP-FIELD-019",
        "generated/public_surfaces_prefreeze_candidate_v48.json",
        "folders[]",
        "scopeNote",
        "READING_NOTE",
        "EXCLUDE",
        "Container scope notes describe curated folders, not individual objects.",
        "Do not copy a container note into member documents.",
    ),
    _field(
        "NLP-FIELD-020",
        "generated/public_surfaces_prefreeze_candidate_v48.json",
        "readingNotes[]",
        "scopeNote",
        "READING_NOTE",
        "EXCLUDE",
        "Reading-note scope text mirrors the curated folder note.",
        "Do not double-index or assign to folder members.",
    ),
    _field(
        "NLP-FIELD-021",
        "generated/public_surfaces_prefreeze_candidate_v48.json",
        "registrationCards[].memberPages[]",
        "title",
        "REGISTRATION_TEXT",
        "EXCLUDE",
        "Registration-card member titles mirror public and held surface titles.",
        "Never traverse unfiltered membership or index this duplicate seam.",
    ),
    _field(
        "NLP-FIELD-022",
        "generated/public_surfaces_prefreeze_candidate_v48.json",
        "researchDossiers[].pageSequence[]",
        "title",
        "DOSSIER_TEXT",
        "EXCLUDE",
        "Dossier page titles are repeated display projections of surface titles.",
        "Do not count repeated pages as independent documents.",
    ),
    _field(
        "NLP-FIELD-023",
        "generated/public_surfaces_prefreeze_candidate_v48.json",
        "appendices[]",
        "title",
        "DOSSIER_TEXT",
        "EXCLUDE",
        "Appendix title is a duplicate display projection of the object title.",
        "Do not double-index.",
    ),
    _field(
        "NLP-FIELD-024",
        "frontend/generated/trace-context-v1/records.json",
        "records[].representations[]",
        "label",
        "INTERNAL_CONTROL_TEXT",
        "SOURCE_LEAKAGE_DIAGNOSTIC_ONLY",
        "Medium, theme, and movement labels are governed proxy targets.",
        "Do not include unmasked in metadata-holdout input.",
    ),
    _field(
        "NLP-FIELD-025",
        "frontend/generated/trace-spacetime-v1/record-index.json",
        "records[]",
        "recordedRegionDisplays",
        "INTERNAL_CONTROL_TEXT",
        "EXCLUDE",
        "Recorded region displays are governed Spacetime observations.",
        "Do not use geography wording as semantic input.",
    ),
    _field(
        "NLP-FIELD-026",
        "frontend/generated/trace-spacetime-v1/record-index.json",
        "records[].time",
        "sourceDisplay",
        "INTERNAL_CONTROL_TEXT",
        "EXCLUDE",
        "Date display is temporal metadata.",
        "Do not allow date-only semantic affinity.",
    ),
    _field(
        "NLP-FIELD-027",
        "docs/audits/v49-exploration-similarity-round1/raw/human-review-summary.json",
        "rows[]/explanationRows[]",
        "anchorTitle/candidateTitle",
        "OBJECT_TITLE",
        "EXCLUDE",
        "Round 6 titles are bounded governed-title mirrors for structured review.",
        "Do not use a prior model output packet as corpus input.",
    ),
    _field(
        "NLP-FIELD-028",
        "data/prefreeze_candidate_v48.sqlite",
        "object_metadata_rows[CITATIONS]",
        "Alternate representation",
        "PROVENANCE_TEXT",
        "HOLD",
        "One public row exists but does not expose a governed alternate-title pair.",
        "Do not label a positive pair or translation without external identity evidence.",
    ),
    _field(
        "NLP-FIELD-029",
        "data/prefreeze_candidate_v48.sqlite",
        "search_documents",
        "body",
        "INTERNAL_CONTROL_TEXT",
        "EXCLUDE",
        "Search body flattens titles, descriptions, labels, and control tokens.",
        "Do not reuse frozen Search documents as NLP semantic documents.",
        rights_safe="FALSE",
    ),
    _field(
        "NLP-FIELD-030",
        "generated/public_surfaces_prefreeze_candidate_v48.json",
        "surfaces[].tables[].rows[]",
        "label/value",
        "INTERNAL_CONTROL_TEXT",
        "EXCLUDE",
        "Display tables mirror normalized, source, rights, citation, and relation fields.",
        "Do not flatten tables or duplicate their source values.",
        rights_safe="FALSE",
    ),
    _field(
        "NLP-FIELD-031",
        "generated/public_surfaces_prefreeze_candidate_v48.json",
        "surfaces[].collectionEvidence",
        "label/boundary",
        "SOURCE_COLLECTION_DESCRIPTION",
        "SOURCE_LEAKAGE_DIAGNOSTIC_ONLY",
        "Collection evidence describes source scope and collection boundaries.",
        "Do not treat collection description as object description.",
    ),
    _field(
        "NLP-FIELD-032",
        "generated/public_surfaces_prefreeze_candidate_v48.json",
        "surfaces[].rights/image",
        "rights.label/image.licenseLabel",
        "RIGHTS_TEXT",
        "EXCLUDE",
        "Rights and license labels govern display and reuse.",
        "Adds zero object-semantic affinity.",
        rights_safe="FALSE",
    ),
    _field(
        "NLP-FIELD-033",
        "generated/public_surfaces_prefreeze_candidate_v48.json",
        "surfaces[].sourceProvenance",
        "boundary/roles/hosts",
        "PROVENANCE_TEXT",
        "EXPLANATION_ONLY",
        "Source-provenance fields describe record custody and source roles.",
        "Adds zero object-semantic affinity.",
        rights_safe="FALSE",
    ),
    _field(
        "NLP-FIELD-034",
        "data/prefreeze_candidate_v48.sqlite",
        "capture_records",
        "source_title",
        "SOURCE_RECORD_TITLE",
        "EXCLUDE",
        "Partial capture table mirrors the canonical/governed title for 3,296 public objects.",
        "Do not create a second title document or infer alternate representation.",
    ),
    _field(
        "NLP-FIELD-035",
        "data/prefreeze_candidate_v48.sqlite",
        "capture_records",
        "source_description",
        "SOURCE_NARRATIVE",
        "EXCLUDE",
        "Partial capture seam mirrors canonical sourceDescription where populated.",
        "Use canonical public-filtered sourceDescription only.",
        rights_safe="REVIEW_REQUIRED",
    ),
    _field(
        "NLP-FIELD-036",
        "data/prefreeze_candidate_v48.sqlite",
        "capture_records",
        "source_notes",
        "PROVENANCE_TEXT",
        "EXCLUDE",
        "Partial capture notes mirror canonical sourceNotes.",
        "Do not index or duplicate provenance/template text.",
        rights_safe="FALSE",
    ),
    _field(
        "NLP-FIELD-037",
        "data/prefreeze_candidate_v48.sqlite",
        "capture_records",
        "source_subjects",
        "OBJECT_SUBJECT_TERMS",
        "EXCLUDE",
        "Partial capture subject seam mirrors canonical sourceSubjects.",
        "Use only the canonical governed subject seam.",
        rights_safe="REVIEW_REQUIRED",
    ),
)


MODEL_INPUT_TOKEN_CAPS = MappingProxyType(
    {
        "NLP_TITLE": 256,
        "NLP_OBJECT_SEMANTIC_COMPOSITE": 256,
        "NLP_SUBJECT": 256,
        "NLP_SOURCE_NARRATIVE": 512,
    }
)


CORPUS_POLICY: dict[str, Any] = {
    "policyVersion": CORPUS_POLICY_VERSION,
    "registryVersion": REGISTRY_VERSION,
    "normalizationVersion": NORMALIZATION_VERSION,
    "boilerplateRegistryVersion": BOILERPLATE_REGISTRY_VERSION,
    "eligibleCohort": "research_disposition=eligible in audited migration ledger",
    "includedRoles": ["OBJECT_TITLE", "OBJECT_SUBJECT_TERMS", "SOURCE_NARRATIVE"],
    "excludedRoles": [
        "CURATORIAL_NOTE",
        "READING_NOTE",
        "DOSSIER_TEXT",
        "REGISTRATION_TEXT",
        "PROVENANCE_TEXT",
        "RIGHTS_TEXT",
        "BOILERPLATE",
        "INTERNAL_CONTROL_TEXT",
    ],
    "aspects": {
        "NLP_TITLE": ["NLP-FIELD-001"],
        "NLP_SUBJECT": ["NLP-FIELD-003"],
        "NLP_SOURCE_NARRATIVE": ["NLP-FIELD-004"],
        "NLP_OBJECT_SEMANTIC_COMPOSITE": ["NLP-FIELD-001"],
    },
    "aspectSeparation": "required",
    "sourceNarrativeIsolation": True,
    "titleOnlyComposite": True,
    "subjectCompositeAdmission": "blocked_pending_leakage_and_boilerplate_review",
    "originalTextPreservation": "hash_only_in_generated_documents; source remains immutable",
    "unicodeNormalization": "NFC",
    "compatibilityNormalization": "separate_fallback_only",
    "machineTranslation": False,
    "generatedSummaries": False,
    "historicalSpellingCorrection": False,
    "heldExclusion": "fail_closed",
    "fullCorpusCommit": False,
    "localArtifactRoot": ".local/trace-nlp-v1",
    "modelInputTemplates": "model_specific_and_revision_pinned",
    "modelInputTokenCaps": dict(MODEL_INPUT_TOKEN_CAPS),
    "modelInputTokenCapUnit": (
        "tokenizer-specific tokens in final prepared model input, including required templates "
        "and special tokens"
    ),
    "modelInputTokenCapPrecedence": "min(governed_aspect_cap, official_model_maximum)",
    "tokenizerSpecificLengthCensus": "required_before_every_model_run",
    "truncationPolicy": {
        "applicationStage": "model_input_only",
        "direction": "HEAD",
        "fullNormalizedCorpusTextPreserved": True,
        "fullNormalizedHashesPreserved": True,
        "silentCorpusOverwrite": False,
        "tokenizerIdentityAndRevisionRequired": True,
        "requiredReceiptFields": [
            "documentCount",
            "tokenCountBefore",
            "tokenCountAfter",
            "documentsTruncated",
            "tokensRemoved",
            "documentTruncationRate",
            "tokenRemovalRate",
        ],
    },
    "prohibitedInference": [
        "historical relation",
        "semantic relation",
        "probability",
        "influence",
        "creator intent",
        "importance",
        "quality",
        "canonicality",
    ],
}


def registry_rows() -> tuple[dict[str, Any], ...]:
    return tuple(asdict(field) for field in FIELDS)


def registry_sha256() -> str:
    return sha256_json({"version": REGISTRY_VERSION, "fields": registry_rows()})


def corpus_policy_sha256() -> str:
    return sha256_json(CORPUS_POLICY)


def model_input_token_caps() -> dict[str, int]:
    """Return a copy of the immutable v1 model-input caps by governed aspect."""

    return dict(MODEL_INPUT_TOKEN_CAPS)


def effective_model_input_token_cap(
    aspect_id: str,
    official_model_max_tokens: int | None = None,
) -> int:
    """Return the smaller governed aspect cap or official model maximum."""

    if aspect_id not in MODEL_INPUT_TOKEN_CAPS:
        raise KeyError(f"unregistered NLP aspect token cap: {aspect_id}")
    if official_model_max_tokens is None:
        return MODEL_INPUT_TOKEN_CAPS[aspect_id]
    if (
        isinstance(official_model_max_tokens, bool)
        or not isinstance(official_model_max_tokens, int)
        or official_model_max_tokens <= 0
    ):
        raise ValueError("official model maximum must be a positive integer")
    return min(MODEL_INPUT_TOKEN_CAPS[aspect_id], official_model_max_tokens)


def field_decision(field_id: str) -> FieldDecision:
    for field in FIELDS:
        if field.field_id == field_id:
            return field
    raise KeyError(f"unregistered NLP text field: {field_id}")


def included_aspect_fields() -> dict[str, tuple[FieldDecision, ...]]:
    result: dict[str, list[FieldDecision]] = {}
    for field in FIELDS:
        if field.aspect_id and field.authoritative_for_aspect:
            result.setdefault(field.aspect_id, []).append(field)
    return {key: tuple(value) for key, value in sorted(result.items())}


def self_test() -> dict[str, Any]:
    identifiers = [field.field_id for field in FIELDS]
    if len(identifiers) != len(set(identifiers)):
        raise AssertionError("field registry IDs are not unique")
    if any(field.primary_role not in ALLOWED_ROLES for field in FIELDS):
        raise AssertionError("field registry contains an invalid role")
    if any(field.governance_decision not in ALLOWED_DECISIONS for field in FIELDS):
        raise AssertionError("field registry contains an invalid decision")
    if any(field.primary_role == "UNCLASSIFIED_UNSAFE" for field in FIELDS):
        raise AssertionError("unclassified text fields remain")
    aspects = included_aspect_fields()
    if set(aspects) != {"NLP_TITLE", "NLP_SUBJECT", "NLP_SOURCE_NARRATIVE"}:
        raise AssertionError("authoritative aspect field set changed")
    if CORPUS_POLICY["aspects"]["NLP_OBJECT_SEMANTIC_COMPOSITE"] != ["NLP-FIELD-001"]:
        raise AssertionError("v1 composite is no longer title-only")
    expected_caps = {
        "NLP_TITLE": 256,
        "NLP_OBJECT_SEMANTIC_COMPOSITE": 256,
        "NLP_SUBJECT": 256,
        "NLP_SOURCE_NARRATIVE": 512,
    }
    if model_input_token_caps() != expected_caps:
        raise AssertionError("governed v1 model-input token caps changed")
    if effective_model_input_token_cap("NLP_SOURCE_NARRATIVE", 384) != 384:
        raise AssertionError("smaller official model maximum does not win")
    truncation = CORPUS_POLICY["truncationPolicy"]
    if (
        truncation["applicationStage"] != "model_input_only"
        or truncation["direction"] != "HEAD"
        or truncation["fullNormalizedCorpusTextPreserved"] is not True
        or truncation["fullNormalizedHashesPreserved"] is not True
        or truncation["silentCorpusOverwrite"] is not False
    ):
        raise AssertionError("v1 model-input truncation policy changed")
    return {
        "status": "PASS",
        "fieldCount": len(FIELDS),
        "classifiedFieldCount": len(FIELDS),
        "unclassifiedFieldCount": 0,
        "registryVersion": REGISTRY_VERSION,
        "registrySha256": registry_sha256(),
        "corpusPolicyVersion": CORPUS_POLICY_VERSION,
        "corpusPolicySha256": corpus_policy_sha256(),
        "modelInputTokenCaps": model_input_token_caps(),
    }


if __name__ == "__main__":
    print(json.dumps(self_test(), ensure_ascii=False, sort_keys=True))
