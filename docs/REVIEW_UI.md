# Issue #5: 데이터 기반 HTML 검토 UI 및 게시 안전 게이트

## 실행

```bash
python -m engine.public_data validate
python -m engine.review_audit --output dist/review-audit.json
python -m engine.review_ui --output dist/review/index.html
python -m unittest discover -s tests -p 'test_*.py' -v
```

## 구현 범위

- `manifest.json`의 전문화 목록을 기준으로 메뉴 생성. 전문화 추가 시 코드 수정 없이 메뉴가 자동 증가합니다.
- 전문화별 영웅 특성 버튼·단일/광역·대상수·전투 구간에 따른 우선순위 **메타데이터** 조회.
- 기존 V11의 다크/골드 디자인 언어 반영. 원본의 통합 기능 전체나 게임 내 회전 성능을 재현했다는 의미는 아닙니다.
- Advanced Tips 79개 색인을 주제별로 묶어 보여 줍니다. **상세 공략 설명은 아직 포함되지 않습니다.**
- 모든 미검증 규칙의 출처 위치·V11 프래그먼트 SHA-256을 점검 화면에서 확인할 수 있습니다.
- `review_audit`는 전체 177행 조건 미해석/178개 한국어 명칭 레코드 미검증 등 차단 사유를 기계적으로 출력합니다.

## 명칭 검증 및 조건식 원칙

- 지금은 V11에서 상속받은 한국어 명칭입니다. 공식 한국어 spell DB와 직접 대조했다는 증거가 없습니다.
- **Spell ID + 공식 KR 이름 + 출처 + 확인 시점**이 모두 일치해야 `verified` 처리할 수 있습니다. AI가 임의 번역한 이름을 자동 승인하지 않습니다.
- `machine_predicates` 일부가 있어도 해당 조건은 충분하지 않으므로 우선순위 사용 여부를 자동 결정할 수 없습니다.
- `target_min: null`인 경우 게임 기준 숫자를 유추하지 않고 "대상 수 미지정"으로 표시합니다.
- `publish_ready`는 false이며 `--require-publish-ready` 옵션은 지금 의도적으로 실패합니다.

## 현재 비범위

- 176개 ID의 공식 한국어 DB 1:1 검증
- 모든 자연어 우선순위 조건의 실행 가능한 AST 변환
- 원문 내용 변경 비교 및 LLM 의미 분석
- V11 교본 HTML의 구조·텍스트·툴팁에 대한 동일성 보장
- 실전 가이드 GitHub Pages 공개

GitHub Actions는 검토용 HTML과 감사 JSON만 Artifact로 보관합니다. 콘텐츠 검증 뒤 실전 교본용 Pages 별도 배포 단계를 진행합니다.
