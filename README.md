# 🎯 bkgkmaker — Blooket·Gimkit 퀴즈 메이커 스킬

> 2022 개정 교육과정에 근거한 **초등 객관식 퀴즈**를 자동 생성하고,
> **Blooket·Gimkit 임포트용 CSV**와 교사용 검증 리포트(JSON)까지 한 번에 만들어 주는 AI 스킬입니다.

<p>
  <img alt="curriculum" src="https://img.shields.io/badge/교육과정-2022_개정-2563eb">
  <img alt="platforms" src="https://img.shields.io/badge/내보내기-Blooket_·_Gimkit-16a34a">
  <img alt="python" src="https://img.shields.io/badge/Python-3.12+-f59e0b">
  <img alt="deps" src="https://img.shields.io/badge/외부의존성-없음-6b7280">
</p>

---

## ✨ 한눈에 보기

하나의 정본(canonical) 퀴즈에서 **두 플랫폼 CSV + 두 감사용 JSON**을 만들어 냅니다. CSV 행을 손으로 짜지 않고, 모든 산출물을 스크립트가 봉인·검증합니다.

| 만들어 주는 것 | 설명 |
|---|---|
| `blooket-import.csv` | Blooket 스프레드시트 임포트 양식 그대로 |
| `gimkit-import.csv` | Gimkit 임포트 양식 그대로 |
| `validation-report.json` | 바이트 단위 CSV 구조 검증 결과 |
| `analysis-report.json` | 문항별 근거·보기 해설 요약(교사 검토용) |

---

## 🧭 두 개의 축으로 분기

요청을 받으면 **범위(Scope)** 와 **근거(Grounding)** 두 축을 독립적으로 설정합니다.

### 범위 (Scope)
| 모드 | 사용 시점 |
|---|---|
| `curriculum` | 국가 성취기준이 경계를 정함 (`strict` / `advisory`) |
| `custom` | 교사가 의도적으로 교육과정 밖 주제를 요청 (품질·안전·검증 게이트는 그대로 유지) |

### 근거 (Grounding)
| 모드 | 사용 시점 |
|---|---|
| `verified_sources` | 공식·검증된 출처 기반 |
| `documents_only` | 모든 정답 사실이 **제공된 문서**에서만 나와야 함 |
| `documents_preferred` | 문서 우선, 선언된 공백만 검증 외부출처로 보충 |
| `mixed_verified` | 문서 + 검증 외부출처 의도적 병용 |

> 교육과정 적용 여부가 모호하면 **딱 한 번** 묻습니다: `교육과정 기준을 적용할까요?`

---

## 📚 교육과정 위키

`references/curriculum-wiki/` — 2022 개정 교육과정 기준, **2026학년도 기준 초등 전 과목** 성취기준을 학년군(1-2 / 3-4 / 5-6)별로 정리한 51개 페이지.

```
국어 · 수학 · 사회 · 과학 · 도덕 · 실과 · 체육 · 음악 · 미술 · 영어
통합교과(바른 생활 · 슬기로운 생활 · 즐거운 생활) · 창의적 체험활동
└─ 2028년 적용 예정 '건강한 생활'까지 예약 등록
```

- **라우트 테이블**: 과목·학년 → 해당 성취기준 페이지 자동 매핑 (`index.md`)
- **단원 오버라이드**: 수학 6학년 *소수의 나눗셈*은 1학기/2학기/전학년 + 개념·단원 페이지까지 세분화 (수학 나선형 프로파일)
- **학생 언어**: `피제수/제수` 대신 `나누어지는 수/나누는 수` 등 초등 눈높이 용어 강제

---

## 🚀 사용 흐름

> 모든 명령은 스킬 루트에서 실행. 외부 라이브러리·API 키 불필요(순수 Python 3.12+).

