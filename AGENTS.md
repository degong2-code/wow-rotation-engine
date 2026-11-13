# ROTATION TEXTBOOK — 작업자 및 AI 에이전트 진입 지침

이 저장소의 최종 제품은 **사용자가 WoW 전문화 이름만 입력하면 정확한 최신 원문을 분석해 V11 이상 한국어 단일 HTML 교본을 CREATE/UPDATE하는 ChatGPT 중심 제작 경험**이다. 독립 API 엔진, 복잡한 원문 수집기, 전문화별 미세 검증 도구가 제품이 아니다.

## 모든 개발·분석·인계 전 필독 (우선순위 순)

1. [docs/QUALITY_FIRST_POLICY.md §0](docs/QUALITY_FIRST_POLICY.md) — **사용자 확정 최상위 교본 중심·범위 통제 정책**. 이 문서가 최상위 정본이며 여기에 동일 정책을 복제하지 않는다.
2. [docs/CHAT_FIRST_PROJECT_INSTRUCTIONS.md](docs/CHAT_FIRST_PROJECT_INSTRUCTIONS.md) — ChatGPT 프로젝트/새 채팅 지침 및 실행 계약.
3. [docs/HANDOFF_CHAT_FIRST_CURRENT.md](docs/HANDOFF_CHAT_FIRST_CURRENT.md) — 활성 브랜치·최신 상태·검증 한계; HEAD/PR은 실제 GitHub에서 재확인.
4. [docs/CHAT_FIRST_PLAYBOOK.md](docs/CHAT_FIRST_PLAYBOOK.md) — 완전한 원문 이해 → 결정 조건 추출 → 교본 집필 → 내용·기능 검증.
5. [docs/EDITORIAL_QUALITY_PROTOCOL.md](docs/EDITORIAL_QUALITY_PROTOCOL.md), [docs/QUALITY_GENERALIZATION_CASEBOOK.md](docs/QUALITY_GENERALIZATION_CASEBOOK.md) — 내용 정확성과 정상/실패 대조.

## 작업을 시작할 때

- 수행할 변경이 **최종 한국어 교본의 정확성, 누락 방지, 이해도, 실전 사용성 또는 다른 전문화 반복 제작성 중 무엇을 개선하는지** 설명한다.
- 선택 ID·물약·특정 기술 한 건의 문제는 **실제 다음 행동에 영향을 주는 핵심 문제인 경우만** 조사 범위를 확장한다. 기존 절차로 해결하거나 REVIEW로 보류할 수 있으면 새 검사기를 만들지 않는다.
- **완성 교본/종단 간 CREATE·UPDATE 경로를 우선**한다. 자동 테스트 수·커밋 수·서류량·도구량을 품질 지표로 삼지 않는다. 반복적인 특수 사례 QA가 최종 교본 제작을 지연하면 작업을 중단하고 전체 제작 흐름으로 복귀한다.
- 원문 Gate A, 게임 의미 Q0/Q1, 이해/실전 Q2/Q3, HTML 보존 Q4를 구분한다. CI 성공을 실전 로테이션의 정확성으로 주장하지 않는다.
- main, 사용자 승인 정본 및 비공개 HTML·외부 장문 원문은 승인 없이 변경·공개하지 않는다. 현재 활성 개발 브랜치/PR은 인계 문서가 아니라 **실제 GitHub 상태**로 판단한다.

**중요:** 저장소의 AGENTS.md·Markdown은 ChatGPT의 모든 새 채팅에 자동 주입되는 계정/프로젝트 설정이 아니다. 프로젝트 설정에는 [CHAT_FIRST_PROJECT_INSTRUCTIONS](docs/CHAT_FIRST_PROJECT_INSTRUCTIONS.md)의 짧은 시작 지침을 등록해야 하며, 새 채팅은 이를 통해 최신 GitHub 문서를 읽는다.
