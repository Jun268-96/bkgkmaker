#!/usr/bin/env python3
"""Dependency-free structural validation for this skill package."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def fail(message: str):
    raise SystemExit(f"FAIL: {message}")


def main():
    skill = ROOT / "SKILL.md"
    text = skill.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        fail("SKILL.md frontmatter is missing")
    fields = {}
    for line in match.group(1).splitlines():
        if not line.strip() or ":" not in line:
            fail(f"invalid frontmatter line: {line!r}")
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip()
    if set(fields) != {"name", "description"}:
        fail("frontmatter must contain only name and description")
    if fields["name"] != "create-blooket-gimkit-quizzes":
        fail("skill name is invalid")
    if not re.fullmatch(r"[a-z0-9-]{1,64}", fields["name"]):
        fail("skill name must be lower kebab-case")
    if len(fields["description"]) < 80:
        fail("skill description is too short to trigger reliably")
    required = [
        "agents/openai.yaml",
        "references/assurance-v2.md",
        "references/analysis-report.md",
        "references/branching-workflow.md",
        "references/canonical-format.md",
        "references/custom-scope.md",
        "references/document-grounding.md",
        "references/diversity-blueprint.md",
        "references/platform-formats.md",
        "references/subject-adapters.md",
        "scripts/curriculum_wiki.py",
        "scripts/custom_scope.py",
        "scripts/document_grounding.py",
        "scripts/evidence_pack.py",
        "scripts/quiz_harness.py",
        "scripts/request_manifest.py",
        "scripts/workflow_router.py",
        "scripts/all_subject_self_test.py",
        "scripts/all_subject_v2_self_test.py",
        "scripts/math_self_test.py",
        "scripts/v2_self_test.py",
        "scripts/branching_self_test.py",
    ]
    missing = [path for path in required if not (ROOT / path).is_file()]
    if missing:
        fail(f"required files missing: {missing}")
    interface = (ROOT / "agents/openai.yaml").read_text(encoding="utf-8")
    for key in ("display_name:", "short_description:", "default_prompt:"):
        if key not in interface:
            fail(f"agents/openai.yaml missing {key}")
    print(f"PASS: skill metadata and {len(required)} required resources validated without external packages")


if __name__ == "__main__":
    try:
        main()
    except OSError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
