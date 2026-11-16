# ROTATION TEXTBOOK — 일반 채팅 간 무손실 인계 계약

> 2026-11-16 작성. **목적:** 일반 ChatGPT 채팅이 길어져 새 채팅으로 옮겨도 제품 정의·승인 상태·실제 개인 HTML·다음 작업·미해결 오류·원문 출처와 검증 한계를 빠뜨리지 않기. 기억/과거 대화 요약만으로 파일이 존재하거나 최신이라고 가정하지 않는다.

## 1. 새 채팅 입장 절차 (필수)

1. 저장소 **degong2-code/wow-rotation-engine**에 실제 접근 가능한지 확인하고 [PROJECT_CANON](PROJECT_CANON.md) → [QUALITY_FIRST_POLICY §0/§0.1](QUALITY_FIRST_POLICY.md) → [CURRENT_STATE](CURRENT_STATE.md) → [CHAT_FIRST_PLAYBOOK](CHAT_FIRST_PLAYBOOK.md) → [ROADMAP_CHAT_FIRST](ROADMAP_CHAT_FIRST.md)의 **현재 브랜치 버전**을 읽는다. 필요한 경우 [SOURCE_ACQUISITION](SOURCE_ACQUISITION.md)과 [EDITORIAL_QUALITY_PROTOCOL](EDITORIAL_QUALITY_PROTOCOL.md) 추가.
2. GitHub **PR/브랜치/HEAD/베이스/미병합 여부/Actions**를 실제 조회한다. CURRENT_STATE에 적힌 SHA/CI는 기록 당시 값이므로 신선도를 재검증한다. main과 활성 작업 브랜치를 혼동하지 않는다.
3. 개인 Library/대화/Project에서 CURRENT_STATE가 가리키는 **원본 V11, 현재 통합 HTML, 해당 전문화 독립본**을 찾고 실제 파일을 읽어 **크기·SHA-256 및 등장 전문화/본문**을 확인한다. 접근 불가하면 역사 문서의 수치와 현재 실물 접근을 구별한다.
4. 정책·제품·원문·UI의 **승인 상태**를 분리한다. 최신 버전 번호가 가장 높은 파일이나 CI 성공을 승인 정본으로 자동 승격하지 않는다. 마지막 사용자 선택: **냉기 V46 조건 괄호 있는 디자인 기본값, V47 괄호 제거안 비채택**.
5. Q0/Q1 내용 검토와 Q4 브라우저 기능 검토를 구분하고 원문 선택형 도움말/오프너·아이콘의 REVIEW 범위를 그대로 복원한다.
6. **사용자가 '읽기 전용 복원' 또는 '인계 상태만 확인'을 요청한 경우에는 상태 보고 후 작업 지시를 기다린다.** 사용자가 처음부터 전문화명·CREATE/UPDATE·'진행'을 명시하면 불필요한 승인 재요청 없이 해당 작업을 수행한다.

## 2. 실제 파일 작업 전/후 체크포인트

### 변경 전
- 어떤 개인 HTML을 기반으로 하는지 **정확한 파일 ID·로컬 경로/Library 경로·실물 SHA** 확보.
- 기본과 수정 대상 전문화의 **기존 게임 본문 범위** 확인. 제로베이스 시험이면 **기존 V11 내용은 초안 작성 후 비교 시에만** 연다.
- 변경이 다음 기술 판단/Q0~Q1 또는 사용자 가독성/Q2~Q3, 실제 Q4 중 무엇을 개선하는지 한 문장으로 적는다.
- 비대상 전문화·기존 자산은 보존. 미확정 외부 원문을 확정 조건으로 섞지 않는다.

### 변경 후
- 로컬 산출물을 실제 생성해 **바이트 수·SHA-256·전문화 수·변경 범위**를 산출한다.
- 첫 화면→상세 표, 영웅 특성·오프너 분기, 기술명/아이콘/툴팁, 모바일·데스크톱과 JS/넘침을 확인하고 Q4 증거 기록. **정형 검사 PASS는 내용 PASS가 아니다**.
- 변경된 게임 문장마다 기준 원문 패치/수정일과 조건을 확인하고 Q0/Q1 미확인 범위 명시.
- **새 버전 파일로 보존**하고 개인 Library 업로드 성공/파일 ID 확인. 이전 버전과 기준 V11 원본을 덮어쓰지 않는다.
- 문서·GitHub 커밋이 개인 파일을 대신하지 않는다. 공개 저장소에는 비공개 HTML/장문 외부 원문을 절대 올리지 않는다.

## 3. 채팅 종료·인계 직전 단일 상태 갱신

**[CURRENT_STATE](CURRENT_STATE.md)를 항상 최종 최신으로 갱신하고, 과거 일자 HANDOFF의 '최신' 구절을 계속 덧씌우지 않는다.** 갱신할 필수 항목:

