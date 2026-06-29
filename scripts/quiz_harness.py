#!/usr/bin/env python3
"""Curriculum-aware blueprint, validation, review, and CSV export harness."""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import random
import re
import sys
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from pathlib import Path

import evidence_pack as evidence
import request_manifest as request_spec
import custom_scope as custom_scope_spec
import document_grounding as grounding_spec


GENERIC_ITEM_TYPES = {
    "direct_recall",
    "concept_classification",
    "example_nonexample",
    "sequence_process",
    "scenario_application",
    "error_analysis",
    "evidence_reasoning",
    "comparison",
}
DECIMAL_ITEM_TYPES = {
    "direct_calculation",
    "word_problem",
    "error_analysis",
    "equivalent_expression",
    "estimation",
    "missing_number",
    "quotient_comparison",
}
ITEM_TYPES = GENERIC_ITEM_TYPES | DECIMAL_ITEM_TYPES
COGNITIVE_LEVELS = {"procedural", "knowledge", "conceptual", "application", "reasoning"}
DIFFICULTIES = {"easy", "medium", "hard"}
OPERATION_FAMILIES = {
    "natural_by_natural",
    "decimal_by_natural",
    "natural_by_decimal",
    "decimal_by_decimal",
}

FEATURES_BY_FAMILY = {
    "natural_by_natural": ["quotient_below_one", "zero_in_quotient", "appended_zero", "estimation_friendly", "decimal_quotient"],
    "decimal_by_natural": ["quotient_below_one", "zero_in_quotient", "appended_zero", "unequal_decimal_places", "estimation_friendly"],
    "natural_by_decimal": ["divisor_below_one", "quotient_larger_than_dividend", "quotient_below_one", "unequal_decimal_places", "estimation_friendly", "appended_zero"],
    "decimal_by_decimal": ["quotient_below_one", "divisor_below_one", "unequal_decimal_places", "zero_in_quotient", "appended_zero", "quotient_larger_than_dividend", "estimation_friendly"],
}

DECIMAL_COGNITIVE_BY_TYPE = {
    "direct_calculation": ["procedural", "conceptual"],
    "word_problem": ["application", "reasoning"],
    "error_analysis": ["conceptual", "reasoning"],
    "equivalent_expression": ["conceptual", "reasoning"],
    "estimation": ["conceptual", "reasoning"],
    "missing_number": ["procedural", "reasoning"],
    "quotient_comparison": ["conceptual", "reasoning"],
}

GENERIC_COGNITIVE_BY_TYPE = {
    "direct_recall": ["knowledge"],
    "concept_classification": ["conceptual", "reasoning"],
    "example_nonexample": ["conceptual", "reasoning"],
    "sequence_process": ["knowledge", "application"],
    "scenario_application": ["application", "reasoning"],
    "error_analysis": ["conceptual", "reasoning"],
    "evidence_reasoning": ["reasoning"],
    "comparison": ["conceptual", "reasoning"],
}

DECIMAL_MISCONCEPTIONS_BY_TYPE = {
    "direct_calculation": ["ignored_decimal_point", "scaled_one_operand_only", "misplaced_quotient_decimal", "arithmetic_slip"],
    "word_problem": ["unit_interpretation_error", "reversed_operands", "multiplied_instead", "incorrect_estimate"],
    "error_analysis": ["conceptual_error", "wrong_inverse_operation", "scaled_one_operand_only", "arithmetic_slip"],
    "equivalent_expression": ["scaled_one_operand_only", "wrong_inverse_operation", "ignored_decimal_point", "conceptual_error"],
    "estimation": ["incorrect_estimate", "misplaced_quotient_decimal", "conceptual_error", "compared_digits_not_values"],
    "missing_number": ["wrong_inverse_operation", "reversed_operands", "arithmetic_slip", "misplaced_quotient_decimal"],
    "quotient_comparison": ["compared_digits_not_values", "incorrect_estimate", "conceptual_error", "arithmetic_slip"],
}

GENERIC_MISCONCEPTIONS_BY_TYPE = {
    "direct_recall": ["confuses_related_terms", "partial_recall", "category_error"],
    "concept_classification": ["surface_feature_only", "overgeneralization", "category_error"],
    "example_nonexample": ["ignores_defining_condition", "surface_feature_only", "overgeneralization"],
    "sequence_process": ["sequence_error", "omits_required_step", "reverses_order"],
    "scenario_application": ["ignores_context_condition", "applies_wrong_rule", "literal_misreading"],
    "error_analysis": ["accepts_plausible_claim", "misses_counterexample", "partial_evidence"],
    "evidence_reasoning": ["irrelevant_evidence", "reverses_cause_effect", "partial_evidence"],
    "comparison": ["compares_wrong_attribute", "overgeneralization", "ignores_context_condition"],
}

DECIMAL_TYPE_PROFILE_20 = [
    "direct_calculation", "direct_calculation", "direct_calculation", "direct_calculation",
    "word_problem", "word_problem", "word_problem", "word_problem",
    "error_analysis", "error_analysis", "error_analysis",
    "equivalent_expression", "equivalent_expression", "equivalent_expression",
    "estimation", "estimation", "missing_number", "missing_number",
    "quotient_comparison", "quotient_comparison",
]

GENERIC_TYPE_PROFILE_20 = [
    "direct_recall", "direct_recall", "direct_recall",
    "concept_classification", "concept_classification", "concept_classification",
    "example_nonexample", "example_nonexample",
    "sequence_process", "sequence_process",
    "scenario_application", "scenario_application", "scenario_application", "scenario_application",
    "error_analysis", "error_analysis",
    "evidence_reasoning", "evidence_reasoning",
    "comparison", "comparison",
]

MATH_TASK_SPECS = {
    "read_write": ("direct_recall", ["knowledge"], ["exact_text"]),
    "represent": ("equivalent_expression", ["conceptual", "reasoning"], ["exact_text", "review_only"]),
    "equivalent_form": ("equivalent_expression", ["conceptual", "reasoning"], ["rational_expression", "exact_text"]),
    "compose_decompose": ("equivalent_expression", ["conceptual", "reasoning"], ["rational_expression", "exact_text"]),
    "compare": ("comparison", ["conceptual", "reasoning"], ["exact_text"]),
    "classify": ("concept_classification", ["conceptual", "reasoning"], ["exact_text"]),
    "number_line": ("example_nonexample", ["conceptual", "reasoning"], ["exact_text"]),
    "compute": ("direct_calculation", ["procedural"], ["rational_expression"]),
    "model_situation": ("word_problem", ["application", "reasoning"], ["rational_expression", "review_only"]),
    "estimate_check": ("estimation", ["conceptual", "reasoning"], ["exact_text", "review_only"]),
    "inverse_missing": ("missing_number", ["procedural", "reasoning"], ["rational_expression"]),
    "compare_strategy": ("comparison", ["conceptual", "reasoning"], ["review_only", "exact_text"]),
    "error_analysis": ("error_analysis", ["conceptual", "reasoning"], ["review_only"]),
    "explain_principle": ("evidence_reasoning", ["reasoning"], ["review_only"]),
    "extend_pattern": ("sequence_process", ["conceptual", "application"], ["exact_text", "rational_expression"]),
    "describe_rule": ("evidence_reasoning", ["conceptual", "reasoning"], ["review_only"]),
    "represent_rule": ("equivalent_expression", ["conceptual", "application"], ["exact_text", "review_only"]),
    "predict": ("scenario_application", ["application", "reasoning"], ["rational_expression", "exact_text"]),
    "compare_rules": ("comparison", ["conceptual", "reasoning"], ["exact_text", "review_only"]),
    "identify": ("concept_classification", ["knowledge", "conceptual"], ["exact_text"]),
    "example_nonexample": ("example_nonexample", ["conceptual", "reasoning"], ["exact_text"]),
    "property_reasoning": ("evidence_reasoning", ["conceptual", "reasoning"], ["review_only"]),
    "construct": ("sequence_process", ["application", "reasoning"], ["exact_text", "review_only"]),
    "transform": ("sequence_process", ["application", "reasoning"], ["exact_text", "review_only"]),
    "viewpoint_reasoning": ("evidence_reasoning", ["conceptual", "reasoning"], ["review_only"]),
    "select_unit": ("scenario_application", ["conceptual", "application"], ["exact_text"]),
    "measure_read": ("scenario_application", ["procedural", "application"], ["rational_expression", "exact_text"]),
    "convert_represent": ("equivalent_expression", ["procedural", "conceptual"], ["rational_expression", "exact_text"]),
    "classify_data": ("concept_classification", ["conceptual", "application"], ["exact_text"]),
    "read_data": ("scenario_application", ["knowledge", "application"], ["rational_expression", "exact_text"]),
    "construct_display": ("sequence_process", ["application", "reasoning"], ["exact_text", "review_only"]),
    "interpret_data": ("evidence_reasoning", ["application", "reasoning"], ["review_only", "exact_text"]),
    "compare_data": ("comparison", ["conceptual", "reasoning"], ["rational_expression", "exact_text"]),
    "critique_display": ("error_analysis", ["conceptual", "reasoning"], ["review_only"]),
    "make_decision": ("scenario_application", ["application", "reasoning"], ["review_only"]),
    "classify_likelihood": ("concept_classification", ["conceptual", "application"], ["exact_text"]),
    "compare_likelihood": ("comparison", ["conceptual", "reasoning"], ["exact_text"]),
    "represent_likelihood": ("equivalent_expression", ["conceptual", "application"], ["rational_expression", "exact_text"]),
    "predict_from_data": ("evidence_reasoning", ["application", "reasoning"], ["review_only", "exact_text"]),
}

MATH_REPRESENTATION_HINTS = {
    "compute": ("expression", "algorithm", "formula", "measurement_value", "fraction", "decimal"),
    "inverse_missing": ("expression", "table", "comparison", "correspondence"),
    "model_situation": ("word_problem", "model", "number_line", "diagram", "scenario", "concrete"),
    "estimate_check": ("number_line", "comparison", "measurement", "instrument", "verbal"),
    "error_analysis": ("algorithm", "expression", "property", "construction", "display", "sample"),
    "explain_principle": ("algorithm", "model", "property", "comparison", "verbal", "diagram"),
    "construct": ("construction", "diagram", "net", "graph", "table", "display", "movement"),
    "construct_display": ("table", "graph", "display"),
    "read_data": ("table", "graph", "display", "summary"),
    "interpret_data": ("table", "graph", "display", "summary"),
    "critique_display": ("graph", "display", "table"),
    "predict_from_data": ("sample", "table", "graph", "scenario"),
}

GIMKIT_HEADERS = ["Question", "Correct Answer", "Incorrect Answer 1", "Incorrect Answer 2 (Optional)", "Incorrect Answer 3 (Optional)"]
BLOOKET_HEADERS = [
    "Question #", "Question Text", "Answer 1", "Answer 2", "Answer 3\n(Optional)", "Answer 4\n(Optional)",
    "Time Limit (sec)\n(Max: 300 seconds)", "Correct Answer(s)\n(Only include Answer #)",
]

