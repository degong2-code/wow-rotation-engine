# 범용 원문 확보 감사 — 중첩 상태, 툴팁 본문, 위치 단서

이 문서는 개발 공통 보조 도구인 engine/source_coverage.py의 사용 범위를 정의한다. 목표는 웹사이트 UI를 복제하거나 독립 크롤러를 만드는 것이 아니라, **ChatGPT가 실제로 수집한 자료에서 중요한 누락을 발견**하는 것이다. 기존 V11 수준의 한글 교본은 계속 ChatGPT가 전문화 이름만 받아 집필한다. 사용자에게 JSON 입력을 요구하지 않는다.

## 입력 구조 (전문화 비종속)

- **guide:** 기준 전문화, URL, 실제 패치, 수정본 식별 정보
- **accesses:** 실제 접속 형태(rendered_ui/live_dom/page_html/search_index/user_supplied), URL, 패치, 수정본. 동일 URL이라도 패치·수정본이 어긋나면 검토 대상으로 분리
- **states:** 각 관측 상태의 선택 경로(path), 발견한 하위 선택(choices), 실제 본문 목록(entries), 조사 완결 여부(inventory_checked)
- **choices.role=decision:** 실제 기술 순서나 우선순위를 바꾸는 분기. 각 옵션에 대응하는 상태를 별도로 관측해야 한다. 상위 옵션을 바꾼 뒤 나타나는 새로운 하위 옵션도 같은 방법으로 추가한다.
- **choices.role=illustrative:** 물약 종류처럼 사용자·장비가 선택하는 **예시**. 그 옵션만으로 독립된 전체 오프너를 강제 생성하지 않는다. 실제 기술 순서를 변경한다는 근거가 있을 때만 좁은 예외를 조사한다.
- **entries:** 자유로운 항목 종류(kind: tooltip, priority, opener, notes, advanced, etc.), 식별자(id), 확보한 설명(text), 선택적 위치 단서(position: section/near/row 등)

**중요:** UI가 제공하는 모든 결정 축을 다루되, 한 상태에 하나의 decision 선택 축을 기록한다. 독립된 두 컨트롤이 동시에 있으면 하나를 먼저 분기하고 **분기된 자식 상태에서 다른 컨트롤을 재발견**한 것으로 기록한다. 실제 UI에 없는 조합을 임의로 만들지 않는다. decision/illustrative 구분은 원문과 게임 로직을 바탕으로 사람이/ChatGPT가 판단한다.

## 주요 검증

| 감지 항목 | 보고되는 결과 | 원칙 |
|---|---|---|
| 상위 선택 이후 특정 옵션 미방문 | unvisited_choice | 새로운 하위 선택을 다시 조사 |
| 실제 내용·툴팁 본문 누락 | missing_content | Gate A 내용 누락 |
| 해당 상태에서 항목 전수를 확인하지 않음 | inventory_not_checked | 전수 확인으로 주장하지 않음 |
| 오프너/Notes 등을 하나도 기록하지 않은 말단 상태 | empty_terminal_state | 화면 본문 재조사 |
| 출처 패치·수정본 불일치 | source_version_conflict | 다른 시점 자료 혼합 금지 |
| 부모 선택에 연결되지 않은 상태 | orphan_state | 임의로 조합 생성하지 않음 |
| 툴팁 본문은 있으나 정확한 위치를 모름 | tooltip_positions_unknown | **경고만**, 누락 처리하지 않음 |

관측 파일 안에 긴 원문을 담아 분석할 수 있어도, 감사 보고서에는 **문장 본문을 복제하지 않는다**. PUBLIC 저장소·Actions 아티팩트에는 실제 외부 공략의 장문 원문·원본 V11 HTML·비공개 교본을 올리지 않는다. 공개 파일은 완전한 합성 fixture뿐이다.

## 시험

    python -m engine.source_coverage --input examples/synthetic-source-coverage.json
    python -m unittest discover -s tests -p 'test_source_coverage.py' -v

