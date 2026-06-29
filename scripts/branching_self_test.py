#!/usr/bin/env python3
"""Exercise curriculum/custom and verified/document grounding branch combinations."""

from __future__ import annotations

import copy
import tempfile
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import curriculum_wiki
import custom_scope as custom_spec
import document_grounding as grounding
import evidence_pack
import quiz_harness
import request_manifest
import workflow_router


def must_fail(label, operation):
    try:
        operation()
    except (quiz_harness.ValidationError, grounding.GroundingError, custom_spec.ScopeError):
        return
    raise AssertionError(f"Expected branch failure was not detected: {label}")


def seal_request(scope_mode: str, grounding_mode: str, subject: str, topic: str, grade: int, seed: int) -> dict:
    data = {
        "schema_version": 2,
        "grade": grade,
        "subject": subject,
        "topic": topic,
        "semester": None,
        "curriculum_mode": "off" if scope_mode == "custom" else "strict",
        "curriculum_mode_source": "explicit_user",
        "scope_mode": scope_mode,
        "grounding_mode": grounding_mode,
        "question_count": 4,
        "choice_count": 4,
        "default_time_limit": 30,
        "long_time_limit": 45,
        "teacher_constraints": ["초등학생이 이해할 수 있는 표현 사용"],
        "seed": seed,
    }
    data["request_manifest_sha256"] = request_manifest.payload_hash(data)
    request_manifest.validate_request(data)
    return data


def seal_custom_scope(request: dict) -> dict:
    data = {
        "schema_version": 1,
        "request_manifest_sha256": request["request_manifest_sha256"],
        "topic": request["topic"],
        "adapter": "technology_making",
        "audience": {"grade": request["grade"], "experience": "beginner"},
        "learning_objectives": [
            {"id": "obj-setup-loop", "description": "setup과 loop의 실행 역할을 구분한다."},
            {"id": "obj-safe-led", "description": "LED 기초 연결에서 안전 규칙을 적용한다."},
        ],
        "in_scope": ["setup과 loop", "LED와 저항", "기초 디지털 출력"],
        "out_of_scope": ["가정용 교류 전원", "리튬 배터리 충전", "고전압 릴레이"],
        "terminology": {"allowed": ["핀", "LED", "저항"], "define_before_use": ["디지털 출력"], "forbidden": ["포인터 산술"]},
        "environment": {"board": "Arduino Uno 계열", "language": "Arduino C++"},
        "safety": {
            "level": "standard",
            "required_rules": ["전원을 끈 상태에서 배선을 확인한다.", "LED에는 알맞은 저항을 사용한다."],
            "prohibited_topics": ["가정용 교류 전원", "배터리 충전"],
            "requires_current_official_verification": False,
        },
    }
    data["custom_scope_sha256"] = custom_spec.payload_hash(data)
    custom_spec.validate_scope(data, request)
    return data


def seal_documents(root: Path, request: dict, target_ids: list[str]):
    source = root / "arduino-notes.txt"
    source.write_text("setup은 시작할 때 한 번 실행되고 loop는 반복 실행된다. LED 연결에는 저항을 사용한다.", encoding="utf-8")
    file_sha = grounding.file_hash(source)
    manifest = {
        "schema_version": 1,
        "request_manifest_sha256": request["request_manifest_sha256"],
        "persistence": "ephemeral",
        "untrusted_instructions_ignored": True,
        "documents": [{
            "id": "doc-arduino-notes",
            "display_name": "arduino-notes.txt",
            "source_path": str(source),
            "format": "txt",
            "rights_basis": "user_supplied",
            "file_sha256": file_sha,
            "extraction": {"status": "pass", "method": "plain_text", "locator_preserved": True, "ocr_used": False, "confidence": "high"},
        }],
    }
    manifest["document_manifest_sha256"] = grounding.payload_hash(manifest, "document_manifest_sha256")
    grounding.validate_document_manifest(manifest, request)
    chunk_sha = evidence_pack.text_hash("setup은 시작할 때 한 번 실행되고 loop는 반복 실행된다.")
    retrieval = {
        "schema_version": 1,
        "request_manifest_sha256": request["request_manifest_sha256"],
        "document_manifest_sha256": manifest["document_manifest_sha256"],
        "chunking": {"method": "section_locator_aware", "version": 1},
        "targets": [{
            "target_id": target_id,
            "query": "setup loop LED 저항",
            "coverage": "sufficient",
            "conflicts": [],
            "selected_chunks": [{
                "document_id": "doc-arduino-notes",
                "chunk_id": "chunk-arduino-basics",
                "locator": "1행",
                "chunk_sha256": chunk_sha,
                "relevance": "direct_support",
                "support_summary": "문서가 setup과 loop의 실행 방식 및 LED 저항 사용을 설명한다.",
            }],
        } for target_id in target_ids],
    }
    retrieval["retrieval_pack_sha256"] = grounding.payload_hash(retrieval, "retrieval_pack_sha256")
    grounding.validate_retrieval_pack(retrieval, request, manifest)
    return manifest, retrieval, chunk_sha


