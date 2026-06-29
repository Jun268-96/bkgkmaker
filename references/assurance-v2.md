# Assurance v2

Keep scope, answer evidence, assessment design, and export validation separate.

## Request manifest

Seal request schema v2 before routing. Required fields are `grade`, `subject`, `topic`, nullable `semester`, `curriculum_mode`, `curriculum_mode_source`, explicit `scope_mode`, explicit `grounding_mode`, `question_count`, `choice_count: 4`, `default_time_limit`, `long_time_limit`, `teacher_constraints`, and `seed`. The request hash is copied into every downstream artifact and report.

## Fact pack

Each fact is an atomic claim used to establish a correct answer.

```json
{
  "schema_version": 1,
  "topic": "대륙과 대양",
  "facts": [
    {
      "id": "fact-korea-in-asia",
      "claim": "우리나라는 아시아 대륙에 위치한다.",
      "support_summary": "검토 자료가 우리나라의 대륙 위치를 아시아로 제시한다.",
      "evidence_sha256": "hash of the exact evidence snapshot or deterministic derivation",
      "source": {
        "id": "source-id",
        "title": "자료명",
        "locator": "URL, page, section, or teacher-review locator",
        "authority": "official",
        "verified_at": "2026-06-28"
      },
      "stability": "stable"
    }
  ]
}
```

Accepted authorities are `official`, `open_reference`, `teacher_review`, `deterministic_rule`, and `user_supplied`. Use `dynamic` plus a future `expires_at` for changing facts. A fact pack must be sealed with `evidence_pack.py`; hand-written hashes are not accepted.

`support_summary` must paraphrase how the source supports the claim. `evidence_sha256` hashes the exact source excerpt, supplied artifact segment, or deterministic derivation used during review; do not store long copyrighted excerpts in the wiki.

## Four assurance results

1. `structure`: schemas, hashes, blueprint adherence, deterministic adapters, and item contracts.
2. `curriculum_scope`: exact topic route plus a separate scope and terminology review.
3. `answer_review`: shuffled blind solving, three rejected-answer explanations, and explicit ambiguity clearance.
4. `csv_import_readiness`: encoding, record separators, columns, headers, mappings, safety, and round-trip parsing.

`csv_import_readiness` is structural. Only an actual upload may set live import verification to true.

## Review separation

The answer packet omits standards, item types, canonical order, and marked answers. The scope packet contains standards and scope evidence but is reviewed separately. Record the real review context. A fresh context or human review is stronger than a same-context blind pass; the report must preserve that distinction.
