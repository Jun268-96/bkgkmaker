#!/usr/bin/env python3
"""Seal document manifests and retrieval packs without persisting source text."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import request_manifest as request_spec


RIGHTS_BASES = {"user_supplied", "licensed", "public_domain", "official"}
PERSISTENCE = {"ephemeral", "session", "approved_persistent"}
FORMATS = {"pdf", "pptx", "docx", "xlsx", "csv", "txt", "md", "html", "png", "jpg", "jpeg"}
COVERAGE = {"sufficient", "partial", "conflicting", "unsupported", "low_extraction_confidence"}
RELEVANCE = {"direct_support", "supporting_context", "counterevidence"}


class GroundingError(Exception):
    pass


def require(condition: bool, message: str):
    if not condition:
        raise GroundingError(message)


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GroundingError(f"Cannot read JSON {path}: {exc}") from exc


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def payload_hash(data: dict, hash_field: str) -> str:
    payload = {key: value for key, value in data.items() if key != hash_field}
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_document_manifest(data: dict, request: dict, require_sealed: bool = True) -> dict:
    try:
        request_spec.validate_request(request)
    except request_spec.RequestError as exc:
        raise GroundingError(str(exc)) from exc
    require(request_spec.effective_grounding_mode(request) != "verified_sources", "document manifest is not used for verified_sources grounding")
    require(isinstance(data, dict) and data.get("schema_version") == 1, "document manifest schema_version must be 1")
    require(data.get("request_manifest_sha256") == request["request_manifest_sha256"], "document manifest request hash is stale")
    require(data.get("persistence") in PERSISTENCE, "document manifest persistence policy is invalid")
    require(data.get("untrusted_instructions_ignored") is True, "document content must be marked as untrusted instructions")
    documents = data.get("documents")
    require(isinstance(documents, list) and documents, "document manifest needs at least one document")
    ids = []
    for index, document in enumerate(documents, start=1):
        label = f"documents[{index}]"
        require(isinstance(document, dict), f"{label} must be an object")
        document_id = document.get("id")
        require(isinstance(document_id, str) and re.fullmatch(r"doc-[a-z0-9][a-z0-9-]{1,63}", document_id), f"{label}.id is invalid")
        ids.append(document_id)
        require(isinstance(document.get("display_name"), str) and document["display_name"].strip(), f"{label}.display_name is required")
        require(document.get("format") in FORMATS, f"{label}.format is unsupported")
        require(document.get("rights_basis") in RIGHTS_BASES, f"{label}.rights_basis is invalid")
        require(isinstance(document.get("file_sha256"), str) and re.fullmatch(r"[0-9a-f]{64}", document["file_sha256"]), f"{label}.file_sha256 is required")
        source_path = document.get("source_path")
        if source_path:
            path = Path(source_path)
            require(path.is_file(), f"{label}.source_path does not exist")
            require(file_hash(path) == document["file_sha256"], f"{label} source file changed")
        extraction = document.get("extraction")
        require(isinstance(extraction, dict) and extraction.get("status") == "pass", f"{label}.extraction must pass")
        require(isinstance(extraction.get("method"), str) and extraction["method"].strip(), f"{label}.extraction.method is required")
        require(isinstance(extraction.get("locator_preserved"), bool) and extraction["locator_preserved"], f"{label} must preserve source locators")
        require(isinstance(extraction.get("ocr_used"), bool), f"{label}.extraction.ocr_used is required")
        require(extraction.get("confidence") in {"high", "reviewed"}, f"{label}.extraction confidence is too low")
    require(len(ids) == len(set(ids)), "document IDs must be unique")
    if require_sealed:
        require(data.get("document_manifest_sha256") == payload_hash(data, "document_manifest_sha256"), "document manifest seal is missing or stale")
    return {"status": "pass", "documents": len(documents), "document_manifest_sha256": payload_hash(data, "document_manifest_sha256")}


def validate_retrieval_pack(data: dict, request: dict, manifest: dict, require_sealed: bool = True) -> dict:
    validate_document_manifest(manifest, request)
    require(isinstance(data, dict) and data.get("schema_version") == 1, "retrieval pack schema_version must be 1")
    require(data.get("request_manifest_sha256") == request["request_manifest_sha256"], "retrieval request hash is stale")
    require(data.get("document_manifest_sha256") == manifest["document_manifest_sha256"], "retrieval document manifest hash is stale")
    chunking = data.get("chunking")
    require(isinstance(chunking, dict), "retrieval chunking metadata is required")
    require(chunking.get("method") in {"heading_page_aware", "section_locator_aware", "table_aware", "hybrid"}, "retrieval chunking method is invalid")
    require(isinstance(chunking.get("version"), int) and chunking["version"] >= 1, "retrieval chunking version is invalid")
    targets = data.get("targets")
    require(isinstance(targets, list) and targets, "retrieval pack needs targets")
    document_ids = {document["id"] for document in manifest["documents"]}
    target_ids = []
    chunk_keys = set()
    for target_index, target in enumerate(targets, start=1):
        label = f"targets[{target_index}]"
        require(isinstance(target, dict), f"{label} must be an object")
        target_id = target.get("target_id")
        require(isinstance(target_id, str) and target_id.strip(), f"{label}.target_id is required")
        target_ids.append(target_id)
        require(isinstance(target.get("query"), str) and len(target["query"].strip()) >= 3, f"{label}.query is too short")
        require(target.get("coverage") in COVERAGE, f"{label}.coverage is invalid")
        require(isinstance(target.get("conflicts"), list), f"{label}.conflicts must be a list")
        chunks = target.get("selected_chunks")
        require(isinstance(chunks, list), f"{label}.selected_chunks must be a list")
        if target["coverage"] == "sufficient":
            require(bool(chunks), f"{label} sufficient coverage needs selected chunks")
            require(not target["conflicts"], f"{label} cannot be sufficient with unresolved conflicts")
        for chunk_index, chunk in enumerate(chunks, start=1):
            chunk_label = f"{label}.selected_chunks[{chunk_index}]"
            require(isinstance(chunk, dict), f"{chunk_label} must be an object")
            require(chunk.get("document_id") in document_ids, f"{chunk_label} references an unknown document")
            require(isinstance(chunk.get("chunk_id"), str) and re.fullmatch(r"chunk-[a-z0-9][a-z0-9-]{1,95}", chunk["chunk_id"]), f"{chunk_label}.chunk_id is invalid")
            require(isinstance(chunk.get("locator"), str) and chunk["locator"].strip(), f"{chunk_label}.locator is required")
            require(isinstance(chunk.get("chunk_sha256"), str) and re.fullmatch(r"[0-9a-f]{64}", chunk["chunk_sha256"]), f"{chunk_label}.chunk_sha256 is required")
            require(chunk.get("relevance") in RELEVANCE, f"{chunk_label}.relevance is invalid")
            require(isinstance(chunk.get("support_summary"), str) and len(chunk["support_summary"].strip()) >= 8, f"{chunk_label}.support_summary is too short")
            chunk_keys.add((chunk["document_id"], chunk["chunk_id"], chunk["chunk_sha256"]))
    require(len(target_ids) == len(set(target_ids)), "retrieval target IDs must be unique")
    if require_sealed:
        require(data.get("retrieval_pack_sha256") == payload_hash(data, "retrieval_pack_sha256"), "retrieval pack seal is missing or stale")
    return {"status": "pass", "targets": len(targets), "unique_chunks": len(chunk_keys), "retrieval_pack_sha256": payload_hash(data, "retrieval_pack_sha256")}


def seal_manifest(args):
    draft, request = read_json(args.input), read_json(args.request_manifest)
    draft["schema_version"] = 1
    draft["request_manifest_sha256"] = request.get("request_manifest_sha256")
    draft.pop("document_manifest_sha256", None)
    for document in draft.get("documents", []):
        if document.get("source_path"):
            path = Path(document["source_path"])
            if path.is_file():
                document["file_sha256"] = file_hash(path)
    validate_document_manifest(draft, request, require_sealed=False)
    draft["document_manifest_sha256"] = payload_hash(draft, "document_manifest_sha256")
    validate_document_manifest(draft, request)
    write_json(args.output, draft)
    print(json.dumps({"status": "pass", "output": str(args.output), "document_manifest_sha256": draft["document_manifest_sha256"]}, ensure_ascii=False))


def seal_retrieval(args):
    draft, request, manifest = read_json(args.input), read_json(args.request_manifest), read_json(args.document_manifest)
    draft["schema_version"] = 1
    draft["request_manifest_sha256"] = request.get("request_manifest_sha256")
    draft["document_manifest_sha256"] = manifest.get("document_manifest_sha256")
    draft.pop("retrieval_pack_sha256", None)
    validate_retrieval_pack(draft, request, manifest, require_sealed=False)
    draft["retrieval_pack_sha256"] = payload_hash(draft, "retrieval_pack_sha256")
    validate_retrieval_pack(draft, request, manifest)
    write_json(args.output, draft)
    print(json.dumps({"status": "pass", "output": str(args.output), "retrieval_pack_sha256": draft["retrieval_pack_sha256"]}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)
    manifest = subs.add_parser("seal-manifest")
    manifest.add_argument("--input", type=Path, required=True)
    manifest.add_argument("--request-manifest", type=Path, required=True)
    manifest.add_argument("--output", type=Path, required=True)
    manifest.set_defaults(func=seal_manifest)
    retrieval = subs.add_parser("seal-retrieval")
    retrieval.add_argument("--input", type=Path, required=True)
    retrieval.add_argument("--request-manifest", type=Path, required=True)
    retrieval.add_argument("--document-manifest", type=Path, required=True)
    retrieval.add_argument("--output", type=Path, required=True)
    retrieval.set_defaults(func=seal_retrieval)
    args = parser.parse_args()
    try:
        args.func(args)
    except GroundingError as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
