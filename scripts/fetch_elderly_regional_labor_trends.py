# -*- coding: utf-8 -*-
"""Fetch regional elderly labor-market trends and estimate regional slopes."""

from __future__ import annotations

import math
import site
import sys
from pathlib import Path

USER_SITE = site.getusersitepackages()
if USER_SITE and USER_SITE not in sys.path:
    sys.path.append(USER_SITE)

ROOT = Path(__file__).resolve().parents[1]
KOREA_ROOT = ROOT.parent
if str(KOREA_ROOT) not in sys.path:
    sys.path.insert(0, str(KOREA_ROOT))

import pandas as pd

from apifunction.kosis import fetch_kosis_statistics, kosis_records_to_dataframe

DATA = ROOT / "data"
DERIVED = DATA / "derived"
START_YEAR = 2010
END_YEAR = 2025
AGE_LABEL = "60세이상"

TABLES = {
    "economic_activity": "DT_1DA7015S",
    "employed": "DT_1DA7031S",
    "unemployed": "DT_1DA7095S",
}

FOCAL_ITEMS = ["취업자", "고용률", "실업자", "비경제활동인구"]


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def fetch_table(table_id: str, *, obj_l3: bool = False) -> pd.DataFrame:
    records = fetch_kosis_statistics(
        table_id,
        org_id="101",
        prd_se="Y",
        start_prd_de=str(START_YEAR),
        end_prd_de=str(END_YEAR),
        itm_id="ALL",
        obj_l1="ALL",
        obj_l2="ALL",
        obj_l3="ALL" if obj_l3 else "",
        timeout=180,
    )
    return kosis_records_to_dataframe(records)


def linear_fit(group: pd.DataFrame) -> pd.Series:
    g = group.dropna(subset=["year", "value"]).sort_values("year")
    if len(g) < 3:
        return pd.Series(
            {
                "n_years": len(g),
                "slope_per_year": math.nan,
                "intercept": math.nan,
                "r2": math.nan,
                "first_year": math.nan,
                "first_value": math.nan,
                "latest_year": math.nan,
                "latest_value": math.nan,
                "change_abs": math.nan,
                "change_pct": math.nan,
            }
        )
    x = g["year"].astype(float)
    y = g["value"].astype(float)
    x_center = x - x.min()
    slope = ((x_center - x_center.mean()) * (y - y.mean())).sum() / ((x_center - x_center.mean()) ** 2).sum()
    intercept = y.mean() - slope * x_center.mean()
    pred = intercept + slope * x_center
    ss_res = ((y - pred) ** 2).sum()
    ss_tot = ((y - y.mean()) ** 2).sum()
    first = g.iloc[0]
    latest = g.iloc[-1]
    change_abs = float(latest["value"] - first["value"])
    change_pct = change_abs / float(first["value"]) * 100 if float(first["value"]) else math.nan
    return pd.Series(
        {
            "n_years": len(g),
            "slope_per_year": round(float(slope), 4),
            "intercept": round(float(intercept), 4),
            "r2": round(float(1 - ss_res / ss_tot), 4) if ss_tot else math.nan,
            "first_year": int(first["year"]),
            "first_value": round(float(first["value"]), 2),
            "latest_year": int(latest["year"]),
            "latest_value": round(float(latest["value"]), 2),
            "change_abs": round(change_abs, 2),
            "change_pct": round(change_pct, 2) if not math.isnan(change_pct) else math.nan,
        }
    )


def build_outputs() -> dict[str, Path]:
    economic = fetch_table(TABLES["economic_activity"])
    employed = fetch_table(TABLES["employed"])
    unemployed = fetch_table(TABLES["unemployed"], obj_l3=True)

    raw_economic = DATA / "regional_elderly_labor_DT_1DA7015S.csv"
    raw_employed = DATA / "regional_elderly_employed_DT_1DA7031S.csv"
    raw_unemployed = DATA / "regional_elderly_unemployed_DT_1DA7095S.csv"
    write_csv(economic, raw_economic)
    write_csv(employed, raw_employed)
    write_csv(unemployed, raw_unemployed)

    econ = economic[(economic["C1_NM"] != "계") & (economic["C2_NM"] == AGE_LABEL)].copy()
    emp = employed[(employed["C1_NM"] != "계") & (employed["C2_NM"] == AGE_LABEL)].copy()
    unemp = unemployed[(unemployed["C1_NM"] != "계") & (unemployed["C3_NM"] == AGE_LABEL)].copy()

    econ["year"] = pd.to_numeric(econ["PRD_DE"], errors="coerce").astype(int)
    emp["year"] = pd.to_numeric(emp["PRD_DE"], errors="coerce").astype(int)
    unemp["year"] = pd.to_numeric(unemp["PRD_DE"], errors="coerce").astype(int)
    econ["value"] = pd.to_numeric(econ["DT"], errors="coerce")
    emp["value"] = pd.to_numeric(emp["DT"], errors="coerce")
    unemp["value"] = pd.to_numeric(unemp["DT"], errors="coerce")

    trend_parts = []
    econ_items = econ[econ["ITM_NM"].isin(["15세이상인구", "경제활동인구", "경제활동참가율", "고용률", "비경제활동인구"])]
    trend_parts.append(
        econ_items.assign(age_group="60세 이상")[
            ["year", "C1", "C1_NM", "age_group", "ITM_NM", "value", "UNIT_NM", "TBL_ID", "TBL_NM"]
        ]
    )
    trend_parts.append(
        emp.assign(age_group="60세 이상")[
            ["year", "C1", "C1_NM", "age_group", "ITM_NM", "value", "UNIT_NM", "TBL_ID", "TBL_NM"]
        ]
    )
    trend_parts.append(
        unemp.assign(age_group="60세 이상")[
            ["year", "C1", "C1_NM", "age_group", "ITM_NM", "value", "UNIT_NM", "TBL_ID", "TBL_NM"]
        ]
    )
    trends = pd.concat(trend_parts, ignore_index=True).rename(
        columns={
            "C1": "region_code",
            "C1_NM": "region",
            "ITM_NM": "item",
            "UNIT_NM": "unit",
            "TBL_ID": "table_id",
            "TBL_NM": "table_name",
        }
    )
    trends = trends.sort_values(["item", "region", "year"])

    slopes_input = trends[trends["item"].isin(FOCAL_ITEMS)].copy()
    slopes = (
        slopes_input.groupby(["region_code", "region", "age_group", "item", "unit"], as_index=False)
        .apply(linear_fit, include_groups=False)
        .reset_index(drop=True)
    )
    slopes["slope_label"] = slopes.apply(
        lambda r: "퍼센트포인트/년" if r["unit"] == "%" else f"{r['unit']}/년",
        axis=1,
    )
    slopes = slopes.sort_values(["item", "slope_per_year"], ascending=[True, False])

    trend_path = DERIVED / "elderly_regional_labor_60plus_trends.csv"
    slopes_path = DERIVED / "elderly_regional_labor_60plus_slopes.csv"
    write_csv(trends, trend_path)
    write_csv(slopes, slopes_path)
    return {
        "economic_raw": raw_economic,
        "employed_raw": raw_employed,
        "unemployed_raw": raw_unemployed,
        "trends": trend_path,
        "slopes": slopes_path,
    }


def main() -> None:
    for key, path in build_outputs().items():
        print(f"{key}: {path}")


if __name__ == "__main__":
    main()
