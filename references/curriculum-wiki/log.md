---
id: curriculum-wiki-log
page_type: log
status: reviewed
verified_at: 2026-06-27
---

# Change log

## [2026-06-28] assurance v2 | Evidence, contracts, and separated reviews

- Added sealed request manifests so grade, subject, topic, mode, count, timing, constraints, and seed cannot drift downstream.
- Added strict non-mathematics topic filtering with fail-closed standard-text matching and explicit reviewed-standard fallback.
- Included topic selection in the knowledge-pack hash.
- Added sealed fact packs with source authority, support summaries, evidence hashes, stability, and expiry controls.
- Added content targets, task contracts, subject-family lenses, stimulus contracts, difficulty bases, scope evidence, answer proofs, and per-distractor wrong-answer proofs.
- Split shuffled blind answer review from curriculum, terminology, teacher-constraint, and subject-adapter scope review.
- Added byte-level CSV encoding, CRLF, column, mapping, safety, and import-readiness checks.
- Added assurance-v2 regression coverage across all 26 active routes plus mutation and end-to-end build controls.
- Added `analysis-report.json` with teacher-facing curriculum, evidence, item-design, answer-review, distractor, risk, and CSV-mapping summaries for every question.
- Added orthogonal curriculum/custom scope and verified/document grounding branches with a central workflow router.
- Added sealed custom scopes, technology/maker safety policies, document manifests, retrieval packs, chunk provenance, and document-only fact enforcement.

## [2026-06-27] mathematics v2 | Full elementary topic profiles

- Mapped all 121 elementary mathematics achievement standards to 62 topic profiles.
- Added 11 task profiles and 94 prerequisite links across number and operations, change and relationships, geometry and measurement, and data and chance.
- Added strict topic selection so a unit request cannot cycle through unrelated grade-band standards.
- Added mathematical-task, representation, structural-feature, and misconception blueprint dimensions.
- Added exact rational-expression validation for integer, decimal, fraction, measurement, data, and formula calculations.
- Added regression coverage for 1,240 blueprint-bound questions across all 62 topics.

## [2026-06-27] catalog v2 | All active elementary subjects

- Added source-verified grade-band standards for 국어, 수학, 도덕, 사회, 과학, 실과, 체육, 음악, 미술, 영어, 바른 생활, 슬기로운 생활, and 즐거운 생활.
- Added 창의적 체험활동 as a school-scoped curriculum area without national achievement-standard codes.
- Cataloged 건강한 생활 as inactive future curriculum with elementary application from 2028-03-01.
- Separated official grade-band routes from teacher-reviewed semester/unit overrides.
- Added strict, advisory, and off knowledge-pack routing plus all-subject regression tests.

## [2026-06-27] ingest | Grade 6 decimal division pilot

- Added the common audience-language page.
- Added the division spiral-concept page.
- Separated official full grade-band scope from teacher-reviewed semester sequencing.
- Added semester 1, semester 2, and explicit full-year routes.
