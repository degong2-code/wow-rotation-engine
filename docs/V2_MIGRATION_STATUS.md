# 실제 V2 엔진 코드 이관 · 공개 범위

이 디렉터리는 **이전 로컬 `wow_rotation_engine_v2` 소스에서 가져온 실제 구현체**를 `engine/v2/`에 격리해 보존합니다. `docs/v2-origin-manifest.json`에 원본 모듈과 기준 V11 파일의 SHA-256을 기록했습니다.

## 이관한 것

- HTML 원형 보존 분할기, 템플릿 기반 정적 HTML 생성기
- 3값(참/거짓/알 수 없음) 조건 계약 평가기
- 우선순위 행과 Advanced Tips 추출기
- 원문 장 SHA / 행 SHA 추적, JSON Schema 검증, 덮어쓰기 방지
- 규칙 diff 및 변경 위험도 분류
- V11 초기 이관 도구, 색인/계약 검증 스크립트
- V11용 시각 템플릿 (별도 전문화 본문 제외)

## 이관하지 않은 것

와우헤드 자료에서 재구성한 7개 전문화의 전체 장 HTML, 규칙/고급 팁 JSON, 전체 한국어 번역본, V11 HTML과 Markdown 원본은 공개 저장소에 포함하지 않았습니다. **실제 V11과의 해시 재생성 및 177/79 건수 검증은 이 저장소에서 아직 수행하지 않았습니다.** 이전 로컬 V2에서 보고한 건수와 SHA는 참고용 출처 정보입니다.

## 테스트 범위

`tests/test_v2_migration.py`는 게임 내용이 아닌 합성 데이터를 이용해 스키마, 변환, 근거 추적, 정규화의 보수성, 변경 위험도를 검증합니다. **테스트 통과는 WoW 공략의 기계적/의미적 정확성에 대한 보증이 아닙니다.**

## 명령

```bash
python -m pip install -r requirements-v2.txt
python -m unittest discover -s tests -p 'test_*.py' -v
```

`python -m engine.v2.build` 같은 실제 교본 생성 명령은 등록된 승인 자료가 없는 동안 실행하지 않습니다. 공개 저장소의 초기 `engine` 빌드는 합성 데모만 생성합니다. 추후 공략 게시 라이선스, 주문 이름 및 근거를 검증한 뒤 실제 교본을 연결합니다.

## 2026-11-11 — ChatGPT-first 전환 (현재 활성 개발 방향)

사용자 평가에 따라 **기존 7개 전문화 V11의 직접 제작 품질을 최우선으로 인정**하고, 독립 AI API·OAuth·Codespaces·GitHub Actions AI 추론이 **사용자 경험상 불필요한 단계**가 되었다고 재판정했다.

- **활성 개발 정본:** [ADR-003](ADR_003_CHAT_FIRST_EDITORIAL.md), [Playbook](CHAT_FIRST_PLAYBOOK.md), [Source acquisition](SOURCE_ACQUISITION.md), [Project instructions](CHAT_FIRST_PROJECT_INSTRUCTIONS.md).
- **입력:** 사용자가 현재 ChatGPT 프로젝트 채팅에 전문화 이름만 입력 → GitHub 운영 지식/현재 공략/비공개 V11 원본을 실제 접근 확인 후 ChatGPT가 CREATE 또는 UPDATE.
- **출력:** 기존 V11 품질의 개인 단일 HTML. 비대상 기존 전문화 바이트 동일, 실제 UI 검증과 게임플레이 사실 검증을 별도 보고. 공개 GitHub에 원본 또는 결과 HTML 업로드 금지.
- **기존 자산:** PR #14~#16의 V11 원형 보존·최소 패치·신규 비전·표·아이콘·`?`/`!`·검증 코드 등은 **재사용**. PR #17~#19의 Plus OAuth/CI 실험은 **기록으로 보존하되 기본 경로에서 제외**.
- **새 브랜치:** `work/chat-first-v11-20261111`, PR #16의 V11 제작 코드 기반. 인증 실험 PR #17~#19에 의존하지 않는다. `main` 미병합.
- **원본 접근:** 현재 프로젝트/대화에서 `wow_rotation_manual_engine_v2.html` 898,297바이트, SHA-256 `5d70279c4dd073eccef1f3b13565a8f555cd81c9f0a5b7eda7e3485e410742be` 확인. 새 세션에서 실제 접근 여부는 매번 재확인 필요.
- **남은 게이트:** `비전 마법사` 1회 입력으로 실제 V11 수준 HTML 생성→개인 파일 제공, 원본 7개 바이트 동일 및 기능 검증. 이 시범을 통과해야 '한 문구 완성' 운영을 PASS라고 선언한다.

이 아래의 초기 V2 이관 설명은 당시 이력이며, 현재 사용자 경험의 최종 제품 경로로 강제하지 않는다.
