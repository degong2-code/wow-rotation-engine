# HANDOFF_PROTOCOL — 일반 채팅 간 복원·종료 계약

> **현재 상태는 [CURRENT_STATE](CURRENT_STATE.md) 하나만** 사용한다. V83/이전 날짜별 HANDOFF 및 [옛 장문 인계](HANDOFF_CHAT_FIRST_CURRENT.md)는 **HISTORY**로만 참조. 이 문서에는 새 버전별 인계문을 붙여 늘리지 않는다.

## 새 채팅 시작 (평소 4개 문서만)

1. GitHub `degong2-code/wow-rotation-engine`의 **현재 활성 PR/HEAD/base/CI를 실조회**한다. `main`과 Draft 작업 브랜치 혼동 금지.
2. **[PROJECT_CANON](PROJECT_CANON.md) → [QUALITY_FIRST_POLICY](QUALITY_FIRST_POLICY.md) §0/§0.1/§5.1 → [CURRENT_STATE](CURRENT_STATE.md) → [CHAT_FIRST_PLAYBOOK](CHAT_FIRST_PLAYBOOK.md)**를 기본 로드. 제작·분석을 시작할 때는 PLAYBOOK **§0.1 작업별 필수 참조**를 추가로 수행한다(원문 의존 작업이라면 기존 SOURCE_ACQUISITION/HTTP/WHML 연구·코드 필수). 과거 HANDOFF 전부는 기본 정독하지 않는다.
3. 실제 사용할 개인 HTML(V11 비교 기준/최신 통합/독립본)을 개인 Library에서 열어 **파일 실물 크기·SHA-256·해당 전문화·승인 상태**를 검증한다. 문서의 파일명/해시는 실물 확보 증거가 아니다.
4. 요청이 명시적 **읽기 전용 독립 복원**이면 GitHub 상태·실제 파일·품질 REVIEW·다음 작업을 보고하고 변경하지 않는다. 전문화명·UPDATE는 해당 제작을 진행한다. **`진행` 단독**은 직전 명확한 진행 작업, 없으면 CURRENT_STATE §4 첫 실행 가능 과제의 순서로 선택하고 PLAYBOOK §0.1 참조를 적용한다.

## 실제 제작 전/후

- **전:** 최신 원문 패치/영웅/선택형 확보 범위, 변경 대상, 기존 UI 자산 및 비대상 보존 범위 확정. 제로베이스 집필이면 기존 V11 게임 본문은 *초안 완성 후 비교*.
- **중:** 원문 Gate A → 조건·행동 Q0/Q1 → 빠른 참조·설명 Q2 → **기존 호평 교본과 동폭 실화면 비교 Q3** → HTML/JS·통합·모바일 Q4. Q4가 Q3 또는 게임 정답을 대신하지 않는다.
- **후:** 새 개인 HTML 생성·Library 저장, 파일 **실제 크기/SHA/ID 재조회**, 본문/JS 보존 범위, Gate A/Q0~Q4 각 판정과 외부 CDN·로컬 실행 한계 보고. 승인 없는 main/PR 병합·배포 및 개인 HTML/원문 공개 업로드 금지.
- **종료:** [CURRENT_STATE](CURRENT_STATE.md) 현 상태 행을 **교체**하고, 실제 다음 1~3개 작업만 남긴다. 날짜별 대형 요약/새 인계 문서/새 검사기는 기본 생성하지 않는다. 규칙 변경은 [PLAYBOOK](CHAT_FIRST_PLAYBOOK.md)의 기존 관련 문장을 **수정**하고, 기존 사실 미적용이면 새로운 규칙을 추가하지 않는다.

## 새 일반 채팅에 붙여 넣을 복원 프롬프트

