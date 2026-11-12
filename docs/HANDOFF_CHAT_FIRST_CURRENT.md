# ROTATION TEXTBOOK — Chat-first 교본 제작 인계 정본

> **인계 기준일:** 2026-11-11 (KST)  
> **상태:** 인계 준비 완료를 위한 증거 정본. 사용자 승인 없이 `main`·원본 교본·공개 Pages를 변경하지 않음.  
> **우선순위:** **교본의 게임 상태·조건·행동 정확성 > 원리·예외 설명 > 사용성 > HTML 검증 > 독립 엔진 구현**.  
> **이 문서는 새 채팅 복원 진입점**이다. **최상위 운영 정책은 [QUALITY_FIRST_POLICY](QUALITY_FIRST_POLICY.md)**, 구체적 품질 게이트는 [EDITORIAL_QUALITY_PROTOCOL](EDITORIAL_QUALITY_PROTOCOL.md), 집필 절차는 [CHAT_FIRST_PLAYBOOK](CHAT_FIRST_PLAYBOOK.md)을 정본으로 삼으며 중복 복제하지 않는다. **과거 사례로 범용화 가치/오탐을 검증하는 후향적 사례집은 [QUALITY_GENERALIZATION_CASEBOOK](QUALITY_GENERALIZATION_CASEBOOK.md) 참조.**

## 1. 현재 제품 정의와 사용자 경험

사용자는 ChatGPT 프로젝트 채팅에서 `생존 사냥꾼`, `화염 마법사 업데이트`처럼 **전문화 이름과 필요한 의도만 입력**한다. ChatGPT가 승인된 개인 V11 원본을 확인하고 최신 소스의 패치·빌드·규칙을 조사한 뒤, 기존 V11 수준 이상의 **한국어 단일 HTML 교본을 신규 CREATE 또는 기존 교본 UPDATE**하여 해당 채팅에서 파일로 전달한다.

- **ChatGPT:** 출처 탐색, 게임 상태·수치·조건 추출, 충돌 분석, 전문화별 최적 설명 구조 결정, 집필, 실제 HTML 수정·검증·결과 전달.
- **GitHub:** 제작 규격, 출처 URL/패치 메타데이터, 원형 보존·기능 QA 코드, 구현 기록, 커밋·CI 증거. 공개 GitHub는 개인 교본 본문 저장소가 아니다.
- **기존 V2 코드/JSON:** 필요한 경우 HTML 원형 보존·패치·브라우저 검증을 위한 **보조 수단**. 데이터 스키마·페이지 장 수·표 개수를 집필 내용보다 먼저 고정하지 않는다.
- **현재 필수 경로에서 제외:** 독립 AI API/Plus OAuth/Codespaces/Actions 무인 AI 추론/별도 웹앱. PR #17–#19는 삭제하지 않고 역사적 검토 기록으로 보존한다.
- **비동기 실행·무제한 품질 자동 승인 아님:** 현재 요청에서 실제 접근 가능한 파일·도구로 작업한다. 계정별 추가 사용량/게임플레이 최적성을 보장하지 않는다.

관련 결정: [ADR-003 — Chat-first](ADR_003_CHAT_FIRST_EDITORIAL.md), [사용자 실행 지침](CHAT_FIRST_PROJECT_INSTRUCTIONS.md).

## 2. 실제 GitHub 복원 지점 (새 대화에서 재조회 필수)