예시 자료는 일부 선택 경로를 의도적으로 방문하지 않은 **합성 실패 데이터**다. 감사 보고서가 unvisited_choice와 inventory_not_checked를 검출하는지 CI에서 확인한다.

## 판정과 한계

- **declared_coverage_candidate=true:** 입력에 선언된 선택지와 항목 사이의 모순이 없다는 의미일 뿐이다. **사이트 전체를 직접 훑었다는 증거가 아니다.**
- **tooltip_positions_unknown:** 팁 본문은 확보했으나 표시 위치 단서가 없다는 뜻이다. 사용자의 합의대로 정확한 행/DOM ID 귀속을 Gate A에서 강제하지 않는다. 다의성이 실제 다음 행동을 바꾸는 경우에만 원본 관계를 추가 확인한다.
- **real_site_completeness_verified=false:** 코드가 알지 못하는 실사이트 숨김 콘텐츠는 자동 발견하지 못한다. 이 감사기로 Gate A의 독립적인 완전성 증명을 할 수는 없다.
- **gameplay_meaning_verified=false:** 어떤 기술을 왜·언제 사용하는지 게임 로직을 이 도구가 결정하지 않는다.
- **automatic_publish_allowed=false:** 이 도구의 자체 성공이 최종 교본·실전 최적화 승인으로 연결되지 않는다.

**반복 제작 경로:** 전문화명 입력 → ChatGPT가 기준 패치의 원문·모든 관련 선택형 콘텐츠·팁 본문을 확보 → 이 공통 감사기로 *선언된 선택 상태의 누락* 확인(필요한 경우) → ChatGPT의 상태/조건/행동/원인 분석 → 모순 및 근거 QA → 기존 V11 보존·PC/모바일 UI 검증 → 단일 HTML 전달.

본문 수집과 해석을 분리한다. 물약은 이름별 오프너가 아니라 오프너의 **물약 사용 타이밍**으로 표현한다. 고양 V3.10의 확보 미완료가 이 도구 도입만으로 해소되는 것은 아니다.

## 정적 HTML 및 페이지 내 WHML 탐색 (2026-11-12 확장)

HTML 원본을 확보할 수 있을 경우 `python -m engine.source_structure --input examples/synthetic-source-structure.html --output /tmp/structure-audit.json` 으로 오프라인 탐색한다. `role=tab`, `aria-controls`, Bootstrap 탭과 숨김 패널, `details`, select/optgroup, `aria-describedby`, `title`, `data-hint-body` 등에서 **선택지/툴팁 후보**를 기록한다. 숨김 섹션은 본문 길이/해시를, `?`는 섹션·표 행·본문 또는 참조 상태를 기록하되 장문 원문은 보고서에 싣지 않는다.

`engine/embedded_markup.py`는 역사적 Wowhead 실제 저장 HTML에 나타난 `WH.markup.printHtml` 호출 가운데 **JSON 호환 문자열 리터럴**만 해석한다. `guide-body`와 `interior-sidebar-related-markup`처럼 대상 컨테이너를 분리하고, WHML의 `tabs`, `toggler`, 명명된 `tooltip` 정의, `tooltip2`를 포함한 참조 이름·중복·미발견 여부를 보고한다. **JavaScript를 실행하지 않으며** 동적 인수와 다른 문자열 직렬화 형태는 미지원으로 표시한다.

