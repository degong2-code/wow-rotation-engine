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