V2_ASSURANCE_PROFILE = "curriculum-evidence-v2"
REVIEW_CONTEXTS = {"fresh_context", "single_context_blind", "human"}
TASK_CONTRACTS = {
    "direct_recall": ("recall", {"none", "definition"}),
    "direct_calculation": ("calculate", {"expression", "measurement", "table"}),
    "concept_classification": ("classify_by_criterion", {"examples", "described_objects", "data"}),
    "example_nonexample": ("test_defining_condition", {"examples", "case", "diagram_description"}),
    "sequence_process": ("order_meaningful_steps", {"procedure", "events", "instructions"}),
    "scenario_application": ("apply_rule_to_new_case", {"scenario", "case", "observation"}),
    "word_problem": ("model_and_solve_situation", {"scenario", "case"}),
    "error_analysis": ("diagnose_specific_error", {"claim", "worked_solution", "procedure"}),
    "evidence_reasoning": ("infer_from_supplied_evidence", {"evidence", "data", "observation", "map_description", "passage"}),
    "comparison": ("compare_on_stated_attribute", {"comparison", "data", "examples", "map_description"}),
    "equivalent_expression": ("recognize_or_build_equivalence", {"expression", "model", "diagram_description"}),
    "estimation": ("estimate_and_check_reasonableness", {"expression", "scenario", "measurement"}),
    "missing_number": ("use_inverse_relation", {"expression", "table", "scenario"}),
    "quotient_comparison": ("compare_quotients_with_reason", {"expression", "comparison", "scenario"}),
}
DIFFICULTY_BASES = {
    "easy": "one explicit condition or one familiar retrieval step",
    "medium": "two linked conditions, a representation shift, or one inference",
    "hard": "multiple linked conditions, competing evidence, or justification",
}
PERFORMANCE_SUBJECTS = {"체육", "음악", "미술", "바른 생활", "슬기로운 생활", "즐거운 생활", "통합교과", "창의적 체험활동"}
SUBJECT_FAMILIES = {
    "국어": "language", "영어": "language",
    "수학": "mathematics",
    "사회": "social", "도덕": "moral",
    "과학": "science", "실과": "practical_arts",
    "체육": "performance", "음악": "performance", "미술": "performance",
    "바른 생활": "integrated", "슬기로운 생활": "integrated", "즐거운 생활": "integrated", "통합교과": "integrated",
    "창의적 체험활동": "experiential",
}
LENSES_BY_FAMILY = {
    "language": ["comprehension", "expression_choice", "language_form", "media_interpretation"],
    "mathematics": ["procedure", "representation", "relation", "justification"],
    "social": ["spatial_relation", "fact_and_judgment", "evidence", "cause_and_perspective"],
    "moral": ["situation_judgment", "rule_application", "perspective", "justification"],
    "science": ["observation_and_inference", "classification", "prediction", "procedure_and_model"],
    "practical_arts": ["safe_procedure", "design_choice", "resource_use", "digital_ethics"],
    "performance": ["concept_support", "process_choice", "observation", "reflection"],
    "integrated": ["daily_life", "inquiry", "play_and_expression", "reflection"],
    "experiential": ["school_activity_goal", "participation", "reflection", "practical_judgment"],
}
CUSTOM_ADAPTER_LENSES = {
    "general_knowledge": ["concept", "classification", "application", "evidence"],
    "technology_making": ["component_function", "code_trace", "wiring_analysis", "debugging", "safe_procedure", "design_choice"],
    "coding": ["code_trace", "debugging", "algorithm", "representation"],
    "safety_training": ["hazard_identification", "safe_procedure", "risk_judgment", "response_sequence"],
    "document_comprehension": ["retrieval", "comprehension", "evidence", "comparison"],
}
SUBJECT_STIMULUS_OVERRIDES = {
    ("social", "evidence_reasoning"): {"evidence", "data", "map_description", "passage"},
    ("social", "comparison"): {"comparison", "data", "map_description", "examples"},
    ("science", "evidence_reasoning"): {"observation", "data", "evidence"},
    ("science", "scenario_application"): {"observation", "scenario"},
    ("language", "evidence_reasoning"): {"passage", "evidence"},
    ("moral", "scenario_application"): {"scenario", "case"},
    ("practical_arts", "sequence_process"): {"procedure", "instructions"},
}


class ValidationError(Exception):
    pass


def require(condition: bool, message: str):
    if not condition:
        raise ValidationError(message)


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"Cannot read JSON {path}: {exc}") from exc


def canonical_bytes(data) -> bytes:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def data_hash(data) -> str:
    return hashlib.sha256(canonical_bytes(data)).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value).casefold()).strip()


def prompt_fingerprint(value: str) -> str:
    return re.sub(r"\d+(?:\.\d+)?", "<n>", normalize_text(value))


def distribute(values: list[str], count: int, rng: random.Random) -> list[str]:
    require(bool(values), "Cannot distribute an empty list")
    result = [values[index % len(values)] for index in range(count)]
    rng.shuffle(result)
    return result


def scaled_profile(base: list[str], count: int, rng: random.Random) -> list[str]:
    if count == 20:
        result = list(base)
        rng.shuffle(result)
        return result
    weights = Counter(base)
    slots = []
    for name, weight in weights.items():
        slots.extend([name] * max(1, round(count * weight / len(base))))
    while len(slots) < count:
        slots.append(base[len(slots) % len(base)])
    rng.shuffle(slots)
    return slots[:count]


def validate_knowledge_pack(pack: dict):
    require(isinstance(pack, dict), "knowledge pack must be an object")
    require(pack.get("schema_version") in {1, 2, 3}, "knowledge pack has unsupported schema_version")
    require(pack.get("curriculum_mode") in {"strict", "advisory", "off"}, "knowledge pack has invalid curriculum_mode")
    require(isinstance(pack.get("knowledge_pack_sha256"), str) and len(pack["knowledge_pack_sha256"]) == 64, "knowledge pack SHA-256 is missing")
    require(isinstance(pack.get("rules"), dict), "knowledge pack rules are missing")
    require(pack.get("audience_language_check") == "enforced", "elementary audience language must be enforced")
    if pack["curriculum_mode"] != "off":
        require(isinstance(pack.get("route"), dict), "curriculum-on knowledge pack needs a route")


def validate_fact_pack(fact_pack: dict | None, knowledge_pack: dict, required: bool = False) -> dict | None:
    if fact_pack is None:
        require(not required, "assurance v2 requires a sealed fact pack")
        return None
    try:
        return evidence.validate_fact_pack(fact_pack, knowledge_pack)
    except evidence.EvidenceError as exc:
        raise ValidationError(str(exc)) from exc


def validate_request_manifest(request_manifest: dict | None, required: bool = False) -> dict | None:
    if request_manifest is None:
        require(not required, "assurance v2 requires a sealed request manifest")
        return None
    try:
        return request_spec.validate_request(request_manifest)
    except request_spec.RequestError as exc:
        raise ValidationError(str(exc)) from exc


def validate_custom_scope(custom_scope: dict | None, request_manifest: dict | None, required: bool = False) -> dict | None:
    if custom_scope is None:
        require(not required, "custom scope branch requires a sealed custom-scope pack")
        return None
    try:
        return custom_scope_spec.validate_scope(custom_scope, request_manifest)
    except custom_scope_spec.ScopeError as exc:
        raise ValidationError(str(exc)) from exc


def validate_document_grounding(
    document_manifest: dict | None,
    retrieval_pack: dict | None,
    request_manifest: dict | None,
    required: bool = False,
) -> dict | None:
    if document_manifest is None or retrieval_pack is None:
        require(not required, "document-grounded branch requires document-manifest and retrieval-pack")
        return None
    try:
        grounding_spec.validate_document_manifest(document_manifest, request_manifest)
        result = grounding_spec.validate_retrieval_pack(retrieval_pack, request_manifest, document_manifest)
    except grounding_spec.GroundingError as exc:
        raise ValidationError(str(exc)) from exc
    modes = request_spec.effective_grounding_mode(request_manifest)
    coverages = {target["coverage"] for target in retrieval_pack["targets"]}
    require(not coverages & {"conflicting", "low_extraction_confidence"}, "document grounding has conflicts or low extraction confidence")
    if modes == "documents_only":
        require(coverages == {"sufficient"}, "documents_only requires sufficient coverage for every retrieval target")
    return result


def validate_fact_grounding(
    fact_pack: dict,
    request_manifest: dict,
    document_manifest: dict | None,
    retrieval_pack: dict | None,
):
    grounding_mode = request_spec.effective_grounding_mode(request_manifest)
    if grounding_mode == "verified_sources":
        return
    validate_document_grounding(document_manifest, retrieval_pack, request_manifest, required=True)
    chunks = {}
    for target in retrieval_pack["targets"]:
        for chunk in target["selected_chunks"]:
            key = (chunk["document_id"], chunk["chunk_id"], chunk["chunk_sha256"])
            chunks.setdefault(key, {"chunk": chunk, "target_ids": set()})["target_ids"].add(target["target_id"])
    document_ids = {document["id"] for document in document_manifest["documents"]}
    for fact in fact_pack["facts"]:
        source = fact["source"]
        if source.get("type") == "user_document":
            key = (source.get("document_id"), source.get("chunk_id"), source.get("chunk_sha256"))
            require(source.get("document_id") in document_ids, f"{fact['id']}: document source is unknown")
            require(key in chunks, f"{fact['id']}: document source does not resolve to a selected retrieval chunk")
            require(source.get("locator") == chunks[key]["chunk"]["locator"], f"{fact['id']}: document locator disagrees with retrieval pack")
            target_ids = source.get("retrieval_target_ids")
            require(isinstance(target_ids, list) and target_ids, f"{fact['id']}: document fact needs retrieval_target_ids")
            require(set(target_ids) <= chunks[key]["target_ids"], f"{fact['id']}: fact targets do not match the retrieval target")
        elif grounding_mode == "documents_only":
            raise ValidationError(f"{fact['id']}: documents_only forbids non-document answer facts")


def uses_v2(quiz: dict | None = None, blueprint: dict | None = None) -> bool:
    metadata = (quiz or {}).get("metadata") or {}
    return metadata.get("assurance_profile") == V2_ASSURANCE_PROFILE or (blueprint or {}).get("schema_version") == 2


def standard_codes(pack: dict) -> list[str]:
    result = []
    for standard in pack.get("rules", {}).get("standards", []):
        code = standard.get("code") if isinstance(standard, dict) else standard
        if isinstance(code, str) and re.fullmatch(r"\[[1-9][가-힣]+\d{2}-\d{2}\]", code) and code not in result:
            result.append(code)
    return result


def is_decimal_division_profile(pack: dict) -> bool:
    route = pack.get("route") or {}
    return (
        route.get("subject") == "수학"
        and route.get("grade") == 6
        and route.get("unit") == "소수의 나눗셈"
        and route.get("unit_override_applied") is True
    )


def make_decimal_blueprint(count: int, seed: int, pack: dict) -> dict:
    rng = random.Random(seed)
    item_types = scaled_profile(DECIMAL_TYPE_PROFILE_20, count, rng)
    allowed_operations = pack["rules"].get("allowed_operation_families") or sorted(OPERATION_FAMILIES)
    require(set(allowed_operations) <= OPERATION_FAMILIES, "knowledge pack contains unknown operation families")
    operations = distribute(allowed_operations, count, rng)
    difficulties = distribute(["easy", "medium", "medium", "hard"], count, rng)
    standards = standard_codes(pack)
    slots = []
    counters = Counter()
    for index, item_type in enumerate(item_types):
        operation = operations[index]
        cognitive_options = DECIMAL_COGNITIVE_BY_TYPE[item_type]
        feature_options = FEATURES_BY_FAMILY[operation]
        misconception_options = DECIMAL_MISCONCEPTIONS_BY_TYPE[item_type]
        cognitive = cognitive_options[counters[(item_type, "cognitive")] % len(cognitive_options)]
        feature = feature_options[counters[(operation, "feature")] % len(feature_options)]
        misconception = misconception_options[counters[(item_type, "misconception")] % len(misconception_options)]
        counters[(item_type, "cognitive")] += 1
        counters[(operation, "feature")] += 1
        counters[(item_type, "misconception")] += 1
        default_standard = "[6수01-14]" if operation == "natural_by_natural" else "[6수01-15]"
        slots.append({
            "id": f"q{index + 1:02d}", "standard": default_standard if default_standard in standards else standards[index % len(standards)],
            "item_type": item_type, "cognitive_level": cognitive, "operation_family": operation,
            "difficulty": difficulties[index], "number_feature": feature, "misconception_target": misconception,
        })
    return {"profile": "grade6-decimal-division-v2", "seed": seed, "count": count, "slots": slots}


def make_generic_blueprint(count: int, seed: int, pack: dict) -> dict:
    rng = random.Random(seed)
    item_types = scaled_profile(GENERIC_TYPE_PROFILE_20, count, rng)
    difficulties = distribute(["easy", "medium", "medium", "hard"], count, rng)
    standards = standard_codes(pack)
    if pack["curriculum_mode"] == "off":
        standards = ["unmapped"]
    elif not standards and pack["rules"].get("requires_teacher_scope"):
        standards = ["teacher_scope"]
    require(bool(standards), "No achievement standards are available for this routed request")
    counters = Counter()
    slots = []
    for index, item_type in enumerate(item_types):
        cognitive_options = GENERIC_COGNITIVE_BY_TYPE[item_type]
        misconception_options = GENERIC_MISCONCEPTIONS_BY_TYPE[item_type]
        cognitive = cognitive_options[counters[(item_type, "cognitive")] % len(cognitive_options)]
        misconception = misconception_options[counters[(item_type, "misconception")] % len(misconception_options)]
        counters[(item_type, "cognitive")] += 1
        counters[(item_type, "misconception")] += 1
        slots.append({
            "id": f"q{index + 1:02d}", "standard": standards[index % len(standards)], "item_type": item_type,
            "cognitive_level": cognitive, "difficulty": difficulties[index], "misconception_target": misconception,
        })
    return {"profile": "elementary-cross-subject-v1", "seed": seed, "count": count, "slots": slots}


