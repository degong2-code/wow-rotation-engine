# 원문 확보 3경로 재현성 — 고양 주술사 (2026-11-16)

> 이 문서는 실제 일반 ChatGPT 채팅의 경로별 접근성과 2026-11-12 과거 실증을 **분리**해 기록한다. 신규 크롤러·독립 AI 엔진 개발의 근거로 사용하지 않는다.

## 기준

- 기준: [Wowhead 고양 주술사 Rotation](https://www.wowhead.com/guide/classes/shaman/enhancement/rotation-cooldowns-pve-dps), **12.1.5 / wordup / 2026-10-13**.
- 대상: 폭풍인도자 / 토템술사 × 단일 / 광역 = **4개 우선순위(9+10+12+12=43행)**, 기본 오프너 4종, **물약 3선택에 따른 실제 행동·시점이 달라지는 12개 상태**와 관련 tooltip·접힘. 상위 옵션이 다른 상태를 한 시퀀스로 합치지 않는다.
- 역사적 비교: [저장본 실제 구조 검증](ENHANCEMENT_SAVED_HTML_EVIDENCE_20261112.md), [전문화명 기반 HTTP 실증](SPECIALIZATION_ONLY_ACQUISITION_20261112.md).

## 이번 세션의 세 경로 실측

| 경로 | 실행 결과 | 판정 |
|---|---|---|
| A. ChatGPT 직접 웹 열람 | URL 직접 조회 성공. **446줄로 표시된 페이지 텍스트**에서 패치·수정일·영웅 2종의 단일/광역 4개 우선순위 및 기본 오프너 4종과 주요 노트를 확인. Potion 세 선택지의 **이름**은 나타나지만, 실제 12개 시전 시점·선시전 분기의 조건부 원문 및 tooltip 정의↔참조 관계는 동등한 정확도로 추출되지 않음. | **부분 확보 / Gate A REVIEW** |
| B. 현재 Python HTTPS GET | 일반 requests로 직접 요청했으나 **www.wowhead.com DNS 조회 실패(NameResolutionError)**. HTTP 응답이 없으므로 이것을 403으로 기록하지 않음. | **현재 실행 환경 BLOCKED** |
| C. 사용자 저장 HTML/ZIP | 현재 대화에 자동 탑재된 첨부·개인 Library를 확인했지만 과거 사용자가 저장한 **실제 Wowhead 원본 ZIP/HTML 바이트를 다시 확보하지 못함**. 당시 파일 구조와 해시를 기록한 GitHub 문서는 조회 가능. | **과거 실증 존재 / 현재 실물 미검증** |

## 2026-11-12 과거 독립 실증 — 오늘 실행으로 둔갑시키지 말 것

- 사용자 저장 메인 HTML **839,307B**, SHA256 **d05d86b5db57b012373293ba5bae8b7c1f4b1e7711da29b3944df8b0ef5ea755**.
- 인라인 WHML 본문 **68,350자**, SHA256 **6657591171c36c79797b739b2248e37b9d967094e7d33e8dd799293283bd5dbe**.
- 구조: **툴팁 정의 44개, 참조 45회(고유 42종), 선택지 16개, 조건부 표시 82회, 접힘 7개, 우선순위 43행**. 빈 렌더링 템플릿만 보고 '툴팁 없음'이라고 판정하면 안 된다. **WH.markup.printHtml 내부 guide-body**에 실제 툴팁 원문이 포함됐다.
- 물약 세 선택이 4개 오프너 각각에서 **실제 사용 시점·선시전 조건**을 바꾸는 사례가 있었다. 단순 '물약 사용' 4개 오프너로 전부 압축하면 실제 원문 조건이 사라진다. 반면 물약 이름만으로 행동 차이가 없는 다른 전문화에 12개 분기를 강제하면 안 된다.
- [GitHub Actions: 전문화 입력→원문](https://github.com/degong2-code/wow-rotation-engine/actions/runs/43181759158) 및 [GitHub Actions: 비공개 집필 패킷](https://github.com/degong2-code/wow-rotation-engine/actions/runs/43182698012)의 **2026-11-12 diagnostic 성공 기록을 2026-11-16 커넥터로 재조회**. 실제 로그에 enhancement_status=guide_identity_confirmed, enhancement_guide_body_characters=68350, enhancement_named_tooltips=44, enhancement_choice_definitions=16, enhancement_modified_date=2026-10-13, enhancement_visible_patches=12.1.5, enhancement_same_user_saved_body=true 확인.
- **같은 로그에 enhancement_current_patch_verified=false도 있음.** 이는 당시의 실제 HTML 본문/저장본 SHA 일치 근거일 뿐, 지금의 라이브 패치 완전 검증·선택별 실사이트 전수·Q0/Q1 정확성의 PASS가 아니다.
- 2026-11-12 Actions 실행 환경에서 HTTP 취득 성공한 사실과 2026-11-16 이 채팅 실행 환경에서 DNS 실패한 사실은 **환경이 달라 모순이 아님**.

## 새 시즌 CREATE/UPDATE에 적용할 결정 순서

1. **웹 열람 먼저:** 최신 패치·작성자·날짜·전문화·영웅/단일/광역을 확인하고, 펼침·선택형·tooltip의 원시 조건까지 읽혔는지 평가한다. 기본 시퀀스와 옵션 이름이 보인다는 이유만으로 Gate A PASS 처리하지 않는다.
2. **부족하면 기존 수집 경로:** 정상 접근 가능한 환경에서 이미 구축된 engine/spec_source_resolver.py, engine/http_source_fetch.py, engine/source_acquisition_pipeline.py 및 source_editorial_packet.py 활용. 실제 HTML/WHML과 패치 정체성·선택/tooltip 참조를 확인한다. 현재 실행 환경 DNS·403·429 등은 각각 구분하고 회피하지 않는다.
3. **그래도 부족하면 사용자 저장 자료:** HTML/ZIP/MHTML이 이미 사용자에게 있다면 해당 원본만 받아 검증. 저장 HTML 자체에 선택 상태가 포함돼 있는지 먼저 확인하고, 없는 경우 필요한 특정 상태만 최소 요청. 오래된 저장본을 새 시즌 최신이라고 추정하지 않는다.
4. **원문 완전성/게임 판단 분리:** 원문 부족 시 실제 확인된 것만 기반으로 REVIEW 초안을 제공하며 보이지 않는 선택 상태를 상상하지 않는다.
5. **새 추출기 추가는 보류:** 동일 결함이 반복되고 기존 웹·정형 수집·사용자 자료를 모두 활용해도 해결이 안 될 때에만 최소 보수를 검토.

## 결과

이번 작업은 **원문 취득 정책·재현성 점검**이며 제품 **V57 HTML은 변경하지 않았다**. 이 경로 테스트의 핵심 품질 지표는 HTTP 200, 페이지 열림, 텍스트 줄 수가 아니라 **해당 패치 실제 선택 상태별 행동·사용 시점·tooltip을 정확한 조건과 함께 확보했는가**이다.
