# ADR-002 — 로컬 PC 없이 GitHub + ChatGPT Plus AI를 사용할 수 있는가?

- 일자: 2026-11-11 (KST)
- 상태: **인증 적합성 판정 완료 / 사용자 계정 실호출 미검증 / 범용 CREATE 개발 보류**
- 범위: 공개 저장소 `degong2-code/wow-rotation-engine`, ChatGPT Plus 유지, AI 추가 결제 0원, 모바일 브라우저·GitHub만 사용
- 이전 구현: PR #17 구독형 Responses 후보 계층, PR #18 로컬 PC OAuth/PKCE 로그인. 둘 다 GitHub 전용 **실사용 성공을 증명하지 않음**.

## 확정 사실: 네 가지 구분

| 경로 | PC 없이 작업? | 구독 포함 사용량으로 AI? | 실제 운용 판정 |
|---|---|---|---|
| GitHub Actions만 + SIWC 로그인 토큰 | 별도 인증 문제 | 이론적 API 기능과 별개 | **NO-GO**. 공개 저장소·Actions Secrets에서 장기 토큰 저장 및 OAuth loopback은 지원 근거 부족; 해당 방식 채택 금지 |
| GitHub Codespaces + **Codex CLI Device Code** | **가능한 공식 사용자 로그인 경로**(모바일 브라우저) | Codex가 사용자의 ChatGPT 구독으로 로그인하면 구독 한도 사용 | **CONDITIONAL GO**. 사용자가 Codespace에서 직접 인증·짧은 `codex exec`를 성공시킨 후에만 증명 |
| GitHub Codespaces + 우리 **SIWC 직접 Responses OAuth** | 현재 구현은 127.0.0.1 callback 전용 | 토큰을 받은 후 가능 | **NO-GO for current implementation**. 휴대전화 브라우저의 loopback과 Codespace의 loopback이 서로 다름. 공식 SIWC Device Code 지원 확인되지 않음. callback 공개 전달·임의 URL 재작성 금지 |
| GitHub Actions + 별도 무료 모델 API | 가능 | Plus 사용량과 무관 | 기술적 대체 가능. 무료 한도·계정 연결·자료 처리 정책의 별도 확인 필요 |

**핵심:** GitHub 자체의 코드 실행은 가능하나, **GitHub Actions가 Plus 계정의 AI 토큰을 안전하고 허용된 방식으로 자동 취득·지속 보관한다는 증거는 없다.** 이를 이미 해결한 것처럼 안내하지 않는다.

## 공식 근거와 차이

