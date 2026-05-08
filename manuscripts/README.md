# 마크다운 원고 편집 안내

이 폴더의 `chapters`와 `sections`에 있는 `.md` 파일이 책의 원고 원천입니다.

- 원고를 수정한 뒤 `python scripts\build_book_pages.py`를 실행하면 HTML에 반영됩니다.
- 자동 반영을 원하면 `python scripts\watch_manuscripts.py`를 켜 둔 상태에서 원고를 저장하면 됩니다.
- 각 HTML 장·절 상단의 `원고 수정` 버튼을 누르면 해당 원고를 브라우저 편집기에서 수정할 수 있습니다.
- 저장 기능은 `python scripts\editor_server.py`로 로컬 편집 서버를 실행한 상태에서 사용할 수 있습니다.
- 그림은 원하는 문단 위치에 `{{chart:차트ID}}` 형식으로 넣습니다.
- 작은 보조 그림은 `{{chart:차트ID|small}}`처럼 넣을 수 있습니다.
- 일반 이미지도 `![그림 설명](../data/example.png)` 형식으로 넣을 수 있습니다.
- 표는 일반 마크다운 표 문법을 사용할 수 있습니다.
- 5.4절의 고령화 예산 사업 표는 `{{aging_budget_program_table}}`로 삽입합니다.

차트 ID와 CSV·출처 정보는 `scripts/build_book_pages.py`의 `CHART_META`에 정의되어 있습니다.
