# 원문 HTML 자동 취득 — Ctrl+S 대응 구조 (2026-11-12)

## 목적과 범위

최종 사용자 경로는 **전문화 이름 입력 → ChatGPT가 원문을 조사하고 한국어 V11 이상 교본 제작**이다. `engine/source_page_acquire.py`는 사용자가 반복적으로 Ctrl+S 저장·전달하는 수고를 줄이기 위한 **선택적 취득 어댑터**다. 다른 전문화에도 재사용하며, 독립 AI API 엔진은 아니다.

## 왜 HTML과 `_files` 폴더가 함께 생기나?

Chrome에서 **웹페이지, 전체(Complete HTML)**로 저장하면 본문 HTML과 함께 CSS·JS·이미지·아이콘 등 외부 리소스를 `_files` 폴더에 저장한다. 페이지를 오프라인에서 비슷하게 표시하기 위한 것이다. 사용자가 전달한 고양 12.1.5 HTML 자체에 **내장 guide-body WHML 68,350자, 명명된 tooltip 44개, 16개 선택 정의/82개 조건부 표시**가 있었으므로 **그 페이지의 원문 분석에는 메인 HTML만으로 핵심 정보 수집이 가능했다**. 모든 다른 웹사이트에서 리소스 폴더 없이 전수 확보가 된다는 뜻은 아니다.

## 구현한 자동 취득 경로

1. **브라우저가 정상 접속할 수 있는 HTTPS URL:** Playwright Chromium을 열고 `page.content()`로 현재 DOM HTML을 저장한다. 가능하면 정상 응답의 네트워크 원본 HTML도 저장한다. 인라인 원문이 더 풍부한 쪽을 `analysis.html`로 자동 선택한다.
2. **화면 보존이 필요한 경우에만:** 선택적 CDP `Page.captureSnapshot(format=mhtml)` 호출로 MHTML 파일을 추가로 만든다. `_files` 폴더를 별도로 만들지 않아도 리소스를 한 파일에 보관할 수 있다. MHTML의 오프라인 동적 기능까지 보장하는 것은 아니다.
3. **이미 저장한 HTML/ZIP:** `.html` 또는 전체 웹페이지 ZIP을 읽고 메인 HTML만 안전하게 추출한다. `_files` 안의 리소스 전체를 열거나 압축을 디스크에 풀지 않는다.
4. **HTTP 403 또는 필수 원문 마커 부재:** 성공으로 처리하지 않고 실패한다. 사이트 차단 회피나 세션/계정 복제를 수행하지 않는다. 사용자 Chrome에서 보이는 페이지가 서버 Chromium에서도 똑같이 열리는지는 독립적인 접근 문제다.

## 개발 환경 사용 예

```bash
python -m engine.source_page_acquire \
  --url https://www.wowhead.com/guide/classes/shaman/enhancement/rotation-cooldowns-pve-dps \
  --allow-remote --require-marker WH.markup.printHtml \
  --output dist/private_source_capture

python -m engine.source_page_acquire \
  --saved-zip /path/to/saved-page.zip \
  --require-marker WH.markup.printHtml \
  --output dist/private_source_capture

# 필요할 때만 URL 수집에 --mhtml 추가
python -m engine.source_structure \
  --input dist/private_source_capture/analysis.html \
  --output dist/private_source_capture/structure-audit.json
```

`--url` 모드는 정상 접근 가능한 Chromium과 Playwright를 사용한다. `--saved-html`/`--saved-zip`에는 브라우저가 필요 없다. 이 명령은 **개발 환경 내부용**이며 사용자에게 설치·실행을 기본 요구하지 않는다.

## 결과와 보안

- `page.html`: 현재 렌더링된 DOM HTML.
- `network-response.html`: 확보할 수 있는 경우에만 HTTP 응답 본문.
- `analysis.html`: 인라인 가이드 원문이 더 풍부한 쪽을 자동 선택한 분석 기본 파일.
- `page.mhtml`: 요청한 경우에만 CSS·이미지 등이 포함된 단일 저장 파일.
- `audit.json`: 메인 HTML SHA·본문/선택/툴팁 수 등의 집계만 기록. 원문 문장·비밀 URL·원래 파일 경로는 공개하지 않는다.