1. **SIWC 약관 (2026-11-04)**: [OpenAI SIWC Terms](https://openai.com/policies/sign-in-with-chatgpt-terms/) §1 — 인증 토큰의 **지속 저장은 로컬 사용자 통제 환경**이어야 하고 원격·관리형 환경에는 지속 저장하지 말라고 명시. §3.1 — 요청은 사용자의 로컬 또는 사용자가 단독 통제하는 원격 런타임에서 발생해야 하며, 백그라운드 사용에는 명시적 승인이 필요. GitHub Actions Secrets에 사용자 SIWC 토큰을 영구 보관하는 설계를 채택하지 않는다.
2. [SIWC Registration and sign-in](https://developers.openai.com/siwc/token-sharing-open-source/sign-in): 신규 동적 등록은 정확한 `http://127.0.0.1:<port>/auth/callback`; 브라우저가 있는 장치에서 callback이 이루어져야 함.
3. [SIWC Self-hosted VMs](https://developers.openai.com/siwc/token-sharing-open-source/self-hosted-vms): 로컬에서 OAuth 후 관리 대상 VM으로 보호된 자격증명 전송을 안내하지만, 최신 SIWC 약관의 **지속적인 원격 토큰 보관 금지 문구와 운영상 긴장 관계**가 있다. 약관을 우선 기준으로 삼고, VM/Actions 보관은 공식 지원 확인 전 사용하지 않는다.
4. [Codex CLI Authentication — headless device code](https://learn.chatgpt.com/docs/auth): 별도 공식 Codex CLI는 원격·headless 환경에서 `codex login --device-auth` 지원(베타). 사용자가 ChatGPT Security에서 Device Code 로그인 허용 후 **폰 브라우저에서 표시된 URL과 일회용 코드로 승인** 가능.
5. [Codex non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode): `codex exec`로 비대화형 요청 및 `--output-schema` JSON 출력을 지원. **기존 우리 앱의 SIWC 직접 Responses 경로와 동일한 인증 절차가 아니다.**
6. [Codex account auth in CI/CD (advanced)](https://learn.chatgpt.com/docs/auth/ci-cd-auth): ChatGPT-managed `auth.json`을 사용하는 CI는 **신뢰할 수 있는 비공개 인프라용** 고급 절차, 공식 경고: **공개 또는 오픈소스 저장소에 사용하지 말 것**. 사용자 공개 제품 저장소에 인증 캐시를 CI Secrets/Artifacts/워크플로 출력으로 넣지 않는다.
7. [GitHub Codespaces](https://github.com/features/codespaces), [billing](https://docs.github.com/en/billing/reference/product-usage-included): 브라우저에서 사용하는 GitHub 클라우드 개발 환경. GitHub Free 개인 계정의 월별 무료 사용량은 120 core-hours/15 GB-month(2-core 런타임 약 60시간). 유료 사용량이 발생하지 않도록 개인 계정의 예산·지출 차단 확인. 조직 소유의 Codespace는 무료 정책이 다를 수 있음.

## 유일한 우선 실측 후보: GitHub Codespaces + Codex CLI (PC 없이)

본 **1차 검증은 Codex CLI에 대한 것이며, SIWC 무료 API 연동의 검증이 아니다.** 향후 사용자 경험을 제공하는 우리 웹앱의 기본 AI API 경로로 사용할 수 있는지 결론 내리려면 Codex CLI가 반환하는 구조화된 결과를 `AIProvider`에 전달하는 조정 계층이 추가로 필요하다. 이는 **실제 1회 로그인·실행이 확인된 뒤** 진행한다.

사용자 본인의 모바일 브라우저에서:
1. 공개 프로젝트 GitHub 페이지 → Code → Codespaces → Create codespace on `work/github-only-plus-feasibility-20261111` (개인 GitHub 계정의 포함 무료 시간·지출 차단 여부 먼저 확인).
2. GitHub Codespace의 **Terminal**에서 Node/npm 및 Codex CLI 설치: `npm install -g @openai/codex`. 실제 설치 가능 여부는 Codespace에서 확인해야 한다. API 키를 생성하거나 `OPENAI_API_KEY`를 설정하지 않는다.
3. ChatGPT 앱의 **Settings → Security**에서 Device Code 로그인 허용(해당 UI가 나타나는 경우). 이후 Codespace 터미널에서 `codex login --device-auth` 실행. 터미널이 제시하는 공식 URL을 **사용자가 직접 모바일 브라우저**에서 열어 일회용 코드를 입력한다. 비밀번호, 인증 코드, `auth.json`, access/refresh token을 채팅·GitHub Issue/PR·Actions Secret에 공유하지 않는다.
4. GitHub Codespace에서 먼저 `bash scripts/probe_codespaces_plus.sh --preflight`를 실행해 **외부 모델 요청 없이** 설치·접속 상태를 확인할 수 있다. 로그인이 완료됐다면 이어서 `codex login status` 실행. 출력의 **ChatGPT-managed 로그인 방식**을 확인한다. 상세 토큰 파일은 열거나 전송하지 않는다.
5. 다음 **단일 최소 요청**으로 AI 실행 여부 검증(명시적으로 사용자 원할 때만): `bash scripts/probe_codespaces_plus.sh --probe --confirm-plus-usage`는 사용자가 동의 옵션을 넣을 때만 **읽기 전용** Codex 모델 요청을 한 번 실행하고 JSON Schema 검증 후 임시 파일을 삭제한다. 유료 API 키가 환경 변수에 있거나 ChatGPT 인증을 확인하지 못하면 모델 호출 전 차단한다.

   직접 실행 예시:
   `codex exec --ephemeral --sandbox read-only "Reply with exactly: ROTATION_AI_OK"`
   성공 판정: 실제 추론이 종료되고 정확한 응답 수신, 별도 API 키/결제 없이 ChatGPT 구독 사용량 경로로 인증됨.
6. 비용·모델 판단: ChatGPT 설정의 Usage 및 GitHub Codespaces 사용량을 확인한다. Sol/Luna 등 정확한 지원 모델·접근 권한은 계정에서 실제 확인하기 전 확정하지 않는다.

*위 단계는 사용자가 직접 수행할 검증 절차이지, ChatGPT가 이미 사용자 계정을 로그인하거나 Codex 요청을 실행했다는 의미가 아니다.*

## GitHub에서 자동 검증한 범위

- `scripts/probe_codespaces_plus.sh`: **기본 --preflight에서는 API/AI 호출 없음**, `--probe --confirm-plus-usage`일 때만 합성 문장·read-only·ephemeral·JSON Schema로 최소 1회 요청.
- `tests/test_github_only_plus_probe.py`: 실제 Codex와 연결하지 않는 모의 CLI 테스트. Codespaces 아닌 환경, 유료 키 변수, 명시적 사용자 승인 없음, ChatGPT 외 인증, JSON 불일치에서 차단됨을 확인.
- 이 테스트가 PASS여도 **사용자 계정의 실제 Codex Device Code 로그인 성공이나 Plus AI 사용 가능성을 증명하지 않는다.**

## 보안 및 수용 기준

- **현재 0원 목표:** ChatGPT Plus 구독 포함량만 사용. GitHub Codespaces 개인 무료 할당량 내 실행, **GitHub 결제 사용 초과 자동 승인 금지**. ChatGPT Settings → Usage에서 앱 크레딧 OFF 확인. Codex 자체 구독 사용량·추가 크레딧 정책 확인.
- **인증 토큰은 공개 GitHub에 기록하지 않는다.** Codex CLI의 인증 캐시가 Codespaces VM에 남을 수 있다. 개인 Codespace가 지속되는 동안 생성되는 해당 원격 파일의 관리·삭제·정책 적합성은 별도 검토 사항. SIWC 토큰 저장과 혼동하지 않는다.
- 설치 프로그램·서드파티 워크플로에 인증 토큰을 넘기지 않는다. 공개 PR/포크 코드의 명령을 인증된 상태로 자동 실행하지 않는다.
- **PASS**: 사용자 본인 명시 인증 → ChatGPT-managed 로그인 확인 → 모델 단일 요청 성공 → 추가 지출 없이 결과 회수 → 이후 AI JSON 스키마 연동 가능.
- **BLOCKED**: Device Code 메뉴 없음/승인 불가, Codespaces 접근 불가, 구독 모델 추론 거절, 비용·약관 불명확, 토큰 비공개 조건 충족 불가.
- **NO-GO**: 정식 지원 없는 SIWC OAuth 리디렉트 변조, 브라우저 세션 쿠키 추출, 제3자 프록시를 통한 토큰 교환, 공개 Actions에 계정 `auth.json` 업로드.
- Code-first CREATE/UPDATE의 범용 엔진 작업은 **이 인증·실호출 성공 결과를 기록할 때까지 보류**한다.

## 엔진 후속 설계 (실호출 성공 후)

GitHub Codespace에서 사용자 승인된 `codex exec --output-schema` → `AIProposal`의 미검증 JSON만 전달 → 기존 `prepare_request`/`review_report`와 CREATE 검증기 → 명시적 승인 후 HTML 생성. Codex CLI는 작업별 도구/모델 권한을 임의 확장하지 않고 읽기 전용으로 제한.

이는 **GitHub Codespaces에서 사용자가 버튼이나 터미널로 AI를 실행하는 방식**까지의 대안이다. 사용자가 Codespace를 닫은 뒤 **GitHub Actions만으로 상시 무인 AI 실행**까지 가능하다는 의미가 아니다. 후자는 별도의 허용된 사용자 인증/보안 저장 수단 및 정책 승인을 확보하기 전까지 보류한다.
