# WoW Rotation Engine

WoW Midnight 딜사이클 교본을 **검증 가능한 규칙 데이터 → HTML**로 만드는 프로젝트입니다.

> **현재 상태: GitHub CI + 실제 V2 코드 + V11 파생 규칙 데이터(PUBLIC)**. 7개 전문화의 구조화된 규칙 **메타데이터**를 이관했습니다. 와우헤드 원문 전체·대량 번역문과 기존 V11 HTML 전체는 게시하지 않았으며, 생성 뷰어는 실전 딜사이클 가이드가 아닙니다.

## 지금 사용하는 결과물

```bash
python -m engine.manual_site --output dist/manual/index.html
```

생성되는 `index.html`은 **단일 파일**입니다. GitHub Actions 성공 실행의 `wow-rotation-quick-reference-html` Artifact에서 내려받아 브라우저로 열 수 있습니다. 7개 전문화·영웅 특성 전환, 상황별 우선순위, 기술명/ID 검색, 대상 수 필터, 출처 링크가 들어 있습니다.

**현재 범위는 빠른 참조판입니다.** 원본 V11의 상세 발동 조건과 Advanced Tips 본문은 아직 데이터에 포함되지 않으므로, 이 HTML만 보고 게임 내 스킬 사용 여부를 결정해서는 안 됩니다. 사용 방법과 데이터 업데이트 방법은 [간략 교본 설명](docs/MANUAL_PREVIEW.md)을 보세요.

## ChatGPT Plus 로컬 로그인 시범 (추가 개발, PR #18)

[WSL2 / Linux 로컬 로그인 가이드](docs/CHATGPT_PLUS_LOCAL_LOGIN.md)에 공식 **Sign in with ChatGPT OAuth/PKCE + 서명된 ID Token 검증 + loopback 콜백 + 소유자 전용 계정 저장** 절차를 기록했습니다.

```bash
python -m pip install -r requirements-v2.txt
python -m engine.v2.chatgpt_signin status
# 사용자가 자기 PC에서 명시적으로 동의할 때만 실행
python -m engine.v2.chatgpt_signin login
```

`login`만으로 AI 추론은 실행하지 않습니다. `--list-models --confirm-credits-off`는 사용자가 앱 크레딧 사용 OFF를 직접 확인한 경우에만 별도 실행합니다. **개인 계정의 실로그인·모델 목록·AI 사용량은 아직 시험하지 않았습니다.** 로컬 저장소는 WSL/Linux 0700/0600 권한 시범이며, 자동 refresh와 Windows 전용 보안 키체인은 미구현입니다.

## ChatGPT Plus 구독 기반 AI 연결 (개발 중)

2026-11-11 논의와 실행 정책을 [ADR-001: ChatGPT Plus AI Runtime](docs/ADR_001_CHATGPT_PLUS_AI_RUNTIME.md)에 기록했습니다.

- Plus 유지, **추가 AI 결제 0원** 목표. 로컬 오픈소스 앱의 Sign in with ChatGPT 구독 연동을 우선 시험하며, 모델은 연결된 계정의 목록을 조회합니다.
- `engine/v2/ai_runtime.py`: 모델 독립적 `AIJob` → `AIProposal` 계약.
- `engine/v2/chatgpt_plan.py`: 이미 인증된 정식 OAuth 세션에 한정한 모델 조회·스트리밍 AI 제안 어댑터. `store=false`, `stream=true`; 사용량 초과 시 **중단, 유료 API 자동 전환 없음**.
- `engine/v2/ai_update_bridge.py`: AI의 **검토 대기** 결과를 기존 V11 UPDATE의 출처·텍스트·승인 검증에 연결. 기존 교본 자동 수정/배포 없음.
- 테스트는 네트워크·실제 구독 사용량을 소모하지 않는 **합성 테스트**입니다. 사용자의 실제 로그인·사용 가능 모델·한도·분석 품질은 검증되지 않았습니다.
- **안전 주의:** ChatGPT Settings → Usage에서 앱 크레딧 사용 허용을 끄고 사용량 제한을 설정해야 합니다. 클라이언트의 확인 플래그는 서버 측 결제 차단 증명과 다릅니다.
- 구버전 `ai_proposals.py`의 별도 API 키 전송 경로는 새 무료 연동 경로에 연결하지 않습니다.

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

