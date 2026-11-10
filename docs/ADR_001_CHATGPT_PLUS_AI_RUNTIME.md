# ADR-001 — AI 제공자와 ChatGPT Plus 구독 연동 정책

- **일자:** 2026-11-11 (KST)
- **상태:** 설계 정책 채택 / 실제 개인 Plus 계정 연결 미검증
- **저장소:** `degong2-code/wow-rotation-engine`
- **기준 브랜치:** `work/v11-fidelity-arcane-20261111` (PR #16)
- **목적:** WoW V11 딜사이클 교본의 **CREATE/UPDATE 범용 엔진**을 AI 제공자·게임 전문화에 종속시키지 않고 개발. AI를 별도 유료 API 비용 없이 활용할 수 있는지 검증

## 1. 사용자 요구와 합의

1. 현재 **ChatGPT Plus 구독은 유지**하며, 교본 엔진으로 인한 **추가 AI 지출은 0원**을 목표로 한다.
2. Plus에서 제공되는 **Work/Codex 사용량을 공유해도 괜찮다.** 이를 일반 채팅 GPT-6 High의 무제한 사용 권한으로 해석하지 않는다.
3. **Sign in with ChatGPT**의 구독 사용량 연동을 우선 검토한다. 개인용/로컬 오픈소스 배포가 초기 범위이며, 외부에 상시 호스팅하는 서버형 웹앱은 별도 지원 조건을 확인한다.
4. 모델은 초기 개발 단계에서 확정하지 않는다. **Sol의 심층 해석 안정성**과 **Luna의 저사용량·구조화 추출 효율**을 나중에 동일한 평가 자료로 비교한다. 실제 모델 선택지는 **연결된 계정이 반환한 목록**에 따른다.
5. AI의 역할: 자료의 의미 추출, 공략 간 차이 설명, 사용 이유·예외 분석, 구조화된 **제안** 작성.
6. 엔진의 역할: 출처·주문 ID·조건/규칙 ID·스키마·공통 V11 컴포넌트 검증, 버전 비교, 승인 후 결정론적 CREATE/UPDATE, 회귀 테스트, 개인 파일 보존.
7. **같은 JSON은 같은 HTML로 생성**되어야 한다. AI가 매번 HTML/CSS/JS를 새로 만들거나 배포 결과를 결정하지 않는다.
8. 비전은 **파일럿 및 회귀 테스트 데이터**다. 비전 34개 우선순위의 세부 검증보다 전문화 독립적인 엔진 완성을 우선한다. 기존 V11 7전문화의 본문·CSS·JS는 바이트 단위 보존한다.
9. 추가 캡처나 화면 이미지를 답변에 제공할 필요 없음. 기존 HTML 내부 기술 아이콘은 유지.
10. 외부 가이드의 장문 원문·번역문, V11 개인 원본, OAuth 토큰·키를 공개 GitHub/CI Artifacts에 보내지 않는다.

## 2. 공식 기술 확인 (2026-11-11)

공식 문서:
- OSS 구독 연동: https://developers.openai.com/siwc/token-sharing-open-source
- 모델 조회·추론: https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference
- 로그인/PKCE: https://developers.openai.com/siwc/token-sharing-open-source/sign-in
- 세션/토큰 보관: https://developers.openai.com/siwc/token-sharing-open-source/profiles-and-sessions
- 에러 처리: https://developers.openai.com/siwc/token-sharing-open-source/errors-and-recovery
- 사용자 사용량·크레딧 설정: https://help.openai.com/en/articles/20001542-using-your-chatgpt-plan-in-other-apps-and-sites

**확인된 인터페이스:**
- 정식 OAuth/PKCE로 로그인 후 `chatgpt.tokens.use.direct` 스코프의 실제 승인 여부 확인. 성공적인 *신원 로그인만으로는 구독 사용 권한 없음*.
- 인증된 토큰으로 `GET https://api.openai.com/v1/models`를 호출하고 `visibility=list`인 `slug`/표시명을 목록에 제공.
- `POST https://api.openai.com/v1/responses`에 `store=false`, `stream=true` 설정; `response.completed`를 확인하기 전에는 결과 적용 금지.
- **사용량은 Plus의 Work/Codex 및 연결된 앱과 공유**하며 5시간 사용량·주간 앱 한도/사용자 설정을 적용. 구체적인 토큰 수·개별 작업당 차감량은 고정 보장 불가.
- `subscription_sharing_usage_limit_exceeded`, `unsupported_capability`, `usage_unavailable`, 인증 실패와 스트림 중단은 각기 다른 오류 상태로 보존.
- API에서 지원되는 `web_search`가 구독 연동 경로에도 그대로 지원되는지는 **검증 전 미확정**. 따라서 공략 **탐색·합법적 수집기**와 **AI 해석**은 별도의 모듈로 설계.
- 토큰 저장은 보안 저장소·로컬 런타임에 한정. 웹 로컬 스토리지, GitHub, 콘솔 로그, CI 환경 공유 금지.

**비용 관련 매우 중요한 조건:** ChatGPT Settings → Usage에서 **앱의 크레딧 사용 허용을 꺼야** 구독 포함량을 초과하여 크레딧이 사용되는 것을 방지할 수 있다. 클라이언트가 서버 측 계정 크레딧 설정을 검증·강제할 수 있다는 문서상 보장은 없다. 따라서 코드에서는 사용자가 이를 확인하기 전 호출을 막고 유료 API 경로로 자동 전환하지 않는다. **이 확인은 사용자의 진술이며 결제 플랫폼의 강제 차단과 같지 않다.** 추후 제품 UI는 매 연결 시 해당 설정을 확인하도록 안내한다. 사용량 초과가 발생해도 정해진 한도로 자동 구매/재시도하지 않는다.

## 3. 기능 분할 및 완성형 사용자 경험

| 사용자 동작 | 자동 구성요소 | 결과 |
|---|---|---|
| 신규 전문화 선택 후 'AI 분석' | Source Collector → AI Provider → JSON Proposal | 검토용 CREATE 후보 |
| 기존 전문화 선택 후 '업데이트' | 기존 스냅샷·새 근거 비교 → 변경된 규칙만 AI 처리 | 변경 diff와 영향 장 목록 |
| 분석 결과 검토 | Evidence Gate → User Approval | 승인/보류된 내용 구분 |
| '교본 생성' | Deterministic V11 renderer + regression tests | 기존 7전문화 보존한 미리보기 |
| 발행 승인 | Version Snapshot + Publisher | 명시적으로 승인된 버전만 게시 |
| 사용량 초과 | Checkpoint + Fail-closed | 중단, 재실행 시 이전 결과 재사용 |

AI 제공자는 `AIProvider`(모델 목록, `AIJob` 입력, `AIProposal` 출력) 계약으로 교체한다. 외부 공략 내용은 입력으로만 사용하며, AI의 텍스트를 그대로 확정 규칙이나 HTML로 적용하지 않는다.

## 4. 이번 개발에서 실제 구현한 것

- `engine/v2/ai_runtime.py`: `AIJob`, `AIProposal`, `ModelOption`, `AIProvider` 공통 인터페이스. `auto_applied=false`, `auto_published=false`, `gameplay_verified=false`을 데이터 계약으로 강제.
- `engine/v2/chatgpt_plan.py`: **이미 정식 OAuth로 인증한 세션을 받아** 계정 모델 조회와 스트리밍 Responses 호출. 크레딧 사용 차단 확인, 스코프 누락, 사용량 초과, 부적합 모델, 중단·부분 응답을 실패 처리. `/v1/responses` 외 요청·자동 유료 경로·재시도 없음.
- `tests/test_v11_chatgpt_plan.py`: 실제 AI 계정이나 네트워크를 사용하지 않는 합성 수송 실험. 모델 선택, 구독 권한, 크레딧 보호, 종료 이벤트, JSON 검증, 사용량 한도, 승인 분리 테스트.
- `engine/v2/ai_update_bridge.py`: 공통 제공자의 미승인 JSON을 기존 `prepare_request` / `review_report`에 연결. 사용자가 선택한 ID와 공략 발췌만 전송하며 AI가 개인 V11 HTML을 자동으로 건드릴 수 없음.
- `tests/test_v11_ai_update_bridge.py`: 제공자 결과가 미리보기/검토 단계에 머물고, 잘못된 인용·ID를 기존 UPDATE 검증기가 거부함을 합성 검사.
- `PlanSession`은 **외부의 신뢰 가능한 OAuth 검증기가 서명·발급자·audience·nonce·scope를 검증한 경우에만** `oauth_verified=true`를 받아 호출한다. 일반 `sk-` 결제 API 키는 거부. 현재 검증기와 사용자 로그인 UI는 구현되지 않았으므로 임의 입력으로 이 플래그를 올려 실제 토큰을 사용하는 것은 지원하지 않는다.

**아직 구현하지 않았거나 통과를 주장하지 않는 것:**
- 실제 사용자 ChatGPT 로그인/PKCE/ID Token 검증/토큰 갱신/보안 저장소 UI. 이는 사용자의 로그인 동의를 받아 별도 구현·검증해야 한다.
- 본인 Plus 계정의 실모델 목록·실제 1회 분석 요청·사용량 소모 실측.
- 구독 연동 경로의 웹 검색 등 도구 지원 여부.
- 모델별 동일 데이터 품질/소비량 비교(Sol vs Luna).
- 범용 CREATE 엔진 전환. 기존 `create_guide.py`는 비전 파일럿이며 전문화 불변식 분리는 다음 단계다.

기존 `ai_proposals.py`의 `--send-api` / `OPENAI_API_KEY` 경로는 이전 시험용으로 남아 있다. **새 무료 정책의 기본 실행 경로와 연결하지 않는다.** 별도의 API 키 유료 호출을 묵시적으로 활성화하거나 비공개 자료를 자동 송신하면 안 된다.

## 5. 우선 개발순위 및 완료 기준

1. **AI 비용·인증 경계 구현(진행 중):** 제공자 중립 계약, ChatGPT Plan 어댑터, 오프라인 오류/검토 테스트 → 별도 Draft PR에 보관.
2. **로컬 사용자 로그인 시범:** 공식 Sign in with ChatGPT 사용자 동의, 실제 계정 모델 조회 및 단일 JSON 결과 수신; 크레딧 설정 OFF 확인. **사용자 승인 없이 자동 로그인·실사용량 소모 금지**.
3. **CREATE 공통 스키마·렌더러:** 기존 비전 전용 ID·selector를 분리, 다른 합성 신규 전문화로 코드 수정 없이 재생성하는 회귀 검사.
4. **AI 해석 파이프라인:** 공개 자료 수집/권리 검증 → 추출 → 근거 검토 → 설명 생성, 각 단계 캐시·Checkpoint·불확실성 유지.
5. **Sol/Luna A/B 평가:** 동일 버전·같은 출처 범위·검증된 문제 세트로 조건 일치율, 누락률, 근거 신뢰성, 생성 안정성 및 사용량 비교. 자동 품질 동등성 주장 금지.
6. **웹 관리 UI:** 신규 등록·업데이트·검토·생성·롤백·발행. 로컬 실행을 우선, 원격 호스팅은 별도 자격 확인.

**금지:** 검증되지 않은 34개 행을 출처 위치만 있다는 이유로 승인, AI가 기존 V11 전체를 재작성, 개인정보/토큰 GitHub 게시, 크레딧 허용을 자동 활성화, 사용자 승인 없는 `main` 병합·Pages 배포.
