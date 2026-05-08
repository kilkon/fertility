# -*- coding: utf-8 -*-
"""Fetch and derive housing-support outcome data for the population book."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
KOREA_ROOT = ROOT.parent
DATA = ROOT / "data"
DERIVED = DATA / "derived"
YOUTH_RAW = KOREA_ROOT / "청년" / "data" / "raw" / "youth_charts"
KOSIS_KEY_FILE = KOREA_ROOT / "apifunction" / "kosis_api_key.txt"
KOSIS_URL = "https://kosis.kr/openapi/Param/statisticsParameterData.do"

SIDO_CODES = {
    "00",
    "11",
    "21",
    "22",
    "23",
    "24",
    "25",
    "26",
    "29",
    "31",
    "32",
    "33",
    "34",
    "35",
    "36",
    "37",
    "38",
    "39",
}
CAPITAL_CODES = {"11", "23", "31"}


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def fetch_kosis_vital(start_year: int = 2015, end_year: int = 2024) -> pd.DataFrame:
    key = KOSIS_KEY_FILE.read_text(encoding="utf-8").strip()
    params = {
        "method": "getList",
        "apiKey": key,
        "tblId": "DT_1B8000I",
        "orgId": "101",
        "startPrdDe": str(start_year),
        "endPrdDe": str(end_year),
        "itmId": "ALL",
        "format": "json",
        "jsonVD": "Y",
        "prdSe": "Y",
        "loadGubun": "2",
        "objL1": "ALL",
    }
    url = KOSIS_URL + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=90) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if isinstance(payload, dict) and payload.get("err"):
        raise RuntimeError(f"KOSIS error {payload.get('err')}: {payload.get('errMsg')}")
    return pd.DataFrame(payload)


def vital_sido_panel(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    df["region_code"] = df["C1"].astype(str).str.zfill(2)
    df = df[df["region_code"].isin(SIDO_CODES)].copy()
    df["year"] = pd.to_numeric(df["PRD_DE"], errors="coerce").astype(int)
    df["value"] = pd.to_numeric(df["DT"], errors="coerce")
    wanted = {
        "T10": "births",
        "T11": "crude_birth_rate",
        "T40": "marriages",
        "T41": "crude_marriage_rate",
    }
    df = df[df["ITM_ID"].isin(wanted)].copy()
    panel = (
        df.pivot_table(
            index=["year", "region_code", "C1_NM"],
            columns="ITM_ID",
            values="value",
            aggfunc="first",
        )
        .reset_index()
        .rename(columns={"C1_NM": "region", **wanted})
    )
    panel.columns.name = None
    return panel.rename(columns=wanted).sort_values(["region_code", "year"])


def under40_homeownership_panel() -> pd.DataFrame:
    owned = pd.read_csv(YOUTH_RAW / "DT_1OH0403_yearly.csv", dtype={"C1": str, "C3": str})
    nonowned = pd.read_csv(YOUTH_RAW / "DT_1OH0418_yearly.csv", dtype={"C1": str, "C3": str})

    def prep(df: pd.DataFrame, value_name: str) -> pd.DataFrame:
        part = df.copy()
        part["region_code"] = part["C1"].astype(str).str.zfill(2)
        part = part[
            part["region_code"].isin(SIDO_CODES)
            & part["C2"].astype(str).eq("0")
            & part["C3_NM"].isin(["30세미만", "30~39세"])
        ].copy()
        part["year"] = pd.to_numeric(part["PRD_DE"], errors="coerce").astype(int)
        part["value"] = pd.to_numeric(part["DT"], errors="coerce")
        return (
            part.groupby(["year", "region_code", "C1_NM"], as_index=False)["value"]
            .sum()
            .rename(columns={"C1_NM": "region", "value": value_name})
        )

    home = prep(owned, "under40_owner_households").merge(
        prep(nonowned, "under40_nonowner_households"),
        on=["year", "region_code", "region"],
        how="inner",
    )
    total = home["under40_owner_households"] + home["under40_nonowner_households"]
    home["under40_homeownership_rate"] = (home["under40_owner_households"] / total * 100).round(2)
    home["under40_nonowner_rate"] = (100 - home["under40_homeownership_rate"]).round(2)
    return home.sort_values(["region_code", "year"])


def regression_summary(panel: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    specs = [
        ("전국 시도 패널", panel[~panel["region_code"].eq("00")]),
        ("수도권 패널", panel[panel["region_code"].isin(CAPITAL_CODES)]),
    ]
    outcomes = [
        ("조혼인율", "crude_marriage_rate"),
        ("조출생률", "crude_birth_rate"),
    ]
    for group_name, sub in specs:
        sub = sub.dropna(subset=["under40_homeownership_rate", "year"]).copy()
        for outcome_label, outcome_col in outcomes:
            model_df = sub.dropna(subset=[outcome_col]).copy()
            if len(model_df) < 6:
                continue
            y = model_df[outcome_col].to_numpy(dtype=float)
            x_home = model_df["under40_homeownership_rate"].to_numpy(dtype=float)
            x_year = model_df["year"].to_numpy(dtype=float) - model_df["year"].min()
            x = np.column_stack([np.ones(len(model_df)), x_home, x_year])
            beta, *_ = np.linalg.lstsq(x, y, rcond=None)
            residual = y - x @ beta
            dof = max(len(model_df) - x.shape[1], 1)
            sigma2 = float((residual @ residual) / dof)
            try:
                cov = sigma2 * np.linalg.inv(x.T @ x)
                se_home = float(np.sqrt(cov[1, 1]))
            except np.linalg.LinAlgError:
                se_home = np.nan
            corr = float(np.corrcoef(x_home, y)[0, 1]) if len(model_df) > 1 else np.nan
            rows.append(
                {
                    "group": group_name,
                    "outcome": outcome_label,
                    "homeownership_coef": round(float(beta[1]), 4),
                    "homeownership_se": round(se_home, 4) if np.isfinite(se_home) else np.nan,
                    "year_coef": round(float(beta[2]), 4),
                    "correlation": round(corr, 4) if np.isfinite(corr) else np.nan,
                    "n": int(len(model_df)),
                    "model": "outcome = a + b*under40_homeownership_rate + c*year",
                }
            )
    return pd.DataFrame(rows)


def housing_finance_burden_by_age() -> pd.DataFrame:
    raw = pd.read_csv(YOUTH_RAW / "DT_1HDAAA06_yearly.csv", dtype={"C2": str, "C3": str})
    raw["year"] = pd.to_numeric(raw["PRD_DE"], errors="coerce").astype(int)
    raw["value"] = pd.to_numeric(raw["DT"], errors="coerce")
    age_groups = {
        "B1601": "29세 이하",
        "B1602": "30~39세",
    }
    metrics = {
        "C0411": "disposable_income_10k_krw",
        "C05": "assets_10k_krw",
        "C050102": "current_home_deposit_10k_krw",
        "C06": "debt_10k_krw",
        "C07": "annual_debt_repayment_10k_krw",
        "C08": "net_assets_10k_krw",
    }
    part = raw[
        raw["C1"].astype(str).eq("A0100")
        & raw["C2"].isin(age_groups)
        & raw["C3"].isin(metrics)
        & raw["ITM_ID"].astype(str).eq("T01")
    ].copy()
    part["age_group"] = part["C2"].map(age_groups)
    wide = (
        part.pivot_table(index=["year", "age_group"], columns="C3", values="value", aggfunc="first")
        .reset_index()
        .rename(columns=metrics)
        .sort_values(["age_group", "year"])
    )
    wide.columns.name = None
    wide["debt_to_disposable_income_pct"] = (
        wide["debt_10k_krw"] / wide["disposable_income_10k_krw"] * 100
    ).round(1)
    wide["repayment_to_disposable_income_pct"] = (
        wide["annual_debt_repayment_10k_krw"] / wide["disposable_income_10k_krw"] * 100
    ).round(1)
    wide["deposit_to_disposable_income_pct"] = (
        wide["current_home_deposit_10k_krw"] / wide["disposable_income_10k_krw"] * 100
    ).round(1)
    return wide


def housing_tenure_for_young_and_newlywed() -> pd.DataFrame:
    raw = pd.read_csv(YOUTH_RAW / "DT_KHFC_026_yearly.csv")
    raw["year"] = pd.to_numeric(raw["PRD_DE"], errors="coerce").astype(int)
    raw["value"] = pd.to_numeric(raw["DT"], errors="coerce")
    groups = {
        "30대 이하": "30대 이하",
        "신혼": "신혼",
        "미혼": "미혼",
    }
    tenure = ["자가", "전세", "보증금 있는 월세"]
    part = raw[raw["C1_NM"].isin(groups) & raw["ITM_NM"].isin(tenure)].copy()
    part["group"] = part["C1_NM"].map(groups)
    part = part.rename(columns={"ITM_NM": "tenure_type", "value": "share_pct"})
    return part[["year", "group", "tenure_type", "share_pct"]].sort_values(["group", "tenure_type", "year"])


def housing_consumption_pressure() -> pd.DataFrame:
    path = KOREA_ROOT / "청년" / "data" / "youth_qol_housing_consumption_share.csv"
    df = pd.read_csv(path)
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype(int)
    df["housing_share_pct"] = pd.to_numeric(df["housing_share_pct"], errors="coerce")
    return df.sort_values("year")


def main() -> None:
    raw_vital = fetch_kosis_vital()
    write_csv(raw_vital, DATA / "kosis_vital_sido_DT_1B8000I.csv")
    vital = vital_sido_panel(raw_vital)
    housing = under40_homeownership_panel()
    panel = housing.merge(vital, on=["year", "region_code", "region"], how="inner")
    panel["capital_area"] = panel["region_code"].isin(CAPITAL_CODES)

    write_csv(housing, DERIVED / "housing_under40_homeownership_sido.csv")
    write_csv(panel, DERIVED / "housing_security_vital_sido_panel.csv")
    write_csv(panel[panel["region_code"].eq("00")], DERIVED / "housing_security_outcomes_national.csv")
    write_csv(
        panel[panel["region_code"].isin(CAPITAL_CODES)].sort_values(["region_code", "year"]),
        DERIVED / "capital_region_housing_marriage_birth.csv",
    )
    write_csv(regression_summary(panel), DERIVED / "housing_security_outcome_regression.csv")
    write_csv(housing_finance_burden_by_age(), DERIVED / "housing_finance_burden_by_age.csv")
    write_csv(housing_tenure_for_young_and_newlywed(), DERIVED / "housing_tenure_young_newlywed.csv")
    write_csv(housing_consumption_pressure(), DERIVED / "youth_housing_consumption_pressure.csv")
    print("Wrote housing-support outcome datasets.")


if __name__ == "__main__":
    main()