## Issue #5: 동적 검토 UI · 게시 안전 게이트

```bash
python -m engine.review_ui --output dist/review/index.html
python -m engine.review_audit --output dist/review-audit.json
```

- `dist/review/index.html`: 7개 전문화 및 영웅 특성별 규칙을 보는 **비실전 검토용 HTML**. JSON 등록 목록에서 메뉴 자동 생성.
- `dist/review-audit.json`: 177개 조건 미해석, 178개 한국어 이름 레코드 미검증 등의 게시 차단 사유 출력.
- 원문 전체·상세 Advanced Tips는 아직 실전 가이드로 게시하지 않음.
- 상세 범위: [docs/REVIEW_UI.md](docs/REVIEW_UI.md).


## 한국어 주문명 검증: Issue #5 후속

```bash
python -m engine.spell_names audit --output dist/spell-name-audit.json
```

이는 176개 주문 ID의 검증 대기 현황을 검사합니다. **Blizzard API는 일반 CI에서 호출하지 않습니다.**
자격증명을 GitHub Secrets에 등록한 경우에만 수동 Actions `Collect Blizzard ko_KR spell names`로 증거를 수집할 수 있습니다. 관측 결과는 기존 명칭을 자동 변경하거나 승인하지 않습니다. 상세: [한국어 주문명 검증](docs/SPELL_NAMES.md).

## 딜사이클 조건식 검토 워크리스트

```bash
python -m engine.condition_worklist --output dist/condition-worklist.json
```

177개 우선순위 전체의 검토 상태를 출력합니다. 일부 **구문적으로 분석 가능한 조건은 실제 기술 사용 충분조건이 아닙니다.** 현재 냉기 마법사 빙결 중첩 조건 2개는 출처 외부 대조를 기다리는 **부분 후보**로만 수록했고, 나머지 175개 행은 미정규화 상태입니다. AI·코드 모두 미검증 규칙을 자동 승인하지 않습니다.

세부 설계: [Condition Worklist](docs/CONDITION_WORKLIST.md).

## 원문 변경 감지 실험 (Issue #5)

```bash
python -m engine.source_snapshots capture --input examples/synthetic-source-before.json --output dist/synthetic-source-before.json
python -m engine.source_snapshots capture --input examples/synthetic-source-after.json --output dist/synthetic-source-after.json
python -m engine.source_snapshots diff --previous dist/synthetic-source-before.json --current dist/synthetic-source-after.json --output dist/synthetic-source-diff.json
```

위 입력은 **완전 합성 문장**입니다. 원문 텍스트를 공개 Artifact에 보관하지 않고 해시만 비교합니다. 결과는 변경 관측 항목의 검토 후보이며 자동 번역·자동 게시와 무관합니다. 상세: [Source Evidence Snapshot](docs/SOURCE_SNAPSHOTS.md).


## 공식 주문명 404·불일치 검토

```bash
python -m engine.spell_triage --output dist/spell-review-queue.json
python -m engine.client_spell_probe --output dist/WoWRotationSpellProbe
```

2026-11-10 공식 API 조회에서 발견된 25개 404와 1개 명칭 불일치를 **실제 우선순위 177행에 미치는 영향**으로 분류합니다. P0는 혹한의 쐐기(4개 행), P1은 기술명 불일치 1개, P2는 기타 사전 전용 404 24개입니다. [검토·클라이언트 교차확인 가이드](docs/SPELL_TRIAGE.md).
