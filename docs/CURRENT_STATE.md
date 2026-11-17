# ROTATION TEXTBOOK — 현재 제품/검증/다음 작업

> **단일 rolling 상태 정본 · 2026-11-17 KST.** 여기에 과거 버전별 긴 작업 기록을 덧붙이지 않는다. 이전 **111KB 원문은 [2026-11-17 정비 직전 Git 이력](https://github.com/degong2-code/wow-rotation-engine/blob/e3416fc9643f2108187648c356d776115e5cda82/docs/CURRENT_STATE.md)**에 전체 보존되어 있다. 이전 사례 상세는 [사례집](QUALITY_GENERALIZATION_CASEBOOK.md)·[기존 인계 이력](HANDOFF_CHAT_FIRST_CURRENT.md)에서 필요 시 조회.

## 1. 최종 제품과 GitHub

- 목표: ChatGPT 일반 채팅에서 전문화명 입력 → 최신 실제 원문 Gate A 확보 → 상태/조건/행동/예외 분석 → V11 이상 한국어 **단일 HTML** CREATE/UPDATE. **독립 AI API·거대 JSON·검사기 증식이 최종 목표가 아니다.**
- 저장소: `degong2-code/wow-rotation-engine` (공개). 활성 작업 브랜치 `work/chat-first-talent-visibility-spell-media-20261114`, **PR [#24](https://github.com/degong2-code/wow-rotation-engine/pull/24) Draft·미병합**, base `work/chat-first-generic-html-assembly-20261113` (main 직접 대상 아님).
- **HEAD/CI는 이 문서보다 실제 GitHub 조회가 우선.** 인계 문서에 옛 SHA/CI를 현재인 것처럼 다시 붙이지 않는다. 승인 없이 PR ready/merge·main 수정·공개 배포 금지.

## 2. 실제 개인 제품 — V83 내용 유지, V86 분노 UI 정규화 시범

| 역할 | 파일 / 개인 Library 식별 | 실제 크기 / SHA-256 | 승인 |
|---|---|---|---|
| **V86 통합 UI 정규화 시범 (분노만 추가 변경)** | `/ROTATION TEXTBOOK/wow_rotation_v83_fury_ui_normalized_v86_REVIEW.html` · `libfile_79fb26a5e4f881919f32d094d65a329d` | **2,616,212B** · `72c9adcc6b39f9465b4d268a3b6c6f0fbf98d135cc4589fce0e45eae1caa5db8` | **사용자 Q3 REVIEW**. V85 밑줄 축소 유지, 14개 원고 불변 |
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
| **Q2/Q3** | V85 **기술명 밑줄 축소 사용자 선호 확인**. 분노 이질성 지적에 따라 V86에서 기존 전용 CSS와 공통 CSS의 중복 책임을 정리. **V86 사용자 동폭 화면 평가 전 REVIEW** |
| **Q4** | V86 V85 대비 **14/14 원고, 기존 JS 21개, 비대상 CSS 29개 원형 보존**. 분노 영웅×6폭 **12상태** JS/넘침/목차/화살표 119개 결합 검사 PASS; 냉기 390/1365px 스타일 동일, 툴팁 Enter/ESC 확인. CDN/file:// REVIEW |
| **GitHub CI** | 2026-11-17 이전 커밋 검사 성공 기록 있음. **최신 HEAD CI는 매번 다시 조회** |

- 특정 근거 보류: 파괴 광역 3명/5명 조건 귀속, 비전 일부 심화 Tips 중첩 조건, 동적 원문/공식 아이콘 신원. 근거가 없으면 그 범위만 REVIEW, 임의 보완하지 않는다.
- **V86 분노 UI 정규화(2026-11-17):** V85에서 분노 전용 스타일(5,216B)과 공통 브리지(1,883B)가 기술명/조건/표/버튼을 중복 지정해 고통·냉기 대비 이질감 발생. **분노 전용 CSS를 4,719B의 구조·전용 분기 담당으로 정리하고, 공통 브리지 v3가 13px/11.1px 기술·조건 및 표/영웅 버튼 시각을 담당**하도록 변경. 전역 2열 폭 20% 규칙의 충돌을 조정하여 데스크톱 상황 열 122px 유지. 분노 우선순위 화살표 119개를 **런타임에서 다음 기술과 결합**(긴 괄호 조건의 줄바꿈 허용). **14개 `.manual-view` HTML 내용 전체·기존 21개 JS·비대상 29개 CSS**는 V85와 원문 동일. 분노 상세표 75행/기술 214개/조건 51개/영웅 블록 8개 보존. Chromium 외부 이미지 차단: 320·390·850·1100·1365·1480px×학살자/산왕 **12상태**에서 JS 예외/문서 넘침/목차 앵커 누락 0, 영웅 전환, 화살표 전부 결합. 390·1365px Enter 툴팁 고정 및 ESC 닫기 확인. 냉기 390·1365px 대표 스타일 V85와 동일. **사용자 V86 Q3, CDN 이미지 실응답, file://, 게임 Gate A/Q0/Q1 전체는 REVIEW**. V85는 밑줄 축소 선호를 얻은 비교용이며 구체적인 전 버전 변경 이력은 Git commit에서 조회.
- **반복 제작 실패 원인:** 냉기 v1은 독립 CSS/2열 과밀로 이미 존재하던 V11 표현 규칙을 미적용, v2는 폭/열만 교정하여 고통의 표·섹션·메뉴·서식 위계를 실제 재사용하지 못했다. **Q4 통과를 Q3 만족으로 오판**. 다른 전문화도 동일한 실물 비교 없이 성공이라고 표기하지 않는다.
- UI 기준은 **사용자 평가를 통해 확정할 공통 실행 자산**이 목표. 콘텐츠는 최신 원문에서 독립 해석하고, UI는 재사용 가능한 검증된 셸/구성요소를 직접 재사용. 추가 문장만으로 재발을 막았다고 주장하지 않는다. 실행 계약: [CHAT_FIRST_PLAYBOOK](CHAT_FIRST_PLAYBOOK.md).

## 4. 다음 실제 제품 작업 (우선순위)

1. **V86 사용자 Q3 실화면 비교:** V85와 V86의 분노 첫 화면을 같은 PC/모바일 폭으로 비교해 표 너비, 기술/조건 크기, 화살표 연결, 행간의 실제 가독성 확인. 특히 아이콘 실제 응답과 850px 안팎의 표/상세 가독성 평가. 승인 전 다른 13개 전문화 일괄 전파 금지.
2. **콘텐츠 정확성·반복성:** 신규 독립 CREATE 및 V11 독립 재집필에서 Gate A/Q0/Q1 중요 누락을 좁게 감사. 빠른 참조 ↔ 상세·심화 역방향 의미 검증, 오프너 분기 확인. 같은 원고 계열 후속본을 독립 성공으로 중복 계산하지 않음.
3. **현재 운영 지식 유지:** PLAYBOOK은 짧은 실행 절차, CURRENT_STATE는 롤링 현황, 품질 정책은 규범, 기존 사례·커밋은 증거. **기존 규칙 미적용 실패는 새 규칙 추가 대신 재사용/검수 절차 교정**. 새 채팅은 긴 과거 인계 기본 정독 금지.

## 5. 복원/유지 원칙

- 새 채팅: **PROJECT_CANON → QUALITY_FIRST_POLICY §0/§0.1/§5.1 → CURRENT_STATE → CHAT_FIRST_PLAYBOOK** (필요할 때만 나머지).
- 완료: 변경 대상·결과물 Library 실물·SHA, 게이트별 PASS/REVIEW, 다음 1~3개로 **이 문서의 해당 칸을 교체**한다. 과거 날짜별 장문 로그를 덧붙이지 않는다.
- **기존 이력 삭제 아님:** [정비 직전 CURRENT_STATE 전체](https://github.com/degong2-code/wow-rotation-engine/blob/e3416fc9643f2108187648c356d776115e5cda82/docs/CURRENT_STATE.md) 및 [버전별 Git History](https://github.com/degong2-code/wow-rotation-engine/commits/work/chat-first-talent-visibility-spell-media-20261114/docs/CURRENT_STATE.md) 사용.
