# SOURCE_ACQUISITION — 실제 공략 원문 확보 실행 경로

> **현행 Gate A 실행 지침.** 신규 CREATE/원문에 의존하는 UPDATE에서 [CHAT_FIRST_PLAYBOOK §0.1](CHAT_FIRST_PLAYBOOK.md)의 **필수 작업별 경로**로 읽는다. 과거 날짜별 연구와 세부 반례는 [정리 전 원문 전체](https://github.com/degong2-code/wow-rotation-engine/blob/592574080fcf6cd6d0a89906c8ffff25dda69363/docs/SOURCE_ACQUISITION.md) 및 아래 증거 문서·Git 이력에 보존. 이 파일에 버전별 장문 결과를 계속 추가하지 않는다.

## 1. 기본 원칙 — 웹 텍스트 누락을 원문 부재로 오인하지 않는다

1. 사용자 지정 출처 우선. 없으면 **현재 패치·해당 전문화의 Wowhead 공략 한 개**를 기준 원문으로 정하고 **실제로 반환된 페이지의 표시 패치/수정일/제목**을 확인한다. 색인 날짜, 과거 같은 URL, PTR·라이브 서로 다른 개정판을 묵시적으로 섞지 않는다.
2. ChatGPT 웹 열람으로 확인 가능한 조건·우선순위·오프너·설명을 먼저 확인한다. 하지만 **선택형 본문·오프너 단계·툴팁이 안 보이면 실제로 없다는 뜻이 아니다**.
3. 다음으로 **기존 정상 HTTP→HTML 내장 WHML 수집/해석 경로**를 적용한다. 페이지 자체를 다운로드할 수 있는 환경이면 사용자 Ctrl+S를 요청하기 전에 이 경로를 시도한다.
4. 그래도 필요한 자료가 남으면 **정상 접근이 가능한 브라우저에서만** 동적 마스터 선택·하위 탭·관련 hover를 보조 확인한다. HTTP와 브라우저가 서로 다른 개정판이면 합치지 않는다.
5. 모든 정상 경로를 확인했는데도 부족하면 사용자에게 **가능한 최소 저장 HTML 1개부터** 요청한다. 그 메인 HTML에 모든 WHML·선택형 데이터가 들어 있는지를 **먼저 분석**한 뒤에야 추가 상태를 요청한다. `_files` 폴더나 4개 상태별 HTML을 무조건 요구하지 않는다.

## 2. 이미 있는 공통 코드 — 새 수집기 만들기 전에 실제 확인

| 기존 코드 | 책임 |
|---|---|
| `engine/spec_source_resolver.py` | 한글/영문 전문화명 → 정규 Wowhead URL (URL 존재/패치는 실제 요청 시 검증) |
| `engine/http_source_fetch.py` | 정상 HTTPS GET **1회**. 공개 User-Agent, 쿠키 복사·세션 가장·프록시 전환·차단 회피 없음 |
| `engine/source_acquisition_pipeline.py` | HTTP/허용된 브라우저/저장 HTML·ZIP → 정체성·선택·툴팁·누락 후보 감사 |
| `engine/embedded_markup.py` | HTML의 `WH.markup.printHtml(..., "guide-body")` 리터럴 안에 있는 `tabs`/`toggler`/`display-options`/툴팁·참조를 JS 실행 없이 추출 |
| `engine/source_editorial_packet.py` | WHML 전체/조건식/툴팁 정의·참조·원문 위치를 **비공개 집필 근거**로 보존 |
| `engine/live_dom_capture.py` | 렌더링이 실제 허용된 브라우저에서 상위·하위 선택과 hover 보조 확인 |
| `engine/source_structure.py` · `engine/source_coverage.py` | 확보한 후보·미방문 상태·툴팁 본문 누락의 **선택적** 감사; 미관측 실사이트 완전성 보증 아님 |

정상 HTTPS가 가능한 환경의 내부 예시(이 세션에서 실제 실행했는지는 **별도 보고**):

```bash
python -m engine.source_acquisition_pipeline \
  --specialization "악마 흑마법사" --allow-remote \
  --expected-patch 12.1.5 --min-updated 2026-10-13 \
  --output /private/rotation-source-demonology
```

원문 HTML/WHML을 먼저 확보한 뒤 **필요할 때만** `--capture-ui` 옵션으로 정상 브라우저를 보조 사용한다. 브라우저와 HTTP의 개정판/SHA가 다르면 동적 관측을 현재 WHML에 연결하지 않는다. 실제 실행 결과가 없으면 해당 명령이 **구현되어 있다는 사실**과 **성공했다는 주장**을 구분한다.

개인용 `analysis.html`, `editorial-evidence-private.json` 등에 원문·툴팁이 있을 수 있으므로 **공개 GitHub/Actions Artifact에 올리지 않는다**. 상세 입출력·보안은 [AUTO_PAGE_ACQUISITION](AUTO_PAGE_ACQUISITION.md), [SPECIALIZATION_ONLY_ACQUISITION](SPECIALIZATION_ONLY_ACQUISITION_20261112.md).

## 3. 선택형·접힌 원문 확인 — Gate A 필수 범위

- 각 영웅·단일/광역·선택 특성·쿨다운·전투 전/오프너의 **유효한 상위→하위 선택 경로**와 실제 행동/수치/조건을 확보. 표시된 선택 옵션을 무조건 서로 독립 곱셈하지 않는다.
- `[display-option]`/`[display-options]`는 **화면 표시 조건**이다. 해당 표시가 실제 기술·시점·선시전을 바꾸는지 원문 본문과 대조한 뒤에만 게임 결정 분기로 해석한다.
- 관련 `?`·hover·`tooltip`/`tooltip2`의 **실제 본문 전수**와 가능한 위치(선택/섹션/인접 기술) 단서를 수집. 정의·참조·미정의·미사용을 구분. **정확한 모든 행 ID 귀속은 Gate A 필수 요건이 아니며**, 행동이 달라지는 중요한 모호함에서만 원시 연결을 더 조사한다.
- 오프너 제목/Notes만 보이면 `[rotation-timeline]`/`[rt-step]`/`[rt-half-step]` 등의 원본 여부를 조사. `rt-step`을 확정된 **1 GCD**나 실제 시전 기술로 자동 단정하지 않는다. 기술 ID·효과/버프 ID와 Notes가 충돌하면 해당 판단만 REVIEW.
- **`[rt-branch]` 보존:** 내부 여러 `[rt-step]`이 항상 순서대로 모두 시전해야 하는 행동이라는 가정 금지. 같은 묶음의 선택/조건부 표식을 유지하고, 별도 오프너 산문·타임라인 사이의 **기술 ID·반복 횟수 불일치**는 임의로 통합하지 않고 각각 출처를 남긴다. 옛 시즌 물약/장신구 아이템 ID도 현재 권장품으로 단정하지 않는다(악마 12.1.5 실증).
- 소비재는 **실제 행동 순서·선시전·사용 시점이 달라질 때만** 오프너를 분리한다. 선택된 물약을 여러 개 연속 사용하게 만들지 않는다. 행동이 같다면 공통 '물약 사용' 슬롯으로 요약.
- **Gate A는 자료 본문/상태 완전성**, **Q0/Q1은 원문 의미·다음 행동 판단 정확성**. 본문 자체 누락=Gate A 미완료/FAIL(부분 결과는 REVIEW), 본문 확보했으나 의미/귀속 모호=Q0/Q1 REVIEW. Q4나 원문 수치 개수로 이를 대체하지 않는다.

## 4. 실패·사용자 요청 전 반드시 구분할 것

| 관측 | 올바른 판정·다음 단계 |
|---|---|
| 웹 텍스트에 선택/툴팁/타임라인 없음 | **원문 부재로 판정 금지**. 실제 HTML 내장 `guide-body` 먼저 조사 |
| 정상 HTTP HTML 200이지만 `guide-body` 없음 | 다른 정적 데이터·DOM·내장 JSON 검토. 성공 추정 금지 |
| 직접 HTTPS **DNS 실패** | HTTP 응답 없음. **403이라고 기록 금지**. 과거 Actions 성공과 이번 환경 실패는 공존 가능 |
| 요청별 HTTP **403/429** | 해당 요청 중단, 우회 금지. 다른 합법 경로/이전에 확보된 같은 패치 원문 확인 |
| 같은 URL의 웹/HTTP/브라우저에서 패치·수정일 불일치 | 서로 다른 개정 원문 병합 금지. 최신성/선택 귀속 REVIEW |
| 현재 환경에서 기존 코드를 실행할 수 없음 | **코드 미실행**으로 명시; 가능한 정상 자료 경로만 사용. 수동 요청을 처음부터 기본값으로 삼지 않음 |

**사용자에게 자료를 요청할 경우:** '어느 URL/패치의 어떤 원문 상태 또는 본문이 부족한지'를 정확히 안내. **메인 HTML 하나를 먼저 분석**, 실제 그 안에 없는 내용만 추가 요청한다. 사용자 저장본도 패치·파일 크기·SHA를 확인하고 비공개로 처리한다.

## 5. 당시 실증 — 현행 방법을 빠뜨리지 않기 위한 참조

- [고양 12.1.5 저장본 실제 구조](ENHANCEMENT_SAVED_HTML_EVIDENCE_20261112.md): 메인 HTML 한 개 내 WHML **68,350자**, tooltip 정의 **44**, 선택 정의 **16**, 조건 표시 **82**. 원시 HTML에는 있지만 렌더링 DOM의 빈 tooltip 템플릿만 보면 누락되는 반례. 물약 선택에 따라 4개 오프너가 **12개 유효 행동 상태**로 달라짐.
- [HTTP 직접 취득 및 선택형 분석](AUTO_PAGE_ACQUISITION.md): 정상 HTTP로 동일 고양 WHML 본문 SHA가 사용자 저장본과 일치했던 **과거 환경의 실증**; 현재 환경의 성공을 보증하지 않음.
- [분노 오프너 타임라인 복원](FURY_OPENER_SOURCE_20261116.md): 웹 텍스트에 없던 **4개×10 단계**와 `rt-half-step` 6개를 기존 WHML 경로로 확인.
- [2026-11-16 환경별 재현성](SOURCE_ACQUISITION_REPRO_20261116.md): Actions HTTP 성공 ↔ 일반 채팅 Python DNS 실패. 도구 부재/접근 실패/원문 부재를 구분.
- [원문 범위 감사](SOURCE_COVERAGE_AUDIT.md), [정상 접근시 실제 DOM 보조](LIVE_DOM_CAPTURE.md): 필요할 때만 사용. 감사/합성 테스트 PASS는 실사이트 전체 PASS가 아님.

**유지:** 새로운 전문화에서 근거 없는 게임 조건을 만들지 않되, **기존 연구·코드를 먼저 재사용한 증거 없이 '원문에 없다/사용자가 저장해야 한다'고 말하지 않는다**. 반복된 병목이 기존 경로로 해결되지 않는 경우에만 기존 도구 자체를 보완한다.
