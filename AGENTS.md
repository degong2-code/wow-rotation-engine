# ROTATION TEXTBOOK — 모든 작업자/AI의 진입 지침

**제품:** GitHub의 제작 지식·품질 기준 + 해당 시즌의 공략 원문을 바탕으로 **ChatGPT가 V11 이상 한국어 단일 HTML 교본을 CREATE/UPDATE**한다. WoW 정보의 정답 데이터베이스나 별도 AI API/웹앱 개발 프로젝트가 아니다.

## 새 채팅 기본 로딩 — 4개만

1. [PROJECT_CANON](docs/PROJECT_CANON.md) — 제품 정의
2. [QUALITY_FIRST_POLICY](docs/QUALITY_FIRST_POLICY.md) §0/§0.1/§5.1 — 최상위 정책
3. [CURRENT_STATE](docs/CURRENT_STATE.md) — **최신 개인 파일·REVIEW·다음 작업** (PR/HEAD/CI 실조회)
4. [CHAT_FIRST_PLAYBOOK](docs/CHAT_FIRST_PLAYBOOK.md) — **실행 가능한 제작/통합 UI 계약**

**기본 4개는 시작점이다.** [PLAYBOOK §0.1](docs/CHAT_FIRST_PLAYBOOK.md)의 **작업별 필수 참조 표**를 적용한다. 특히 **신규 CREATE·원문 UPDATE·선택형/오프너/툴팁 미확보**라면 [SOURCE_ACQUISITION](docs/SOURCE_ACQUISITION.md)과 **기존 HTTP/WHML 수집 코드·과거 실증**을 먼저 실제 확인한다. 웹 텍스트에 없다고 원문이 없다고 단정하거나, 기존 도구 확인 전에 사용자 Ctrl+S를 기본 요구하지 않는다. 인계는 [HANDOFF_PROTOCOL](docs/HANDOFF_PROTOCOL.md), 장기 방향은 [ROADMAP](docs/ROADMAP_CHAT_FIRST.md)을 필요할 때만 참조한다. 과거 장문 자료는 해당 작업에 필요한 증거 부분만 조회한다.

## 작업의 절대 기준

- **실제 원문 및 버전부터:** 사용자 지정 원문 우선, 없으면 동일 패치의 Wowhead 하나를 편집 기준. 영웅/전투/선택/숨은 관련 본문·오프너를 검토하며 없는 자료를 채우지 않음.
- **진짜 게임 판단만:** 기술 사용 자체가 증명하는 전제·상위 조건 불충족을 우선순위마다 반복하지 않음. 선택이 달라지는 숫자·발동·예외는 반드시 보존. 사용자 교본은 공식 한국어 기술명/아이콘/툴팁 사용.
- **채택한 UI:** 빠른 참조의 기술명은 주정보, 조건은 괄호·작은 글씨·옅은 색. 사용자용 가정형 실전 사례 장 금지, 내부 반례 검증 유지. 구조/표/행 수 고정 금지.
- **품질 판정:** Gate A 원문 / Q0·Q1 게임 / Q2·Q3 독해·사용성 / Q4 HTML 기능을 **분리**. CI 통과는 내용 정답이나 최종 승인 증거가 아님.
- **제품 보호:** 비대상 전문화·원본 V11 보존, 다른 패치 자료 혼합 금지, 공개 저장소에 개인 전체 HTML·외부 장문 원문·비밀키 게시 금지. 사용자 승인 없이 main 변경/PR 병합/공개 배포 금지.
- **작업 선택:** 의미 있는 완성 교본 CREATE/UPDATE·V11 독립 재생성/사후 비교를 우선. 한 이슈·새 검사기·독립 AI 엔진 개발에 매몰되지 않음.
- **새 채팅:** 현재 사용자 지시가 명시적 읽기 전용 복원이면 상태만 조회. 전문화명/CREATE/UPDATE/진행이면 바로 실행. 일반 채팅에 Work/Codex 전환 필수 요구 금지.
- **인계:** 다음 채팅을 위해 유일한 상태 파일 [CURRENT_STATE](docs/CURRENT_STATE.md)를 실제 파일 ID·SHA·승인 경계로 갱신. 과거 HANDOFF는 역사 기록이다.

**프로젝트 설정 주의:** AGENTS.md 및 GitHub 문서만 변경해도 ChatGPT의 실제 프로젝트 지침이 자동 변경되지는 않는다. [CHAT_FIRST_PROJECT_INSTRUCTIONS](docs/CHAT_FIRST_PROJECT_INSTRUCTIONS.md)의 최소 본문을 사용자가 해당 ChatGPT 프로젝트 설정에 등록한다.
