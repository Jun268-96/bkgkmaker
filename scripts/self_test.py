#!/usr/bin/env python3
"""Run positive and negative harness checks against a completed fixture."""

from __future__ import annotations

import argparse
import copy
import tempfile
from pathlib import Path

import quiz_harness as harness


def must_fail(label, operation):
    try:
        operation()
    except harness.ValidationError:
        return
    raise AssertionError(f"Expected failure was not detected: {label}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quiz", type=Path, required=True)
    parser.add_argument("--knowledge-pack", type=Path, required=True)
    parser.add_argument("--blueprint", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    args = parser.parse_args()

    quiz = harness.read_json(args.quiz)
    knowledge_pack = harness.read_json(args.knowledge_pack)
    blueprint = harness.read_json(args.blueprint)
    review = harness.read_json(args.review)
    harness.validate_quiz(quiz, knowledge_pack, blueprint)
    harness.validate_review(quiz, review, knowledge_pack)

    wrong_quotient = copy.deepcopy(quiz)
    division_item = next(
        item for item in wrong_quotient["questions"] if item["verification"]["kind"] == "division"
    )
    division_item["verification"]["quotient"] = "999"
    must_fail("wrong quotient", lambda: harness.validate_quiz(wrong_quotient, knowledge_pack, blueprint))

    duplicate_answer = copy.deepcopy(quiz)
    numeric_item = next(
        item
        for item in duplicate_answer["questions"]
        if item["verification"].get("choice_numeric_values")
    )
    numeric_item["verification"]["choice_numeric_values"][1] = numeric_item["verification"]["choice_numeric_values"][0]
    must_fail("numeric duplicate", lambda: harness.validate_quiz(duplicate_answer, knowledge_pack, blueprint))

    stale_review_quiz = copy.deepcopy(quiz)
    stale_review_quiz["questions"][0]["prompt"] += " "
    must_fail("stale review", lambda: harness.validate_review(stale_review_quiz, review, knowledge_pack))

    forbidden_term = copy.deepcopy(quiz)
    forbidden_term["questions"][0]["answer_explanation"] += " 제수"
    must_fail("forbidden student term", lambda: harness.validate_quiz(forbidden_term, knowledge_pack, blueprint))

    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        gimkit_rows, blooket_rows, _ = harness.export_rows(quiz)
        gimkit_path = output_dir / "gimkit.csv"
        blooket_path = output_dir / "blooket.csv"
        harness.write_csv(gimkit_path, gimkit_rows)
        harness.write_csv(blooket_path, blooket_rows)
        harness.validate_csv_roundtrip(quiz, gimkit_path, blooket_path)

    print("PASS: positive build checks and four negative controls")


if __name__ == "__main__":
    main()
