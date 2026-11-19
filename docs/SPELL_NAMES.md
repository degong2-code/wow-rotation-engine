# 한국어 주문명 검증 파이프라인

## 상태

기존 `content/public/spells.json`에는 V11에서 상속한 **176종 주문 ID / 178개 이름 기록**이 있습니다. 모두 독립 검증되지 않은 상태입니다. 로컬라이제이션 검증은 우선순위·Advanced Tips의 **의미 검증과 별도**로 수행합니다.

- 오프라인: `python -m engine.spell_names audit --output dist/spell-name-audit.json`
- Blizzard API 증거 수집(사용자가 비밀 값 등록 후 수동 실행): GitHub Actions → `Collect Blizzard ko_KR spell names` → Run workflow
- 저장되는 증거: 요청한 spell ID, 관측 한국어 이름, 조회 시점(UTC), 결과 상태. **API 토큰과 비밀 값은 저장하지 않습니다.**
- 관측 비교: `python -m engine.spell_names audit --snapshot evidence.json --output comparison.json`
- 엄격한 검사(일부 미조회·불일치 시 실패): `--require-all-matched`. 단 **PASS하더라도 자동 게시/이름 승인하지 않습니다**.

## GitHub Secrets (필요 시 1회 설정)

Settings → Secrets and variables → Actions → Repository secrets:
- `BLIZZARD_CLIENT_ID`
- `BLIZZARD_CLIENT_SECRET`

Blizzard Developer Portal에서 본인이 등록한 OAuth 클라이언트 자격증명만 사용합니다. 채팅이나 파일에 직접 적지 않습니다. **자격증명이 없으면 수동 수집 워크플로는 실패**하며, 일반 CI는 공식 API를 호출하지 않습니다.

## 조회·보안 규칙

조회 대상은 `https://kr.api.blizzard.com/data/wow/spell/<ID>?namespace=static-kr&locale=ko_KR`입니다. 토큰은 OAuth client credentials로 얻어 HTTP Authorization 헤더에만 전송합니다. 처리 중 일시적 서버 오류(429·5xx)는 최대 3회 시도하고, 404는 `not_found`로 기록합니다.

실제 API에서 기술별 데이터가 없을 수 있습니다. **404는 기술이 잘못됐다는 증거가 아닙니다.** 문자열이 일치하더라도 V11 명칭의 정확한 패치·영웅 특성 문맥까지 검증했다는 뜻은 아닙니다. 불일치는 원문 대조 전까지 보류합니다.

독립적인 대조가 필요한 이름은 한국어 게임 클라이언트의 `C_Spell.GetSpellName(spellID)` / `C_Spell.GetSpellInfo(spellID)`로 교차 검증할 수 있습니다. 이것도 사용자가 직접 게임 클라이언트를 실행할 수 있는 경우에 한합니다.

## 승인 경계

- API 결과는 **증거 후보**이며 기존 한국어 이름을 자동 수정하지 않습니다.
- URL·시점·ID·실제 한국어 관측 문자열을 대조하고 이름 중복 및 문맥을 확인한 뒤 승인합니다.
- `engine.review_audit`의 `publish_ready = false`는 유지됩니다.
- 원문 공략 수집, 자동 번역·딜사이클 변경, Pages 실전 게시 기능과 혼동하면 안 됩니다.

공식 문서: https://develop.battle.net/documentation/world-of-warcraft/game-data-apis


## 2026-11-14: 신규 전문화 주문 ID와 공식 Blizzard 아이콘 미디어

기존 Blizzard ko_KR 이름 증거 경로에 공식 아이콘 조회 기능을 **선택적으로 확장**했다. 별도의 번역기나 아이콘 추정기는 만들지 않았다. 신규 전문화에서는 기존 V11 176개 주문 ID에 없는 **1~100개의 양의 정수 주문 ID**도 직접 지정할 수 있다.

**GitHub Actions 사용 절차**

1. Actions → Collect Blizzard ko_KR spell names and icons → Run workflow.
2. 기존 GitHub Secrets인 BLIZZARD_CLIENT_ID / BLIZZARD_CLIENT_SECRET가 등록되어 있어야 한다. 비밀 키를 채팅에 입력하거나 로그에 쓰지 않는다.
3. spell_ids: 예를 들어 5176,93402,205636처럼 새 전문화의 주문 ID를 쉼표로 입력한다. 비워두면 기존 V11의 176개 중 max_ids 범위를 조회한다.
4. include_media: true를 선택하면 공식 한국어 주문명 조회가 성공한 ID에만 미디어 조회를 추가한다. 기본값은 false다.

**실행 명령 예시**

    python -m engine.spell_names fetch --spell-ids "5176,93402,205636" --include-media --output dist/spell-name-snapshot.json --report dist/spell-name-audit.json

**공식 조회 경로**

- 이름: https://kr.api.blizzard.com/data/wow/spell/5176?namespace=static-kr&locale=ko_KR
- 아이콘: https://kr.api.blizzard.com/data/wow/media/spell/5176?namespace=static-kr&locale=ko_KR
- 별도 게임 클라이언트 대조: C_Spell.GetSpellInfo(ID)의 name / iconID / originalIconID. 덮어쓰기 기술이라면 현재/원본 아이콘을 구분한다.

응답 주문 ID 일치·Blizzard CDN HTTPS 미디어 URL·공식 이름·404/인증 실패를 확인한다. 잘못된 URL이나 미확인 아이콘 파일명을 공식 사실로 승격하지 않는다. 신규 ID는 new_spell_requires_editorial_review, 모든 아이콘은 icon_review=pending, 보고서 publish_ready=false를 유지한다. 공식 데이터가 있어도 원문 패치·게임 판단의 정확성은 별도로 검토해야 한다.

**조화 드루이드 V4 경계:** 개인 HTML에서는 14개 기술 ID와 한국어 Wowhead 페이지·아이콘 파일명 참조를 반영했으나, 아직 **Blizzard API의 실제 14개 응답을 받아 확정하지 않았다**. 공식 명칭/아이콘 교차검증은 REVIEW다. V11의 기존 7개 내용은 자동 교정·변경하지 않는다.
