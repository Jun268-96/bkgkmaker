#!/usr/bin/env python3
"""Exercise every active elementary route plus generic quiz and CSV gates."""

from __future__ import annotations

import tempfile
from pathlib import Path

import curriculum_wiki
import quiz_harness


ORDINALS = ["첫째", "둘째", "셋째", "넷째"]


def synthetic_quiz(pack: dict, blueprint: dict) -> dict:
    route = pack.get("route") or {"subject": "검증", "grade": 4}
    questions = []
    for index, slot in enumerate(blueprint["slots"]):
        correct_index = index % 4
        choices = [f"{ORDINALS[index]} 문항의 {ORDINALS[choice_index]} 선택" for choice_index in range(4)]
        distractor_indices = [choice_index for choice_index in range(4) if choice_index != correct_index]
        misconceptions = [slot["misconception_target"], "alternative_error_a", "alternative_error_b"]
        questions.append({
            **{key: value for key, value in slot.items() if key != "misconception_target"},
            "prompt": f"{ORDINALS[index]} 구조 검증 문항에서 조건에 맞는 선택지를 고르세요.",
            "choices": choices,
            "correct_index": correct_index,
            "answer_explanation": "정해진 검증 조건과 일치하는 선택지입니다.",
            "verification": {"kind": "exact_text", "expected_answer": choices[correct_index]},
            "distractors": [
                {"choice_index": choice_index, "misconception": misconception, "reason": "검증 조건의 일부를 다르게 적용함"}
                for choice_index, misconception in zip(distractor_indices, misconceptions)
            ],
            "time_limit": 30,
        })
    metadata = {
        "title": f"{route['subject']} 구조 회귀 검증",
        "grade": route["grade"],
        "subject": route["subject"],
        "unit": route.get("unit") or "구조 회귀 검증",
        "curriculum": "2022 개정 교육과정",
        "curriculum_mode": pack["curriculum_mode"],
        "knowledge_pack_sha256": pack["knowledge_pack_sha256"],
    }
    if pack["rules"].get("requires_teacher_scope"):
        metadata["teacher_scope"] = "학급에서 정한 구조 회귀 검증 활동"
    return {"metadata": metadata, "questions": questions}


def main():
    lint = curriculum_wiki.lint_wiki()
    index = curriculum_wiki.load_index()
    route_count = 0
    question_count = 0

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        for route_index, route in enumerate(index["routes"]):
            unit = "전 범위"
            pack = curriculum_wiki.build_pack("strict", route["subject"], route["grades"][0], None, unit)
            blueprint = quiz_harness.make_blueprint(4, 1000 + route_index, pack)
            quiz = synthetic_quiz(pack, blueprint)
            quiz_harness.validate_quiz(quiz, pack, blueprint)
            review = quiz_harness.make_review_packet(quiz, pack)
            for question, review_item in zip(quiz["questions"], review["questions"]):
                review_item["selected_index"] = question["correct_index"]
                review_item["scope_pass"] = True
                review_item["reasoning"] = "정답 위치와 범위 조건을 독립적으로 다시 확인했습니다."
            quiz_harness.validate_review(quiz, review, pack)

            gimkit_rows, blooket_rows, _ = quiz_harness.export_rows(quiz)
            gimkit_path = temp_root / f"gimkit-{route_index}.csv"
            blooket_path = temp_root / f"blooket-{route_index}.csv"
            quiz_harness.write_csv(gimkit_path, gimkit_rows)
            quiz_harness.write_csv(blooket_path, blooket_rows)
            quiz_harness.validate_csv_roundtrip(quiz, gimkit_path, blooket_path)
            route_count += 1
            question_count += len(quiz["questions"])

        for override in index["unit_overrides"]:
            pack = curriculum_wiki.build_pack(
                "strict", override["subject"], override["grade"], str(override["semester"]), override["unit"]
            )
            if not pack["route"]["unit_override_applied"]:
                raise AssertionError(f"Unit override did not apply: {override}")
            quiz_harness.make_blueprint(20, 20260627, pack)

        inactive = index["inactive_subjects"][0]
        try:
            curriculum_wiki.build_pack("strict", inactive["subject"], inactive["grades"][0], None, None)
        except curriculum_wiki.WikiError:
            pass
        else:
            raise AssertionError("Inactive future subject was routed as active")

        for label, operation in (
            ("missing strict non-math topic", lambda: curriculum_wiki.build_pack("strict", "사회", 6, None, None)),
            ("unresolved strict non-math topic", lambda: curriculum_wiki.build_pack("strict", "사회", 6, None, "존재하지 않는 주제")),
        ):
            try:
                operation()
            except curriculum_wiki.WikiError:
                pass
            else:
                raise AssertionError(f"Strict route did not fail closed: {label}")

        topic_pack = curriculum_wiki.build_pack("strict", "사회", 6, None, "대륙과 대양")
        full_pack = curriculum_wiki.build_pack("strict", "사회", 6, None, "전 범위")
        if topic_pack["knowledge_pack_sha256"] == full_pack["knowledge_pack_sha256"]:
            raise AssertionError("Topic selection was not included in the knowledge-pack hash")

    print(
        f"PASS: {lint['routes']} routes linted; {route_count} route packs, "
        f"{question_count} synthetic questions, {len(index['unit_overrides'])} unit overrides, and CSV round trips checked"
    )


if __name__ == "__main__":
    main()
