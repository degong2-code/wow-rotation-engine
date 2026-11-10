# WoW Rotation Engine

WoW Midnight 딜사이클 교본을 **검증 가능한 규칙 데이터 → HTML**로 만드는 프로젝트입니다.

> **현재 상태: GitHub CI bootstrap (PUBLIC)**. 이 저장소에는 엔진 개발용 코드와 *합성 테스트 데이터*만 있습니다. 이전 V2의 7개 전문화 실제 교본·와우헤드 번역 콘텐츠는 **아직 공개 이관하지 않았습니다**. 이 데모 HTML은 실전 딜사이클 가이드가 아닙니다.

## 시작

Python 3.11+ 표준 라이브러리만 사용합니다.

\`\`\`bash
python -m unittest discover -s tests -v
python -m engine validate --input examples/synthetic.json
python -m engine build --input examples/synthetic.json --output dist/index.html --allow-demo
python -m engine diff --before examples/synthetic.json --after examples/synthetic.json
\`\`\`

- GitHub Actions: \`.github/workflows/ci.yml\` — 테스트, JSON 검증, 데모 HTML 빌드, Artifact.
- \`engine/\`: 안전한 조건 평가(unknown 지원), 최소 스키마 검사, 결정론적 HTML 렌더링, 변경 위험도 비교.
- \`examples/\`: 실제 게임을 주장하지 않는 합성 데이터.
- \`docs/MIGRATION.md\`: 로컬 V2 엔진을 공개 코드와 저작권 검토 대상 데이터로 분리해 순차 이관하는 계획.

## 운영 원칙

1. **PR-first**: 격리 브랜치 → 테스트 → PR 검토 → 병합.
2. **원문 근거 없는 자동 게시 금지**: 우선순위·조건·Advanced Tips 변경은 승인 전 배포하지 않습니다.
3. **주문 ID 우선**: 검증된 한국어 주문명만 최종 자료에 사용합니다.
4. **저작권·접근 정책 준수**: 와우헤드 원문 전체/전체 번역문, 개인 자격증명, API 키를 PUBLIC에 올리지 않습니다.
5. **동작·품질의 분리**: CI PASS는 코드 검증이지 게임 내 최적 딜사이클의 정확도 보증이 아닙니다.

본 저장소는 AI 분석·증분 업데이트 기능을 단계적으로 확장할 기반입니다.
