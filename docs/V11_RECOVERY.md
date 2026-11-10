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
```

- `engine/v2/import_v11.py`에 선택적 `destination_root` 추가: 기존 기본 동작은 유지
- `engine/v2/parity.py`: V2 importer/build의 바이트 동일 재조립을 임시 workspace에서 검사
- `engine/v2/detail_bridge.py`: `content/public/rules/*.json`의 그룹·규칙·팁 ID와 V11 개별 SHA-256을 대조한 후, 설명의 텍스트/마크업을 비공개 JSON으로 추출
- `tests/test_v11_parity.py`, `tests/test_v11_detail_bridge.py`: 실제 공략 텍스트 없는 합성 입력만 사용

**원본의 실제 구조를 별도 읽기 전용 로컬 조사로 대조한 결과** 7개 전문화 / 23개 표 / 177개 행 / 79개 팁의 출처 ID와 SHA-256 조합 지문이 공개 JSON과 전문화별로 일치했다. 이는 출처 대응·복원 가능성의 증거이며 현재 live 게임의 우선순위 적합성 증명은 아니다.

## 아직 구현되지 않은 연결

- 추출된 비공개 상세 JSON을 편집한 결과가 V2의 `content/guides/*.json` 장 HTML에 자동 반영되는 기능
- AI 원문 변경 해석 → 필요한 규칙·팁만 수정 → 리뷰 diff → 수정된 V11 HTML을 V2 builder로 재생성하는 경로
- 원본 전체 및 장문 번역문을 포함한 **공개** Pages 배포 (권리 확인 후 별도 결정)

## 다음 구현 순서

1. 비공개 상세 JSON의 변경 한 항목을 기존 `rule_id` 또는 `tip_id`에 매핑
2. 원래 장 HTML의 해당 문구·마크업만 바꾸고 나머지 원문·스타일·스크립트 바이트는 보존
3. V2 builder로 전체 교본 재조립; 변경 전·후 문서 diff 및 렌더 검증
4. 잠행 도적에서 처음 검증한 후 7개 전문화 공통 업데이트 경로로 일반화

**주의:** 현재 `manual_site.py`의 간략판은 별도 용도. 전체 V11 HTML을 간략판 CSS/JS로 재작성하지 않는다.
