# 원문 변경 감지 — Source Evidence Snapshot V1

## 이번 기능의 목적

와우헤드 URL이 등록된 전문화에 대해, 사용자가 적법하게 확보한 원문 구절을 `rule_id`별로 제공하면 **원문 텍스트를 GitHub에 저장하지 않고** 텍스트 지문(SHA-256)을 생성합니다. 이후 동일한 방식의 새 구절을 제공받아 비교하면 변경된 **관측 항목**을 검토 목록에 올립니다.

이 엔진은 공식 사이트를 직접 수집하지 않으며, 입력된 구절이 와우헤드의 실제 최신 원문이라고 검증하지도 않습니다.

## 사용 예시

먼저 `examples/synthetic-source-before.json`의 구조를 참고해 JSON 입력을 작성합니다. 이 예제는 **실제 공략 내용이 아닌 완전한 합성 문장**이며, URL은 규칙 ID를 연결하는 등록 키입니다.

```bash
python -m engine.source_snapshots capture --input MY_LOCAL_SOURCE_BEFORE.json --output dist/before.json
python -m engine.source_snapshots capture --input MY_LOCAL_SOURCE_AFTER.json --output dist/after.json
python -m engine.source_snapshots diff --previous dist/before.json --current dist/after.json --output dist/change-report.json
```

개발 CI에서는 `examples/synthetic-source-*.json` 두 개로 비교 과정만 시험합니다. 실제 공략 원문은 CI·GitHub Actions 입력·Artifact에 포함하지 않습니다.

## 비교 결과 해석

- `changed_observed_rules`: 앞뒤 입력에 모두 존재하는 규칙의 본문 지문이 바뀐 경우
- `newly_observed_rules`: 이전 입력에는 없고 새 입력에는 있는 규칙 (실제 공략에 추가됐다는 뜻 **아님**)
- `no_longer_observed_rules`: 이전 입력에는 있었지만 새 입력에는 없는 규칙 (실제 공략에서 삭제됐다는 뜻 **아님**)
- `unchanged_observed_rules`: 관측 본문 지문이 동일한 규칙
- `affected_rule_ids`: 위 세 가지 변화의 합집합. 내용이 달라진 행을 AI·사람이 재검토할 **후보** 목록

지문 계산은 Unicode NFC 정규화 후 연속 공백을 하나로 합치는 방식을 사용합니다. 동일한 구절에서 줄바꿈·연속 공백만 바뀐 경우는 변경되지 않은 것으로 취급합니다. 문장 의미가 같아도 단어가 바뀌면 해시가 달라지므로 의미 검증은 별도 작업입니다.

## 출처 안전 경계

- 입력한 문장이 **원문에 실재하는지**, 공식 사이트가 최신인지, 해당 `rule_id`에 정확히 대응하는지는 코드가 독립적으로 확인하지 못합니다.
- V11의 `v11_fragment_sha256`과 새 입력의 `observed_text_sha256`은 **서로 다른 표현을 해시한 값**입니다. 비교 대상으로 섞지 않습니다.
- `source_url`은 해당 전문화가 등록한 URL과 정확히 일치해야 합니다. 전체 원문이나 제3자 번역의 무단 재배포를 허용하는 기능이 아닙니다.
- 스냅샷에는 관측 구절의 텍스트가 아니라 ID·URL·시간·SHA-256만 있습니다.
- GitHub PUBLIC 저장소에 원문 입력 파일을 올리지 않도록 유의하세요. 원문 JSON을 직접 commit 또는 Actions 입력으로 전달하지 마세요.
- 모든 스냅샷·변경 보고서는 `automatic_publish_allowed:false`, `source_meaning_verified:false`를 유지합니다.
- 등록된 근거 해시나 주문 ID가 바뀌면 독립 검증 없이 자동 승인하지 않습니다.

## 향후 개발

1. 허용된 원문 접근·사용자 본문 입력 인터페이스 개발
2. 공식 접근이 확인된 원문을 안전한 실행 환경에서 수집하고 스냅샷화
3. 변경된 ID만 LLM에 분석 요청하되 원문 해석·번역·게임 조건의 검증 증거를 별도 수집
4. 검증된 조건·명칭·Advanced Tips만 승인하여 실제 교본에 게시

**현 단계의 핵심은 '업데이트 후보 탐지'이지, '딜사이클 자동 수정'이 아닙니다.**
