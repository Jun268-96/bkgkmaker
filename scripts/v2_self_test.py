#!/usr/bin/env python3
"""Exercise assurance-v2 evidence, contracts, blind review, scope review, and CSV gates."""

from __future__ import annotations

import copy
import tempfile
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import curriculum_wiki
import evidence_pack
import quiz_harness
import request_manifest


def must_fail(label, operation):
    try:
        operation()
    except (quiz_harness.ValidationError, evidence_pack.EvidenceError):
        return
    raise AssertionError(f"Expected v2 failure was not detected: {label}")


def build_fixture():
    pack = curriculum_wiki.build_pack("strict", "사회", 6, None, "대륙과 대양")
    request = {
        "schema_version": 1,
        "grade": 6,
        "subject": "사회",
        "topic": "대륙과 대양",
        "semester": None,
        "curriculum_mode": "strict",
        "curriculum_mode_source": "asked_user",
        "question_count": 4,
        "choice_count": 4,
        "default_time_limit": 30,
        "long_time_limit": 45,
        "teacher_constraints": [],
        "seed": 20260628,
    }
    request["request_manifest_sha256"] = request_manifest.payload_hash(request)
    request_manifest.validate_request(request)
    fact_pack = {
        "schema_version": 1,
        "topic": "대륙과 대양",
        "knowledge_pack_sha256": pack["knowledge_pack_sha256"],
        "facts": [
            {
                "id": "fact-continent-ocean-category",
                "claim": "대륙은 큰 육지의 범주이고 대양은 큰 바다의 범주이다.",
                "support_summary": "검토 자료가 대륙과 대양을 서로 다른 지표 범주로 구분한다.",
                "evidence_sha256": evidence_pack.text_hash("대륙과 대양의 범주 구분 근거"),
                "source": {
                    "id": "teacher-reviewed-geography-basics",
                    "title": "초등 지리 기본 개념 검토",
                    "locator": "teacher-review:continents-oceans/category",
                    "authority": "teacher_review",
                    "verified_at": date.today().isoformat(),
                },
                "stability": "stable",
            },
            {
                "id": "fact-korea-in-asia",
                "claim": "우리나라는 아시아 대륙에 위치한다.",
                "support_summary": "검토 자료에서 우리나라의 대륙 위치를 아시아로 확인했다.",
                "evidence_sha256": evidence_pack.text_hash("우리나라의 아시아 위치 근거"),
                "source": {
                    "id": "teacher-reviewed-geography-basics",
                    "title": "초등 지리 기본 개념 검토",
                    "locator": "teacher-review:continents-oceans/korea",
                    "authority": "teacher_review",
                    "verified_at": date.today().isoformat(),
                },
                "stability": "stable",
            },
        ],
    }
    fact_pack["fact_pack_sha256"] = evidence_pack.payload_hash(fact_pack)
    evidence_pack.validate_fact_pack(fact_pack, pack)
    blueprint = quiz_harness.make_blueprint(4, 20260628, pack, fact_pack, request)
    questions = []
    for index, slot in enumerate(blueprint["slots"]):
        correct_index = index % 4
        choices = [f"{slot['id']} 선택 {choice + 1}" for choice in range(4)]
        kind = "none" if "none" in slot["allowed_stimulus_kinds"] else slot["allowed_stimulus_kinds"][0]
        stimulus_text = "" if kind == "none" else f"{slot['item_type']} 활동을 위한 대륙과 대양 자료를 살펴보았다."
        prompt = f"{stimulus_text} {slot['item_type']} 조건에 맞는 답을 고르세요.".strip()
        top_level = {
            key: value for key, value in slot.items()
            if key not in {"misconception_target", "allowed_stimulus_kinds", "verification_kind"}
        }
        incorrect = [choice for choice in range(4) if choice != correct_index]
        questions.append({
            **top_level,
            "prompt": prompt,
            "choices": choices,
            "correct_index": correct_index,
            "answer_explanation": "검토된 사실 근거와 문항의 조건이 일치하는 선택입니다.",
            "verification": {"kind": "exact_text", "expected_answer": choices[correct_index]},
            "stimulus": {"kind": kind, "text": stimulus_text},
            "scope_evidence": f"{slot['standard']}의 대륙과 대양 위치 이해 범위에 직접 해당합니다.",
            "answer_proof": f"{slot['fact_ids'][0]}에 기록된 검토 사실과 조건을 적용했습니다.",
            "distractors": [
                {
                    "choice_index": choice,
                    "misconception": slot["misconception_target"] if offset == 0 else f"secondary-{offset}",
                    "reason": "문항 조건의 일부를 잘못 적용함",
                    "why_wrong": "검토된 사실 근거 또는 제시된 분류 조건과 일치하지 않습니다.",
                }
                for offset, choice in enumerate(incorrect)
            ],
            "time_limit": 30,
        })
    quiz = {
        "metadata": {
            "schema_version": 2,
            "assurance_profile": quiz_harness.V2_ASSURANCE_PROFILE,
            "title": "초등 6학년 사회 대륙과 대양 v2 검증",
            "grade": 6,
            "subject": "사회",
            "unit": "대륙과 대양",
            "curriculum": "2022 개정 교육과정",
            "curriculum_mode": "strict",
            "knowledge_pack_sha256": pack["knowledge_pack_sha256"],
            "fact_pack_sha256": fact_pack["fact_pack_sha256"],
            "request_manifest_sha256": request["request_manifest_sha256"],
        },
        "questions": questions,
    }
    return request, pack, fact_pack, blueprint, quiz


