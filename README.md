# WoW Rotation Engine

WoW 딜사이클 교본의 **V11 품질을 보존하면서 ChatGPT 채팅에서 전문화 이름만으로 CREATE/UPDATE**하는 프로젝트입니다. HTML 보존·검증용 V2 엔진은 재사용하되, 별도 AI API 앱 구축을 필수 경로로 삼지 않습니다.

> **현재 상태: GitHub CI + 실제 V2 코드 + V11 파생 규칙 데이터(PUBLIC)**. 7개 전문화의 구조화된 규칙 **메타데이터**를 이관했습니다. 와우헤드 원문 전체·대량 번역문과 기존 V11 HTML 전체는 게시하지 않았으며, 생성 뷰어는 실전 딜사이클 가이드가 아닙니다.

## 기본 사용자 경로 — ChatGPT 중심 제작 (2026-11-11 방향 전환)

**사용자 입력:** `비전 마법사`, `화염 마법사 업데이트`, `잠행 도적 고급 운용 보강`처럼 **전문화 이름만** 채팅에 입력.

**ChatGPT가 수행:** 실제 비공개 V11 정본 복구 및 SHA 검증 → GitHub 제작 규칙·공략 출처 URL 확인 → 최신 패치/영웅 특성별 심층 분석·설명 집필 → 기존 V11 디자인·기술 연결·`?`/`!` 재사용 → 비대상 전문화 바이트 동일 검증 → 단일 HTML 파일 전달.

**개발 방향:** 원래 직접 편집한 7개 V11 교본의 설명 깊이와 품질을 기준으로 한다. 신규 비전 초안이 짧거나 단순화된 부분을 보완하기 위해 사용자가 AI 로그인, JSON, Codespaces, Actions, API 키, 외부 관리 UI를 오가게 만들지 않는다. AI 인증 실험 PR #17~#19는 기록으로 보존하되 **기본 사용 경로에서 제외**했다.

**새 채팅 독립 복원 진입점:** [HANDOFF_CHAT_FIRST_CURRENT — 현재 상태·V11/V3 파일 및 승인 구분·품질 게이트·다음 작업](docs/HANDOFF_CHAT_FIRST_CURRENT.md). 새 채팅은 이 문서부터 읽기 전용으로 복원하고 사용자 `진행` 승인 후 작업한다.

**범용 원문 확보 보조 도구 (2026-11-12):** [중첩 선택·툴팁 본문·위치 단서·패치 일관성 감사](docs/SOURCE_COVERAGE_AUDIT.md)를 추가했습니다. 신규 전문화에도 동일한 방식으로 누락 경로를 검사하지만, 실제 웹사이트를 크롤링하거나 자동으로 원문 확보·게임플레이 검증을 완료하는 도구가 아닙니다. 원문 내용은 ChatGPT가 확보하고 의미 분석합니다. 개인 HTML과 외부 장문 원문을 PUBLIC 저장소에 올리지 않습니다.

**구조 후보 ↔ 수집 기록 대조(2026-11-12):** 정적 HTML에서 발견한 숨김 패널·툴팁·선택지 후보를 관측 원문과 대조해 **추가 확인할 항목**을 정리하는 `engine.source_reconcile` 도구와 합성 회귀 검사를 추가했습니다. [원문 확보 감사 문서](docs/SOURCE_COVERAGE_AUDIT.md). 실제 최신 Wowhead의 원문 수집/검증을 자동 대체하지 않습니다.

**다전문화 범용화 회귀 검사:** [냉기 마법사·생존 사냥꾼·징벌 성기사의 원문 선택 형태 검토](docs/CROSS_SPEC_SOURCE_VALIDATION_20261112.md). 원본 HTML 구조·관측 기록은 SHA-256 및 패치/수정본이 일치할 때만 연결하고, 검색 색인만으로 라이브 UI 확보를 주장하지 않습니다.

**실제 HTML 구조 스모크:** 과거 공개 Wowhead HTML 2종을 CI에서 임시 분석해 WHML 탭 2그룹·6개 본문과 0그룹을 구분했습니다. [검증 범위·한계](docs/SOURCE_COVERAGE_AUDIT.md). 최신 패치 공략 원문을 전수 확보했다는 의미는 아닙니다.

**동적 DOM 확인 보조:** [브라우저 런타임 수집 규격](docs/LIVE_DOM_CAPTURE.md)과 실제 Chromium 합성 회귀 검사를 추가했습니다. 현재 Wowhead 접근 제한 해결과 원문 전수 확보를 뜻하지 않습니다.

