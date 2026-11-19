# ROTATION TEXTBOOK — 현재 제품·REVIEW·다음 작업

> **Rolling 현황 정본 · 2026-11-19 KST.** 이 파일은 버전별 일지가 아니다. 이전 상세 Q0/Q1·Q3/Q4 및 연구 검증 수치는 [정비 직전 전체 상태](https://github.com/degong2-code/wow-rotation-engine/blob/f989fbd3205949bae141078829fb60a86328ca72/docs/CURRENT_STATE.md)와 기존 Git 이력·[사례집](QUALITY_GENERALIZATION_CASEBOOK.md)에 보존한다. 이 표의 과거 실측 SHA는 **새 채팅의 실제 파일 접근 증거가 아니다**.

## 1. 현재 GitHub 기준

- 공개 저장소: `degong2-code/wow-rotation-engine`.
- 작업 브랜치: `work/chat-first-talent-visibility-spell-media-20261114` / [PR #24](https://github.com/degong2-code/wow-rotation-engine/pull/24) **Draft·미병합**, base `work/chat-first-generic-html-assembly-20261113` (**main 아님**).
- HEAD·활성 PR·base·CI는 **매 작업에서 실제 GitHub를 재조회**하며 이 파일의 날짜/과거 로그로 대체하지 않는다. 사용자 승인 없이 main 변경·병합·공개 배포 금지.

## 2. 개인 Library 제품 — 마지막 실측 기록

> **2026-11-19 실물 검증:** 통합 V88·악마 v11·기존 V11·고통 V82·악마 원문을 비교하고, 신규 **악마 독립 v12를 Library에 저장한 다음 재취득하여 크기·SHA-256을 실제 확인**했다. 매 새 채팅에서 실물 접근과 해시를 다시 검증한다.

| 역할 / 상태 | Library 위치 및 ID | 기록된 실제 바이트·SHA-256 |
|---|---|---|
| **통합 V88** · 14개 전문화, **디자인 일부 선호 확인·전체 REVIEW** | `/ROTATION TEXTBOOK/wow_rotation_v83_fury_editorial_v88_no_cell_shading_REVIEW.html` · `libfile_1c87d86e0b048191a7ee46bc6b093fc1` | **2,629,547B** · `1c817f1f8896b111f18be367fe879aa09214e6ecd4e450afa399a6443efbd236` |
| **악마 흑마법사 독립 v12** · 15번째 후보, 미통합, **표 여백·아이콘·심화 내용 보완 / Q3·전체 Q0/Q1 REVIEW** | `/ROTATION TEXTBOOK/wow_rotation_demonology_1215_table_content_v12_REVIEW.html` · `libfile_d0e0df6403cc81918f1b7322bcd394e1` | **116,250B** · `3f8409f60a07c397d1421120302d7387106ad013008a6abdecffc2d336369893` |
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
| **Gate A** | 실제 12.1.5 개인 WHML 원문 확보 상태 유지(영웅 2·우선순위 4×8·오프너 17/18 타임라인 표식). 악마학자 시각 타임라인 `264187`은 **부식성 물(Corrosive Waters) 주문 ID 오기**이고 산문 `[spell=264178]`은 악마 화살과 일치해 **v10의 선시전 기술명은 그대로 유지**. 미정의 `Trick-Op`는 영혼수확자 오프너 소개 문구에만 쓰임, 실제 오프너/우선순위는 별도 `soul-harvester` 표시. `NotesHighlight`는 공통 hover 안내 참조; 새로운 명시 행동을 함부로 추론하지 않음 |
| **Q0/Q1** | 이전 v11에서 해결된 **영혼의 조각 3개→굴단의 손을 아르거스의 지배자 종료까지 동적 반복**·영혼수확자 야생 임프 2마리 선준비 유지. v12는 같은 12.1.5 저장 원문을 다시 대조해 **군림하는 폭군 선택 시 공포사냥개 지속시간 연장**, **악마의 핵 평소 2중첩 비축**, **임프 군주 소환 시 자체 해제/쿨 중 마법 태우기**를 기존 심화에 보강. 저장 와우헤드의 지옥 유린자 주문 차단 구문은 **블리자드 12.0.5 공식 변경**과 충돌하므로 기존의 마법 해제·마법 삼키기 정정을 보존. 공포사냥개 선소환은 기계적 필수 조건이 아닌 폭군 강화·특성 효과 정렬로 설명. **전체 전문화 Q0/Q1 최종 승인 아님** |
| **Q2/Q3** | 사용자 **악마 v11 '가독성 좋아'** 평가 수용. v12는 `table-shell` 안 표 자체의 아래쪽 20px 여백 및 다음 오프너의 겹친 구분선을 제거해 **빈 행처럼 보이는 띠**를 수정. 실제 빈 `<tr>`는 0개였으며 단일 상세 조건 공란 2개를 작은 `—`(접근성 라벨 '추가 조건 없음')로 표시. 고통 V82·통합 V88·V11과 내용 역할을 대조하여 장/표 수 강제 복제 없이 기존 심화에서 필요한 판단만 추가. **850px Chromium 실제 화면 시각 확인, 320/390px v12 실제 화면·사용자 최종 Q3는 REVIEW** |
| **Q4** | v12 vs v11 정적 비교: **4개 상세 우선순위×8행/2개 빠른표/영웅별 실제 오프너 흐름·전투 전 준비·오프너 설명 동일**. 6개 표의 행 수 `[3,3,9,9,9,9]` 그대로, 아이콘 없는 기술 표시 **11곳(지옥 유린자)**를 실제 저장 WHML 확인 아이콘으로 연결하여 **138/138 표시 skill 요소 아이콘 포함**, 툴팁·공통 JS 보존. 실제 Chromium **850px 영웅 전환 및 화면 1회 확인**, 후속 12상태 자동 브라우저 재실행은 환경 타임아웃으로 완료하지 못했으므로 **v12 Q4 전체 PASS 주장 금지**. 이전 v11 12상태 PASS는 과거 기록이며 CDN 실응답·실기기·`file://` 미검증. 통합 V88 무변경 |

**현재 기준 문서:** [PLAYBOOK](CHAT_FIRST_PLAYBOOK.md) §0의 작업 선택·§0.1의 **필수 참조 라우팅**. 신규 CREATE·원문 UPDATE는 웹 텍스트만 읽고 사용자에게 저장본 여러 개를 바로 요청하지 않는다. 기존 HTTP→WHML→필요 시 정상 브라우저 경로를 먼저 확인·가능하면 실행한다. **코드 존재/실행/원문 취득/게임 판단 승인**은 서로 다르다.

## 4. 다음 1~3개 제품 작업 — `진행` 단독 요청의 기준

1. **악마 독립 v12 모바일·동폭 Q3/Q4 마무리:** 실제 320/390px에서 표 하단 여백·조건 `—`·새 지옥 유린자 아이콘의 정렬/줄바꿈을 통합 V88·고통 V82와 비교하고, 두 영웅 전환·툴팁·오프너·가로 넘침/JS를 다시 점검. 사용자의 'v11 가독성 좋아'는 v12 전체 승인으로 승격하지 않음.
2. **다른 전문화에서 반복 제작 실증:** 신규 독립 CREATE, 기존 V11 제로베이스 집필 또는 원문 UPDATE로 원문 Gate A→조건 Q0/Q1→교본 Q2/Q3→HTML Q4를 재현. 악마 v1~v12 수정 이력을 독립 성공 제품 수로 중복 계산하지 않음.
3. **악마 통합 승인 여부:** v12의 모바일 Q3 및 전문화 전체 Q0/Q1 남은 REVIEW 정리 후 사용자가 승인하면 통합 V88에 15번째 전문화로 연결. 승인 전 기존 V88 14개와 독립 v12를 별도 보존.

## 5. 갱신 규칙

작업 완료 때 **현재 파일·승인/REVIEW·남은 범위·다음 1~3개만 교체**한다. 세부 변경/테스트 기록은 Git 커밋과 [사례집](QUALITY_GENERALIZATION_CASEBOOK.md)에 보존하고 여기에 버전별 장문을 누적하지 않는다. 현재 제품을 변경하지 않은 문서 정비는 **HTML 제품 버전을 올리지 않는다**.
