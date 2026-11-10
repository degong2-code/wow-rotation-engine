# WoW Rotation Engine — 프로젝트 지식 지도

> 현재 판정·정책·HEAD는 [단일 인계 정본](HANDOFF_CURRENT.md)을 우선합니다. 과거 문서는 당시 작업의 영수증/설계를 보존한 기록이며 `main`의 현재 상태와 혼동하지 마세요.

| 찾으려는 정보 | 우선 경로 | 보조 위치 |
|---|---|---|
| 프로젝트 현재 상태·최종 목표·최신 정책·바로 다음 작업 | [HANDOFF_CURRENT.md](HANDOFF_CURRENT.md) | [PR #12](https://github.com/degong2-code/wow-rotation-engine/pull/12) |
| 현재 사용자용 단일 HTML | `engine/manual_site.py` | [MANUAL_PREVIEW.md](MANUAL_PREVIEW.md), `tests/test_manual_site.py` |
| 전문화·영웅 특성·순위 데이터 정본 | `content/public/manifest.json`, `content/public/rules/*.json` | `content/public/spells.json` |
| 현재 생성·회귀 영수증 | `.github/workflows/ci.yml`, [Actions #42805475905](https://github.com/degong2-code/wow-rotation-engine/actions/runs/42805475905) | `wow-rotation-quick-reference-html` Artifact (14일 보존) |
| 이전 V11/V2 상세 콘텐츠 구조/파서 | `engine/v2/rules.py`, `engine/v2/build.py` | `engine/v2/templates/shell.html`, [v2-origin-manifest.json](v2-origin-manifest.json), [V2_MIGRATION_STATUS.md](V2_MIGRATION_STATUS.md) |
| 23개 표/177행/79개 Advanced Tips 색인·한계 | `content/public/` | [PUBLIC_DATA.md](PUBLIC_DATA.md), [MANUAL_PREVIEW.md](MANUAL_PREVIEW.md) |
| 조건식 후보(현재 제품의 선행조건 아님) | `engine/condition_worklist.py`, `content/review/condition-candidates.json` | [CONDITION_WORKLIST.md](CONDITION_WORKLIST.md) |
| 공식 `ko_KR` 관측/404/불일치 | `content/review/blizzard-spell-20261110.json` | [BLIZZARD_LIVE_AUDIT_20261110.md](BLIZZARD_LIVE_AUDIT_20261110.md), [SPELL_TRIAGE.md](SPELL_TRIAGE.md) |
| 원문 변경 지문·AI 연결 후보 | `engine/source_snapshots.py` | [SOURCE_SNAPSHOTS.md](SOURCE_SNAPSHOTS.md) |
| Pages 준비/제한 | `.github/workflows/deploy-review-pages.yml` | [PAGES.md](PAGES.md) |
| 저작권·자격증명 경계 | [SECURITY.md](SECURITY.md) | [MIGRATION.md](MIGRATION.md) (역사 기록) |

## 개발·검증 최소 루틴

- **REUSE → CONNECT → EXTEND**: 기존 코드, V2 규칙 추출기 및 데이터 캐시/증거를 먼저 사용. 실제 필요가 입증되지 않으면 새 엔진/검사기를 늘리지 않음.
- **내용 복원 우선**: 새로운 상세 설명 데이터 구조를 만든 다음 기존 HTML 생성기에서 렌더링. 모든 역사적 177행을 완벽히 형식화할 때까지 막지 않는다.
- **변경 범위만 테스트**: 콘텐츠 JSON·수정 전문화·HTML 생성, 검색/상황 필터 등 관련 기능을 검증. CI의 기존 전체 테스트 PASS는 이미 저장돼 있으며 인계만 위해 수동 재실행하지 않음.
- **실제 구현 vs 실증**: 코드가 있다는 것과 게임/브라우저에서 검증됐다는 것은 다름. PR/Actions 링크 및 검증 범위를 항상 함께 기록.
- **PR 우선**: 별도 브랜치 → 최소 diff → Actions 자동 결과 확인 → PR. 병합·공식 승격은 사용자가 별도 승인하지 않으면 하지 않음.
- **비밀·원문**: 자격증명은 GitHub Secrets만, 저작권상 제한된 전체 공략 원문·대량 번역문은 PUBLIC 저장소/Artifact에 올리지 않음.
