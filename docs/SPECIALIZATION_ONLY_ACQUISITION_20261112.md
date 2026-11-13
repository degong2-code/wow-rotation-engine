# 전문화 이름 → 실제 Wowhead 원문 → 비공개 집필 근거 패킷 (2026-11-12)

## 목적

사용자가 **전문화 이름만 입력**하면 Wowhead의 해당 전문화 공략을 일관된 방식으로 찾아 **정상 HTTPS GET → 원문 정체성 검증 → WHML 선택 조건·툴팁 원문 확보 → 비공개 집필 자료**까지 준비한다. 최종 제품 목표는 별도 API/관리자 엔진 없이 ChatGPT가 **분석·집필·V11 이상 한국어 단일 HTML 제작**을 책임지는 것이다. 이 단계는 아직 HTML 작성 및 게임 로직 검증을 자동 완료하는 엔진이 아니다.

## 범용 전문화 이름 해석

- `engine/spec_source_resolver.py`는 **13직업·40전문화**의 영문·한글 정규명과 일부 명시적인 별칭을 조회해 고정 Wowhead `.../guide/classes/{class}/{spec}/rotation-cooldowns-pve-dps` URL을 구성한다. 이 분류표는 **URL 탐색용 명칭 목록**이지 전문화별 로직·영웅 특성/물약 분기 규칙은 아니다.
- ``고양 주술사`·`고양`→ `shaman/enhancement`, ``비전 마법사`→ `mage/arcane`, ``생존 사냥꾼`→ `hunter/survival`, ``포식 악마사냥꾼`→ `demon-hunter/devourer`.
- ``냉기` 같은 모호한 명칭은 마법사·죽음의 기사를 구분하지 못하므로 **URL 요청 전 중단**한다. ``냉기 마법사` 또는 ``냉기 죽음의 기사`로 지정해야 한다. 비슷한 단어를 지어내거나 임의 URL 경로를 사용하지 않는다.
- 모든 40개 정규명은 오프라인 URL·역변환 테스트를 거친다. 단 **실제 URL의 현재 존재와 공략 출처는 요청할 때 HTML로 확인**한다. 40개 공략 전부를 원격 다운로드해 검증했다고 주장하지 않는다.

## 본문 취득·검증 순서

1. ``resolve_specialization`으로 정해진 전문화 URL 결정. 사용자 입력을 URL 경로에 직접 결합하지 않는다.
2. ``http_source_fetch.get_html`로 정상 HTTPS 요청 1회. 로그인·쿠키·브라우저 위장·프록시 회피·무제한 재시도는 하지 않는다. 403/429는 중단.
3. ``guide_identity.inspect_identity`로 HTML의 `title`/`h1`이 **해당 전문화 Rotation Guide**인지 대조한다. 보이는 원문에 표시된 `Patch`·`Updated` 및 문서 수정 메타데이터를 **단서**로 읽는다.
4. ``--expected-patch` 또는 ``--min-updated`가 주어졌다면 그 근거가 실제 HTML에 없거나 날짜가 과거이면 **비공개 원문 파일을 생성하기 전에 실패**한다. 패치 문자열이 **스크립트 안에만 있는 경우**에는 보이는 패치의 증거로 인정하지 않는다.
5. ``source_acquisition_pipeline.inspect_and_store`가 원본 WHML `guide-body`, 탭, 선택 조건, 툴팁 정의·참조 및 불일치 후보를 조사한다. ``--expected-guide-sha256`으로 이전 사용자 확인 원문과 일치 여부를 추가 비교할 수 있다.
6. ``source_editorial_packet.packet_from_html`가 **원문 WHML 전체와 정렬된 tooltip 정의/참조, radio 선택, `display-options` 조건표현, 제목 위치**를 비공개 인덱스로 만든다. 이는 원문 상태를 잃지 않기 위한 자료이며 **조건·행동 의미를 자동으로 만들어내지 않는다**.

## 검증 완료한 실제 전문화

| 한국어 입력 | guide-body 길이 | tooltip 정의 | 선택 정의 | 원문 표시 수정일 | 원문 표시 패치 |
|---|---:|---:|---:|---|---|
| 고양 주술사 | 68,350자 | 44 | 16 | 2026-10-13 | 12.1.5 |
| 생존 사냥꾼 | 53,084자 | 39 | 8 | 2026-10-13 | 12.1.5 |
| 비전 마법사 | 30,016자 | 7 | 2 | 2026-10-16 | 12.1.5 |

- [전문화 이름만으로 HTTP 원본 취득 실험](https://github.com/degong2-code/wow-rotation-engine/actions/runs/43181759158): 3개 모두 title/heading과 실제 WHML 확인. 고양 원문 SHA는 사용자가 Ctrl+S로 제공해 직접 12.1.5임을 확인한 **동일 원문과 일치**.
- [실제 원문 집필 패킷 검증](https://github.com/degong2-code/wow-rotation-engine/actions/runs/43182698012): 3개 모두 이름 있는 tooltip 정의와 모든 `display-options` 조건을 비공개 인덱스에서 개수 일치 확인. raw WHML/기술명·팁 본문은 공개 로그·저장소에 두지 않았다.
- **주의:** `12.1.5`는 확인한 HTML에서 **표시된 패치**다. 그 패치가 현재 라이브 게임의 세계적 최신판인지, 저장본의 조건이 실제 최적화 로직인지 자동 승인하지 않는다. 출처 정체성/개정일 → 원문 전체 상태 → 게임 콘텐츠 Q0/Q1 → HTML 기능 QA는 계속 별개.

## 내부 실행 예시

```bash
python -m engine.source_acquisition_pipeline \
  --specialization '고양 주술사' --allow-remote \
  --output dist/private_sources/enhancement \
  --expected-patch 12.1.5 --min-updated 2026-10-13 \
  --expected-guide-sha256 6657591171c36c79797b739b2248e37b9d967094e7d33e8dd799293283bd5dbe
