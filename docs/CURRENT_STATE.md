# ROTATION TEXTBOOK — 현재 제품·REVIEW·다음 작업

> **Rolling 현황 정본 · 2026-11-18 KST.** 이 파일은 버전별 일지가 아니다. 이전 상세 Q0/Q1·Q3/Q4 및 연구 검증 수치는 [정비 직전 전체 상태](https://github.com/degong2-code/wow-rotation-engine/blob/f989fbd3205949bae141078829fb60a86328ca72/docs/CURRENT_STATE.md)와 기존 Git 이력·[사례집](QUALITY_GENERALIZATION_CASEBOOK.md)에 보존한다. 이 표의 과거 실측 SHA는 **새 채팅의 실제 파일 접근 증거가 아니다**.

## 1. 현재 GitHub 기준

- 공개 저장소: `degong2-code/wow-rotation-engine`.
- 작업 브랜치: `work/chat-first-talent-visibility-spell-media-20261114` / [PR #24](https://github.com/degong2-code/wow-rotation-engine/pull/24) **Draft·미병합**, base `work/chat-first-generic-html-assembly-20261113` (**main 아님**).
- HEAD·활성 PR·base·CI는 **매 작업에서 실제 GitHub를 재조회**하며 이 파일의 날짜/과거 로그로 대체하지 않는다. 사용자 승인 없이 main 변경·병합·공개 배포 금지.

## 2. 개인 Library 제품 — 마지막 실측 기록

> **2026-11-18 실물 검증:** 통합 V88·독립 악마 v10·V11 원본·고통 V82·악마 원문 저장본의 바이트·SHA를 재확인했으며, 이번 교정 후 **독립 악마 v11을 Library에 새로 저장하고 다시 파일을 취득해 동일 SHA 검증**했다. 다음 채팅에서도 실물 재확인은 필요하다.

| 역할 / 상태 | Library 위치 및 ID | 기록된 실제 바이트·SHA-256 |
|---|---|---|
| **통합 V88** · 14개 전문화, **디자인 일부 선호 확인·전체 REVIEW** | `/ROTATION TEXTBOOK/wow_rotation_v83_fury_editorial_v88_no_cell_shading_REVIEW.html` · `libfile_1c87d86e0b048191a7ee46bc6b093fc1` | **2,629,547B** · `1c817f1f8896b111f18be367fe879aa09214e6ecd4e450afa399a6443efbd236` |
| **악마 흑마법사 독립 v11** · 15번째 후보, 미통합, **동적 반복 국소 Q0/Q1 교정·Q3 REVIEW** | `/ROTATION TEXTBOOK/wow_rotation_demonology_1215_opener_loop_q1_v11_REVIEW.html` · `libfile_4452eb6114588191a08465652e7781f9` | **110,196B** · `c191f937568aaa06a52c537d9bb6fe144f3bf6259765f6d88dc871ccdc664684` |
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
| **Q0/Q1** | **v11의 남은 국소 쟁점 판정:** 저장 WHML의 영혼수확자 시각 타임라인 `굴단의 손` 5회는 **표본/예시**이며, 오프너 산문은 고정 3회 뒤 `영혼의 조각 3개 모음 → 굴단의 손`을 **아르거스의 지배자 종료까지 동적 반복**하도록 지시. v10 마지막 굴단의 손이 필수 추가 고정 시전처럼 보이는 위험을 두 영웅 첫 화면의 마지막 단계 `cond` 2개를 추가해 교정했다. 악마학자 첫 2회·영혼수확자 첫 3회의 고정 굴단의 손과 선후 시전 순서는 그대로. 영혼수확자의 **야생 임프 2마리 확보 후 -5초 마력 착취**, 악마학자 원문 `264187` ID 오기/산문 `264178` 악마 화살 확인, 구 시즌 소비재 일반 슬롯도 보존. **횟수 해석 국소 쟁점은 해소, 전문화 전체 게임 Q0/Q1 최종 승인 아님** |
| **Q2/Q3** | v9에서 **사용자 호평**인 첫 화면 간결화 방향 보존. v11은 두 영웅 첫 화면 오프너의 마지막 `굴단의 손`에 `(영혼의 조각 3개 확보 후 / 아르거스의 지배자 종료까지 반복)` 조건을 직접 배치하고 바로 아래 중복 안내만 짧게 축약. 영웅별 전투 전 준비·악마의 핵 부재 예외는 유지. **v11 실제 사용자 동폭·모바일 Q3 및 전체 승인 미완료** |
| **Q4** | v11 vs v10: 첫 화면 2개 반복 조건 + 2개 안내문 외 우선순위·오프너 고정 기술/순서·상세 본문·아이콘 124개·툴팁/버튼·JS/CSS **동일**. Chromium `set_content` 외부 이미지/폰트 차단, 320/390/650/850/1180/1365px × 영웅 2개 **12상태 PASS**, 가로 넘침·JS 오류 0, 툴팁/ESC 확인. 실제 `file://`, CDN 실응답·모바일 실기기·전체 게임 Q0/Q1 미검증. 통합 V88 무변경 |

**현재 기준 문서:** [PLAYBOOK](CHAT_FIRST_PLAYBOOK.md) §0의 작업 선택·§0.1의 **필수 참조 라우팅**. 신규 CREATE·원문 UPDATE는 웹 텍스트만 읽고 사용자에게 저장본 여러 개를 바로 요청하지 않는다. 기존 HTTP→WHML→필요 시 정상 브라우저 경로를 먼저 확인·가능하면 실행한다. **코드 존재/실행/원문 취득/게임 판단 승인**은 서로 다르다.

## 4. 다음 1~3개 제품 작업 — `진행` 단독 요청의 기준

1. **악마 독립 v11 동폭·모바일 Q3 평가:** v9의 컴팩트한 빠른 우선순위와 새 반복 조건의 독해 흐름을 통합 V88·호평 고통 V82와 실제 850/320/390px 폭에서 비교. 야생 임프 2마리 사전 준비·아르거스의 지배자 종료 시점이 독자에게 명확한지 확인. Q4 PASS를 사용자 Q3 승인으로 승격하지 않음.
2. **반복 제작 품질 실증:** 새 전문화 독립 CREATE, 기존 V11 제로베이스 재집필 또는 원문 UPDATE로 동일한 원문/조건·행동/화면 기준을 재현. 같은 악마 원고 v1~v11 수정을 신규 성공 사례 11개로 계산하지 않음.
3. **악마 통합 여부 검토:** v11 Q3 및 나머지 전문화 전반의 Q0/Q1 승인 범위를 확정한 뒤, 사용자 검토 하에 V88의 15번째 전문화로 통합할지 결정. 승인 전 통합 14개와 독립 v11을 보존.

## 5. 갱신 규칙

작업 완료 때 **현재 파일·승인/REVIEW·남은 범위·다음 1~3개만 교체**한다. 세부 변경/테스트 기록은 Git 커밋과 [사례집](QUALITY_GENERALIZATION_CASEBOOK.md)에 보존하고 여기에 버전별 장문을 누적하지 않는다. 현재 제품을 변경하지 않은 문서 정비는 **HTML 제품 버전을 올리지 않는다**.
