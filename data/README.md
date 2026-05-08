# 인구·저출산·고령화 데이터

초기 웹페이지는 기존 `헬조선_인구_share` 프로젝트의 영광군 산출물 일부를 복사해 사용합니다.

- `yeonggwang_aging_indicators_by_year.csv`
- `yeonggwang_population_structure_by_year.csv`
- `yeonggwang_birth_cohort_summary.csv`

공식 자료 갱신은 `python scripts/fetch_population_book_data.py`에서 수행합니다. 이 스크립트는 `../apifunction`의 KOSIS, ECOS, e-나라지표, 열린재정 래퍼를 사용합니다.
