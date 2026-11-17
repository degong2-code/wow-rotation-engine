# ROTATION TEXTBOOK — 현재 제품/검증/다음 작업

> **단일 rolling 상태 정본 · 2026-11-17 KST.** 여기에 과거 버전별 긴 작업 기록을 덧붙이지 않는다. 이전 **111KB 원문은 [2026-11-17 정비 직전 Git 이력](https://github.com/degong2-code/wow-rotation-engine/blob/e3416fc9643f2108187648c356d776115e5cda82/docs/CURRENT_STATE.md)**에 전체 보존되어 있다. 이전 사례 상세는 [사례집](QUALITY_GENERALIZATION_CASEBOOK.md)·[기존 인계 이력](HANDOFF_CHAT_FIRST_CURRENT.md)에서 필요 시 조회.

## 1. 최종 제품과 GitHub

- 목표: ChatGPT 일반 채팅에서 전문화명 입력 → 최신 실제 원문 Gate A 확보 → 상태/조건/행동/예외 분석 → V11 이상 한국어 **단일 HTML** CREATE/UPDATE. **독립 AI API·거대 JSON·검사기 증식이 최종 목표가 아니다.**
- 저장소: `degong2-code/wow-rotation-engine` (공개). 활성 작업 브랜치 `work/chat-first-talent-visibility-spell-media-20261114`, **PR [#24](https://github.com/degong2-code/wow-rotation-engine/pull/24) Draft·미병합**, base `work/chat-first-generic-html-assembly-20261113` (main 직접 대상 아님).
- **HEAD/CI는 이 문서보다 실제 GitHub 조회가 우선.** 인계 문서에 옛 SHA/CI를 현재인 것처럼 다시 붙이지 않는다. 승인 없이 PR ready/merge·main 수정·공개 배포 금지.

## 2. 실제 개인 제품 — V83 내용 유지, V87 분노 편집 구조 시범

| 역할 | 파일 / 개인 Library 식별 | 실제 크기 / SHA-256 | 승인 |
|---|---|---|---|
| **V87 통합 UI 편집 구조 시범 (분노만 재배치)** | `/ROTATION TEXTBOOK/wow_rotation_v83_fury_editorial_v87_REVIEW.html` · `libfile_10b945e5305881918b7eae513550c3fa` | **2,629,448B** · `62ef9915a8a61e75e91c0b5fc2ee63997b6d239b85368a0360a5ebf8d148031d` | **Q3 사용자 REVIEW**, 게임 규칙 원고 유지. V86 별도 보존 |
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
| **Q2/Q3** | V85 **기술명 밑줄 축소 사용자 선호 확인**, V86은 글꼴·표 개선만으로 정보 위계 이질성 미해결. V87 분노 **영웅 선택→요약/오프너→영웅별 원칙** 재배치, 사용자 최종 가독성 **REVIEW** |
| **Q4** | V87 vs V86: 분노 외 **13개 전문화 원시 HTML 바이트 동일**, 기존 JS 22개·비대상 스타일 원문 동일. 분노 **75개 상세행·60개 오프너 단계·기존 우선순위/툴팁 데이터 유지**. 6폭×2영웅 **12상태** 넘침·JS·목차 PASS, 다른 3전문화 전환/신규 원칙 툴팁 Enter/ESC 시험 범위 PASS. CDN·실제 `file://` REVIEW |
| **GitHub CI** | 2026-11-17 이전 커밋 검사 성공 기록 있음. **최신 HEAD CI는 매번 다시 조회** |

- 특정 근거 보류: 파괴 광역 3명/5명 조건 귀속, 비전 일부 심화 Tips 중첩 조건, 동적 원문/공식 아이콘 신원. 근거가 없으면 그 범위만 REVIEW, 임의 보완하지 않는다.
- **V87 구조 재편집(2026-11-17):** V86에서 글자/색상만 맞춰도 분노의 정보 설계가 이질적이란 사용자 피드백. **게임 우선순위 내용은 유지**하면서 영웅 선택을 빠른 참조 제목 위로, 기존 6개 핵심 원칙을 첫 화면 하단으로 이동; 영웅 전용 원칙은 선택 영웅에만 표시. `00` 장 시작 번호 제거, 나머지 장 01~05·사이드 목차/해시 동기화, 두 원문 표·기본 오프너와 상세 75행/60단계 유지. 업무용 `신규 CREATE`/장문 검증 메타데이터는 첫 화면에서 내리고 출처 장에 보존. 기존 동일 분노 내부에서 확인된 스킬 이미지/툴팁 **25곳을 심화 문장에 연결**(외부 이미지 실제 응답은 미검증). V86 대비 **다른 13개 `.manual-view` 원시 원본 문자열과 기존 `<script>`·비대상 `<style>` 원형 보존**, Fury 규칙·오프너 조건/순서 대조 PASS. Chromium 320·390·850·1100·1365·1480px×학살자/산왕 12상태: 메뉴/영웅 전환/선택형 원칙/넘침·JS 오류 0. 390·1365px 신규 기술 툴팁 **Enter 열기/ESC 닫기**, 다른 3전문화 전환 확인. 사용자가 화면 직접 읽어 보는 Q3 및 원문/게임 전체 Gate A/Q0/Q1, 아이콘 CDN/file://는 **REVIEW**. V83 통합 원본과 이전 V86 별도 보존.
- **반복 제작 실패 원인:** 냉기 v1은 독립 CSS/2열 과밀로 이미 존재하던 V11 표현 규칙을 미적용, v2는 폭/열만 교정하여 고통의 표·섹션·메뉴·서식 위계를 실제 재사용하지 못했다. **Q4 통과를 Q3 만족으로 오판**. 다른 전문화도 동일한 실물 비교 없이 성공이라고 표기하지 않는다.
- UI 기준은 **사용자 평가를 통해 확정할 공통 실행 자산**이 목표. 콘텐츠는 최신 원문에서 독립 해석하고, UI는 재사용 가능한 검증된 셸/구성요소를 직접 재사용. 추가 문장만으로 재발을 막았다고 주장하지 않는다. 실행 계약: [CHAT_FIRST_PLAYBOOK](CHAT_FIRST_PLAYBOOK.md).

## 4. 다음 실제 제품 작업 (우선순위)

1. **V87 사용자 Q3 비교:** V86과 V87의 분노 첫 화면 및 이동한 핵심 원칙을 같은 PC/모바일 폭에서 비교. 특히 **기술명/아이콘, 영웅 선택 위치, 4가지 전투 상태의 독해, 장 목차·본문 연결, 첫 화면 길이**의 실사용 가독성 평가. 게임 원문 판단이나 모든 전문화 디자인 승격은 사용자 승인 전 REVIEW.
2. **콘텐츠 정확성·반복성:** 신규 독립 CREATE 및 V11 독립 재집필에서 Gate A/Q0/Q1 중요 누락을 좁게 감사. 빠른 참조 ↔ 상세·심화 역방향 의미 검증, 오프너 분기 확인. 같은 원고 계열 후속본을 독립 성공으로 중복 계산하지 않음.
3. **현재 운영 지식 유지:** PLAYBOOK은 짧은 실행 절차, CURRENT_STATE는 롤링 현황, 품질 정책은 규범, 기존 사례·커밋은 증거. **기존 규칙 미적용 실패는 새 규칙 추가 대신 재사용/검수 절차 교정**. 새 채팅은 긴 과거 인계 기본 정독 금지.

## 5. 복원/유지 원칙

- 새 채팅: **PROJECT_CANON → QUALITY_FIRST_POLICY §0/§0.1/§5.1 → CURRENT_STATE → CHAT_FIRST_PLAYBOOK** (필요할 때만 나머지).
- 완료: 변경 대상·결과물 Library 실물·SHA, 게이트별 PASS/REVIEW, 다음 1~3개로 **이 문서의 해당 칸을 교체**한다. 과거 날짜별 장문 로그를 덧붙이지 않는다.
- **기존 이력 삭제 아님:** [정비 직전 CURRENT_STATE 전체](https://github.com/degong2-code/wow-rotation-engine/blob/e3416fc9643f2108187648c356d776115e5cda82/docs/CURRENT_STATE.md) 및 [버전별 Git History](https://github.com/degong2-code/wow-rotation-engine/commits/work/chat-first-talent-visibility-spell-media-20261114/docs/CURRENT_STATE.md) 사용.
