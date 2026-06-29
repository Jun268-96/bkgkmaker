# Canonical quiz format v2

Use one JSON source for both platforms. Store student-facing strings exactly as exported and use a zero-based `correct_index`.

```json
{
  "metadata": {
    "schema_version": 2,
    "assurance_profile": "curriculum-evidence-v2",
    "title": "초등 6학년 사회 - 대륙과 대양",
    "grade": 6,
    "subject": "사회",
    "unit": "대륙과 대양",
    "curriculum": "2022 개정 교육과정",
    "curriculum_mode": "strict",
    "knowledge_pack_sha256": "64-character hash",
    "fact_pack_sha256": "64-character hash",
    "request_manifest_sha256": "64-character hash"
  },
  "questions": [
    {
      "id": "q01",
      "standard": "[6사09-02]",
      "item_type": "scenario_application",
      "cognitive_level": "application",
      "difficulty": "medium",
      "content_target": "fact-korea-in-asia",
      "fact_ids": ["fact-korea-in-asia"],
      "task_contract": "apply_rule_to_new_case",
      "discipline_lens": "spatial_relation",
      "difficulty_basis": "two linked conditions, a representation shift, or one inference",
      "stimulus": {
        "kind": "scenario",
        "text": "세계 지도에서 우리나라가 있는 대륙을 찾고 있다."
      },
      "prompt": "세계 지도에서 우리나라가 있는 대륙을 찾고 있다. 어느 대륙을 찾아야 할까요?",
      "choices": ["아시아", "유럽", "아프리카", "오세아니아"],
      "correct_index": 0,
      "answer_explanation": "우리나라는 아시아 대륙에 위치합니다.",
      "scope_evidence": "[6사09-02]의 우리나라 위치 이해 범위에 직접 해당합니다.",
      "answer_proof": "fact-korea-in-asia에 기록된 위치 사실에 따라 아시아가 정답입니다.",
      "verification": {
        "kind": "exact_text",
        "expected_answer": "아시아"
      },
      "distractors": [
        {
          "choice_index": 1,
          "misconception": "confuses_nearby_regions",
          "reason": "우리나라의 대륙 위치를 다른 지역과 혼동함",
          "why_wrong": "유럽은 우리나라가 위치한 대륙이 아닙니다."
        },
        {
          "choice_index": 2,
          "misconception": "category_location_error",
          "reason": "대륙 이름은 알지만 우리나라 위치와 연결하지 못함",
          "why_wrong": "아프리카는 우리나라가 위치한 대륙이 아닙니다."
        },
        {
          "choice_index": 3,
          "misconception": "map_position_error",
          "reason": "세계 지도에서 동아시아 위치를 잘못 찾음",
          "why_wrong": "오세아니아는 우리나라가 위치한 대륙이 아닙니다."
        }
      ],
      "time_limit": 30
    }
  ]
}
```

The blueprint supplies `content_target`, `fact_ids`, `task_contract`, and `difficulty_basis`; copy them exactly. `stimulus.text` must appear in the exported prompt unless the permitted kind is `none`.

## Verification adapters

- `exact_text`: expected text must equal the marked choice.
- `rational_expression`: safe exact expression, expected value, and four numeric choice values.
- `division`: exact decimal division fields and four numeric choice values.
- `review_only`: semantic answer review is mandatory; use only when deterministic recomputation is not possible.

For curriculum mode `off`, use `standard: "unmapped"`. For 창의적 체험활동 without national codes, use `standard: "teacher_scope"` and provide `metadata.teacher_scope`.

For a custom-scope branch, use `standard: "unmapped"`, copy the blueprint's `learning_objective_id`, and include `metadata.custom_scope_sha256`. Document-grounded branches also include document and retrieval hashes; their facts must carry matching document/chunk provenance.

For performance-centered subjects also set `metadata.supplementary_assessment_acknowledged: true`.

## Mathematics fields

Math topic blueprints additionally require `math_task`, `representation`, `structural_feature`, and the prescribed verification kind. Copy every field exactly; do not replace a reasoning task with bare computation.
