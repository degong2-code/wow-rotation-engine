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

## 실제 사용자 V11 로컬 통합 검증 (2026-11-10)

GitHub의 작업 브랜치 코드와 **Git Blob SHA-1이 일치하는 파일**을 격리 로컬 환경에 구성한 뒤, 개인 Library에서 복구한 **실제 V11 898,297바이트 원본**으로 실행했다. 검증 목적의 복사본 외에 공개 저장소/Actions에는 원본을 전송하지 않았다.

- `engine.v2.parity` 직접 실행: **7개 전문화, 60개 HTML 섹션, 176개 고유 주문 ID** 추출 후 V2로 재생성. 원본과 재생성 결과가 **바이트 단위 동일**, SHA-256 둘 다 `5d70279c4dd073eccef1f3b13565a8f555cd81c9f0a5b7eda7e3485e410742be`. **PASS**.
- 별도 읽기 전용 구조 대조: 복원한 비공개 7개 상세 JSON과 원본의 **23개 표 / 177개 행 / 79개 Tip**에 대해 ID, 근거 SHA-256, 실제 텍스트·마크업을 대조. **불일치 0건**.
- `engine.v2.patch_v11` 직접 실행: 잠행 도적 조건 1개에 **합성 HTML 주석 38바이트만** 추가, V2 재생성 **PASS**. 주석 제거 시 원본과 전체 바이트 동일.
- `engine.v2.private_changes` → `engine.v2.patch_v11` 연결 실행: 잠행 도적 Advanced Tip 1개의 **합성 주석 32바이트**만 후보 JSON에 추가 → 수정 1개 ID만 패치 생성 → V2 HTML 재생성 **PASS**. 주석 제거 시 원본과 전체 바이트 동일.
- 후자의 두 패치 시험에서 출처·본문 판정 입력은 앞서 전체 대조한 **비공개 상세 JSON을 읽는 로컬 검증용 어댑터**를 사용했다. 실제 `detail_bridge.py`의 공개 JSON 로더까지 결합한 무수정 통합 호출과 동일하다고 주장하지 않는다.
- 모든 합성 패치/수정 HTML은 실험 종료 후 삭제. 실제 V11 사용자 설명, 아이콘, 게임 공략 의미를 변경하지 않았다.

GitHub Actions의 PASS는 **합성 오프라인 단위 테스트**에 대한 증거이며, 위 실제 V11 로컬 증거와 별도로 기록한다.

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

## AI 부분 업데이트 — 명시적 실행 및 검토 게이트

`engine/v2/ai_proposals.py`는 사용자 제공 최신 공략의 **작은 발췌문**과 **기존 ID 1~8개**만 모델에 전달하는 선택적 모듈이다. 원문 수집·웹 스크래핑·자동 순위 변경·자동 게시 기능이 아니다.

```bash
# 사용자 소유 자료의 변경 근거를 로컬 텍스트 파일에 저장한 후
# 원본 교본 전체 대신 잠행 도적의 특정 ID 하나만 분석 대상으로 준비
python -m engine.v2.ai_proposals prepare \
  --detail /private/v11-details/rogue.json \
  --source /private/new-guide-excerpt.txt \
  --id rogue:rogue-rotation:table-1:row-1 \
  --output /private/ai-request.json

# 명시적으로 승인하여 API 전송할 때만 실행. 키는 환경변수로 입력.
# --model에는 본인 API 계정에서 실제 사용 가능한 모델 ID를 지정한다.
python -m engine.v2.ai_proposals suggest \
  --request /private/ai-request.json --send-api --model YOUR_MODEL_ID \
  --output /private/ai-proposal.json

# 근거 인용·대상 ID·기존 문구를 검증하고 승인되지 않은 리뷰 보고서 생성
python -m engine.v2.ai_proposals review \
  --detail /private/v11-details/rogue.json \
  --request /private/ai-request.json \
  --proposal /private/ai-proposal.json \
  --output /private/ai-review.json

# /private/ai-review.json을 직접 확인하고 아래 형식의 별도 승인 파일을 작성.
# 승인 파일이 없으면 어떤 후보도 수정된 교본 JSON으로 변환할 수 없음.
python -m engine.v2.ai_proposals approve \
  --detail /private/v11-details/rogue.json \
  --request /private/ai-request.json \
  --proposal /private/ai-proposal.json \
  --approval /private/ai-approval.json \
  --output /private/proposed/rogue.json

# 이후 기존 최소 패치 엔진 사용
python -m engine.v2.private_changes /private/v11-details/rogue.json \
  /private/proposed/rogue.json --output /private/rogue.patch.json
python -m engine.v2.patch_v11 /private/path/v11.html \
  /private/rogue.patch.json --output /private/updated.html
```

