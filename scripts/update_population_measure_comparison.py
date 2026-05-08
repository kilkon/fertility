from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
KOREA_ROOT = ROOT.parent
if str(KOREA_ROOT) not in sys.path:
    sys.path.insert(0, str(KOREA_ROOT))

from apifunction.kosis import fetch_kosis_table


START_YEAR = 2000
END_YEAR = 2024


def numeric_series(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.replace(",", "", regex=False), errors="coerce")


def load_registered_population() -> pd.Series:
    raw = fetch_kosis_table("DT_1B040A3", cycle="A", start_year=START_YEAR, end_year=END_YEAR)
    raw["year"] = pd.to_numeric(raw["PRD_DE"], errors="coerce").astype("Int64")
    raw["population"] = numeric_series(raw["DT"])
    total = raw[
        (raw["C1_NM"].astype(str) == "전국")
        & (raw["ITM_NM"].astype(str) == "총인구수")
        & (raw["year"].between(START_YEAR, END_YEAR))
    ]
    return total.set_index("year")["population"].sort_index()


def load_projection_population() -> pd.Series:
    raw = pd.read_csv(ROOT / "data" / "population_projection_indicators.csv")
    raw["year"] = pd.to_numeric(raw["PRD_DE"], errors="coerce").astype("Int64")
    raw["population"] = numeric_series(raw["DT"])
    total = raw[
        (raw["C1"].astype(str) == "1")
        & (raw["C2_NM"].astype(str) == "전국")
        & (raw["C3_NM"].astype(str) == "총인구(명)")
        & (raw["year"].between(START_YEAR, END_YEAR))
    ]
    return total.set_index("year")["population"].sort_index()


def load_census_population() -> pd.Series:
    historical = pd.Series(
        {
            2000: 46_136_101,
            2005: 47_278_951,
            2010: 48_580_293,
        },
        name="population",
        dtype="float64",
    )
    registered_census = fetch_kosis_table("INH_1IN1503_01", cycle="A", start_year=2015, end_year=END_YEAR)
    registered_census["year"] = pd.to_numeric(registered_census["PRD_DE"], errors="coerce").astype("Int64")
    registered_census["population"] = numeric_series(registered_census["DT"])
    annual = registered_census[
        (registered_census["C1_NM"].astype(str) == "전국")
        & (registered_census["C2_NM"].astype(str) == "합계")
        & (registered_census["ITM_NM"].astype(str) == "총인구(명)")
        & (registered_census["year"].between(2015, END_YEAR))
    ].set_index("year")["population"]
    return pd.concat([historical, annual]).sort_index()


def main() -> None:
    years = pd.Index(range(START_YEAR, END_YEAR + 1), name="year")
    out = pd.DataFrame(index=years)
    out["registered_population"] = load_registered_population().reindex(years)
    out["census_population"] = load_census_population().reindex(years)
    out["projection_population"] = load_projection_population().reindex(years)
    out = out.reset_index()
    integer_cols = ["registered_population", "census_population", "projection_population"]
    for col in integer_cols:
        out[col] = out[col].round().astype("Int64")
    out.to_csv(ROOT / "data" / "population_measure_comparison.csv", index=False, encoding="utf-8-sig")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
