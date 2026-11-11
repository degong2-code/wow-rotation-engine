# SOURCE_ACQUISITION — 교본 공략 자료 자동 확보·검증 규칙

> ChatGPT가 채팅에서 전문화 이름만 받았을 때 실행하는 **공개 원문 위치 탐색 지침**. 다른 사이트의 공략 전체를 GitHub에 보관하거나 무단 재게시하는 자료 창고가 아니다.

## 1. 탐색 순서

**1순위: 사용자 지정 자료.** 채팅에 URL·텍스트·파일을 제공하면 우선하되, 패치·특성·대상 수가 실제 요청과 일치하는지 확인.

**2순위: 사용자 지정이 없을 때 Wowhead 하나를 기본 기준 공략으로 선택.**
- [Wowhead 직업 가이드](https://www.wowhead.com/guides/classes) — 전문화의 Rotation/Cooldowns/PvE를 기본 원문으로 선택하고 패치/빌드/영웅/대상 수와 간편판·상세판의 차이를 확인한다.
- **조건부 보조 검증:** [Icy Veins WoW](https://www.icy-veins.com/wow/), [Method WoW Guides](https://www.method.gg/guides) 등은 기준 자료의 누락·모호함·상충 또는 삭제된 기술 등 구체적인 의문을 해결해야 할 때에만 해당 부분을 대조한다. **기본적으로 복수 공략을 수집하지 않는다.**
- **기술 사실 확인:** [Blizzard WoW 직업 안내](https://worldofwarcraft.blizzard.com/ko-kr/game/classes), 해당 패치 노트, 실제 주문 페이지의 기술 유효성·ID·변경 사항을 확인한다. 이는 다른 사이트의 전체 로테이션을 합치는 것과 다르다.

위 사이트의 접근 정책·이용 조건을 준수하고, 직접 확인할 수 없는 원문을 실제로 확인했다고 쓰지 않는다. **위 목록은 무조건 모두 조사하라는 체크리스트가 아니다.** [QUALITY_FIRST_POLICY](QUALITY_FIRST_POLICY.md)의 최소 필요 근거 원칙을 따른다. 일반 검색 결과의 검색 날짜만으로 '최신'이라고 확정하지 않는다.

## 2. 검색 질의 구조

먼저 버전·레이드/시즌·직업·전문화를 확인한다. `{CURRENT_PATCH}`와 `{SPECIALIZATION_EN}`는 **실제 발견된 값**으로 대체하고 문자열 그대로 검색하거나 오래된 버전을 추측해서 넣지 않는다.

예시 (검색 식이며 확인 완료된 URL이 아님):
- `{SPECIALIZATION_EN} WoW {CURRENT_PATCH} rotation cooldowns raid single target aoe`
- `{SPECIALIZATION_EN} {CURRENT_PATCH} opener hero talents detailed priority`
- `site:wowhead.com/guide/classes {SPECIALIZATION_EN} rotation`
- `site:icy-veins.com/wow/ {SPECIALIZATION_EN} rotation cooldowns`
- `site:method.gg/guides {SPECIALIZATION_EN} rotation`
- `{SPECIALIZATION_EN} buff proc tier set spell ID Korean localized`

동시에 확인할 필드:
- 페이지 제목, URL, **게시/수정일과 실제 적용 패치**, 작성자의 범위, 빌드/영웅 특성, 대상 수, 매크로/특수 상황, 최신 패치와의 일치.
- 우선순위 행별 **조건과 예외**, 특성/버프/리소스/세트 효과의 전제, 간략판·상세판의 차이.
- 다른 출처를 **실제로 사용한 경우에만**, 해당 쟁점의 조건 차이·패치/빌드·작성자/파생 출처의 독립성 여부를 기록. 출처가 하나라면 단독 기준이라고 명시할 뿐 사이트 수를 채울 필요는 없다.
- **추출 충실도:** 선택한 영웅 특성 탭·접힌/동적 표·오프너 단계·선택 특성 분기의 문맥이 텍스트 수집 과정에서 소실되지 않았는지 확인. 잃어버린 조건을 한 시퀀스로 합성하지 않는다.

### 선택형·접힌 원문 확인 (실제 콘텐츠 확보 기준)

- 페이지가 제공하는 **딜사이클 관련** 영웅/전문화·특성/빌드 스위치, ST/AoE·전투 유형, 오프너/물약 선택, Talent Swaps, Notes, Further/Advanced, 접힌 쿨다운 설명, 행별 hover/tip 및 조건부 표·이미지/타임라인을 식별한다. 원문이 제공하지 않는 모든 특성 조합을 임의로 생성하는 작업은 아니다.
- 가능하면 각 유효한 선택 상태를 실제로 전환/펼쳐 내용을 확인하고 원래 상태·행·조건 귀속을 보존한다. 일반 본문 열람에서 제목만 나오거나 하위 항목/행이 끊기거나 선택지 텍스트가 한데 합쳐지면 **완전 수집으로 판정하지 않는다**. 같은 Wowhead URL의 검색 색인/다른 접근 가능한 표현을 대조하여 누락을 먼저 복구한다. 검색 색인도 실제 선택 상태와 일치한다고 자동 가정하지 않는다.
- 브라우저 선택 조작 또는 원문 구조 확인이 불가능하고 결정에 필요한 내용이 여전히 빠져 있다면 해당 부분만 보조 확인한다. 끝내 확보하지 못한 분기는 **미확인**으로 표시하며 전 분기 확보를 주장하지 않는다. 출처 수를 늘리는 것이 목적이 아니다.
- 원문 확보 범위와 최종 교본에 선별 반영할 범위를 분리한다. 특히 **행동·임계값·쿨다운/자원·발동·특성별 예외를 바꾸는 정보는 누락하지 않는다**. 단순 일반론/중복, 해당 빌드에 무관한 정보는 축약할 수 있다.
- 기록은 실제 주요 선택/접힌 설명의 확보·미확인 범위를 짧게 남기면 충분하다. 별도 크롤러·고정 조합 수·강제 체크리스트는 필요성의 반복 증거 없이 개발하지 않는다. 사례: [범용 사례집 §19](QUALITY_GENERALIZATION_CASEBOOK.md).


## 3. 기존 알려진 비전 자료 — 항상 최신성 재검증

2026-11-11 시점 PR #15·#16에서 사용한 **참고 시작점**이다. 미래 패치의 자동 정본이 아니다.

| 사이트 | 기존 확인 주소 | 주의 |
|---|---|---|
| Wowhead | https://www.wowhead.com/guide/classes/mage/arcane/rotation-cooldowns-pve-dps | 쉬운 운용과 상세 우선순위의 조건 차이 확인 |
| Icy Veins | https://www.icy-veins.com/wow/arcane-mage-pve-dps-rotation-cooldowns-abilities | 버전·특성·대상 수 범위 확인 |
| Method | https://www.method.gg/guides/arcane-mage/playstyle-and-rotation | 영웅 특성·티어 세트 전제 확인 |
| Blizzard | https://worldofwarcraft.blizzard.com/ko-kr/game/classes/mage | 공식 한국어 직업 안내, 개별 주문 검증은 별도 |

공략 간 대조에서 확인된 **검토 필요 예시**:
- 성난태양 비전 보주의 사용 충전물 기준: 자료의 쉬운판/상세판 차이와 해당 빌드 조건을 비교해야 함.
- 주문술사 광역 비전 보주 사용 시 오버캡·특성 선택 조건이 다르게 기술된 가능성.
- 탄막 중첩 조건은 **성난태양 25 / 주문술사 20**으로 구분하며 정확한 특성·오프너 예외를 다시 검증해야 함.
- 비전 초안 34개 우선순위 중 출처 '섹션'을 연결해 놓았다는 것과 실제 전체 발동 조건을 검증했다는 것은 다르다. 검증 완료로 표시하지 않는다.

**새 전문화의 실제 원문 URL을 찾으면** 결과 보고와 추후 공개 가능한 근거 인덱스에 URL·검증일·실제 패치 범위를 기록한다. 사용자의 명시적 편집 요청 없이 모든 신규 자료를 자동 GitHub에 커밋할 필요는 없다.

## 4. 기존 7개 V11 전문화 탐색 인덱스

| 한국어 | 영문 검색 키 | 기본 작업 |
|---|---|---|
| 화염 마법사 | Fire Mage | 기존 교본 UPDATE |
| 냉기 마법사 | Frost Mage | 기존 교본 UPDATE |
| 냉기 죽음의 기사 | Frost Death Knight | 기존 교본 UPDATE |
| 사격 사냥꾼 | Marksmanship Hunter | 기존 교본 UPDATE |
| 야수 사냥꾼 | Beast Mastery Hunter | 기존 교본 UPDATE |
| 잠행 도적 | Subtlety Rogue | 기존 교본 UPDATE |
| 암살 도적 | Assassination Rogue | 기존 교본 UPDATE |
| 비전 마법사 | Arcane Mage | 기존 7개 정본에는 없으므로 CREATE, 단 이전 초안은 참고 |

이 표의 '기본 작업'은 현재 기준 원본 V11에 따른 것이다. 사용자가 **업데이트된 8전문화 HTML을 새 정본으로 승인**하면 인덱스도 정본의 실제 전문화 목록에 맞춰 갱신한다.

## 4.1. 2026-11-11 신규 생존 사냥꾼 자료 확인

사용자의 `생존 사냥꾼` CREATE 실작업에서 12.1.5 최신 출처를 대조했다.
- [Wowhead 생존 회전](https://www.wowhead.com/ko/guide/classes/hunter/survival/rotation-cooldowns-pve-dps) · 2026-10-13 갱신
- [Method 생존 운용](https://www.method.gg/guides/survival-hunter/playstyle-and-rotation) · 2026-10-14 갱신
- [Icy Veins 생존 회전](https://www.icy-veins.com/wow/survival-hunter-pve-dps-rotation-cooldowns-abilities) · 2026-10-12 갱신
- [Icy Veins 생존 특성](https://www.icy-veins.com/wow/survival-hunter-pve-dps-spec-builds-talents) · 2026-10-22 갱신

현재 **7개 전문화 V11 원본에는 생존이 없으며**, 2026-11-11 별도 개인 파일로 8번째 교본을 생성해 전달했다. 해당 HTML을 다음 정본으로 승격하는 것은 사용자의 검토·승인을 기다린다. 공략·메뉴 기능/검증 내용: [생존 제작 기록](CHAT_FIRST_RUN_SURVIVAL_20261111.md). 실제 완성 HTML을 공개 저장소에 보관하지 않는다.

## 5. 저작권·근거 표현

- 외부 공략의 **전체 표·문단·대량 번역문을 복제하지 말고**, 기술적 조건을 검토한 뒤 독자적인 한국어 설명으로 표현한다.
- 인용은 필요 최소한만, URL로 연결. 링크가 실제로 접근되는지 확인한다. 인용했다는 사실은 메커니즘 승인 증거가 아님.
- 공식 spell ID, 버프 이름, 주문 아이콘은 실제 데이터와 맞지 않으면 `미확인`으로 유지.
- 출처에서 게임플레이 판단 근거가 모호하면 다른 모델의 추론만으로 사실을 확정하지 않는다.
- 공개 GitHub에는 제목/URL/확인일/패치/해시 같은 **메타데이터만** 저장한다. 사용자가 제공한 개인 원문은 개인 실행 환경에서만 분석한다.

## 6. 작업 완료 보고에 반드시 들어갈 정보

- 실제 사용한 주요 URL과 페이지의 패치/수정일(확인 가능할 경우).
- 어떤 전문화·영웅 특성·대상 수를 다뤘는지.
- **보조 출처를 사용한 경우에만** 대조한 주요 조건과 차이. 사용하지 않았으면 기준 단일 출처와 확인한 공식 패치/주문 근거를 명시.
- 실제 공식 주문 ID·번역명을 검증한 부분과 미확인 부분.
- **'원문 근거 확인'**, **'의미 검토 필요'**, **'브라우저/UI PASS'**를 서로 혼동하지 않는 상태 구분.
