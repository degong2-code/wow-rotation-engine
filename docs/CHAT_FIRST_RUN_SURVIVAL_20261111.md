# Chat-first RUN — 생존 사냥꾼 신규 제작 및 왼쪽 2단 메뉴 접기/펼치기

- 실행일: 2026-11-11 (KST)
- 기록 상태: **완성 HTML 채팅에서 개인 전달 / 사용자 최종 승인 전 검토본**
- 제품 방식: ADR-003 / CHAT_FIRST_PLAYBOOK, 별도 AI API·OAuth·Codespaces 불필요
- 사용자 요청: `생존 사냥꾼 제작` + `왼쪽 전문화 메뉴 상위/하위 항목 숨기기`

## 전달한 실제 파일 (비공개, GitHub에 업로드하지 않음)

- 사용자 개인 V11 기준: `wow_rotation_manual_engine_v2.html`, **898,297바이트**; SHA-256 `5d70279c4dd073eccef1f3b13565a8f555cd81c9f0a5b7eda7e3485e410742be`
- 전달된 단일 HTML 이름: `wow_rotation_v11_survival_collapsible.html`
- 출력 크기: **1,031,697바이트**; SHA-256 `dce1790d115fc12e50e5339850f40a1cd10041173a06c3ff304805433fa44516`
- **기존 7개 `manual-view` 연결된 원본 영역 858,646바이트가 원본과 바이트 동일**. 공개 GitHub에는 해당 영역이나 결과 HTML 없음.
- 전체 전문화 **8개**, 생존 **10개 장**, 단일/광역 × 파수꾼/무리의 지도자 **우선순위 4개 표·총 38개 행**, 생존 장 내 도움말 마커 6개 및 기술 연결 139개(반복 포함).
- 실전 스킬 사용 조건은 참고 공략을 바탕으로 *조건부 설명*으로 작성했으며, 게임 내 모든 특성·장비 조합의 최적 딜사이클을 독립적으로 검증한 것은 아님.
- 완성 HTML은 **사용자 채팅의 개인 파일 링크**로 제공하며 공개 GitHub/Actions/Pages에 올리지 않는다.

## 자료 탐색 기록 — Midnight Season 2 / 12.1.5

- [Wowhead Survival Rotation](https://www.wowhead.com/ko/guide/classes/hunter/survival/rotation-cooldowns-pve-dps) (2026-10-13 갱신): 살상 명령 / 창끝 / 자원 상한, 파수꾼 표식 / 무리의 지도자 야수 소환 조건, 단일/광역.
- [Method Survival Playstyle and Rotation](https://www.method.gg/guides/survival-hunter/playstyle-and-rotation) (2026-10-14 갱신): 오프너, 단일/다수 기술 순서, 제압·붐스틱·선택형 Flamefang Pitch.
- [Icy Veins Survival Rotation](https://www.icy-veins.com/wow/survival-hunter-pve-dps-rotation-cooldowns-abilities) (2026-10-12 갱신): 창끝 생성/소비, 제압 전후 예외, 영웅/특성 조건과 오프너 변형.
- [Icy Veins Survival Talents](https://www.icy-veins.com/wow/survival-hunter-pve-dps-spec-builds-talents) (2026-10-22 갱신): 전체 콘텐츠 파수꾼 권장, 무리의 지도자 빌드별 강점 구분.
- 주문 ID를 확인할 수 있는 Wowhead 페이지와 기술 아이콘 파일명을 연결. 미확인 ID/아이콘 또는 한국어 현지화가 불확실한 선택 기술은 추측하지 않았다.

**게임플레이 근거 해석 주의:** Method의 단순화 오프너와 Icy Veins의 빌드별 개별 오프너가 다르므로 절대 1개의 고정 오프너로 통합하지 않았다. 제압의 초 단위 효과 시간도 자료 간 단순화 설명과 실제 주문 툴팁을 혼동하지 않는다. 원시의 쇄도 등 일부 특성의 정확한 한국어 이름/ID는 후속 공식 자료 확인이 필요하다.

## 왼쪽 메뉴 — 직업/전문화 2단 접기/펼치기

원본 V11의 직업/전문화/영웅 특성 목록을 접근 가능한 중첩 메뉴로 확장:
- **직업 토글:** 마법사 / 죽음의 기사 / 사냥꾼 / 도적, `aria-expanded` + `aria-controls`와 독립 panel `hidden`.
- **전문화 토글:** 각 직업의 전문화명을 누르면 영웅 특성 버튼 목록만 접거나 펼침.
- **선택 연계:** 전용 `data-guide-button` 선택시 해당 `manual-view`와 목차를 활성화; 현재 선택 직업/전문화는 자동으로 펼침.
- **키보드:** `button type=button` 기반으로 Enter/Space 작동, 포커스 스타일, `aria-expanded`.
- **기존 hero switch 보존:** 냉기 마법사/암살 도적의 영웅 특성 전환과 독립적으로 생존 `sentinel`/`packleader` 선택 상태를 제어.
- **기본 상태:** 화염 선택 및 마법사 메뉴 열림; 나머지 직업은 접힘.
- 스타일은 기존 V11 CSS에 추가하며, 원본 7개 HTML 본문 자체를 재직렬화하지 않음.

## 테스트 증거

1. 기존 HTML 정본 SHA 검증 및 7개 `manual-view` 원문 연속 문자열 **858,646바이트 동일성 PASS**.
2. BeautifulSoup DOM: 8개 `manual-view`, 중복 `id` 없음, 8개 전문화/70개 목차 링크 모두 실제 섹션에 연결.
3. Node.js `node --check`: 원본 툴팁 스크립트 + 확장된 전문화/영웅 전환 스크립트 + 새 메뉴 스크립트 **3개 PASS**.
4. Chromium/Playwright **1365×850 및 390×844**: 직업·전문화 접고 펼치기 PASS, 생존 단일 HTML 보기 PASS, 파수꾼↔무리의 지도자 PASS, 기존 사격/야수/냉기/암살 등 다른 뷰 전환 PASS, `?` 도움말과 Escape 닫기 PASS, URL hash 목차 복원 PASS. JS page errors **0**.
5. 모바일 390px에서 문서 전체 가로 넘침 **없음**. 우선순위/비교표는 기존처럼 표 영역 내부 가로 스크롤.
6. CI는 실제 개인 HTML을 사용하지 않으므로 이 증거를 **합성 GitHub Actions 테스트와 동일하다고 주장하지 않음**. 스크린샷 사용자 제공 없음.

## 재사용 지침 및 승인 조건

- 기존 원본/결과 HTML은 개인 ChatGPT Project/Library 등 사용자만 접근할 수 있는 위치에 보관하고, **새 출력물을 정본으로 승격하는 것은 사용자 평가·승인 후** 결정.
- 사용자가 이후 `생존 사냥꾼 업데이트`를 요청하면 승인된 이 결과 HTML을 확보하고 변경 영역만 수정; 새 정본이 승인되기 전에는 기준 7전문화 V11을 자동 교체하지 않는다.
- 메뉴 기능 변경은 콘텐츠와 독립된 공통 UI 개선이므로 향후 모든 새 교본에 유지하되, 원본 섹션 byte 동일 규칙을 지킨다.
