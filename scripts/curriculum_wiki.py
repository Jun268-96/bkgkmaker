#!/usr/bin/env python3
"""Route, merge, hash, and lint the Markdown curriculum wiki."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path


WIKI_ROOT = Path(__file__).resolve().parent.parent / "references" / "curriculum-wiki"
INDEX_PATH = WIKI_ROOT / "index.md"
SOURCE_MANIFEST_PATH = WIKI_ROOT / "source-manifest.md"
MATH_TOPIC_MAP_PATH = WIKI_ROOT / "math" / "topic-map.md"
MATH_TASK_PROFILES_PATH = WIKI_ROOT / "math" / "task-profiles.md"
MATH_FULL_BAND_NAMES = {"전체", "전범위", "학년군전체", "수학전체"}
FULL_BAND_NAMES = MATH_FULL_BAND_NAMES | {"전과정", "전체과정", "전체범위", "과목전체"}
KOREAN_TOPIC_SUFFIXES = (
    "으로부터", "에서부터", "에게서", "까지", "부터", "으로", "에서", "에게", "처럼",
    "보다", "와", "과", "을", "를", "은", "는", "이", "가", "의", "에", "로", "도",
)


class WikiError(Exception):
    pass


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise WikiError(f"Cannot read {path}: {exc}") from exc


def parse_flat_frontmatter(path: Path) -> dict:
    text = read_text(path)
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        raise WikiError(f"Missing frontmatter: {path}")
    result = {}
    for raw_line in match.group(1).splitlines():
        if not raw_line.strip():
            continue
        if ":" not in raw_line or raw_line.startswith((" ", "\t")):
            raise WikiError(f"Frontmatter must be flat in {path}: {raw_line!r}")
        key, value = raw_line.split(":", 1)
        result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def parse_json_block(path: Path, label: str) -> dict:
    text = read_text(path)
    pattern = rf"```json {re.escape(label)}\n(.*?)\n```"
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        raise WikiError(f"Missing `json {label}` block: {path}")
    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise WikiError(f"Invalid JSON block in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise WikiError(f"JSON block must be an object: {path}")
    return data


def canonical_hash(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(set(paths), key=lambda item: item.as_posix()):
        relative = path.relative_to(WIKI_ROOT).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def data_hash(data) -> str:
    encoded = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def relative_page(relative: str) -> Path:
    path = (WIKI_ROOT / relative).resolve()
    try:
        path.relative_to(WIKI_ROOT.resolve())
    except ValueError as exc:
        raise WikiError(f"Wiki path escapes root: {relative}") from exc
    if not path.is_file():
        raise WikiError(f"Wiki page does not exist: {relative}")
    return path


def load_index() -> dict:
    return parse_json_block(INDEX_PATH, "route-table")


def load_sources() -> dict[str, dict]:
    manifest = parse_json_block(SOURCE_MANIFEST_PATH, "source-manifest")
    sources = manifest.get("sources")
    if not isinstance(sources, list):
        raise WikiError("source-manifest sources must be a list")
    by_id = {}
    for source in sources:
        source_id = source.get("id") if isinstance(source, dict) else None
        if not source_id or source_id in by_id:
            raise WikiError(f"Invalid or duplicate source ID: {source_id!r}")
        by_id[source_id] = source
    return by_id


def local_markdown_links(path: Path) -> list[Path]:
    links = []
    for target in re.findall(r"\[[^\]]+\]\(([^)]+\.md)\)", read_text(path)):
        if "://" in target:
            continue
        resolved = (path.parent / target).resolve()
        try:
            resolved.relative_to(WIKI_ROOT.resolve())
        except ValueError as exc:
            raise WikiError(f"Local link escapes wiki root in {path}: {target}") from exc
        links.append(resolved)
    return links


def normalize_topic_name(value: str) -> str:
    return re.sub(r"[^0-9a-z가-힣]", "", unicodedata.normalize("NFKC", value).casefold())


def topic_tokens(value: str) -> list[str]:
    raw_tokens = re.findall(r"[0-9a-z가-힣]+", unicodedata.normalize("NFKC", value).casefold())
    result = []
    for token in raw_tokens:
        stripped = token
        for suffix in KOREAN_TOPIC_SUFFIXES:
            if stripped.endswith(suffix) and len(stripped) - len(suffix) >= 2:
                stripped = stripped[:-len(suffix)]
                break
        if len(stripped) >= 2 and stripped not in result:
            result.append(stripped)
    return result


def select_generic_topic(unit: str, standards: list[dict]) -> tuple[list[dict], dict]:
    query = normalize_topic_name(unit)
    tokens = topic_tokens(unit)
    if not query or not tokens:
        return [], {"status": "unresolved", "reason": "topic_has_no_searchable_terms"}

    scored = []
    for standard in standards:
        if not isinstance(standard, dict):
            continue
        searchable = " ".join(
            str(standard.get(field, ""))
            for field in ("statement", "scope", "notes", "keywords")
        )
        normalized = normalize_topic_name(searchable)
        exact_phrase = query in normalized
        matched = [token for token in tokens if normalize_topic_name(token) in normalized]
        coverage = len(matched) / len(tokens)
        if exact_phrase or coverage == 1:
            score = (2 if exact_phrase else 1) + coverage + min(len(query), 40) / 1000
            scored.append((score, standard, matched, exact_phrase))

    if not scored:
        return [], {
            "status": "unresolved",
            "reason": "no_standard_contains_all_topic_terms",
            "query_terms": tokens,
        }

    best = max(score for score, *_ in scored)
    selected = [entry for entry in scored if entry[0] == best]
    if len(selected) > max(6, len(standards) // 2):
        return [], {
            "status": "ambiguous",
            "reason": "topic_matches_too_much_of_grade_band",
            "query_terms": tokens,
            "candidate_codes": [entry[1].get("code") for entry in selected],
        }
    result = [entry[1] for entry in selected]
    return result, {
        "status": "resolved",
        "method": "reviewed_standard_text_match",
        "query": unit,
        "query_terms": tokens,
        "matched_codes": [standard.get("code") for standard in result],
        "placement": "grade_band_only",
    }


def load_math_catalog() -> tuple[dict, dict]:
    topics = parse_json_block(MATH_TOPIC_MAP_PATH, "math-topic-map")
    profiles = parse_json_block(MATH_TASK_PROFILES_PATH, "math-task-profiles")
    return topics, profiles


def math_grade_band_standards() -> dict[str, set[str]]:
    result = {}
    for grade_band in ("1-2", "3-4", "5-6"):
        rules = parse_json_block(WIKI_ROOT / "math" / "grade-bands" / f"{grade_band}.md", "curriculum-rules")
        result[grade_band] = {
            standard["code"] if isinstance(standard, dict) else standard
            for standard in rules.get("standards", [])
        }
    return result


def lint_math_catalog() -> dict:
    for path in (MATH_TOPIC_MAP_PATH, MATH_TASK_PROFILES_PATH):
        frontmatter = parse_flat_frontmatter(path)
        if frontmatter.get("status") != "reviewed" or not frontmatter.get("verified_at"):
            raise WikiError(f"Math catalog page is not reviewed: {path.relative_to(WIKI_ROOT)}")
    topic_data, profile_data = load_math_catalog()
    topics = topic_data.get("topics")
    profiles = profile_data.get("profiles")
    if not isinstance(topics, list) or not isinstance(profiles, list):
        raise WikiError("Math topic map and task profiles must contain lists")
    profile_ids = set()
    for profile in profiles:
        profile_id = profile.get("id") if isinstance(profile, dict) else None
        if not profile_id or profile_id in profile_ids:
            raise WikiError(f"Invalid or duplicate math profile: {profile_id!r}")
        profile_ids.add(profile_id)
        for key in ("allowed_tasks", "required_tasks", "representations", "features", "misconceptions", "verification_kinds"):
            if not isinstance(profile.get(key), list) or not profile[key]:
                raise WikiError(f"Math profile {profile_id} has invalid {key}")
        if not set(profile["required_tasks"]) <= set(profile["allowed_tasks"]):
            raise WikiError(f"Math profile {profile_id} requires a disallowed task")
        ratio = profile.get("max_direct_ratio")
        if not isinstance(ratio, (int, float)) or not 0 <= ratio <= 0.3:
            raise WikiError(f"Math profile {profile_id} has invalid max_direct_ratio")

    band_standards = math_grade_band_standards()
    all_standard_codes = set().union(*band_standards.values())
    topic_ids = set()
    alias_owners = {}
    coverage = Counter()
    prerequisite_refs = []
    for topic in topics:
        topic_id = topic.get("id") if isinstance(topic, dict) else None
        if not topic_id or topic_id in topic_ids:
            raise WikiError(f"Invalid or duplicate math topic: {topic_id!r}")
        topic_ids.add(topic_id)
        grade_band = topic.get("grade_band")
        if grade_band not in band_standards:
            raise WikiError(f"Math topic {topic_id} has invalid grade_band")
        if topic.get("profile") not in profile_ids:
            raise WikiError(f"Math topic {topic_id} uses unknown profile {topic.get('profile')}")
        aliases = [topic.get("name"), *topic.get("aliases", [])]
        if not all(isinstance(alias, str) and alias.strip() for alias in aliases):
            raise WikiError(f"Math topic {topic_id} has invalid aliases")
        for alias in aliases:
            key = (grade_band, normalize_topic_name(alias))
            if key in alias_owners and alias_owners[key] != topic_id:
                raise WikiError(f"Duplicate math topic alias in {grade_band}: {alias}")
            alias_owners[key] = topic_id
        standards = topic.get("standards")
        if not isinstance(standards, list) or not standards:
            raise WikiError(f"Math topic {topic_id} has no standards")
        unknown = set(standards) - band_standards[grade_band]
        if unknown:
            raise WikiError(f"Math topic {topic_id} has standards outside {grade_band}: {sorted(unknown)}")
        coverage.update(standards)
        prerequisites = topic.get("prerequisites", [])
        if not isinstance(prerequisites, list):
            raise WikiError(f"Math topic {topic_id} has invalid prerequisites")
        prerequisite_refs.extend((topic_id, prerequisite) for prerequisite in prerequisites)

    for topic_id, prerequisite in prerequisite_refs:
        if prerequisite not in topic_ids or prerequisite == topic_id:
            raise WikiError(f"Math topic {topic_id} has invalid prerequisite {prerequisite}")
    missing = all_standard_codes - set(coverage)
    extra = set(coverage) - all_standard_codes
    if missing or extra:
        raise WikiError(f"Math topic coverage mismatch; missing={sorted(missing)}, extra={sorted(extra)}")
    allowed_shared = set(topic_data.get("allowed_shared_standards", []))
    unexpected_shared = {code for code, count in coverage.items() if count > 1 and code not in allowed_shared}
    if unexpected_shared:
        raise WikiError(f"Unexpected shared math standards: {sorted(unexpected_shared)}")
    unused_shared = {code for code in allowed_shared if coverage[code] < 2}
    if unused_shared:
        raise WikiError(f"Declared shared math standards are not shared: {sorted(unused_shared)}")
    return {
        "math_topics": len(topics),
        "math_profiles": len(profiles),
        "math_standards_covered": len(coverage),
        "math_spiral_links": len(prerequisite_refs),
    }


def lint_wiki() -> dict:
    index = load_index()
    sources = load_sources()
    routes = index.get("routes")
    unit_overrides = index.get("unit_overrides", [])
    inactive_subjects = index.get("inactive_subjects", [])
    audience_pages = index.get("audience_pages")
    if not all(isinstance(value, list) for value in (routes, unit_overrides, inactive_subjects, audience_pages)):
        raise WikiError("Index must contain routes and audience_pages lists")

    route_keys = set()
    routed_pages = set(audience_pages)
    for route in routes:
        if not isinstance(route, dict):
            raise WikiError("Every route must be an object")
        grades = route.get("grades")
        if not isinstance(grades, list) or not grades or not all(isinstance(grade, int) and 1 <= grade <= 6 for grade in grades):
            raise WikiError(f"Route has invalid grades: {route}")
        key = (route.get("subject"), tuple(sorted(grades)))
        if not route.get("subject") or key in route_keys:
            raise WikiError(f"Invalid or duplicate route: {key}")
        route_keys.add(key)
        aliases = route.get("aliases", [])
        if not isinstance(aliases, list) or not all(isinstance(alias, str) and alias for alias in aliases):
            raise WikiError(f"Route has invalid aliases: {key}")
        pages = route.get("pages")
        if not isinstance(pages, list) or not pages:
            raise WikiError(f"Route has no pages: {key}")
        routed_pages.update(pages)

    override_keys = set()
    for override in unit_overrides:
        key = (override.get("subject"), override.get("grade"), str(override.get("semester")), override.get("unit"))
        if None in key or key in override_keys:
            raise WikiError(f"Invalid or duplicate unit override: {key}")
        override_keys.add(key)
        pages = override.get("pages")
        if not isinstance(pages, list) or not pages:
            raise WikiError(f"Unit override has no pages: {key}")
        routed_pages.update(pages)

    for inactive in inactive_subjects:
        if not isinstance(inactive, dict) or not inactive.get("subject") or not inactive.get("active_from"):
            raise WikiError(f"Invalid inactive subject entry: {inactive}")
        relative_page(inactive.get("page"))

    page_ids = {}
    checked_sources = set()
    for relative in sorted(routed_pages):
        path = relative_page(relative)
        frontmatter = parse_flat_frontmatter(path)
        for required in ("id", "page_type", "status", "verified_at"):
            if not frontmatter.get(required):
                raise WikiError(f"Missing {required} in {relative}")
        if frontmatter["status"] not in {"reviewed", "source_verified"}:
            raise WikiError(f"Routed page has an unaccepted status: {relative}")
        page_id = frontmatter["id"]
        if page_id in page_ids:
            raise WikiError(f"Duplicate page id {page_id}: {page_ids[page_id]}, {relative}")
        page_ids[page_id] = relative
        rules = parse_json_block(path, "curriculum-rules")
        for source_id in rules.get("sources", []):
            if source_id not in sources:
                raise WikiError(f"Unknown source {source_id} in {relative}")
            checked_sources.add(source_id)

    math_catalog = lint_math_catalog()
    checked_links = 0
    for path in WIKI_ROOT.rglob("*.md"):
        for linked_path in local_markdown_links(path):
            checked_links += 1
            if not linked_path.is_file():
                raise WikiError(f"Broken local link in {path}: {linked_path}")

    return {
        "status": "pass",
        "routes": len(routes),
        "unit_overrides": len(unit_overrides),
        "inactive_subjects": len(inactive_subjects),
        "routed_pages": len(routed_pages),
        "sources_referenced": len(checked_sources),
        "local_links_checked": checked_links,
        **math_catalog,
    }


def merge_value(current, incoming):
    if isinstance(current, dict) and isinstance(incoming, dict):
        result = dict(current)
        for key, value in incoming.items():
            result[key] = merge_value(result[key], value) if key in result else value
        return result
    if isinstance(current, list) and isinstance(incoming, list):
        result = list(current)
        fingerprints = {json.dumps(value, ensure_ascii=False, sort_keys=True) for value in result}
        for value in incoming:
            fingerprint = json.dumps(value, ensure_ascii=False, sort_keys=True)
            if fingerprint not in fingerprints:
                result.append(value)
                fingerprints.add(fingerprint)
        return result
    if current == incoming:
        return current
    values = current if isinstance(current, list) else [current]
    for value in incoming if isinstance(incoming, list) else [incoming]:
        if value not in values:
            values.append(value)
    return values


def merge_rules(rule_sets: list[dict]) -> dict:
    merged = {}
    for rules in rule_sets:
        for key, value in rules.items():
            merged[key] = merge_value(merged[key], value) if key in merged else value
    return merged


def dedupe_standards(rules: dict):
    standards = rules.get("standards")
    if not isinstance(standards, list):
        return
    by_code = {}
    order = []
    for standard in standards:
        code = standard.get("code") if isinstance(standard, dict) else standard
        key = code if isinstance(code, str) else json.dumps(standard, ensure_ascii=False, sort_keys=True)
        if key not in by_code:
            order.append(key)
            by_code[key] = standard
        elif isinstance(standard, dict):
            by_code[key] = standard
    rules["standards"] = [by_code[key] for key in order]


def select_math_topic(unit: str, grade_band: str) -> tuple[dict | None, list[str]]:
    topic_data, profile_data = load_math_catalog()
    candidates = [topic for topic in topic_data["topics"] if topic["grade_band"] == grade_band]
    query = normalize_topic_name(unit)
    exact = []
    fuzzy = []
    for topic in candidates:
        aliases = [topic["name"], *topic.get("aliases", [])]
        normalized_aliases = [normalize_topic_name(alias) for alias in aliases]
        if query in normalized_aliases:
            exact.append(topic)
            continue
        matching_lengths = []
        for alias in normalized_aliases:
            if len(alias) < 2:
                continue
            if alias in query:
                matching_lengths.append(len(alias))
            elif query in alias:
                matching_lengths.append(len(query))
        if matching_lengths:
            fuzzy.append((max(matching_lengths), topic))
    matches = exact
    if not matches and fuzzy:
        best = max(score for score, _ in fuzzy)
        matches = [topic for score, topic in fuzzy if score == best]
    if len(matches) != 1:
        return None, [topic["name"] for topic in matches]
    topic = dict(matches[0])
    by_id = {item["id"]: item for item in topic_data["topics"]}
    topic["prerequisite_topics"] = [
        {"id": prerequisite, "name": by_id[prerequisite]["name"], "grade_band": by_id[prerequisite]["grade_band"]}
        for prerequisite in topic.get("prerequisites", [])
    ]
    topic["successor_topics"] = [
        {"id": item["id"], "name": item["name"], "grade_band": item["grade_band"]}
        for item in topic_data["topics"] if topic["id"] in item.get("prerequisites", [])
    ]
    profiles = {profile["id"]: profile for profile in profile_data["profiles"]}
    topic["task_profile"] = profiles[topic["profile"]]
    topic["placement"] = topic_data.get("placement", "grade_band_only")
    return topic, []


def standard_actions(standards: list[dict]) -> list[str]:
    patterns = (
        (r"읽고 쓸|읽고,?\s*쓸", "read_write"),
        (r"계산|구할 수", "compute"),
        (r"비교", "compare"),
        (r"분류", "classify"),
        (r"나타낼|표현", "represent"),
        (r"어림", "estimate_check"),
        (r"측정|시각을 읽", "measure_read"),
        (r"그릴|만들|채우", "construct"),
        (r"규칙", "describe_rule"),
        (r"해석", "interpret_data"),
        (r"수집", "construct_display"),
        (r"예상|추측", "predict"),
        (r"설명|추론|탐구", "explain_principle"),
    )
    result = []
    text = " ".join(standard.get("statement", "") for standard in standards if isinstance(standard, dict))
    for pattern, action in patterns:
        if re.search(pattern, text) and action not in result:
            result.append(action)
    return result


def apply_math_topic(rules: dict, topic: dict):
    selected_codes = set(topic["standards"])
    standards = [
        standard for standard in rules.get("standards", [])
        if (standard.get("code") if isinstance(standard, dict) else standard) in selected_codes
    ]
    found_codes = {
        standard.get("code") if isinstance(standard, dict) else standard
        for standard in standards
    }
    if found_codes != selected_codes:
        raise WikiError(f"Math topic {topic['id']} could not resolve standards: {sorted(selected_codes - found_codes)}")
    profile = dict(topic.pop("task_profile"))
    profile["standard_actions"] = standard_actions(standards)
    rules["standards"] = standards
    rules["math_topic"] = topic
    rules["math_profile"] = profile
    rules.setdefault("scope_guardrails", []).append(
        "Use prerequisite topics only for necessary review; do not assess successor-topic content unless it is included in the selected standards."
    )


def apply_generic_topic(rules: dict, unit: str, mode: str, route_result: dict, route_notes: list[str]):
    if normalize_topic_name(unit) in FULL_BAND_NAMES:
        route_result["topic_selection_applied"] = False
        route_result["topic_selection"] = {"status": "full_grade_band", "query": unit}
        route_notes.append("User explicitly requested the full grade band; no topic filter was applied.")
        return

    standards = rules.get("standards", [])
    if not standards and rules.get("requires_teacher_scope"):
        route_result["topic_selection_applied"] = True
        route_result["topic_selection"] = {
            "status": "teacher_scope",
            "query": unit,
            "placement": "school_defined",
        }
        rules["selected_topic"] = unit
        return

    selected, decision = select_generic_topic(unit, standards)
    if not selected:
        message = f"No defensible topic-to-standard match for {unit!r}: {decision.get('reason')}"
        if decision.get("candidate_codes"):
            message += f"; candidates={decision['candidate_codes']}"
        if mode == "strict":
            raise WikiError(message)
        route_result["topic_selection_applied"] = False
        route_result["topic_selection"] = decision
        route_notes.append(message)
        return


    rules["standards"] = selected
    rules["selected_topic"] = unit
    rules["topic_terms"] = decision["query_terms"]
    rules.setdefault("scope_guardrails", []).append(
        "Assess only the selected topic and matched achievement standards; adjacent grade-band content is out of scope."
    )
    route_result["topic_selection_applied"] = True
    route_result["topic_selection"] = decision


def apply_explicit_standards(rules: dict, unit: str, codes: list[str], route_result: dict):
    requested = list(dict.fromkeys(codes))
    available = {
        standard.get("code"): standard
        for standard in rules.get("standards", [])
        if isinstance(standard, dict) and standard.get("code")
    }
    unknown = set(requested) - set(available)
    if unknown:
        raise WikiError(f"Explicit standards are outside the routed grade band: {sorted(unknown)}")
    if not requested:
        raise WikiError("Explicit standard selection is empty")
    rules["standards"] = [available[code] for code in requested]
    rules["selected_topic"] = unit
    rules.setdefault("scope_guardrails", []).append(
        "Assess only the explicitly reviewed achievement standards selected for this topic."
    )
    route_result["topic_selection_applied"] = True
    route_result["topic_selection"] = {
        "status": "resolved",
        "method": "explicit_reviewed_standard_codes",
        "query": unit,
        "matched_codes": requested,
        "placement": "grade_band_only",
    }


def build_pack(
    mode: str,
    subject: str | None,
    grade: int | None,
    semester: str | None,
    unit: str | None,
    selected_standards: list[str] | None = None,
) -> dict:
    if mode not in {"strict", "advisory", "off"}:
        raise WikiError(f"Unknown curriculum mode: {mode}")
    lint_wiki()
    index = load_index()
    audience_relatives = index["audience_pages"]
    curriculum_relatives = []
    route_result = None
    route_notes = []
    auxiliary_relatives = []

    if mode != "off":
        missing = [name for name, value in (("subject", subject), ("grade", grade)) if value in (None, "")]
        if missing:
            raise WikiError(f"{mode} mode requires: {', '.join(missing)}")
        for inactive in index.get("inactive_subjects", []):
            if subject == inactive["subject"]:
                raise WikiError(f"{subject} is not active for the current catalog; active_from={inactive['active_from']}")
        matches = [
            route
            for route in index["routes"]
            if subject in [route["subject"], *route.get("aliases", [])]
            and grade in route["grades"]
        ]
        if len(matches) != 1:
            raise WikiError(f"No unique active wiki route for {subject} grade={grade}")
        base_route = matches[0]
        route_result = {
            "subject": base_route["subject"],
            "grade": grade,
            "semester": semester,
            "unit": unit,
            "grade_band": f"{min(base_route['grades'])}-{max(base_route['grades'])}",
            "unit_override_applied": False,
        }
        curriculum_relatives = list(base_route["pages"])
        if base_route["subject"] == "수학":
            auxiliary_relatives = ["math/topic-map.md", "math/task-profiles.md"]
        if semester not in (None, "") and unit not in (None, ""):
            overrides = [
                override for override in index.get("unit_overrides", [])
                if override["subject"] == base_route["subject"]
                and override["grade"] == grade
                and str(override["semester"]) == str(semester)
                and override["unit"] == unit
            ]
            if len(overrides) > 1:
                raise WikiError(f"Multiple unit overrides for {subject} grade={grade} semester={semester} unit={unit}")
            if overrides:
                route_result["unit_override_applied"] = True
                for relative in overrides[0]["pages"]:
                    if relative not in curriculum_relatives:
                        curriculum_relatives.append(relative)
            else:
                route_notes.append("No reviewed semester/unit override; validation is limited to official grade-band scope.")
        elif semester not in (None, "") or unit not in (None, ""):
            route_notes.append("Semester and unit were not both supplied; validation is limited to official grade-band scope.")

    audience_paths = [relative_page(relative) for relative in audience_relatives]
    curriculum_paths = [relative_page(relative) for relative in curriculum_relatives]
    rule_sets = [parse_json_block(path, "curriculum-rules") for path in audience_paths + curriculum_paths]
    auxiliary_paths = [relative_page(relative) for relative in auxiliary_relatives]
    pack_paths = [INDEX_PATH, SOURCE_MANIFEST_PATH] + audience_paths + curriculum_paths + auxiliary_paths
    merged = merge_rules(rule_sets)
    dedupe_standards(merged)
    if route_result and route_result["subject"] == "수학":
        if selected_standards:
            raise WikiError("Mathematics uses its reviewed topic map; explicit standard overrides are not allowed")
        if unit not in (None, ""):
            if normalize_topic_name(unit) in MATH_FULL_BAND_NAMES:
                route_result["math_topic_profile_applied"] = False
                route_notes.append("User explicitly requested the full mathematics grade band; no single topic profile was applied.")
            else:
                topic, ambiguous = select_math_topic(unit, route_result["grade_band"])
                if topic is None:
                    message = f"No unique math topic profile for {unit!r} in grade band {route_result['grade_band']}"
                    if ambiguous:
                        message += f"; candidates={ambiguous}"
                    if mode == "strict":
                        raise WikiError(message)
                    route_notes.append(message)
                else:
                    topic["placement"] = "reviewed_semester_override" if route_result["unit_override_applied"] else "grade_band_only"
                    route_result["math_topic_id"] = topic["id"]
                    route_result["math_topic_profile_applied"] = True
                    apply_math_topic(merged, topic)
        else:
            route_result["math_topic_profile_applied"] = False
            message = "Mathematics strict mode requires a unit/topic or an explicit full-grade-band request."
            if mode == "strict":
                raise WikiError(message)
            route_notes.append(message)
    elif route_result:
        if unit not in (None, ""):
            if selected_standards:
                apply_explicit_standards(merged, str(unit), selected_standards, route_result)
            else:
                apply_generic_topic(merged, str(unit), mode, route_result, route_notes)
        else:
            route_result["topic_selection_applied"] = False
            message = "Strict curriculum mode requires a unit/topic or an explicit full-grade-band request."
            if mode == "strict":
                raise WikiError(message)
            route_notes.append(message)

    pack = {
        "schema_version": 3,
        "curriculum_mode": mode,
        "curriculum_check": "skipped_by_user" if mode == "off" else ("warning_only" if mode == "advisory" else "enforced"),
        "audience_language_check": "enforced",
        "route": route_result,
        "route_notes": route_notes,
        "pages": {
            "audience": audience_relatives,
            "curriculum": curriculum_relatives,
            "auxiliary": auxiliary_relatives,
        },
        "rules": merged,
        "source_bundle_sha256": canonical_hash(pack_paths),
    }
    pack["knowledge_pack_sha256"] = data_hash(pack)
    return pack


def write_output(data: dict, output: Path | None):
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    lint_parser = subparsers.add_parser("lint")
    lint_parser.add_argument("--output", type=Path)

    route_parser = subparsers.add_parser("route")
    route_parser.add_argument("--mode", choices=("strict", "advisory", "off"), required=True)
    route_parser.add_argument("--subject")
    route_parser.add_argument("--grade", type=int)
    route_parser.add_argument("--semester")
    route_parser.add_argument("--unit")
    route_parser.add_argument("--standard", action="append", dest="standards")
    route_parser.add_argument("--output", type=Path)

    args = parser.parse_args()
    try:
        if args.command == "lint":
            result = lint_wiki()
        else:
            result = build_pack(args.mode, args.subject, args.grade, args.semester, args.unit, args.standards)
        write_output(result, args.output)
    except WikiError as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
