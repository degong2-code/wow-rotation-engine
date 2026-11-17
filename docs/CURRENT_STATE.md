# ROTATION TEXTBOOK — 현재 제품/검증/다음 작업

> **단일 rolling 상태 정본 · 2026-11-17 KST.** 여기에 과거 버전별 긴 작업 기록을 덧붙이지 않는다. 이전 **111KB 원문은 [2026-11-17 정비 직전 Git 이력](https://github.com/degong2-code/wow-rotation-engine/blob/e3416fc9643f2108187648c356d776115e5cda82/docs/CURRENT_STATE.md)**에 전체 보존되어 있다. 이전 사례 상세는 [사례집](QUALITY_GENERALIZATION_CASEBOOK.md)·[기존 인계 이력](HANDOFF_CHAT_FIRST_CURRENT.md)에서 필요 시 조회.

## 1. 최종 제품과 GitHub

- 목표: ChatGPT 일반 채팅에서 전문화명 입력 → 최신 실제 원문 Gate A 확보 → 상태/조건/행동/예외 분석 → V11 이상 한국어 **단일 HTML** CREATE/UPDATE. **독립 AI API·거대 JSON·검사기 증식이 최종 목표가 아니다.**
- 저장소: `degong2-code/wow-rotation-engine` (공개). 활성 작업 브랜치 `work/chat-first-talent-visibility-spell-media-20261114`, **PR [#24](https://github.com/degong2-code/wow-rotation-engine/pull/24) Draft·미병합**, base `work/chat-first-generic-html-assembly-20261113` (main 직접 대상 아님).
- **HEAD/CI는 이 문서보다 실제 GitHub 조회가 우선.** 인계 문서에 옛 SHA/CI를 현재인 것처럼 다시 붙이지 않는다. 승인 없이 PR ready/merge·main 수정·공개 배포 금지.

## 2. 실제 개인 제품 — V83 게임 내용 유지, V88 UI 시범

| 역할 | 파일 / 개인 Library 식별 | 실제 크기 / SHA-256 | 승인 |
|---|---|---|---|
| **악마 흑마법사 12.1.5 독립 v2 Q0 교정 (15번째 후보)** | `/ROTATION TEXTBOOK/wow_rotation_demonology_1215_independent_q0correction_v2_REVIEW.html` · `libfile_67b931dcec788191b14fd930c86d52aa` | **104,859B** · `be9be38131e53996d1c852eb3df1339b9ea1ae1bd6d2ea2fc00a859d59007f5e` | **Gate A·Q0/Q1·Q3 REVIEW**. v1 원고 계열 교정이며 V88 통합 14개 불변 |
| **V88 통합 UI 검토본 — 분노 표 음영 제거** | `/ROTATION TEXTBOOK/wow_rotation_v83_fury_editorial_v88_no_cell_shading_REVIEW.html` · `libfile_1c87d86e0b048191a7ee46bc6b093fc1` | **2,629,547B** · `1c817f1f8896b111f18be367fe879aa09214e6ecd4e450afa399a6443efbd236` | **Q3: 사용자 더 깔끔하다고 평가**, 전 제품/게임 최종 승인과 별개 |
| **UI 브리지 v3 CSS (비공개 공통 자산)** | `/ROTATION TEXTBOOK/rotation_shared_ui_bridge_v3.css` · `libfile_58a5fa44280881919ba7b90470d4dc3a` | **3,187B** · `5bd71813a185cf4facd6bde4ca9b88bc73f73d0091401862507f968c89c6ec64` | 공통 기술·조건·표/버튼 시각 담당. 기존 분노 CSS는 전용 구조·영웅·반응형 담당 |
| **최신 통합 V83 (14개 전문화)** | `/ROTATION TEXTBOOK/wow_rotation_v11_partial_design_v83_REVIEW.html` · `libfile_098b2ad2528081919d0608ba39b185d4` | **2,611,792B** · `14be1b44db12cea04ca56a1655a97a3dcc921dab697070e97f5935901c2419ed` | **REVIEW** |
| **원본 V11 UX 비교 기준(7개)** | `wow_rotation_manual_engine_v2.html` · `libfile_047243e589bc8191b348398ec923c910` | **898,297B** · `5d70279c4dd073eccef1f3b13565a8f555cd81c9f0a5b7eda7e3485e410742be` | 역사적 비교 기준. 현재 패치 정답 아님 |
| 고통 흑마법사 독립 UX 비교 | `/ROTATION TEXTBOOK/wow_rotation_affliction_decision_sync_v82_REVIEW.html` · `libfile_cf7ca2a7c1ac819192442028ac1b3c87` | **148,608B** · `a46a18a6209545fb4da9f4be9a94df1de002e9301be6e4cf146a2472d8b123c8` | 첫 화면 가독성 사용자 호평. 게임 전체 정확성·전역 디자인 승인 아님 |

- V83 14개: 화염·냉기·비전 마법사 / 냉기 죽음의 기사 / 사격·야수 사냥꾼 / 잠행·암살 도적 / 조화 드루이드 / 고양 주술사 / 징벌 성기사 / 분노 전사 / 파괴·고통 흑마법사.
- V83은 비전·파괴 배경 통일, 파괴 기술명 **흰색·굵게·기본 밑줄 없음** 시범. 기존 14개 전문화 본문/JS는 V82 대비 보존, 통합 CSS 1개 블록만 변경. **V83 사용자 Q2/Q3 최종 평가는 아직 REVIEW**. 금색/핫핑크/전체 타이포·행간 의미체계 확정되지 않음.
- **개인 파일을 사용하기 전에 현재 세션에서 실물 크기/SHA와 접근을 다시 검증.** 이 표는 기록 당시 실증이지 새 채팅의 실물 접근을 대신하지 않는다. 비공개 HTML/저장된 와우헤드 원문은 공개 GitHub 업로드 금지.

## 3. 현재 품질/승인 경계

| 구분 | 현재 판단 |
|---|---|
| **Gate A** | 기준 패치·영웅·선택형/숨김·hover·오프너의 **전체 확보는 REVIEW** |
| **Q0/Q1** | 모든 기술명·수치·조건·우선순위·실제 다음 선택을 전수 승인하지 않음 (**REVIEW**) |
| **Q2/Q3** | **V85 밑줄 축소, V87 정보 재배치, V88 분노 첫 화면의 표 셀 음영 제거** 사용자 선호 확인. 다른 전문화의 시각 일관성, 게임 이해도 및 통합본 전체 승인은 REVIEW |
| **Q4** | V88↔V87: **14개 본문·기존 22개 스크립트 완전 동일**, 31개 스타일 중 **분노 전용 CSS 1블록만 99B 증가**. 320·390·850·1365px×학살자/산왕 **8상태**의 44개 표 머리글·셀 배경 투명, JS 오류/가로 넘침 0. 실제 `file://` 접근은 실행 환경에서 차단, CDN 이미지 응답 REVIEW |
| **GitHub CI** | 2026-11-17 이전 커밋 검사 성공 기록 있음. **최신 HEAD CI는 매번 다시 조회** |

- 특정 근거 보류: 파괴 광역 3명/5명 조건 귀속, 비전 일부 심화 Tips 중첩 조건, 동적 원문/공식 아이콘 신원. 근거가 없으면 그 범위만 REVIEW, 임의 보완하지 않는다.
- **V88 사용자 디자인 결정·실물 검증(2026-11-17):** V87의 영웅 선택→우선순위→오프너→핵심 원칙 배치를 유지하고 분노의 빠른 우선순위/오프너 표 `th/td` **음영만 투명화**. 사용자는 **'더 깔끔해졌다, 구분이 부족하면 나중에 조정'**이라고 평가. V87 대비 14개 원본 `.manual-view` 전체·스크립트 22개 동일, 오직 `fury-v58-scoped-style` 한 블록 99바이트 변경. 별도 HTML 파일 Library 저장·SHA 검증. 사용성 선호만 채택, Gate A/Q0/Q1 및 V88 전역 Q3 최종 승인 아님. [상세 V87 검증 당시 기록](https://github.com/degong2-code/wow-rotation-engine/blob/fefc53245a1d22a866322159e887c764ec84dd8b/docs/CURRENT_STATE.md).
- **악마 흑마법사 v2 Q0 근거 교정(2026-11-18):** Wowhead NotWarlock 12.1.5(2026-10-13) 동일 기준 원문 재조회. 동적 스위치 없이도 원문 텍스트에 우선순위 4목록×8행과 오프너 2목록이 노출되지만 선택 버튼의 원본 DOM·오프너 단일/광역 분기·관련 hover 전수/행 귀속은 미확보(Gate A REVIEW). 원문 `Power Siphon / Implosion`을 v1이 **'선택 특성 중 하나'**라 임의 단정한 오류를 찾아 **원문 병렬 표기·선택 조건 미확인**으로 변경하고, `Ruination`·`Infernal Bolt`의 미확정 발동/전환 조건도 REVIEW로 명시. 공식 한국어 주문 페이지로 마력 착취=날뛰는 임프 최대 2마리 희생/악마의 핵 2회 충전, 파열=15초 쿨/최대 6임프 소비 확인. 기준 공략의 `Grimoire: Fel Ravager` 차단 설명과 현행 주문 페이지의 정화·마법 삼키기 설명 충돌을 별도 노출, **차단 기술로 확정하지 않음**. 원문 말미에 위치가 분리된 두 설명(조각 과충전 방지/악마 화살로 파멸 확산)을 확보하되 원래 행 귀속 미확정. v1 대비 **32개 상세 우선순위 행, 23개 오프너 행동 문장, 132개 이미지 URL, CSS·JS 원문 보존**. Chromium 외부 이미지 차단 **6폭(320/390/650/850/1180/1365)×2영웅=12상태**에서 가로 넘침·JS 오류·영웅 전환·목차·Enter/ESC 툴팁 범위 PASS. 실제 CDN, file://, 원문 완전성, 전체 게임 판단 및 사용자 Q3는 REVIEW. 정상 컨테이너 직접 HTTP는 DNS 실패, 브라우저 세션 연결 불가; 우회 없이 공개 텍스트+주문 페이지 범위에서 교정. 개인 v2 Library 저장본 크기/SHA 실재 대조; v1/V88 유지. **완료 CREATE 성공으로 중복 집계 금지**.
- **반복 제작 실패 원인:** 냉기 v1은 독립 CSS/2열 과밀로 이미 존재하던 V11 표현 규칙을 미적용, v2는 폭/열만 교정하여 고통의 표·섹션·메뉴·서식 위계를 실제 재사용하지 못했다. **Q4 통과를 Q3 만족으로 오판**. 다른 전문화도 동일한 실물 비교 없이 성공이라고 표기하지 않는다.
- UI 기준은 **사용자 평가를 통해 확정할 공통 실행 자산**이 목표. 콘텐츠는 최신 원문에서 독립 해석하고, UI는 재사용 가능한 검증된 셸/구성요소를 직접 재사용. 추가 문장만으로 재발을 막았다고 주장하지 않는다. 실행 계약: [CHAT_FIRST_PLAYBOOK](CHAT_FIRST_PLAYBOOK.md).

## 4. 다음 실제 제품 작업 (우선순위)

1. **악마 흑마법사 Gate A 미확보 동적 선택 확인:** 영웅 마스터·오프너 단일/광역·?·hover 원본을 동일 12.1.5 페이지의 정상 DOM 또는 사용자 저장 HTML로 확보. 원문 텍스트에 이미 있는 두 분리 설명의 원래 적용 위치도 필요 시 확인. 403/접속 오류 우회·추측 보충 금지.
2. **악마 독립 v2 게임 판단·Q3 검증:** `/` 병렬 행동의 실제 선택 조건과 영웅 전환·오프너를 정확히 귀속한 뒤 첫 화면·상세 역방향 재검토. 실제 기술 아이콘이 표시된 PC/모바일 화면을 고통·냉기·분노와 동폭 비교하고 사용자 가독성 검토. Gate A/Q0/Q1 미완료를 Q4 PASS로 대체하지 않음.
3. **다음 독립 CREATE 및 통합 반복성:** 다른 새 전문화로 동일 절차 적용, 사용자 승인 후에만 통합 V88의 기존 14개 본문/JS 보존 검증을 포함하여 UPDATE; 새 정책/도구/인계 장문 누적 금지.

## 5. 복원/유지 원칙

- 새 채팅: **PROJECT_CANON → QUALITY_FIRST_POLICY §0/§0.1/§5.1 → CURRENT_STATE → CHAT_FIRST_PLAYBOOK** (필요할 때만 나머지).
- 완료: 변경 대상·결과물 Library 실물·SHA, 게이트별 PASS/REVIEW, 다음 1~3개로 **이 문서의 해당 칸을 교체**한다. 과거 날짜별 장문 로그를 덧붙이지 않는다.
- **기존 이력 삭제 아님:** [정비 직전 CURRENT_STATE 전체](https://github.com/degong2-code/wow-rotation-engine/blob/e3416fc9643f2108187648c356d776115e5cda82/docs/CURRENT_STATE.md) 및 [버전별 Git History](https://github.com/degong2-code/wow-rotation-engine/commits/work/chat-first-talent-visibility-spell-media-20261114/docs/CURRENT_STATE.md) 사용.