def fill_answer_review(quiz, pack, fact_pack, request):
    review = quiz_harness.make_review_packet(quiz, pack, fact_pack, request)
    _, permutations = quiz_harness.review_layout(quiz)
    by_id = {question["id"]: question for question in quiz["questions"]}
    review.update({"review_context": "fresh_context", "reviewer_id": "v2-self-test", "reviewed_at": date.today().isoformat()})
    for item in review["questions"]:
        question = by_id[item["id"]]
        selected = permutations[item["id"]].index(question["correct_index"])
        item["selected_index"] = selected
        item["reasoning"] = "제시된 조건과 검토 사실을 다시 적용해 정답을 선택했습니다."
        item["why_others_wrong"] = {
            str(index): "조건 또는 검토 사실과 일치하지 않는 선택입니다."
            for index in range(4) if index != selected
        }
        item["ambiguity_flag"] = False
    return review


def fill_scope_review(quiz, pack, fact_pack, request):
    review = quiz_harness.make_scope_review_packet(quiz, pack, fact_pack, request)
    review.update({"review_context": "fresh_context", "reviewer_id": "v2-scope-test", "reviewed_at": date.today().isoformat()})
    for item in review["questions"]:
        item["scope_pass"] = True
        item["terminology_pass"] = True
        item["constraints_pass"] = True
        item["discipline_pass"] = True
        item["discipline_reasoning"] = "사회과의 공간 관계와 사실 판단 관점에서 다시 확인했습니다."
        item["reasoning"] = "선택된 성취기준의 대륙과 대양 범위 및 초등학생 용어에 맞습니다."
    return review


