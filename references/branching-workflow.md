# Branching workflow

Scope and grounding are independent. Never infer that `curriculum_mode: off` also disables scope or quality checks.

| Branch | Required scope artifacts | Required grounding artifacts |
|---|---|---|
| `curriculum_verified_sources` | topic-scoped curriculum pack | sealed fact pack |
| `curriculum_documents` | topic-scoped curriculum pack | document manifest, retrieval pack, sealed fact pack |
| `custom_verified_sources` | audience pack and custom scope | sealed fact pack |
| `custom_documents` | audience pack and custom scope | document manifest, retrieval pack, sealed fact pack |

`documents_only` requires sufficient retrieval coverage for every target and permits only document-backed answer facts. `documents_preferred` and `mixed_verified` permit declared external facts but still block unresolved conflicts and low-confidence extraction.

Run `workflow_router.py` after sealing the request and after each major artifact. Its `next_artifact` is the next dependency, not an optional suggestion.

The common downstream path is always:

`fact pack → blueprint → canonical questions → candidate gate → blind answer review → scope/safety review → CSV build → validation and analysis reports`.

No branch may skip elementary language, one-answer integrity, distractor proof, review freshness, spreadsheet safety, or CSV round-trip gates.
