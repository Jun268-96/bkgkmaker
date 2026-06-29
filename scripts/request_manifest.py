#!/usr/bin/env python3
"""Seal and validate reproducible quiz request manifests."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


MODES = {"strict", "advisory", "off"}
MODE_SOURCES = {"explicit_user", "inferred_request", "asked_user"}
SCOPE_MODES = {"curriculum", "custom"}
GROUNDING_MODES = {"verified_sources", "documents_only", "documents_preferred", "mixed_verified"}


class RequestError(Exception):
    pass


def require(condition: bool, message: str):
    if not condition:
        raise RequestError(message)


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RequestError(f"Cannot read JSON {path}: {exc}") from exc


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def payload_hash(data: dict) -> str:
    payload = {key: value for key, value in data.items() if key != "request_manifest_sha256"}
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def effective_scope_mode(data: dict) -> str:
    return data.get("scope_mode") or ("custom" if data.get("curriculum_mode") == "off" else "curriculum")


def effective_grounding_mode(data: dict) -> str:
    return data.get("grounding_mode") or "verified_sources"


def validate_request(data: dict, require_sealed: bool = True) -> dict:
    require(isinstance(data, dict), "request manifest must be an object")
    require(data.get("schema_version") in {1, 2}, "request schema_version must be 1 or 2")
    require(isinstance(data.get("grade"), int) and 1 <= data["grade"] <= 6, "request grade must be 1..6")
    require(isinstance(data.get("subject"), str) and data["subject"].strip(), "request subject is required")
    require(isinstance(data.get("topic"), str) and data["topic"].strip(), "request topic is required")
    require(data.get("curriculum_mode") in MODES, "request curriculum_mode is invalid")
    require(data.get("curriculum_mode_source") in MODE_SOURCES, "request curriculum_mode_source is invalid")
    scope_mode = effective_scope_mode(data)
    grounding_mode = effective_grounding_mode(data)
    require(scope_mode in SCOPE_MODES, "request scope_mode is invalid")
    require(grounding_mode in GROUNDING_MODES, "request grounding_mode is invalid")
    if data.get("schema_version") == 2:
        require(data.get("scope_mode") in SCOPE_MODES, "request v2 requires explicit scope_mode")
        require(data.get("grounding_mode") in GROUNDING_MODES, "request v2 requires explicit grounding_mode")
    if scope_mode == "curriculum":
        require(data["curriculum_mode"] in {"strict", "advisory"}, "curriculum scope requires strict or advisory mode")
    else:
        require(data["curriculum_mode"] == "off", "custom scope requires curriculum_mode=off")
    require(isinstance(data.get("question_count"), int) and 4 <= data["question_count"] <= 100, "request question_count must be 4..100")
    require(data.get("choice_count") == 4, "this skill requires exactly four choices")
    for field in ("default_time_limit", "long_time_limit"):
        require(isinstance(data.get(field), int) and 5 <= data[field] <= 300, f"request {field} must be 5..300")
    require(data["long_time_limit"] >= data["default_time_limit"], "long_time_limit must not be shorter than default_time_limit")
    constraints = data.get("teacher_constraints")
    require(isinstance(constraints, list) and all(isinstance(value, str) and value.strip() for value in constraints), "teacher_constraints must be a list of nonempty strings")
    require(isinstance(data.get("seed"), int), "request seed must be an integer")
    if data.get("semester") is not None:
        require(isinstance(data["semester"], str) and data["semester"].strip(), "request semester must be text or null")
    if require_sealed:
        require(data.get("request_manifest_sha256") == payload_hash(data), "request manifest seal is missing or stale")
    return {
        "status": "pass",
        "scope_mode": scope_mode,
        "grounding_mode": grounding_mode,
        "request_manifest_sha256": payload_hash(data),
    }


def command_seal(args):
    draft = read_json(args.input)
    draft["schema_version"] = 2
    draft.pop("request_manifest_sha256", None)
    validate_request(draft, require_sealed=False)
    draft["request_manifest_sha256"] = payload_hash(draft)
    validate_request(draft)
    write_json(args.output, draft)
    print(json.dumps({"status": "pass", "output": str(args.output), "request_manifest_sha256": draft["request_manifest_sha256"]}, ensure_ascii=False))


def command_check(args):
    print(json.dumps(validate_request(read_json(args.input)), ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    seal = subparsers.add_parser("seal")
    seal.add_argument("--input", type=Path, required=True)
    seal.add_argument("--output", type=Path, required=True)
    seal.set_defaults(func=command_seal)
    check = subparsers.add_parser("check")
    check.add_argument("--input", type=Path, required=True)
    check.set_defaults(func=command_check)
    args = parser.parse_args()
    try:
        args.func(args)
    except RequestError as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