```bash
# 1) 요청 봉인 (scope_mode / grounding_mode 명시)
python3 scripts/request_manifest.py seal \
  --input request-draft.json --output request-manifest.json

# 2) 워크플로 계획 생성 (next_artifact를 따라 진행)
python3 scripts/workflow_router.py \
  --request-manifest request-manifest.json --output workflow-plan.json

# 3) 교육과정 지식팩 라우팅 (예: 6학년 사회 '대륙과 대양')
python3 scripts/curriculum_wiki.py route \
  --mode strict --subject 사회 --grade 6 --unit '대륙과 대양' \
  --output knowledge-pack.json

# 4) 근거 사실 봉인 → 5) 블루프린트 → 6) blind 답안/범위 리뷰 → 7) 빌드
python3 scripts/quiz_harness.py build \
  --input questions.json --request-manifest request-manifest.json \
  --knowledge-pack knowledge-pack.json --fact-pack fact-pack.json \
  --blueprint blueprint.json --review answer-review.json \
  --scope-review scope-review.json --output-dir output
```

산출물: `output/` 안에 두 CSV + 두 JSON 리포트.

---

## 🛡️ 품질 게이트 (Hard Gates)

- 문항당 **정답은 정확히 하나**, 10문항 이상 세트에서 단순 암기·단순 계산은 **30% 이하**
- 보기는 이름·숫자만 바꾸지 않고 **사고·근거·표상·오개념**을 바꿔 다양화
- 공급/출판 문제·긴 지문·저작 이미지 복제 금지 — 짧은 요약·로케이터·해시만 저장
- strict 주제 미해결, 출처 충돌, 근거 없는 문서 사실, 안전 실패, 리뷰 만료 등에서 **즉시 중단**
- `single_context_blind`를 독립 리뷰로, 구조 검증을 실제 업로드 검증으로 **포장 금지**

---

## 🧩 구성

```
create-blooket-gimkit-quizzes/
├── SKILL.md                  # 스킬 본문(워크플로·게이트 규정)
├── agents/openai.yaml        # 에이전트 정의
├── references/               # 레퍼런스 문서 10편
│   ├── branching-workflow.md     # 분기 워크플로
│   ├── assurance-v2.md           # 근거 보증 프로파일 v2
│   ├── document-grounding.md     # 문서 근거화(비저장 원칙)
│   ├── diversity-blueprint.md    # 문항 다양성 설계
│   ├── subject-adapters.md       # 과목별 어댑터
│   ├── canonical-format.md       # 정본 포맷
│   ├── platform-formats.md       # Blooket/Gimkit CSV 포맷
│   └── curriculum-wiki/          # 교육과정 위키 (51 페이지)
└── scripts/                  # 무의존 Python 하네스 15종
    ├── request_manifest.py       # 요청 봉인
    ├── workflow_router.py        # 워크플로 분기 계획
    ├── curriculum_wiki.py        # 위키 라우팅·병합·해시·린트
    ├── custom_scope.py           # 비교육과정 범위 봉인
    ├── document_grounding.py     # 문서 매니페스트·검색팩 봉인
    ├── evidence_pack.py          # 근거 사실팩 봉인
    ├── quiz_harness.py           # 블루프린트·검증·리뷰·CSV 내보내기
    └── *_self_test.py / validate_skill.py  # 자체 검증 하네스
```

---

## 🧪 자체 검증

```bash
PYTHONPATH=scripts python3 scripts/all_subject_self_test.py
PYTHONPATH=scripts python3 scripts/all_subject_v2_self_test.py
PYTHONPATH=scripts python3 scripts/math_self_test.py
PYTHONPATH=scripts python3 scripts/v2_self_test.py
PYTHONPATH=scripts python3 scripts/branching_self_test.py
python3 scripts/validate_skill.py
```

---

## 📌 메모

- 이 스킬은 **Codex(OpenAI) 에이전트 스킬** 형식(`agents/openai.yaml`)으로 작성되었습니다.
- 모든 검증은 **순수 Python 표준 라이브러리**만 사용 — 별도 설치 없이 동작합니다.
- 정답 진실성은 성취기준이 아니라 **봉인된 근거 사실(fact pack)** 이 결정합니다. 성취기준은 *범위*만 정합니다.
