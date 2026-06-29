# Analysis report

`analysis-report.json` is a teacher-facing audit artifact generated during `build`. It does not replace `validation-report.json`.

- `validation-report.json`: machine gate statuses, hashes, route, distribution, review contexts, and CSV readiness.
- `analysis-report.json`: concise, checkable summaries that help a teacher inspect each item.

The analysis report contains:

1. Request, quiz, curriculum route, semester limitation, and distribution summaries.
2. Fact claims, support summaries, evidence hashes, stability, expiry, and sources.
3. Per-question standard mapping, scope evidence, subject-adapter review, item type, cognitive level, difficulty basis, content target, task contract, and stimulus.
4. Correct answer, verification kind, answer proof, blind-review result, ambiguity result, and rejected-answer summaries.
5. Distractor misconception, design reason, why it is wrong, CSV mapping, and risk flags.
6. Structural CSV readiness and the explicit live-import verification state.
7. For custom scope: learning objective, audience, adapter, in/out scope, and safety results.
8. For document grounding: document display name, rights basis, extraction metadata, retrieval coverage, chunk locator/hash, and per-question citations.

Do not place hidden chain-of-thought, long copyrighted excerpts, student personal data, or unsupported certainty claims in this report. Use short evidence summaries already present in the sealed artifacts and reviews.
