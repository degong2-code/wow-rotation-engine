# ROTATION TEXTBOOK — 현재 상태 (rolling state)

> **최신 상태를 갱신하는 유일한 GitHub 파일.** 2026-11-16 KST 기준 체크포인트. 이 문서에 적힌 GitHub SHA/Actions 상태는 기록 시점의 사실일 뿐, 새 채팅에서는 **실제 원격 조회가 우선**한다. 오래된 HANDOFF_*.md 및 과거 버전 파일의 "최신" 표시는 역사 기록이다.

## 2026-11-16 V48 냉기 마법사 내용 보완 — 단기 로드맵 1단계 진행

- **최신 개인 통합 결과물:** `wow_rotation_v11_frost_zero_base_v48_REVIEW.html`; 개인 Library `/ROTATION TEXTBOOK/wow_rotation_v11_frost_zero_base_v48_REVIEW.html`, ID **`libfile_08a82437e8088191a3282c027d6855ae`**; **1,590,892바이트**, SHA-256 **`8803cbbf1592b695a815acbe113297d93e91ee1d60989dd59f1ea92867c3d23d`**. 원본 V46은 별도 보존, V48이 최신 **REVIEW**. 사용자 확정 '괄호 안 작은/옅은 조건' UI 보존.
- **독립 냉기 마법사 v4:** `wow_rotation_frost_independent_1215_v4_content_REVIEW.html`; 개인 Library `/ROTATION TEXTBOOK/wow_rotation_frost_independent_1215_v4_content_REVIEW.html`, ID **`libfile_f4e3517f0d58819186dd3223d49b72e2`**; **186,532바이트**, SHA-256 **`d63e170fdb5ee0124f82a92e9534011a61ccd48a9338544f8021c037b3c04ca5`**.
- **원문 근거:** 동일 저자 Dorovon의 [와우헤드 냉기 12.1.5 2026-10-13 딜사이클](https://www.wowhead.com/guide/classes/mage/frost/rotation-cooldowns-pve-dps) + [냉기 UI·매크로](https://www.wowhead.com/guide/classes/mage/frost/addons-macro-ui-imports)(매크로에만 사용). V11 원본(사후 비교)에는 주시/마우스오버, 오라 취소, 커서 시전 4종 매크로가 있었으나 독립 v2에서는 빠졌음. 현재 매크로 공략을 별도로 확인한 다음 선택형 4종을 **접어서 기본 화면을 길게 만들지 않고** 복원. 원문 및 V11의 고드름 5개→혹한의 쐐기, 두뇌 빙결→열기 동공, 서리의 손가락 1/2중첩, 서리 광선 전투 종료/집중 공격 타이밍 해설을 보강. 실게임에서 한국어 매크로 구문 실행 결과는 **REVIEW**.
- **우선순위 조건 정리:** 서리불꽃 광역 `눈보라`의 `빗발치는 냉기 특성 선택 / 효과 발동`은 이미 발동 효과로 선택 여부를 증명하므로 `빗발치는 냉기 발동`으로 첫 화면/상세 동시에 단순화. **42개 행동 이름/순서와 16개 오프너 단계 원형 유지**. 현재 와우헤드 4표 9+11+10+12 총 42행. V46 대비 상세 조건 변화는 **서리불꽃 광역 7번 1행뿐**. 원래의 검증 중인 게임 사실을 신규 확정으로 둔갑시키지 않음.
- **Q4 실물:** 정적 비교에서 **다른 9개 전문화 `.manual-view` HTML DOM 완전 동일**, 공통 JS 12개 원형 동일. 독립·통합 HTML **320/390/900/1365px × 주문술사/서리불꽃** 실제 Chromium: 영웅 전환, 20/22행 표시, 첫 화면↔상세 42쌍 조건 동일, 16 오프너, 매크로 접기 펼치기, JavaScript 오류·가로 넘침 **0** PASS. **Gate A 동적 영웅/접힘/도움말 전수·Q0/Q1 전체 게임 판단 및 사용자 최종 콘텐츠 승인은 여전히 REVIEW**.
- **다음 작업:** 냉기 12.1.5 원문 선택형 콘텐츠 중 실제 행동을 바꾸는 미확정 사항이 추가 확보되지 않으면 리뷰 상태를 명확히 두고 종료. [ROADMAP_CHAT_FIRST](ROADMAP_CHAT_FIRST.md)의 **사격 사냥꾼 제로베이스 CREATE → V11 사후 비교**로 이동. 미시 검사기 신규 개발로 후퇴하지 않는다.

## 2026-11-16 문서 구조 정비 결과

- **신규 단일 진입/정본:** [PROJECT_CANON](PROJECT_CANON.md)(정체성/역할/문서 우선순위), **이 CURRENT_STATE**(유일한 최신 상태), [ROADMAP_CHAT_FIRST](ROADMAP_CHAT_FIRST.md)(개발 순서·원문 확보·AI/비AI), [HANDOFF_PROTOCOL](HANDOFF_PROTOCOL.md)(채팅 복원/인계).
- **기존 문서 정비:** README/AGENTS를 새 진입 링크로 교체, [CHAT_FIRST_PROJECT_INSTRUCTIONS](CHAT_FIRST_PROJECT_INSTRUCTIONS.md)를 실제 ChatGPT 프로젝트 지침에 복사하기 쉬운 내용으로 갱신, QUALITY_FIRST_POLICY/CHAT_FIRST_PLAYBOOK의 오래된 시작 경로·7→8개 고정 판정 수정.
- **실질적 충돌 해결:** SOURCE_ACQUISITION의 '물약은 분기 안 한다'와 실제 선택에 따른 오프너 변화 보존 원칙을 **행동·시점 변화 기준**으로 통일. 이전 인계 문서 3개는 내용 삭제 없이 **역사 기록 표지** 추가.
- **검증 범위:** GitHub 문서 경로가 존재하는지 및 상대 링크 검사, CI(문서 변경). **실제 비공개 교본 V46 자체는 이번 문서 구조 정비 과정에서 수정하지 않음.** GitHub 정리는 게임 Q0/Q1 검증이 아니다.
- **사용자 수동 설정 필요:** GitHub 커밋은 ChatGPT 프로젝트의 지침을 자동 갱신하지 않는다. 프로젝트 → ••• → 프로젝트 설정의 지침 내용을 [CHAT_FIRST_PROJECT_INSTRUCTIONS](CHAT_FIRST_PROJECT_INSTRUCTIONS.md)의 **복사할 내용**으로 등록/병합해야 새 일반 채팅에 처음부터 유효하다.

## 0. 무엇을 만들고 있는가

**GitHub 제작 지식 + 해당 시즌 Wowhead/사용자 원문 → ChatGPT의 게임 판단 해석·한국어 집필 → V11 이상 단일 HTML CREATE/UPDATE.** 독립 AI API 앱이나 자동 CI 뷰어는 최종 제품이 아니다. [PROJECT_CANON](PROJECT_CANON.md) 참조.

## 1. GitHub 실제 작업 지점

- 저장소: **degong2-code/wow-rotation-engine** (공개; 비공개 원문/완성 HTML 업로드 금지).
- 활성 작업 브랜치(2026-11-16 확인): **work/chat-first-talent-visibility-spell-media-20261114**.
- 현재 협업 PR: **#24 Draft / open / 미병합**. PR base: **work/chat-first-generic-html-assembly-20261113**, main 직접 대상 아님.
- 문서 구조 개편 이전 HEAD(2026-11-16 조회): **0f6cbf33796b12fbbef272bdc2794a2525496ae5**; 해당 커밋 Actions **completed/success**. **이 문서를 만드는 동안 새 커밋이 발생했으므로 이 SHA를 현재 HEAD로 쓰지 말 것.** 새 채팅은 PR HEAD와 연결된 Actions 재조회. 승인 없는 PR ready/merge, main 변경, Pages 공개 배포 금지.

## 2. 비공개 교본 제품 — 승인 경계

| 구분 | 개인 파일 및 Library 경로 | 크기·SHA-256 | 상태 |
|---|---|---|---|
| **V11 비교 기준 7개 원본** | wow_rotation_manual_engine_v2.html (개인 자료; GitHub 미게시) | 898,297B / 5d70279c4dd073eccef1f3b13565a8f555cd81c9f0a5b7eda7e3485e410742be | 역사적 UX·게임 콘텐츠 품질 기준. 새 패치의 정답으로 자동 승격 불가 |
| **현재 최신 통합 검토본 V46** | /ROTATION TEXTBOOK/wow_rotation_v11_frost_zero_base_v46_REVIEW.html; Library ID **libfile_16f7073754988191b1f9d977fdf4b8db** | 1,583,685B / 5b8a856bb7ef74d86ffce8b3d341770b18b605b463a40c145237be18ad2c3525 | **10개 전문화 통합 REVIEW.** 사용자가 "괄호 있는 조건 표현" 디자인을 기본값으로 선택했으나 전체 게임 판단/게시 최종 승인 아님 |
| 냉기 마법사 제로베이스 독립본 v2 | /ROTATION TEXTBOOK/wow_rotation_frost_independent_1215_v2_REVIEW.html; Library ID **libfile_0f959497fcfc8191ab6079cb2106c53a** | 179,362B / d46022e94c188728d86d3cda163545438c93a7c53165ab5567c0feee45b32cce | V11 냉기 42개 상세 우선순위의 **행동·순서 42/42 재현**, 전체 내용 완전성 REVIEW |
| 고양 주술사 신규 CREATE 기준본 V44 | /ROTATION TEXTBOOK/wow_rotation_v11_enhancement_minimal_conditions_v44_REVIEW.html; Library ID **libfile_42bb3ea5f3c48191b9ef0b6fa3f9703b** | 1,556,713B / 7935f0441b460df27a1e438fc9eecd1cc8187210ea4cd522ee0d2ca7b054f380 | 원문 단일 기준 출처, 우선순위 간결화 적용. Q0/Q1 동적 옵션·툴팁 REVIEW |

- 통합 V46의 **10개 전문화**: 화염·냉기·비전 마법사, 냉기 죽음의 기사, 사격·야수 사냥꾼, 잠행·암살 도적, 조화 드루이드, 고양 주술사.
- V46은 V44에서 **냉기 마법사 1개**를 독립 재집필본으로 교체한 비교용 통합 사본이다. **다른 9개 전문화 DOM 원형 보존**. 독립 냉기 V1/V2와 통합 V45/V46는 원본 V11과 분리 보존.
- **V47은 괄호만 제거한 비채택 비교본**이며, 이름의 버전 숫자가 더 크다고 최신 승인 디자인인 것은 아니다. 차기 작업의 UI 기본값은 **V46(기술명 강조, 조건은 괄호 + 작은 글씨 + 옅은 색, 조건 아이콘 축소)**.
- V41의 왼쪽 메뉴 노치 포인터, 영문명 한글명과 같은 행, 가운데 짧은 직업 구분선은 V46 공통 UI에 유지되도록 확인한 범위에서 사용한다.
- **원본과 결과물은 개인 Library에서 매 새 채팅 실제로 다시 열어보고 크기/SHA 검증 필요.** 이 문서의 해시를 실제 접근 성공의 증명으로 혼동하지 말 것.

## 3. 현재까지 입증된 것 / 입증되지 않은 것

**입증된 범위:**
- 고양 신규 CREATE V42→V44 실물, 원문 4개 우선순위의 44행 + 기본 오프너 4종, 기존 본문 보존, Chromium PC/모바일 영웅 메뉴 Q4 검사.
- 냉기 마법사 V11 게임 본문을 **재생성 초안의 입력으로 쓰지 않고** Wowhead 12.1.5/2026-10-13 원문으로 집필한 뒤 사후 비교: 4표 행동·순서 42/42.
- 냉기 독립 v2/V46의 **조건 괄호·옅은 색·작은 글씨**가 사용자에게 더 좋다고 선택됨.
- 조건의 **행동 결정 기여** 기준: 사용 가능·전제 특성·발동 여부 자체를 중복하지 않음, 다른 기술을 바꾸는 실질적 예외는 보존, 미정의 "강화 창 밖" 제거.

**아직 REVIEW:**
- 원문의 영웅/전투/소비 아이템/특성별 동적 선택, 접힌 내용과 모든 관련 ? 팁의 실제 원문 전수 확보.
- Blizzard 한국어 공식 주문 이름·아이콘 신원 전체, 시즌 변경에 대한 완전 대응.
- V11 냉기 원본의 매크로 4종, 심화·기술 사전 중 새 교본에서 유용하지만 빠진 자료의 평가/보완.
- 전체 Q0/Q1 실전 결정 정확성, 전 전문화 반복 제작성, V1 제품 승인.
- CI PASS는 저장소 정적·합성 검사 결과로만 기록. 게임 정답의 근거로 쓰지 말 것.

## 4. 바로 이어갈 작업 (정렬 순서)

1. **냉기 v2 / 통합 V46 내용 보완:** 같은 패치·원문에서 오프너/선택형/툴팁 누락 중 실제 행동을 바꾸는 사항 조사. V11의 유용한 매크로·기술 사전·심화 정보의 퇴보 여부 평가 후 필요한 것만 복원. 사용자 채택 UI 보존.
2. **사격 사냥꾼 제로베이스:** 새 소스만 보고 별도 교본 CREATE → 원본 V11 내용 사후 비교. 조건·오프너·예외·사용성/기술 ID를 대조하고 PASS/REVIEW 분리.
3. **잠행 도적 제로베이스 + 신규 전문화 1~2개 CREATE:** 서로 다른 게임 메커니즘에서도 재현 검증.
4. **기존 전문화 UPDATE 1회:** 원문 패치 변경을 반영하면서 비대상 본문·기능 보존.
5. [ROADMAP_CHAT_FIRST](ROADMAP_CHAT_FIRST.md)의 V1 합격 기준을 충족하면 검토·승인 후 정상 운영 전환. V11 나머지 7개 사후 재생성은 장기 심화 비교.

## 5. 매 인계에서 이 파일 갱신하는 원칙

- 날짜, **승인/REVIEW** 분리, 실제 마지막 파일 경로/크기/SHA/Library ID, 변경 범위, Gate A/Q0~Q4, 다음 1~3개 작업, 막힌 원문 자료를 **검증된 사실**로만 갱신.
- 별도 역사 문서는 이전 상태를 지우거나 이 문서를 가리키는 정본으로 승격하지 않는다.
- PR HEAD·CI를 조회한 시점을 적고 **파일 업데이트 커밋 이후는 HEAD가 바뀐다**는 점을 명시. 새 채팅에서 항상 재조회한다.
- 작업 전/종료 시 [HANDOFF_PROTOCOL](HANDOFF_PROTOCOL.md)의 체크리스트를 따른다. 위 업무는 사용자가 이후 다른 우선순위를 명시하면 즉시 재평가한다.
