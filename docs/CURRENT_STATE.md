# ROTATION TEXTBOOK — 현재 제품/검증/다음 작업

> **단일 rolling 상태 정본 · 2026-11-17 KST.** 여기에 과거 버전별 긴 작업 기록을 덧붙이지 않는다. 이전 **111KB 원문은 [2026-11-17 정비 직전 Git 이력](https://github.com/degong2-code/wow-rotation-engine/blob/e3416fc9643f2108187648c356d776115e5cda82/docs/CURRENT_STATE.md)**에 전체 보존되어 있다. 이전 사례 상세는 [사례집](QUALITY_GENERALIZATION_CASEBOOK.md)·[기존 인계 이력](HANDOFF_CHAT_FIRST_CURRENT.md)에서 필요 시 조회.

## 1. 최종 제품과 GitHub

- 목표: ChatGPT 일반 채팅에서 전문화명 입력 → 최신 실제 원문 Gate A 확보 → 상태/조건/행동/예외 분석 → V11 이상 한국어 **단일 HTML** CREATE/UPDATE. **독립 AI API·거대 JSON·검사기 증식이 최종 목표가 아니다.**
- 저장소: `degong2-code/wow-rotation-engine` (공개). 활성 작업 브랜치 `work/chat-first-talent-visibility-spell-media-20261114`, **PR [#24](https://github.com/degong2-code/wow-rotation-engine/pull/24) Draft·미병합**, base `work/chat-first-generic-html-assembly-20261113` (main 직접 대상 아님).
- **HEAD/CI는 이 문서보다 실제 GitHub 조회가 우선.** 인계 문서에 옛 SHA/CI를 현재인 것처럼 다시 붙이지 않는다. 승인 없이 PR ready/merge·main 수정·공개 배포 금지.

## 2. 실제 개인 제품 — V83 내용 정본 유지, V84 UI 통합 시범 별도

| 역할 | 파일 / 개인 Library 식별 | 실제 크기 / SHA-256 | 승인 |
|---|---|---|---|
| **V84 통합 UI 브리지 시범 (14개, 콘텐츠 V83 동일)** | `/ROTATION TEXTBOOK/wow_rotation_v83_ui_bridge_v84_REVIEW.html` · `libfile_b5bd6a2d32388191b023496edac6b674` | **2,614,135B** · `4be23429eee6208ad5d1266e8f8bb5d0eccd352366dd080d6f32ad0c6fd3914d` | **Q3 사용자 비교 전 REVIEW**. V83은 변경·덮어쓰기 없음 |
| **UI 브리지 v1 CSS (비공개 공통 자산)** | `/ROTATION TEXTBOOK/rotation_shared_ui_bridge_v1.css` · `libfile_955399743bec8191a761d082bf689e26` | **1,441B** · `075e66d3d77093bd6bd2506cb7dc3b8b826ee1e3661f9e6a3b396e6518e7fba1` | 냉기·분노 한정 적용 시범. 최종 디자인 정본 아님 |
| **최신 통합 V83 (14개 전문화)** | `/ROTATION TEXTBOOK/wow_rotation_v11_partial_design_v83_REVIEW.html` · `libfile_098b2ad2528081919d0608ba39b185d4` | **2,611,792B** · `14be1b44db12cea04ca56a1655a97a3dcc921dab697070e97f5935901c2419ed` | **REVIEW** |
| **원본 V11 UX 비교 기준(7개)** | `wow_rotation_manual_engine_v2.html` · `libfile_047243e589bc8191b348398ec923c910` | **898,297B** · `5d70279c4dd073eccef1f3b13565a8f555cd81c9f0a5b7eda7e3485e410742be` | 역사적 비교 기준. 현재 패치 정답 아님 |
| 냉기 독립 **v1** | `/ROTATION TEXTBOOK/wow_rotation_frost_independent_1215_v1_REVIEW(2).html` · `libfile_f2d6d136aee48191830c0f78f869789c` | **154,130B** · `a3d64e678dd7343e7cf6c98a3c747b656ec1ec8783c4d79cc6ed4d614c6e7251` | **Q3 반려 반례**. 게임 내용 Q0/Q1 검토본 |
| 냉기 독립 **v2 UI 시범** | `/ROTATION TEXTBOOK/wow_rotation_frost_independent_1215_v2_integrated_ui_REVIEW.html` · `libfile_caf97e75a5848191b0bae79cf9215af4` | **157,165B** · `7aaf88403379cc3ac1376570b3d648e76b1e2e91fc4f11ae1d1cf065499a85d8` | **Q3 비교에서 여전히 고통 V82 대비 미흡**. 독립 성공 2회로 집계 금지 |
| **공통 UI 셸 v0 (콘텐츠 없음)** | `/ROTATION TEXTBOOK/rotation_shared_ui_shell_v0_REVIEW.html` · `libfile_43334e8486288191a3ad1b8476c9d3c4` | **13,653B** · `a05f2698f5f43cc5f095e4c28787967d9675d0d4fb391b2802ee7e6bd3a6ed0e` | **UI 재사용 시험용 REVIEW**. 최종 UI 정본 아님 |
| 냉기 독립 **v3 공통 UI 파일럿** | `/ROTATION TEXTBOOK/wow_rotation_frost_independent_1215_v3_shared_ui_REVIEW.html` · `libfile_e5356d68bc448191880b116441b5bb62` | **173,022B** · `079150c7a6f5277e756d2d7135e9a1b6acab272ff54253f220110b66b93c4bcc` | **Q3 사용자 비교 전 REVIEW**. 기존 냉기 v2 원고에서 UI만 전환한 계열 |
| **분노 전사 v5 공통 UI 교차 시범** | `/ROTATION TEXTBOOK/wow_rotation_fury_independent_1215_v5_shared_ui_REVIEW.html` · `libfile_e8f45cded4108191a7ce7c44a97a176d` | **193,834B** · `a7a06dab22dcaf6488296435fe07aa1f253a116acdaa9a8a5ae546dfdf6063cb` | **Q3 사용자 평가 전 REVIEW**. 기존 분노 v4 원고의 UI 변경 계열 |
| 고통 흑마법사 독립 UX 비교 | `/ROTATION TEXTBOOK/wow_rotation_affliction_decision_sync_v82_REVIEW.html` · `libfile_cf7ca2a7c1ac819192442028ac1b3c87` | **148,608B** · `a46a18a6209545fb4da9f4be9a94df1de002e9301be6e4cf146a2472d8b123c8` | 첫 화면 가독성 사용자 호평. 게임 전체 정확성·전역 디자인 승인 아님 |

- V83 14개: 화염·냉기·비전 마법사 / 냉기 죽음의 기사 / 사격·야수 사냥꾼 / 잠행·암살 도적 / 조화 드루이드 / 고양 주술사 / 징벌 성기사 / 분노 전사 / 파괴·고통 흑마법사.
- V83은 비전·파괴 배경 통일, 파괴 기술명 **흰색·굵게·기본 밑줄 없음** 시범. 기존 14개 전문화 본문/JS는 V82 대비 보존, 통합 CSS 1개 블록만 변경. **V83 사용자 Q2/Q3 최종 평가는 아직 REVIEW**. 금색/핫핑크/전체 타이포·행간 의미체계 확정되지 않음.
- **개인 파일을 사용하기 전에 현재 세션에서 실물 크기/SHA와 접근을 다시 검증.** 이 표는 기록 당시 실증이지 새 채팅의 실물 접근을 대신하지 않는다. 비공개 HTML/저장된 와우헤드 원문은 공개 GitHub 업로드 금지.

## 3. 현재 품질/승인 경계

| 구분 | 현재 판단 |
|---|---|
| **Gate A** | 기준 패치·영웅·선택형/숨김·hover·오프너의 **전체 확보는 REVIEW** |
| **Q0/Q1** | 모든 기술명·수치·조건·우선순위·실제 다음 선택을 전수 승인하지 않음 (**REVIEW**) |
| **Q2/Q3** | 고통 UX 일부 호평. V83 최종 평가 REVIEW, 냉기 v1/v2는 고통 대비 **가독성 퇴보를 사용자가 지적** |
| **Q4** | V83 V82↔V83 70상태 검사 범위 PASS, 냉기 v2 20상태 검사 범위 PASS. **이는 Q3 합격·실제 CDN HTTP·로컬 `file://` 증거가 아님** |
| **GitHub CI** | 2026-11-17 이전 커밋 검사 성공 기록 있음. **최신 HEAD CI는 매번 다시 조회** |

- 특정 근거 보류: 파괴 광역 3명/5명 조건 귀속, 비전 일부 심화 Tips 중첩 조건, 동적 원문/공식 아이콘 신원. 근거가 없으면 그 범위만 REVIEW, 임의 보완하지 않는다.
- **V84 실제 통합 시험(2026-11-17):** 공통 UI 셸 v0의 9.3KB CSS를 V83의 냉기·분노에 무조건 적용한 경우 JS·가로 넘침은 없었지만 **간격·표 타이포의 Q3 회귀**. 독립 냉기 v3 전체 이식은 V83 냉기 약 6,877자→4,971자 수준의 내용 차이, 상세 장 구성 차이(실물 원시 표 행 V83 84 vs 독립 52), 클릭형 tooltip 261→0 및 기존 메뉴 앵커 2개 미해결, 320px 폭 330px로 **콘텐츠·통합 Q4 퇴보**였으므로 *모두 기각*, V83은 수정하지 않음. 분노 v5는 V83과 거의 동문이지만 일부 설명 문구가 다르므로 원고 교체도 보류. **대안 V84**는 V83 원본 14개 `.manual-view` HTML·기존 CSS 30개·기존 JS 21개를 모두 **바이트 동일하게 보존**하고, **공통 CSS v1 1개(1,441B) + 냉기/분노용 클래스 연결 JS 1개**만 추가한 비공개 UI 시범. 320/390/1365px×냉기·분노×영웅 2종 = **12상태**: 문서 가로 넘침 0, JS 오류 0, 메뉴·영웅 본문 선택 정합·기존 앵커 누락 0. PC/모바일 각 냉기·분노 **4개 상호작용 상태**에서 영웅 본문 버튼 클릭, 툴팁 Enter 열기 및 ESC 닫기 확인. 기존 콘텐츠 Q0/Q1 재승인 증거 아님, 실제 아이콘 외부 HTTP·file:// 및 **사용자 Q3·전 전문화 통합 회귀**는 REVIEW. 사용자 승인 전 V84 UI 전체 강제 금지.
- **반복 제작 실패 원인:** 냉기 v1은 독립 CSS/2열 과밀로 이미 존재하던 V11 표현 규칙을 미적용, v2는 폭/열만 교정하여 고통의 표·섹션·메뉴·서식 위계를 실제 재사용하지 못했다. **Q4 통과를 Q3 만족으로 오판**. 다른 전문화도 동일한 실물 비교 없이 성공이라고 표기하지 않는다.
- UI 기준은 **사용자 평가를 통해 확정할 공통 실행 자산**이 목표. 콘텐츠는 최신 원문에서 독립 해석하고, UI는 재사용 가능한 검증된 셸/구성요소를 직접 재사용. 추가 문장만으로 재발을 막았다고 주장하지 않는다. 실행 계약: [CHAT_FIRST_PLAYBOOK](CHAT_FIRST_PLAYBOOK.md).

## 4. 다음 실제 제품 작업 (우선순위)

1. **V84 통합 디자인 사용자 Q3 평가:** V83과 V84(냉기·분노만 공통 UI 적용)를 같은 PC·모바일 화면 폭에서 비교. 확인된 아이콘 HTTP·file:// 실행 및 전 전문화 회귀 범위는 별도 점검. **최종 채택·전체 14개 전파는 사용자 승인 전 금지**.
2. **콘텐츠 정확성·반복성:** 신규 독립 CREATE 및 V11 독립 재집필에서 Gate A/Q0/Q1 중요 누락을 좁게 감사. 빠른 참조 ↔ 상세·심화 역방향 의미 검증, 오프너 분기 확인. 같은 원고 계열 후속본을 독립 성공으로 중복 계산하지 않음.
3. **현재 운영 지식 유지:** PLAYBOOK은 짧은 실행 절차, CURRENT_STATE는 롤링 현황, 품질 정책은 규범, 기존 사례·커밋은 증거. **기존 규칙 미적용 실패는 새 규칙 추가 대신 재사용/검수 절차 교정**. 새 채팅은 긴 과거 인계 기본 정독 금지.

## 5. 복원/유지 원칙

- 새 채팅: **PROJECT_CANON → QUALITY_FIRST_POLICY §0/§0.1/§5.1 → CURRENT_STATE → CHAT_FIRST_PLAYBOOK** (필요할 때만 나머지).
- 완료: 변경 대상·결과물 Library 실물·SHA, 게이트별 PASS/REVIEW, 다음 1~3개로 **이 문서의 해당 칸을 교체**한다. 과거 날짜별 장문 로그를 덧붙이지 않는다.
- **기존 이력 삭제 아님:** [정비 직전 CURRENT_STATE 전체](https://github.com/degong2-code/wow-rotation-engine/blob/e3416fc9643f2108187648c356d776115e5cda82/docs/CURRENT_STATE.md) 및 [버전별 Git History](https://github.com/degong2-code/wow-rotation-engine/commits/work/chat-first-talent-visibility-spell-media-20261114/docs/CURRENT_STATE.md) 사용.
