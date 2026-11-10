# V11 보존형 엔진 복원 — 비공개 상세 콘텐츠 연결

## 제품 방향

**최종 사용자 화면은 기존 V11 HTML**이다. 현재의 간략 참조판 `engine/manual_site.py`를 전체 교본의 새로운 디자인으로 사용하지 않는다. V2의 HTML 템플릿, 전문화별 장 HTML, 아이콘·툴팁·메뉴와 동일한 화면을 유지한다. 원본과 변경 없는 재생성 결과는 SHA-256까지 동일해야 한다.

## 원본 기준

- 사용자 소유 V11 HTML: **898,297 bytes**, SHA-256 `5d70279c4dd073eccef1f3b13565a8f555cd81c9f0a5b7eda7e3485e410742be`
- 실제 V11 내용은 GitHub 공개 저장소에 **저장하지 않음**
- V11의 게임 내 정확도, 원문 공략 재게시 권리는 SHA 일치만으로 입증되지 않음

## 구현된 실행 경로

**개인 환경의 원본을 사용**하며 GitHub Actions에는 실제 HTML을 업로드하지 않는다.

```bash
# 원본 → V2 임시 workspace 추출 → 원본 HTML 재조립 (결과는 SHA·개수만 출력)
python -m engine.v2.parity /private/path/v11.html

# 원본에서 조건 177행·Advanced Tips 79개를 public ID/해시 기준으로 대응
# --output-dir는 GitHub 작업 트리 바깥의 비공개 경로여야 함
python -m engine.v2.detail_bridge /private/path/v11.html --output-dir /private/v11-details

# 수정할 조건 또는 팁의 ID/원본 해시를 포함한 비공개 패치 JSON을 적용.
# 대상 요소의 내부 HTML만 바꾼 뒤 기존 V2 builder로 HTML을 재생성한다.
python -m engine.v2.patch_v11 /private/path/v11.html /private/patch.json --output /private/updated.html
```

- `engine/v2/import_v11.py`에 선택적 `destination_root` 추가: 기존 기본 동작은 유지
- `engine/v2/parity.py`: V2 importer/build의 바이트 동일 재조립을 임시 workspace에서 검사
- `engine/v2/detail_bridge.py`: `content/public/rules/*.json`의 그룹·규칙·팁 ID와 V11 개별 SHA-256을 대조한 후, 설명의 텍스트/마크업을 비공개 JSON으로 추출
- `engine/v2/patch_v11.py`: 비공개 변경 JSON의 `rule_id`/`tip_id`와 원본 증거 해시를 검증하고 해당 HTML 요소의 내부만 변경. 이후 기존 V2 importer/builder로 정확히 재조립; 다른 콘텐츠 바이트는 보존
- `tests/test_v11_parity.py`, `tests/test_v11_detail_bridge.py`, `tests/test_v11_patch.py`: 실제 공략 텍스트 없는 합성 입력만 사용

**원본의 실제 구조를 별도 읽기 전용 로컬 조사로 대조한 결과** 7개 전문화 / 23개 표 / 177개 행 / 79개 팁의 출처 ID와 SHA-256 조합 지문이 공개 JSON과 전문화별로 일치했다. 이는 출처 대응·복원 가능성의 증거이며 현재 live 게임의 우선순위 적합성 증명은 아니다.

## 비공개 패치 JSON 계약

`patch_v11.py`는 직접 텍스트를 생성하지 않는다. AI 또는 사용자가 작성·검토한 **비공개 변경 제안**을 받아 기존 ID와 출처 지문을 검사한다. 변경 대상은 `kind=rule`의 `condition` 내부 또는 `kind=tip`의 항목 내부다. JSON 예시의 괄호 부분은 개인 작업공간의 실제 값으로 치환한다.

```json
{
  "schema_version": "v11-private-patch-v1",
  "baseline_v11_sha256": "<원본 V11 SHA-256>",
  "updates": [
    {
      "kind": "rule",
      "id": "rogue:rogue-rotation:table-1:row-1",
      "expected_source_sha256": "<비공개 상세 JSON에서 해당 행의 source_fragment_sha256>",
      "new_inner_html": "<b>검토 완료한 교체 내용</b>"
    }
  ]
}
```

`new_inner_html`은 **해당 셀의 내부 마크업**이며 전체 `<td>`나 `<p>` 태그가 아니다. 원본 DOM 외곽 태그·CSS·JS·아이콘·메뉴는 그대로 유지한다. 변경 결과물은 공개 작업 트리 바깥에만 저장되며 원본 파일을 덮어쓰지 않는다. 허용되지 않은 스크립트·이벤트 핸들러는 차단한다.

## 아직 구현되지 않은 연결

- 실제 공략 변경의 AI 의미 비교 → 리뷰된 `updates` 후보 생성·승인 단계 (현재는 사람이 비공개 패치 JSON을 제공)
- 업데이트 결과의 원본 대비 사용자 UI 실제 브라우저 확인 및 이력 관리
- 원본 전체 및 장문 번역문을 포함한 **공개** Pages 배포 (권리 확인 후 별도 결정)

## 다음 구현 순서

1. 현재 `patch_v11.py`를 개인 V11 원본에 **실제로 적용·실행**해 임시 변경 1건 및 V2 재생성 결과 검증 (GitHub CI는 합성 테스트만 수행)
2. AI가 실제 원문 변경에서 필요한 `updates`만 제안하도록 연결; 사람 검토 후 반영
3. 원본 대비 변경 요소만 diff 및 실제 브라우저 확인
4. 출판 권리를 검토한 배포 콘텐츠만 Pages에 게시

**주의:** 현재 `manual_site.py`의 간략판은 별도 용도. 전체 V11 HTML을 간략판 CSS/JS로 재작성하지 않는다.
