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

# 상세 JSON을 비공개 후보 디렉터리에 복사한 뒤 바뀐 본문/마크업만 수정·검토한다.
# 새 시전 조건이나 팁 내용은 AI가 추측 생성하지 않는다.
# 변경되지 않은 원본 주문 아이콘·툴팁 HTML은 보존한다.
python -m engine.v2.private_changes /private/v11-details/rogue.json /private/proposed/rogue.json --output /private/rogue.patch.json

# 변경된 항목만 V11 원본에 적용하고 기존 V2 builder로 HTML을 재생성한다.
python -m engine.v2.patch_v11 /private/path/v11.html /private/rogue.patch.json --output /private/updated.html
```

- `engine/v2/import_v11.py`에 선택적 `destination_root` 추가: 기존 기본 동작은 유지
- `engine/v2/parity.py`: V2 importer/build의 바이트 동일 재조립을 임시 workspace에서 검사
- `engine/v2/detail_bridge.py`: `content/public/rules/*.json`의 그룹·규칙·팁 ID와 V11 개별 SHA-256을 대조한 후, 설명의 텍스트/마크업을 비공개 JSON으로 추출
- `engine/v2/private_changes.py`: 원본 대비 검토된 상세 JSON의 변경된 `condition_html` 또는 Advanced Tip `html`만 자동 선별; 변경 없는 항목은 패치에 포함하지 않음. 원본 출처 지문과 아이콘 보존 확인
- `engine/v2/patch_v11.py`: 비공개 변경 JSON의 `rule_id`/`tip_id`와 원본 증거 해시를 검증하고 해당 HTML 요소의 내부만 변경. 이후 기존 V2 importer/builder로 정확히 재조립; 다른 콘텐츠 바이트는 보존. 기존 V11 이미지의 `onerror`는 **동일한 내용으로 보존**하는 경우 허용하지만 신규/변경된 이벤트 핸들러는 거부
- `tests/test_v11_parity.py`, `tests/test_v11_detail_bridge.py`, `tests/test_v11_patch.py`, `tests/test_v11_private_changes.py`: 실제 공략 텍스트 없는 합성 입력만 사용

**원본의 실제 구조를 별도 읽기 전용 로컬 조사로 대조한 결과** 7개 전문화 / 23개 표 / 177개 행 / 79개 팁의 출처 ID와 SHA-256 조합 지문이 공개 JSON과 전문화별로 일치했다. 이는 출처 대응·복원 가능성의 증거이며 현재 live 게임의 우선순위 적합성 증명은 아니다.

## 비공개 후보 JSON → 최소 패치 계약

`private_changes.py`는 기존 비공개 상세 JSON과 **검토된 수정 후보 JSON**을 비교한다. 동일한 `guide_id`, 동일한 V11 baseline, 동일한 `rule_id`/`tip_id`, 동일한 출처 지문이 필수다. 콘텐츠는 `condition_html` + 일치하는 `condition_text_ko` 또는 Advanced Tip `html` + `text_ko`에서만 변경할 수 있다.

수정된 규칙 1개라면 비공개 패치 JSON의 `updates`에 **해당 ID 1개만** 들어간다. 아무것도 바뀌지 않았으면 `updates: []`다. AI가 실제 공략 변경을 해석하는 기능은 아직 없으므로, 후보 내용은 사용자가 제공하거나 AI가 별도로 분석·검토한 입력이어야 한다.

생성되는 패치의 형태:

```json
{
  "schema_version": "v11-private-patch-v1",
  "baseline_v11_sha256": "<원본의 SHA-256>",
  "updates": [
    {
      "kind": "rule",
      "id": "rogue:rogue-rotation:table-1:row-1",
      "expected_source_sha256": "<해당 원본 조건의 SHA-256>",
      "new_inner_html": "<기존 주문 아이콘 등을 보존한 검토 완료 HTML 조각>"
    }
  ]
}
```

`new_inner_html`은 **해당 조건 셀/Advanced Tip의 내부**만 의미하며, 전체 `<td>` 또는 `<p>` 태그를 포함하지 않는다. 원본 CSS·JS·아이콘·외곽 DOM은 변경하지 않는다. 원본 V11이 이미 사용하던 이미지 오류 핸들러의 **동일한 보존**은 허용하지만, 신규 이벤트 코드·스크립트·실행 URL 및 기존 아이콘 삭제는 차단한다. 패치·출력 HTML은 GitHub 작업 트리 바깥의 비공개 경로에만 저장한다.

## 아직 구현되지 않은 연결

- 실제 공략 변경의 AI 의미 비교 → 수정 후보 상세 JSON 생성·검토 단계 (현재는 사람이 비공개 후보 JSON을 제공)
- 업데이트 결과의 원본 대비 사용자 UI 실제 브라우저 확인 및 이력 관리
- 원본 전체 및 장문 번역문을 포함한 **공개** Pages 배포 (권리 확인 후 별도 결정)

## 다음 구현 순서

1. 현재 `patch_v11.py`를 개인 V11 원본에 **실제로 적용·실행**해 임시 변경 1건 및 V2 재생성 결과 검증 (GitHub CI는 합성 테스트만 수행)
2. AI가 실제 원문 변경에서 필요한 상세 JSON 항목만 수정 제안하도록 연결; 사람 검토 후 `private_changes.py`로 최소 패치 생성
3. 원본 대비 변경 요소만 diff 및 실제 브라우저 확인
4. 출판 권리를 검토한 배포 콘텐츠만 Pages에 게시

**주의:** 현재 `manual_site.py`의 간략판은 별도 용도. 전체 V11 HTML을 간략판 CSS/JS로 재작성하지 않는다.