- 저장소: **`degong2-code/wow-rotation-engine`** (공개 제품·개발 기록).
- 활성 개발 브랜치: **`work/chat-first-v11-20261111`**, Draft **PR #20**. PR #20의 기준 브랜치는 `work/v11-fidelity-arcane-20261111` (PR #16)로, 인증 실험 PR #17–#19와 **종속되지 않는다**.
- **이번 인계 작업 직전 확인된 개발 HEAD:** `5f9a6b5143d3f95a4069fd1f512d398fa0d5ec01`. **인계 문서 커밋으로 HEAD가 변경될 수 있으니 현재 값을 반드시 GitHub에서 다시 확인**한다.
- 당시 `main` HEAD: `5ba7d12263fbf0b9ecbb52160cc01e2a53e593a0`. 변경·병합하지 않았다.
- 기존 PR #14–#20: 조회 시 모두 open; #14–#20 Draft (별도로 #13은 역사적 handoff PR이며 open, non-Draft). 이전 PR의 완료·미병합 상태는 실제 GitHub에서 재확인한다.
- 당시 마지막 push Actions: [run #42935513509](https://github.com/degong2-code/wow-rotation-engine/actions/runs/42935513509) / PR Actions [#42935520228](https://github.com/degong2-code/wow-rotation-engine/actions/runs/42935520228), 성공. **로그 기준 202/202 합성 테스트 PASS**. 이 증거는 신규 V3 교본의 게임플레이 사실 검증이 아니다.
- GitHub의 활성 `docs/`에는 이번 인계 정본이 없었으므로 본 파일을 새로 작성한다. 예전 PR #13/엔진 인계 문서가 별도 브랜치에 있더라도 신규 제품 경로의 최상위 정본으로 되돌리지 않는다.

**GitHub 검증:** `main` / 활성 브랜치 HEAD, PR #20(base/head/state), PR #14–#19 보존 상태, 최종 push-triggered Actions의 `head_sha`/결론을 실제로 조회한다. 증거가 이미 PASS이면 인계 목적 때문에 전체 집필/수집/QA를 재실행하지 않는다.

## 3. 개인 V11 원본 및 생존 V3 — 접근과 승인 구분

### 개인 기존 7개 V11 HTML (이번 인계 세션에서 직접 검증됨)

- 파일명: `wow_rotation_manual_engine_v2.html`.
- 실제 크기 **898,297바이트**, SHA-256 **`5d70279c4dd073eccef1f3b13565a8f555cd81c9f0a5b7eda7e3485e410742be`**.
- 이번 인계 세션의 개인 Library 파일을 실제로 materialize하고 직접 SHA-256을 계산함. **7개 `manual-view`** 확인. 새 채팅에서도 이 파일이 자동 마운트되는지는 보장하지 않으므로 Files/Project/Library에서 실제 확인한다.
- 정본 전문화: **화염·냉기 마법사, 냉기 죽음의 기사, 사격·야수 사냥꾼, 잠행·암살 도적**.
- 사용자 평가상 이 일곱 전문화는 **딜사이클 판단 조건·수치·이유·예외를 명확히 전달한 품질 기준**이다.
- 신규/부분 수정 시 비대상 기존 7개 `manual-view`의 **원시 HTML 바이트 동일성**을 검증한다. 개인 원본이나 해당 본문 전체를 공개 GitHub·CI Artifact·Pages에 올리지 않는다.

### 생존 사냥꾼 V3 (GitHub의 당시 제작·검증 기록, 이번 세션에서 파일 미확보)

- 기록: [생존 V3 전면 재집필](CHAT_FIRST_RUN_SURVIVAL_V3_20261111.md).
- 파일명 `wow_rotation_v11_survival_reauthored_v3.html`; 기록된 크기 **1,104,628바이트**, SHA-256 **`83cc1ba65e9a72a16d2acc2ce0027c3ca58524da0765808a159b7a02bd078e04`**.
- 내용 기록: **8전문화 통합**, 생존 **8개 주요 영역**, 파수꾼·무리의 지도자 영웅 특성별 단일/광역 **우선순위 4표·37행** (기본 열 `순위 / 행동 / 사용 조건`), 영웅별 빠른 참고 요약 2표, 기존 7개 본문 원시 바이트 동일성 7/7.
- 당시 브라우저 검증 기록: Chromium **1365×850 / 390×844**, 직업/전문화 메뉴 접기·펼치기, 영웅 전환, 툴팁·`?`, 기존 전문화 복귀, 목차/가로 넘침, JS 오류 0. Node 정적 검증 기록도 있음.
- **반드시 지킬 상태 분리:** (a) 당시 파일 생성·브라우저 검증 완료는 **기록 확인**, (b) **이번 인계 실행에서 V3 실제 파일은 대화/Project/Library 검색과 작업 컨테이너에서 확인되지 않아 다시 읽거나 해시 계산하지 못함**, (c) **사용자의 최종 정본 승인 확인되지 않음**. 따라서 V3는 **검토본/승인 대기**다.
- 생존 V1/V2는 실패·비교 이력. 특히 V2 Quick Reference 국소 수정본을 최신 정본으로 오인하지 않는다. 새로운 작업에서 V2의 본문을 기본 초안으로 가져오지 않는다.
- V3 HTML이 필요한 다음 작업에서는 해당 파일의 실제 가용성을 먼저 확인하되, 이를 공개 GitHub에 업로드해 복구하지 않는다. 사용자의 명시적 새 정본 승인 없이는 원래 7전문화 HTML을 덮어쓰지 않는다.

## 4. 생존 V1/V2 실패 → V3 개선: 왜 그랬는가

| 실패 메커니즘 | 관측된 문제 | 근본 예방 |
|---|---|---|
| **Template-first / 2열 데이터** | `priority(action,reason)`가 기술·조건을 한 칸으로 합치고 정확한 사용 조건을 별도 검증할 수 없게 함 | 소스에서 **상태→조건식→행동→이유→예외** 추출 후 맞는 표/흐름 선택 |
| **출처 혼합/패치 불일치** | Wowhead·Icy Veins·Method의 패치·영웅·선택 특성을 섞고 제거 기록이 있는 `Flamefang Pitch`를 초안에 남김 | 동일 패치·빌드의 **기준 공략 1개** 고정, 보조 출처는 검증/반례용 |
| **모호한 회피 문장** | `상황에 따라`, `특성에 따라 달라질 수 있음`으로 실수치·행동 변화를 숨김 | **어떤 특성/상태/임계값에서 어떤 행동을 하는지** 인접해 기술 |
| **분량·UI PASS에 과신** | V2는 10장/38행·많은 텍스트·버튼 정상인데도 판단 정보가 희석 | 조건 충실도/반례를 콘텐츠 QA로 독립 검사; JS/바이트 동등성은 별도 기능 QA |
| **국소 패치** | Quick Reference만 수정해 오프너·우선순위·심화 전체 결함은 잔존 | 피드백 발생 시 해당 **오류 생성 방식**이 전 장에 반복되는지 전체 감사 |
| **실패 초안 관성** | 잘못된 2열 템플릿·일반론을 반복 편집하여 품질 손실 재생산 | V1/V2는 반례·회귀 자료로만, 근거에서 독립 재추출 |
| **정보 선택 실패** | 다량 원문을 읽고도 중첩·충전·지속시간·대상수 정보가 일반 설명으로 치환 | 적은 글로 **다음 GCD를 선택 가능하게 하는 정보 밀도** 우선 |

**V3의 기록된 실질 개선:** 내용 약 16,172→12,796자(단순한 분량 자체가 품질 증거는 아님), 10→8영역, 4표 38→37행, 핵심 수치와 예외 회복. 예: 쌍둥이 송곳니 OFF이면 제압 전 창끝 ≥2, ON이면 창끝 0에서 진입/3 생성·1 소비; 붐스틱 집중 50/전방 20야드/약 3초 채널; 파수꾼 폭탄 완충 4~6초 전; 무리의 지도자 제압 후 **첫** 살상 명령 쇄도; 제거된 `Flamefang Pitch` 제외. 이 수치·패치 적합성은 **V3 제작 기록의 검토 근거**이고 새 패치에 무조건 재사용할 수 없다.

기존 7전문화 전수 비교: [V3 기록 §1](CHAT_FIRST_RUN_SURVIVAL_V3_20261111.md)에 화염 발화/30% 마무리, 냉기 6/12중첩, 냉죽 룬·도살기, 사격 정밀/교묘한 사격, 야수 날카로운 사격 2충전·격노 3초, 잠행 춤/연계점수, 암살 출혈·독 등 **전문화마다 다른 판단 변수를 어떻게 표현했는지** 기록되어 있다. 모든 전문화에 같은 장 수/표 수를 강제하지 않는다.

## 5. 다음 제작의 **강제 품질 게이트** (세부는 EDITORIAL_QUALITY_PROTOCOL)

1. **Gate A — 자료 범위:** 패치·시즌·영웅·ST/AoE·선택 특성·세트를 확인하고 **기준 소스 하나**를 고른다. 패치에서 삭제된 기술·옛 특성 적용 금지.
2. **Gate B — 규칙 추출:** 버프/중첩/집중/쿨다운/대상수/충전/위치의 **상태·판정식·행동·이유·예외·URL 근거**를 **문장 작성 전에** 기록한다. 상태 없는 행동/의미 없는 포괄 설명은 우선순위 행으로 확정하지 않는다.
3. **Gate C — 모순/반례:** 능력 OFF/ON, 중첩 임계 전/후, 충전 만료 전/후, 오프너와 지속 딜의 충돌, 영웅 특성 교차 오염 확인. **실제 중요한 결정 분기·경계 기반의 검증**(고정 6개 사례 할당량 아님).
4. **Gate D — 최적 표현:** 첫 화면에는 실전용 단일·광역 지속 딜/오프너/핵심 원칙. 상세 우선순위의 기본 열은 **순위 / 행동 / 사용 조건**; 이유·예외는 필요할 때 `?` 상세 팁/인접 문맥. 장·표·요약 행 수는 전문화별 최적화.
5. **Gate E — 정보밀도/근거:** 원문의 임계값을 `적절할 때`로 치환하지 않고, 장황한 반복·조건 없는 주의 문장을 제거한다. 서로 다른 출처의 충돌을 임의로 합성하지 않는다.
6. **Gate F — 의미 QA와 기능 QA 분리:** 콘텐츠의 판단 가능성/원문 대조와, 실제 HTML의 7개 비대상 본문 byte parity/메뉴/영웅 특성/기술 아이콘·툴팁·`?`·`!`/모바일·JS를 **별도 증거**로 보고한다. 실제 로그·DPS 시뮬레이션을 안 했으면 최적화 완료를 주장하지 않는다.
7. **Gate G — 피드백 학습:** 피드백을 공통 작성 원칙·특정 기술 사실·UI 결함으로 분류하고 **원인이 발생한 단계**를 고친다. 반복 제작할수록 균일하거나 개선된 품질이 목표다.

**특히:** 생존 V3도 **사용자 승인 대기**이지 영구적인 게임 데이터 정답이 아니다. 새 시즌·패치는 최신 검증부터 다시 수행한다. 외부 공략의 장문 복제/대량 번역 저장 금지.

## 6. 재사용할 자산 및 보류/금지 영역

| 분류 | 대상 | 지침 |
|---|---|---|
| **REUSE** | 개인 V11의 7개 교본, 아이콘·툴팁·빠른 참고·우선순위/비교표·`?`/`!`, 실제 JS/CSS | 읽기/부분 수정/품질 비교. 비대상 본문 원형 보존 |
| **REUSE** | 생존 V3 검토 기록, `EDITORIAL_QUALITY_PROTOCOL`, 7전문화 품질 비교, [SOURCE_ACQUISITION](SOURCE_ACQUISITION.md) | 원문 추출·반례 QA 기준. 파일 없으면 V3 실제 내용이 있는 듯 재사용 금지 |
| **REUSE/CONNECT** | `engine/v2/parity.py`, `import_v11.py`, `patch_v11.py`, `fidelity.py`, `annotations.py`, 합성 테스트 | 개인 HTML 보호·바이트 동일성·툴팁/상태 기능 검사에 필요한 범위에서 사용 |
| **EXTEND** | 원래 V11 메뉴의 **직업→전문화→영웅 특성** 두 층 접기/펼치기, 자동 선택 열기, 모바일/키보드 | 사용자에게 승인된 UI 사용성 개선으로 유지; 개인 원본 바이트를 수정하지 않고 결과본에서 구현 |
| **REPLACE** | V2 생존의 `priority(action,reason)` 2열·불명확한 조건/오프너 | **규칙부터 재추출**하여 판단 가능 표로 수정; 재포맷만 해서는 안 됨 |
| **STOP** | 독립 AI API 인증·Sol/Luna 자동 라우팅·Codex/Codespaces/Actions 무인 모델 호출·별도 관리 웹앱 | 이번 Chat-first 사용자 목표의 선결 조건이 아님. 코드/PR은 보존만 |
| **FORBIDDEN** | 개인 원본/완성 HTML PUBLIC 업로드, 임의 주문 ID·특성 효과 추측, 승인 없이 정본 교체/Pages 배포/`main` merge, 사용자에게 추가 스크린샷 첨부 | 항상 금지 |

원본 수집·메타데이터 경로: [SOURCE_ACQUISITION](SOURCE_ACQUISITION.md), 구형 엔진/V11 보존 상세: [V11_RECOVERY](V11_RECOVERY.md), [V11_FIDELITY](V11_FIDELITY.md). 이들은 **현재 콘텐츠 품질 최상위 규격**을 대체하지 않는다.

## 7. 항목별 현 상태와 승인 게이트

| 항목 | 인계 기준 상태 | 근거/제약 |
|---|---|---|
| 기본 제품 방향 Chat-first | **결정·문서화 완료** | ADR-003, Playbook, User Instructions |
| V11 원본 7개 | **실물 접근·SHA 검증 완료** | 이번 인계 세션에서 실제 Library 파일 898,297바이트 검증 |
| V11 HTML 전체 자동 원형 보존 도구 | **기존 개발·검증 성과 재사용** | PR #14–#16 관련 코드/합성 테스트; 이번 인계에서 재실행하지 않음 |
| 생존 V1/V2 | **실패·비교 이력 보존** | 후속 제작 정본/재사용 초안 아님 |
| 생존 V3 | **당시 제작·브라우저 검증 기록 확인 / 파일 현 세션 미확보 / 사용자 승인 대기** | V3 기록·해시만 확보. 정본으로 승격 금지 |
| 직업/전문화 접기·펼치기 | **V3 당시 결과물 기능 테스트 기록 확인** | 신규 결과 HTML에서 재현되어야 함 |
| 편집 품질 7단계 게이트 | **문서화 완료, 전 전문화 반복 운영 미실증** | Editorial Quality Protocol |
| 전문화 이름만으로 매번 완성 HTML | **사용자 경험 목표 / 반복 검증 미실증** | 한 회의 생존 작성/개선 사례는 존재, 여러 전문화 독립 반복 검증 미완 |
| 실제 게임플레이 최적화·사용자 V3 최종 승인 | **미실증·승인 대기** | CI/HTML 기능 PASS로 대체 불가 |
| Plus OAuth/독립 엔진 | **보류(이력 보존)** | PR #17–#19 Draft |
| 공개 배포/정본 교체 | **승인 전 금지** | 공개 저장소에 개인 본문/완성 HTML 없음 |

**새 채팅 첫 응답 제한:** GitHub/파일 상태를 **읽기 전용**으로 독립 복원하고 위 항목의 실측/미확인 여부를 보고한다. 사용자가 `진행` 승인하기 전에는 집필, HTML/문서 수정, 커밋, Actions 재실행, 외부 공략 대량 수집, 배포를 하지 않는다.

## 8. 즉시 다음 작업 및 단기·장기 로드맵

**최신 우선 개발 과제(2026-11-11 후속 정책):** 개별 생존 교본 보완보다 **과거 성과의 범용화 → 평가 기준 검증 → 새 전문화에서 독립 전이 시험**을 우선한다. 생존 V3는 후속 채팅에서 실물을 회수·검증했고 V3.1 별도 검토본도 제작됐으나 **사용자 최종 정본 승인은 없다**. 이전 §3의 '이번 인계 세션 V3 미확보'는 그 당시의 역사적 관측이다.

**단기:** (1) 최신 정본 후보와 사용자의 다음 전문화/UPDATE 요청 파악 → (2) Editorial Gate A–G로 소스/조건/반례 분석 → (3) 기존 V11 표현 컴포넌트의 **최소 필수** 수정 → (4) 실제 개인 단일 HTML 제공 → (5) 사용자 검토 후 승인됐을 때만 정본 해시 승격.

**장기:** 전문화별 동일 수준 이상의 품질을 안정적으로 재현, 실제 사용자 피드백의 공통 실패 원인을 프로토콜/QA에 누적, 원본 V11 보존을 기계적으로 검증. 실제 품질과 사용자 편의 개선에 증거가 있을 때만 추가 자동화를 재검토한다.

## 9. 새 채팅의 독립 복원 순서

1. 이 문서를 GitHub 활성 브랜치 **최신 HEAD**에서 읽고 [QUALITY_FIRST_POLICY](QUALITY_FIRST_POLICY.md)의 확정 정책·검증 가설 구분을 우선 확인한다. 과거 SHA만으로 현재 파일이 있다고 단정하지 않는다.
2. [EDITORIAL_QUALITY_PROTOCOL](EDITORIAL_QUALITY_PROTOCOL.md) → [생존 V3 기록](CHAT_FIRST_RUN_SURVIVAL_V3_20261111.md) → [CHAT_FIRST_PLAYBOOK](CHAT_FIRST_PLAYBOOK.md) → [CHAT_FIRST_PROJECT_INSTRUCTIONS](CHAT_FIRST_PROJECT_INSTRUCTIONS.md) → [ADR-003](ADR_003_CHAT_FIRST_EDITORIAL.md) → [SOURCE_ACQUISITION](SOURCE_ACQUISITION.md) 순으로 읽는다. 필요한 경우 [V11_RECOVERY](V11_RECOVERY.md)/[V11_FIDELITY](V11_FIDELITY.md)/생존 최초 [기록](CHAT_FIRST_RUN_SURVIVAL_20261111.md)을 열람한다.
3. `main`, 개발 HEAD, Draft PR #20 및 핵심 CI의 최종 결론을 **읽기 전용**으로 검증한다. 합성 CI ≠ 실제 교본의 내용 QA.
4. 개인 원본 V11과 생존 V3를 Project/현재 채팅/Library에서 각각 검색해 **실물 존재·SHA·승인 여부를 분리** 보고한다. 공개 GitHub의 해시만으로 개인 파일을 복구한 척하지 않는다.
5. **읽기 전용 복원 보고만 작성**하고 `진행` 지시를 기다린다.

## 10. 과거 기록 보존과 보안

- 생성물·외부 공략 장문·저작권 원문·개인 코드/토큰은 공개 저장소에 보관하지 않는다.
- 인계는 V3 파일 자체를 공개하지 않으며, 요약된 연구/품질 교훈과 검증 메타데이터만 담는다.
- 문서 상호 참조만 갱신하고, 사용자 승인 없는 `main` 머지·PR Draft 해제·Pages 배포·실제 AI 인증 실험은 수행하지 않는다.
- 새로운 전문화를 실제 집필할 때는 이 인계 정본만으로 규칙을 만들지 말고 **현재 날짜에 일치하는 공략·특성·패치**부터 확인한다.

**이 인계 정본은 최신 사용자 승인 상태를 기록할 때 업데이트한다.** 다만 세부 제작 절차·소스 목록·품질 게이트를 여기로 복제하지 않고 각각의 기존 문서 정본을 참조한다.

## 11. 2026-11-11 후속 정책 결정과 증거 상태

- **확정:** 주 개발 대상은 개별 전문화 수정이 아니라 **재사용 가능한 고품질 교본 제작·검증 방법론**. 새 개발 항목은 실제 품질 기여 가설과 비교 증거가 있어야 한다.
- **확정:** 사용자 지정 공략 우선, 미지정 시 **Wowhead 단일 기본 원문**. 다른 사이트의 의무적 최소 비교 수는 폐지하고, 불확실한 쟁점만 필요시 보조 검증한다. 공식 변경 노트/주문 데이터 검증은 유지. 복수 사이트 로테이션 혼합 금지.
- **확정:** Q0~Q4 품질 판정을 제작 절차 및 HTML 기능 PASS와 분리. 고정 반례 6개·고정 표/장/출처 수로 품질을 판정하지 않는다.
- **확정:** 과거 V11 7개, 비전·생존 이력은 범용 **성공/실패/오탐 대조군**. 지식의 발견·후향적 검증과 새 전문화 전이·반복 실증을 구분한다.
- **잠정 연구:** 고양 주술사 초기 원문 탐색에서 출처 독립성·선택형 탭/오프너 구조 손실 가능성 관찰. [사례집 §9](QUALITY_GENERALIZATION_CASEBOOK.md) 참조. 완성 교본 QA 또는 방법론 실증 완료가 아님.
- **개인 파일:** 생존 V3는 후속 실행에서 실물을 확인했으며 V3.1 비공개 수정 검토본도 존재한다. 두 버전 모두 **정본 승격 미승인**. 원본 7개 V11 유지.
- **운영:** 개발/검증 도구는 필요한 범위로 제한. `main`·공개 Pages·개인 교본 원본은 사용자 별도 승인 없이 변경하지 않는다. 본 문서는 최신 HEAD 번호를 상수로 주장하지 않으며 항상 GitHub 조회가 우선이다.

- **확정(추가 지침):** 모든 발견마다 범용·일반화 가능성을 **항상 판단**한다. 일회성·특정 패치 문제인지, 기존 Wowhead→필요시 보조 공략 절차로 해결할 수 있는지, 여러 전문화에 반복되는 근본 원인인지 검토한다. **일반화가 불필요하다는 결론도 성공적인 판단**이며, 드문 단일 사례 때문에 별도 엔진·검증 구조를 추가하지 않는다. [사례집 §13](QUALITY_GENERALIZATION_CASEBOOK.md) 참고.

- **2026-11-11 실제 HTML CREATE 결과:** `wow_rotation_v11_enhancement_review_v1.html` 고양 주술사 검토본, **원본 V11 7개 raw byte 동일**, 8전문화 통합·신규 4표/43행·PC/모바일 인터랙션 PASS, SHA256 `ef65b8d36d265e1d0786a87f6030c9b7b75ac2c89042252f0b132cdff602c3b8`. 파일은 해당 개인 채팅에 전달됐으며 **사용자 승인 미완/공개 GitHub에 HTML 없음**. 자세한 검증·범용화 판정은 [실제 제작 기록](QUALITY_FIRST_REAL_HTML_RUN_ENHANCEMENT_20261111.md) 참조.

- **2026-11-11 고양 V2 실물 수정:** `wow_rotation_v11_enhancement_review_v2.html` SHA256 `b8938bd1402212fc57e01d9861ba07dbf192313e2ecc39af7ac15fb168e543e8`, 기존 7개 raw byte 동일, 4표/43행 유지. 사용자 V1 평가에 따른 조건·수치 중심 압축 및 V11 공통 서식·아이콘·기준선 정렬 정책은 [QUALITY_FIRST_POLICY](QUALITY_FIRST_POLICY.md)와 [EDITORIAL_QUALITY_PROTOCOL](EDITORIAL_QUALITY_PROTOCOL.md), 증거는 [사례집 §15](QUALITY_GENERALIZATION_CASEBOOK.md) 참조. V2 개인 채팅 전달, 최종 사용자 승인 전 검토본. 외부 CDN 로딩·실전 최적화 미검증.

- **고양 V2.1:** `wow_rotation_v11_enhancement_review_v2_1.html`, SHA256 `c06570fd49fd8cb527a7350cbe64e7c1d925bc9d50b62f2ccdfaa79c9e0b1f99`. 사용자 요청에 따라 M 정의와 필수 기초 메커니즘 보강. 원본 7개와 상세 우선순위 43행 문구 보존. [사례집 §16](QUALITY_GENERALIZATION_CASEBOOK.md) 및 정책 참고. 개인 채팅 전달, 사용자 최종 승인 대기.

- **징벌 성기사 V1 신규 검토본:** `wow_rotation_v11_retribution_review_v1.html`, SHA256 `c4fd209d7dcc185c784d971da8e476b17e5c6b906a93c0dcab412986006dc408`. 기존 7개 원시 바이트 동일, 4표/55행, 16종 아이콘 매핑, PC/모바일 오프라인 브라우저 QA 통과. 고양 V2.1의 범용 원칙을 적용한 개인 검토본. [사례집 §17](QUALITY_GENERALIZATION_CASEBOOK.md) 참고. 외부 이미지 로딩/실전 최적화 미검증, 사용자 최종 승인 대기. 공개 GitHub에 HTML 없음.

- **징벌 성기사 V2:** `wow_rotation_v11_retribution_review_v2.html`, SHA256 `6550e32232360fe409438cca1805a303a53a4a700999bd626805c6119463042b`. 사용자 피드백 4개 반영: 공통 직업/전문화 메뉴 축소, 순위와 순차 시전 구분, 실제 제목/내부 링크·구체적 A/B 예외, 의미별 목록. 기존 7개 본문 동일·55행/16종 매핑 유지, PC/모바일 오프라인 QA 통과. [사례집 §18](QUALITY_GENERALIZATION_CASEBOOK.md) 참조. 종료 직전 정확한 최적 초수·실전 최적화·외부 CDN 로딩 미검증. 정본 미승인, 비공개 전달.

- **확정(필수 원문 확보 게이트):** 모든 전문화의 실제 관련 마스터 스위치·하위 탭·빌드/단일·광역·오프너 선택·Further/Advanced·접이식·hover·대체 시퀀스/타임라인의 본문과 상태 귀속을 확인한다. 상위 선택 변경 뒤 하위 컨트롤 재탐색 필수. 핵심 미확인 분기가 남으면 완전 수집·최종 승인 주장 금지. [SOURCE_ACQUISITION](SOURCE_ACQUISITION.md) 정본과 [사례집 §20](QUALITY_GENERALIZATION_CASEBOOK.md) 근거. 이번에는 정책 반영 및 징벌·냉죽·암살의 원문 표현 대조만 수행; 다음 실제 교본에서 누락 감사와 제작 결과를 함께 검증한다.

- **고양 V3 부분 검토 후 확정(2026-11-11):** 영웅별 Notes 전부, 행별 `?` 호버 본문/행 귀속, 물약별 오프너/시점, 마스터 선택 이후 발생하는 하위 선택 및 접이식은 모든 전문화의 **필수 원문 확보 대상**. 하나라도 핵심 미확인이면 완전 수집·완성 교본 PASS 불가. [SOURCE_ACQUISITION](SOURCE_ACQUISITION.md) 및 [사례집 §21](QUALITY_GENERALIZATION_CASEBOOK.md). 부분 파일 `wow_rotation_v11_enhancement_review_v3_partial_audit.html`은 **부분 검토본**, 필수 게이트 미통과·정본 미승인. 개인 HTML은 공개하지 않음.

- **고양 V3 확대 검토본(2026-11-11)**: 개인 파일 `wow_rotation_v11_enhancement_v3_expanded_review.html`, SHA256 `287227572290dc90c13b0da220410280b9b7289e22594b97203d278b35a14eae`. 4표/43행·기존 7개 원문 바이트 보존·데스크톱/모바일 조작 PASS. Wowhead 검색 색인에서 확인한 Notes, 토림 자동 소비 전환, 쇄도하는 토템 효과, 물약별 일부 조건 보강. **실제 Wowhead 마스터 스위치·물약 탭·43행 ? 툴팁·타임라인은 미확인**이라 원문 확보 PASS 불가, 사용자 최종 승인 전. [선택 경로별 감사 현황](ENHANCEMENT_SOURCE_COVERAGE_V3_20261111.md), [사례집 §22](QUALITY_GENERALIZATION_CASEBOOK.md). 개인 HTML 공개 금지.

- **고양 V3.1 교정본(2026-11-11):** `wow_rotation_v11_enhancement_v3_1_source_corrections.html`, SHA256 `382bef6bd12eb03cef6519a85f9a05779e4f7e71834e58c4784cccf7b72c68fb`. 동일 Wowhead URL의 직접 열람 2026-07-26/패치 12.0.7 vs 검색 색인 2026-10-13/패치 12.1.5 충돌 발견. 최신 색인 근거로 토템술사 ST/AoE 전격의 불길 1순위 **화염 충격 미적용** 조건 2행 복원, 폭풍인도자 AoE 전투 -1초 낙뢰 복원, ST 폭풍의 일격 1회 명료화, Pre-Combat Checklist 보강. 43개 행·7개 원본 본문 보존, PC/모바일 오프라인 기능 PASS. 원문 동적 선택·실제 `?` 팁 모두 검증하지 못해 Gate A 미통과, 사용자 승인 대기. [상세 감사](ENHANCEMENT_SOURCE_COVERAGE_V3_20261111.md#v31-최신-색인-대조-및-원문-시점-충돌-감사-2026-11-11)·[사례집 §23](QUALITY_GENERALIZATION_CASEBOOK.md).

- **접근 장애 실측(2026-11-11):** GitHub Actions Chromium [접속 실험](https://github.com/degong2-code/wow-rotation-engine/actions/runs/42983699671)에서 Wowhead HTTP 403(본문 513자, 관련 컨트롤 0, `readable_page=false`). Actions 잡 PASS는 실행 성공이지 소스 접근 성공 아님. 무작정 재시도·접근 우회 대신 정상 사용자 로컬 브라우저 기반 단발성 자동 선택/호버 수집기와 로컬 JSON 사용자 전달이 다음 실행 후보. 기존 소스 완전성 PASS 아님. [상세 기록](ENHANCEMENT_SOURCE_COVERAGE_V3_20261111.md#github-서버-chromium-현장-접근-실험-2026-11-11).

- **실행 접근 변경(2026-11-11 사용자 피드백):** 로컬 브라우저 수집기를 바로 만들지 말고 Wowhead HTML의 숨김 요소·라이브 DOM·내장 JSON/스크립트·정상 네트워크 데이터를 **먼저** 조사한다. 같은 원문 텍스트 열람에서 여러 영웅의 조건·팁이 동시에 확인되는 반면 Notes 일부는 제목만 나옴. **구체적인 원본 DOM/JS 구조는 아직 직접 검사하지 못함**. 상태→행·툴팁 귀속을 구조로 검증한 뒤 마지막에 필요한 UI 클릭/호버만 수행; 사용자 PC 설치는 기본 경로 아님. [SOURCE_ACQUISITION](SOURCE_ACQUISITION.md), [사례집 §25](QUALITY_GENERALIZATION_CASEBOOK.md). 원문 확보 Gate A 미통과 유지.

- **고양 V3.2 교정(2026-11-11):** `wow_rotation_v11_enhancement_v3_2_source_audit.html`, SHA256 `7ab041145e16d4ba17912dd30e985c063d40734c02149ea9343db5cf6b7c023f`. **V3.1의 토템술사 ST/AoE 전격의 불길 1순위 화염 충격 미적용 조건은 구패치 12.0.7 내용을 12.1.5에 잘못 반영한 회귀**. 2026-10-13 Wowhead 최신 색인 및 시즌 2세트 Notes로 재검증하여 **사용 가능 시 1순위**로 복원. 43행/7개 원본 보존, 로컬 HTML PC/모바일 기능 PASS. 직접 raw HTML/DOM/JS 구조는 현재 소스 접근 불가(DNS·GitHub 403·연결된 브라우저 부재)로 미검증, `?` 팁 전수 확인 및 Gate A 미완. [원문 감사](ENHANCEMENT_SOURCE_COVERAGE_V3_20261111.md#v32-원문-버전-교차-검증--v31의-잘못된-조건-복원-2026-11-11)·[사례집 §26](QUALITY_GENERALIZATION_CASEBOOK.md). 개인 HTML GitHub 게시 금지.

- **Wowhead 마크업 구조 조사·고양 인벤토리(2026-11-11):** 공식 WHML 문서에서 `toggler`·`tabs`와 이름/ID를 통한 `tooltip` 참조 구조 확인. 사용자 주장대로 보이지 않는 콘텐츠도 원문 내 명시적 연결을 가질 수 있으나 **고양 12.1.5 원본 DOM의 실제 구현은 미확인**. 개인 V3.2에서 우선순위 43행(9/10/12/12)·자체 편집 `?` 4개를 분리 집계한 개인 `enhancement_v3_2_source_inventory.json` 생성(20,177 bytes, SHA256 `3ca144055f0582a55dc0b641169d4163a41dbaf9821ae68c705012b523466a7e`). Wowhead 행별 팁 귀속 입증 0건이므로 Gate A 미통과, 교본 수정 없음. [원문 정책](SOURCE_ACQUISITION.md), [사례집 §27](QUALITY_GENERALIZATION_CASEBOOK.md).

- **고양 V3.3 검토본(2026-11-11)**: `wow_rotation_v11_enhancement_v3_3_indexed_order_review.html`(1,061,215 bytes, SHA256 `9856320cf98145d4112e2dcd165b28ee6480eba247054ca667753cdecd2da406`). 개인 `enhancement_v3_3_indexed_order_audit.json`(25,075 bytes, SHA256 `859f5cc8be4fa724da6ce420baa927c654c770d60ca9aea2309986804ceeb1b8`). Wowhead 12.1.5 **검색 색인의 기술명·순위 43/43 일치**(9/10/12/12); V3.2의 '태고의 폭풍 마지막 번개는 150%' 오류를 원시 촉매의 별도 150% 반복 공격과 분리해 교정. PC/모바일/원본 7개 보존 PASS. **실제 DOM·호버·물약 선택 상태 미검증**이므로 Gate A 미통과, 교본/JSON 개인 채팅 제공만. [감사 기록](ENHANCEMENT_SOURCE_COVERAGE_V3_20261111.md#v33--1215-검색-색인-기반-43행-독립-순위-대조-및-150-설명-교정-2026-11-11), [사례집 §28](QUALITY_GENERALIZATION_CASEBOOK.md).

- **고양 V3.4 조건 개선 및 WHML 감사기 보강 (2026-11-11)**: `wow_rotation_v11_enhancement_v3_4_conditional_tip_review.html` (1,061,391 bytes; SHA256 `3af8b2c1305fb6776cb700671705de09e082c535e83c08ff3d7bdbf602442fc9`). Wowhead 12.1.5 토템술사 Notes(기본 10중첩, 5~9 용암 채찍 초기화/뜨거운 손 연장 예외)에 따라 ST/AoE 12순위의 조건 직접 보강. 기존 V11 7개 뷰/고양 43행 원시 보존, PC/모바일 오프라인 기능 PASS. 원본 HTML/선택지별 원문 `?` 귀속 미확인으로 Gate A 미통과. 개인 `wowhead_whml_inspector.py`가 공식 WHML의 **`tooltip2` 복수 참조를 누락**하던 문제 수정, 중복·선행 참조 포함 **8 테스트 PASS**. 이름 연결 ≠ 우선순위 행 귀속을 분리. [사례집 §30](QUALITY_GENERALIZATION_CASEBOOK.md)·[원문 정책](SOURCE_ACQUISITION.md). 검사기/테스트/교본 HTML은 GitHub 공개하지 않음.

- **고양 V3.5 네 조건 셀 보강(2026-11-11):** 개인 `wow_rotation_v11_enhancement_v3_5_priority_reasons_review.html` (1,061,657 bytes; SHA256 `3815635a3d0138dd30ca1bf30262906841ecf992a8b0d0992657ff079337f5b9`). 폭풍인도자 ST/AoE 1위 전격의 불길에 시즌 2세트 불타는 핵 사용 이유, 2위 낙뢰에 폭풍 해방 발동의 쿨 무시·강화 중첩 이유를 조건칸에 명시. **4행만 수정**, V11 7개 원본/고양 43순위 행·공통 JS 원시 보존. Chromium 로컬 PC/모바일 기능 PASS. 기준은 Wowhead 2026-10-13/12.1.5 검색 색인. **최신 원본 HTML/실제 `?` 행별 귀속 미검증 → Gate A 미통과**. [세부](ENHANCEMENT_SOURCE_COVERAGE_V3_20261111.md#v35--폭풍인도자-우선순위-4행의-사용-이유-직접-복원-2026-11-11)·[사례집 §31](QUALITY_GENERALIZATION_CASEBOOK.md). 개인 HTML 공개하지 않음.

- **고양 V3.6 조건 일관성 감사 (2026-11-11):** 부분 HTML `wow_rotation_v11_enhancement_v3_6_condition_consistency_review.html` (1,065,543 bytes, SHA256 `6103ac48a034a0e29f4a8e617b0816e0f5860d1b775aeff1f3a99c8de6bafb49`), 개인 43행 감사 JSON `enhancement_v3_6_condition_audit.json` (23,849 bytes). 43개 기술명/순위 일치, 색인상 상세 조건 직접 19행/노트·기본 규칙 조합 24행, 원문 `?` 실제 행 귀속 0. 토템술사 ST/AoE 9순위 M10 vs 12순위 M5+ 중복 설명 교정, 5~9 조기 소비가 상위 기술을 건너뛰는지 **판정 보류**로 표시. 10개 정상 상태 판독/2개 미해결, 개인 HTML에는 접이식 12상태 테스트. 기존 7개 노드·43행 보존, 로컬 Chromium PC/모바일 기능 PASS. **원문 Gate A 미통과, 사용자 승인 전.** [감사 기록](ENHANCEMENT_V36_CONDITION_AUDIT_20261111.md)·[사례집 §32](QUALITY_GENERALIZATION_CASEBOOK.md). 개인 파일 공개 금지.

- **고양 V3.7 조건 충돌 1건 보강(2026-11-11):** 개인 `wow_rotation_v11_enhancement_v3_7_proc_pooling_review.html`(1,066,498 bytes / SHA256 `eb6eff4fd9f3d2e66b12b46d6bc21bf36178b4ea6f370a8da84e9a9a79133069`). 폭풍인도자 AoE 10순위 M5+ 최하위 연쇄 번개에서 **폭풍 발동·M9이면 M10 폭풍을 우선 목표**라는 최신 Wowhead 12.1.5 원칙이 누락된 문제를 수정. 상태 검사 15개(13개 순위 일관, 2개 정확한 다음 GCD 보류). V11 7뷰/고양 43행 보존, PC/모바일 팝업·영웅 전환 PASS. 여전히 토템술사 M7 조기 소비와 Stormbringer M9 폭풍 발동 시 극단 상태의 정확한 다음 행동은 미확인. 원문 `?`/물약 탭 실제 귀속 Gate A 미통과. [감사](ENHANCEMENT_V37_PROC_POOLING_AUDIT_20261111.md), [사례집 §33](QUALITY_GENERALIZATION_CASEBOOK.md). 개인 HTML/JSON은 공개 GitHub 미게시, PR #20 Draft 유지.


## 2026-11-12 사용자 최신 확정 — 전체 원문 먼저, 툴팁 위치 단서, 의미적 귀속은 다음 단계

- **Gate A 원문 확보:** 전체 관련 영웅·전투·빌드/특성·물약별 오프너·쿨다운·Notes/Further/Advanced·타임라인·실제 존재하는 관련 `?`/hover의 **모든 본문**을 확보한다. 팁이 어느 영웅/전투 탭·섹션·표/행·인접 기술 옆에 있는지 **가능한 위치 단서**를 함께 기록한다. 모든 `?`의 정확한 DOM ID·대상 행 귀속 입증은 필수가 아니다.
- **Q0/Q1 의미 분석:** ChatGPT가 확보된 내용과 위치 단서로 기술·조건·우선권·예외를 연결한다. 적용 대상이 모호하거나 행동이 바뀌는 경우에 한해 해당 참조를 추가 확인한다. 본문 누락=Gate A FAIL, 본문 확보·중요 의미 미확정=Q0/Q1 REVIEW. 최종 교본 PASS는 핵심 불확실성이 없을 때만 가능.
- **제약 유지:** 패치 버전 혼합 금지, 배타적인 물약 오프너 합성 금지, `tooltip2` 등의 복수 설명 누락 금지, 장문 Wowhead 원문·개인 HTML의 PUBLIC GitHub 업로드 금지. [SOURCE_ACQUISITION](SOURCE_ACQUISITION.md) 및 [범용 사례집 §34](QUALITY_GENERALIZATION_CASEBOOK.md)를 최신 정책으로 적용한다.
- **현 상태:** 고양 12.1.5 검색 색인에서는 Notes와 4개 표를 상당 부분 확인했으나 모든 팁의 실제 내용과 물약별 완전한 오프너는 미확인이다. 따라서 아직 Gate A PASS나 V3.7 최종 승인 아님. 이 수정은 교본 HTML 변경을 수반하지 않는다.


## 2026-11-12 사용자 최신 교정 — 물약 종류가 아닌 오프너 순서·사용 슬롯을 기준으로

- **규칙:** 물약 종류는 사용자 선택·착용 장비에 따라 결정한다. 원문에 열거된 물약명은 원칙적으로 **사용 예시**로 취급한다. 오프너는 영웅 특성·단일/광역·실제 기술 순서를 바꾸는 조건으로 구성하고, 해당 자리에 중립적인 **`물약 사용`**을 넣는다.
- **불필요한 요구 폐기:** 물약 A/B/C별로 별도 전체 기술 시퀀스를 작성·전수 확인하는 것을 필수 수집 조건으로 삼지 않는다. 검색 색인의 3가지 물약 이름이 하나의 Opener 구간에 등장해도 **세 개의 독립 오프너를 뜻하지 않는다**. 실제 물약 효과가 기술 순서를 변경한다고 구체적으로 명시된 예외만 별도 검토한다.
- **현 고양 12.1.5 상태:** 여전히 영웅×ST/AoE 핵심 오프너의 독립 상태별 완전 확보와 실제 모든 관련 `?` 내용 확보가 미검증이며 Gate A는 미통과. 기존 V3.7 HTML이나 원래 V11 7개 교본을 이번 교정에서 수정하지 않았다. [SOURCE_ACQUISITION](SOURCE_ACQUISITION.md)과 [사례집 §35](QUALITY_GENERALIZATION_CASEBOOK.md)를 현재 정본으로 적용한다.


## 2026-11-12 고양 V3.8 — 원본 해시 검증 후 물약 사용 슬롯 수정

- V3.8 개인 검토본: `wow_rotation_v11_enhancement_v3_8_potion_timing_review.html` · 1,067,296 bytes · SHA256 `0fd338a8af37342c7190562c10d2623c6fb1ca986d8d13b4b351f71328e013f3`. V3.7 실제 원본(1,066,498 bytes / SHA256 `eb6eff4fd9f3d2e66b12b46d6bc21bf36178b4ea6f370a8da84e9a9a79133069`)을 복구해 **해시가 정확히 일치함**을 확인한 뒤 관련 부분만 수정.
- **수정 범위:** 고양의 네 영웅×ST/AoE 오프너에 `물약 사용` 단계 표기, Quick Reference 오프너에 동일 슬롯 표시, ‘3.3 물약별 비교표’ 제거 후 사용자 선택·타이밍 원칙 설명, 근거 미확정 ‘물약 분기에 따른 추가 낙뢰’ 문구 제거. **물약 종류는 장비·사용자 선택이며 영웅/단일·광역의 별도 로테이션 분기 기준이 아님**. 일반 시작 전 사용과 사전 예열형처럼 효과별 시점 차이는 구별하고 임의의 초수를 모든 물약에 적용하지 않음.
- **콘텐츠 보존:** 기존 V11 7개 `manual-view` HTML 파싱 결과 원문과 완전 일치. 고양 4개 우선순위표 **9/10/12/12=43행** 유지. 고양 외 HTML·공통 JS/CSS 바이트 미변경. 고양의 실제 기술 사용 순서 변경 없이 물약 슬롯 추가·광역 선시전 낙뢰 설명을 오프너 목록 내부로 이동.
- **기능 QA:** 로컬 Chromium `page.set_content` 방식으로 데스크톱 **1365×850**·모바일 **390×844**에서 영웅 토글/오프너 2개씩/기술 팝업·ESC/문서 가로 넘침 없음/JS 예외 0 PASS. Wowhead의 실제 탭·툴팁·외부 CDN 이미지를 시험한 것이 아님.
- **콘텐츠 QA/승인:** 최근 Wowhead 검색 색인에서는 해당 패치 오프너의 물약명이 여러 선택지로 평면화되는 점을 관측. **새 시점 표기는 일반화된 슬롯이며, 각 물약의 개별 지속/예열 시간을 보장하는 규칙이 아님.** 원문 모든 팁·선택형 UI 확보 **Gate A 미통과**, 고양의 미해결 2개 다음 행동 Q0/Q1 REVIEW, **V3.8은 최종 사용자 승인 전**. 개인 HTML과 장문 원문은 PUBLIC repo 미게시.


## 2026-11-12 추가 인계 — 고양 V3.9, 최신 색인 주변 설명 활용

- **개인 V3.9:** `wow_rotation_v11_enhancement_v3_9_tooltip_context_review.html` 1,067,634 bytes · SHA256 `1b98ac9aa7bc228d76307118f6c371c9ed630f3a0fd818f71aa135179cfff66e`. V3.8 기반 폭풍인도자 단일·광역 오프너의 첫 폭풍의 일격을 **선택적 1회**로 정정(요약·상세·고급 문맥에 연쇄 반영). 최신 Wowhead 2026-10-13/12.1.5 검색 색인의 오프너 부근 추가 설명 근거. GitHub에는 개인 HTML/원문 장문 미게시.
- **추가 수집:** 최신 한국어 검색 색인에서 4개 Priority 주변 설명 및 오프너의 Sample Timeline 주변 설명을 확인. 관련 `?` 위젯의 실제 개수·모든 본문·화면 위치는 여전히 미확인. **일부 내용 복구는 Gate A PASS가 아님.** [고양 확보 기록](ENHANCEMENT_SOURCE_COVERAGE_V3_20261111.md), [사례집 §36](QUALITY_GENERALIZATION_CASEBOOK.md).
- **QA:** 기존 7개 전문화 본문 동일, 고양 43행/4오프너 유지, Chromium PC/모바일 영웅 전환·팝업/ESC·넘침·JS 예외 없음. 고양 M7·M9 판단 보류 유지. PR #20 Draft 유지, 최종 사용자 승인 전.


## 2026-11-12 추가 인계 — V3.10 설명 1건 보강 및 27개 의미 대조

- **개인 V3.10:** `wow_rotation_v11_enhancement_v3_10_crash_lightning_proc_context_review.html` · 1,067,897 bytes · SHA256 `537be20cc9109aa9103c9babefc565137d336e50473c138059f5174e056655b1`. V3.9에서 고양 고급 운용의 낙뢰 초기화 문장 1곳 보강. 사용 가능하면 즉시 재사용하되 ‘불꽃 회오리 발동에 따른 완전 초기화 가능성’과 시즌 세트의 부분적 쿨다운 감소를 구별. 실제 아이콘 위치·정확한 기전 조건 미확인이라고 명시.
- **선별 감사:** 개인 `enhancement_v310_source_meaning_coverage_audit.json` · 13,005 bytes · SHA256 `1a6cee20d44fb46204520da38a15403e82e35340cf53909e7e2a42f3db2e6970`. 최신 2026-10-13 Wowhead 검색 색인 부근의 주요 의미 27개를 대조(22개 기존 반영/보강, 2개 부분, 3개 의미 검증 필요). **원문 전체 `?` 트리거 27개를 발견했다는 뜻이 아님**.
- **검증:** 기존 V11 7개 본문 동일, 고양 4표/43행 유지. Chromium PC·모바일 영웅 전환, 팝업/ESC, overflow 없음, JS 오류 0. Gate A FAIL, Q0/Q1 일부 REVIEW, 승인 전 검토본. 기존 실제 Wowhead DOM 접근 불가와 패치 버전 충돌(12.0.7 vs 12.1.5)은 그대로 유효. [상세 감사](ENHANCEMENT_SOURCE_COVERAGE_V3_20261111.md), [사례집 §37](QUALITY_GENERALIZATION_CASEBOOK.md).


## 2026-11-12 범용 원문 확보 감사기 — 특정 전문화 코드 없이 재사용

- **목표:** 고양 V3.10 같은 단발 수정 대신, 사용자가 전문화명만 입력하는 ChatGPT-first 제작에서 모든 전문화의 **동적 선택→하위 선택·접힘·툴팁 내용** 누락을 같은 방식으로 점검한다. 크롤러나 자동 집필 엔진이 아니라 **선택적 내부 감사 보조**다.
- **구현:** `engine/source_coverage.py`, `tests/test_source_coverage.py`, `examples/synthetic-source-coverage.json`, `docs/SOURCE_COVERAGE_AUDIT.md`. 합성 테스트에서 중첩 선택, 새 하위 선택, 물약 예시의 카르테시안 과잉 분기 방지, 툴팁 본문/위치 분리, 동일 URL의 패치 충돌, 본문 누락, 오탐 방어를 검증한다.
- **분리:** 결과의 `declared_coverage_candidate`는 **입력에 선언된 요소에만** 적용한다. 실제 웹페이지 전체에 대해 발견하지 못한 `?`가 없다는 증명은 아님. `real_site_completeness_verified=false`, `gameplay_meaning_verified=false`, `automatic_publish_allowed=false` 유지. 기존 V11 HTML과 최신 고양 V3.10 개인 교본은 변경하지 않았으며 PUBLIC에 올리지 않음.
- **다음 초점:** 실제 접근 가능한 새로운 전문화에서 원문 내용/선택을 수집할 때 이 공통 감사로 누락을 줄이는지 비교 검증. 브라우저/네트워크 접근 문제는 이 모듈만으로 해결되지 않는다.


## 2026-11-12 범용 HTML 내부 구조 탐색 보강

- `engine/source_structure.py`는 실제 접근 가능한 정적 HTML의 숨김/접힌 영역, 다중 탭, 폼 선택, `?` 팁 본문 또는 참조 후보 및 위치 단서를 수집한다. `engine/embedded_markup.py`는 `WH.markup.printHtml`의 JSON 문자열 리터럴에 담긴 WHML의 `tooltip`·`tooltip2`·`tabs`·`toggler`를 식별한다. **최신 고양 원문을 전수 수집했다는 뜻은 아니다.**
- 실제 역사적 공개 분노 전사 HTML fixture에서 `printHtml` 호출 2개(사이드바 동적 데이터 1개, `guide-body` 14,037자 본문 리터럴 1개)를 확인해 접근 경로를 실증. 동적 JS 실행·우회·네트워크 다운로드 없음.
- 합성 기반 테스트 및 GitHub CI 통합. 공개 저장소에는 실제 가이드 HTML/원문/개인 V11 파일을 올리지 않는다. 실제 페이지의 숨김/동적 선택지 전수 여부와 콘텐츠 Q0/Q1은 별도 판단.


## 2026-11-12 범용 HTML 구조 후보와 수집 기록 대조기 추가

- **배경:** `source_structure`는 숨김 패널·`?` 후보를 찾아도 실제 문장을 읽었다는 기록과 연결되지 않아 수집 누락을 한눈에 알기 어려웠다. `engine/source_reconcile.py`가 구조 후보와 `source_coverage`의 수집 기록을 연결해 `unmapped_candidates`, `static_body_unresolved_ids`, `invalid_mappings`를 보고하도록 함. 자료가 없거나 의미가 미확정일 때 자동 PASS 금지.
- **범용성:** 특정 전문화/기술 고정 없음. `tooltip2` 같은 다중 팁 독립 검사, 숨김 설명 DOM과 트리거의 중복 방지, 정확한 본문 해시 일치만 자동 연결, 접근 패치 충돌·수집 내용 누락을 별도 유지. 위치 ID는 HTML 스냅샷 내부 전용이고, 의미상 귀속은 ChatGPT가 검토.
- **보안/승인:** 개인 HTML·Wowhead 장문 원문은 PUBLIC 미게시. `real_site_completeness_verified=false`, `gameplay_meaning_verified=false`, `automatic_publish_allowed=false` 유지. 실사이트 원본 접근 장애나 최신 고양의 Gate A FAIL을 해결했다고 주장하지 않음. [공통 감사 기준](SOURCE_COVERAGE_AUDIT.md).

## 2026-11-12 후속 — 범용 출처 지문·다전문화 구조 검증

- `engine/source_structure.py` 결과에 `source_sha256` 추가. `engine/source_reconcile.py`는 수집 기록의 `html_sha256` 및 URL·패치·수정본 일치가 없으면 후보 연결을 유효한 증거로 인정하지 않음. `search_index`는 HTML 지문의 증명이 되지 않는다. **이 일치 자체는 실사이트 최신성·전수성 증명이 아님.**
- 구조 보고서에서 섹션·컨트롤·옵션의 원문 문구를 DOM 위치/해시로 대체하여 PUBLIC 출력에 장문 원문이 실리지 않도록 함. 실제 의미 분석에는 비공개 원문 문맥 활용.
- [CROSS_SPEC_SOURCE_VALIDATION_20261112](CROSS_SPEC_SOURCE_VALIDATION_20261112.md): 최신 2026-10-13 검색 색인에서 냉기 마법사(영웅별 우선순위), 생존 사냥꾼(추가 선택), 징벌 성기사(단일/광역 오프너 전환) 패턴 확인. 이 UI 패턴을 본뜬 **합성 테스트 8개** 추가. 전수 원문을 확보했다고 주장하지 않음. 냉기 마법사는 색인 2026-10-13 vs 직접 열람 2026-04-20/12.0.7 충돌을 확인.
- CI Push·PR에서 **전체 오프라인 254개 테스트 PASS**(커밋 `1d4a25bb835b3a3269a11a0e5857cde4496731c1`). 고양 V3.10 및 V11 비공개 HTML 변경 없음. 다음 과제는 실제 최신 HTML/렌더링 상태의 합법적·안정적 접근 후 공통 수집 검증 적용.

## 2026-11-12 범용 실제 HTML 스모크: 탭 2그룹·본문 6개

- 고정된 공개 과거 Wowhead HTML 2개를 실제 GitHub CI 중 임시 수집 후 `source_structure`로 처리. `guide_283`는 탭 2그룹/6개 하위 본문, `guide_3087`는 0그룹인 것을 구분. **실제 HTML을 코드로 처리했음**을 검증했지만 최신 공략을 직접 수집한 것은 아님.
- 새로운 `embedded_markup._tab_groups`는 각 하위 탭의 본문 해시·길이·닫힘 여부를 별도 추적하고 `source_reconcile`는 미확보 탭을 독립 후보로 표시. 과거와 동일한 WHML 형식이 아니어도 된다는 범용 탐색 원칙 유지.
- [성공한 Push CI](https://github.com/degong2-code/wow-rotation-engine/actions/runs/43152516953): 전체 257개 오프라인 테스트 + 공개 과거 HTML 스모크 성공. 프라이빗 V11·고양 V3.10 HTML 무변경, 공개 원문/개인 HTML 저장 금지 유지.
- 남은 병목: 실제 최신 Wowhead HTML 및 렌더링 후 생성되는 동적 선택지·모든 `?` 본문을 확보하는 접근 경로. [공통 취득 감사](SOURCE_COVERAGE_AUDIT.md) 참고.

## 2026-11-12 동적 DOM 수집 어댑터 추가

- `engine/live_dom_capture.py`, 가상 동적 UI fixture, 브라우저 회귀 테스트, 전용 Playwright CI 추가. 실제 Chromium에서 영웅 전환→하위 ST/AoE·다른 영웅 선택형·접이식·`?`의 관련 본문을 관측.
- private 원문 JSON과 공개용 감사 JSON을 분리하고 query/fragment 및 파일 경로 노출 차단. 경로 깊이·상태 상한으로 미완료 시 남은 탐색 수 표시. 게임 로직 의미 분석이나 원문 Gate A 자동 PASS 금지.
- Push/PR 브라우저 테스트 및 기존 전체 오프라인 CI 성공. 고양 12.1.5 Wowhead 서버 HTTP 403 및 현재 원문 패치 불일치는 그대로 미해결. PRIVATE V11 7개 및 고양 V3.10 HTML 무변경.
- 운영 규격: [LIVE_DOM_CAPTURE](LIVE_DOM_CAPTURE.md). 최종 목표는 사용자에게 JSON/로컬 설치를 요구하지 않는 ChatGPT-first 단일 HTML 제작.

## 2026-11-12 동적 관측↔공통 누락 감사 통합

- `engine/live_dom_capture.py`에 안정적 ID 우선 선택 재현·ID 없는 `?`의 DOM 경로 hover·관측된 미호버 팁 수·깊이 제한·대기 경로 기록을 추가했다. CSS 클래스/스킬 이름에 종속되지 않으며, 화면에서 표시되는 실제 본문과 hover 생성 설명을 구분한다.
- `engine/live_dom_bridge.py` 및 합성 테스트는 비공개 브라우저 캡처를 `source_coverage`용 검토 초안으로 변환한다. 원문 설명은 개인 기록에만, 공개 보고서는 검사 항목 수와 누락 종류만 포함한다. 경로 식별자는 **사용자 게임플레이 선택 분기로 승격하지 않는다**.
- 브라우저 캡처에 원문 전수 확보를 자동 보장하는 인증은 없음. 선택 상태가 탐지되지 않았거나 페이지가 제한적으로 보이면 여전히 누락 가능. 특히 실제 최신 고양 Wowhead는 동일 URL 버전 충돌·선행 403 때문에 **Gate A 미통과**다.
- 코드·검증 기준: [LIVE_DOM_CAPTURE](LIVE_DOM_CAPTURE.md), [SOURCE_COVERAGE_AUDIT](SOURCE_COVERAGE_AUDIT.md). 개인 V11 7개·고양 V3.10 HTML 미수정, PR #20 Draft 유지.


## 2026-11-12 현재 최신 인계 — 사용자 제공 Wowhead 실제 저장본·고양 V3.11

- 사용자가 최신 고양 Wowhead 12.1.5(Updated 2026/10/13)의 실제 페이지를 열어 영웅/단일·광역/오프너/`?` 작동을 확인하고 6MB ZIP 전달. **이전 최신 HTML 접근 실패·툴팁 미확보 판단은 이 저장본 범위에서 해소**. 내부 WHML 68,350자, tooltip 정의 44개/참조 45회/미정의 0개, 16개 선택 정의/82개 조건부 표시/7개 접힘 확보. 사적 ZIP/원문은 공개 저장소에 넣지 않음.
- **정정된 범용 원칙:** 물약 종류를 무조건 단순 예시 처리하지 않음. 실제 `display-options`가 오프너 시전 시간/순서/기술을 바꾸는지 보고 결정 축 여부 판단. 고양의 영웅×ST/AoE×3물약 = **12개 실질 조합**이며 폭풍인도자 AoE에서 Recklessness와 나머지 2개 사이 **낙뢰 선시전 여부도 달라짐**. 다른 전문화에서 동일하다고 단정하지 않음.
- **고양 V3.11 개인 HTML:** `wow_rotation_v11_enhancement_v3_11_verified_potion_branches_review.html`, 1,112,664 bytes, SHA256 `b14d47ca44ed015132f1a355db77353c4e95d6450fbc31207bc293c5450159f2`. 기존 7개 V11 본문 완전 동일, 고양 4표·43행 동일. 4오프너×3 native details 조합; Chromium PC·모바일 영웅 전환·물약 펼침/상호 배타적 선택·가로 넘침 0·JS 오류 0.
- **보류:** 원본에는 광역용 tooltip `SBAOE-O-Pot`이 존재하지만 실제 광역 UI는 `SBST-O-Pot`을 참조하는 능력치 팁 혼선이 있으며 상태→다음 GCD 2건은 독립 gameplay Q0/Q1 검증이 필요. V3.11은 미승인 검토본. 실제 브라우저 동적 실행 자체를 모델이 다시 수행했다고 주장하지 않음. [검증 근거](ENHANCEMENT_SAVED_HTML_EVIDENCE_20261112.md), [범용 사례 §38](QUALITY_GENERALIZATION_CASEBOOK.md).
