# V11 CREATE 품질·표현 규격 — 실데이터 역설계 (2026-11-11)

## 해결하려는 문제

신규 비전 교본은 기존 7개 V11 매뉴얼과 CSS 일부는 공유했지만, 실제로는 **장 번호, 요약표, 판단 전후 설명, 오프너 단계, 주의 박스, 기술별 툴팁, 용어집 행** 등을 단순화한 별도 템플릿이었다. 시각적/서술적 완성도의 편차는 원본 내용의 양뿐 아니라 **CREATE의 구조화 데이터·렌더러**에 원인이 있다.

원본 7개를 재작성하지 않는다. 개인 V11 원본은 **읽기 전용**으로 분석하고, 기존 HTML 본문은 항상 바이트 동일하게 보존한다.

## V11 7개 전문화에서 확인한 구성 요소

비공개 원본 SHA-256: `5d70279c4dd073eccef1f3b13565a8f555cd81c9f0a5b7eda7e3485e410742be`.

`BeautifulSoup(guide.get_text(" ", strip=True))`을 사용한 **구조·문자 수 지표**이며, 게임플레이 질이나 사용자 가독성의 정량 평점은 아니다. 본 문서에 기존 공략 본문은 포함하지 않는다.

| 전문화 | 장 수 | HTML 내 교본 텍스트 문자 수 |
|---|---:|---:|
| 화염 | 10 | 10,836 |
| 냉기 마법사 | 8 | 8,625 |
| 냉기 죽음의 기사 | 8 | 8,679 |
| 사격 사냥꾼 | 8 | 8,371 |
| 야수 사냥꾼 | 8 | 8,556 |
| 잠행 도적 | 9 | 11,101 |
| 암살 도적 | 9 | 12,355 |
| **기존 평균** | **약 8.6** | **약 9,789** |

일곱 전문화에서 공통으로 사용한 V11 CSS/DOM 클래스 11종:
`quick-head`, `chapter-heading`, `chapter-no`, `steps`, `aside`,
`glossary-list`, `glossary-row`, `priority`, `table-scroll`,
`spell`, `tip-trigger`.

여기에 영웅 특성별 표시를 위한 `variant`, `hero-switch`, 요약표 `overview-table`까지 합쳐 **14종의 재사용 구성 요소**를 신규 비전에 적용한다.

## CREATE v1 → V11 편집 규격

`content/new_guides/arcane.json`의 `editorial.version=v11-editorial-v1` 추가:
- `overview.lead` / `decision_order` / `caution`: 영웅 특성과 대상 수를 먼저 판단하도록 순서를 제시
- `chapters`: 준비·원리·오프너·우선순위·고급 운용·용어집의 **본문 맥락과 주의/예외**를 별도 기록
- `rotation_groups[*].intro/caution`: 네 우선순위 표의 독립 해설
- `cooldowns[*]`: 기술별 **원리 / 사용 판단 / 예외**를 구분한 상세 장
- `practice[*]`: 확정적인 시전 지시 대신 조건을 읽는 연습 사례
- `spells[*].hint`: 12개 기술의 각기 다른, 검토 상태를 반영한 툴팁 설명
- `review_policy`: 불확실하면 내용을 꾸며내지 않고 검토 대기로 남기는 정책

`engine/v2/create_guide.py`는 위 데이터를 V11의 `quick-head`, `chapter-heading`·장 번호, `aside.plain/warn`, `steps.compact`, `glossary-list` 스타일로 렌더링한다. 이전과 마찬가지로 기존 일곱 `manual-view`의 HTML은 **바이트 동일**하지 않으면 실패한다.

`engine/v2/fidelity.py`:
- `baseline_profile(private_v11_html)`: 기존 7개 구조의 **개수와 문자 수만** 출력, 원문/HTML 조각은 보고서에 포함하지 않는다.
- `audit_create_fragment(html, draft)`: 14개 V11 구성 요소·장 헤더/번호·오프너 단계·영웅별 우선순위·용어집·기술/팁 개수 검증.
- 증거가 없는 규칙의 근거를 생성해서 공란을 채우지 않는다. 단순한 글자 수 **최소 할당량 없음**.

