# Custom scope

Use for intentionally non-curriculum topics. Keep `curriculum_mode: off` and `scope_mode: custom`.

A custom scope must contain:

- topic and request hash;
- elementary grade and experience level;
- adapter: `general_knowledge`, `technology_making`, `coding`, `safety_training`, or `document_comprehension`;
- stable learning-objective IDs and descriptions;
- explicit in-scope and out-of-scope content;
- allowed, define-before-use, and forbidden terminology;
- environment details such as board, software, version, language, or kit;
- safety level, required rules, prohibited topics, and whether current official verification is mandatory.

Every question uses `standard: "unmapped"` plus a blueprint-bound `learning_objective_id`. Scope review must independently pass custom scope, audience, terminology, teacher constraints, adapter meaning, and safety.

For technology and maker topics, do not include household mains electricity, battery charging, high-voltage relays, external motor power, soldering, or other higher-risk work unless the explicit scope, current official facts, equipment conditions, and supervision requirements support it. A prohibited topic is never usable as a distractor if merely seeing it would normalize unsafe practice without explanation.