| 항목 | 반드시 적는 사실 |
|---|---|
| 목표·작업 단계 | 지금 무엇을 만들고, 단기 로드맵 어느 단계인지 |
| GitHub | 활성 브랜치, PR과 base, 조회 당시 HEAD/CI, main 병합 여부 |
| 개인 정본 | 원본 V11 및 최신 **승인/REVIEW 분리**된 HTML 파일명, Library ID/경로, 크기, SHA |
| 변경 범위 | 실제 수정된 전문화/장, 비대상 보존 검사 결과 |
| 출처/범위 | Wowhead URL·패치·수정일·실제로 확인한 영웅/전투/선택 분기 |
| 품질 | Gate A·Q0/Q1·Q2/Q3·Q4 각각 PASS/REVIEW/FAIL과 그 근거 |
| 막힘 | 검증 불가 선택형/툴팁·아이콘/사용자 승인 등 남은 쟁점과 다음 조치 |
| 다음 작업 | 중요도 순 **1~3개**, 재현 가능한 첫 실행 단위 |
| 사용자 선택 | 현재 사용자가 승인한 UI/내용과 반려한 비교본(별개로 기록) |

이후 [ROADMAP_CHAT_FIRST](ROADMAP_CHAT_FIRST.md)은 **개발 단계·완료 조건이 실제로 바뀐 경우에만** 변경한다. 새 규칙은 [QUALITY_FIRST_POLICY](QUALITY_FIRST_POLICY.md) 또는 [CHAT_FIRST_PLAYBOOK](CHAT_FIRST_PLAYBOOK.md) 한 위치에만 정의하고 CURRENT_STATE에는 링크/결과만 적는다. 자세한 실험 로그는 기존 사례 문서에 보존하되 현재 작업 진입점으로 삼지 않는다.

## 4. GitHub 문서 및 브랜치 관리

- 단일 최신 상태는 **CURRENT_STATE**. 이 파일의 '최신 제품'을 지난 인계 문서의 V32/V45 요약으로 되돌리지 않는다.
- 현재 PR이 Draft라면 승인 없이 ready/merge하지 않는다. 기본 브랜치 main은 변경 금지.
- 과거 자료를 삭제·압축해 지식 소실시키지 말고, 목차에서 **HISTORY**라고 명시해 현재 정본과 분리한다.
- 새 채팅 시작 프롬프트는 **깃허브 문서의 실제 내용을 읽게 하는 링크**만 담고, 긴 과거 세부 수치·단일 버전의 로직을 복제하지 않는다.
- git commit/CI까지 끝난 뒤 최종 보고에서는 **제품 Q0~Q4와 CI를 따로 표기**, CI 실행이 끝나지 않았으면 진행 중이라고 기록.

## 5. 새 일반 채팅 인계 프롬프트 (복사)

> **ROTATION TEXTBOOK / WoW Rotation Engine — 독립 상태 복원**
>
> GitHub \`degong2-code/wow-rotation-engine\`의 최신 활성 작업 브랜치에서 **docs/PROJECT_CANON.md → docs/QUALITY_FIRST_POLICY.md §0/§0.1 → docs/CURRENT_STATE.md → docs/CHAT_FIRST_PLAYBOOK.md → docs/ROADMAP_CHAT_FIRST.md → docs/HANDOFF_PROTOCOL.md**를 실제로 읽어라. 오래된 HANDOFF나 README의 과거 상태를 현재 정본으로 삼지 마라.
>
> 최종 제품은 **GitHub의 제작 지식과 최신 공략 원문을 바탕으로 ChatGPT가 V11 이상 한국어 단일 HTML 교본을 CREATE/UPDATE하는 것**이다. 별도 API 자동화 엔진 개발이 목적이 아니다.
>
> GitHub 실제 PR/head/base/CI를 다시 조회하고, CURRENT_STATE의 최신 개인 HTML을 Library/첨부에서 실제 열어 파일 크기·해시·전문화·승인/REVIEW 상태를 검증하라. 접근하지 못한 개인 파일을 복원했다고 주장하지 마라. 기존 승인본과 다른 전문화의 본문을 보존하고, 원문 Gate A·게임 Q0/Q1·독해 Q2/Q3·기능 Q4를 분리하라. 원문 조건과 오프너를 추측하지 말며, 불필요한 기능/검사기 개발보다 실제 품질 높은 교본 제작을 우선하라.
>
> **이번 메시지는 읽기 전용 복원 요청이다.** 실제 파일·GitHub 변경이나 새 교본 제작 없이 현재 상태, 핵심 보류 사항, 우선순위 1~3개만 간결히 보고하고 \`진행\`을 기다려라.

이 프롬프트는 **명시적 복원 요청**에만 사용한다. 일반 프로젝트 채팅에서 사용자가 \`사격 사냥꾼\`을 입력했다면 복원 자료를 확인한 뒤 곧바로 해당 CREATE/UPDATE 업무를 시작한다.

## 6. 복원 실패 시 정상 대응

- GitHub 커넥터/원본 HTML/웹 자료 중 하나가 없으면 **어느 증거가 누락됐는지 정확하게 명시**하고 가능한 범위만 처리한다. 없는 내용을 추정해 PASS하지 않는다.
- 이미 문서에 적힌 사용자 요구를 다시 질문하지 않는다. 꼭 필요한 최신 자료가 빠질 때만 한 가지 명확한 입력을 요청한다.
- 다음 채팅이나 다음 날에 사용자에게 전달할 수 있다고 백그라운드 수행을 약속하지 않는다.
- **프로젝트 지침이 GitHub 문서에서 자동 동기화되는 것은 아니다.** 실제 프로젝트 설정에 최소 부팅 지침을 등록해야 재진입 성공률이 높아진다. [CHAT_FIRST_PROJECT_INSTRUCTIONS](CHAT_FIRST_PROJECT_INSTRUCTIONS.md) 참조.
