# WoW Rotation Engine

WoW Midnight 딜사이클 교본을 **검증 가능한 규칙 데이터 → HTML**로 만드는 프로젝트입니다.

> **현재 상태: GitHub CI + 실제 V2 코드 + V11 파생 규칙 데이터(PUBLIC)**. 7개 전문화의 구조화된 규칙 **메타데이터**를 이관했습니다. 와우헤드 원문 전체·대량 번역문과 기존 V11 HTML 전체는 게시하지 않았으며, 생성 뷰어는 실전 딜사이클 가이드가 아닙니다.

## 시작

Python 3.11+ 표준 라이브러리만 사용합니다.

```bash
python -m unittest discover -s tests -v
python -m engine validate --input examples/synthetic.json
python -m engine build --input examples/synthetic.json --output dist/index.html --allow-demo
python -m engine diff --before examples/synthetic.json --after examples/synthetic.json
```

- GitHub Actions: `.github/workflows/ci.yml` — 테스트, JSON 검증, 데모 HTML 빌드, Artifact.
- `engine/`: 안전한 조건 평가(unknown 지원), 최소 스키마 검사, 결정론적 HTML 렌더링, 변경 위험도 비교.
- `examples/`: 실제 게임을 주장하지 않는 합성 데이터.
- `docs/MIGRATION.md`: 로컬 V2 엔진을 공개 코드와 저작권 검토 대상 데이터로 분리해 순차 이관하는 계획.

## 운영 원칙

1. **PR-first**: 격리 브랜치 → 테스트 → PR 검토 → 병합.
2. **원문 근거 없는 자동 게시 금지**: 우선순위·조건·Advanced Tips 변경은 승인 전 배포하지 않습니다.
3. **주문 ID 우선**: 검증된 한국어 주문명만 최종 자료에 사용합니다.
4. **저작권·접근 정책 준수**: 와우헤드 원문 전체/전체 번역문, 개인 자격증명, API 키를 PUBLIC에 올리지 않습니다.
5. **동작·품질의 분리**: CI PASS는 코드 검증이지 게임 내 최적 딜사이클의 정확도 보증이 아닙니다.

본 저장소는 AI 분석·증분 업데이트 기능을 단계적으로 확장할 기반입니다.

## 원본 V2 코드 이관

원본 V2의 Python 모듈과 데이터 구조 검사기를 `engine/v2/`로 이관했습니다. 이식 전에 로컬 V2 자체는 18개 오프라인 테스트와 기준 V11 HTML SHA-256 재생성 검사를 통과했습니다. GitHub에서는 실제 공략 대신 합성 데이터로 재검증합니다. 범위·해시는 [이관 보고서](docs/V2_MIGRATION_STATUS.md)를 확인하세요.

## 공개 구조화 데이터 (V11 기반)

사용자 승인에 따라 V11에서 추출한 **분석용 메타데이터**를 `content/public/`에 이관했습니다: 전문화 7개, 우선순위 23개 표/177행, Advanced Tips 색인 79개, 주문 ID 176종(178개 이름 레코드). 13개 행동은 주문 ID가 미해결입니다.

**제한:** 기존 HTML 교본의 본문 전체를 올린 것은 아닙니다. 외부 원문과 한국어 주문명이 아직 독립 검증되지 않았고, 규칙의 조건은 대부분 미해석 상태이므로 이 데이터 자체로 실전 딜사이클을 자동 결정할 수 없습니다. 모든 규칙은 `pending`이며 자동 게시하지 않습니다.

```bash
python -m engine.public_data validate
python -m engine.public_data build --output dist/public-index.html
```

`dist/public-index.html`은 7개 전문화를 전환하며 순위·주문 ID·Advanced Tips 분류를 볼 수 있는 **데이터 검토 화면**입니다. 유효한 실전 공략으로 사용해서는 안 됩니다. 세부 범위는 [공개 데이터 정책](docs/PUBLIC_DATA.md)을 확인하세요.