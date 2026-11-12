# OPENER TIMELINE QA — 범용 상태 전이 설계 및 증거 경계 (2026-11-13)

**상태: 범용 검사기와 합성 정상/실패 대조 구현. 실제 고양 12개 오프너의 전체 Q0/Q1 검증은 미완료.**

구현: engine/opener_timeline_qa.py, tests/test_opener_timeline_qa.py. 상위 규칙은 QUALITY_FIRST_POLICY.md 및 EDITORIAL_QUALITY_PROTOCOL.md. 기존 engine/gameplay_decision_qa.py는 유지한다.

## 1. 범용화의 대상과 목적

기존 opener 검사는 순서(step→action), 배타적 문맥, 중복 단계 충돌을 평가하지만 전투 전 선시전 시점, GCD 밖 동시 사용, 선택적 시전, 직전 행동에 따른 다음 상태의 변화를 충분히 설명하지 못한다.

**범용화할 것은 어떤 전문화의 기술 순서가 아니라 조건·시간·동시성·상태 전이·근거·검증의 관계다.** 고양 전용 자동 딜사이클 엔진을 만들거나 Q0/Q1 의미 해석을 코드로 대체하지 않는다.

## 2. 제작-검증 계약

1. **원문 확정:** 실제 패치/수정일/빌드, 유효한 상위·하위 선택과 접힌 Notes/툴팁 본문을 비공개로 확보하고 하나의 원문 WHML SHA를 고정한다.
2. **행동 주석:** 편집자가 실제 원문을 해석해 각 유효 문맥(context), 사건(event), 조건(when), 상태 변화(set_state), 시간 및 GCD 구분을 작성한다. 도구는 기술 효과·GCD 길이·쿨다운·시전시간을 추측하지 않는다.
3. **독립 기대값:** 별도의 출처 대조에서 기대 행동·시점을 만든다. *주석 이벤트를 그대로 기대값에 복사하면 독립 검증은 성립하지 않는다.*
4. **기계 검증:** 원문 지문/오프셋/첫 행동 인용 마커, 배타적 문맥, 조건 3값, 같은 시점의 GCD 충돌, 상태 전이, 선언한 기대값, 미시험 분기를 검사한다.
5. **품질 분리:** 실제 원문 의미 Q0/Q1, 이해 Q2, 실전 사용성 Q3, 기존 HTML 보존/작동 Q4, 사용자 승인은 별도로 판단한다.

### 최소 입력 구조

- source packet: 기존 비공개 source-editorial-evidence-private-v1. 원문 본문·해시는 로컬에만 둔다.
- annotations: opener-timeline-private-v1. source_sha256, branches, cases.
- branch: 유효한 context(영웅/단일·광역/실제 행동을 바꾸는 선택)와 events.
- event: id, action, beat, phase, lane, when, set_state, evidence, action_source_marker. action_source_marker는 **첫 번째 실제 행동 근거 span** 안에 있어야 하며, 설명 툴팁에만 등장하는 기술명으로 통과할 수 없다.
- beat: 게임 초나 GCD 횟수가 아닌 논리적 판단 단계. **같은 beat의 GCD 행동은 최대 하나**, off_gcd 사건은 함께 올 수 있다.
- phase: prepull / pull / combat. 정확한 근거가 있는 경우에만 pull 상대 time_ms와 time_anchor(start/finish/impact/use)를 함께 입력한다. 선시전 시작과 적중 시점은 구분한다.
- when: 명시적 AND 술어. 필요한 상태가 빠지면 underdetermined, 무조건 false가 아니다.
- set_state: **확인된 사실로 편집자가 적은** 효과만 다음 beat에 적용. 동일 beat의 모든 행동은 동일한 시작 상태를 읽는다. 같은 beat에서 같은 필드가 서로 다르게 변경되면 ambiguous.
- case: context, initial_state, independently derived expected_events. 각 선언된 유효 분기와 선택적 시전의 양쪽 결과를 확인한다.
- 결과: matched/mismatch/underdetermined/ambiguous/no_branch 및 원문 근거 실패, 미시험 분기, 미시험 이벤트 blocker. 공개 출력은 코드·개수·사례 순번으로 한정한다.

**명시적 비목표:** 자동 게임플레이 최적화, 주문 시전시간/투사체/쿨다운 계산, 미확인 물약·장비 효과 추론, 게임 로그 독립 증명. 의미가 불명확하면 REVIEW.

## 3. 고양 주술사 12.1.5에 적용할 검증

[원문 구조 기록](ENHANCEMENT_SAVED_HTML_EVIDENCE_20261112.md)에서 검증한 guide-body SHA256:
6657591171c36c79797b739b2248e37b9d967094e7d33e8dd799293283bd5dbe.

유효 문맥은 폭풍인도자/토템술사 × 단일/광역 × 각 오프너의 Liquid Luster, Potion of Recklessness, Light's Potential = **12개**. 16개 선택 정의의 모든 조합을 곱하거나, 물약을 무조건 통합하지 않는다. 다른 전문화에 물약 세 종류를 공통으로 강제하지 않는다.

출처로 이미 확인한 구별 사례: 폭풍인도자 광역 Recklessness는 낙뢰 풀 1초 전 선시전, 다른 두 물약은 풀 시점 낙뢰 사용. 폭풍인도자 단일 Liquid Luster는 풀 12초 전 물약, Light's Potential은 선택적 초기 폭풍의 일격 뒤/승천 전 물약. 토템술사 광역은 낙뢰 선시전 없음.

**다음 실제 검증:** 동일 지문의 비공개 원문을 확보 → 12개의 전체 이벤트와 근거·상태를 작성 → 독립 예상 사건 목록을 추출 → 선시전, GCD 밖 동시 사용, 조건부 시전 양방향, 다음 상태, 물약 상호 배타성과 지속 딜 접속 확인 → V3.11 요약·오프너·심화와 대조. 우선순위 9중첩 극단 및 조기 소비 상충, 툴팁 원문 불일치는 별도 검토.

이번 추가 테스트의 **12가지 문맥은 합성 모델**이다. 원문 12개 전체의 실제 전이/최적화 검증과 혼동하지 않는다. Library의 실물 등록은 확인했으나 이번 실행에서는 ZIP·V3.11의 원본 바이트를 다시 확보하지 못했으며, Q0/Q1 PASS를 선언하지 않는다.

## 4. 정상/실패 대조 및 정책 승격 게이트

정상: 서로 배타적인 12문맥, GCD+off-GCD 동시 사건, 선택 조건에 따른 다음 beat 변경, 관련 없는 전문화의 동일 입력 스키마.

실패: 미관측 상태 무시, 동일 beat의 GCD 둘, 동시 상태 변경 충돌, 풀 상대 시점 불일치, 원문 첫 인용 마커 불일치, 다른 원문 SHA, 미시험 분기, 중복 테스트 ID. 기존 V11 전문화의 장/표 수는 검사 범위가 아니다.

all_declared_cases_matched=true의 의미는 **주석과 선언된 기대 행동의 내부 재현**이다. original_source_meaning_independently_verified=false, timing_and_gcd_game_mechanics_verified=false, automatic_publish_allowed=false를 유지한다.

**변경 판단:** 현재는 검증 도구 및 반례 구조까지만 완료. 실제 고양 12개 사례와 다른 전문화의 정상·실패 역검증을 통해 유의미한 품질 개선이 확인되기 전에는 최상위 품질 정책을 개정하지 않는다.
