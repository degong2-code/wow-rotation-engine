# 신규 전문화 CREATE 시험 — 비전 마법사 (Arcane)

## 목표 및 범위

- 사용자 지정 신규 전문화: **마법사 비전**, `Midnight Season 2 / patch 12.1.5`
- 기존 7개 전문화의 **V11 화면과 설명 HTML을 바이트 단위로 보존**하면서 8번째 교본 추가
- **영웅 특성 2개:** 성난태양(Sunfury), 주문술사(Spellslinger)
- **딜사이클 표 4개:** 성난태양 단일·광역 + 주문술사 단일·광역
- **신규 초안:** 우선순위 **34행**, 고급 운용 **10개**, HTML 장 **7개**, 기술명 색인 **12개**
- V11 원본과 장문 번역문은 공개 GitHub에 올리지 않음. 본 신규 비전 JSON의 설명은 독자적으로 작성한 한글 초안이며 `draft_review_required` 상태를 유지한다.

## 참고한 자료 (2026-11-10 확인)

- [Wowhead Arcane Mage rotation 12.1.5](https://www.wowhead.com/ko/guide/classes/mage/arcane/rotation-cooldowns-pve-dps)
- [Icy Veins Arcane Mage rotation 12.1.5](https://www.icy-veins.com/wow/arcane-mage-pve-dps-rotation-cooldowns-abilities)
- [Method Arcane Mage rotation](https://www.method.gg/guides/arcane-mage/playstyle-and-rotation)
- [Blizzard Korean Mage](https://worldofwarcraft.blizzard.com/ko-kr/game/classes/mage)

동일한 영웅 특성/기술이라도 특성 선택, 티어 세트, 대상 수, 핫픽스에 따라 분기가 달라진다. 외부 공략의 문장/우선순위 표를 통째로 복제하지 않으며, 독자 해설과 출처 링크만 수록한다. 조건의 현재 게임 적합성은 추가 검토 전까지 `needs_manual_gameplay_review`로 둔다.

## 구현

- `content/new_guides/arcane.json`: 구조화된 신규 전문화 초안. 기존 `content/public/` V11 7전문화 파일과 구분. 자동 게시 차단.
- `engine/v2/create_guide.py`: 사용자 제공 **원본 V11 SHA-256 `5d70279c...`**을 확인한 뒤 메뉴·목차·신규 문서·영웅 전환에 필요한 최소 스크립트/CSS만 추가. 기존 7개 `manual-view` 요소 HTML이 변경되면 오류로 중단.
- `engine/v2/import_v11.py`: 마지막 장이 래퍼 끝에 맞닿아도 추출하며, 7개 원본 또는 8개 확장 HTML을 재생성할 수 있도록 확장. **7개 원본 parity는 유지**.
- `tests/test_v11_arcane_create.py`: 합성 V11과 실제 비전 초안 JSON으로 신규 8개 전문화 추출·재생성·원본 7개 바이트 보존·두 영웅과 4개 상황·메뉴/목차 누락 방어 검증.

## 비공개 HTML 미리보기 생성

원본 V11을 이미 가지고 있는 환경에서 아래 명령을 실행한다. 실제 사용자가 보는 스타일은 V11 CSS/JS를 그대로 재사용한다.

```bash
python -m engine.v2.create_guide /private/wow_rotation_manual_engine_v2.html \
  --draft content/new_guides/arcane.json \
  --output /private/wow_rotation_manual_with_arcane_preview.html
```

- 원본 898,297바이트 V11 파일은 읽기만 함.
- 출력 파일은 GitHub 저장소 **외부**에만 생성하도록 제한.
- 원본 SHA 불일치, 7개 기존 전문화 HTML 변조, 링크·ID 충돌, 영웅 특성 누락, 아이콘 경로 부정확, 잘못된 JS 등록 앵커가 있으면 생성 중단.
- 검증된 아이콘 파일명만 표시하고, 불확실한 신규 주문 아이콘은 동종 스타일의 중립 표시로 대체. 신규 주문 ID는 추가 확인이 필요한 항목에서 `미확인`으로 유지.
- 인용·저작권 및 수동 게임플레이 리뷰가 끝나기 전까지 자동 공개 Pages 배포 금지.

## 실행 결과 구분

**GitHub 오프라인 테스트:** 합성 7전문화 원본에 신규 비전 자료를 붙인 후 V2 importer/builder로 완전히 재조립, 원본 7개 전문화의 HTML 바이트 동일성 PASS. 이는 실제 private V11 원본이 CI에 업로드됐다는 의미가 아니다.

**로컬 V11 UI 시험:** 실제 사용자 V11 원본의 JS에 신규 비전 전환 코드 11곳을 정확히 반영한 뒤 `node --check` PASS. Chromium 헤드리스에서 원본 V11 화면 + **합성 비전 시험 콘텐츠**를 이용해 비전 선택, 두 영웅 전환, 기존 냉기 교본 복귀 PASS. 실제 `content/new_guides/arcane.json` 전체를 공식 generator로 미리보기 생성하여 브라우저 검증한 것은 아니므로 그 추가 검증은 남아 있다. 별도 스크린샷/캡처 생성하지 않음.

## 다음 단계

1. 사용자 제공 V11에 실제 `create_guide.py`를 직접 실행하여 **8전문화 HTML 전체 통합 생성** 확인.
2. 새로운 비전 초안의 마법사 전용 주문 ID/아이콘·세트 및 영웅 특성 조건과 시즌 2 원문을 수동 대조. 모호한 곳은 가정값으로 배포하지 않음.
3. 신규 등록 JSON을 기존 AI 변경 후보·승인·부분 갱신 경로와 연결(현재 `detail_bridge`는 구 V11 7개 공개 인덱스를 기준으로 동작).
4. 사용자 승인된 경우에만 병합·Pages 공개 단계 진행.

**이 기능은 PR #14 V11 보존형 엔진 브랜치를 기반으로 한 별도 후속 PR이다.** PR #14를 건너뛰어 `main`에 독립 병합하면 필요한 모듈이 누락될 수 있다.