def seal_facts(request: dict, pack: dict, documents: bool, target_ids: list[str], chunk_sha: str | None = None) -> dict:
    source = {
        "id": "source-arduino-basics",
        "title": "아두이노 기초 근거",
        "locator": "1행" if documents else "teacher-review:arduino/setup-loop",
        "authority": "user_supplied" if documents else "teacher_review",
        "verified_at": date.today().isoformat(),
    }
    if documents:
        source.update({
            "type": "user_document",
            "document_id": "doc-arduino-notes",
            "chunk_id": "chunk-arduino-basics",
            "chunk_sha256": chunk_sha,
            "retrieval_target_ids": target_ids,
        })
    facts = {
        "schema_version": 1,
        "topic": request["topic"],
        "knowledge_pack_sha256": pack["knowledge_pack_sha256"],
        "facts": [{
            "id": "fact-setup-runs-once",
            "claim": "setup은 프로그램 시작 시 한 번 실행된다.",
            "support_summary": "검토 근거가 setup의 실행 횟수를 한 번으로 설명한다.",
            "evidence_sha256": evidence_pack.text_hash("setup one time"),
            "source": source,
            "stability": "stable",
        }],
    }
    facts["fact_pack_sha256"] = evidence_pack.payload_hash(facts)
    evidence_pack.validate_fact_pack(facts, pack)
    return facts


def make_quiz(request, pack, facts, blueprint, custom, manifest, retrieval):
    questions = []
    for index, slot in enumerate(blueprint["slots"]):
        correct = index % 4
        choices = [f"{slot['id']} 선택 {choice + 1}" for choice in range(4)]
        kind = "none" if "none" in slot["allowed_stimulus_kinds"] else slot["allowed_stimulus_kinds"][0]
        stimulus = "" if kind == "none" else f"{slot['discipline_lens']} 아두이노 자료를 살펴보았다."
        top_level = {key: value for key, value in slot.items() if key not in {"misconception_target", "allowed_stimulus_kinds", "verification_kind"}}
        questions.append({
            **top_level,
            "stimulus": {"kind": kind, "text": stimulus},
            "prompt": f"{stimulus} {slot['item_type']} 조건에 맞는 답을 고르세요.".strip(),
            "choices": choices,
            "correct_index": correct,
            "answer_explanation": "제공된 근거와 조건에 일치하는 선택입니다.",
            "scope_evidence": f"{slot['standard']} 또는 사용자 정의 학습 목표 범위에 해당합니다.",
            "answer_proof": f"{slot['fact_ids'][0]}의 근거를 적용했습니다.",
            "verification": {"kind": "exact_text", "expected_answer": choices[correct]},
            "distractors": [{
                "choice_index": choice,
                "misconception": slot["misconception_target"] if offset == 0 else f"other-{offset}",
                "reason": "조건 일부를 다르게 적용함",
                "why_wrong": "제공된 사실 또는 문항 조건과 일치하지 않습니다.",
            } for offset, choice in enumerate([value for value in range(4) if value != correct])],
            "time_limit": 30,
        })
    metadata = {
        "schema_version": 2,
        "assurance_profile": quiz_harness.V2_ASSURANCE_PROFILE,
        "title": f"{request['topic']} 분기 검증",
        "grade": request["grade"],
        "subject": request["subject"],
        "unit": request["topic"],
        "curriculum": "2022 개정 교육과정" if request["scope_mode"] == "curriculum" else "not_applicable",
        "curriculum_mode": request["curriculum_mode"],
        "knowledge_pack_sha256": pack["knowledge_pack_sha256"],
        "fact_pack_sha256": facts["fact_pack_sha256"],
        "request_manifest_sha256": request["request_manifest_sha256"],
    }
    if custom:
        metadata["custom_scope_sha256"] = custom["custom_scope_sha256"]
    if manifest:
        metadata["document_manifest_sha256"] = manifest["document_manifest_sha256"]
        metadata["retrieval_pack_sha256"] = retrieval["retrieval_pack_sha256"]
    return {"metadata": metadata, "questions": questions}


