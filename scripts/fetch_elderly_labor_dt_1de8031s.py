# -*- coding: utf-8 -*-
"""Fetch and derive KOSIS DT_1DE8031S elderly labor-market data."""

from __future__ import annotations

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
TABLE_ID = "DT_1DE8031S"
START_YEAR = 2010
END_YEAR = 2025

ITEM_ORDER = [
    "고령층인구",
    "경제활동인구",
    "취업자",
    "고용률",
    "실업자",
    "실업률",
    "비경제활동인구",
]

AGE_ORDER = ["55~79세 전체", "55~64세", "65~79세"]


def clean_age_group(value: object) -> str:
    text = str(value).strip()
    if text == "* 55~79세":
        return "55~79세 전체"
    return text


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def fetch_raw() -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for year in range(START_YEAR, END_YEAR + 1):
        period = f"{year}05"
        records = fetch_kosis_statistics(
            TABLE_ID,
            org_id="101",
            prd_se="M",
            start_prd_de=period,
            end_prd_de=period,
            itm_id="ALL",
            obj_l1="ALL",
            timeout=60,
        )
        frame = kosis_records_to_dataframe(records)
        frames.append(frame)
        print(f"fetched {period}: {len(frame)} rows")
    raw = pd.concat(frames, ignore_index=True)
    return raw


def build_outputs(raw: pd.DataFrame) -> dict[str, Path]:
    raw = raw.copy()
    raw["DT"] = pd.to_numeric(raw["DT"], errors="coerce")
    raw["year"] = raw["PRD_DE"].astype(str).str[:4].astype(int)
    raw["month"] = raw["PRD_DE"].astype(str).str[4:6].astype(int)
    raw["age_group"] = raw["C1_NM"].map(clean_age_group)
    raw["item"] = raw["ITM_NM"]
    raw["value"] = raw["DT"]
    raw["unit"] = raw["UNIT_NM"]
    raw["item_order"] = raw["item"].map({item: idx for idx, item in enumerate(ITEM_ORDER)})
    raw["age_order"] = raw["age_group"].map({age: idx for idx, age in enumerate(AGE_ORDER)})

    trends = raw[raw["item"].isin(ITEM_ORDER) & raw["age_group"].isin(AGE_ORDER)].copy()
    trends = trends.sort_values(["item_order", "age_order", "year"])
    trends = trends[
        [
            "PRD_DE",
            "year",
            "month",
            "age_group",
            "item",
            "value",
            "unit",
            "item_order",
            "age_order",
            "TBL_ID",
            "TBL_NM",
        ]
    ].rename(columns={"PRD_DE": "period", "TBL_ID": "table_id", "TBL_NM": "table_name"})

    first_year = int(trends["year"].min())
    latest_year = int(trends["year"].max())
    summary_rows: list[dict[str, object]] = []
    for (item, age_group), group in trends.groupby(["item", "age_group"], sort=False):
        group = group.sort_values("year")
        first = group[group["year"] == first_year].iloc[0]
        latest = group[group["year"] == latest_year].iloc[0]
        first_value = float(first["value"])
        latest_value = float(latest["value"])
        change_abs = latest_value - first_value
        change_pct = change_abs / first_value * 100 if first_value else None
        summary_rows.append(
            {
                "item": item,
                "age_group": age_group,
                "unit": latest["unit"],
                "first_year": first_year,
                "first_value": round(first_value, 1),
                "latest_year": latest_year,
                "latest_value": round(latest_value, 1),
                "change_abs": round(change_abs, 1),
                "change_pct": round(change_pct, 1) if change_pct is not None else None,
            }
        )
    summary = pd.DataFrame(summary_rows)
    summary["item_order"] = summary["item"].map({item: idx for idx, item in enumerate(ITEM_ORDER)})
    summary["age_order"] = summary["age_group"].map({age: idx for idx, age in enumerate(AGE_ORDER)})
    summary = summary.sort_values(["item_order", "age_order"])
    summary = summary[
        [
            "item",
            "age_group",
            "unit",
            "first_year",
            "first_value",
            "latest_year",
            "latest_value",
            "change_abs",
            "change_pct",
        ]
    ]

    raw_path = DATA / "elderly_labor_DT_1DE8031S.csv"
    trends_path = DERIVED / "elderly_labor_dt_1de8031s_trends.csv"
    summary_path = DERIVED / "elderly_labor_dt_1de8031s_summary.csv"
    write_csv(raw, raw_path)
    write_csv(trends, trends_path)
    write_csv(summary, summary_path)
    return {"raw": raw_path, "trends": trends_path, "summary": summary_path}


def main() -> None:
    outputs = build_outputs(fetch_raw())
    for name, path in outputs.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