## 실제 V11을 이용한 로컬 시범 결과

기존 7개 HTML은 변경 없이 유지. 새 비전은 **9개 장 / 시전 우선순위 4표·34행 / 고급 팁 10개**.

| 지표 | 이전 비전 CREATE | 개정 시범 |
|---|---:|---:|
| 장 수 | 7 | 9 |
| 교본 텍스트 | 약 4,900자 | 약 9,685자 |
| 장 번호·공통 헤더 | 단순화 | V11 구조 사용 |
| 오프너 단계 구성 | 일반 목록 | `steps compact` |
| 기술 설명 | 동일한 기본 안내 위주 | 기술별 힌트 12개 |
| 쿨다운·판단 연습 | 독립 장 없음 | 2개 장 추가 |
| V11 공통/확장 구성 요소 | 일부 | **14종 재사용** |

과도한 주의 박스 반복을 피하기 위해 쿨다운·판단 연습의 일부 보충 내용을 일반 문단으로 옮겼다. 비전의 `aside`는 **8개**로 유지해 기존 일곱 교본의 시각적 밀도에 가까워지도록 했다.

로컬 `create_arcane` → 새 HTML **956,914 bytes**, SHA-256 `a2de8480909dbd5dcdbbb4e36c8199a34e632a6089b2c79e5a7f7877d6435422`. 기존 7개 `manual-view` byte-identical. 전체 8개 전문화 / 69개 장의 V2 importer→builder byte-identical, `validate` 오류 0. Chromium 데스크톱(1365px)·모바일(390px): 비전 영웅 선택/주문술사 전환/냉기 복귀 PASS, JS 오류 0. **비공개 생성본을 GitHub/CI/Pages에 올리지 않음.** 이 결과는 동일한 편집 구조의 로컬 구현 검증이며 GitHub SHA가 다른 파일의 최종 실데이터 재실행과 구분한다. GitHub 코드 자체는 합성 CI로 확인한다.

## 남은 품질 게이트

**구조적 품질 개선과 게임플레이 검증은 별개.**
- 규칙별 출처 지문/원문 위치가 연결된 항목: **0/34** (전체 공략 링크는 존재하나 행별 증거 미연결)
- 새 비전 우선순위 34행·고급 팁 10개: `needs_manual_gameplay_review` 유지
- 특정 주문 ID/아이콘, 특성·티어 세트 효과: 개별 검토 필요
- 실제 사용자의 눈으로 본 글자 크기/표 밀도/읽기 흐름은 별도 평가 필요
- 자동 공개/배포/기존 main 병합 금지

새 텍스트 길이가 기존 평균과 비슷해졌다고 좋은 설명이 되었다고 **선언하지 않는다**. 실제 게임의 시전 판단, 근거 정확성, 누락 예외, 설명 친절함은 별도 검토한다.

## V11 행동 지식 구조화 — 기술 연결·결정 흐름 (2026-11-11)

이전 비전 생성기는 V11 장 구성/툴팁을 재사용했으나, 기존 화염의 **기술 연결 → 조건 비교 → 실행 흐름 → 예외**에 해당하는 내용이 주로 일반 문단으로 출력되었다. 화면 전체 비교에서 확인된 이 차이를 줄이기 위해 CREATE 데이터 계약과 V11 렌더러를 추가했다.

### 새 데이터 계약

`content/new_guides/arcane.json`의 `editorial.mechanics.schema_version=v11-mechanics-v1`:
- `flows[3]`: 충전물→비전 탄막, 번뜩임→신비한 화살→비전 연사 판단, 쿨다운 오프너→탄막→비전의 여파를 **기술/상태 단계**와 사용 이유·예외로 기록
- `comparisons[1]`: 성난태양의 비전의 영혼 및 일반 25중첩, 주문술사의 20중첩을 비교하고 **행동 후보·이유**를 별도 열로 구분
- 각 블록의 `related_rule_ids`: 기존 초안의 해당 우선순위 행과 내부 링크. **외부 공략 원문 증거로 취급하지 않음**
- `review=needs_manual_gameplay_review`: 단 한 블록이라도 검토 상태를 임의로 승인 처리하면 검증 실패

