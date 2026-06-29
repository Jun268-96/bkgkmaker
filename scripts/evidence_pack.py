#!/usr/bin/env python3
"""Seal and validate source-backed fact packs used by quiz assurance v2."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path


ACCEPTED_AUTHORITIES = {"official", "open_reference", "teacher_review", "deterministic_rule", "user_supplied"}
STABILITIES = {"stable", "dynamic"}


class EvidenceError(Exception):
    pass


def require(condition: bool, message: str):
    if not condition:
        raise EvidenceError(message)


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceError(f"Cannot read JSON {path}: {exc}") from exc


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def payload_hash(data: dict) -> str:
    payload = {key: value for key, value in data.items() if key != "fact_pack_sha256"}
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def text_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def iso_date(value, label: str) -> date:
    require(isinstance(value, str), f"{label} must be an ISO date")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise EvidenceError(f"{label} must be YYYY-MM-DD") from exc


def validate_fact_pack(pack: dict, knowledge_pack: dict, require_sealed: bool = True) -> dict:
    require(isinstance(pack, dict), "fact pack must be an object")
    require(pack.get("schema_version") == 1, "fact pack schema_version must be 1")
    require(
        pack.get("knowledge_pack_sha256") == knowledge_pack.get("knowledge_pack_sha256"),
        "fact pack knowledge hash is stale",
    )
    require(isinstance(pack.get("topic"), str) and pack["topic"].strip(), "fact pack topic is required")
    facts = pack.get("facts")
    require(isinstance(facts, list) and facts, "fact pack must contain at least one fact")
    ids = []
    dynamic_count = 0
    for index, fact in enumerate(facts, start=1):
        label = f"facts[{index}]"
        require(isinstance(fact, dict), f"{label} must be an object")
        fact_id = fact.get("id")
        require(
            isinstance(fact_id, str) and re.fullmatch(r"fact-[a-z0-9][a-z0-9-]{1,63}", fact_id),
            f"{label}.id must use fact-kebab-case",
        )
        ids.append(fact_id)
        require(isinstance(fact.get("claim"), str) and len(fact["claim"].strip()) >= 8, f"{label}.claim is too short")
        require(isinstance(fact.get("support_summary"), str) and len(fact["support_summary"].strip()) >= 8, f"{label}.support_summary is too short")
        require(isinstance(fact.get("evidence_sha256"), str) and re.fullmatch(r"[0-9a-f]{64}", fact["evidence_sha256"]), f"{label}.evidence_sha256 is required")
        source = fact.get("source")
        require(isinstance(source, dict), f"{label}.source is required")
        require(source.get("authority") in ACCEPTED_AUTHORITIES, f"{label}.source.authority is not accepted")
        for field in ("id", "title", "locator", "verified_at"):
            require(isinstance(source.get(field), str) and source[field].strip(), f"{label}.source.{field} is required")
        iso_date(source["verified_at"], f"{label}.source.verified_at")
        stability = fact.get("stability")
        require(stability in STABILITIES, f"{label}.stability must be stable or dynamic")
        if stability == "dynamic":
            dynamic_count += 1
            expires = iso_date(fact.get("expires_at"), f"{label}.expires_at")
            require(expires >= date.today(), f"{label} dynamic fact is expired")
    require(len(set(ids)) == len(ids), "fact IDs must be unique")
    if require_sealed:
        require(pack.get("fact_pack_sha256") == payload_hash(pack), "fact pack seal is missing or stale")
    return {"status": "pass", "facts": len(facts), "dynamic_facts": dynamic_count, "fact_pack_sha256": payload_hash(pack)}


def command_seal(args):
    draft = read_json(args.input)
    knowledge_pack = read_json(args.knowledge_pack)
    draft["schema_version"] = 1
    draft["knowledge_pack_sha256"] = knowledge_pack.get("knowledge_pack_sha256")
    draft.pop("fact_pack_sha256", None)
    validate_fact_pack(draft, knowledge_pack, require_sealed=False)
    draft["fact_pack_sha256"] = payload_hash(draft)
    validate_fact_pack(draft, knowledge_pack)
    write_json(args.output, draft)
    print(json.dumps({"status": "pass", "output": str(args.output), "facts": len(draft["facts"]), "fact_pack_sha256": draft["fact_pack_sha256"]}, ensure_ascii=False))


def command_check(args):
    result = validate_fact_pack(read_json(args.input), read_json(args.knowledge_pack))
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("seal", "check"):
        sub = subparsers.add_parser(command)
        sub.add_argument("--input", type=Path, required=True)
        sub.add_argument("--knowledge-pack", type=Path, required=True)
        if command == "seal":
            sub.add_argument("--output", type=Path, required=True)
            sub.set_defaults(func=command_seal)
        else:
            sub.set_defaults(func=command_check)
    args = parser.parse_args()
    try:
        args.func(args)
    except EvidenceError as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
