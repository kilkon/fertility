# -*- coding: utf-8 -*-
"""Fetch and derive KOSIS DT_1DE8051S elderly pension receipt data."""

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
TABLE_ID = "DT_1DE8051S"
START_YEAR = 2008
END_YEAR = 2025

SEX_ORDER = ["계", "남자", "여자"]

ITEM_LABELS = {
    "T00": "55~79세인구",
    "T10": "연금수령자",
    "T20": "월평균 10만원미만",
    "T30": "월평균 10~25만원미만",
    "T40": "월평균 25~50만원미만",
    "T50": "월평균 50~100만원미만",
    "T51": "월평균 100~150만원미만",
    "T52": "월평균 150만원이상",
    "T54": "평균수령액",
}

DISTRIBUTION_ITEMS = ["T20", "T30", "T40", "T50", "T51", "T52"]


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
    return pd.concat(frames, ignore_index=True)


def build_outputs(raw: pd.DataFrame) -> dict[str, Path]:
    raw = raw.copy()
    raw["DT"] = pd.to_numeric(raw["DT"], errors="coerce")
    raw["year"] = raw["PRD_DE"].astype(str).str[:4].astype(int)
    raw["month"] = raw["PRD_DE"].astype(str).str[4:6].astype(int)
    raw["sex"] = raw["C1_NM"].astype(str).str.strip()
    raw["item"] = raw["ITM_ID"].map(ITEM_LABELS).fillna(raw["ITM_NM"])
    raw["value"] = raw["DT"]
    raw["unit"] = raw["UNIT_NM"]
    raw["sex_order"] = raw["sex"].map({sex: idx for idx, sex in enumerate(SEX_ORDER)})

    wide = raw.pivot_table(
        index=["year", "month", "sex"],
        columns="ITM_ID",
        values="value",
        aggfunc="first",
    ).reset_index()
    wide = wide.rename(
        columns={
            "T00": "total_population_thousand",
            "T10": "pension_recipients_thousand",
            "T54": "average_amount_10k_krw",
            "T20": "under_10_thousand",
            "T30": "amount_10_25_thousand",
            "T40": "amount_25_50_thousand",
            "T50": "amount_50_100_thousand",
            "T51": "amount_100_150_thousand",
            "T52": "amount_150_plus_thousand",
        }
    )
    wide["recipient_rate"] = (
        wide["pension_recipients_thousand"] / wide["total_population_thousand"] * 100
    ).round(1)
    wide["high_amount_100plus_share"] = (
        (wide["amount_100_150_thousand"] + wide["amount_150_plus_thousand"])
        / wide["pension_recipients_thousand"]
        * 100
    ).round(1)
    wide["low_amount_under25_share"] = (
        (wide["under_10_thousand"] + wide["amount_10_25_thousand"])
        / wide["pension_recipients_thousand"]
        * 100
    ).round(1)
    wide["average_amount_10k_krw"] = wide["average_amount_10k_krw"].round(1)
    wide["sex_order"] = wide["sex"].map({sex: idx for idx, sex in enumerate(SEX_ORDER)})
    trends = wide.sort_values(["sex_order", "year"])[
        [
            "year",
            "month",
            "sex",
            "total_population_thousand",
            "pension_recipients_thousand",
            "recipient_rate",
            "average_amount_10k_krw",
            "low_amount_under25_share",
            "high_amount_100plus_share",
            "under_10_thousand",
            "amount_10_25_thousand",
            "amount_25_50_thousand",
            "amount_50_100_thousand",
            "amount_100_150_thousand",
            "amount_150_plus_thousand",
        ]
    ]

    distribution_rows: list[dict[str, object]] = []
    for _, row in trends.iterrows():
        total = float(row["pension_recipients_thousand"])
        for key, label in [
            ("under_10_thousand", "10만원 미만"),
            ("amount_10_25_thousand", "10~25만원 미만"),
            ("amount_25_50_thousand", "25~50만원 미만"),
            ("amount_50_100_thousand", "50~100만원 미만"),
            ("amount_100_150_thousand", "100~150만원 미만"),
            ("amount_150_plus_thousand", "150만원 이상"),
        ]:
            value = float(row[key])
            distribution_rows.append(
                {
                    "year": int(row["year"]),
                    "sex": row["sex"],
                    "amount_band": label,
                    "pension_recipients_thousand": round(value, 1),
                    "share_of_recipients": round(value / total * 100, 1) if total else None,
                }
            )
    distribution = pd.DataFrame(distribution_rows)

    first_year = int(trends["year"].min())
    latest_year = int(trends["year"].max())
    summary_rows: list[dict[str, object]] = []
    for sex, group in trends.groupby("sex", sort=False):
        group = group.sort_values("year")
        first = group[group["year"] == first_year].iloc[0]
        latest = group[group["year"] == latest_year].iloc[0]
        amount_change = latest["average_amount_10k_krw"] - first["average_amount_10k_krw"]
        amount_change_pct = amount_change / first["average_amount_10k_krw"] * 100
        rate_change = latest["recipient_rate"] - first["recipient_rate"]
        summary_rows.append(
            {
                "sex": sex,
                "first_year": first_year,
                "first_average_amount_10k_krw": round(float(first["average_amount_10k_krw"]), 1),
                "latest_year": latest_year,
                "latest_average_amount_10k_krw": round(float(latest["average_amount_10k_krw"]), 1),
                "amount_change_10k_krw": round(float(amount_change), 1),
                "amount_change_pct": round(float(amount_change_pct), 1),
                "first_recipient_rate": round(float(first["recipient_rate"]), 1),
                "latest_recipient_rate": round(float(latest["recipient_rate"]), 1),
                "recipient_rate_change_pctp": round(float(rate_change), 1),
                "latest_high_amount_100plus_share": round(float(latest["high_amount_100plus_share"]), 1),
                "latest_low_amount_under25_share": round(float(latest["low_amount_under25_share"]), 1),
            }
        )
    summary = pd.DataFrame(summary_rows)

    raw_path = DATA / "elderly_pension_DT_1DE8051S.csv"
    trends_path = DERIVED / "elderly_pension_dt_1de8051s_trends.csv"
    distribution_path = DERIVED / "elderly_pension_dt_1de8051s_distribution.csv"
    summary_path = DERIVED / "elderly_pension_dt_1de8051s_summary.csv"
    write_csv(raw, raw_path)
    write_csv(trends, trends_path)
    write_csv(distribution, distribution_path)
    write_csv(summary, summary_path)
    return {
        "raw": raw_path,
        "trends": trends_path,
        "distribution": distribution_path,
        "summary": summary_path,
    }


def main() -> None:
    outputs = build_outputs(fetch_raw())
    for name, path in outputs.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
