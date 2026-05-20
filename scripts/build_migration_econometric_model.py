# -*- coding: utf-8 -*-
"""Build an exploratory province-year econometric model for migration.

The model is descriptive rather than causal. It combines KOSIS provincial
indicators with the book's derived internal-migration and housing panels.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
KOREA_ROOT = ROOT.parent
if str(KOREA_ROOT) not in sys.path:
    sys.path.insert(0, str(KOREA_ROOT))

from apifunction.kosis import fetch_kosis_dataframe


START_YEAR = 2015
END_YEAR = 2024
DATA = ROOT / "data"
SOURCE = DATA / "source"
DERIVED = DATA / "derived"

YOUTH_POP_TABLE = "DT_1YL20643"
YOUTH_EMP_TABLE = "INH_1DA7015S"
GRDP_PC_TABLE = "INH_1C96_02"
BUSINESS_DENSITY_TABLE = "DT_1YL20842"

OLD_TO_CURRENT_SIDO = {
    "11": "11",
    "21": "26",
    "22": "27",
    "23": "28",
    "24": "29",
    "25": "30",
    "26": "31",
    "29": "36",
    "31": "41",
    "32": "51",
    "33": "43",
    "34": "44",
    "35": "52",
    "36": "46",
    "37": "47",
    "38": "48",
    "39": "50",
}


def numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str).str.replace(",", "", regex=False).str.strip(),
        errors="coerce",
    )


def fetch_table(table_id: str) -> pd.DataFrame:
    return fetch_kosis_dataframe(
        table_id,
        org_id="101",
        prd_se="Y",
        start_prd_de=str(START_YEAR),
        end_prd_de=str(END_YEAR),
        load_gubun="2",
        itm_id="ALL",
        obj_l1="ALL",
        obj_l2="ALL",
        obj_l3="ALL",
        timeout=120,
    )


def fetch_inputs() -> dict[str, pd.DataFrame]:
    SOURCE.mkdir(parents=True, exist_ok=True)
    tables = {
        "youth_population": fetch_table(YOUTH_POP_TABLE),
        "youth_employment": fetch_table(YOUTH_EMP_TABLE),
        "grdp_per_capita": fetch_table(GRDP_PC_TABLE),
        "business_density": fetch_table(BUSINESS_DENSITY_TABLE),
    }
    for name, df in tables.items():
        df.to_csv(
            SOURCE / f"kosis_{name}_sido_{START_YEAR}_{END_YEAR}.csv",
            index=False,
            encoding="utf-8-sig",
        )
    return tables


def normalize_sido_code(raw_code: object) -> str:
    code = str(raw_code).strip().zfill(2)
    return OLD_TO_CURRENT_SIDO.get(code, code)


def build_youth_population(df: pd.DataFrame) -> pd.DataFrame:
    rows = df[
        (df["C1"].astype(str).str.fullmatch(r"\d{2}"))
        & (df["C1"].astype(str) != "00")
        & (df["C2"].astype(str).isin(["11", "12", "13"]))
    ][["PRD_DE", "C1", "C1_NM", "C2", "DT"]].copy()
    rows["year"] = numeric(rows["PRD_DE"]).astype("Int64")
    rows["C1"] = rows["C1"].map(normalize_sido_code)
    rows["value"] = numeric(rows["DT"])
    wide = (
        rows.pivot_table(index=["year", "C1", "C1_NM"], columns="C2", values="value", aggfunc="first")
        .reset_index()
        .rename(
            columns={
                "C1_NM": "region_kosis",
                "11": "youth_share_19_39",
                "12": "youth_population_19_39",
                "13": "total_population",
            }
        )
    )
    return wide[["year", "C1", "region_kosis", "youth_share_19_39", "youth_population_19_39", "total_population"]]


def build_youth_employment(df: pd.DataFrame) -> pd.DataFrame:
    rows = df[
        (df["C1"].astype(str).str.fullmatch(r"\d{2}"))
        & (df["C1"].astype(str) != "00")
        & (df["C2"].astype(str) == "75")
    ][["PRD_DE", "C1", "DT"]].copy()
    rows["year"] = numeric(rows["PRD_DE"]).astype("Int64")
    rows["C1"] = rows["C1"].map(normalize_sido_code)
    rows["youth_employment_rate_15_29"] = numeric(rows["DT"])
    return rows[["year", "C1", "youth_employment_rate_15_29"]]


def build_grdp_per_capita(df: pd.DataFrame) -> pd.DataFrame:
    rows = df[
        (df["C1"].astype(str).str.fullmatch(r"\d{2}"))
        & (df["C1"].astype(str) != "00")
    ][["PRD_DE", "C1", "DT"]].copy()
    rows["year"] = numeric(rows["PRD_DE"]).astype("Int64")
    rows["C1"] = rows["C1"].map(normalize_sido_code)
    rows["grdp_per_capita_thousand_won"] = numeric(rows["DT"])
    return rows[["year", "C1", "grdp_per_capita_thousand_won"]]


def build_business_density(df: pd.DataFrame) -> pd.DataFrame:
    rows = df[
        (df["C1"].astype(str).str.fullmatch(r"\d{2}"))
        & (df["C1"].astype(str) != "00")
        & (df["ITM_ID"].astype(str) == "T10")
    ][["PRD_DE", "C1", "DT"]].copy()
    rows["year"] = numeric(rows["PRD_DE"]).astype("Int64")
    rows["C1"] = rows["C1"].map(normalize_sido_code)
    rows["businesses_per_1000_people"] = numeric(rows["DT"])
    return rows[["year", "C1", "businesses_per_1000_people"]]


def build_migration_outcome() -> pd.DataFrame:
    migration = pd.read_csv(DERIVED / "sido_net_migration_age_by_year.csv", dtype={"C1": str})
    total = pd.read_csv(DERIVED / "sido_net_migration_total.csv", dtype={"C1": str})
    youth_bands = ["20-24세", "25-29세", "30-34세"]
    youth = (
        migration[migration["age_band"].isin(youth_bands)]
        .groupby(["year", "C1", "region"], as_index=False)["net_migration"]
        .sum()
        .rename(columns={"net_migration": "youth_net_migration_20_34"})
    )
    total = total[["year", "C1", "net_migration"]].rename(columns={"net_migration": "total_net_migration"})
    return youth.merge(total, on=["year", "C1"], how="left")


def build_housing_panel() -> pd.DataFrame:
    housing = pd.read_csv(DERIVED / "housing_security_vital_sido_panel.csv", dtype={"region_code": str})
    housing = housing.rename(columns={"region_code": "C1"})
    housing["C1"] = housing["C1"].map(normalize_sido_code)
    housing["capital_area"] = housing["C1"].isin(["11", "28", "41"])
    return housing[
        [
            "year",
            "C1",
            "under40_homeownership_rate",
            "under40_nonowner_rate",
            "capital_area",
        ]
    ]


def ols_fit(df: pd.DataFrame, y_col: str, x_cols: list[str], fixed_effect_cols: list[str]) -> dict[str, object]:
    work = df[[y_col] + x_cols + fixed_effect_cols].dropna().copy()
    y = work[y_col].to_numpy(dtype=float)
    parts = [pd.Series(1.0, index=work.index, name="const")]
    for col in x_cols:
        parts.append(work[col].astype(float))
    for fe in fixed_effect_cols:
        dummies = pd.get_dummies(work[fe].astype(str), prefix=fe, drop_first=True, dtype=float)
        parts.append(dummies)
    x = pd.concat(parts, axis=1)
    x_arr = x.to_numpy(dtype=float)
    beta = np.linalg.lstsq(x_arr, y, rcond=None)[0]
    fitted = x_arr @ beta
    residual = y - fitted
    n = len(y)
    k = x_arr.shape[1]
    ss_res = float(np.sum(residual**2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot else 1.0
    dof = max(n - k, 1)
    sigma2 = ss_res / dof
    xtx_inv = np.linalg.pinv(x_arr.T @ x_arr)
    se = np.sqrt(np.diag(xtx_inv) * sigma2)
    names = list(x.columns)
    return {
        "n": n,
        "k": k,
        "r2": r2,
        "names": names,
        "beta": beta,
        "se": se,
        "residual": residual,
        "fitted": fitted,
        "index": work.index,
    }


def standardized_fit(df: pd.DataFrame, y_col: str, x_cols: list[str], fixed_effect_cols: list[str]) -> dict[str, object]:
    work = df[[y_col] + x_cols + fixed_effect_cols].dropna().copy()
    z = pd.DataFrame(index=work.index)
    y_std = work[y_col].std(ddof=0)
    z[y_col] = (work[y_col] - work[y_col].mean()) / y_std
    for col in x_cols:
        x_std = work[col].std(ddof=0)
        z[col] = (work[col] - work[col].mean()) / x_std if x_std else 0.0
    for fe in fixed_effect_cols:
        z[fe] = work[fe]
    return ols_fit(z, y_col, x_cols, fixed_effect_cols)


def p_value_from_t(t_stat: float) -> float:
    # Normal approximation is sufficient for a compact descriptive table.
    return math.erfc(abs(t_stat) / math.sqrt(2))


def build_model_outputs(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    variables = [
        "youth_employment_rate_15_29",
        "log_grdp_per_capita",
        "businesses_per_1000_people",
        "under40_homeownership_rate",
        "capital_area_numeric",
    ]
    labels = {
        "youth_employment_rate_15_29": "청년고용률",
        "log_grdp_per_capita": "1인당 GRDP(로그)",
        "businesses_per_1000_people": "사업체 밀도",
        "under40_homeownership_rate": "40세 미만 주택소유율",
        "capital_area_numeric": "수도권 더미",
    }
    model_panel = panel[panel["year"].between(2020, END_YEAR)].copy()
    pooled = ols_fit(model_panel, "youth_net_migration_rate_per_1000", variables, ["year"])
    pooled_std = standardized_fit(model_panel, "youth_net_migration_rate_per_1000", variables, ["year"])

    fe_variables = variables[:-1]
    fixed_effect = ols_fit(model_panel, "youth_net_migration_rate_per_1000", fe_variables, ["C1", "year"])
    fixed_std = standardized_fit(model_panel, "youth_net_migration_rate_per_1000", fe_variables, ["C1", "year"])

    rows = []
    for model_name, fit, std_fit, model_note in [
        ("시도-연도 패널 OLS", pooled, pooled_std, "연도 고정효과 포함, 수도권 더미 포함"),
        ("지역·연도 고정효과", fixed_effect, fixed_std, "지역 고정효과와 연도 고정효과 포함, 수도권 더미 제외"),
    ]:
        for var in (variables if model_name == "시도-연도 패널 OLS" else fe_variables):
            idx = fit["names"].index(var)
            std_idx = std_fit["names"].index(var)
            coefficient = float(fit["beta"][idx])
            se = float(fit["se"][idx])
            t_stat = coefficient / se if se else np.nan
            rows.append(
                {
                    "model": model_name,
                    "variable": var,
                    "variable_label": labels[var],
                    "coefficient": round(coefficient, 4),
                    "standard_error": round(se, 4),
                    "t_stat": round(float(t_stat), 3) if np.isfinite(t_stat) else np.nan,
                    "p_value_normal_approx": round(p_value_from_t(float(t_stat)), 4) if np.isfinite(t_stat) else np.nan,
                    "standardized_beta": round(float(std_fit["beta"][std_idx]), 3),
                    "r2": round(float(fit["r2"]), 3),
                    "n": int(fit["n"]),
                    "model_note": model_note,
                }
            )
    coef = pd.DataFrame(rows)

    prediction = model_panel.dropna(subset=variables + ["youth_net_migration_rate_per_1000"]).copy()
    pred_fit = ols_fit(prediction, "youth_net_migration_rate_per_1000", variables, ["year"])
    prediction["predicted_youth_net_migration_rate"] = pred_fit["fitted"]
    prediction = prediction[
        [
            "year",
            "C1",
            "region",
            "youth_net_migration_rate_per_1000",
            "predicted_youth_net_migration_rate",
            "youth_net_migration_20_34",
            "youth_population_19_39",
            "youth_employment_rate_15_29",
            "grdp_per_capita_thousand_won",
            "businesses_per_1000_people",
            "under40_homeownership_rate",
            "capital_area",
        ]
    ]
    return coef, prediction


def main() -> None:
    DERIVED.mkdir(parents=True, exist_ok=True)
    tables = fetch_inputs()
    youth_population = build_youth_population(tables["youth_population"])
    youth_employment = build_youth_employment(tables["youth_employment"])
    grdp = build_grdp_per_capita(tables["grdp_per_capita"])
    business = build_business_density(tables["business_density"])
    migration = build_migration_outcome()
    housing = build_housing_panel()

    panel = (
        migration.merge(youth_population, on=["year", "C1"], how="left")
        .merge(youth_employment, on=["year", "C1"], how="left")
        .merge(grdp, on=["year", "C1"], how="left")
        .merge(business, on=["year", "C1"], how="left")
        .merge(housing, on=["year", "C1"], how="left")
    )
    panel = panel[panel["year"].between(START_YEAR, END_YEAR)].copy()
    panel["region"] = panel["region"].fillna(panel["region_kosis"])
    panel["youth_net_migration_rate_per_1000"] = (
        panel["youth_net_migration_20_34"] / panel["youth_population_19_39"] * 1000
    )
    panel["total_net_migration_rate_per_1000"] = panel["total_net_migration"] / panel["total_population"] * 1000
    panel["log_grdp_per_capita"] = np.log(panel["grdp_per_capita_thousand_won"])
    panel["capital_area_numeric"] = panel["capital_area"].astype(str).str.lower().isin(["true", "1"]).astype(int)
    panel = panel.sort_values(["C1", "year"])

    coef, prediction = build_model_outputs(panel)
    panel.to_csv(DERIVED / "migration_model_panel_2015_2024.csv", index=False, encoding="utf-8-sig")
    coef.to_csv(DERIVED / "migration_model_coefficients.csv", index=False, encoding="utf-8-sig")
    prediction.to_csv(DERIVED / "migration_model_predictions.csv", index=False, encoding="utf-8-sig")

    print("migration_model_panel_2015_2024.csv", len(panel))
    print(coef.to_string(index=False))


if __name__ == "__main__":
    main()