**주의:** 원문 HTML, MHTML, ZIP, 전체 툴팁 본문은 비공개로 보관하고 PUBLIC GitHub에 업로드하지 않는다. 실행 성공은 자료 취득 여부일 뿐 실제 최신 패치 일치·전체 선택지 전수성·게임플레이 정확성 승인이 아니다. 추후 `source_structure`, `embedded_markup`, `live_dom_capture` 및 ChatGPT의 의미 QA를 별도로 적용한다.

## 검증

합성 HTML/ZIP·403 실패·필수 마커 누락·HTML 응답과 렌더링 DOM 차이·내용 비공개 분리 단위 테스트와 실제 Chromium에서 `page.content()`/MHTML 생성 테스트를 수행한다. **2026-11-12 현재 최신 Wowhead 원본을 서버에서 자동 취득하는 실증은 별도이며, 기존 서버 403 접근 문제의 해결을 주장하지 않는다.**

## 사용자 제공 실제 ZIP의 비공개 검증

사용자가 전달한 실제 Wowhead 전체 페이지 ZIP을 오프라인에서 메인 HTML 선별 점수로 검사했다. **총 210개 파일 항목, HTML 후보 26개**, 메인 HTML 1개와 동반 `_files` 폴더 항목 209개로 구성되어 있었다. `_files` 내부에는 **약 993KB인 부가 HTML**도 있어 메인 HTML(839,307바이트)보다 크다. 가장 큰 HTML을 고르는 수집기는 이 파일을 잘못 선택할 수 있다. 현재 코드는 내장 `WH.markup.printHtml`/`guide-body` 등을 우선해 **메인 HTML을 정확히 선택**했고, 해당 HTML SHA-256은 사용자 저장본의 기록(`d05d86b5db57b012373293ba5bae8b7c1f4b1e7711da29b3944df8b0ef5ea755`)과 일치했다.

이 검사 역시 **이미 사용자 브라우저에서 저장한 ZIP의 재해석**이다. ChatGPT 실행 환경에서 Wowhead URL의 최신 페이지를 직접 다운로드하는 능력이 확인됐다는 뜻은 아니다. 실제 ZIP/HTML/리소스 문구는 공개 저장소에 올리지 않는다.

## 브라우저 → WHML 분석 원스텝 파이프라인 (2026-11-12 후속)

`engine/source_acquisition_pipeline.py`는 별도 파일 수동 처리 없이 다음 작업을 **하나의 내부 명령**으로 수행한다.

1. 정상 접근 가능한 HTTPS 원문 취득 또는 저장 HTML/ZIP에서 메인 HTML 확보
2. 렌더링 HTML과 최초 응답 HTML 중 내장 원문이 더 풍부한 쪽으로 `analysis.html` 선택
3. 구조 분석기로 숨김 패널·탭·`?` 후보 탐색 및 WHML의 named tooltip/조건부 선택 정의 개수 검사
4. 미정의 팁 참조·미선언 선택 조건·잘린 후보 목록·미해석 스크립트 등의 위험을 별도 표시
5. 비공개 원문(`analysis.html` 등)과 요약 검사(`pipeline-audit.json`)를 분리

```bash
python -m engine.source_acquisition_pipeline \
  --url https://www.wowhead.com/guide/classes/shaman/enhancement/rotation-cooldowns-pve-dps \
  --allow-remote --capture-ui \
  --output dist/private_source_capture
```

`--capture-ui`는 브라우저가 정상 열리는 경우 실제 탭·`?`를 hover한 관측을 **별도 비공개 파일**에 덧붙인다. 현재 기본 코드는 **서버에서 Wowhead 403을 우회하지 않고**, 동일 호스트 밖으로 나가는 메인 프레임 이동을 제한한다. 도메인 이동이 필요한 정상 사이트는 현재 자동으로 실패하도록 설계했다.

브라우저 연동을 사용할 수 없는 ChatGPT 세션에서는 URL 취득을 성공한 것처럼 주장하지 않는다. 정상 접근 가능한 출처의 원문만 비교 분석하며, 완전한 최신성·선택 상태 전수·실전 로직 정확성은 별도 QA를 거친다.
