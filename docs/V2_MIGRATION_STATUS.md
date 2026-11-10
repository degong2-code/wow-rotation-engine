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

## 2026-11-11 — V11 CREATE/UPDATE 및 Plus AI 실행 계층 상태 (후속 개발)

이 문서 위의 '초기 이관' 설명은 **해당 당시의 스냅샷**이다. 이후 원본을 바이트 단위로 유지하는 V11 Import/Build/UPDATE, 신규 비전 CREATE 파일럿 및 V11 표·`?`/`!`·기술 흐름 재사용이 별도 Draft PR에서 개발되었다.

| PR | 주요 역할 | 상태 |
|---|---|---|
| #14 | 기존 V11 파생 구조의 Import/Build/UPDATE, 바이트 동등성 검증 | Draft / 미병합 |
| #15 | 비전 신규 등록 파일럿 | Draft / 미병합 |
| #16 | V11 표현·메커니즘·근거 위치 감사 | Draft / 미병합 |
| **#17** | **ChatGPT Plus AI Provider / 정책 ADR / 기존 UPDATE 검토 계층 연결** | **Draft / 미병합** |

**이번 논의의 결정 및 구현 정본:** [ADR-001 — ChatGPT Plus AI Runtime](ADR_001_CHATGPT_PLUS_AI_RUNTIME.md). Plus를 유지하며 추가 AI 비용을 발생시키지 않는 로컬 연동을 우선한다. Sol/Luna는 고정하지 않고 계정 모델 목록과 실제 품질을 비교한다. GPT-6 High 일반 채팅을 무제한 외부 API로 취급하지 않는다.

**엔진 구분:** `engine/v2/ai_runtime.py`는 제공자 독립 작업 계약, `chatgpt_plan.py`는 검증된 OAuth 세션 후 Responses 요청, `ai_update_bridge.py`는 기존 원문 증거·승인 게이트로 연결한다. CI는 합성 요청만 사용하며 로그인·실사용량을 소모하지 않는다. 개인 Plus 사용자 OAuth 동의/실제 모델 조회/한도 실측, 범용 CREATE 전환은 다음 단계다.

**변경 금지 정책:** 기존 V11 7개 본문·개인 원본, 비공개 상세 공략 데이터, 계정 토큰/키 비공개. 생성된 공략 검증·사용자 승인 없이 자동 게시 금지. 모든 PR은 명시적 승인 전 `main` 병합/Pages 게시 금지.
