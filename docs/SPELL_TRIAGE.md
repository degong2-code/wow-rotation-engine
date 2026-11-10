# 공식 주문명 불일치·404 검토 큐 (2026-11-10)

## 실제 증거

- [Blizzard API 원본 조회](https://github.com/degong2-code/wow-rotation-engine/actions/runs/42799171635)에서 `ko_KR` 176개 고유 주문 ID 수집.
- 이전에 생성한 `content/review/blizzard-spell-20261110.json`의 **분류 150 일치 / 1 불일치 / 25 API 404**를 사용.
- 원본 `spells.json` Git Blob SHA-1과 분류 기록의 `baseline_spells_git_blob_sha`가 동일해야 빌드가 통과합니다.
- 전원 배타·전체 범위 검사: 176개 ID가 정확히 한 번씩 150+1+25+0에 분류돼야 합니다.

## 우선순위

- **P0_rotation_reference**: 실제 177개 우선순위 행에 등장하는 API 미해결 ID. 현재 `199786`(혹한의 쐐기) 단 1개로, 냉기 마법사 우선순위 4행이 연관됩니다.
- **P1_name_disagreement**: V11과 Blizzard 공식 `ko_KR` 이름 불일치. `1249809`의 기존 표기는 **마무리 작업**, API는 **끝맺음**. 현재 V11 우선순위 행에는 직접 등장하지 않습니다.
- **P2_glossary_only_404**: 우선순위 행에 직접 등장하지 않는 나머지 API 404 ID 24개.

**404는 주문 ID가 틀렸다는 증거가 아닙니다.** 일부 기록은 야수 기술, 상태 효과, 소모품 등 성격이 서로 다를 수 있습니다. 우선순위 행에 없다고 공략에 영향을 전혀 주지 않는다는 뜻도 아닙니다.

와우헤드 한국어에는 [혹한의 쐐기 199786](https://www.wowhead.com/ko/spell=199786) 페이지가 존재합니다. 다만 이 페이지의 존재는 현재 클라이언트의 주문·영웅 특성 조건까지 검증하지 않습니다.

추가 주의: V11 `name_en` 일부에는 주문명 외 설명이 붙어 있습니다. 이를 외부 공식 영어 데이터처럼 취급하지 않고 `inherited_english_metadata_may_include_commentary`으로 표시합니다.

## 실행

```bash
python -m engine.spell_triage --output dist/spell-review-queue.json
python -m engine.client_spell_probe --output dist/WoWRotationSpellProbe
```

Actions는 분류 JSON과 선택형 WoW 애드온 두 개의 Artifact를 제공합니다. 실행 가능한 딜사이클로 승인하는 기능은 없습니다.

## 선택형 WoW 클라이언트 교차 조회

API가 404를 반환한 25개와 이름 불일치 1개를 실제 **한국어 WoW 리테일 클라이언트**에서 확인하기 위한 로컬 도구입니다.

1. GitHub Actions의 `wow-ko-kr-client-spell-probe` Artifact를 받아 `WoWRotationSpellProbe` 폴더를 만듭니다.
2. 해당 폴더에 `WoWRotationSpellProbe.toc` 및 `SpellProbe.lua`를 넣고 게임의 `World of Warcraft/_retail_/Interface/AddOns/WoWRotationSpellProbe/`에 배치합니다.
3. 한국어(`koKR`) 클라이언트로 접속하면 스캔하고, `/wrspell`로 요약을 확인하거나 `/wrspell scan`으로 재확인합니다.
4. `/reload` 또는 로그아웃하여 `WTF/Account/<계정>/SavedVariables/WoWRotationSpellProbe.lua`를 저장합니다. **해당 파일을 공개 GitHub에 커밋하지 마세요.**
5. 이 파일은 요청한 주문 ID의 클라이언트 이름·해석 불가 상태만 기록하도록 구성했으며 캐릭터 이름, 전투 기록, 위치를 수집하는 코드는 없습니다. 단 클라이언트나 게임 환경이 수정한 파일에는 임의 정보가 추가될 수 있으므로 내용 확인 후에만 공유하세요.

현재 템플릿은 `Interface: 120105`로 생성합니다. 게임 버전이 다르면 `/run print(select(4,GetBuildInfo()))`로 인터페이스 번호를 확인해 `.toc`를 변경해야 할 수 있습니다. 이 애드온은 코드를 자동 테스트했지만 **실제 게임 내 실행 테스트를 수행하지 않았습니다**.

`C_Spell.GetSpellInfo(spellID)`는 정수 ID를 사용하며, 정보가 아직 로딩되지 않은 경우 `C_Spell.RequestLoadSpellData`로 재요청합니다. `nil` 또는 이벤트 실패도 기술이 틀렸다는 증거가 아닙니다.

## 제한

- API 응답·클라이언트 조회는 **기술명에 관한 별도 증거**이며 177개 로테이션의 게임 내 타당성 검증이 아닙니다.
- 기존 V11 JSON의 명칭을 자동 수정하지 않습니다.
- 승인된 이름/조건이 생기기 전까지 `automatic_publish_allowed = false`를 유지합니다.
