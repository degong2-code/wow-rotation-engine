# GitHub Pages 준비 상태

`deploy-review-pages.yml`은 **수동 실행 전용**입니다. 메인 CI에서 자동으로 Pages에 게시하지 않습니다.

## 사전 설정 (관리자 1회)

GitHub `Settings → Pages → Build and deployment → Source: GitHub Actions`로 지정해야 합니다.
현재 연결된 GitHub 기능에는 Pages 설정 변경·워크플로 수동 실행 작업이 없으므로 해당 설정이 필요합니다.

## 배포 대상

- `dist/pages/index.html`: 공개용 **데이터 검토 화면**. 실전 딜사이클 교본이 아닙니다.
- `dist/pages/audit.json`: **미검증 규칙 게시 불가** 감사 결과.

워크플로를 수동 실행하면 코드 테스트·데이터 검증 후 이 두 파일만 Pages에 배포합니다.
실제 V11 전문화 공략의 전체 번역 본문, 원문, 캡처본, API 키는 배포하지 않습니다.

**자동 업데이트 버튼은 아직 구현하지 않았습니다.**
실전 교본의 Pages 배포는 한국어 기술명·규칙 조건·출처·권리 검토 후 별도로 진행합니다.

예상 URL: `https://degong2-code.github.io/wow-rotation-engine/` (실제 배포 성공 전 미확정).