`engine/v2/mechanics.py`는 다음을 제공한다.
- V11 정본의 `p.sequence`, `ol.steps.compact`, `table.comparison`을 직접 재사용
- `[[spell:arcane-barrage]]` 같은 **명시적 토큰만** 기존 `_spell`의 실아이콘/툴팁 렌더러에 연결. 이름 유사도 기반 자동 치환·아이콘/주문 ID 추측 없음
- 일반 문장은 HTML 이스케이프, 알 수 없는 기술·손상된 토큰·기존 우선순위 ID가 아닌 관계를 거부

`create_guide.py`는 핵심 원리, 오프너, 준비, 쿨다운, 고급 운용, 판단 연습, 요약에서도 필요한 기술 링크를 생성한다. `fidelity.py`의 CREATE 감사는 흐름도·비교표의 개수와 **여러 장에 걸친 문맥별 기술 링크**를 확인한다.

### 관측된 실제 HTML 지표

개인 V11 원본을 이용한 **로컬 개발 사본**의 8전문화 생성 시범:
- 비전 새 `manual-view`에 **기술 링크 88개** (우선순위/용어집 이외 42개)
- V11 스타일의 **흐름도 3개**(핵심 원리 2, 오프너 1), 조건 비교표 1개, 기술별 조건·역할 설명
- 기존 V11의 7개 전문화 HTML 바이트 동일
- 전체 출력: **985,280 bytes**, SHA-256 `dee3dbf04042906e25bbf7e4c0acbc3a0e094c4bbadf4bcfe4e5ad7e8780abea`
- V2 importer → builder **8전문화/69장** byte-identical, `validate` 오류 0
- Chromium headless 1365px·390px에서 비전 선택, 성난태양→주문술사, 기존 냉기 복귀 모두 PASS. JavaScript page errors 0
- 본 실데이터 HTML은 **로컬 개발 소스**를 실행한 결과이며, GitHub Blob SHA가 완전히 같은 최신 생성기를 실행했다는 증거는 아니다. GitHub 공식 코드의 검증은 별도 합성 CI에서 이루어진다. 화면 캡처 파일 생성 없음

### 품질·근거 구분

- 새 흐름과 비교표의 내부 초안 우선순위 ID 귀속은 **7개 고유 행**.
- 외부 원문 증거가 개별 행에 연결된 항목은 여전히 **0/34**. 내부 링크와 기술 아이콘 수 증가가 사실 검증을 의미하지 않는다.
- 모든 메커니즘·행은 검토 대기이며, 오프너도 시전 조건에 따른 **예시**로 표기. 고정 매크로·확정 콤보로 재해석하지 않는다.
- 신규 아이콘 ID가 검증되지 않은 경우 중립 표시를 유지하고 기존 7전문화 원문/HTML은 절대 공개·재작성하지 않는다.

## V11 조건 비교표와 `?` / `!` 마커 재사용 (2026-11-11)

사용자 화면 비교에서 기존 화염 교본의 **표·`?` 상세 설명·`!` 주의 표시**도 비전 CREATE가 재현해야 할 요소로 확인했다. 기존 V11 원본의 실제 DOM/CSS/JS 계약을 분석한 후 별도 UI 시스템을 만들지 않고 다음 요소를 재사용했다.

