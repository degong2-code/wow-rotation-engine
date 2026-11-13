# LIVE DOM CAPTURE — 허용된 브라우저에서 동적 원문 수집

**프로젝트 기본 경로는 전문화 이름 입력 → ChatGPT 조사·분석·V11 이상 한국어 단일 HTML 제작이다.** 이 어댑터는 별도 AI 자동화 엔진이 아니며 JSON·브라우저 설치를 사용자에게 요구하는 필수 절차가 아니다.

## 적용 조건

- 사용자가 열람할 권한이 있고 정상적으로 접근 가능한 브라우저 환경에서만 실행한다. HTTP 403, 보안 챌린지, 네트워크 DNS 실패를 우회하지 않는다.
- 현재 ChatGPT 세션에서 사용자 브라우저의 DOM에 접근할 수 있다고 가정하지 않는다. 연결 또는 실행 권한이 확인될 때만 사용한다.
- 실제 Wowhead의 장문 본문, V11 HTML 원본, 개인 교본 및 비공개 수집 JSON을 PUBLIC GitHub와 CI Artifact에 저장하지 않는다. 스크린샷은 생성하지 않는다.

## 수집 기능

1. 렌더링된 현재 DOM에서 `aria-controls`, `role=tab`, `select`, radio/checkbox, `summary` 형태의 안전한 선택 컨트롤을 탐지한다.
2. 기본 페이지를 재로드하고 상태 선택을 제한된 깊이까지 재생한다. 상위 선택 후 새로 나타나는 하위 탭·선택을 다시 발견한다. 임의 링크·폼 제출 버튼은 클릭하지 않는다.
3. 보이는 `?`/hover 요소의 `title`, `aria-describedby`, `tooltip`, `tooltip2`, `data-*` 설명과 표·행 단서를 확보하고 hover 후 나타난 tooltip도 수집한다.
4. 본문과 툴팁 내용은 **비공개 JSON**으로 저장한다. 공개 보고서에는 내용의 길이/해시·탐색한 상태 수·팁 후보 수만 저장한다. URL 쿼리/fragment와 로컬 경로도 제외한다.
5. 상태 수·깊이·팁 수에 상한을 둔다. 남은 경로 수 `pending_state_count`가 0보다 크거나 오류가 있으면 미완료로 구분한다. 0이어도 실제 사이트 전체 UI 발견의 증거는 아니다.

## 검증 자료 및 실행

- 구현: `engine/live_dom_capture.py`
- 합성 실제 인터랙션 페이지: `examples/synthetic-live-dom.html`
- Chromium 테스트: `tests/test_live_dom_capture.py`
- 전용 워크플로: `.github/workflows/browser-probe-fixture.yml`
- 실행 예: `python -m engine.live_dom_capture --html examples/synthetic-live-dom.html --private-output /tmp/private-capture.json --audit-output /tmp/public-audit.json`
- 해당 전용 CI만 선택적 Playwright/Chromium을 설치한다. 기본 오프라인 CI에는 브라우저를 필수로 강제하지 않는다.

## 기존 범용 수집 구조와의 관계

- HTML 안에 원문이 있으면 `source_structure`와 `embedded_markup`로 정적 후보·탭 본문을 추출한다.
- 렌더링 상태가 있어야 나타나는 선택/hover는 이 동적 DOM 보조 도구로 별도 수집한다.
- 확보한 본문을 실제 패치·영웅·전투 유형·빌드별로 확인해 `source_coverage`/`source_reconcile`의 누락 감사와 비교한다. 어댑터의 JSON 자체를 게임 판단 규칙이나 Gate A 통과로 간주하지 않는다.
- ChatGPT가 `상태→조건→행동→이유→예외`를 분석한 뒤 별도로 Q0/Q1 콘텐츠 QA 및 V11 비대상 보존·HTML 기능 QA를 수행한다.

## 현재 접근성 한계