```

예상 비공개 파일: `analysis.html`, `editorial-evidence-private.json` (원문 WHML·툴팁 본문·조건식 원문 포함), `structure-audit.json`, `pipeline-audit.json`. 지정된 출력은 일시적 **비공개 저장공간**에만 두고 공개 GitHub/Actions Artifact에 업로드하지 않는다. 프로젝트 사용자에게 로컬 Python 실행이나 HTML 저장을 기본적으로 요구하지 않는다.

## 남은 과제

이 단계는 **원문 위치·취득·정체성/개정 단서·조건/툴팁 근거 정리**를 구현한 것이다. 여전히 ChatGPT가 원문에 따라 `상태 → 조건 → 다음 행동 → 이유 → 예외`를 추출하고 반례/교차 검증 후 V11 이상 HTML을 만들어야 한다. 이 후속 작업이 실제로 수행되지 않으면 전문화 입력만으로 자동 교본을 **제작 완료**했다고 말하면 안 된다. 동적 JS로만 생기는 상태는 추가 브라우저 조사가 필요할 수 있다.


## 2026-11-12 실제 조건 적용 범위 분석

[WHML 범위 귀속과 실제 3전문화 전수 계수](WHML_SCOPE_EVIDENCE_20261112.md): 고양 `62 범위형 + 20 독립 마커 = 82 원문 조건`, 생존 61/61, 비전 5/5, 미귀속 0. 닫힘 불일치 경고는 고양·비전 각각 1건이라 범위를 추측해 합치지 않는다. UI 표시 조건을 실제 게임 행동 조건으로 혼동하지 않고 비공개 집필용 자료에 원문 위치를 유지한다.


## 2026-11-13 후속 — 전문화 이름으로 선택형 UI 수집까지 연결

**반복된 실물 교본 결함:** 생존 사냥꾼 V1~V11 REVIEW 과정에서는 검색 색인에 최신 12.1.5가 표시됐어도 직접 열린 동일 URL에서 12.0.7(2026-05-03) 본문이 확인됐다. 이 상태에서 서로 다른 버전의 우선순위·영웅 특성 선택·툴팁을 섞으면 실제 다음 기술이 바뀐다. 기존 전문화 입력 HTTP 모드는 WHML의 선택 조건을 추출할 수 있었으나 브라우저 UI 실증은 수동 URL 입력을 요구했다.

**기존 공통 기능 연결:** 새로운 크롤러를 만들지 않고 기존 source_acquisition_pipeline의 전문화 해석과 run_browser/live_dom_capture를 결합한다. HTTP 경로는 그대로 유지한다. `--specialization`에 `--capture-ui` 또는 `--mhtml`을 지정해도 **먼저 정상 HTTP 원문·패치·집필 패킷을 확보**한다. 이후 같은 정규 Wowhead URL의 Chromium 수집을 선택적으로 시도하며, **원문 guide-body SHA·수정일이 정확히 일치할 때만** 브라우저 상태를 결합한다. URL 직접 조합·로그인 우회·사이트 차단 회피 없음.

예시(명령을 실행하는 환경에 승인된 Chromium과 정상 사이트 접근이 있을 경우):

```bash
python -m engine.source_acquisition_pipeline \
  --specialization "생존 사냥꾼" --allow-remote --capture-ui \
  --expected-patch 12.1.5 --min-updated 2026-10-13 \
  --max-states 24 --max-depth 3 \
  --output /private/rotation-source-survival
