#!/usr/bin/env python3
"""Plan the correct quiz workflow branch from a sealed request and available artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import custom_scope as custom
import document_grounding as grounding
import evidence_pack as evidence
import request_manifest as request_spec
import quiz_harness as harness


class RouterError(Exception):
    pass


def read_json(path: Path | None):
    if path is None:
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RouterError(f"Cannot read JSON {path}: {exc}") from exc


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def plan_hash(data: dict) -> str:
    payload = {key: value for key, value in data.items() if key != "workflow_plan_sha256"}
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def branch_id(scope_mode: str, grounding_mode: str) -> str:
    source = "documents" if grounding_mode != "verified_sources" else "verified_sources"
    return f"{scope_mode}_{source}"


def artifact(name: str, required: bool, present: bool, purpose: str) -> dict:
    return {"name": name, "required": required, "present": present, "purpose": purpose}


def supplied(path: Path | None) -> bool:
    return path is not None and path.is_file()


def build_plan(args) -> dict:
    request = read_json(args.request_manifest)
    try:
        request_spec.validate_request(request)
    except request_spec.RequestError as exc:
        raise RouterError(str(exc)) from exc
    scope_mode = request_spec.effective_scope_mode(request)
    grounding_mode = request_spec.effective_grounding_mode(request)
    uses_documents = grounding_mode != "verified_sources"

    knowledge_pack = read_json(args.knowledge_pack)
    custom_scope = read_json(args.custom_scope)
    document_manifest = read_json(args.document_manifest)
    retrieval_pack = read_json(args.retrieval_pack)
    fact_pack = read_json(args.fact_pack)

    if knowledge_pack is not None:
        if not isinstance(knowledge_pack, dict) or not isinstance(knowledge_pack.get("knowledge_pack_sha256"), str):
            raise RouterError("knowledge/audience pack is invalid")
        if knowledge_pack.get("curriculum_mode") != request["curriculum_mode"]:
            raise RouterError("knowledge/audience pack mode disagrees with request")
        if scope_mode == "curriculum":
            route = knowledge_pack.get("route") or {}
            if (route.get("subject"), route.get("grade"), route.get("unit")) != (request["subject"], request["grade"], request["topic"]):
                raise RouterError("curriculum route disagrees with request")
        elif knowledge_pack.get("route") is not None:
            raise RouterError("custom scope requires an off-mode audience pack without a curriculum route")

    if custom_scope is not None:
        try:
            custom.validate_scope(custom_scope, request)
        except custom.ScopeError as exc:
            raise RouterError(str(exc)) from exc
    if document_manifest is not None:
        try:
            grounding.validate_document_manifest(document_manifest, request)
        except grounding.GroundingError as exc:
            raise RouterError(str(exc)) from exc
    if retrieval_pack is not None:
        if document_manifest is None:
            raise RouterError("retrieval pack requires a document manifest")
        try:
            grounding.validate_retrieval_pack(retrieval_pack, request, document_manifest)
        except grounding.GroundingError as exc:
            raise RouterError(str(exc)) from exc
    if fact_pack is not None:
        if knowledge_pack is None:
            raise RouterError("fact pack requires a knowledge/audience pack")
        try:
            evidence.validate_fact_pack(fact_pack, knowledge_pack)
        except evidence.EvidenceError as exc:
            raise RouterError(str(exc)) from exc
        try:
            harness.validate_fact_grounding(fact_pack, request, document_manifest, retrieval_pack)
        except harness.ValidationError as exc:
            raise RouterError(str(exc)) from exc

    artifacts = [
        artifact("request-manifest.json", True, True, "Freeze user intent and branch choices"),
        artifact("knowledge-pack.json", True, knowledge_pack is not None, "Curriculum scope or elementary audience rules"),
        artifact("custom-scope.json", scope_mode == "custom", custom_scope is not None, "Teacher-defined objectives and safety boundaries"),
        artifact("document-manifest.json", uses_documents, document_manifest is not None, "Hash and extraction provenance for supplied documents"),
        artifact("retrieval-pack.json", uses_documents, retrieval_pack is not None, "Objective-targeted document evidence"),
        artifact("fact-pack.json", True, fact_pack is not None, "Atomic answer evidence"),
        artifact("blueprint.json", True, supplied(args.blueprint), "Content and item-design coverage"),
        artifact("answer-review.json", True, supplied(args.answer_review), "Blind answer and ambiguity review"),
        artifact("scope-review.json", True, supplied(args.scope_review), "Scope, terminology, constraints, discipline, and safety review"),
    ]
    missing = [item["name"] for item in artifacts if item["required"] and not item["present"]]
    dependency_order = [item["name"] for item in artifacts if item["required"]]
    next_artifact = next((name for name in dependency_order if name in missing), None)

    blocking_questions = []
    if scope_mode == "custom" and custom_scope is None:
        blocking_questions.append("Confirm experience level, learning objectives, in/out scope, terminology, adapter, and safety policy.")
    if uses_documents and document_manifest is None:
        blocking_questions.append("Attach or identify the source documents and choose ephemeral, session, or approved persistent handling.")
    if uses_documents and grounding_mode in {"documents_preferred", "mixed_verified"}:
        blocking_questions.append("Confirm whether external verified sources may fill document coverage gaps.")

    hard_gates = [
        "request, scope, document, retrieval, fact, quiz, and review hashes must remain current",
        "every correct answer must cite sealed facts",
        "every document fact must resolve to a selected chunk and source locator",
        "unresolved retrieval conflicts or low extraction confidence block affected questions",
        "documents_only forbids unsupported external facts",
        "custom scope requires audience, objective, terminology, out-of-scope, and safety review",
        "live platform import is never implied by structural CSV validation",
    ]
    result = {
        "schema_version": 1,
        "request_manifest_sha256": request["request_manifest_sha256"],
        "branch": branch_id(scope_mode, grounding_mode),
        "scope_mode": scope_mode,
        "grounding_mode": grounding_mode,
        "status": "ready_to_build" if not missing else "pending_artifacts",
        "next_artifact": next_artifact,
        "artifacts": artifacts,
        "blocking_questions": blocking_questions,
        "hard_gates": hard_gates,
    }
    result["workflow_plan_sha256"] = plan_hash(result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request-manifest", type=Path, required=True)
    parser.add_argument("--knowledge-pack", type=Path)
    parser.add_argument("--custom-scope", type=Path)
    parser.add_argument("--document-manifest", type=Path)
    parser.add_argument("--retrieval-pack", type=Path)
    parser.add_argument("--fact-pack", type=Path)
    parser.add_argument("--blueprint", type=Path)
    parser.add_argument("--answer-review", type=Path)
    parser.add_argument("--scope-review", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = build_plan(args)
        write_json(args.output, result)
        print(json.dumps({"status": "pass", "branch": result["branch"], "next_artifact": result["next_artifact"], "output": str(args.output)}, ensure_ascii=False))
    except RouterError as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
