#!/usr/bin/env python3
"""Exercise assurance-v2 contracts and reviews across every active elementary route."""

from __future__ import annotations

import tempfile
from datetime import date
from pathlib import Path

import curriculum_wiki
import evidence_pack
import quiz_harness
import request_manifest


def make_fact_pack(pack: dict, index: int) -> dict:
    result = {
        "schema_version": 1,
        "topic": "전 범위",
        "knowledge_pack_sha256": pack["knowledge_pack_sha256"],
        "facts": [{
            "id": f"fact-route-{index:02d}",
            "claim": "이 사실은 전 과목 보증 구조를 검증하기 위한 교사 검토 항목이다.",
            "support_summary": "전 과목 v2 경로의 사실 근거 구조를 점검하는 검토 요약이다.",
            "evidence_sha256": evidence_pack.text_hash(f"all-subject-route-{index}"),
            "source": {
                "id": "all-subject-v2-self-test",
                "title": "전 과목 v2 구조 검증",
                "locator": f"self-test:route/{index}",
                "authority": "teacher_review",
                "verified_at": date.today().isoformat(),
            },
            "stability": "stable",
        }],
    }
    result["fact_pack_sha256"] = evidence_pack.payload_hash(result)
    evidence_pack.validate_fact_pack(result, pack)
    return result


def make_quiz(pack: dict, fact_pack: dict, blueprint: dict, request: dict) -> dict:
    route = pack["route"]
    questions = []
    for index, slot in enumerate(blueprint["slots"]):
        correct = index % 4
        choices = [f"{slot['id']}의 검증 선택 {choice + 1}" for choice in range(4)]
        kind = "none" if "none" in slot["allowed_stimulus_kinds"] else slot["allowed_stimulus_kinds"][0]
        stimulus_text = "" if kind == "none" else f"{route['subject']} {slot['discipline_lens']} 자료를 확인했다."
        top_level = {
            key: value for key, value in slot.items()
            if key not in {"misconception_target", "allowed_stimulus_kinds", "verification_kind"}
        }
        questions.append({
            **top_level,
            "stimulus": {"kind": kind, "text": stimulus_text},
            "prompt": f"{stimulus_text} {slot['item_type']} 구조에 맞는 답을 고르세요.".strip(),
            "choices": choices,
            "correct_index": correct,
            "answer_explanation": "검증용 사실과 제시된 조건을 함께 적용한 정답입니다.",
            "scope_evidence": f"{slot['standard']}에 연결된 전 범위 구조 검증 항목입니다.",
            "answer_proof": f"{slot['fact_ids'][0]}에 기록된 검토 항목을 적용했습니다.",
            "verification": {"kind": "exact_text", "expected_answer": choices[correct]},
            "distractors": [{
                "choice_index": choice,
                "misconception": slot["misconception_target"] if offset == 0 else f"other-{offset}",
                "reason": "검증 조건의 일부를 다르게 적용함",
                "why_wrong": "검증용 사실 또는 제시된 조건과 일치하지 않습니다.",
            } for offset, choice in enumerate([value for value in range(4) if value != correct])],
            "time_limit": 30,
        })
    metadata = {
        "schema_version": 2,
        "assurance_profile": quiz_harness.V2_ASSURANCE_PROFILE,
        "title": f"{route['subject']} v2 경로 검증",
        "grade": route["grade"],
        "subject": route["subject"],
        "unit": route["unit"],
        "curriculum": "2022 개정 교육과정",
        "curriculum_mode": "strict",
        "knowledge_pack_sha256": pack["knowledge_pack_sha256"],
        "fact_pack_sha256": fact_pack["fact_pack_sha256"],
        "request_manifest_sha256": request["request_manifest_sha256"],
    }
    if pack["rules"].get("requires_teacher_scope"):
        metadata["teacher_scope"] = "학교에서 정한 전 범위 구조 검증 활동"
    if route["subject"] in quiz_harness.PERFORMANCE_SUBJECTS:
        metadata["supplementary_assessment_acknowledged"] = True
    return {"metadata": metadata, "questions": questions}


def fill_reviews(quiz: dict, pack: dict, fact_pack: dict, request: dict):
    answer = quiz_harness.make_review_packet(quiz, pack, fact_pack, request)
    answer.update({"review_context": "fresh_context", "reviewer_id": "all-subject-v2", "reviewed_at": date.today().isoformat()})
    by_id = {question["id"]: question for question in quiz["questions"]}
    _, permutations = quiz_harness.review_layout(quiz)
    for item in answer["questions"]:
        selected = permutations[item["id"]].index(by_id[item["id"]]["correct_index"])
        item["selected_index"] = selected
        item["reasoning"] = "검증 사실과 조건을 다시 확인해 선택했습니다."
        item["why_others_wrong"] = {
            str(index): "검증 사실이나 조건과 일치하지 않는 선택입니다."
            for index in range(4) if index != selected
        }
        item["ambiguity_flag"] = False

    scope = quiz_harness.make_scope_review_packet(quiz, pack, fact_pack, request)
    scope.update({"review_context": "fresh_context", "reviewer_id": "all-subject-scope", "reviewed_at": date.today().isoformat()})
    for item in scope["questions"]:
        item["scope_pass"] = True
        item["terminology_pass"] = True
        item["constraints_pass"] = True
        item["discipline_pass"] = True
        item["discipline_reasoning"] = "해당 과목 어댑터의 의미 조건과 사고 활동을 확인했습니다."
        item["reasoning"] = "해당 경로의 성취기준과 초등학생 용어 조건을 확인했습니다."
    return answer, scope


def main():
    routes = curriculum_wiki.load_index()["routes"]
    question_count = 0
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        for index, route in enumerate(routes):
            pack = curriculum_wiki.build_pack("strict", route["subject"], route["grades"][0], None, "전 범위")
            request = {
                "schema_version": 1,
                "grade": route["grades"][0],
                "subject": route["subject"],
                "topic": "전 범위",
                "semester": None,
                "curriculum_mode": "strict",
                "curriculum_mode_source": "explicit_user",
                "question_count": 4,
                "choice_count": 4,
                "default_time_limit": 30,
                "long_time_limit": 45,
                "teacher_constraints": [],
                "seed": 8000 + index,
            }
            request["request_manifest_sha256"] = request_manifest.payload_hash(request)
            request_manifest.validate_request(request)
            facts = make_fact_pack(pack, index)
            blueprint = quiz_harness.make_blueprint(4, 8000 + index, pack, facts, request)
            quiz = make_quiz(pack, facts, blueprint, request)
            quiz_harness.validate_quiz(quiz, pack, blueprint, facts, request)
            answer, scope = fill_reviews(quiz, pack, facts, request)
            quiz_harness.validate_review(quiz, answer, pack, facts, request)
            quiz_harness.validate_scope_review(quiz, scope, pack, facts, request)
            gimkit, blooket, _ = quiz_harness.export_rows(quiz)
            gimkit_path = root / f"g-{index}.csv"
            blooket_path = root / f"b-{index}.csv"
            quiz_harness.write_csv(gimkit_path, gimkit)
            quiz_harness.write_csv(blooket_path, blooket)
            quiz_harness.validate_csv_roundtrip(quiz, gimkit_path, blooket_path)
            question_count += len(quiz["questions"])
    print(f"PASS: {len(routes)} assurance-v2 subject routes, {question_count} contract-bound questions, blind and scope reviews, and CSV byte checks")


if __name__ == "__main__":
    main()
