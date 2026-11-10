# 코드 이관 변경 내역

- 원본 `engine/*.py`를 `engine/v2/*.py`로 파일별 보존.
- 모듈 경로 변경에 따라 `build.py`, `import_v11.py`의 `ROOT`를 프로젝트 루트로 조정.
- `import_v11.py`의 `engine.html_spans` 절대 import를 `engine.v2.html_spans`에 상응하는 상대 import로 변경.
- 실제 전문화 데이터 없이도 수행할 수 있도록 합성 테스트 파일 추가.
- CLI 기본 경로에는 원본 V2 데이터가 없으므로 검증을 시도하지 않습니다.
- `templates/shell.html`은 렌더링 코드/스타일만 포함하며 V11 실제 교본 장 HTML은 제외되었습니다.