- `overview-table`: 영웅 특성별 빠른 참고 표. 주의가 필요한 첫 규칙은 `!`를 중복 표시.
- `priority`: 해당 우선순위 행의 조건 바로 뒤에 원본 V11의 `button.note-marker.tip-trigger` 삽입.
- `comparison` + `table-scroll`: 기존 성난태양/주문술사 탄막 기준에 더해 번뜩임→신비한 화살/비전 탄막 4행 비교표 추가 (핵심 원리 비교표 2개).
- `note-marker`의 `?`: 원리·추가 판단 설명. `note-marker.critical`의 `!`: 세트 조건·특성 선택·영웅 특성의 중첩 차이 같은 주의.
- `data-hint-title/body/href`: 기존 V11 `floating-tip`의 **호버 표시·클릭 고정·자세히 읽기·Escape/닫기·모바일 탭** 기능 그대로 사용. 새 JS나 CSS 없음.
- `note-key`/ `note-key.important`: 기존 V11 설명 마크 범례. 마크를 무차별적으로 추가하지 않고 `?` 3종·`!` 3종, 총 **6개의 서로 다른 설명 근거 항목**만 구성한다. 빠른 참고 표 재표시까지 포함하면 렌더된 버튼 **7개**.

### 신규 CREATE 데이터 계약

`content/new_guides/arcane.json` → `editorial.annotations.schema_version=v11-notes-v1`:
- `id`, `target_type` (`rule`/`mechanic`), `target_id`, `marker`, `title`, `body`, `detail_anchor`, `review`.
- `engine/v2/annotations.py`: 존재하는 규칙 ID·메커니즘 ID만 참조, 유효한 해당 교본 장 앵커만 허용, `!`에 실제 주의 설명이 있는지 검사. HTML/스크립트 삽입 차단을 위한 문자열 이스케이프, 무단 리뷰 승격 거부.
- `create_guide.py`와 `mechanics.py`: V11 원본과 동일한 클래스로 버튼·비교표·범례 연결.
- `fidelity.py`: 실제 출력에서 개별 마커 누락, `?`/`!` 의미 불일치, 잘못된 장 링크, 툴팁/접근성 정보 누락 검사.
- `tests/test_v11_annotations.py`: 모든 6개 항목의 ID, 위치, 심각도, 링크, 범례, 2개 비교표, 악성 입력·잘못된 ID 거부. 공개 GitHub에는 실제 기존 7개 전문화의 장문 원문을 넣지 않는다.

### 실제 V11 JavaScript 사용성 시험

개인 V11 전체 HTML에 위 마커를 삽입한 **로컬 상호작용 전용 미리보기**를 제작하여 Chromium headless에서 실험.

- 기존 7전문화 `manual-view` HTML 바이트 동일. 비전 포함 전체 HTML **992,633 bytes**, SHA-256 `5a7a5bbb92b359279ef5baa9e0ff81e1fd25f363fed6db256dd9035ea67acdb3`.
- 데스크톱 1365px, 모바일 390px 모두: `?` 마우스 진입→툴팁, 클릭 고정, Escape 닫기, `!` 경고 강조 및 설명, 자세히 읽기 링크, 닫기 버튼, 기존 화염의 `?`/`!` 트리거 **PASS**. JS page errors **0건**.
- 표 2개, 버튼 7개 확인. 별도 화면 캡처 파일 생성 없음.
- **정확한 범위:** 이 미리보기는 앞선 비전 메커니즘 로컬 HTML을 바탕으로 동일한 V11 마크업을 위치별 삽입한 상호작용 검증 결과다. GitHub 정식 `create_guide.py`의 최신 코드·데이터를 사용한 완전한 canonical E2E 실행이라는 뜻이 아니다. 정식 코드와 JSON의 생성·구조 검증은 별도 GitHub 합성 CI PASS로 확인했다.

`?`와 `!`의 내용 또한 현재 **초안 해설**로 `needs_manual_gameplay_review` 상태다. 외부 원문의 34개 우선순위 조건별 게임플레이 증거가 모두 검증됐다는 주장을 하지 않는다.

## 개발 및 인계

- PR #14: 원본 V11 보존·UPDATE 기반
- PR #15: 비전 CREATE 8번째 전문화
- 현재 브랜치 `work/v11-fidelity-arcane-20261111`: PR #15 기반의 편집/표현 품질 규격

후속 전문화의 공통 엔진으로 확장할 때는 `fidelity.py`의 Arcane-specific section 선택자를 선언형 `guide_id` 매핑으로 일반화해야 한다. 현재는 비전 파일럿에 대한 **구체적인 품질 계약**이며 범용 CREATE 엔진 완성 선언은 아니다.