```

- 기존 `--specialization`만 지정하면 가벼운 HTTP 원문 수집, `--capture-ui` 추가 시 먼저 HTTP 본문을 확정하고 브라우저에서 선택형 UI·접힘·툴팁 보강을 시도. UI가 차단되면 이미 검증한 원문은 유지하되 UI 내용은 미확보 REVIEW로 기록. 원문 인덱스 `editorial-evidence-private.json` 및 `scoped-evidence-private.json`과 `private-ui-capture.json`을 **같은 비공개 출력 아래** 보존.
- **패치 차단:** 실제 브라우저 DOM과 HTTP 응답 각각의 제목·패치 표시·수정일이 요구 조건을 충족해야 하며, 서로 개정이 다르면 브라우저 상태를 결합하지 않는다. 정상 HTTP 원문의 스냅샷은 보호한다. URL이나 검색 결과의 날짜를 현재 열람한 본문의 날짜로 대체하지 않는다.
- **상태별 차단:** 동적 선택 상태를 재방문할 때마다 실제 DOM 정체성/패치·수정일을 다시 확인한다. 불일치 상태의 본문/팁은 관측 자료에 포함하지 않고 별도 수집 오류로 기록; `ui_known_capture_gaps=true`이면 수집 완전성 승인 금지.
- **안전한 의미:** 초기 원문·UI 관측은 별개 자료다. WHML display-options 표시 조건은 게임플레이 조건을 자동 결정하지 않는다. 모든 유효 선택형 상태·툴팁을 방문했는지는 여전히 개별 검토가 필요하며 `real_site_completeness_verified=false`·`gameplay_meaning_verified=false`를 유지한다.
- 처음 HTTPS GET에서 403/429가 발생하거나 패치가 맞지 않으면 중단한다. **정상 HTTP 원문을 이미 확보한 뒤** Chromium 접근만 거부되면 이를 우회하지 않고 `ui_capture_status=browser_access_denied`로 기록하며 교본 원문은 보존한다. 검색 색인·과거 교본으로 원문을 대체해 성공 판정을 만들지 않는다. 필요하다면 정당하게 확보한 사용자 저장 HTML/ZIP을 기존 `--saved-html` / `--saved-zip` 경로로 분석한다.

**검증 범위:** 합성 HTML에서 전문화 이름→브라우저 경로 선택, 정상 사적 원문·UI 패킷 공동 기록, 오래된 패치/다른 전문화/DOM과 응답 개정 충돌, 동적 상태 재로딩 중 패치 변경 차단을 테스트한다. 실제 Wowhead 선택형 전체 사이트를 지금 접근 가능한 환경에서 성공 수집했다는 주장이 아니며, 실제 12.1.5 복원은 별도 현장 증거가 필요하다.

**전체 최종 제품과의 연결:** 이 기능의 출력은 ChatGPT가 상태·조건·행동·이유·오프너를 독립적으로 집필할 **집필 근거**다. 사용자의 전문화 입력만으로 HTML을 자동 완성했다고 주장하지 않는다. 구버전 혼합을 막고 원문 상태별 자료를 잃지 않는 것이 다음 V11+ 교본 제작에서의 실질적인 품질 기여다.

## 2026-11-13 실사이트 검증과 HTTP-first 수집 보호 (PR #22 후속)

- [실제 Wowhead 재수집](https://github.com/degong2-code/wow-rotation-engine/actions/runs/43435619340): 생존 사냥꾼 12.1.5 / 표시 수정일 2026-10-13, WHML 본문 1개, 툴팁 정의 39개, 선택 항목 8개. 미선언 선택 ID가 ordered 행동 후보에 연결되어 **source_selector_action_review_required=true**. 이 원문 SHA와 상태별 UI 실제 표시를 별도로 검증하기 전에는 Q0/Q1 승인 불가.
- [동일 실행 환경의 실제 Chromium 검사](https://github.com/degong2-code/wow-rotation-engine/actions/runs/43435836835): 사이트에서 브라우저 접근을 차단함 (survival_live_ui_issue=denied_or_blocked). 원문을 HTTP로 받았다는 이유로 브라우저 상태도 확보했다고 가정하지 않는다.
- **발견한 제작 경로 결함:** 이전 전문화 --capture-ui 모드는 브라우저부터 열어서, Chromium이 막히면 정상 접근 가능한 12.1.5 WHML까지 산출하지 못했다. 최종 Chat-first 교본은 정본 원문을 최우선 확보해야 하므로 기존 run_specialization을 먼저 실행하고 optional Chromium은 **동일 버전·동일 guide-body SHA로 확인될 때만** 합친다. 성공한 HTTP 원문을 오래된 렌더링 결과로 대체하지 않는다.
- **실패 판정:** HTTP 패치 검증 실패 → 수집 자체 FAIL, 산출물 없음. HTTP 검증 PASS + Chromium 접근 불가/불일치 → 원문 자료 보존·UI 미확보 REVIEW. UI 일부 상태만 확보 → 관측 기록 보존, ui_known_capture_gaps=true이면 REVIEW. 모든 경우 real_site_completeness_verified=false / gameplay_meaning_verified=false / automatic_publish_allowed=false.
- 공개 저장소와 GitHub 로그에는 원문·개인 교본·툴팁 장문을 저장하지 않는다. GitHub Actions는 일시적 비공개 디렉터리의 감사 메타데이터만 기록한다.

**실제 제품 판단:** 12.1.5 원문 취득은 가능하지만 현재 모든 선택 상태의 조건 귀속을 재현하지 못했으므로 생존 사냥꾼 검토본 게임 Q0/Q1은 REVIEW를 유지한다. 새 버전 번호나 새로운 우선순위 행을 근거 없이 만들지 않는다.