def fill_reviews(quiz, pack, facts, request, custom, manifest, retrieval):
    answer = quiz_harness.make_review_packet(quiz, pack, facts, request, custom, manifest, retrieval)
    answer.update({"review_context": "fresh_context", "reviewer_id": "branch-test-answer", "reviewed_at": date.today().isoformat()})
    by_id = {question["id"]: question for question in quiz["questions"]}
    _, permutations = quiz_harness.review_layout(quiz)
    for item in answer["questions"]:
        selected = permutations[item["id"]].index(by_id[item["id"]]["correct_index"])
        item["selected_index"] = selected
        item["reasoning"] = "근거와 조건을 다시 적용하여 정답을 확인했습니다."
        item["why_others_wrong"] = {str(i): "근거 또는 조건과 일치하지 않는 선택입니다." for i in range(4) if i != selected}
        item["ambiguity_flag"] = False
    scope = quiz_harness.make_scope_review_packet(quiz, pack, facts, request, custom, manifest, retrieval)
    scope.update({"review_context": "fresh_context", "reviewer_id": "branch-test-scope", "reviewed_at": date.today().isoformat()})
    for item in scope["questions"]:
        item["scope_pass"] = True
        item["terminology_pass"] = True
        item["constraints_pass"] = True
        item["discipline_pass"] = True
        item["discipline_reasoning"] = "선택된 과목 또는 사용자 정의 어댑터의 의미 조건을 확인했습니다."
        item["reasoning"] = "요청 범위와 근거 및 초등 대상 표현에 맞는지 확인했습니다."
        if custom:
            item["custom_scope_pass"] = True
            item["audience_pass"] = True
            item["safety_pass"] = True
    return answer, scope


