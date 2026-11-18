# ROADMAP_CHAT_FIRST — 장기 제품 완료 기준

> **현재 할 일·작업 순서는 [CURRENT_STATE §4](CURRENT_STATE.md)만 정본.** 이 파일은 완료된 UI 시범이나 날짜별 개발 목표를 다시 '다음 작업'으로 열거하지 않는다. [기존 로드맵 전체](https://github.com/degong2-code/wow-rotation-engine/blob/f989fbd3205949bae141078829fb60a86328ca72/docs/ROADMAP_CHAT_FIRST.md)는 Git 이력에 보존.

## 1. 재현 가능한 단일 교본 제작

- 일반 ChatGPT 채팅에서 전문화명 입력 → 실제 최신 패치 기준 원문 확보 → 게임 상태·조건·행동·이유·오프너·영웅 특성 분석 → **V11 이상 품질 한국어 단일 HTML** 제작·Library 비공개 저장·REVIEW/승인 구분.
- **원문 Gate A:** 선택형·접힌 본문·관련 툴팁·오프너까지 포함해 실제 결정에 영향을 미치는 원문을 확보. 웹 텍스트가 빠진 경우 [SOURCE_ACQUISITION](SOURCE_ACQUISITION.md)의 기존 정상 HTTP/WHML·DOM 코드를 우선 재사용. 접근 불가와 본문 부재/조건 미확정을 구분하고 미확정 사항은 REVIEW.
- **내용 Q0/Q1:** 원문 숫자·분기·예외·우선순위를 임의 합치거나 과거 교본에서 추정하지 않는다. 상세↔첫 화면의 실제 다음 기술 선택을 역방향 검증.
- **Q2/Q3/Q4:** 사용자 독해·동폭 가독성/모바일·선택형 UI와 HTML 기능·타 전문화 본문 보존을 따로 검증. CI PASS와 사용자 승인 구분.

## 2. 여러 전문화·패치에서의 반복성

- 서로 다른 원고 계보의 **신규 CREATE 최소 2종**, V11 전문화의 **독립 제로베이스 재제작 2~3종**, 기존 전문화의 **패치 UPDATE 최소 1회**에서 같은 절차가 재현돼야 한다. 기존 v1→v3 교정본은 독립 CREATE 수에 중복 계산하지 않는다.
- 다른 메커니즘의 전문화에도 UI 구성요소를 재사용하고, 고유 조건·오프너·영웅 분기를 보존한다. 전체 UI를 자동 일괄 변경하거나 문서·장 수를 강제하지 않는다.
- 새 일반 채팅에서도 GitHub **기본 4문서 → PLAYBOOK §0.1 필수 작업별 참조 → 기존 코드 적용/실행 증거 → Gate A/Q0~Q4 분리**가 실제로 작동해야 한다. 코드가 *있다*는 것만으로 원문 수집 성공이라고 주장하지 않는다.

## 3. 유지보수와 장기 지속성

- 새 시즌/확장팩 원문부터 다시 분석. 이전 패치 게임 사실/선택 조건을 재사용하지 않는다.
- [PROJECT_CANON](PROJECT_CANON.md) 제품 정의, [QUALITY_FIRST_POLICY](QUALITY_FIRST_POLICY.md) 품질 규범, [CHAT_FIRST_PLAYBOOK](CHAT_FIRST_PLAYBOOK.md) 실행 경로, [CURRENT_STATE](CURRENT_STATE.md) 단일 현황, Git 이력/사례집의 상세 증거를 구분한다.
- 정책 누적·검사기 증식·독립 AI API·공개 웹앱을 목표로 삼지 않는다. 이미 검증된 기존 수집·UI·QA 자산을 적용한 다음 **실제 교본 품질**로 성과를 측정한다. 사용자 승인 없이 메인 병합·비공개 HTML/원문 공개 업로드 금지.