def math_task_sequence(profile: dict, count: int, rng: random.Random) -> list[str]:
    allowed = profile.get("allowed_tasks", [])
    required = profile.get("required_tasks", [])
    require(set(required) <= set(allowed), "Math profile requires a disallowed task")
    unknown = set(allowed) - set(MATH_TASK_SPECS)
    require(not unknown, f"Math profile contains unknown tasks: {sorted(unknown)}")
    tasks = list(required[:count])
    cursor = 0
    while len(tasks) < count:
        tasks.append(allowed[cursor % len(allowed)])
        cursor += 1
    rng.shuffle(tasks)
    return tasks


def compatible_representations(task: str, representations: list[str]) -> list[str]:
    hints = MATH_REPRESENTATION_HINTS.get(task)
    if not hints:
        return representations
    compatible = [
        representation for representation in representations
        if any(hint in representation for hint in hints)
    ]
    return compatible or representations


def make_math_blueprint(count: int, seed: int, pack: dict) -> dict:
    profile = pack["rules"].get("math_profile")
    topic = pack["rules"].get("math_topic")
    require(isinstance(profile, dict) and isinstance(topic, dict), "Math topic blueprint requires math_profile and math_topic")
    standards = standard_codes(pack)
    require(bool(standards), "Math topic has no selected achievement standards")
    rng = random.Random(seed)
    tasks = math_task_sequence(profile, count, rng)
    difficulties = distribute(["easy", "medium", "medium", "hard"], count, rng)
    representations = profile["representations"]
    features = profile["features"]
    misconceptions = profile["misconceptions"]
    allowed_verification = set(profile["verification_kinds"])
    counters = Counter()
    slots = []
    for index, task in enumerate(tasks):
        item_type, cognitive_options, verification_options = MATH_TASK_SPECS[task]
        valid_verification = [kind for kind in verification_options if kind in allowed_verification]
        require(bool(valid_verification), f"Math task {task} has no verification kind allowed by profile {profile['id']}")
        cognitive = cognitive_options[counters[(task, "cognitive")] % len(cognitive_options)]
        verification_kind = valid_verification[counters[(task, "verification")] % len(valid_verification)]
        task_representations = compatible_representations(task, representations)
        representation = task_representations[counters[(task, "representation")] % len(task_representations)]
        structural_feature = features[index % len(features)]
        misconception = misconceptions[index % len(misconceptions)]
        counters[(task, "cognitive")] += 1
        counters[(task, "verification")] += 1
        counters[(task, "representation")] += 1
        slots.append({
            "id": f"q{index + 1:02d}",
            "standard": standards[index % len(standards)],
            "item_type": item_type,
            "cognitive_level": cognitive,
            "difficulty": difficulties[index],
            "math_task": task,
            "representation": representation,
            "structural_feature": structural_feature,
            "verification_kind": verification_kind,
            "misconception_target": misconception,
        })
    return {
        "profile": "elementary-math-topic-v1",
        "math_topic_id": topic["id"],
        "math_task_profile": profile["id"],
        "seed": seed,
        "count": count,
        "slots": slots,
    }


def add_v2_blueprint_fields(blueprint: dict, fact_pack: dict, request_manifest: dict, custom_scope: dict | None = None):
    facts = fact_pack["facts"]
    if blueprint["count"] >= 10:
        require(len(facts) >= 4, "Sets of ten or more require at least four distinct answer facts")
    scope_mode = request_spec.effective_scope_mode(request_manifest)
    subject = (blueprint.get("route") or {}).get("subject") or request_manifest["subject"]
    family = custom_scope["adapter"] if scope_mode == "custom" else SUBJECT_FAMILIES.get(subject, "general")
    lenses = CUSTOM_ADAPTER_LENSES.get(family) or LENSES_BY_FAMILY.get(family, ["knowledge", "application", "evidence", "reflection"])
    objectives = (custom_scope or {}).get("learning_objectives", [])
    for index, slot in enumerate(blueprint["slots"]):
        item_type = slot["item_type"]
        contract, stimulus_kinds = TASK_CONTRACTS[item_type]
        stimulus_kinds = SUBJECT_STIMULUS_OVERRIDES.get((family, item_type), stimulus_kinds)
        fact_id = facts[index % len(facts)]["id"]
        fact = facts[index % len(facts)]
        slot.update({
            "content_target": fact_id,
            "fact_ids": [fact_id],
            "task_contract": contract,
            "allowed_stimulus_kinds": sorted(stimulus_kinds),
            "difficulty_basis": DIFFICULTY_BASES[slot["difficulty"]],
            "discipline_lens": lenses[index % len(lenses)],
        })
        if objectives:
            objective_ids = {objective["id"] for objective in objectives}
            grounded_targets = fact.get("source", {}).get("retrieval_target_ids", [])
            grounded_objectives = [target for target in grounded_targets if target in objective_ids]
            slot["learning_objective_id"] = grounded_objectives[0] if grounded_objectives else objectives[index % len(objectives)]["id"]
    blueprint["schema_version"] = 2
    blueprint["assurance_profile"] = V2_ASSURANCE_PROFILE
    blueprint["fact_pack_sha256"] = fact_pack["fact_pack_sha256"]
    blueprint["subject_adapter"] = family
    if custom_scope is not None:
        blueprint["custom_scope_sha256"] = custom_scope["custom_scope_sha256"]


def make_blueprint(
    count: int,
    seed: int,
    knowledge_pack: dict,
    fact_pack: dict | None = None,
    request_manifest: dict | None = None,
    custom_scope: dict | None = None,
    document_manifest: dict | None = None,
    retrieval_pack: dict | None = None,
) -> dict:
    require(4 <= count <= 100, "Question count must be between 4 and 100")
    validate_knowledge_pack(knowledge_pack)
    if fact_pack is not None:
        validate_request_manifest(request_manifest, required=True)
        scope_mode = request_spec.effective_scope_mode(request_manifest)
        grounding_mode = request_spec.effective_grounding_mode(request_manifest)
        validate_custom_scope(custom_scope, request_manifest, required=scope_mode == "custom")
        validate_document_grounding(
            document_manifest, retrieval_pack, request_manifest,
            required=grounding_mode != "verified_sources",
        )
        validate_fact_grounding(fact_pack, request_manifest, document_manifest, retrieval_pack)
        if scope_mode == "custom" and custom_scope["safety"]["requires_current_official_verification"]:
            safety_facts = [
                fact for fact in fact_pack["facts"]
                if "safety" in fact.get("tags", []) and fact["source"].get("authority") == "official"
            ]
            require(bool(safety_facts), "custom safety policy requires at least one current official fact tagged safety")
        route = knowledge_pack.get("route") or {}
        if knowledge_pack["curriculum_mode"] != "off":
            require(request_manifest["grade"] == route.get("grade"), "request grade disagrees with knowledge route")
            require(request_manifest["subject"] == route.get("subject"), "request subject disagrees with knowledge route")
            require(request_manifest["topic"] == route.get("unit"), "request topic disagrees with knowledge route")
            require(request_manifest.get("semester") == route.get("semester"), "request semester disagrees with knowledge route")
        require(request_manifest["curriculum_mode"] == knowledge_pack["curriculum_mode"], "request curriculum mode disagrees with knowledge pack")
        require(request_manifest["question_count"] == count, "blueprint count disagrees with request manifest")
        require(request_manifest["seed"] == seed, "blueprint seed disagrees with request manifest")
        require(fact_pack.get("topic") == request_manifest["topic"], "fact pack topic disagrees with request manifest")
    if is_decimal_division_profile(knowledge_pack):
        blueprint = make_decimal_blueprint(count, seed, knowledge_pack)
    elif (knowledge_pack.get("route") or {}).get("subject") == "수학" and knowledge_pack["rules"].get("math_profile"):
        blueprint = make_math_blueprint(count, seed, knowledge_pack)
    else:
        blueprint = make_generic_blueprint(count, seed, knowledge_pack)
    blueprint.update({
        "curriculum_mode": knowledge_pack["curriculum_mode"],
        "knowledge_pack_sha256": knowledge_pack["knowledge_pack_sha256"],
        "route": knowledge_pack.get("route"),
    })
    if fact_pack is not None:
        validate_fact_pack(fact_pack, knowledge_pack)
        add_v2_blueprint_fields(blueprint, fact_pack, request_manifest, custom_scope)
        blueprint["request_manifest_sha256"] = request_manifest["request_manifest_sha256"]
        if document_manifest is not None:
            blueprint["document_manifest_sha256"] = document_manifest["document_manifest_sha256"]
            blueprint["retrieval_pack_sha256"] = retrieval_pack["retrieval_pack_sha256"]
    else:
        blueprint["schema_version"] = 1
    return blueprint


def decimal_value(value, label: str) -> Decimal:
    require(isinstance(value, str) and re.fullmatch(r"\d+(?:\.\d+)?", value) is not None, f"{label} must be a nonnegative decimal string: {value!r}")
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValidationError(f"Invalid decimal in {label}: {value}") from exc


def decimal_places(value: str) -> int:
    return len(value.partition(".")[2]) if "." in value else 0


def check_operation_family(family: str, dividend: str, divisor: str):
    expected = {
        "natural_by_natural": (False, False), "decimal_by_natural": (True, False),
        "natural_by_decimal": (False, True), "decimal_by_decimal": (True, True),
    }[family]
    require(("." in dividend, "." in divisor) == expected, f"Operation family {family} does not match {dividend}÷{divisor}")


def rational_value(value, label: str) -> Fraction:
    require(isinstance(value, str) and re.fullmatch(r"-?\d+(?:\.\d+)?(?:/-?\d+(?:\.\d+)?)?", value.strip()) is not None, f"{label} must be an integer, decimal, or fraction string")
    try:
        if "/" in value:
            numerator, denominator = value.split("/", 1)
            denominator_value = Fraction(denominator)
            require(denominator_value != 0, f"{label} has a zero denominator")
            return Fraction(numerator) / denominator_value
        return Fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValidationError(f"Invalid rational value in {label}: {value}") from exc


