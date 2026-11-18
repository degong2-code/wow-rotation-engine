# ROTATION TEXTBOOK — ChatGPT 중심 한국어 WoW 딜사이클 교본

**목표:** 사용자가 일반 ChatGPT 채팅에 WoW 전문화 이름만 입력하면, 해당 패치의 실제 공략 원문을 분석해 **V11 이상 품질의 한국어 단일 HTML 교본**을 CREATE/UPDATE한다. 별도의 AI API 엔진·공개 웹앱·검사기 증식이 목적이 아니다.

## 시작 — 기본 4개 문서

1. [PROJECT_CANON](docs/PROJECT_CANON.md) — 불변 제품 정의 및 문서 역할
2. [QUALITY_FIRST_POLICY](docs/QUALITY_FIRST_POLICY.md) **§0/§0.1/§5.1** — 품질·게임 판단·UI 우선 원칙
3. [CURRENT_STATE](docs/CURRENT_STATE.md) — **지금의 제품, 개인 Library 파일, REVIEW, 다음 작업**
4. [CHAT_FIRST_PLAYBOOK](docs/CHAT_FIRST_PLAYBOOK.md) — 실제 CREATE/UPDATE 순서 및 **작업 유형별 필수 참조 경로**

**중요:** 4개는 *진입용*이다. 신규 전문화·원문 의존 UPDATE라면 [PLAYBOOK §0.1](docs/CHAT_FIRST_PLAYBOOK.md)의 라우팅에 따라 **[SOURCE_ACQUISITION](docs/SOURCE_ACQUISITION.md)과 기존 원문 수집 코드를 반드시 확인**한다. 오프너/선택형/툴팁 등이 웹 텍스트에 없다면 기존 HTTP·WHML 재사용 경로부터 확인하고, 곧바로 사용자에게 수동 HTML 여러 개를 요청하지 않는다.

## 실제 제품 진행

`원문 Gate A → 조건·행동 Q0/Q1 → 한국어 설명·빠른 참조 Q2 → 동폭 화면 비교 Q3 → HTML/JS·비대상 보존 Q4`

- 원문은 **동일 패치·한 개 기준 공략**에서 독립 분석. 확정하지 못한 조건은 REVIEW로 남긴다.
- UI는 기존 긍정 평가된 공통 구성요소를 재사용하되, 전문화 고유 게임 판단·오프너를 고정 형식에 억지로 맞추지 않는다.
- **CI/Q4 PASS는 게임 정답·독해·사용자 승인과 별개**다.
- 개인 HTML과 저장 원문은 비공개 Library/대화에 보관. **공개 GitHub 업로드 금지**. 사용자 승인 없이 main 병합·공개 배포 금지.

## 필요할 때만 읽는 자료

| 작업 | 진입 문서 |
|---|---|
| 선택형 Wowhead 원문·툴팁·타임라인 | [SOURCE_ACQUISITION](docs/SOURCE_ACQUISITION.md) → 과거 실증·실제 코드 |
| 정확한 게임 판단·조건 역방향 검증 | [EDITORIAL_QUALITY_PROTOCOL](docs/EDITORIAL_QUALITY_PROTOCOL.md) |
| 새 채팅 읽기 전용 복원·인계 | [HANDOFF_PROTOCOL](docs/HANDOFF_PROTOCOL.md) |
| 장기 제품 로드맵 | [ROADMAP_CHAT_FIRST](docs/ROADMAP_CHAT_FIRST.md) |
| 오래된 성공·실패 원인 확인 | [QUALITY_GENERALIZATION_CASEBOOK](docs/QUALITY_GENERALIZATION_CASEBOOK.md) 해당 부분 / Git 이력 |
| ChatGPT 프로젝트 설정 갱신 | [CHAT_FIRST_PROJECT_INSTRUCTIONS](docs/CHAT_FIRST_PROJECT_INSTRUCTIONS.md) |

**역사 보존:** 예전 V2 엔진, 데모 빌드, 공개 데이터·개별 이슈의 장문 설명은 [정비 직전 README 원문](https://github.com/degong2-code/wow-rotation-engine/blob/592574080fcf6cd6d0a89906c8ffff25dda69363/README.md)과 Git 이력에 그대로 남는다. 현재 제품의 기본 실행 경로로 오인하지 않는다.

**운영 원칙:** 최신 HEAD·활성 PR/base/CI는 실제 GitHub에서 조회하고, 개인 HTML 사용 전에는 실물 파일 크기·SHA를 다시 검증한다. 문서는 날짜별 로그를 누적하는 대신 **현재 유효한 방법으로 교체**한다. GitHub 지침 수정이 ChatGPT 프로젝트 설정에 자동 반영되는 것은 아니다.
