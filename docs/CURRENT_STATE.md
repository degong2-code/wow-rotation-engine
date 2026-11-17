# ROTATION TEXTBOOK — 현재 제품/검증/다음 작업

> **단일 rolling 상태 정본 · 2026-11-17 KST.** 여기에 과거 버전별 긴 작업 기록을 덧붙이지 않는다. 이전 **111KB 원문은 [2026-11-17 정비 직전 Git 이력](https://github.com/degong2-code/wow-rotation-engine/blob/e3416fc9643f2108187648c356d776115e5cda82/docs/CURRENT_STATE.md)**에 전체 보존되어 있다. 이전 사례 상세는 [사례집](QUALITY_GENERALIZATION_CASEBOOK.md)·[기존 인계 이력](HANDOFF_CHAT_FIRST_CURRENT.md)에서 필요 시 조회.

## 1. 최종 제품과 GitHub

- 목표: ChatGPT 일반 채팅에서 전문화명 입력 → 최신 실제 원문 Gate A 확보 → 상태/조건/행동/예외 분석 → V11 이상 한국어 **단일 HTML** CREATE/UPDATE. **독립 AI API·거대 JSON·검사기 증식이 최종 목표가 아니다.**
- 저장소: `degong2-code/wow-rotation-engine` (공개). 활성 작업 브랜치 `work/chat-first-talent-visibility-spell-media-20261114`, **PR [#24](https://github.com/degong2-code/wow-rotation-engine/pull/24) Draft·미병합**, base `work/chat-first-generic-html-assembly-20261113` (main 직접 대상 아님).
- **HEAD/CI는 이 문서보다 실제 GitHub 조회가 우선.** 인계 문서에 옛 SHA/CI를 현재인 것처럼 다시 붙이지 않는다. 승인 없이 PR ready/merge·main 수정·공개 배포 금지.

## 2. 실제 개인 제품 — V83 내용 유지, V85 밑줄 축소 디자인 시범

| 역할 | 파일 / 개인 Library 식별 | 실제 크기 / SHA-256 | 승인 |
|---|---|---|---|
| **V85 통합 디자인 시범 (냉기·분노 밑줄 축소)** | `/ROTATION TEXTBOOK/wow_rotation_v83_ui_bridge_v85_no_skill_underline_REVIEW.html` · `libfile_4f6232097cc881919079ed8c8e45dbe5` | **2,614,577B** · `ab771fd5fc527a30aae12ebc4bfa962640a8b0b895b958fce0f52522a6ca0b12` | **Q3 사용자 평가 전 REVIEW**. V83 게임 내용·14개 본문 불변 |
| **UI 브리지 v2 CSS (비공개 공통 자산)** | `/ROTATION TEXTBOOK/rotation_shared_ui_bridge_v2.css` · `libfile_49bd5ee91078819190690375539619cc` | **1,883B** · `2aaeb2e7bd916e2f58ca7f24b72784c42b00e4b27baf5699fff22a1d4070313a` | 냉기·분노 한정. 기본 점선 제거·hover 색상·키보드 포커스 |
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
| **Q2/Q3** | V85 **기술명 밑줄 축소 사용자 선호 확인**(냉기·분노 시범). 단 분노는 기존 전용 서식과 공통 CSS가 혼재해 **이질적**이라는 피드백. 공통 UI 전체 Q3 승인은 REVIEW |
| **Q4** | V83 V82↔V83 70상태 검사 범위 PASS, 냉기 v2 20상태 검사 범위 PASS. **이는 Q3 합격·실제 CDN HTTP·로컬 `file://` 증거가 아님** |
| **GitHub CI** | 2026-11-17 이전 커밋 검사 성공 기록 있음. **최신 HEAD CI는 매번 다시 조회** |

- 특정 근거 보류: 파괴 광역 3명/5명 조건 귀속, 비전 일부 심화 Tips 중첩 조건, 동적 원문/공식 아이콘 신원. 근거가 없으면 그 범위만 REVIEW, 임의 보완하지 않는다.
- **V84 사용자 평가 및 원인(2026-11-17):** 냉기/분노 모두 V83과 **비슷함**, V84가 대체로 조금 더 보기 좋음. 공통 CSS가 일부 위계만 개선해 체감 격차는 작다. 기술명에 `text-decoration:none`이 있어도 기존 `.spell.tip-trigger`의 **1px 점선 `border-bottom`이 남는 것**을 실제 computed style로 확인. 이는 별도 기능/콘텐츠 문제가 아니라 CSS 표현 층의 중복이다. V84 통합 실험·기각본과 상세 QA는 [이전 CURRENT_STATE Git 기록](https://github.com/degong2-code/wow-rotation-engine/blob/17dc6728a8a1fc27558c06a7bf653fb9ebd8858c/docs/CURRENT_STATE.md)에 보존.
- **V85 밑줄 축소 시범(사용자 선호 확인):** V84 HTML 마지막 UI CSS 한 블록만 **442B** 수정해 냉기·분노의 기술/효과 툴팁 기본 점선 하단 테두리를 **투명** 처리(기존 1px 레이아웃 유지), hover는 금색 글자, 키보드 `:focus-visible`은 2px 금색 outline. 일반 출처 링크·고통/파괴·타 12개 전문화 미수정. V84 대비 **14개 `.manual-view` HTML 완전 동일**, 기존 22개 script/30개 선행 CSS 및 2,871개 tip-trigger, 489개 링크 보존. Chromium 외부 요청 차단 상태에서 320·390·850·1365px×냉기/분노×영웅 2종 **16상태** Q4 범위: 가로 넘침 0/JS 오류 0/목차 앵커 누락 0. 추가 390·1365px×냉기/분노 **4상태** 영웅 전환·툴팁 Enter/ESC 확인, 키보드 modality `focus-visible` outline 작동 확인. **기술명 밑줄 축소 Q3 선호는 확인**, 실제 CDN 아이콘 응답/file://, 전체 UI 승인 및 Gate A/Q0/Q1은 REVIEW. V83 불변. 공통 UI 전체 승격 금지.
- **분노 이질성 직접 비교:** Chromium 1365px에서 V85 분노 기술명 **12px**, 조건 **10.5px**, 고통 V82 기술명 **13px**, 조건 **11.1px**로 실측. 분노 첫 화면은 쿨다운 중/밖×단일/광역 4행, 고통은 단일/광역 2행이므로 **원문 판단 분기 수 차이는 보존**하면서 활자 크기·여백·정보 위계를 정규화해야 한다. 분노 장 첫 번호 `00` vs 고통 `01`, 앞쪽 긴 범위/REVIEW 메타데이터 등도 이질감 요인. 특정 UI가 전체 승인됐다고 처리하지 않는다.
- **반복 제작 실패 원인:** 냉기 v1은 독립 CSS/2열 과밀로 이미 존재하던 V11 표현 규칙을 미적용, v2는 폭/열만 교정하여 고통의 표·섹션·메뉴·서식 위계를 실제 재사용하지 못했다. **Q4 통과를 Q3 만족으로 오판**. 다른 전문화도 동일한 실물 비교 없이 성공이라고 표기하지 않는다.
- UI 기준은 **사용자 평가를 통해 확정할 공통 실행 자산**이 목표. 콘텐츠는 최신 원문에서 독립 해석하고, UI는 재사용 가능한 검증된 셸/구성요소를 직접 재사용. 추가 문장만으로 재발을 막았다고 주장하지 않는다. 실행 계약: [CHAT_FIRST_PLAYBOOK](CHAT_FIRST_PLAYBOOK.md).

## 4. 다음 실제 제품 작업 (우선순위)

1. **분노 UI 이질성의 구조적 교정:** 현재 V83과 V85의 분노 본문 HTML은 완전 동일. V58에서 만든 분노 전용 CSS 5,216B를 그대로 둔 채 V85 공통 CSS 1,883B를 추가한 상태여서 서식 역할이 중복됨. **단순 CSS 추가 반복 대신 분노의 기존 전용 스타일과 공통 UI의 소유권을 정리**하여 고통·냉기와 동폭 비교. 게임 본문·75개 상세 우선순위·오프너·툴팁·메뉴 보존을 먼저 증명하며 승인 전 14개 일괄 변경 금지.
2. **콘텐츠 정확성·반복성:** 신규 독립 CREATE 및 V11 독립 재집필에서 Gate A/Q0/Q1 중요 누락을 좁게 감사. 빠른 참조 ↔ 상세·심화 역방향 의미 검증, 오프너 분기 확인. 같은 원고 계열 후속본을 독립 성공으로 중복 계산하지 않음.
3. **현재 운영 지식 유지:** PLAYBOOK은 짧은 실행 절차, CURRENT_STATE는 롤링 현황, 품질 정책은 규범, 기존 사례·커밋은 증거. **기존 규칙 미적용 실패는 새 규칙 추가 대신 재사용/검수 절차 교정**. 새 채팅은 긴 과거 인계 기본 정독 금지.

## 5. 복원/유지 원칙

- 새 채팅: **PROJECT_CANON → QUALITY_FIRST_POLICY §0/§0.1/§5.1 → CURRENT_STATE → CHAT_FIRST_PLAYBOOK** (필요할 때만 나머지).
- 완료: 변경 대상·결과물 Library 실물·SHA, 게이트별 PASS/REVIEW, 다음 1~3개로 **이 문서의 해당 칸을 교체**한다. 과거 날짜별 장문 로그를 덧붙이지 않는다.
- **기존 이력 삭제 아님:** [정비 직전 CURRENT_STATE 전체](https://github.com/degong2-code/wow-rotation-engine/blob/e3416fc9643f2108187648c356d776115e5cda82/docs/CURRENT_STATE.md) 및 [버전별 Git History](https://github.com/degong2-code/wow-rotation-engine/commits/work/chat-first-talent-visibility-spell-media-20261114/docs/CURRENT_STATE.md) 사용.