**동적 수집과 누락 감사 통합:** [LIVE_DOM_CAPTURE](docs/LIVE_DOM_CAPTURE.md) — 영웅/전투 하위 UI와 관련 `?`를 실제 브라우저에서 수집하고 [범용 감사](docs/SOURCE_COVERAGE_AUDIT.md)의 검토용 초안에 연결합니다. 원문 전수 확보·게임 판단 최종 검증은 자동 선언하지 않습니다.

**고양 최신 실물 원본 검증(2026-11-12):** 사용자가 제공한 Wowhead 12.1.5 저장본에서 tooltip 44개·선택 정의 16개·조건 표시 82개 및 물약별 실제 오프너 12조합을 확인했습니다. 선택이 게임 행동을 바꾸는 경우에만 분기하도록 [범용 수집 정책](docs/SOURCE_COVERAGE_AUDIT.md)을 수정했습니다. [증거 메타데이터](docs/ENHANCEMENT_SAVED_HTML_EVIDENCE_20261112.md). 개인 HTML/원문 미게시.

**원문 HTML 자동 취득기:** [Ctrl+S 대응 HTML·ZIP·MHTML 취득 설계](docs/AUTO_PAGE_ACQUISITION.md). 정상 접근 가능한 브라우저에서 원문 HTML을 자동 저장하고 공통 WHML 분석에 넘깁니다. 사용자 저장 시 동반되는 `_files` 리소스 폴더는 일반적으로 원문 조건 분석에 필수는 아닙니다. 서버 403 우회는 포함하지 않습니다.

**원클릭에 가까운 원문 취득·감사 통합:** [source_acquisition_pipeline](docs/AUTO_PAGE_ACQUISITION.md)에서 URL → 분석용 HTML → 선택지·`?` 구조 감사까지 통합했습니다. 서버 Wowhead 접근은 별도 문제이며, 사이트 차단을 우회하지 않습니다.

**HTTP-first 실제 취득 검증:** 브라우저 없이 일반 HTTPS GET으로 고양 12.1.5 원문의 WHML 68,350자·툴팁 44개를 취득했고 **사용자 저장본의 원문 SHA-256과 동일**함을 확인했습니다. 생존 사냥꾼도 동일 수집기로 원문 53,084자 취득(패치 별도 검증 필요). [실측 및 HTTP 403 대응](docs/AUTO_PAGE_ACQUISITION.md).

**전문화 이름만 입력하는 원문 취득:** [40전문화 이름 해석·실제 고양/생존/비전 자동 취득·비공개 조건/툴팁 패킷](docs/SPECIALIZATION_ONLY_ACQUISITION_20261112.md). 콘텐츠 판단 및 V11 HTML 생성 QA는 이후 별도 수행합니다.

**조건 적용 범위와 누락 감사:** [실제 3전문화 WHML 표시 조건 82/61/5개 전수 귀속, 근거 위치·부분 조건 보존](docs/WHML_SCOPE_EVIDENCE_20261112.md). UI 표시 조건을 실제 게임 기술 로직으로 임의 변환하지 않습니다.

**게임플레이 판단 QA:** [원문 근거를 첨부한 우선순위·오프너 반례 검사](docs/GAMEPLAY_DECISION_QA_20261112.md). 근거 없는 행동이나 임계값을 생성하지 않고, 편집 규칙의 충돌·미시험·예외 미모델링을 검사합니다.

**실제 게임 상태 판단 검증(2026-11-12):** [고양 주술사 12.1.5 폭풍인도자 단일 10규칙·13상태 및 no_rule 반례](docs/ENHANCEMENT_ST_DECISION_QA_20261112.md). 원문 SHA·스킬 ID·툴팁 참조를 대조했으며 전체 전문화/게임 최적화 승인과 구분합니다.

**과거자료·범용 품질 역검증:** [V11 7뷰 원시 HTML 보존, V3.9→V3.11 변경 범위, 과거 원문 F01~F09와 물약 예외 반례](docs/HISTORICAL_REGRESSION_AUDIT_20261112.md). 장/표 수 고정을 피하고 정상 교본의 오탐까지 검증합니다.