def main():
    request, pack, fact_pack, blueprint, quiz = build_fixture()
    quiz_harness.validate_quiz(quiz, pack, blueprint, fact_pack, request)
    answer_review = fill_answer_review(quiz, pack, fact_pack, request)
    scope_review = fill_scope_review(quiz, pack, fact_pack, request)
    quiz_harness.validate_review(quiz, answer_review, pack, fact_pack, request)
    quiz_harness.validate_scope_review(quiz, scope_review, pack, fact_pack, request)

    bad_fact = copy.deepcopy(quiz)
    bad_fact["questions"][0]["fact_ids"] = ["fact-does-not-exist"]
    must_fail("unknown fact", lambda: quiz_harness.validate_quiz(bad_fact, pack, blueprint, fact_pack, request))

    bad_contract = copy.deepcopy(quiz)
    bad_contract["questions"][0]["stimulus"] = {"kind": "unrelated", "text": "관련 없는 자료입니다."}
    must_fail("invalid item contract", lambda: quiz_harness.validate_quiz(bad_contract, pack, blueprint, fact_pack, request))

    bad_proof = copy.deepcopy(quiz)
    bad_proof["questions"][0]["answer_proof"] = "근거 식별자를 포함하지 않은 설명입니다."
    must_fail("uncited answer proof", lambda: quiz_harness.validate_quiz(bad_proof, pack, blueprint, fact_pack, request))

    ambiguous = copy.deepcopy(answer_review)
    ambiguous["questions"][0]["ambiguity_flag"] = True
    must_fail("ambiguous answer", lambda: quiz_harness.validate_review(quiz, ambiguous, pack, fact_pack, request))

    bad_scope = copy.deepcopy(scope_review)
    bad_scope["questions"][0]["scope_pass"] = False
    must_fail("strict scope rejection", lambda: quiz_harness.validate_scope_review(quiz, bad_scope, pack, fact_pack, request))

    stale_request = copy.deepcopy(request)
    stale_request["teacher_constraints"] = ["변경된 조건"]
    must_fail("stale request manifest", lambda: quiz_harness.validate_quiz(quiz, pack, blueprint, fact_pack, stale_request))

    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        for name, data in (
            ("request.json", request),
            ("knowledge.json", pack),
            ("facts.json", fact_pack),
            ("blueprint.json", blueprint),
            ("questions.json", quiz),
            ("answer-review.json", answer_review),
            ("scope-review.json", scope_review),
        ):
            quiz_harness.write_json(output_dir / name, data)
        built = output_dir / "built"
        quiz_harness.command_build(SimpleNamespace(
            input=output_dir / "questions.json",
            request_manifest=output_dir / "request.json",
            knowledge_pack=output_dir / "knowledge.json",
            fact_pack=output_dir / "facts.json",
            blueprint=output_dir / "blueprint.json",
            review=output_dir / "answer-review.json",
            scope_review=output_dir / "scope-review.json",
            output_dir=built,
        ))
        report = quiz_harness.read_json(built / "validation-report.json")
        if report["assurance"]["profile"] != quiz_harness.V2_ASSURANCE_PROFILE:
            raise AssertionError("End-to-end build did not report v2 assurance")
        analysis = quiz_harness.read_json(built / "analysis-report.json")
        if analysis.get("report_kind") != "teacher_audit_summary" or len(analysis.get("questions", [])) != 4:
            raise AssertionError("Analysis report is missing question-level audit content")
        if analysis["questions"][0]["answer_analysis"]["blind_review_pass"] is not True:
            raise AssertionError("Analysis report did not preserve the blind-review result")
        if "analysis-report.json" not in report["files"]:
            raise AssertionError("Validation report did not hash the analysis report")

        gimkit_rows, blooket_rows, _ = quiz_harness.export_rows(quiz)
        gimkit_path = output_dir / "gimkit.csv"
        blooket_path = output_dir / "blooket.csv"
        quiz_harness.write_csv(gimkit_path, gimkit_rows)
        quiz_harness.write_csv(blooket_path, blooket_rows)
        quiz_harness.validate_csv_roundtrip(quiz, gimkit_path, blooket_path)
        gimkit_path.write_bytes(gimkit_path.read_bytes()[3:])
        must_fail("missing BOM", lambda: quiz_harness.validate_csv_roundtrip(quiz, gimkit_path, blooket_path))

    print("PASS: assurance-v2 evidence, contracts, blind answer review, scope review, mutations, and byte-level CSV gates")


if __name__ == "__main__":
    main()
