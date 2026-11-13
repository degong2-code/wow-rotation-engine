# Gameplay Decision QA — 원문 근거가 있는 실제 판단 규칙 감사 (2026-11-12)

## 위치와 목표

원문 취득·WHML 표시 조건의 범위 보존 다음 단계다. ChatGPT가 **비공개 WHML의 실제 기술·툴팁을 읽고 직접 주석을 붙인** 우선순위/오프너 규칙과 전투 상태별 예상 행동을 대조한다. 프로그램이 스킬 이름·임계값·게임 로직을 만들어내지 않는다.

사용 모듈: `engine.gameplay_decision_qa`. 입력은 `editorial-evidence-private.json` 및 별도로 작성한 `decision-annotations-private.json`, 출력은 원문을 제외한 `gameplay-decision-audit.json`이다.

## 주석 단위

각 규칙에 `id`, `kind`(priority/opener), `context`(영웅·ST/AoE·물약 등의 원문 적용범위), `when`(전투 상태 조건 AND), `action`, `reason`, `exceptions`, `evidence`(guide-body SHA-256·원문 start/end)를 기록한다. priority 규칙은 `rank`(작을수록 우선), opener 규칙은 `step`(작을수록 선시전)을 사용하며 나머지는 null로 둔다.

각 반례에는 `kind`, `context`, `state`, `expected_action` 또는 오프너의 `expected_actions`를 기록한다. 숫자 임계·발동·영웅 변경·특성 ON/OFF·물약별 실제 기술 변화 등 **행동이 갈리는 상태**를 중심으로 준비한다. 최소 개수를 맞추려고 가짜 경우를 만들지 않는다.

## 판정과 실패 차단

| 발견 사항 | 판정 |
|---|---|
| 적용되는 규칙 중 더 높은 순위의 조건값이 빠짐 | `underdetermined`; 하위 filler를 임의로 선택하지 않음 |
| 동일 상태에서 동일 최고 순위에 서로 다른 행동 | `ambiguous` |
| 기대 행동/오프너가 실제 주석 규칙과 다름 | `mismatch` |
| 어떤 규칙도 맞지 않음 | `no_rule` |
| 오프너 단계가 1·3처럼 비연속이거나 한 단계에서 행동 충돌 | 검토 보류 |
| 근거 원문 SHA/오프셋이 불일치 | `invalid_source_evidence` |
| 규칙의 예외가 설명 문장에만 있고 조건식으로 반영되지 않음 | `unmodeled_rule_exceptions` |
| 하나 이상의 규칙을 테스트한 사례 없음 | `unexercised_rule_branches` |

규칙의 `reason`은 필수지만 해당 해석이 실제로 올바른지는 **이 검사기가 증명하지 못한다**. 단순히 출처 위치를 가리키기만 하는 것으로 게임 정확성을 보장할 수도 없다. 경우별 검사 결과에서 작성자가 붙인 사례 이름, 기술명, 원문 문장은 공개하지 않고 번호·오류 코드·건수만 보고한다.

## 개발 환경 실행

```bash
python -m engine.gameplay_decision_qa \
  --source-packet dist/private_sources/spec/editorial-evidence-private.json \
  --annotations dist/private_sources/spec/decision-annotations-private.json \
  --report dist/private_sources/spec/gameplay-decision-audit.json
```

검증 완료: 합성 버프 ON/OFF, 중첩 2/3/4 경계, 상위 우선순위 불명, 동순위 충돌, 물약별 오프너 시퀀스 차이, 누락 단계, 원문 지문/오프셋 오류, 미시험 분기, 문장형 예외, 사례 ID 비공개 처리.

**검증하지 않은 것:** 실제 고양·생존·비전의 전문화별 기술 행동과 임계값이 원문에 정확히 대응하는지. 세 전문화는 현재 원문·조건/툴팁 범위 확보까지 검증됐으며 실제 Q0/Q1 주석 작성과 반례 검증은 다음 콘텐츠 작업이다.

집필 내용은 Q0 사실 검증→Q1 다음 행동·상위 우선순위 검증→Q2/Q3 이해·실전 사용성→Q4 비대상 HTML 보존/기능 검증 순서로 검토한다. 모든 주석 사례가 일치해도 `gameplay_meaning_verified=false`, `automatic_publish_allowed=false`다. PUBLIC GitHub에 개인 원문·주석을 업로드하지 않는다.


## 실제 전문화 원문 적용(2026-11-12)

[고양 주술사 폭풍인도자 단일 우선순위 13개 상태](ENHANCEMENT_ST_DECISION_QA_20261112.md)는 사용자 확인 12.1.5 WHML 지문과 직접 HTTP 취득본이 일치할 때만 검증한다. 원문 우선순위 9행/편집 규칙 10개, 중첩·발동·쿨다운 관련 13개 사례 모두 **모델 내부 일치**. 4중첩/상위 기술 모두 불가 상태의 `no_rule` 반례도 의도적으로 발견. UI 코드·원문 근거에서 게임 메커니즘을 무조건 확정하지 않으며 Q0/Q1 전체 PASS는 아님.


## 2026-11-12 과거 오탐 반례 추가

[역검증](HISTORICAL_REGRESSION_AUDIT_20261112.md): 인용된 행동 마커를 검증할 때 **첫 번째 실제 행동 근거 span**에서 찾아야 한다. 뒤쪽에 붙인 `?` 툴팁에만 나온 기술을 행동 근거로 오인하지 않는다. 한 상태에서 상위 우선순위 규칙의 조건값이 누락되어 `underdetermined`이거나 동순위 다른 기술 때문에 `ambiguous`이면 하위/같은 순위 규칙의 실제 승리 시험으로 인정하지 않는다. 바뀐 로직은 `tests/test_gameplay_decision_qa.py`에서 과거 실패 패턴의 **합성 대조**로 시험했고, 기존 실제 고양 13상태 원문 검증도 별도 유지했다.
