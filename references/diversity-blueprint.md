# Cross-subject diversity blueprint

Change what the student must think about, not just names, numbers, or surface context.

## Required dimensions

Assign these before drafting every item:

1. Achievement standard or explicit teacher scope.
2. Item type: recall, classification, example/non-example, sequence, application, error analysis, evidence reasoning, or comparison.
3. Cognitive level: knowledge, conceptual understanding, application, or reasoning; mathematics may also use procedural.
4. Difficulty: easy, medium, hard, controlled by reasoning steps and evidence rather than obscure vocabulary.
5. Misconception target: a named plausible misunderstanding that produces one distractor.
6. Representation or context: text, short dialogue, table, described observation, situation, procedure, or comparison as the subject permits.
7. Content target: a sealed fact or deterministic rule, distributed to prevent one-concept clustering.
8. Task contract: the observable structure the drafted item must contain.
9. Difficulty basis: the number of linked conditions, representation shifts, or required inferences.
10. Discipline lens: the subject-specific act, such as spatial relation, observation and inference, comprehension, safe procedure, or justified judgment.

In assurance v2 the harness assigns `content_target`, `fact_ids`, `task_contract`, permitted stimulus kinds, and `difficulty_basis`. A label alone is insufficient: the stimulus must be present in the exported prompt and satisfy the assigned contract.

## Default 20-item mix

| Item type | Count |
|---|---:|
| Direct recall | 3 |
| Concept classification | 3 |
| Example/non-example | 2 |
| Sequence/process | 2 |
| Scenario application | 4 |
| Error analysis | 2 |
| Evidence reasoning | 2 |
| Comparison | 2 |

Keep direct recall and bare calculation together at or below 30% for sets of ten or more. For short sets, preserve at least two distinct cognitive acts.

## Subject controls

- 국어·영어: vary comprehension, expression choice, language form, and media interpretation. Use original or licensed passages.
- 수학: vary procedure, representation, estimation, inverse reasoning, error analysis, comparison, and real situations. Apply a concept-specific adapter when available.
- 사회·도덕: distinguish fact, perspective, evidence, rule application, and justified judgment. Avoid treating a debatable value claim as a context-free fact.
- 과학: vary observation, classification, prediction, procedure, evidence, model use, and application. Do not claim an experiment occurred when only text is supplied.
- 실과: include safe procedure, design choice, resource use, digital ethics, and practical judgment. Current safety guidance may require a fresh source check.
- 체육·음악·미술·통합교과: quizzes supplement performance, creation, play, observation, and reflection; they do not replace those outcomes.
- 창의적 체험활동: require the school's activity objective or supplied material before strict content generation.

## Distractor controls

Each wrong answer must trace to a distinct misconception, incomplete criterion, reversed relationship, ignored condition, or sequence error. Reject arbitrary nearby wording, joke answers, overlapping choices, and choices that differ only in grammatical fit.

## Mathematics enforcement

For mathematics, the selected topic profile replaces the generic 20-item mix. It must distribute:

- mathematical acts such as computation, modeling, representation, estimation, inverse reasoning, construction, spatial reasoning, data interpretation, or justification;
- at least the profile's `required_tasks`;
- all available representation families across the set where the item medium permits;
- structural features such as place-value boundaries, equivalent forms, mixed units, nonprototype figures, hidden blocks, nonunit graph scales, or small-sample uncertainty;
- named misconception families specific to number, operation, fraction/decimal, relation, geometry, spatial, measurement, data, or probability learning.

Do not select standards by cycling through the full grade band. Resolve the requested topic first and use only its mapped standards.
