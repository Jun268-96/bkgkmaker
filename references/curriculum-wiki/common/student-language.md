---
id: elementary-student-language
page_type: audience
status: reviewed
verified_at: 2026-06-27
---

# Elementary student language and item quality

Apply these rules to prompts, every answer choice, and student-facing explanations. Internal JSON field names may use technical English identifiers.

```json curriculum-rules
{
  "audience": "elementary",
  "forbidden_student_terms": {
    "피제수": "나누어지는 수",
    "제수": "나누는 수"
  },
  "wording_rules": [
    "Use terms that appear in the routed grade-band standards or define the term in the prompt.",
    "Prefer one main task per sentence unless comparison or reasoning requires more.",
    "Avoid double negatives, trick wording, and clues caused only by answer length or grammar.",
    "State units and conditions consistently in the prompt and choices.",
    "Do not introduce a technical term only inside an incorrect choice.",
    "For grades 1-2, keep reading load short and do not make decoding difficulty the hidden test unless the target is Korean reading."
  ],
  "item_quality_rules": [
    "Every item must have exactly one defensible answer under the stated conditions.",
    "Distractors must represent a plausible misconception, partial understanding, or category error.",
    "Do not reduce performance, creation, discussion, or practical-skill standards to factual recall only; mark the quiz as a supplementary check.",
    "Do not expose achievement-standard codes in student-facing prompts."
  ],
  "sources": [
    "teacher-reviewed-semester-map-2026-06-27"
  ]
}
```