def evaluate_rational_expression(expression: str, label: str) -> Fraction:
    require(isinstance(expression, str) and 1 <= len(expression) <= 160, f"{label} expression length invalid")
    require(re.fullmatch(r"[0-9.()+\-*/ ]+", expression) is not None, f"{label} expression contains unsupported characters")
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ValidationError(f"{label} expression is invalid") from exc

    def visit(node) -> Fraction:
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return Fraction(str(node.value))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = visit(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            require(right != 0, f"{label} expression divides by zero")
            return left / right
        raise ValidationError(f"{label} expression uses an unsupported operation")

    return visit(tree)


def validate_metadata(
    metadata: dict,
    pack: dict,
    fact_pack: dict | None = None,
    request_manifest: dict | None = None,
    custom_scope: dict | None = None,
    document_manifest: dict | None = None,
    retrieval_pack: dict | None = None,
):
    require(isinstance(metadata, dict), "metadata must be an object")
    for field in ("title", "subject", "unit", "curriculum", "curriculum_mode", "knowledge_pack_sha256"):
        require(isinstance(metadata.get(field), str) and metadata[field].strip(), f"metadata.{field} is required")
    require(isinstance(metadata.get("grade"), int) and 1 <= metadata["grade"] <= 6, "metadata.grade must be 1..6")
    require(metadata["curriculum_mode"] == pack["curriculum_mode"], "metadata curriculum_mode disagrees with knowledge pack")
    require(metadata["knowledge_pack_sha256"] == pack["knowledge_pack_sha256"], "metadata knowledge pack hash is stale")
    if pack["curriculum_mode"] != "off":
        route = pack["route"]
        require(metadata["subject"] == route["subject"], "metadata.subject disagrees with curriculum route")
        require(metadata["grade"] == route["grade"], "metadata.grade disagrees with curriculum route")
        if route.get("unit") not in (None, ""):
            require(metadata["unit"] == route["unit"], "metadata.unit disagrees with curriculum route")
        if pack["rules"].get("requires_teacher_scope"):
            require(isinstance(metadata.get("teacher_scope"), str) and len(metadata["teacher_scope"].strip()) >= 5, "strict/advisory 창의적 체험활동 requires metadata.teacher_scope")
    if metadata.get("assurance_profile") == V2_ASSURANCE_PROFILE:
        validate_fact_pack(fact_pack, pack, required=True)
        validate_request_manifest(request_manifest, required=True)
        require(metadata.get("schema_version") == 2, "assurance v2 requires metadata.schema_version=2")
        require(metadata.get("fact_pack_sha256") == fact_pack["fact_pack_sha256"], "metadata fact pack hash is stale")
        require(metadata.get("request_manifest_sha256") == request_manifest["request_manifest_sha256"], "metadata request manifest hash is stale")
        require(metadata["grade"] == request_manifest["grade"], "metadata.grade disagrees with request manifest")
        require(metadata["subject"] == request_manifest["subject"], "metadata.subject disagrees with request manifest")
        require(metadata["unit"] == request_manifest["topic"], "metadata.unit disagrees with request manifest")
        require(metadata["curriculum_mode"] == request_manifest["curriculum_mode"], "metadata mode disagrees with request manifest")
        scope_mode = request_spec.effective_scope_mode(request_manifest)
        grounding_mode = request_spec.effective_grounding_mode(request_manifest)
        if scope_mode == "custom":
            validate_custom_scope(custom_scope, request_manifest, required=True)
            require(metadata.get("custom_scope_sha256") == custom_scope["custom_scope_sha256"], "metadata custom scope hash is stale")
        if grounding_mode != "verified_sources":
            validate_document_grounding(document_manifest, retrieval_pack, request_manifest, required=True)
            require(metadata.get("document_manifest_sha256") == document_manifest["document_manifest_sha256"], "metadata document manifest hash is stale")
            require(metadata.get("retrieval_pack_sha256") == retrieval_pack["retrieval_pack_sha256"], "metadata retrieval pack hash is stale")
        if metadata["subject"] in PERFORMANCE_SUBJECTS:
            require(metadata.get("supplementary_assessment_acknowledged") is True, "performance-centered subjects require supplementary_assessment_acknowledged=true")


def check_student_language(question: dict, pack: dict):
    qid = question.get("id", "<missing>")
    values = [("prompt", question.get("prompt", "")), ("answer_explanation", question.get("answer_explanation", ""))]
    values.extend((f"choice {index + 1}", value) for index, value in enumerate(question.get("choices", [])))
    for forbidden, replacement in pack["rules"].get("forbidden_student_terms", {}).items():
        for label, value in values:
            require(forbidden not in value, f"{qid}: student-facing {label} uses {forbidden!r}; use {replacement!r}")
    prompt = question.get("prompt", "")
    negative_markers = sum(prompt.count(marker) for marker in ("않은", "아닌", "없지", "틀리지"))
    require(negative_markers <= 1, f"{qid}: avoid double-negative or trick wording")
    grade = (pack.get("route") or {}).get("grade")
    if grade in {1, 2}:
        require(len(prompt) <= 180, f"{qid}: grade 1-2 prompt exceeds the reading-load limit")
        require(all(len(choice) <= 60 for choice in question.get("choices", [])), f"{qid}: grade 1-2 choice exceeds the reading-load limit")
        sentence_count = len(re.findall(r"[.!?。]|[까요나요]$", prompt.strip()))
        require(sentence_count <= 3, f"{qid}: grade 1-2 prompt has too many sentences")


def validate_division(question: dict, verification: dict):
    qid = question["id"]
    family = question.get("operation_family")
    require(family in OPERATION_FAMILIES, f"{qid}: division item needs a valid operation_family")
    require(question.get("number_feature") in FEATURES_BY_FAMILY[family], f"{qid}: invalid number_feature for operation_family")
    dividend_raw, divisor_raw, quotient_raw = (verification.get(key) for key in ("dividend", "divisor", "quotient"))
    dividend = decimal_value(dividend_raw, f"{qid}.dividend")
    divisor = decimal_value(divisor_raw, f"{qid}.divisor")
    quotient = decimal_value(quotient_raw, f"{qid}.quotient")
    require(divisor != 0, f"{qid}: division by zero")
    require(divisor * quotient == dividend, f"{qid}: quotient is not exact")
    require(max(dividend, divisor, quotient) <= Decimal("10000"), f"{qid}: values are unnecessarily large")
    require(max(decimal_places(dividend_raw), decimal_places(divisor_raw), decimal_places(quotient_raw)) <= 3, f"{qid}: more than three decimal places")
    check_operation_family(family, dividend_raw, divisor_raw)
    answer_role = verification.get("answer_role", "quotient")
    require(answer_role in {"dividend", "divisor", "quotient"}, f"{qid}: invalid answer_role")
    numeric_values = verification.get("choice_numeric_values")
    require(isinstance(numeric_values, list) and len(numeric_values) == 4, f"{qid}: division verification needs four choice_numeric_values")
    normalized = [decimal_value(value, f"{qid}.choice_numeric_values") for value in numeric_values]
    require(len(set(normalized)) == 4, f"{qid}: numerically equivalent choices detected")
    expected = {"dividend": dividend, "divisor": divisor, "quotient": quotient}[answer_role]
    require(normalized[question["correct_index"]] == expected, f"{qid}: marked answer does not equal verified {answer_role}")


def validate_rational_expression(question: dict, verification: dict):
    qid = question["id"]
    calculated = evaluate_rational_expression(verification.get("expression"), f"{qid}.verification")
    expected = rational_value(verification.get("expected_value"), f"{qid}.expected_value")
    require(calculated == expected, f"{qid}: rational expression result disagrees with expected_value")
    require(expected >= 0, f"{qid}: elementary rational result must be nonnegative")
    values = verification.get("choice_numeric_values")
    require(isinstance(values, list) and len(values) == 4, f"{qid}: rational_expression needs four choice_numeric_values")
    normalized = [rational_value(value, f"{qid}.choice_numeric_values") for value in values]
    require(all(value >= 0 for value in normalized), f"{qid}: elementary numeric choices must be nonnegative")
    require(len(set(normalized)) == 4, f"{qid}: numerically equivalent choices detected")
    require(normalized[question["correct_index"]] == expected, f"{qid}: marked answer does not equal expected_value")


def validate_v2_question(
    question: dict,
    pack: dict,
    fact_pack: dict,
    slot: dict | None,
    request_manifest: dict,
    custom_scope: dict | None,
):
    qid = question["id"]
    fact_ids = question.get("fact_ids")
    known_fact_ids = {fact["id"] for fact in fact_pack["facts"]}
    require(isinstance(fact_ids, list) and fact_ids, f"{qid}: assurance v2 requires fact_ids")
    require(set(fact_ids) <= known_fact_ids, f"{qid}: fact_ids contain unknown evidence")
    require(isinstance(question.get("content_target"), str) and question["content_target"].strip(), f"{qid}: content_target is required")
    contract, allowed_stimulus = TASK_CONTRACTS[question["item_type"]]
    require(question.get("task_contract") == contract, f"{qid}: task_contract does not match item_type")
    require(question.get("difficulty_basis") == DIFFICULTY_BASES[question["difficulty"]], f"{qid}: difficulty_basis does not match difficulty")
    scope_mode = request_spec.effective_scope_mode(request_manifest)
    subject = ((pack.get("route") or {}).get("subject") or request_manifest.get("subject"))
    family = custom_scope["adapter"] if scope_mode == "custom" else SUBJECT_FAMILIES.get(subject, "general")
    lenses = CUSTOM_ADAPTER_LENSES.get(family) or LENSES_BY_FAMILY.get(family, ["knowledge", "application", "evidence", "reflection"])
    require(question.get("discipline_lens") in lenses, f"{qid}: discipline_lens is invalid for {subject}")
    if scope_mode == "custom":
        require(question["standard"] == "unmapped", f"{qid}: custom scope questions must use standard=unmapped")
        objective_ids = {objective["id"] for objective in custom_scope["learning_objectives"]}
        require(question.get("learning_objective_id") in objective_ids, f"{qid}: learning objective is outside custom scope")
        student_text = " ".join([question["prompt"], question["answer_explanation"], *question["choices"]])
        for forbidden in custom_scope["terminology"]["forbidden"]:
            require(forbidden not in student_text, f"{qid}: custom-scope forbidden term {forbidden!r}")
    expected_grounding_target = question.get("learning_objective_id") if scope_mode == "custom" else question["standard"]
    for fact_id in fact_ids:
        fact = next(fact for fact in fact_pack["facts"] if fact["id"] == fact_id)
        source = fact.get("source", {})
        if source.get("type") == "user_document":
            require(expected_grounding_target in source.get("retrieval_target_ids", []), f"{qid}: document fact is not retrieved for this question's scope target")

    stimulus = question.get("stimulus")
    require(isinstance(stimulus, dict), f"{qid}: stimulus object is required")
    kind = stimulus.get("kind")
    require(kind in allowed_stimulus, f"{qid}: stimulus kind {kind!r} does not satisfy {contract}")
    text = stimulus.get("text", "")
    require(isinstance(text, str), f"{qid}: stimulus.text must be text")
    if kind == "none":
        require(not text.strip(), f"{qid}: none stimulus must have empty text")
    else:
        require(len(text.strip()) >= 5, f"{qid}: stimulus text is too short")
        require(normalize_text(text) in normalize_text(question["prompt"]), f"{qid}: stimulus text must appear in the exported prompt")

    scope_evidence = question.get("scope_evidence")
    require(isinstance(scope_evidence, str) and len(scope_evidence.strip()) >= 16, f"{qid}: scope_evidence is too short")
    if question["standard"].startswith("["):
        require(question["standard"] in scope_evidence, f"{qid}: scope_evidence must cite the mapped standard")
    proof = question.get("answer_proof")
    require(isinstance(proof, str) and len(proof.strip()) >= 16, f"{qid}: answer_proof is too short")
    require(all(fact_id in proof for fact_id in fact_ids), f"{qid}: answer_proof must cite every fact_id")

    if slot:
        require(kind in set(slot.get("allowed_stimulus_kinds", [])), f"{qid}: stimulus kind violates blueprint contract")


def validate_question(
    question: dict,
    pack: dict,
    slot: dict | None = None,
    fact_pack: dict | None = None,
    assurance_v2: bool = False,
    request_manifest: dict | None = None,
    custom_scope: dict | None = None,
) -> list[str]:
    qid = question.get("id", "<missing>")
    for field in ("id", "standard", "item_type", "cognitive_level", "difficulty", "prompt", "choices", "correct_index", "answer_explanation", "verification", "distractors", "time_limit"):
        require(field in question, f"{qid}: missing {field}")
    require(question["item_type"] in ITEM_TYPES, f"{qid}: invalid item_type")
    require(question["cognitive_level"] in COGNITIVE_LEVELS, f"{qid}: invalid cognitive_level")
    require(question["difficulty"] in DIFFICULTIES, f"{qid}: invalid difficulty")
    math_profile = None if is_decimal_division_profile(pack) else pack.get("rules", {}).get("math_profile")
    if math_profile:
        task = question.get("math_task")
        require(task in math_profile["allowed_tasks"], f"{qid}: invalid math_task for selected topic")
        require(question.get("representation") in math_profile["representations"], f"{qid}: invalid representation for selected math topic")
        require(question.get("structural_feature") in math_profile["features"], f"{qid}: invalid structural_feature for selected math topic")
        require(task in MATH_TASK_SPECS and question["item_type"] == MATH_TASK_SPECS[task][0], f"{qid}: item_type is incompatible with math_task")

    warnings = []
    allowed_standards = set(standard_codes(pack))
    standard = question["standard"]
    if pack["curriculum_mode"] == "strict":
        if allowed_standards:
            require(standard in allowed_standards, f"{qid}: standard is outside routed grade-band scope")
        else:
            require(standard == "teacher_scope", f"{qid}: curriculum area requires teacher_scope mapping")
    elif pack["curriculum_mode"] == "advisory" and allowed_standards and standard not in allowed_standards:
        warnings.append(f"{qid}: standard {standard} is outside routed grade-band scope")

    prompt = question["prompt"]
    require(isinstance(prompt, str) and 5 <= len(prompt) <= 500, f"{qid}: prompt length invalid")
    require(not prompt.lstrip().startswith(("=", "+", "-", "@")), f"{qid}: unsafe CSV-leading character")
    choices = question["choices"]
    require(isinstance(choices, list) and len(choices) == 4, f"{qid}: exactly four choices required")
    require(all(isinstance(choice, str) and choice.strip() for choice in choices), f"{qid}: choices must be nonempty strings")
    require(all(len(choice) <= 200 for choice in choices), f"{qid}: a choice exceeds the skill's 200-character import safety limit")
    require(len({normalize_text(choice) for choice in choices}) == 4, f"{qid}: duplicate choice text")
    require(isinstance(question["correct_index"], int) and 0 <= question["correct_index"] < 4, f"{qid}: invalid correct_index")
    require(isinstance(question["answer_explanation"], str) and len(question["answer_explanation"].strip()) >= 8, f"{qid}: explanation too short")
    require(isinstance(question["time_limit"], int) and 5 <= question["time_limit"] <= 300, f"{qid}: time_limit must be 5..300")
    check_student_language(question, pack)

    verification = question["verification"]
    require(isinstance(verification, dict), f"{qid}: verification must be an object")
    kind = verification.get("kind")
    require(kind in {"division", "rational_expression", "exact_text", "review_only"}, f"{qid}: invalid verification.kind")
    if math_profile:
        require(kind in math_profile["verification_kinds"], f"{qid}: verification.kind is not allowed by selected math topic")
    if kind == "division":
        validate_division(question, verification)
    elif kind == "rational_expression":
        validate_rational_expression(question, verification)
    elif kind == "exact_text":
        require(verification.get("expected_answer") == choices[question["correct_index"]], f"{qid}: exact_text expected_answer disagrees with marked choice")

    distractors = question["distractors"]
    require(isinstance(distractors, list) and len(distractors) == 3, f"{qid}: three distractor records required")
    expected_indices = set(range(4)) - {question["correct_index"]}
    actual_indices = set()
    for distractor in distractors:
        require(isinstance(distractor, dict), f"{qid}: invalid distractor record")
        actual_indices.add(distractor.get("choice_index"))
        require(isinstance(distractor.get("misconception"), str) and distractor["misconception"].strip(), f"{qid}: distractor misconception is required")
        require(isinstance(distractor.get("reason"), str) and len(distractor["reason"].strip()) >= 5, f"{qid}: distractor reason too short")
        if assurance_v2:
            require(isinstance(distractor.get("why_wrong"), str) and len(distractor["why_wrong"].strip()) >= 10, f"{qid}: assurance v2 requires why_wrong for every distractor")
    require(actual_indices == expected_indices, f"{qid}: distractor indices do not cover all incorrect choices")

    if assurance_v2:
        validate_v2_question(question, pack, fact_pack, slot, request_manifest, custom_scope)

    if slot:
        for field, value in slot.items():
            if field == "misconception_target":
                require(value in {item["misconception"] for item in distractors}, f"{qid}: blueprint misconception target not used")
            elif field == "verification_kind":
                require(verification.get("kind") == value, f"{qid}: does not follow blueprint verification_kind")
            elif field in {"allowed_stimulus_kinds"}:
                continue
            elif field not in {"route"}:
                require(question.get(field) == value, f"{qid}: does not follow blueprint field {field}")
    return warnings


def validate_distribution(questions: list[dict], blueprint: dict | None, pack: dict) -> dict:
    count = len(questions)
    type_counts = Counter(question["item_type"] for question in questions)
    cognitive_counts = Counter(question["cognitive_level"] for question in questions)
    if count >= 10:
        direct = type_counts["direct_calculation"] + type_counts["direct_recall"]
        require(direct / count <= 0.30, "Direct calculation/recall items exceed 30%")
        require(len(type_counts) >= 4, "Use at least four item types")
        require(len(cognitive_counts) >= 3, "Use at least three cognitive levels")
    fingerprints = Counter(prompt_fingerprint(question["prompt"]) for question in questions)
    repeated = [fingerprint for fingerprint, value in fingerprints.items() if value > 2]
    require(not repeated, f"Prompt templates repeated more than twice: {repeated[:3]}")
    choice_sets = Counter(tuple(sorted(normalize_text(choice) for choice in question["choices"])) for question in questions)
    repeated_choice_sets = [value for value, occurrences in choice_sets.items() if occurrences > 1]
    require(not repeated_choice_sets, "The same answer-choice set is reused across questions")

    result = {
        "item_types": dict(sorted(type_counts.items())),
        "cognitive_levels": dict(sorted(cognitive_counts.items())),
        "difficulties": dict(sorted(Counter(question["difficulty"] for question in questions).items())),
    }
    math_profile = pack.get("rules", {}).get("math_profile")
    math_tasks = [question.get("math_task") for question in questions]
    if math_profile and all(math_tasks):
        task_counts = Counter(math_tasks)
        direct = type_counts["direct_calculation"] + type_counts["direct_recall"]
        if count >= 10:
            require(direct / count <= math_profile["max_direct_ratio"], "Math profile direct-item ratio exceeded")
            required_tasks = set(math_profile["required_tasks"])
            require(required_tasks <= set(task_counts), f"Math profile required tasks missing: {sorted(required_tasks - set(task_counts))}")
        result["math_tasks"] = dict(sorted(task_counts.items()))
        result["representations"] = dict(sorted(Counter(question.get("representation") for question in questions).items()))
        result["structural_features"] = dict(sorted(Counter(question.get("structural_feature") for question in questions).items()))
    if all(question.get("content_target") for question in questions):
        content_counts = Counter(question["content_target"] for question in questions)
        if count >= 10:
            require(len(content_counts) >= 4, "Use at least four content targets for sets of ten or more")
        result["content_targets"] = dict(sorted(content_counts.items()))
    operations = [question.get("operation_family") for question in questions]
    if all(operations):
        operation_counts = Counter(operations)
        expected_families = len({slot.get("operation_family") for slot in (blueprint or {}).get("slots", []) if slot.get("operation_family")})
        if count >= 10:
            require(len(operation_counts) >= min(3, expected_families), "Use all operation-family breadth required by the blueprint")
        result["operation_families"] = dict(sorted(operation_counts.items()))
    return result


def validate_quiz(
    quiz: dict,
    pack: dict,
    blueprint: dict | None = None,
    fact_pack: dict | None = None,
    request_manifest: dict | None = None,
    custom_scope: dict | None = None,
    document_manifest: dict | None = None,
    retrieval_pack: dict | None = None,
):
    validate_knowledge_pack(pack)
    assurance_v2 = uses_v2(quiz, blueprint)
    if assurance_v2:
        require((quiz.get("metadata") or {}).get("assurance_profile") == V2_ASSURANCE_PROFILE, "v2 blueprint requires v2 canonical metadata")
    validate_fact_pack(fact_pack, pack, required=assurance_v2)
    validate_request_manifest(request_manifest, required=assurance_v2)
    if assurance_v2:
        scope_mode = request_spec.effective_scope_mode(request_manifest)
        grounding_mode = request_spec.effective_grounding_mode(request_manifest)
        validate_custom_scope(custom_scope, request_manifest, required=scope_mode == "custom")
        validate_document_grounding(document_manifest, retrieval_pack, request_manifest, required=grounding_mode != "verified_sources")
        validate_fact_grounding(fact_pack, request_manifest, document_manifest, retrieval_pack)
        if scope_mode == "custom" and custom_scope["safety"]["requires_current_official_verification"]:
            require(any(
                "safety" in fact.get("tags", []) and fact["source"].get("authority") == "official"
                for fact in fact_pack["facts"]
            ), "custom safety policy requires at least one current official fact tagged safety")
    validate_metadata(
        quiz.get("metadata"), pack, fact_pack, request_manifest,
        custom_scope, document_manifest, retrieval_pack,
    )
    questions = quiz.get("questions")
    require(isinstance(questions, list) and 4 <= len(questions) <= 100, "questions must contain 4..100 items")
    if assurance_v2:
        require(len(questions) == request_manifest["question_count"], "question count disagrees with request manifest")
    ids = [question.get("id") for question in questions]
    require(len(set(ids)) == len(ids), "Question IDs must be unique")
    prompts = [normalize_text(question.get("prompt", "")) for question in questions]
    require(len(set(prompts)) == len(prompts), "Question prompts must be unique")

    slots_by_id = None
    if blueprint is not None:
        require(blueprint.get("count") == len(questions), "Blueprint count does not match questions")
        require(blueprint.get("knowledge_pack_sha256") == pack["knowledge_pack_sha256"], "Blueprint knowledge pack hash is stale")
        if assurance_v2:
            require(blueprint.get("schema_version") == 2, "assurance v2 requires blueprint schema_version=2")
            require(blueprint.get("fact_pack_sha256") == fact_pack["fact_pack_sha256"], "Blueprint fact pack hash is stale")
            require(blueprint.get("request_manifest_sha256") == request_manifest["request_manifest_sha256"], "Blueprint request manifest hash is stale")
            if request_spec.effective_scope_mode(request_manifest) == "custom":
                require(blueprint.get("custom_scope_sha256") == custom_scope["custom_scope_sha256"], "Blueprint custom scope hash is stale")
            if request_spec.effective_grounding_mode(request_manifest) != "verified_sources":
                require(blueprint.get("document_manifest_sha256") == document_manifest["document_manifest_sha256"], "Blueprint document manifest hash is stale")
                require(blueprint.get("retrieval_pack_sha256") == retrieval_pack["retrieval_pack_sha256"], "Blueprint retrieval pack hash is stale")
        slots = blueprint.get("slots")
        require(isinstance(slots, list) and len(slots) == len(questions), "Invalid blueprint slots")
        slots_by_id = {slot["id"]: slot for slot in slots}
        require(set(ids) == set(slots_by_id), "Question IDs do not match blueprint slots")

    warnings = []
    for question in questions:
        warnings.extend(validate_question(
            question,
            pack,
            slots_by_id.get(question["id"]) if slots_by_id else None,
            fact_pack,
            assurance_v2,
            request_manifest,
            custom_scope,
        ))
    distribution = validate_distribution(questions, blueprint, pack)
    return {"question_count": len(questions), "distribution": distribution, "warnings": warnings, "quiz_sha256": data_hash(quiz)}


def review_layout(quiz: dict) -> tuple[list[dict], dict[str, list[int]]]:
    seed = int(data_hash(quiz)[:16], 16)
    rng = random.Random(seed)
    questions = list(quiz["questions"])
    rng.shuffle(questions)
    permutations = {}
    for question in questions:
        indices = list(range(4))
        rng.shuffle(indices)
        permutations[question["id"]] = indices
    return questions, permutations


def standard_statement(pack: dict, code: str) -> str:
    for standard in pack.get("rules", {}).get("standards", []):
        if isinstance(standard, dict) and standard.get("code") == code:
            return standard.get("statement", "")
    return "teacher-defined scope" if code == "teacher_scope" else ""


def make_review_packet(
    quiz: dict,
    pack: dict,
    fact_pack: dict | None = None,
    request_manifest: dict | None = None,
    custom_scope: dict | None = None,
    document_manifest: dict | None = None,
    retrieval_pack: dict | None = None,
) -> dict:
    validation = validate_quiz(
        quiz, pack, fact_pack=fact_pack, request_manifest=request_manifest,
        custom_scope=custom_scope, document_manifest=document_manifest, retrieval_pack=retrieval_pack,
    )
    if uses_v2(quiz):
        questions, permutations = review_layout(quiz)
        items = []
        for question in questions:
            order = permutations[question["id"]]
            items.append({
                "id": question["id"],
                "prompt": question["prompt"],
                "choices": [question["choices"][index] for index in order],
                "selected_index": None,
                "reasoning": "",
                "why_others_wrong": {},
                "ambiguity_flag": None,
            })
        packet = {
            "schema_version": 2,
            "review_kind": "answer_blind",
            "source_quiz_sha256": validation["quiz_sha256"],
            "knowledge_pack_sha256": pack["knowledge_pack_sha256"],
            "fact_pack_sha256": fact_pack["fact_pack_sha256"],
            "request_manifest_sha256": request_manifest["request_manifest_sha256"],
            "review_context": None,
            "reviewer_id": "",
            "reviewed_at": "",
            "instructions": "정답·성취기준을 보지 말고 섞인 선택지로 다시 푸세요. 선택하지 않은 세 답이 틀린 이유와 모호성 여부를 기록하세요.",
            "questions": items,
        }
        if custom_scope is not None:
            packet["custom_scope_sha256"] = custom_scope["custom_scope_sha256"]
        if document_manifest is not None:
            packet["document_manifest_sha256"] = document_manifest["document_manifest_sha256"]
            packet["retrieval_pack_sha256"] = retrieval_pack["retrieval_pack_sha256"]
        return packet

    questions = [{
        "id": question["id"], "standard": question["standard"], "item_type": question["item_type"],
        "prompt": question["prompt"], "choices": question["choices"], "selected_index": None,
        "scope_pass": None, "reasoning": "",
    } for question in quiz["questions"]]
    return {
        "source_quiz_sha256": validation["quiz_sha256"],
        "knowledge_pack_sha256": pack["knowledge_pack_sha256"],
        "curriculum_mode": pack["curriculum_mode"],
        "instructions": "정답 표시를 보지 말고 각 문항을 다시 풀어 selected_index, scope_pass, reasoning을 채우세요.",
        "questions": questions,
    }


def make_scope_review_packet(
    quiz: dict,
    pack: dict,
    fact_pack: dict,
    request_manifest: dict,
    custom_scope: dict | None = None,
    document_manifest: dict | None = None,
    retrieval_pack: dict | None = None,
) -> dict:
    validation = validate_quiz(
        quiz, pack, fact_pack=fact_pack, request_manifest=request_manifest,
        custom_scope=custom_scope, document_manifest=document_manifest, retrieval_pack=retrieval_pack,
    )
    require(uses_v2(quiz), "scope review packets require assurance v2")
    subject = quiz["metadata"]["subject"]
    scope_mode = request_spec.effective_scope_mode(request_manifest)
    subject_adapter = custom_scope["adapter"] if scope_mode == "custom" else SUBJECT_FAMILIES.get(subject, "general")
    packet = {
        "schema_version": 2,
        "review_kind": "curriculum_scope",
        "source_quiz_sha256": validation["quiz_sha256"],
        "knowledge_pack_sha256": pack["knowledge_pack_sha256"],
        "fact_pack_sha256": fact_pack["fact_pack_sha256"],
        "request_manifest_sha256": request_manifest["request_manifest_sha256"],
        "review_context": None,
        "reviewer_id": "",
        "reviewed_at": "",
        "request_constraints": list(request_manifest["teacher_constraints"]),
        "instructions": "정답 검토와 별도로 성취기준 범위, 주제 범위, 학생 용어를 확인하세요.",
        "questions": [{
            "id": question["id"],
            "standard": question["standard"],
            "standard_statement": standard_statement(pack, question["standard"]),
            "learning_objective_id": question.get("learning_objective_id"),
            "learning_objective": next((item["description"] for item in (custom_scope or {}).get("learning_objectives", []) if item["id"] == question.get("learning_objective_id")), None),
            "content_target": question["content_target"],
            "discipline_lens": question["discipline_lens"],
            "subject_adapter": subject_adapter,
            "fact_ids": question["fact_ids"],
            "prompt": question["prompt"],
            "choices": question["choices"],
            "scope_evidence": question["scope_evidence"],
            "scope_pass": None,
            "terminology_pass": None,
            "constraints_pass": None,
            "discipline_pass": None,
            "discipline_reasoning": "",
            "custom_scope_pass": None if scope_mode == "curriculum" else None,
            "audience_pass": None if scope_mode == "curriculum" else None,
            "safety_pass": None if scope_mode == "curriculum" else None,
            "reasoning": "",
        } for question in quiz["questions"]],
    }
    if custom_scope is not None:
        packet["custom_scope_sha256"] = custom_scope["custom_scope_sha256"]
        packet["custom_scope_summary"] = {
            "topic": custom_scope["topic"],
            "adapter": custom_scope["adapter"],
            "in_scope": custom_scope["in_scope"],
            "out_of_scope": custom_scope["out_of_scope"],
            "safety": custom_scope["safety"],
        }
    if document_manifest is not None:
        packet["document_manifest_sha256"] = document_manifest["document_manifest_sha256"]
        packet["retrieval_pack_sha256"] = retrieval_pack["retrieval_pack_sha256"]
    return packet


def validate_review_header(
    review: dict,
    quiz: dict,
    pack: dict,
    fact_pack: dict,
    request_manifest: dict,
    expected_kind: str,
    custom_scope: dict | None = None,
    document_manifest: dict | None = None,
    retrieval_pack: dict | None = None,
):
    require(review.get("schema_version") == 2, "v2 review schema_version must be 2")
    require(review.get("review_kind") == expected_kind, f"expected {expected_kind} review packet")
    require(review.get("source_quiz_sha256") == data_hash(quiz), "Review packet is stale")
    require(review.get("knowledge_pack_sha256") == pack["knowledge_pack_sha256"], "Review knowledge pack is stale")
    require(review.get("fact_pack_sha256") == fact_pack["fact_pack_sha256"], "Review fact pack is stale")
    require(review.get("request_manifest_sha256") == request_manifest["request_manifest_sha256"], "Review request manifest is stale")
    if request_spec.effective_scope_mode(request_manifest) == "custom":
        require(review.get("custom_scope_sha256") == custom_scope["custom_scope_sha256"], "Review custom scope is stale")
    if request_spec.effective_grounding_mode(request_manifest) != "verified_sources":
        require(review.get("document_manifest_sha256") == document_manifest["document_manifest_sha256"], "Review document manifest is stale")
        require(review.get("retrieval_pack_sha256") == retrieval_pack["retrieval_pack_sha256"], "Review retrieval pack is stale")
    require(review.get("review_context") in REVIEW_CONTEXTS, "review_context must describe the actual review context")
    require(isinstance(review.get("reviewer_id"), str) and len(review["reviewer_id"].strip()) >= 3, "reviewer_id is required")
    require(isinstance(review.get("reviewed_at"), str) and review["reviewed_at"].strip(), "reviewed_at is required")


def validate_review(
    quiz: dict,
    review: dict,
    pack: dict,
    fact_pack: dict | None = None,
    request_manifest: dict | None = None,
    custom_scope: dict | None = None,
    document_manifest: dict | None = None,
    retrieval_pack: dict | None = None,
) -> list[str]:
    if uses_v2(quiz):
        validate_fact_pack(fact_pack, pack, required=True)
        validate_request_manifest(request_manifest, required=True)
        validate_custom_scope(custom_scope, request_manifest, required=request_spec.effective_scope_mode(request_manifest) == "custom")
        validate_document_grounding(document_manifest, retrieval_pack, request_manifest, required=request_spec.effective_grounding_mode(request_manifest) != "verified_sources")
        validate_review_header(
            review, quiz, pack, fact_pack, request_manifest, "answer_blind",
            custom_scope, document_manifest, retrieval_pack,
        )
        items = review.get("questions")
        require(isinstance(items, list), "review.questions must be a list")
        by_id = {item.get("id"): item for item in items}
        require(len(by_id) == len(quiz["questions"]), "Review question count mismatch")
        _, permutations = review_layout(quiz)
        for question in quiz["questions"]:
            qid = question["id"]
            require(qid in by_id, f"Review missing {qid}")
            item = by_id[qid]
            order = permutations[qid]
            expected_choices = [question["choices"][index] for index in order]
            require(item.get("choices") == expected_choices and item.get("prompt") == question["prompt"], f"{qid}: blind review content was changed")
            selected = item.get("selected_index")
            require(isinstance(selected, int) and 0 <= selected < 4, f"{qid}: invalid blind selected_index")
            require(order[selected] == question["correct_index"], f"{qid}: blind answer disagrees with marked answer")
            require(isinstance(item.get("reasoning"), str) and len(item["reasoning"].strip()) >= 12, f"{qid}: blind reasoning too short")
            require(item.get("ambiguity_flag") is False, f"{qid}: ambiguity must be explicitly cleared")
            why = item.get("why_others_wrong")
            require(isinstance(why, dict), f"{qid}: why_others_wrong must be an object")
            expected_keys = {str(index) for index in range(4) if index != selected}
            require(set(why) == expected_keys, f"{qid}: explain every unselected answer")
            require(all(isinstance(reason, str) and len(reason.strip()) >= 10 for reason in why.values()), f"{qid}: an unselected-answer reason is too short")
        warnings = []
        if review["review_context"] == "single_context_blind":
            warnings.append("Answer review used the same model context; report as single-context blind, not independent.")
        return warnings

    require(review.get("source_quiz_sha256") == data_hash(quiz), "Review packet is stale")
    require(review.get("knowledge_pack_sha256") == pack["knowledge_pack_sha256"], "Review knowledge pack is stale")
    items = review.get("questions")
    require(isinstance(items, list), "review.questions must be a list")
    by_id = {item.get("id"): item for item in items}
    require(len(by_id) == len(quiz["questions"]), "Review question count mismatch")
    warnings = []
    for question in quiz["questions"]:
        qid = question["id"]
        require(qid in by_id, f"Review missing {qid}")
        item = by_id[qid]
        require(item.get("selected_index") == question["correct_index"], f"{qid}: independent answer disagrees with marked answer")
        if pack["curriculum_mode"] == "strict":
            require(item.get("scope_pass") is True, f"{qid}: curriculum scope review failed")
        elif pack["curriculum_mode"] == "advisory" and item.get("scope_pass") is False:
            warnings.append(f"{qid}: reviewer marked curriculum scope as advisory-only")
        require(isinstance(item.get("reasoning"), str) and len(item["reasoning"].strip()) >= 8, f"{qid}: review reasoning too short")
    return warnings


def validate_scope_review(
    quiz: dict,
    review: dict,
    pack: dict,
    fact_pack: dict,
    request_manifest: dict,
    custom_scope: dict | None = None,
    document_manifest: dict | None = None,
    retrieval_pack: dict | None = None,
) -> list[str]:
    validate_request_manifest(request_manifest, required=True)
    scope_mode = request_spec.effective_scope_mode(request_manifest)
    validate_custom_scope(custom_scope, request_manifest, required=scope_mode == "custom")
    validate_document_grounding(document_manifest, retrieval_pack, request_manifest, required=request_spec.effective_grounding_mode(request_manifest) != "verified_sources")
    validate_review_header(
        review, quiz, pack, fact_pack, request_manifest, "curriculum_scope",
        custom_scope, document_manifest, retrieval_pack,
    )
    require(review.get("request_constraints") == request_manifest["teacher_constraints"], "Scope review request constraints are stale")
    items = review.get("questions")
    require(isinstance(items, list), "scope review questions must be a list")
    by_id = {item.get("id"): item for item in items}
    require(len(by_id) == len(quiz["questions"]), "Scope review question count mismatch")
    for question in quiz["questions"]:
        qid = question["id"]
        require(qid in by_id, f"Scope review missing {qid}")
        item = by_id[qid]
        for field in ("standard", "content_target", "discipline_lens", "fact_ids", "prompt", "choices", "scope_evidence"):
            require(item.get(field) == question.get(field), f"{qid}: scope review {field} was changed")
        require(item.get("standard_statement") == standard_statement(pack, question["standard"]), f"{qid}: scope standard statement is stale")
        expected_adapter = custom_scope["adapter"] if scope_mode == "custom" else SUBJECT_FAMILIES.get(quiz["metadata"]["subject"], "general")
        require(item.get("subject_adapter") == expected_adapter, f"{qid}: subject adapter is stale")
        if pack["curriculum_mode"] == "strict":
            require(item.get("scope_pass") is True, f"{qid}: strict curriculum scope review failed")
        if scope_mode == "custom":
            require(item.get("custom_scope_pass") is True, f"{qid}: custom scope review failed")
            require(item.get("audience_pass") is True, f"{qid}: custom audience review failed")
            require(item.get("safety_pass") is True, f"{qid}: custom safety review failed")
            require(item.get("learning_objective_id") == question.get("learning_objective_id"), f"{qid}: learning objective changed during review")
        require(item.get("terminology_pass") is True, f"{qid}: student terminology review failed")
        require(item.get("constraints_pass") is True, f"{qid}: teacher-constraint review failed")
        require(item.get("discipline_pass") is True, f"{qid}: subject-specific semantic review failed")
        require(isinstance(item.get("discipline_reasoning"), str) and len(item["discipline_reasoning"].strip()) >= 12, f"{qid}: subject-specific reasoning too short")
        require(isinstance(item.get("reasoning"), str) and len(item["reasoning"].strip()) >= 12, f"{qid}: scope reasoning too short")
    warnings = []
    if review["review_context"] == "single_context_blind":
        warnings.append("Scope review used the same model context.")
    return warnings


def csv_safe(value: str, label: str):
    require(isinstance(value, str), f"{label} must be text")
    require(not any(unicodedata.category(char) == "Cc" and char not in "\r\n\t" for char in value), f"{label} contains a control character")
    visible = "".join(char for char in unicodedata.normalize("NFKC", value) if unicodedata.category(char) not in {"Cf", "Zl", "Zp"})
    require(not visible.lstrip().startswith(("=", "+", "-", "@")), f"{label} starts with unsafe spreadsheet formula character")


def write_csv(path: Path, rows: list[list]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        csv.writer(handle, lineterminator="\r\n", quoting=csv.QUOTE_MINIMAL).writerows(rows)


def export_rows(quiz: dict):
    gimkit = [["Gimkit Spreadsheet Import Template", "", "", "", ""], GIMKIT_HEADERS]
    blooket = [["Blooket\nImport Template", "", "", "", "", "", "", ""], BLOOKET_HEADERS]
    mapping = []
    for index, question in enumerate(quiz["questions"]):
        prompt, choices = question["prompt"], list(question["choices"])
        correct = choices[question["correct_index"]]
        incorrect = [choice for choice_index, choice in enumerate(choices) if choice_index != question["correct_index"]]
        for label, value in [(f"{question['id']} prompt", prompt), *[(f"{question['id']} choice {i + 1}", choice) for i, choice in enumerate(choices)]]:
            csv_safe(value, label)
        gimkit.append([prompt, correct, *incorrect])
        target = index % 4
        ordered = list(incorrect)
        ordered.insert(target, correct)
        blooket.append([index + 1, prompt, *ordered, question["time_limit"], target + 1])
        mapping.append({"id": question["id"], "blooket_correct_position": target + 1})
    return gimkit, blooket, mapping


def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.reader(handle))


def validate_csv_bytes(path: Path):
    raw = path.read_bytes()
    require(raw.startswith(b"\xef\xbb\xbf"), f"{path.name}: UTF-8 BOM is missing")
    require(b"\x00" not in raw, f"{path.name}: NUL byte detected")
    text = raw[3:].decode("utf-8")
    quoted = False
    index = 0
    while index < len(text):
        char = text[index]
        if char == '"':
            if quoted and index + 1 < len(text) and text[index + 1] == '"':
                index += 2
                continue
            quoted = not quoted
        elif not quoted and char == "\n":
            require(index > 0 and text[index - 1] == "\r", f"{path.name}: record separator is not CRLF")
        elif not quoted and char == "\r":
            require(index + 1 < len(text) and text[index + 1] == "\n", f"{path.name}: bare CR record separator")
        index += 1
    require(not quoted, f"{path.name}: unclosed quoted field")


def validate_csv_roundtrip(quiz: dict, gimkit_path: Path, blooket_path: Path):
    validate_csv_bytes(gimkit_path)
    validate_csv_bytes(blooket_path)
    gimkit, blooket = read_csv(gimkit_path), read_csv(blooket_path)
    require(gimkit[0][0] == "Gimkit Spreadsheet Import Template" and gimkit[1] == GIMKIT_HEADERS, "Gimkit template header mismatch")
    require(blooket[0][0] == "Blooket\nImport Template" and blooket[1] == BLOOKET_HEADERS, "Blooket template header mismatch")
    require(len(gimkit) == len(quiz["questions"]) + 2, "Gimkit row count mismatch")
    require(len(blooket) == len(quiz["questions"]) + 2, "Blooket row count mismatch")
    require(all(len(row) == 5 for row in gimkit), "Gimkit contains a row with the wrong column count")
    require(all(len(row) == 8 for row in blooket), "Blooket contains a row with the wrong column count")
    for index, question in enumerate(quiz["questions"], start=2):
        correct = question["choices"][question["correct_index"]]
        require(gimkit[index][0] == question["prompt"] and gimkit[index][1] == correct, f"Gimkit mapping mismatch at row {index + 1}")
        require(blooket[index][7] in {"1", "2", "3", "4"}, f"Blooket answer position invalid at row {index + 1}")
        answer_position = int(blooket[index][7])
        require(blooket[index][1] == question["prompt"], f"Blooket prompt mismatch at row {index + 1}")
        require(blooket[index][answer_position + 1] == correct, f"Blooket answer mapping mismatch at row {index + 1}")
        require(5 <= int(blooket[index][6]) <= 300, f"Blooket time invalid at row {index + 1}")
    return {
        "gimkit_rows": len(gimkit) - 2, "blooket_rows": len(blooket) - 2,
        "correct_position_counts": dict(sorted(Counter(row[7] for row in blooket[2:]).items())),
        "encoding": "UTF-8-BOM", "record_separator": "CRLF", "column_counts": {"gimkit": 5, "blooket": 8},
        "structural_import_ready": True, "live_platform_import_verified": False,
    }


def command_blueprint(args):
    pack = read_json(args.knowledge_pack)
    fact_pack = read_json(args.fact_pack) if args.fact_pack else None
    request_manifest = read_json(args.request_manifest) if args.request_manifest else None
    custom_scope = read_json(args.custom_scope) if getattr(args, "custom_scope", None) else None
    document_manifest = read_json(args.document_manifest) if getattr(args, "document_manifest", None) else None
    retrieval_pack = read_json(args.retrieval_pack) if getattr(args, "retrieval_pack", None) else None
    blueprint = make_blueprint(
        args.count, args.seed, pack, fact_pack, request_manifest,
        custom_scope, document_manifest, retrieval_pack,
    )
    write_json(args.output, blueprint)
    print(json.dumps({"status": "pass", "profile": blueprint["profile"], "output": str(args.output), "count": args.count}, ensure_ascii=False))


def command_check(args):
    quiz, pack = read_json(args.input), read_json(args.knowledge_pack)
    blueprint = read_json(args.blueprint) if args.blueprint else None
    fact_pack = read_json(args.fact_pack) if args.fact_pack else None
    request_manifest = read_json(args.request_manifest) if args.request_manifest else None
    custom_scope = read_json(args.custom_scope) if getattr(args, "custom_scope", None) else None
    document_manifest = read_json(args.document_manifest) if getattr(args, "document_manifest", None) else None
    retrieval_pack = read_json(args.retrieval_pack) if getattr(args, "retrieval_pack", None) else None
    result = validate_quiz(
        quiz, pack, blueprint, fact_pack, request_manifest,
        custom_scope, document_manifest, retrieval_pack,
    )
    print(json.dumps({"status": "pass", **result}, ensure_ascii=False, indent=2))


def command_review_packet(args):
    quiz, pack = read_json(args.input), read_json(args.knowledge_pack)
    fact_pack = read_json(args.fact_pack) if args.fact_pack else None
    request_manifest = read_json(args.request_manifest) if args.request_manifest else None
    custom_scope = read_json(args.custom_scope) if getattr(args, "custom_scope", None) else None
    document_manifest = read_json(args.document_manifest) if getattr(args, "document_manifest", None) else None
    retrieval_pack = read_json(args.retrieval_pack) if getattr(args, "retrieval_pack", None) else None
    if args.kind == "scope":
        packet = make_scope_review_packet(
            quiz, pack, fact_pack, request_manifest,
            custom_scope, document_manifest, retrieval_pack,
        )
    else:
        packet = make_review_packet(
            quiz, pack, fact_pack, request_manifest,
            custom_scope, document_manifest, retrieval_pack,
        )
    write_json(args.output, packet)
    print(json.dumps({"status": "pass", "output": str(args.output), "questions": len(packet["questions"])}, ensure_ascii=False))


def question_risk_flags(question: dict, pack: dict, fact_details: list[dict], review_context: str | None) -> list[dict]:
    flags = []
    if review_context == "single_context_blind":
        flags.append({
            "code": "single_context_review",
            "severity": "warning",
            "message": "정답 검토가 생성과 같은 모델 맥락에서 수행되었습니다.",
        })
    if question["verification"].get("kind") == "review_only":
        flags.append({
            "code": "semantic_verification_only",
            "severity": "info",
            "message": "결정적 계산 대신 블라인드 의미 검토로 정답을 확인했습니다.",
        })
    dynamic = [fact["id"] for fact in fact_details if fact.get("stability") == "dynamic"]
    if dynamic:
        flags.append({
            "code": "dynamic_fact",
            "severity": "warning",
            "message": "유효기간이 있는 동적 사실을 사용했습니다.",
            "fact_ids": dynamic,
        })
    if pack["curriculum_mode"] == "advisory":
        flags.append({
            "code": "advisory_curriculum_mode",
            "severity": "warning",
            "message": "교육과정 범위가 강제되지 않는 advisory 모드입니다.",
        })
    if len(question["prompt"]) > 300 or max(len(choice) for choice in question["choices"]) > 120:
        flags.append({
            "code": "high_reading_load",
            "severity": "info",
            "message": "문항 또는 선택지의 읽기 분량이 비교적 깁니다.",
        })
    return flags


def make_analysis_report(
    quiz: dict,
    pack: dict,
    fact_pack: dict | None,
    request_manifest: dict | None,
    blueprint: dict,
    answer_review: dict,
    scope_review: dict | None,
    validation: dict,
    csv_roundtrip: dict,
    mapping: list[dict],
    generated_at: str,
    custom_scope: dict | None = None,
    document_manifest: dict | None = None,
    retrieval_pack: dict | None = None,
) -> dict:
    facts_by_id = {fact["id"]: fact for fact in (fact_pack or {}).get("facts", [])}
    answer_by_id = {item.get("id"): item for item in answer_review.get("questions", [])}
    scope_by_id = {item.get("id"): item for item in (scope_review or {}).get("questions", [])}
    mapping_by_id = {item["id"]: item for item in mapping}
    documents_by_id = {document["id"]: document for document in (document_manifest or {}).get("documents", [])}
    v2 = uses_v2(quiz, blueprint)
    permutations = review_layout(quiz)[1] if v2 else {}
    question_reports = []

    for question in quiz["questions"]:
        qid = question["id"]
        fact_details = [facts_by_id[fact_id] for fact_id in question.get("fact_ids", []) if fact_id in facts_by_id]
        document_citations = []
        for fact in fact_details:
            source = fact.get("source", {})
            if source.get("type") == "user_document":
                document = documents_by_id.get(source.get("document_id"), {})
                document_citations.append({
                    "fact_id": fact["id"],
                    "document_id": source.get("document_id"),
                    "display_name": document.get("display_name"),
                    "chunk_id": source.get("chunk_id"),
                    "locator": source.get("locator"),
                    "chunk_sha256": source.get("chunk_sha256"),
                })
        answer_item = answer_by_id.get(qid, {})
        scope_item = scope_by_id.get(qid, {})
        rejected = []
        if v2 and qid in permutations and isinstance(answer_item.get("selected_index"), int):
            order = permutations[qid]
            for shuffled_index_text, reason in answer_item.get("why_others_wrong", {}).items():
                shuffled_index = int(shuffled_index_text)
                original_index = order[shuffled_index]
                rejected.append({
                    "choice_index": original_index,
                    "choice": question["choices"][original_index],
                    "review_reason": reason,
                })
            selected_original = order[answer_item["selected_index"]]
        else:
            selected_original = answer_item.get("selected_index")

        question_reports.append({
            "id": qid,
            "prompt": question["prompt"],
            "choices": [{"index": index, "text": choice} for index, choice in enumerate(question["choices"])],
            "correct_index": question["correct_index"],
            "correct_answer": question["choices"][question["correct_index"]],
            "curriculum_analysis": {
                "standard": question["standard"],
                "standard_statement": standard_statement(pack, question["standard"]),
                "scope_evidence": question.get("scope_evidence"),
                "scope_pass": scope_item.get("scope_pass"),
                "terminology_pass": scope_item.get("terminology_pass"),
                "constraints_pass": scope_item.get("constraints_pass"),
                "discipline_pass": scope_item.get("discipline_pass"),
                "review_summary": scope_item.get("reasoning"),
                "discipline_review_summary": scope_item.get("discipline_reasoning"),
            },
            "custom_scope_analysis": None if custom_scope is None else {
                "custom_scope_sha256": custom_scope["custom_scope_sha256"],
                "learning_objective_id": question.get("learning_objective_id"),
                "learning_objective": next((item["description"] for item in custom_scope["learning_objectives"] if item["id"] == question.get("learning_objective_id")), None),
                "custom_scope_pass": scope_item.get("custom_scope_pass"),
                "audience_pass": scope_item.get("audience_pass"),
                "safety_pass": scope_item.get("safety_pass"),
            },
            "fact_analysis": [{
                "id": fact["id"],
                "claim": fact["claim"],
                "support_summary": fact.get("support_summary"),
                "evidence_sha256": fact.get("evidence_sha256"),
                "stability": fact.get("stability"),
                "expires_at": fact.get("expires_at"),
                "source": fact.get("source"),
            } for fact in fact_details],
            "item_analysis": {
                "item_type": question["item_type"],
                "cognitive_level": question["cognitive_level"],
                "difficulty": question["difficulty"],
                "difficulty_basis": question.get("difficulty_basis"),
                "content_target": question.get("content_target"),
                "task_contract": question.get("task_contract"),
                "discipline_lens": question.get("discipline_lens"),
                "stimulus": question.get("stimulus"),
            },
            "answer_analysis": {
                "verification_kind": question["verification"].get("kind"),
                "deterministic_gate": "pass" if question["verification"].get("kind") != "review_only" else "not_applicable",
                "answer_explanation": question["answer_explanation"],
                "answer_proof": question.get("answer_proof"),
                "blind_review_context": answer_review.get("review_context"),
                "blind_selected_canonical_index": selected_original,
                "blind_review_pass": selected_original == question["correct_index"],
                "ambiguity_flag": answer_item.get("ambiguity_flag"),
                "review_summary": answer_item.get("reasoning"),
                "rejected_answer_reviews": sorted(rejected, key=lambda item: item["choice_index"]),
            },
            "distractor_analysis": [{
                "choice_index": distractor["choice_index"],
                "choice": question["choices"][distractor["choice_index"]],
                "misconception": distractor["misconception"],
                "design_reason": distractor["reason"],
                "why_wrong": distractor.get("why_wrong"),
            } for distractor in sorted(question["distractors"], key=lambda item: item["choice_index"])],
            "csv_mapping": {
                "gimkit_correct_answer_column": "B",
                "blooket_correct_position": mapping_by_id[qid]["blooket_correct_position"],
            },
            "document_grounding": {
                "mode": request_spec.effective_grounding_mode(request_manifest) if request_manifest else "legacy",
                "citations": document_citations,
                "grounding_pass": (
                    bool(document_citations)
                    if document_manifest is not None and request_spec.effective_grounding_mode(request_manifest) == "documents_only"
                    else (True if document_manifest is not None else None)
                ),
            },
            "risk_flags": question_risk_flags(question, pack, fact_details, answer_review.get("review_context")),
        })

    route = pack.get("route") or {}
    placement = "not_applicable"
    if pack["curriculum_mode"] != "off":
        placement = "reviewed_semester_override" if route.get("unit_override_applied") else "grade_band_only"
    overall_risks = []
    if answer_review.get("review_context") == "single_context_blind":
        overall_risks.append("Answer review was blind but not independent of the generation context.")
    if not csv_roundtrip.get("live_platform_import_verified"):
        overall_risks.append("CSV files were structurally validated but not uploaded to live platforms.")

    return {
        "schema_version": 1,
        "report_kind": "teacher_audit_summary",
        "generated_at": generated_at,
        "reasoning_policy": "Contains concise, checkable evidence summaries and review results; does not expose private chain-of-thought.",
        "request_summary": None if request_manifest is None else {
            key: value for key, value in request_manifest.items() if key != "request_manifest_sha256"
        } | {"request_manifest_sha256": request_manifest["request_manifest_sha256"]},
        "quiz_summary": {
            "title": quiz["metadata"]["title"],
            "grade": quiz["metadata"]["grade"],
            "subject": quiz["metadata"]["subject"],
            "unit": quiz["metadata"]["unit"],
            "question_count": len(quiz["questions"]),
            "assurance_profile": quiz["metadata"].get("assurance_profile", "legacy-v1"),
        },
        "curriculum_analysis": {
            "mode": pack["curriculum_mode"],
            "route": pack.get("route"),
            "semester_placement": placement,
            "route_notes": pack.get("route_notes", []),
            "standards": [{"code": code, "statement": standard_statement(pack, code)} for code in sorted({question["standard"] for question in quiz["questions"]})],
        },
        "custom_scope_analysis": None if custom_scope is None else {
            "topic": custom_scope["topic"],
            "adapter": custom_scope["adapter"],
            "audience": custom_scope["audience"],
            "learning_objectives": custom_scope["learning_objectives"],
            "in_scope": custom_scope["in_scope"],
            "out_of_scope": custom_scope["out_of_scope"],
            "safety": custom_scope["safety"],
            "custom_scope_sha256": custom_scope["custom_scope_sha256"],
        },
        "document_grounding_analysis": None if document_manifest is None else {
            "mode": request_spec.effective_grounding_mode(request_manifest),
            "document_manifest_sha256": document_manifest["document_manifest_sha256"],
            "retrieval_pack_sha256": retrieval_pack["retrieval_pack_sha256"],
            "documents": [{
                "id": document["id"],
                "display_name": document["display_name"],
                "file_sha256": document["file_sha256"],
                "rights_basis": document["rights_basis"],
                "extraction": document["extraction"],
            } for document in document_manifest["documents"]],
            "targets": retrieval_pack["targets"],
        },
        "distribution_analysis": validation["distribution"],
        "fact_catalog": list(facts_by_id.values()),
        "questions": question_reports,
        "csv_analysis": csv_roundtrip,
        "overall_risk_notes": overall_risks,
    }


def command_build(args):
    quiz, pack = read_json(args.input), read_json(args.knowledge_pack)
    blueprint, review = read_json(args.blueprint), read_json(args.review)
    fact_pack = read_json(args.fact_pack) if args.fact_pack else None
    request_manifest = read_json(args.request_manifest) if args.request_manifest else None
    custom_scope = read_json(args.custom_scope) if getattr(args, "custom_scope", None) else None
    document_manifest = read_json(args.document_manifest) if getattr(args, "document_manifest", None) else None
    retrieval_pack = read_json(args.retrieval_pack) if getattr(args, "retrieval_pack", None) else None
    validation = validate_quiz(
        quiz, pack, blueprint, fact_pack, request_manifest,
        custom_scope, document_manifest, retrieval_pack,
    )
    review_warnings = validate_review(
        quiz, review, pack, fact_pack, request_manifest,
        custom_scope, document_manifest, retrieval_pack,
    )
    scope_warnings = []
    scope_review = None
    if uses_v2(quiz, blueprint):
        require(args.scope_review is not None, "assurance v2 build requires --scope-review")
        scope_review = read_json(args.scope_review)
        scope_warnings = validate_scope_review(
            quiz, scope_review, pack, fact_pack, request_manifest,
            custom_scope, document_manifest, retrieval_pack,
        )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    gimkit_path, blooket_path = args.output_dir / "gimkit-import.csv", args.output_dir / "blooket-import.csv"
    gimkit_rows, blooket_rows, mapping = export_rows(quiz)
    write_csv(gimkit_path, gimkit_rows)
    write_csv(blooket_path, blooket_rows)
    roundtrip = validate_csv_roundtrip(quiz, gimkit_path, blooket_path)
    generated_at = datetime.now(timezone.utc).isoformat()
    analysis_report = make_analysis_report(
        quiz, pack, fact_pack, request_manifest, blueprint, review, scope_review,
        validation, roundtrip, mapping, generated_at,
        custom_scope, document_manifest, retrieval_pack,
    )
    analysis_path = args.output_dir / "analysis-report.json"
    write_json(analysis_path, analysis_report)
    report = {
        "status": "pass", "generated_at": generated_at,
        "curriculum": {
            "version": quiz["metadata"]["curriculum"], "mode": pack["curriculum_mode"],
            "route": pack.get("route"), "knowledge_pack_sha256": pack["knowledge_pack_sha256"],
            "request_manifest_sha256": request_manifest.get("request_manifest_sha256") if request_manifest else None,
            "standards": sorted({question["standard"] for question in quiz["questions"]}),
        },
        "workflow_branch": None if request_manifest is None else {
            "scope_mode": request_spec.effective_scope_mode(request_manifest),
            "grounding_mode": request_spec.effective_grounding_mode(request_manifest),
            "custom_scope_sha256": custom_scope.get("custom_scope_sha256") if custom_scope else None,
            "document_manifest_sha256": document_manifest.get("document_manifest_sha256") if document_manifest else None,
            "retrieval_pack_sha256": retrieval_pack.get("retrieval_pack_sha256") if retrieval_pack else None,
        },
        "validation": validation,
        "answer_review": {
            "status": "pass", "reviewed_questions": len(quiz["questions"]), "warnings": review_warnings,
            "context": review.get("review_context", "legacy_unrecorded"),
        },
        "scope_review": {
            "status": "pass" if scope_review else "legacy_not_separated",
            "reviewed_questions": len(quiz["questions"]) if scope_review else 0,
            "warnings": scope_warnings,
            "context": scope_review.get("review_context") if scope_review else None,
        },
        "csv_roundtrip": roundtrip, "blooket_mapping": mapping,
        "files": {
            "gimkit-import.csv": file_hash(gimkit_path),
            "blooket-import.csv": file_hash(blooket_path),
            "analysis-report.json": file_hash(analysis_path),
        },
    }
    report["assurance"] = {
        "profile": V2_ASSURANCE_PROFILE if uses_v2(quiz, blueprint) else "legacy-v1",
        "structure": "pass",
        "curriculum_scope": "pass" if pack["curriculum_mode"] == "strict" and scope_review else ("legacy" if not scope_review else "advisory"),
        "custom_scope": "pass" if custom_scope else "not_applicable",
        "document_grounding": "pass" if document_manifest else "not_applicable",
        "fact_evidence": "pass" if fact_pack else "legacy_not_required",
        "answer_review": "pass",
        "csv_import_readiness": "structural_only",
        "live_platform_import_verified": False,
    }
    report["independent_review"] = {
        "status": "pass",
        "reviewed_questions": len(quiz["questions"]),
        "warnings": review_warnings,
        "context": review.get("review_context", "legacy_unrecorded"),
        "independent": review.get("review_context") in {"fresh_context", "human"},
    }
    write_json(args.output_dir / "validation-report.json", report)
    print(json.dumps({"status": "pass", "output_dir": str(args.output_dir), "files": report["files"]}, ensure_ascii=False, indent=2))


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    blueprint = subparsers.add_parser("blueprint")
    blueprint.add_argument("--knowledge-pack", type=Path, required=True)
    blueprint.add_argument("--fact-pack", type=Path)
    blueprint.add_argument("--request-manifest", type=Path)
    blueprint.add_argument("--custom-scope", type=Path)
    blueprint.add_argument("--document-manifest", type=Path)
    blueprint.add_argument("--retrieval-pack", type=Path)
    blueprint.add_argument("--count", type=int, default=20)
    blueprint.add_argument("--seed", type=int, default=20260627)
    blueprint.add_argument("--output", type=Path, required=True)
    blueprint.set_defaults(func=command_blueprint)

    check = subparsers.add_parser("check")
    check.add_argument("--input", type=Path, required=True)
    check.add_argument("--knowledge-pack", type=Path, required=True)
    check.add_argument("--fact-pack", type=Path)
    check.add_argument("--request-manifest", type=Path)
    check.add_argument("--custom-scope", type=Path)
    check.add_argument("--document-manifest", type=Path)
    check.add_argument("--retrieval-pack", type=Path)
    check.add_argument("--blueprint", type=Path)
    check.set_defaults(func=command_check)

    review = subparsers.add_parser("review-packet")
    review.add_argument("--input", type=Path, required=True)
    review.add_argument("--knowledge-pack", type=Path, required=True)
    review.add_argument("--fact-pack", type=Path)
    review.add_argument("--request-manifest", type=Path)
    review.add_argument("--custom-scope", type=Path)
    review.add_argument("--document-manifest", type=Path)
    review.add_argument("--retrieval-pack", type=Path)
    review.add_argument("--kind", choices=("answer", "scope"), default="answer")
    review.add_argument("--output", type=Path, required=True)
    review.set_defaults(func=command_review_packet)

    build = subparsers.add_parser("build")
    build.add_argument("--input", type=Path, required=True)
    build.add_argument("--knowledge-pack", type=Path, required=True)
    build.add_argument("--fact-pack", type=Path)
    build.add_argument("--request-manifest", type=Path)
    build.add_argument("--custom-scope", type=Path)
    build.add_argument("--document-manifest", type=Path)
    build.add_argument("--retrieval-pack", type=Path)
    build.add_argument("--blueprint", type=Path, required=True)
    build.add_argument("--review", type=Path, required=True)
    build.add_argument("--scope-review", type=Path)
    build.add_argument("--output-dir", type=Path, required=True)
    build.set_defaults(func=command_build)
    return parser


def main():
    args = build_parser().parse_args()
    try:
        args.func(args)
    except ValidationError as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