승인 파일 계약: 검토 보고서의 `proposal_sha256`을 그대로 지정하며, `approved_ids`에는 실제 반영할 항목만 작성한다.

```json
{
  "schema_version": "v11-ai-approval-v1",
  "proposal_sha256": "<검토 보고서의 proposal_sha256>",
  "approved_ids": ["rogue:rogue-rotation:table-1:row-1"]
}
```

승인 파일의 해시가 후보 JSON과 일치하지 않거나, 근거 인용이 입력 발췌문에 존재하지 않거나, 이전 문구가 기존 HTML 텍스트 노드 하나에 **정확히 한 번** 나타나지 않으면 반영을 중단한다. AI는 HTML을 직접 생성하지 않고 일반 텍스트 치환만 제안한다. 검토하지 않은 AI 출력은 **교본에 반영되지 않는다**.

### 데이터 경계

- 모든 요청·후보·검토 보고서·승인·수정 JSON 경로는 공개 저장소 외부여야 한다.
- 외부 전송은 `suggest --send-api`에서만 발생한다. `OPENAI_API_KEY`를 환경변수로 공급해야 하며 코드는 키를 기록·출력하지 않는다.
- API 요청은 `store: false`, `tool_choice: none`, 구조화 JSON 출력 설정을 사용한다. 다른 클라우드 서비스로의 전송 및 자료의 재사용 가능성은 사용자가 제공 자료의 권리를 확인해야 한다.
- 기존 V11 전체 HTML, 7개 전문화 전체 JSON을 **AI 모델에 통째로 전달하지 않는다**. 선택한 기존 설명 텍스트 및 최대 12,000자의 사용자 제공 발췌문만 입력한다.
- **AI가 틀릴 가능성은 남아 있다.** 인용 존재 여부는 사실 관계·게임 메커니즘의 진위를 증명하지 못하므로 사용자 검토가 필수다.
- 현재 API는 **코드 연결 및 합성 테스트만 완료**, 사용자 API 키로 실제 모델 응답을 수신하는 실서비스 호출은 수행하지 않았다.

## 아직 구현되지 않은 연결

- 실제 API 모델을 통한 새 공략 변경 해석의 실데이터 시범 실행·검토 (현재 API 요청·후보·근거 검증·명시적 승인 구조는 구현됨)
- 업데이트 결과의 원본 대비 사용자 UI 실제 브라우저 확인 및 이력 관리
- 원본 전체 및 장문 번역문을 포함한 **공개** Pages 배포 (권리 확인 후 별도 결정)

## 다음 구현 순서

1. 실데이터 추출·부분 변경 실험의 로컬 검증용 어댑터를 **정식 `detail_bridge.py` 공개 메타데이터 대조 경로**로 교체하고 1개 수정 시나리오 재검증
2. 사용자 제공 새 공략 발췌문으로 AI 후보 제안·사람 검토를 실행하고 원문 대비 의미 왜곡을 평가
3. 원본 대비 변경 요소만 diff 및 실제 브라우저 확인
4. 출판 권리를 검토한 배포 콘텐츠만 Pages에 게시

**주의:** 현재 `manual_site.py`의 간략판은 별도 용도. 전체 V11 HTML을 간략판 CSS/JS로 재작성하지 않는다.