직접 확인한 공개 역사적 예시: [aurokin/warcraft_cli의 분노 전사 HTML fixture](https://github.com/aurokin/warcraft_cli/blob/main/tests/fixtures/wowhead/guide_3087_page.html)에서 `printHtml` 호출 두 개가 있으며, 하나는 사이드바용 동적 `WH.getPageData`, 다른 하나는 `guide-body`의 14,037자 리터럴이었다. 이 특정 예시에는 WHML `tooltip` 정의·`tabs`·`toggler`가 없었고, **최신 고양 12.1.5의 구조나 모든 `?`가 존재한다는 증거는 아니다.**

이 탐색은 기존 `engine/source_coverage.py`의 **수집 기록 내부 감사**보다 한 단계 앞에서 후보를 발견해 누락 여부를 사람이/ChatGPT가 대조할 수 있게 한다. 두 도구를 사용해도 실제 라이브 UI에서 동적으로 생성되는 추가 선택지까지 전수 확보했음을 증명하지 못한다. 현 원문 Gate A는 별도 판정이며 교본 최종 승인으로 자동 이어지지 않는다.

## 수집 기록과 구조 후보 자동 대조 — source_reconcile (2026-11-12)

`source_structure`가 정적 HTML에서 발견한 후보는 실제 수집됐다는 뜻이 아니다. `source_reconcile`은 이 후보들을 `source_coverage`의 **이미 확보한 본문/선택 기록**과 대조하여 미확인 항목을 명시한다. 전문화별 기술명을 코드에 박아 넣지 않는다.

수집·분석자가 다음 순서로 이용한다. **사용자에게 JSON 조작을 요청하지 않는다.**

1. 실제로 확보할 수 있었던 HTML을 내부적으로 분석해 `structure.json`을 만든다. 원본 HTML, 개인 V11, 장문 원문은 PUBLIC 저장소에 업로드하지 않는다.
2. 해당 원문을 읽어 작성한 내부 `observations.json`의 각 설명 항목에 `source_candidate_ids`를 붙인다. 툴팁은 `tooltip:<HTML element index>:<description index>`, 접힌 영역은 `panel:<index>`, 선택 컨트롤은 `control:<index>`, WHML 참조는 `whml_reference:<payload index>:<reference index>`다. 이 ID들은 **하나의 HTML 구조 검사 결과 안에서만 유효**하며, 다른 리비전에서는 다시 대조한다.
3. 본문을 정확히 수집했지만 개별 ID를 아직 모를 경우, 도구는 **중복 없는 정확한 본문 해시 일치**만 자동 연결한다. 비슷한 단어나 위치만으로 원문이 동일하다고 추측하지 않는다. 특정 팁의 인접 행을 완전히 입증할 의무는 없다.
4. 다른 출처/맥락에 속하는 후보는 필요시 `source-reconciliation-decisions-v1`의 `not_relevant`에 후보 ID와 8자 이상의 구체적 이유를 작성한다. 자동으로 모든 버튼을 게임 선택으로 취급하지 않으며, 제외 수를 결과에 별도로 기록한다.
5. `unmapped_candidates`를 추가 수집 후보로 조사한다. `static_body_unresolved_ids`는 HTML의 참조만으로 본문을 확보할 수 없었던 설명을 뜻한다. `invalid_mappings`는 대상 없는 연결·종류 오류·중복 연결이다. **수집할 필요 없는 UI 요소와 실제 누락된 필수 원문을 의미 분석으로 구별한다.**

실행(공개 합성 자료만 사용):

```bash
python -m engine.source_structure --input examples/synthetic-source-structure.html --output /tmp/synthetic-structure.json
python -m engine.source_reconcile --structure /tmp/synthetic-structure.json --observations examples/synthetic-source-coverage.json --output /tmp/synthetic-reconcile.json
```

이 합성 예시는 의도적으로 선택지를 미방문으로 남겼으므로 결과에 **미수집 후보와 기존 누락**이 함께 나온다. 성공을 증명하는 예시가 아니다.

**QA 판정의 분리:** `candidate_comparison_complete`가 참이어도 **선언된 정적 후보만 연결됐다는 뜻**이다. 현재 도구 출력의 `real_site_completeness_verified`, `gameplay_meaning_verified`, `automatic_publish_allowed`는 항상 `false`다. JavaScript 동적 생성, 원본 패치 확인의 독립성, 숨겨진 실제 사이트의 미발견 요소는 자동으로 해결되지 않는다. `?`의 본문 확보와 위치/행 귀속을 혼동하지 않는다. 분석·집필 후 Q0/Q1 콘텐츠 QA와 별도 HTML/JS QA를 수행한다.

## HTML 지문으로 원본과 관측 기록 연결 (2026-11-12)

정적 HTML 탐색 결과 `source_sha256`은 해당 HTML 전체의 SHA-256이다. 같은 HTML을 조사한 관측 기록의 `accesses[]`에 `html_sha256`을 **정확히 동일한 값**으로 넣고, `kind=page_html/live_dom/rendered_ui`, 기준 URL·패치·수정본이 모두 맞을 때에만 `source_reconcile`의 명시 연결 및 본문 해시 연결을 유효하게 취급한다. **검색 색인은 그 HTML 자체가 아니므로 `search_index` 접근에 HTML 지문을 붙여 자동 연결해서는 안 된다.**

`declared_source_binding_matches=true`는 관측 파일과 구조 파일의 *동일 소스 선언 일치*만 뜻한다. 실제 사이트 인증이나 모든 `?`의 전수 확보가 아니다. 다른 패치 또는 다른 HTML인 경우 `source_binding_mismatch`와 경고를 남기고 후보 수집 완료를 차단한다.

공개용 구조 결과의 섹션 제목은 DOM 좌표(`h2@번호` 등), 컨트롤·선택 항목은 길이와 SHA-256으로 저장한다. 오래된 구조 검사기는 문구를 포함할 수 있으므로 **과거 검사 결과를 새 안전한 보고서로 간주하지 않는다**. 위치의 의미는 별도 비공개 원문 문맥에서 분석한다.

다전문화 실제 색인 조사와 합성 반례 검증: [CROSS_SPEC_SOURCE_VALIDATION_20261112](CROSS_SPEC_SOURCE_VALIDATION_20261112.md). 검색 색인·구버전 직접 열람의 날짜/패치 불일치와 동적 하위 선택 문제를 별도 한계로 관리한다.

## 실제 Wowhead HTML 저장본 2종 스모크 검증 (2026-11-12)

- 공공 GitHub `aurokin/warcraft_cli`의 과거 Wowhead HTML 테스트 fixture를 **고정 커밋 `376f5aec0aad29b4cf4e290b2879ec3e91870fde`**에서 GitHub Actions 실행 중 임시 다운로드하여 검증한다. 내부 `/tmp`에서 제거하며 개인 교본·실제 가이드 HTML은 우리 저장소·공개 Artifact에 추가하지 않는다.
- `guide_283_page.html`: `WH.markup.printHtml`의 `guide-body` 본문에서 실제 WHML **탭 그룹 2개, 그룹당 하위 탭 3개, 합계 6개**를 확인. `_tab_groups`는 각 옵션의 순서·라벨 해시·닫힘 상태·본문 길이/해시를 기록한다.
- `guide_3087_page.html`: 같은 형태의 `guide-body` 문자열이 있지만 WHML 탭 그룹은 **0개**다. 두 파일 모두 사이드바용 `WH.getPageData` 호출은 동적 인수이므로 **실행하지 않고 미해석으로 구분**한다.
- `source_reconcile`는 `whml_tab:<payload>:<group>:<tab>` 단위로 원문 수집 목록과 대조하므로 **탭 그룹이 존재한다는 관측**과 **각 탭 본문을 확보했다는 관측**을 구별한다. 다른 전문화의 숨김 선택에도 같은 원리를 적용한다.
- CI 실제 실행: [GitHub Actions 43152516953](https://github.com/degong2-code/wow-rotation-engine/actions/runs/43152516953)에서 **실제 HTML 스모크 PASS + 전체 257개 테스트 PASS**. 최신 게임 패치의 공략 정확성, 현재 Wowhead 전체 DOM, 모든 `?` 본문은 이 검증 범위 밖이다.

**중요:** 실제로 확인된 것은 특정 공개 *과거 저장본*의 HTML 구조다. 여전히 최신 고양 12.1.5 페이지의 직접 HTML 취득·동적 UI 전수 확보는 미완료이며, Gate A PASS로 승격하지 않는다.