2026-11-12 기준: 같은 고양 주술사 Wowhead URL의 최신 검색 색인은 2026-10-13 업데이트로 표시되지만 직접 열람은 2026-07-26·패치 12.0.7이다. 선행 GitHub Actions Playwright 접근은 HTTP 403이었다. 본 도구의 합성 브라우저 테스트 통과는 **실제 최신 Wowhead 동적 UI 확보 성공이 아니다.** 접근 가능한 최신 브라우저 환경에서 재검증하기 전에는 고양 V3.10의 Gate A는 FAIL, 교본 최종 승인은 보류한다.

## 2026-11-12 범용 누락 감사 연결 및 관측 범위 강화

- `engine/live_dom_capture.py`는 선택지 재현 시 임의 DOM 순번보다 **고유 ID를 우선** 사용하고, ID 없는 `?`는 렌더링된 DOM의 구조 경로를 활용해 hover한다. `title`·`aria-describedby`뿐 아니라 마우스를 올릴 때만 생성되는 overlay 본문도 별도로 보관한다. 단순 텍스트 `?`도 수집 후보로 포함한다.
- `tooltip_trigger_total`, `unhovered_tooltip_triggers`, `tooltip_snapshot_truncated`, `depth_limited_state_count`, `pending_state_count`는 수집 제한 때문에 발견하지 못한 내용이 있는지 추적한다. `known_capture_gaps`는 관측된 제한·오류를 표시하며, **false라고 해도 실제 페이지 전체의 완전성을 뜻하지 않는다.**
- 신규 `engine/live_dom_bridge.py`는 **비공개** 브라우저 수집본을 `source_coverage` 공통 형식의 **검토용 초안**으로 바꾼다. 하나의 `?`가 여러 속성·참조와 hover 본문을 가진다면 각각 별도 설명 항목으로 보존한다. 호버하지 못한 팁/잘린 후보를 `missing_content`로, 탐색하지 못한 UI 경로를 `unvisited_choice`로 기록한다. 모든 수집 상태는 `inventory_checked=false`를 유지한다.
- 변환의 `observed-ui-depth-N` 선택 경로는 **브라우저 방문 이력의 기술적 식별자**이지 실제 게임 로직의 영웅/전투·물약 분기라고 해석해서는 안 된다. ChatGPT가 원문 의미를 분석하며 진짜 의사결정 분기와 예시 선택을 재분류해야 한다.
- 실제 브라우저 캡처에 포함된 `source_sha256`은 초기 HTML 렌더링 상태의 지문이다. 입력자가 적은 패치·수정본 문자열은 **자동 검증되지 않는다**. 정적 HTML 구조의 해시와 연결되는지, 실제 가이드가 최신 패치인지 판단은 별도 단계다.

```bash
python -m engine.live_dom_bridge \
  --capture /tmp/private-capture-fixture.json \
  --specialization 'Synthetic Spec' --patch 'synthetic' --revision 'fixture' \
  --private-ledger /tmp/private-coverage-ledger.json \
  --audit-output /tmp/public-coverage-audit.json
```

위 실행은 개발 환경 예시다. `/tmp/private-coverage-ledger.json`은 **원문 텍스트가 포함된 비공개 자료**여서 PUBLIC 저장소·Actions Artifact에 포함하지 않는다. 공개 감사 보고서도 원문 본문을 복제하지 않는다. 브라우저 CI에서는 합성 픽스처만 사용하고 종료 후 모든 파일을 삭제한다.


## 자동 취득과 런타임 탐색 구분

[Source Page Acquisition](AUTO_PAGE_ACQUISITION.md)은 페이지 HTML과 선택적 MHTML을 먼저 저장하고, 본 모듈은 정상 렌더링된 페이지의 **동적 선택·hover**를 조사한다. 내장 원문이 HTML에 있으면 `_files` 폴더가 필요 없지만 모든 사이트에서 전수 확보를 보장하지 않는다.