**운영 정본:**
- [ADR-003 — ChatGPT 중심 제작 결정](docs/ADR_003_CHAT_FIRST_EDITORIAL.md)
- [CHAT_FIRST_PLAYBOOK — CREATE/UPDATE 작업 순서](docs/CHAT_FIRST_PLAYBOOK.md)
- [EDITORIAL_QUALITY_PROTOCOL — 7전문화 전체 비교 기반 상태→조건→행동 QA](docs/EDITORIAL_QUALITY_PROTOCOL.md)
- [생존 사냥꾼 V3 실작업 감사·재작성 결과](docs/CHAT_FIRST_RUN_SURVIVAL_V3_20261111.md)
- [SOURCE_ACQUISITION — 공략 자료 수집·검증 방법](docs/SOURCE_ACQUISITION.md)
- [CHAT_FIRST_PROJECT_INSTRUCTIONS — 프로젝트 설정용 짧은 지침](docs/CHAT_FIRST_PROJECT_INSTRUCTIONS.md)

**한 문구 요청을 완전히 검증했다는 뜻은 아니다.** ChatGPT가 현재 채팅에서 GitHub·웹·개인 V11 원본을 실제로 읽을 수 있어야 하며, 채팅 요청에 따라 파일을 생성한다. AI의 백그라운드 무인 실행이나 게임플레이 검증의 자동 완료를 보장하지 않는다. 공개 GitHub에는 원본 V11과 실제 완성 교본 HTML을 업로드하지 않는다.

## 기존 빠른 참조 데모



```bash
python -m engine.manual_site --output dist/manual/index.html
```

생성되는 `index.html`은 **단일 파일**입니다. GitHub Actions 성공 실행의 `wow-rotation-quick-reference-html` Artifact에서 내려받아 브라우저로 열 수 있습니다. 7개 전문화·영웅 특성 전환, 상황별 우선순위, 기술명/ID 검색, 대상 수 필터, 출처 링크가 들어 있습니다.

**현재 범위는 빠른 참조판입니다.** 원본 V11의 상세 발동 조건과 Advanced Tips 본문은 아직 데이터에 포함되지 않으므로, 이 HTML만 보고 게임 내 스킬 사용 여부를 결정해서는 안 됩니다. 사용 방법과 데이터 업데이트 방법은 [간략 교본 설명](docs/MANUAL_PREVIEW.md)을 보세요.

## 시작

Python 3.11+ 표준 라이브러리만 사용합니다.

```bash
python -m unittest discover -s tests -v
python -m engine validate --input examples/synthetic.json
python -m engine build --input examples/synthetic.json --output dist/index.html --allow-demo
python -m engine diff --before examples/synthetic.json --after examples/synthetic.json
```

- GitHub Actions: `.github/workflows/ci.yml` — 테스트, JSON 검증, 데모 HTML 빌드, Artifact.
- `engine/`: 안전한 조건 평가(unknown 지원), 최소 스키마 검사, 결정론적 HTML 렌더링, 변경 위험도 비교.
- `examples/`: 실제 게임을 주장하지 않는 합성 데이터.
- `docs/MIGRATION.md`: 로컬 V2 엔진을 공개 코드와 저작권 검토 대상 데이터로 분리해 순차 이관하는 계획.

## 운영 원칙

1. **PR-first**: 격리 브랜치 → 테스트 → PR 검토 → 병합.
2. **원문 근거 없는 자동 게시 금지**: 우선순위·조건·Advanced Tips 변경은 승인 전 배포하지 않습니다.
3. **주문 ID 우선**: 검증된 한국어 주문명만 최종 자료에 사용합니다.
4. **저작권·접근 정책 준수**: 와우헤드 원문 전체/전체 번역문, 개인 자격증명, API 키를 PUBLIC에 올리지 않습니다.
5. **동작·품질의 분리**: CI PASS는 코드 검증이지 게임 내 최적 딜사이클의 정확도 보증이 아닙니다.

본 저장소는 AI 분석·증분 업데이트 기능을 단계적으로 확장할 기반입니다.

## 원본 V2 코드 이관

원본 V2의 Python 모듈과 데이터 구조 검사기를 `engine/v2/`로 이관했습니다. 이식 전에 로컬 V2 자체는 18개 오프라인 테스트와 기준 V11 HTML SHA-256 재생성 검사를 통과했습니다. GitHub에서는 실제 공략 대신 합성 데이터로 재검증합니다. 범위·해시는 [이관 보고서](docs/V2_MIGRATION_STATUS.md)를 확인하세요.

## 공개 구조화 데이터 (V11 기반)

