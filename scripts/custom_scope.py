#!/usr/bin/env python3
"""Seal and validate teacher-defined scope packs for non-curriculum quizzes."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import request_manifest as request_spec


ADAPTERS = {"general_knowledge", "technology_making", "coding", "safety_training", "document_comprehension"}
SAFETY_LEVELS = {"none", "standard", "high"}


class ScopeError(Exception):
    pass


def require(condition: bool, message: str):
    if not condition:
        raise ScopeError(message)


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ScopeError(f"Cannot read JSON {path}: {exc}") from exc


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def payload_hash(data: dict) -> str:
    payload = {key: value for key, value in data.items() if key != "custom_scope_sha256"}
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_scope(data: dict, request: dict, require_sealed: bool = True) -> dict:
    try:
        request_spec.validate_request(request)
    except request_spec.RequestError as exc:
        raise ScopeError(str(exc)) from exc
    require(request_spec.effective_scope_mode(request) == "custom", "custom scope requires request scope_mode=custom")
    require(isinstance(data, dict) and data.get("schema_version") == 1, "custom scope schema_version must be 1")
    require(data.get("request_manifest_sha256") == request["request_manifest_sha256"], "custom scope request hash is stale")
    require(data.get("topic") == request["topic"], "custom scope topic disagrees with request")
    require(data.get("adapter") in ADAPTERS, "custom scope adapter is invalid")
    audience = data.get("audience")
    require(isinstance(audience, dict), "custom scope audience is required")
    require(audience.get("grade") == request["grade"], "custom scope audience grade disagrees with request")
    require(isinstance(audience.get("experience"), str) and audience["experience"].strip(), "custom scope audience experience is required")
    objectives = data.get("learning_objectives")
    require(isinstance(objectives, list) and objectives, "custom scope needs learning objectives")
    ids = []
    for index, objective in enumerate(objectives, start=1):
        require(isinstance(objective, dict), f"learning_objectives[{index}] must be an object")
        objective_id = objective.get("id")
        require(isinstance(objective_id, str) and re.fullmatch(r"obj-[a-z0-9][a-z0-9-]{1,63}", objective_id), f"learning_objectives[{index}].id is invalid")
        require(isinstance(objective.get("description"), str) and len(objective["description"].strip()) >= 8, f"learning_objectives[{index}].description is too short")
        ids.append(objective_id)
    require(len(ids) == len(set(ids)), "learning objective IDs must be unique")
    for field in ("in_scope", "out_of_scope"):
        values = data.get(field)
        require(isinstance(values, list) and values and all(isinstance(value, str) and value.strip() for value in values), f"custom scope {field} must be a nonempty string list")
    require(not set(data["in_scope"]) & set(data["out_of_scope"]), "custom scope includes and excludes the same item")
    terminology = data.get("terminology")
    require(isinstance(terminology, dict), "custom scope terminology is required")
    for field in ("allowed", "define_before_use", "forbidden"):
        require(isinstance(terminology.get(field), list), f"custom scope terminology.{field} must be a list")
    safety = data.get("safety")
    require(isinstance(safety, dict) and safety.get("level") in SAFETY_LEVELS, "custom scope safety policy is invalid")
    for field in ("required_rules", "prohibited_topics"):
        require(isinstance(safety.get(field), list), f"custom scope safety.{field} must be a list")
    require(isinstance(safety.get("requires_current_official_verification"), bool), "custom scope safety verification flag is required")
    if data["adapter"] in {"technology_making", "safety_training"}:
        require(safety["level"] != "none", "technology and safety adapters require a safety policy")
        require(bool(safety["required_rules"]), "technology and safety adapters require safety rules")
    if require_sealed:
        require(data.get("custom_scope_sha256") == payload_hash(data), "custom scope seal is missing or stale")
    return {"status": "pass", "objectives": len(objectives), "adapter": data["adapter"], "custom_scope_sha256": payload_hash(data)}


def command_seal(args):
    draft, request = read_json(args.input), read_json(args.request_manifest)
    draft["schema_version"] = 1
    draft["request_manifest_sha256"] = request.get("request_manifest_sha256")
    draft.pop("custom_scope_sha256", None)
    validate_scope(draft, request, require_sealed=False)
    draft["custom_scope_sha256"] = payload_hash(draft)
    validate_scope(draft, request)
    write_json(args.output, draft)
    print(json.dumps({"status": "pass", "output": str(args.output), "custom_scope_sha256": draft["custom_scope_sha256"]}, ensure_ascii=False))


def command_check(args):
    print(json.dumps(validate_scope(read_json(args.input), read_json(args.request_manifest)), ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)
    seal = subs.add_parser("seal")
    seal.add_argument("--input", type=Path, required=True)
    seal.add_argument("--request-manifest", type=Path, required=True)
    seal.add_argument("--output", type=Path, required=True)
    seal.set_defaults(func=command_seal)
    check = subs.add_parser("check")
    check.add_argument("--input", type=Path, required=True)
    check.add_argument("--request-manifest", type=Path, required=True)
    check.set_defaults(func=command_check)
    args = parser.parse_args()
    try:
        args.func(args)
    except ScopeError as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
