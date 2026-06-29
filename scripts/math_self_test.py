#!/usr/bin/env python3
"""Exercise every elementary mathematics topic profile and verification path."""

from __future__ import annotations

import copy
import tempfile
from pathlib import Path

import curriculum_wiki
import quiz_harness


TOKENS = list("가나다라마바사아자차카타파하") + ["거", "너", "더", "러", "머", "버"]


def choices_for(index: int, kind: str):
    correct_index = index % 4
    if kind == "rational_expression":
        expected = index + 2
        values = [str(expected + offset) for offset in (0, 11, 22, 33)]
        correct = values.pop(0)
        values.insert(correct_index, correct)
        verification = {
            "kind": kind,
            "expression": f"1 + {expected - 1}",
            "expected_value": str(expected),
            "choice_numeric_values": values,
        }
        return values, correct_index, verification
    values = [f"{TOKENS[index]}-{choice_index + 1} 선택" for choice_index in range(4)]
    verification = {"kind": kind}
    if kind == "exact_text":
        verification["expected_answer"] = values[correct_index]
    return values, correct_index, verification


def synthetic_quiz(pack: dict, blueprint: dict) -> dict:
    questions = []
    for index, slot in enumerate(blueprint["slots"]):
        kind = slot["verification_kind"]
        choices, correct_index, verification = choices_for(index, kind)
        incorrect = [choice_index for choice_index in range(4) if choice_index != correct_index]
        misconceptions = [slot["misconception_target"], "secondary_misconception", "tertiary_misconception"]
        top_level = {key: value for key, value in slot.items() if key not in {"misconception_target", "verification_kind"}}
        questions.append({
            **top_level,
            "prompt": f"{TOKENS[index]} 유형의 수학 구조 검증 문항에서 알맞은 답을 고르세요.",
            "choices": choices,
            "correct_index": correct_index,
            "answer_explanation": "계산 또는 개념 조건을 독립적으로 확인한 답입니다.",
            "verification": verification,
            "distractors": [
                {"choice_index": choice_index, "misconception": misconception, "reason": "수학 조건의 일부를 다르게 적용함"}
                for choice_index, misconception in zip(incorrect, misconceptions)
            ],
            "time_limit": 30,
        })
    route = pack["route"]
    return {
        "metadata": {
            "title": f"{pack['rules']['math_topic']['name']} 구조 회귀 검증",
            "grade": route["grade"],
            "subject": "수학",
            "unit": pack["rules"]["math_topic"]["name"],
            "curriculum": "2022 개정 교육과정",
            "curriculum_mode": "strict",
            "knowledge_pack_sha256": pack["knowledge_pack_sha256"],
        },
        "questions": questions,
    }


def must_fail(label, operation):
    try:
        operation()
    except (curriculum_wiki.WikiError, quiz_harness.ValidationError):
        return
    raise AssertionError(f"Expected failure was not detected: {label}")


def main():
    topic_data, _ = curriculum_wiki.load_math_catalog()
    question_count = 0
    rational_control = None
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        for index, topic in enumerate(topic_data["topics"]):
            grade = int(topic["grade_band"].split("-")[1])
            pack = curriculum_wiki.build_pack("strict", "수학", grade, None, topic["name"])
            if pack["route"].get("math_topic_id") != topic["id"]:
                raise AssertionError(f"Topic selection mismatch: {topic['id']}")
            selected = {
                standard["code"] if isinstance(standard, dict) else standard
                for standard in pack["rules"]["standards"]
            }
            if selected != set(topic["standards"]):
                raise AssertionError(f"Standard filtering mismatch: {topic['id']}")
            blueprint = quiz_harness.make_blueprint(20, 3000 + index, pack)
            quiz = synthetic_quiz(pack, blueprint)
            quiz_harness.validate_quiz(quiz, pack, blueprint)
            if rational_control is None and any(question["verification"]["kind"] == "rational_expression" for question in quiz["questions"]):
                rational_control = (copy.deepcopy(quiz), pack, blueprint)
            review = quiz_harness.make_review_packet(quiz, pack)
            for question, item in zip(quiz["questions"], review["questions"]):
                item["selected_index"] = question["correct_index"]
                item["scope_pass"] = True
                item["reasoning"] = "계산 결과와 성취기준 범위를 독립적으로 다시 확인했습니다."
            quiz_harness.validate_review(quiz, review, pack)

            gimkit_rows, blooket_rows, _ = quiz_harness.export_rows(quiz)
            gimkit_path = temp_root / f"g-{index}.csv"
            blooket_path = temp_root / f"b-{index}.csv"
            quiz_harness.write_csv(gimkit_path, gimkit_rows)
            quiz_harness.write_csv(blooket_path, blooket_rows)
            quiz_harness.validate_csv_roundtrip(quiz, gimkit_path, blooket_path)
            question_count += len(quiz["questions"])

        if rational_control is None:
            raise AssertionError("No rational-expression control was generated")
        bad_quiz, bad_pack, bad_blueprint = rational_control
        rational_item = next(question for question in bad_quiz["questions"] if question["verification"]["kind"] == "rational_expression")
        rational_item["verification"]["expected_value"] = "999"
        must_fail("wrong rational result", lambda: quiz_harness.validate_quiz(bad_quiz, bad_pack, bad_blueprint))

        outside_scope, outside_pack, outside_blueprint = rational_control
        outside_scope = copy.deepcopy(outside_scope)
        outside_scope["questions"][0]["standard"] = "[6수04-06]"
        must_fail("off-topic standard", lambda: quiz_harness.validate_quiz(outside_scope, outside_pack, outside_blueprint))

        must_fail("unknown strict topic", lambda: curriculum_wiki.build_pack("strict", "수학", 4, None, "없는 단원"))
        must_fail("ambiguous strict topic", lambda: curriculum_wiki.build_pack("strict", "수학", 6, None, "분수"))
        must_fail("missing strict topic", lambda: curriculum_wiki.build_pack("strict", "수학", 4, None, None))

    print(
        f"PASS: {len(topic_data['topics'])} math topics, {question_count} blueprint-bound questions, "
        "rational/exact/review verification, CSV round trips, and five negative controls checked"
    )


if __name__ == "__main__":
    main()
