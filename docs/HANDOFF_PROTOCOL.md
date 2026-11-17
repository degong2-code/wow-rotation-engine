# HANDOFF_PROTOCOL — 일반 채팅 간 복원·종료 계약

> **현재 상태는 [CURRENT_STATE](CURRENT_STATE.md) 하나만** 사용한다. V83/이전 날짜별 HANDOFF 및 [옛 장문 인계](HANDOFF_CHAT_FIRST_CURRENT.md)는 **HISTORY**로만 참조. 이 문서에는 새 버전별 인계문을 붙여 늘리지 않는다.

## 새 채팅 시작 (평소 4개 문서만)

1. GitHub `degong2-code/wow-rotation-engine`의 **현재 활성 PR/HEAD/base/CI를 실조회**한다. `main`과 Draft 작업 브랜치 혼동 금지.
2. **[PROJECT_CANON](PROJECT_CANON.md) → [QUALITY_FIRST_POLICY](QUALITY_FIRST_POLICY.md) §0/§0.1/§5.1 → [CURRENT_STATE](CURRENT_STATE.md) → [CHAT_FIRST_PLAYBOOK](CHAT_FIRST_PLAYBOOK.md)**만 기본 로드. 추가 문서는 작업에 직접 관련된 구간만 읽는다. 과거 HANDOFF 전체 정독을 기본값으로 만들지 않는다.
3. 실제 사용할 개인 HTML(V11 비교 기준/최신 통합/독립본)을 개인 Library에서 열어 **파일 실물 크기·SHA-256·해당 전문화·승인 상태**를 검증한다. 문서의 파일명/해시는 실물 확보 증거가 아니다.
4. 요청이 명시적 **읽기 전용 독립 복원**이면 GitHub 상태·실제 파일·품질 REVIEW·다음 작업을 보고하고 변경하지 않는다. 전문화명·진행/UPDATE를 받은 경우는 제작 계약에 따라 작업한다.

## 실제 제작 전/후

- **전:** 최신 원문 패치/영웅/선택형 확보 범위, 변경 대상, 기존 UI 자산 및 비대상 보존 범위 확정. 제로베이스 집필이면 기존 V11 게임 본문은 *초안 완성 후 비교*.
- **중:** 원문 Gate A → 조건·행동 Q0/Q1 → 빠른 참조·설명 Q2 → **기존 호평 교본과 동폭 실화면 비교 Q3** → HTML/JS·통합·모바일 Q4. Q4가 Q3 또는 게임 정답을 대신하지 않는다.
- **후:** 새 개인 HTML 생성·Library 저장, 파일 **실제 크기/SHA/ID 재조회**, 본문/JS 보존 범위, Gate A/Q0~Q4 각 판정과 외부 CDN·로컬 실행 한계 보고. 승인 없는 main/PR 병합·배포 및 개인 HTML/원문 공개 업로드 금지.
- **종료:** [CURRENT_STATE](CURRENT_STATE.md) 현 상태 행을 **교체**하고, 실제 다음 1~3개 작업만 남긴다. 날짜별 대형 요약/새 인계 문서/새 검사기는 기본 생성하지 않는다. 규칙 변경은 [PLAYBOOK](CHAT_FIRST_PLAYBOOK.md)의 기존 관련 문장을 **수정**하고, 기존 사실 미적용이면 새로운 규칙을 추가하지 않는다.

## 새 일반 채팅에 붙여 넣을 복원 프롬프트

> ROTATION TEXTBOOK 프로젝트의 최신 상태를 **읽기 전용으로 복원**하라. GitHub `degong2-code/wow-rotation-engine`의 실제 활성 PR/head/base/CI를 재조회하고, 그 HEAD의 `docs/PROJECT_CANON.md`, `docs/QUALITY_FIRST_POLICY.md` §0·§0.1·§5.1, `docs/CURRENT_STATE.md`, `docs/CHAT_FIRST_PLAYBOOK.md`를 읽어라. 과거 HANDOFF를 최신 상태로 오용하지 마라. 현재 통합 HTML과 V11 원본을 개인 Library에서 실제 열어 크기/SHA/전문화/승인·REVIEW를 확인하고, 접근 못 한 자료는 명확히 말하라. 게임 원문 Gate A/Q0/Q1, 독해 Q2/Q3, 기능 Q4를 분리하라. **이번 첫 응답은 변경 없이 최신 제품과 미해결 핵심·다음 1~3개를 보고한 뒤 진행 지시를 기다려라.** 비공개 HTML이나 저장 원문을 공개 GitHub에 올리지 않고, Work/독립 API 엔진을 요구하지 마라.

**중요:** 이 프롬프트는 사용자가 *복원만 요청한 경우*에 사용한다. 보통의 전문화명 단독 입력은 제작 요청으로 처리한다.

## 복원 실패 처리

- GitHub/Library/원문이 실제로 없으면 이전 인계의 숫자를 실물 확인으로 둔갑시키지 말고 해당 범위를 REVIEW.
- GitHub 문서를 수정해도 ChatGPT 프로젝트 설정이 자동 갱신되지는 않는다. 사용자 설정에는 [최소 시작 지침](CHAT_FIRST_PROJECT_INSTRUCTIONS.md)을 별도로 등록한다.
- 본문 상세 검증과 과거 실험은 [이전 절차 이력](https://github.com/degong2-code/wow-rotation-engine/blob/e3416fc9643f2108187648c356d776115e5cda82/docs/HANDOFF_PROTOCOL.md) 및 [사례집](QUALITY_GENERALIZATION_CASEBOOK.md)에 남는다.
