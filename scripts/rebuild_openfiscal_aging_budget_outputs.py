# -*- coding: utf-8 -*-
"""Rebuild derived aging-budget CSVs from the downloaded OpenFiscal matches."""

from __future__ import annotations

import site
import sys
import re
from pathlib import Path

USER_SITE = site.getusersitepackages()
if USER_SITE and USER_SITE not in sys.path:
    sys.path.append(USER_SITE)

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DERIVED = DATA / "derived"
KEYWORD_PATTERN = re.compile(
    r"노인|고령|고령자|어르신|기초연금|기초노령연금|장기요양|치매|경로당|독거노인|노인돌봄|노인맞춤돌봄"
)


def classify_program(name: str) -> str:
    if "기초연금" in name or "기초노령연금" in name:
        return "기초연금"
    if "노인일자리" in name or "노인 일자리" in name:
        return "노인일자리"
    if "장기요양" in name or "치매" in name:
        return "장기요양·치매"
    if "돌봄" in name or "독거" in name:
        return "노인돌봄"
    return "기타 노인·고령화"


def main() -> None:
    path = DATA / "openfiscal_VW_OPFI940_aging_budget_matches.csv"
    matches = pd.read_csv(path)
    matches = matches[
        matches["SACTV_NM"].fillna("").astype(str).str.contains(KEYWORD_PATTERN, na=False)
    ].copy()
    matches["aging_budget_category"] = matches["SACTV_NM"].fillna("").astype(str).map(classify_program)
    matches["program_key"] = (
        matches["OFFC_NM"].fillna("").astype(str)
        + "|"
        + matches["FSCL_NM"].fillna("").astype(str)
        + "|"
        + matches["ACTV_NM"].fillna("").astype(str)
        + "|"
        + matches["SACTV_NM"].fillna("").astype(str)
    )

    matches.drop(columns=["program_key"]).to_csv(path, index=False, encoding="utf-8-sig")

    grouped = (
        matches.groupby("FSCL_YY", dropna=False)
        .agg(
            program_count=("SACTV_NM", "nunique"),
            program_line_count=("program_key", "nunique"),
            budget_amount_thousand_krw=("budget_amount_thousand_krw", "sum"),
        )
        .reset_index()
        .rename(columns={"FSCL_YY": "year"})
    )
    grouped["budget_amount_trillion_krw"] = (
        grouped["budget_amount_thousand_krw"] / 1_000_000_000
    ).round(3)

    categories = (
        matches.pivot_table(
            index="FSCL_YY",
            columns="aging_budget_category",
            values="budget_amount_thousand_krw",
            aggfunc="sum",
            fill_value=0,
        )
        .reset_index()
        .rename(columns={"FSCL_YY": "year"})
    )
    for category in ["기초연금", "노인일자리", "장기요양·치매", "노인돌봄", "기타 노인·고령화"]:
        if category not in categories.columns:
            categories[category] = 0
        categories[f"{category}_trillion_krw"] = (categories[category] / 1_000_000_000).round(3)

    trend = grouped.merge(
        categories[
            [
                "year",
                "기초연금_trillion_krw",
                "노인일자리_trillion_krw",
                "장기요양·치매_trillion_krw",
                "노인돌봄_trillion_krw",
                "기타 노인·고령화_trillion_krw",
            ]
        ],
        on="year",
        how="left",
    ).sort_values("year")
    trend.to_csv(DERIVED / "openfiscal_aging_budget_trends.csv", index=False, encoding="utf-8-sig")

    category_long = (
        matches.groupby(["FSCL_YY", "aging_budget_category"], dropna=False)
        .agg(
            program_count=("SACTV_NM", "nunique"),
            budget_amount_thousand_krw=("budget_amount_thousand_krw", "sum"),
        )
        .reset_index()
        .rename(columns={"FSCL_YY": "year", "aging_budget_category": "category"})
    )
    category_long["budget_amount_trillion_krw"] = (
        category_long["budget_amount_thousand_krw"] / 1_000_000_000
    ).round(3)
    category_long.to_csv(
        DERIVED / "openfiscal_aging_budget_category_trends.csv",
        index=False,
        encoding="utf-8-sig",
    )

    latest_year = int(trend["year"].max())
    top_programs = (
        matches[matches["FSCL_YY"] == latest_year]
        .groupby(["SACTV_NM", "aging_budget_category"], dropna=False)
        .agg(
            budget_amount_thousand_krw=("budget_amount_thousand_krw", "sum"),
            offices=("OFFC_NM", lambda values: ", ".join(sorted(set(map(str, values)))[:3])),
        )
        .reset_index()
        .rename(columns={"SACTV_NM": "program_name", "aging_budget_category": "category"})
        .sort_values("budget_amount_thousand_krw", ascending=False)
        .head(15)
    )
    top_programs["year"] = latest_year
    top_programs["budget_amount_trillion_krw"] = (
        top_programs["budget_amount_thousand_krw"] / 1_000_000_000
    ).round(3)
    top_programs.to_csv(
        DERIVED / "openfiscal_aging_budget_top_programs_latest.csv",
        index=False,
        encoding="utf-8-sig",
    )

    print(trend.head(8).to_string(index=False))
    print(trend.tail(3).to_string(index=False))


if __name__ == "__main__":
    main()
