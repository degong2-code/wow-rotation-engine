# ROTATION TEXTBOOK — 현재 제품·REVIEW·다음 작업

> **Rolling 현황 정본 · 2026-11-18 KST.** 이 파일은 버전별 일지가 아니다. 이전 상세 Q0/Q1·Q3/Q4 및 연구 검증 수치는 [정비 직전 전체 상태](https://github.com/degong2-code/wow-rotation-engine/blob/f989fbd3205949bae141078829fb60a86328ca72/docs/CURRENT_STATE.md)와 기존 Git 이력·[사례집](QUALITY_GENERALIZATION_CASEBOOK.md)에 보존한다. 이 표의 과거 실측 SHA는 **새 채팅의 실제 파일 접근 증거가 아니다**.

## 1. 현재 GitHub 기준

- 공개 저장소: `degong2-code/wow-rotation-engine`.
- 작업 브랜치: `work/chat-first-talent-visibility-spell-media-20261114` / [PR #24](https://github.com/degong2-code/wow-rotation-engine/pull/24) **Draft·미병합**, base `work/chat-first-generic-html-assembly-20261113` (**main 아님**).
- HEAD·활성 PR·base·CI는 **매 작업에서 실제 GitHub를 재조회**하며 이 파일의 날짜/과거 로그로 대체하지 않는다. 사용자 승인 없이 main 변경·병합·공개 배포 금지.

## 2. 개인 Library 제품 — 마지막 실측 기록

| 역할 / 상태 | Library 위치 및 ID | 기록된 실제 바이트·SHA-256 |
|---|---|---|
| **통합 V88** · 14개 전문화, **디자인 일부 선호 확인·전체 REVIEW** | `/ROTATION TEXTBOOK/wow_rotation_v83_fury_editorial_v88_no_cell_shading_REVIEW.html` · `libfile_1c87d86e0b048191a7ee46bc6b093fc1` | **2,629,547B** · `1c817f1f8896b111f18be367fe879aa09214e6ecd4e450afa399a6443efbd236` |
| **악마 흑마법사 v3** · 15번째 후보, 통합 미연결, **Gate A·Q0/Q1·Q3 REVIEW** | `/ROTATION TEXTBOOK/wow_rotation_demonology_1215_independent_q0verified_v3_REVIEW.html` · `libfile_4f0b0b886858819193d8ab5b9a5dfce2` | **106,510B** · `c6d191fd237781835f82e8ccbd38a6e1fc38d98ac00cf161efe2a2356a914e6a` |
| **기존 통합 V83** · 14개, 변경 전 비교 기준 | `/ROTATION TEXTBOOK/wow_rotation_v11_partial_design_v83_REVIEW.html` · `libfile_098b2ad2528081919d0608ba39b185d4` | **2,611,792B** · `14be1b44db12cea04ca56a1655a97a3dcc921dab697070e97f5935901c2419ed` |
| **기존 V11** · UX·설명 비교 기준, 현재 패치 게임 정답 아님 | `wow_rotation_manual_engine_v2.html` · `libfile_047243e589bc8191b348398ec923c910` | **898,297B** · `5d70279c4dd073eccef1f3b13565a8f555cd81c9f0a5b7eda7e3485e410742be` |
| **고통 흑마법사 V82** · 사용자 가독성 호평(전체 승인 아님) | `/ROTATION TEXTBOOK/wow_rotation_affliction_decision_sync_v82_REVIEW.html` · `libfile_cf7ca2a7c1ac819192442028ac1b3c87` | **148,608B** · `a46a18a6209545fb4da9f4be9a94df1de002e9301be6e4cf146a2472d8b123c8` |
| **공통 CSS 브리지 v3** · 이전 시범 참고용, 독립 제품 아님 | `/ROTATION TEXTBOOK/rotation_shared_ui_bridge_v3.css` · `libfile_58a5fa44280881919ba7b90470d4dc3a` | **3,187B** · `5bd71813a185cf4facd6bde4ca9b88bc73f73d0091401862507f968c89c6ec64` |

- 14개: 화염·냉기·비전 마법사, 냉기 죽음의 기사, 사격·야수 사냥꾼, 잠행·암살 도적, 조화 드루이드, 고양 주술사, 징벌 성기사, 분노 전사, 파괴·고통 흑마법사.
- **V88 사용자 선호:** V85 기술명 기본 밑줄 축소, V87 분노 첫 화면 정보 배치, V88 우선순위/오프너 표 셀 음영 제거. 구분이 부족할 때만 다시 디자인 검토. **전 제품 UI 정식 승인 아님**.
- **비공개 자산 정책:** 개인 HTML·저장 원문·원시 툴팁 본문 공개 GitHub 업로드 금지. 실제 사용할 파일은 Library에서 매번 실물 크기·SHA 재조회.
- **악마 12.1.5 원문 저장본 확보(2026-11-18):** 개인 Library `/ROTATION TEXTBOOK/source_demonology_1215_wowhead_saved_20261118_PRIVATE.html` · `libfile_1f27a2505e288191b2fea4ebd122fcaf` · **561,371B**, SHA-256 `e5e7069f248b07a25a047fc008ee1a9048d5b9491d8dcf153fe89b4d4857f5b2`. 내장 `guide-body` WHML **19,383자**, SHA-256 `e6e0bb1f6f82e89018a4ea14d168bb7fb66f7ba528623ba192c66cb31d7f2070`, 영웅 선택 2개·단일/광역 우선순위 4×8행·영웅별 오프너 timeline 2개/`rt-step` 35개/`rt-branch` 4개·명명 툴팁 본문 2개 확보. 패치 12.1.5·작성자 NotWarlock·2026-10-13 수정 메타 포함. 원문은 공개 GitHub에 업로드하지 않음.

## 3. 남은 검증 경계

| 게이트 | 현재 판정 |
|---|---|
| **Gate A** | **악마 기준 원문 WHML 확보:** 위 개인 저장본에서 영웅 2종·우선순위 4개·영웅별 오프너 2개/타임라인·실제 tooltip 내용 확인. 기존 DNS 실패는 이번 컨테이너 네트워크 경로의 실패로 **원문 부재가 아님**. 원문 내 `Trick-Op` 미정의 표시 조건·`NotesHighlight` 미정의 참조, 타임라인 기술 ID↔산문 차이는 REVIEW. 단일/광역 **별도 4오프너라는 증거 없음**. 메인 HTML 추가 제출 불필요 |
| **Q0/Q1** | 악마 v3는 원문 타임라인의 종족기/장신구/소모품 분기·영혼수확자 전투 전 2초 선시전 표식이 누락됨. 확보한 선택/조건/Notes를 우선순위↔오프너에 귀속 후 교정 필요. 일부 출처 내 참조 불일치는 표시만 REVIEW. 파괴 광역·비전 심화도 별도 REVIEW |
| **Q2/Q3** | V88 선호 일부 확인. **악마 v3↔고통 V82 동폭 850px:** 첫 빠른 우선순위 표 **340px(악마) vs 219px(고통)**; 악마 단일 164px/광역 135px vs 고통 105px/75px. 내용·설명 밀도 개선 필요. Chromium `set_content`, 외부 이미지 차단 기준. 사용자/전체 Q3 REVIEW |
| **Q4** | V88↔V87 14개 본문·기존 JS 보존, 8상태 UI 기능 검사 범위 PASS. 악마 v3 12상태 검사 범위 PASS. **CDN 이미지 실응답·실제 `file://`·완전한 실기기 검증은 별도 REVIEW** |

**현재 기준 문서:** [PLAYBOOK](CHAT_FIRST_PLAYBOOK.md) §0의 작업 선택·§0.1의 **필수 참조 라우팅**. 신규 CREATE·원문 UPDATE는 웹 텍스트만 읽고 사용자에게 저장본 여러 개를 바로 요청하지 않는다. 기존 HTTP→WHML→필요 시 정상 브라우저 경로를 먼저 확인·가능하면 실행한다. **코드 존재/실행/원문 취득/게임 판단 승인**은 서로 다르다.

## 4. 다음 1~3개 제품 작업 — `진행` 단독 요청의 기준

1. **악마 원문→v3 Q0/Q1 교정:** 이번에 Library에 확보한 실제 12.1.5 WHML의 `display-options`, `[rotation-timeline]` 및 tooltip 정의를 기존 `embedded_markup` 방법으로 연결. 누락된 전투 전 2초·종족기/장신구/소모품 조건과 설명 원래 귀속을 복원. `Trick-Op`/`NotesHighlight` 미정의는 원문 이상으로 별도 REVIEW하고, **없는 단일·광역 오프너 분기 생성 금지**.
2. **악마 v3 원고·첫 화면 재검토:** 확보한 추가 조건만 Q0/Q1에 보충. 고통 V82·통합 V88과 동폭 Q2/Q3 비교, 중요한 행동 조건의 요약↔상세 귀속 검수. 게임 판단 모호함은 좁게 REVIEW.
3. **반복 제작 품질 실증:** 다른 전문화의 신규 독립 CREATE 또는 V11 제로베이스 재집필과 UPDATE로 동일 절차가 실제 반복되는지 확인. 같은 원고의 v1~v3 수정본을 독립 성공 사례로 중복 계산하지 않음.

## 5. 갱신 규칙

작업 완료 때 **현재 파일·승인/REVIEW·남은 범위·다음 1~3개만 교체**한다. 세부 변경/테스트 기록은 Git 커밋과 [사례집](QUALITY_GENERALIZATION_CASEBOOK.md)에 보존하고 여기에 버전별 장문을 누적하지 않는다. 현재 제품을 변경하지 않은 문서 정비는 **HTML 제품 버전을 올리지 않는다**.