> **ROTATION TEXTBOOK — 현행 GitHub 정본 기반 읽기 전용 독립 복원**
>
> 이전 채팅의 요약이나 과거 날짜별 HANDOFF를 최신 상태로 사용하지 말고, GitHub `degong2-code/wow-rotation-engine`의 **실제 열린 PR·작업 HEAD·base·CI**를 먼저 조회하라. `main`과 Draft 작업 브랜치를 혼동하지 마라.
>
> 해당 HEAD에서 **`docs/PROJECT_CANON.md` → `docs/QUALITY_FIRST_POLICY.md` §0·§0.1·§5.1 → `docs/CURRENT_STATE.md` → `docs/CHAT_FIRST_PLAYBOOK.md`**를 읽어라. `CURRENT_STATE`가 유일한 현재 제품·REVIEW·다음 작업 정본이다. `HANDOFF_PROTOCOL`은 복원 절차, 날짜별 V83/이전 인계는 HISTORY다. 첫 복원에서 불필요한 과거 이력을 전부 정독하지 마라.
>
> **Library 실물로 검증:** `CURRENT_STATE`의 최신 **통합 REVIEW HTML(전문화 수는 CURRENT_STATE에 따름)**, 미통합 **독립 전문화 REVIEW HTML**, UX 비교용 **V11 원본**, 필요시 호평 독립본/개인 원문을 실제 열어 **파일명·Library ID·바이트·SHA-256·전문화 수·승인/REVIEW**를 확인하라. 기록된 해시를 지금 열었다는 증거로 둔갑시키지 마라. 독립본을 통합본의 전문화 수에 합산하지 마라.
>
> **확정 방향:** ChatGPT 일반 채팅에서 최신 패치 원문을 독립 분석해 V11 이상 한국어 단일 HTML을 CREATE/UPDATE한다. 독립 AI API 엔진·거대 JSON·공개 웹앱·검사기 증식이 목표가 아니다. 새로운 UI를 매번 재설계하지 않고 호평받은 실제 공통 구성요소를 재사용하되, 과거 교본의 게임 로직은 정답으로 가져오지 않는다.
>
> **실수 방지:** 원문 Gate A(영웅/전투/특성/소비재 선택·접힘·실제 ?/hover·오프너·WHML) → 게임 조건/행동 Q0·Q1 → 독해 Q2 → 실제 동폭·모바일 가독성 Q3 → 기능·보존 Q4를 구분한다. **첫 화면 단일/광역 우선순위에는 다음 기술을 실제로 바꾸는 발동·중첩·대상 수·타이밍 조건만** 남기고, 기술명/배타적 대안만으로 명백한 반복 설명은 상세에 보관한다. 오프너는 **실제로 누를 완결된 순서 하나**로 표현하고 5단계 미리보기나 원시 타임라인 표식 복사·상세 중복·검증 메타 노출을 피한다. 실제 원문에서 행동을 바꾸는 숨은 조건은 간결화하면서 절대 지우지 않는다.
>
> **보고:** 실제 HEAD/PR/base/CI; 실물 확인된 통합/독립/V11 파일·해시; 현행 전문화 수·사용자 확정 UI 선호; Gate A 및 Q0~Q4 증거·REVIEW; 원문 내부의 미해결 충돌과 사용자 모바일·전체 미승인; `CURRENT_STATE §4`의 다음 1~3개 작업과 이유. 기능/CI PASS와 사용자 Q2/Q3·게임 Q0/Q1 최종 승인을 구분하라.
>
> **이번 첫 응답은 읽기 전용이다.** GitHub/HTML/PR 변경·Actions 수동 실행·대량 원문 수집·새 전문화 집필·배포를 하지 말고 복원 결과를 보고한 뒤 사용자 `진행`을 기다려라. 후속 제작을 시작할 때만 `CHAT_FIRST_PLAYBOOK §0.1`의 **작업별 필수 참조 경로**(원문 의존 시 `SOURCE_ACQUISITION` 및 기존 HTTP/WHML 코드)를 실제 확인·가능하면 실행한다. 사용자에게 수집을 성급히 떠넘기지 않는다. 개인 HTML·저장 공략 원문 공개 GitHub 업로드, 승인 없는 병합, Work/외부 API 강제 전환 금지.

**중요:** 이 프롬프트는 사용자에게서 *읽기 전용 복원*을 명시적으로 요청받은 경우에만 적용한다. 전문화명 단독 입력이나 후속 `진행`은 현행 PLAYBOOK의 실제 제작·작업 선택 규칙을 따른다.

## 복원 실패 처리

- GitHub/Library/원문이 실제로 없으면 이전 인계의 숫자를 실물 확인으로 둔갑시키지 말고 해당 범위를 REVIEW.
- GitHub 문서를 수정해도 ChatGPT 프로젝트 설정이 자동 갱신되지는 않는다. 사용자 설정에는 [최소 시작 지침](CHAT_FIRST_PROJECT_INSTRUCTIONS.md)을 별도로 등록한다.
- 본문 상세 검증과 과거 실험은 [이전 절차 이력](https://github.com/degong2-code/wow-rotation-engine/blob/e3416fc9643f2108187648c356d776115e5cda82/docs/HANDOFF_PROTOCOL.md) 및 [사례집](QUALITY_GENERALIZATION_CASEBOOK.md)에 남는다.
