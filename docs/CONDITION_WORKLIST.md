# 우선순위 조건식 워크리스트 — Issue #5

## 목적

사용자 편집 V11에서 가져온 7개 전문화의 23개 우선순위 표 / 177개 행을 **원본의 순번·주문 ID·근거 해시와 연결**하고, 조건을 단계적으로 정규화하기 위한 별도 데이터 레이어를 제공합니다.

**이 모듈은 딜사이클 추천기가 아닙니다.** 원문 구절의 일부(예: 빙결 6중첩)가 참이라도 더 높은 우선순위 기술, 발동 버프, GCD, 쿨기, 대상 선택 등 빠진 조건이 있을 수 있습니다.

## 실행 방법

```bash
python -m engine.condition_worklist --output dist/condition-worklist.json
python -m unittest discover -s tests -p 'test_*.py' -v
```

워크리스트에서는 규칙 ID·전문화·그룹·상황·주문 ID·원문 SHA-256과 현재 후보 상태를 확인합니다.

## 2개의 실제 V11 기반 **부분 후보** 예시

- 냉기 마법사 주문술사 단일 얼음창: 대상 빙결 ≥6중첩 (추출된 문장 조건의 **일부**).
- 냉기 마법사 서리불꽃 단일 얼음창: 대상 빙결 ≥12중첩 (추출된 문장 조건의 **일부**).

명시적으로 `completeness: partial`, `source_review: pending_external_verification`, `review: pending`, `automatic_publish_allowed: false`를 요구합니다. 이 수치 자체도 현재 패치·원본 의미에 대해 외부 검증을 완료한 사실이 아닙니다.

### 참·거짓·미확인과 추천 허가의 구분

- `syntactic_predicate_result`: 후보 AST 일부만 평가한 결과(true/false/null).
- `rotation_applicability`: 언제나 null, 전체 스킬 사용 판단은 불가.
- `can_recommend_ability`: 언제나 false, 후보 AST만으로 게임 내 추천 금지.
- `debuff:freezing`: 대상에게 적용된 중첩 값. 플레이어 버프(`buff:`)와 분리합니다.

**조건 일부가 거짓이라도** 실행 가능한 전체 로테이션 규칙이 검증됐다는 뜻은 아니며, 이 결과를 다른 기술 사용 결정으로 환산해서는 안 됩니다.

## 근거와 변경 검증

후보마다 본문 JSON의 `rule_id`, `guide_id`, `spell_id`, `source_fragment_sha256`가 공개 원본 데이터와 일치해야 합니다. 하나라도 달라지면 빌드를 실패시킵니다.

사용자가 제공한 V11은 외부 원문과 독립 대조되지 않았습니다. 해당 출처 근거를 검증하기 전에는 **완전 검증된 AST 또는 권장 순서라고 표시하지 않습니다.** 현재 2개 부분 후보 / 175개 미정규화 / 0개 승인입니다.

## 후속 개발

1. 외부 허용 원문 텍스트와 각 행을 쌍으로 연결하고 조건 분리·부정 표현 검토
2. 누락된 발동, 쿨다운, 자원, 영웅 특성, 대상 수 등을 완전한 AST로 모델링
3. 최적화 변경은 원문·패치 버전·주문 ID 증거와 비교해 승인
4. 미검증 전용 UI와 실전 가이드 배포를 계속 분리
