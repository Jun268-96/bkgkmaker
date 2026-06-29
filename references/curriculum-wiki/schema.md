---
id: curriculum-wiki-schema
page_type: schema
status: reviewed
verified_at: 2026-06-27
---

# Wiki schema

Keep four kinds of knowledge separate: official achievement standards, grade-band scope, textbook or semester sequence, and teacher-reviewed student language.

Every routed page must contain flat frontmatter with `id`, `page_type`, `status`, and `verified_at`, plus one fenced `json curriculum-rules` block. Source claims must cite IDs from `source-manifest.md`.

## Review states

- `source_verified`: achievement-standard codes and statements were extracted from an official source, counted against an expected manifest, and hashed.
- `reviewed`: a person or a deterministic review process checked the derived rule or routing decision.
- `cataloged`: useful future or inactive material; never loaded by an active strict route.

## Page types

- `audience`: wording and age constraints that apply even when curriculum checking is off.
- `grade_band`: official achievement standards for one subject and grade band.
- `concept`: vertical prerequisite and successor relationships, used especially for spiral mathematics.
- `unit`: a curriculum-level unit interpretation.
- `semester`: teacher- or textbook-reviewed semester placement.
- `curriculum_area`: an area without national achievement-standard codes, such as creative experiential activities.
- `topic_map`: a reviewed concept-to-standard and prerequisite map used to narrow a grade-band route.
- `task_profiles`: allowed mathematical acts, representations, structural features, misconceptions, and verification adapters.

## Authority order

1. The effective national notice and official subject appendices define active curriculum scope.
2. Official achievement-level documents provide structured copies of achievement standards.
3. Approved textbooks, teacher guides, or explicit teacher review define semester sequence; national grade-band standards do not.
4. Generated summaries never become authoritative without a source ID, extraction hash, and accepted review state.

## Routing modes

- `strict`: load the subject's grade-band page and any exact unit override; scope violations fail.
- `advisory`: load the same pages but return scope violations as warnings.
- `off`: skip curriculum pages while retaining elementary audience and item-quality checks.

If the user has not clearly selected a mode, ask once: `교육과정 기준을 적용할까요?` A yes answer defaults to `strict`; a request for enrichment or flexible reference maps to `advisory`.

For mathematics, `strict` additionally requires a uniquely resolved topic when a unit is requested. Topic selection filters the grade-band standards but does not establish semester placement. Only an exact reviewed unit override may change placement to `reviewed_semester_override`.

For every other subject, `strict` also requires a topic or the explicit `전 범위`. Topic matching must resolve against reviewed achievement-standard text and filter the knowledge pack. An unresolved or excessively broad match fails closed. Topic selection changes the knowledge-pack hash so a review or quiz cannot be reused across different topics from the same grade-band page.
