# WoW Rotation Engine — 현재 단일 인계 정본

- **기준일:** 2026-11-10 (KST), PR #12 및 `main` Actions 확인
- **제품 정본:** [`degong2-code/wow-rotation-engine`](https://github.com/degong2-code/wow-rotation-engine) · Public · `main`
- **인계 기준 제품 HEAD:** `5ba7d12263fbf0b9ecbb52160cc01e2a53e593a0`
- **인계 기록 작업:** `work/handoff-20261110-v1` → PR (아직 `main`으로 병합하지 않음). **이 문서의 HEAD는 마지막 검증한 제품 기준이며, 읽는 시점에는 GitHub API에서 `main`/작업 브랜치 HEAD를 재확인할 것.**
- **핵심 지식 지도:** [PROJECT_MAP.md](PROJECT_MAP.md)
- **최신 사용자 정책의 근거:** 최신 다른 개발 채팅 지시 및 [PR #12](https://github.com/degong2-code/wow-rotation-engine/pull/12), [MANUAL_PREVIEW.md](MANUAL_PREVIEW.md)
- **소유권:** 현재 개발은 동일 공개 저장소의 GitHub PR/Actions를 사용. 다른 채팅에서도 개발했다고 보고됐으나 다른 채팅의 배타적 소유권·실행 중 작업은 **확인 불가**. 조사 당시 열린 PR은 0개였음. 새로운 작업 전 최신 PR/branches/HEAD 조회 필수.

## 최종 목표·현재 위치

**목표:** 한국어 World of Warcraft 딜사이클 교본의 7개 전문화 내용을 정확하고 읽기 쉽게 제공하고, 새 전문화 추가/공략 변경 시 AI가 필요한 부분만 분석해 구조화 JSON과 단일 HTML·웹 교본을 갱신하도록 한다. **코드/검증 모듈 증가 자체가 목표가 아니다.**

**최신 사용자 결정 (2026-11-10):** “너무 엄격한 검증은 필요 없어.” 공식 주문 ID 404나 세부 조건의 완전 인증 때문에 **사용자 교본 제작을 멈추지 않는다**. 필수 검증은 JSON·ID 연결, 명백한 내용 충돌, HTML 생성·사용성 등 실질 문제 중심. 다만 **빠진 상세 시전 조건을 AI가 창작하지 않고**, 불확실함을 표시한다. 로컬 애드온 설치/수동 실행/스크린샷 첨부는 정규 개발 경로가 아니다. 프로젝트는 **GitHub + Actions + AI 후보 생성 + JSON + HTML** 중심이다.

**현재 제품:** [PR #12](https://github.com/degong2-code/wow-rotation-engine/pull/12)로 7개 전문화·23개 상황별 표·177개 우선순위 행, 기술 검색, 영웅 특성 전환, 대상 수/단일·광역 필터가 있는 **128KB 안팎의 단일 HTML 빠른 참조판**이 생성된다. 본문 전체가 있는 **V11급 상세 교본은 아직 아니다**. Advanced Tips **79개는 주제 색인만** 있고 실제 심화 설명이 빠져 있다.

## 주요 코드·데이터·검증의 단일 진입점

| 역할 | 정본 위치 | 상태 |
|---|---|---|
| 사용자 HTML 생성 | `engine/manual_site.py` | 구현, CI 검증 |
| 공개 구조화 데이터 | `content/public/manifest.json`, `content/public/rules/*.json`, `content/public/spells.json` | 7/23/177/79 색인 이관; 본문 부족 |
| HTML 핵심 스모크 테스트 | `tests/test_manual_site.py` | 존재, [main CI #42805475905](https://github.com/degong2-code/wow-rotation-engine/actions/runs/42805475905) PASS |
| 빌드 및 Artifact | `.github/workflows/ci.yml` | `python -m engine.manual_site --output dist/manual/index.html`; `wow-rotation-quick-reference-html` (14일 보존) |
| 현재 간략판 설명 | [MANUAL_PREVIEW.md](MANUAL_PREVIEW.md) | 제품 사용·한계의 기준 설명 |
| 원래 V2 파서·조건·생성기 | `engine/v2/`, `engine/v2/templates/shell.html` | 코드 재사용 가능; 원본 7개 전문화 본문 데이터는 저장소에 없음 |
| 원본 V11/V2 내용 기준 | [v2-origin-manifest.json](v2-origin-manifest.json) | V11 SHA-256 `5d70279c4dd073eccef1f3b13565a8f555cd81c9f0a5b7eda7e3485e410742be`, 898,297 bytes; 원본 자체는 이 공개 저장소에 없음 |
| 공식 이름 관측 증거 | `content/review/blizzard-spell-20261110.json`, [BLIZZARD_LIVE_AUDIT_20261110.md](BLIZZARD_LIVE_AUDIT_20261110.md) | 176 IDs 조회: 150 일치, 1 불일치(`1249809`), 25 API 404 |
| 조건식 후보·검토 엔진 | `content/review/condition-candidates.json`, `engine/condition_worklist.py` | 2개 부분 후보, 175개 미정규화; 빠른 참조판 빌드 필수 아님 |
| 내용 변경 지문 | `engine/source_snapshots.py` | 합성 입력 비교만 실증, 외부 원문 자동 수집 안 함 |
| Pages 준비 | `.github/workflows/deploy-review-pages.yml` | **검토용 수동 배포 워크플로**만 있음; Pages 사이트 최초 활성화·실제 배포 성공은 미확인 |

세부 경로 및 기능 관계는 [PROJECT_MAP.md](PROJECT_MAP.md) 참조. 낡은 [MIGRATION.md](MIGRATION.md), [REVIEW_UI.md](REVIEW_UI.md) 등은 **해당 단계의 역사 문서**이며 최신 제품 상태의 판정은 이 문서와 `main` 코드·최근 Actions를 우선한다.

## 완료 / 부분 / 미실증 / 미구현

**구현·오프라인/CI 완료**
- 7전문화 메뉴, 영웅 특성·상황 전환, 기술명·Spell ID 검색, 대상 수 필터, Wowhead 링크, 단일 HTML 생성. JSON 추가 시 메뉴 확장 테스트 포함.
- CI에서 Python 테스트, 정적 데이터 연결, HTML 결정성, 추출 JavaScript의 `node --check` 통과. [Actions #42805475905](https://github.com/degong2-code/wow-rotation-engine/actions/runs/42805475905), `main` HEAD 위에서 PASS.
- 공식 Blizzard `ko_KR` **실제 조회** 실행 [#42799171635](https://github.com/degong2-code/wow-rotation-engine/actions/runs/42799171635) 완료. 조회 증거는 GitHub에 요약 보관.

**부분 구현**
- 177개 우선순위 행: 순위/기술·일부 시나리오는 공개 데이터로 존재하지만 **원래의 정확한 상세 발동/예외 조건이 부족**. 숫자 조건 두 건의 부분 형식화가 존재할 뿐 완전한 로테이션 solver는 없음.
- Advanced Tips 79개: 현재 제목·태그·원본 위치/해시 색인만 있고 **상세 설명 본문 미복원**.
- 원문 업데이트: 수동 입력의 일부 본문 해시 비교는 가능하지만 실제 웹 공략 자동 변경 확인, AI 의미 해석·검토·JSON 수정·사이트 빌드의 완전한 연결은 없음.

**실제 환경 미실증**
- PR #12의 Actions PASS는 **HTML 생성·JS 구문·정적 조건**의 증거이며 게임 내 딜사이클 적합성이나 실제 브라우저 사용성 테스트를 보증하지 않는다.
- GitHub Pages 최초 활성화·사이트 실제 공개 주소, 실전 사이트 배포는 **미확인**.
- 이전 V2는 로컬에서 18개 테스트 PASS와 V11 HTML 바이트 단위 재생성 SHA 일치 보고가 있었으나 **현재 GitHub 공개 데이터만으로 V11 전체 본문을 재생성하지 못함**. 원본 소스 자료 확보가 선행 조건.
- 이번 인계 작업 컨테이너에서 원본 `wow_rotation_engine_v2_bundle.zip` 및 `reference/v11.html` **파일 경로는 존재하지 않았음**. 원본의 기존 기록/과거 저장 위치를 새 채팅에서 확인하되, 파일이 당장 GitHub에 있다고 가정하지 말 것.

**미구현 / 사용 중단**
- AI 원문 해석→부분 diff→규칙/팁 내용 JSON 업데이트→최종 교본 HTML→Pages 배포의 통합 자동 엔진.
- 선택형 WoW 클라이언트 애드온 코드(`engine/client_spell_probe.py`)는 **유지하되 정규 워크플로에서 사용하지 않음**. [PR #12](https://github.com/degong2-code/wow-rotation-engine/pull/12)에서 기본 CI 애드온 생성 단계 제거. API 404 25건 완전 해소를 제품 개발 선행조건으로 만들지 않음.

**재현 결함 / 충돌 주의**
- 이전 [PR #10](https://github.com/degong2-code/wow-rotation-engine/pull/10)의 178개의 이름 레코드를 176개의 고유 주문 ID와 혼동하던 집계 오류는 수정 완료.
- 현재 공략 표시의 '우선순위 행 순번'은 **적절한 시전 조건의 보증이 아님**.
- 기존 `docs/PUBLIC_DATA.md` 등은 초기 검토 단계 서술을 담고 있으며, 이후 실제 Blizzard 관측/PR #12 상태와 다를 수 있음. 이 문서가 최신 종합 판정.
- 저작권/약관: 원문 전체·대량 번역문을 무단으로 PUBLIC에 커밋하지 말고, 사용자 독자 해설 또는 권한이 확인된 입력을 재사용.
- 비밀 값: `BLIZZARD_CLIENT_ID`, `BLIZZARD_CLIENT_SECRET`은 GitHub Secrets로 등록 및 실제 Actions 조회 성공. 채팅/커밋/Artifact에 토큰을 기록하지 않음.

## 다음 작업 — 개발 효율 판단

| 판단 | 대상 | 이유/실행 |
|---|---|---|
| **REUSE** | `engine/v2/rules.py`, `engine/v2/templates/shell.html`, `v2-origin-manifest.json` | V11 상세 조건/Advanced Tips 구조와 테마 복원 시작점; 원본 7개 전문화 파일 확보 여부 먼저 확인 |
| **CONNECT** | 현재 `manual_site.py` ↔ 허용된 상세 설명 JSON | 기존 7/23/177 순서·검색·메뉴를 유지한 채 정보량 확장 |
| **EXTEND** | 원문 내용 구조화 → 독립적 비교·AI 후보 갱신 → HTML 생성 | 변경된 전문화/조건/팁만 갱신; 검증은 의미 훼손·연결 오류 중심 |
| **STOP** | 추가 WoW 애드온 설치 요구·25개 API 404 완전 해결 선행·자동 게이트 확대 | 최신 사용자 지시와 충돌, 사용자 효용 대비 비효율 |
| **LATER** | Pages 활성화·실전 콘텐츠 게시 | 상세 정보가 준비되면 검토용 Pages와 구분해 설정·배포 |

**단기 로드맵**: (1) V11 전체 본문/사용자 독자 원문이 실제로 접근 가능한지 확인 → (2) 상세 시전 조건·심화 설명을 **새 구조화 상세 콘텐츠**에 연결하고 7개 전문화 가운데 한 전문화부터 완성 → (3) 메뉴/검색/필터를 유지하며 HTML 표시 → (4) 해당 내용 변경에 한정한 CI/뷰 테스트 → (5) 나머지 전문화로 확장.

**장기 로드맵**: 새 전문화 입력·출처 매핑 → 변경 탐지 → AI가 증거 링크가 있는 후보 생성 → 필요한 부분의 경량 검토 → JSON 병합 → 결정론적 HTML 재생성 → GitHub Pages 자동 갱신. 비용 없는 GitHub Actions 기본 실행을 우선하고, 외부 AI API 호출/비용은 사전 검토.

**특별 내용 유의:** 잠행 도적의 심화 운용에서 초자력충전기/고대의 기술은 은밀한 기술 강화 후에도 남은 강화 마무리 기술 충전이 있다면 절개/검은 화약 같은 후속 마무리 기술까지 고려한다는 **기존 사용자 피드백**이 있음. 현재 간략 참조판에 이 심화 설명이 수록된 것으로 간주하지 말고, 내용 복원 때 점검할 예시로 보존.

## 최근 변경 영수증 / 중단점

- 최근 제품 PR: [#12](https://github.com/degong2-code/wow-rotation-engine/pull/12), merge commit `5ba7d12263fbf0b9ecbb52160cc01e2a53e593a0`.
- 제품 CI: [#42805475905](https://github.com/degong2-code/wow-rotation-engine/actions/runs/42805475905) PASS; Artifact `wow-rotation-quick-reference-html` (14일, 만료 가능) 및 `wow-engine-data-review-html`.
- 이 인계는 문서만 격리 브랜치에 PR 제안; **자동 병합/Pages 변경/외부 API 재조회/제품 코드 변경은 하지 않는다**.
- **진행 중인 다른 PR:** 조사 시 0건. 다른 채팅의 비PR 작업 존재 여부는 확인할 수 없음.

## 새 채팅에서 읽는 순서와 시작 제약

1. `main`/열린 PR/브랜치 HEAD와 이 인계 PR의 상태를 먼저 읽기 전용으로 확인.
2. 본 `docs/HANDOFF_CURRENT.md`와 [PROJECT_MAP.md](PROJECT_MAP.md)를 읽고 [MANUAL_PREVIEW.md](MANUAL_PREVIEW.md), `engine/manual_site.py`, `content/public/manifest.json`, `tests/test_manual_site.py`만 우선 확인.
3. 상세 본문 복원 계획에 들어갈 때만 `engine/v2/rules.py`, `engine/v2/templates/shell.html`, [v2-origin-manifest.json](v2-origin-manifest.json)을 확인하고 **실제 V11/V2 원본을 어디서 읽을 수 있는지 확인**한다.
4. 원문 업데이트 설계는 현재 `engine/source_snapshots.py`를 재사용하고, 공식 명칭 오류가 실제 교본 내용에 영향을 줄 때만 조회 자료를 열람한다.
5. **첫 응답은 읽기 전용 상태 복원 보고만**. 사용자가 새 채팅에서 명시적으로 “진행”이라고 승인하기 전까지 코드/문서 변경·커밋/PR/병합·테스트/Actions·외부 수집/API·고비용 작업을 시작하지 않는다.
