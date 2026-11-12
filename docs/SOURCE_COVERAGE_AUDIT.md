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