def run_branch(root: Path, scope_mode: str, grounding_mode: str, seed: int, build: bool = False):
    curriculum = scope_mode == "curriculum"
    request = seal_request(scope_mode, grounding_mode, "사회" if curriculum else "아두이노", "대륙과 대양" if curriculum else "아두이노 기초", 6, seed)
    pack = curriculum_wiki.build_pack("strict", "사회", 6, None, "대륙과 대양") if curriculum else curriculum_wiki.build_pack("off", None, None, None, None)
    custom = None if curriculum else seal_custom_scope(request)
    target_ids = ["[6사09-02]"] if curriculum else [objective["id"] for objective in custom["learning_objectives"]]
    manifest = retrieval = chunk_sha = None
    if grounding_mode != "verified_sources":
        manifest, retrieval, chunk_sha = seal_documents(root, request, target_ids)
    facts = seal_facts(request, pack, manifest is not None, target_ids, chunk_sha)
    blueprint = quiz_harness.make_blueprint(4, seed, pack, facts, request, custom, manifest, retrieval)
    quiz = make_quiz(request, pack, facts, blueprint, custom, manifest, retrieval)
    quiz_harness.validate_quiz(quiz, pack, blueprint, facts, request, custom, manifest, retrieval)
    answer, scope = fill_reviews(quiz, pack, facts, request, custom, manifest, retrieval)
    quiz_harness.validate_review(quiz, answer, pack, facts, request, custom, manifest, retrieval)
    quiz_harness.validate_scope_review(quiz, scope, pack, facts, request, custom, manifest, retrieval)
    expected_branch = f"{scope_mode}_{'documents' if manifest else 'verified_sources'}"
    if build:
        case = root / expected_branch
        case.mkdir()
        files = {
            "request.json": request, "pack.json": pack, "facts.json": facts, "blueprint.json": blueprint,
            "quiz.json": quiz, "answer.json": answer, "scope.json": scope,
        }
        if custom:
            files["custom.json"] = custom
        if manifest:
            files["manifest.json"] = manifest
            files["retrieval.json"] = retrieval
        for name, data in files.items():
            quiz_harness.write_json(case / name, data)
        routed = workflow_router.build_plan(SimpleNamespace(
            request_manifest=case / "request.json",
            knowledge_pack=case / "pack.json",
            custom_scope=case / "custom.json" if custom else None,
            document_manifest=case / "manifest.json" if manifest else None,
            retrieval_pack=case / "retrieval.json" if retrieval else None,
            fact_pack=case / "facts.json",
            blueprint=case / "blueprint.json",
            answer_review=case / "answer.json",
            scope_review=case / "scope.json",
        ))
        if routed["branch"] != expected_branch or routed["status"] != "ready_to_build":
            raise AssertionError("Workflow router did not resolve the completed branch")

        forbidden = copy.deepcopy(quiz)
        forbidden["questions"][0]["prompt"] += " 포인터 산술"
        must_fail("custom forbidden terminology", lambda: quiz_harness.validate_quiz(forbidden, pack, blueprint, facts, request, custom, manifest, retrieval))

        external_fact = copy.deepcopy(facts)
        external_fact["facts"][0]["source"].pop("type", None)
        must_fail("documents-only external fact", lambda: quiz_harness.validate_fact_grounding(external_fact, request, manifest, retrieval))

        conflicting = copy.deepcopy(retrieval)
        conflicting["targets"][0]["coverage"] = "conflicting"
        conflicting["targets"][0]["conflicts"] = ["서로 다른 실행 설명"]
        conflicting["retrieval_pack_sha256"] = grounding.payload_hash(conflicting, "retrieval_pack_sha256")
        must_fail("retrieval conflict", lambda: quiz_harness.validate_document_grounding(manifest, conflicting, request, required=True))

        unsafe_review = copy.deepcopy(scope)
        unsafe_review["questions"][0]["safety_pass"] = False
        must_fail("custom safety review", lambda: quiz_harness.validate_scope_review(quiz, unsafe_review, pack, facts, request, custom, manifest, retrieval))

        output = case / "output"
        quiz_harness.command_build(SimpleNamespace(
            input=case / "quiz.json", knowledge_pack=case / "pack.json", fact_pack=case / "facts.json",
            request_manifest=case / "request.json", custom_scope=case / "custom.json" if custom else None,
            document_manifest=case / "manifest.json" if manifest else None, retrieval_pack=case / "retrieval.json" if retrieval else None,
            blueprint=case / "blueprint.json", review=case / "answer.json", scope_review=case / "scope.json", output_dir=output,
        ))
        analysis = quiz_harness.read_json(output / "analysis-report.json")
        if custom and analysis["custom_scope_analysis"] is None:
            raise AssertionError("Custom branch was not included in analysis report")
        if manifest and analysis["document_grounding_analysis"] is None:
            raise AssertionError("Document branch was not included in analysis report")
    return expected_branch


def main():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        branches = {
            run_branch(root, "curriculum", "verified_sources", 9101),
            run_branch(root, "curriculum", "documents_only", 9102),
            run_branch(root, "custom", "verified_sources", 9103),
            run_branch(root, "custom", "documents_only", 9104, build=True),
        }
    expected = {"curriculum_verified_sources", "curriculum_documents", "custom_verified_sources", "custom_documents"}
    if branches != expected:
        raise AssertionError(f"Branch coverage mismatch: {branches}")
    print("PASS: four scope/grounding branches, custom safety scope, document citations, reviews, and end-to-end analysis build")


if __name__ == "__main__":
    main()
