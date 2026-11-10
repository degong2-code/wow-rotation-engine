# ChatGPT Plus — 로컬 로그인 시범 (WSL2 / Linux)

> **단계:** 사용자 동의가 필요한 실제 OAuth 로그인 코드를 구현했지만 **사용자 계정으로 로그인·모델 조회·AI 추론을 아직 실행하지 않았다.** 현재 GitHub Actions는 오직 합성 키·localhost 콜백·모의 토큰·임시 디렉터리만 테스트한다.

## 목적

WoW 교본 CREATE/UPDATE의 AI 실행을 **ChatGPT Plus 구독 기반, 추가 API 결제 없이** 사용하는 최초 로컬 연결 실험. 일반 유료 OpenAI API 키와 일반 ChatGPT 웹 세션 쿠키는 사용하지 않는다. 모든 AI 결과는 미승인 제안이며 `main` 병합과 교본 공개/자동 반영은 하지 않는다.

## 공식 기술 계약

- 신규 앱은 `client_id=dynamic_agent_client`, 고정된 `ext_agent_host_id`, `agent_name_hint=WoW Rotation Textbook`으로 사용자 동의를 받는다.
- 로컬 브라우저 callback은 **`http://127.0.0.1:{port}/auth/callback`**만 허용. `localhost`/공개 IP/다른 경로는 허용하지 않는다.
- 매 시도 새 `state`·OIDC `nonce`·PKCE verifier/S256 생성. callback의 `state`와 발급된 `oaiapp_...` client ID 검증.
- 사용자 인증 코드 → **`https://auth.openai.com/api/accounts/oauth/token`** 에 원본 redirect URI·PKCE를 함께 보낸다.
- `https://auth.openai.com/.well-known/jwks.json`의 공개키로 ID Token의 **서명, 발급자, audience, exp/iat, nonce, sub** 확인. **callback의 scope는 권한 증거가 아니다**. 토큰 응답의 `chatgpt.tokens.use.direct`를 별도로 검증한다.
- 연결 계정 재인증 시 발급된 client ID와 서명된 `sub`가 바뀌면 기존 자격증명을 덮어쓰지 않는다.
- 계정별 access/refresh/ID 토큰과 고정 host ID는 기본적으로 사용자 WSL 파일시스템의 `~/.config/wow-rotation-textbook/chatgpt/`에 **0700 디렉터리·0600 파일**로 보관한다. 별도의 공개 저장소·CI·브라우저 localStorage·스크린샷·콘솔 로그에 기록하지 않는다.
- **유료 결제 안전:** `sk-` API 키 금지, 추론 자동 실행 금지, `--list-models`도 사용자가 ChatGPT Settings → Usage에서 앱 크레딧 사용 OFF를 확인하고 명시적 플래그를 입력할 때만 허용. 이 확인은 계정 서버의 실제 과금 설정을 조회하는 것이 아니므로 **요금이 절대 발생하지 않는다는 기술적 보증은 아님**.

공식 문서:
- https://developers.openai.com/siwc/token-sharing-open-source/sign-in
- https://developers.openai.com/siwc/token-sharing-open-source/token-reference
- https://developers.openai.com/siwc/token-sharing-open-source/profiles-and-sessions
- https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference
- https://developers.openai.com/siwc/token-sharing-open-source/errors-and-recovery

## 로컬 사용자 실행 (현재는 수동 실행만)

WSL2 Ubuntu 또는 Linux에서 본인의 코드 체크아웃을 사용하는 경우:

```bash
python -m pip install -r requirements-v2.txt

# 로컬 등록 상태만 확인, 사용자 로그인/AI 호출 없음
python -m engine.v2.chatgpt_signin status

# 명시적으로 브라우저 인증, 추론/모델 조회는 자동 실행하지 않음
python -m engine.v2.chatgpt_signin login
```

사용자가 실제 계정 모델 목록까지 확인하기로 결정했다면 ChatGPT **Settings → Usage**에서 연결 앱의 크레딧 사용이 꺼져 있는지 확인한 다음:

```bash
python -m engine.v2.chatgpt_signin login --list-models --confirm-credits-off
```

- 브라우저에서 **ChatGPT 로그인·요청 권한 동의**는 사용자가 직접 처리한다. 인증 코드/토큰을 챗봇이나 GitHub에 붙여넣지 않는다.
- 모델 목록 조회는 AI 추론이 아니지만 외부 서비스 요청이다. 실제 연결된 계정의 모델 목록을 표시할 뿐 **Sol/Luna가 반드시 존재한다고 가정하지 않는다**.
- 여러 계정이 저장된 경우 `--account oaiapp_...`으로 기존 등록을 선택한다. 새 계정/워크스페이스는 `--new-account`. 연결된 ID는 사용자의 로컬 계정 파일로만 보관한다.
- WSL2의 Linux 브라우저 실행이 Windows 기본 브라우저와 연결되지 않은 환경에서는 사용자 측 브라우저 연동 설정이 필요할 수 있다. 본 단계는 환경별 실행 테스트를 완료했다는 뜻이 아니다.
- native Windows Python은 현재 Unix 0600 저장소 보안 모델에 포함되지 않는다. WSL/Linux에서만 시험한다.
- **현재 명령에는 실제 AI 분석 실행 기능이 없다.** 기존 `ChatGPTPlanProvider`의 검토 전용 Responses 어댑터를 승인된 사용자 모델·실측 결과에 연결하는 작업은 다음 단계다.

## 위협 모델·범위 한계

1. 로컬 인증 콜백을 타인이 보내도 `state`가 정확히 일치해야 한다. 한 번 수신된 정상 callback은 재사용하지 않는다. HTTP 서버는 loopback에만 바인드하고 authorization query를 로그에 남기지 않는다.
2. 임의 `alg=none` 토큰, 서명 불일치, 잘못된 issuer/audience/nonce, 재인증 subject 불일치, callback 중복 필드, 잘못된 신규 client ID는 거부한다.
3. **개인 로컬 디스크에 저장된 토큰은 현재 암호화된 키체인에 보관되지 않는다.** Unix 소유자 전용 파일 권한만 사용한다. 개인 WSL 파일시스템에서만 시범하며, 생산용 Windows/다중 사용자/클라우드 배포는 OS 비밀 저장소 및 계정별 갱신 동기화가 필요하다.
4. refresh token 수명(문서상 30일)과 회전형 갱신을 지원하는 **자동 refresh 구현은 아직 미완료**. 액세스 토큰 만료 후 재로그인 또는 별도 토큰 갱신 모듈이 필요하다.
5. `--list-models`는 OAuth 동의 뒤에 별도 요청을 한다. **실사용량 차감 없는 테스트·로그인 실패 시 재시도 정책 검증은 아직 미실시**.
6. AI 제공자 인터페이스를 그대로 유지한다. 신규 전문화 CREATE의 범용 렌더러 완성 및 모델별 Sol/Luna 비교는 이번 로그인 기능과 별개로 수행한다.

## 검증 및 개발 기록

- 신규 엔진: `engine/v2/chatgpt_oauth.py` / `chatgpt_local_store.py` / `chatgpt_signin.py`
- 테스트: `tests/test_v11_chatgpt_oauth.py` / `test_v11_chatgpt_signin.py`
- 의존성: `requirements-v2.txt`에 `PyJWT[crypto]` 추가.
- 실제 서비스 측 자격 증명·사용량을 사용하지 않는 완전 오프라인 테스트를 GitHub Actions에서 실행한다.
- 새 PR은 #17 기반 **Draft**, 별도 승인 전 원본 V11 7개 전문화 변경·`main` 병합·Pages 배포 금지.