사용자 승인에 따라 V11에서 추출한 **분석용 메타데이터**를 `content/public/`에 이관했습니다: 전문화 7개, 우선순위 23개 표/177행, Advanced Tips 색인 79개, 주문 ID 176종(178개 이름 레코드). 13개 행동은 주문 ID가 미해결입니다.

**제한:** 기존 HTML 교본의 본문 전체를 올린 것은 아닙니다. 외부 원문과 한국어 주문명이 아직 독립 검증되지 않았고, 규칙의 조건은 대부분 미해석 상태이므로 이 데이터 자체로 실전 딜사이클을 자동 결정할 수 없습니다. 모든 규칙은 `pending`이며 자동 게시하지 않습니다.

```bash
python -m engine.public_data validate
python -m engine.public_data build --output dist/public-index.html
```

`dist/public-index.html`은 7개 전문화를 전환하며 순위·주문 ID·Advanced Tips 분류를 볼 수 있는 **데이터 검토 화면**입니다. 유효한 실전 공략으로 사용해서는 안 됩니다. 세부 범위는 [공개 데이터 정책](docs/PUBLIC_DATA.md)을 확인하세요.

## Issue #5: 동적 검토 UI · 게시 안전 게이트

```bash
python -m engine.review_ui --output dist/review/index.html
python -m engine.review_audit --output dist/review-audit.json
```

- `dist/review/index.html`: 7개 전문화 및 영웅 특성별 규칙을 보는 **비실전 검토용 HTML**. JSON 등록 목록에서 메뉴 자동 생성.
- `dist/review-audit.json`: 177개 조건 미해석, 178개 한국어 이름 레코드 미검증 등의 게시 차단 사유 출력.
- 원문 전체·상세 Advanced Tips는 아직 실전 가이드로 게시하지 않음.
- 상세 범위: [docs/REVIEW_UI.md](docs/REVIEW_UI.md).


## 한국어 주문명 검증: Issue #5 후속

```bash
python -m engine.spell_names audit --output dist/spell-name-audit.json
```

이는 176개 주문 ID의 검증 대기 현황을 검사합니다. **Blizzard API는 일반 CI에서 호출하지 않습니다.**
자격증명을 GitHub Secrets에 등록한 경우에만 수동 Actions `Collect Blizzard ko_KR spell names`로 증거를 수집할 수 있습니다. 관측 결과는 기존 명칭을 자동 변경하거나 승인하지 않습니다. 상세: [한국어 주문명 검증](docs/SPELL_NAMES.md).

## 딜사이클 조건식 검토 워크리스트

```bash
python -m engine.condition_worklist --output dist/condition-worklist.json
```

177개 우선순위 전체의 검토 상태를 출력합니다. 일부 **구문적으로 분석 가능한 조건은 실제 기술 사용 충분조건이 아닙니다.** 현재 냉기 마법사 빙결 중첩 조건 2개는 출처 외부 대조를 기다리는 **부분 후보**로만 수록했고, 나머지 175개 행은 미정규화 상태입니다. AI·코드 모두 미검증 규칙을 자동 승인하지 않습니다.

세부 설계: [Condition Worklist](docs/CONDITION_WORKLIST.md).

## 원문 변경 감지 실험 (Issue #5)

```bash
python -m engine.source_snapshots capture --input examples/synthetic-source-before.json --output dist/synthetic-source-before.json
python -m engine.source_snapshots capture --input examples/synthetic-source-after.json --output dist/synthetic-source-after.json
python -m engine.source_snapshots diff --previous dist/synthetic-source-before.json --current dist/synthetic-source-after.json --output dist/synthetic-source-diff.json
```

위 입력은 **완전 합성 문장**입니다. 원문 텍스트를 공개 Artifact에 보관하지 않고 해시만 비교합니다. 결과는 변경 관측 항목의 검토 후보이며 자동 번역·자동 게시와 무관합니다. 상세: [Source Evidence Snapshot](docs/SOURCE_SNAPSHOTS.md).


## 공식 주문명 404·불일치 검토

```bash
python -m engine.spell_triage --output dist/spell-review-queue.json
python -m engine.client_spell_probe --output dist/WoWRotationSpellProbe
```

2026-11-10 공식 API 조회에서 발견된 25개 404와 1개 명칭 불일치를 **실제 우선순위 177행에 미치는 영향**으로 분류합니다. P0는 혹한의 쐐기(4개 행), P1은 기술명 불일치 1개, P2는 기타 사전 전용 404 24개입니다. [검토·클라이언트 교차확인 가이드](docs/SPELL_TRIAGE.md).
