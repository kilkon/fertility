# -*- coding: utf-8 -*-
"""Build exploratory econometric datasets for section 6.11."""

from __future__ import annotations

from pathlib import Path
import site
import sys

USER_SITE = site.getusersitepackages()
if USER_SITE and USER_SITE not in sys.path:
    sys.path.append(USER_SITE)

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DERIVED = ROOT / "data" / "derived"


def write_csv(df: pd.DataFrame, filename: str) -> None:
    DERIVED.mkdir(parents=True, exist_ok=True)
    df.to_csv(DERIVED / filename, index=False, encoding="utf-8-sig")


def ols(y: np.ndarray, x: np.ndarray) -> dict[str, object]:
    y = np.asarray(y, dtype=float)
    x = np.asarray(x, dtype=float)
    valid = np.isfinite(y) & np.all(np.isfinite(x), axis=1)
    y = y[valid]
    x = x[valid]
    n, k = x.shape
    beta = np.linalg.lstsq(x, y, rcond=None)[0]
    resid = y - x @ beta
    sse = float(np.sum(resid**2))
    tss = float(np.sum((y - y.mean()) ** 2))
    r2 = 1 - sse / tss if tss else np.nan
    dof = max(n - k, 1)
    sigma2 = sse / dof
    xtx_inv = np.linalg.pinv(x.T @ x)
    se = np.sqrt(np.diag(xtx_inv * sigma2))
    return {"beta": beta, "se": se, "r2": r2, "n": n, "resid": resid, "valid": valid}


def zscore(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce")
    sd = s.std(ddof=0)
    if not np.isfinite(sd) or sd == 0:
        return s * np.nan
    return (s - s.mean()) / sd


def build_national_change_models() -> tuple[pd.DataFrame, pd.DataFrame]:
    fertility = pd.read_csv(DERIVED / "fertility_age_pattern.csv")
    fertility = fertility[["year", "total_fertility_rate", "asfr_25_29", "asfr_30_34", "asfr_35_39", "asfr_40_44"]]

    family = pd.read_csv(DERIVED / "family_condition_dashboard.csv")
    private_edu = pd.read_csv(DERIVED / "private_education_cost_trend.csv")
    housing = pd.read_csv(DERIVED / "youth_housing_consumption_pressure.csv")
    employment = pd.read_csv(DERIVED / "youth_employment_context.csv")
    income = pd.read_csv(DERIVED / "young_income_trend_by_age.csv")
    income = income[income["age_group"] == "30~39세"][["year", "real_disposable_income_2025_million_krw"]]
    life = pd.read_csv(DERIVED / "young_life_satisfaction_trend.csv")
    life = life[life["age_group"] == "30~39세"][["year", "life_satisfaction_avg_0_10"]]

    df = fertility.merge(
        family[["year", "crude_marriage_rate", "under40_homeownership_rate", "youth_employed_population_2000_100", "newlywed_no_child_pct"]],
        on="year",
        how="left",
    )
    df = df.merge(private_edu[["year", "monthly_private_education_10k_krw"]], on="year", how="left")
    df = df.merge(housing[["year", "housing_share_pct"]], on="year", how="left")
    df = df.merge(employment[["year", "employed_population_index"]], on="year", how="left")
    df = df.merge(income, on="year", how="left")
    df = df.merge(life, on="year", how="left")

    df = df.sort_values("year")
    df["dlog_tfr"] = np.log(df["total_fertility_rate"]).diff()
    candidates = [
        ("혼인율 변화", "crude_marriage_rate", "McDonald/Doepke 계열: 가족형성·일가정 양립"),
        ("40세 미만 주택보유율 변화", "under40_homeownership_rate", "주거비·공간 불평등 모형"),
        ("청년 취업자 지수 변화", "youth_employed_population_2000_100", "경제적 불안정성 모형"),
        ("30대 실질 처분가능소득 변화", "real_disposable_income_2025_million_krw", "소득·기회비용 모형"),
        ("주거비 비중 변화", "housing_share_pct", "주거비 부담 모형"),
        ("사교육비 변화", "monthly_private_education_10k_krw", "Becker-Lewis/Kim-Tertilt-Yum: 수량-질·지위경쟁"),
        ("30대 삶의 만족도 변화", "life_satisfaction_avg_0_10", "생애전망·삶의 질 모형"),
        ("신혼부부 무자녀 비율 변화", "newlywed_no_child_pct", "혼인 이후 출산 이행 모형"),
    ]

    rows = []
    model_rows = []
    for label, col, paper in candidates:
        sub = df[["year", "dlog_tfr", col]].dropna().copy()
        sub[f"d_{col}"] = sub[col].diff()
        sub = sub.dropna()
        if len(sub) < 5:
            continue
        y = zscore(sub["dlog_tfr"]).to_numpy()
        xvar = zscore(sub[f"d_{col}"]).to_numpy()
        x = np.column_stack([np.ones(len(sub)), xvar])
        fit = ols(y, x)
        beta = float(fit["beta"][1])
        se = float(fit["se"][1])
        rows.append(
            {
                "level": "전국 시계열 변화율",
                "channel": label,
                "variable": col,
                "std_beta": round(beta, 3),
                "std_se": round(se, 3),
                "n": int(fit["n"]),
                "r2": round(float(fit["r2"]), 3),
                "paper_family": paper,
                "interpretation": "양(+)이면 해당 변수 증가와 합계출산율 증가가 같은 방향, 음(-)이면 반대 방향",
            }
        )
        model_rows.append(
            {
                "model": f"전국 변화율: {label}",
                "equation": f"z(Δlog TFR_t) = α + β z(Δ{col}_t) + ε_t",
                "sample": f"{int(sub['year'].min())}-{int(sub['year'].max())}",
                "n": int(fit["n"]),
                "r2": round(float(fit["r2"]), 3),
                "key_coefficient": round(beta, 3),
                "source_model": paper,
                "caution": "전국 시계열의 표본이 작아 인과 추정이 아니라 방향성 점검으로 해석",
            }
        )

    age = fertility.dropna(subset=["asfr_25_29", "asfr_30_34", "asfr_35_39", "asfr_40_44"]).copy()
    start = age[age["year"] == 2000].iloc[0]
    end = age[age["year"] == 2024].iloc[0]
    age_rows = []
    for col, label in [
        ("asfr_25_29", "25-29세"),
        ("asfr_30_34", "30-34세"),
        ("asfr_35_39", "35-39세"),
        ("asfr_40_44", "40-44세"),
    ]:
        contribution = (float(end[col]) - float(start[col])) * 5 / 1000
        age_rows.append(
            {
                "age_group": label,
                "asfr_2000": float(start[col]),
                "asfr_2024": float(end[col]),
                "asfr_change": round(float(end[col]) - float(start[col]), 3),
                "tfr_contribution_change": round(contribution, 3),
            }
        )
    age_df = pd.DataFrame(age_rows)
    write_csv(age_df, "fertility_driver_age_contribution.csv")
    return pd.DataFrame(rows), pd.DataFrame(model_rows)


def build_panel_models() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    panel = pd.read_csv(DERIVED / "housing_security_vital_sido_panel.csv")
    panel = panel[(panel["region"] != "전국") & panel["crude_birth_rate"].notna()].copy()
    panel["capital_area"] = panel["capital_area"].astype(str).str.lower().isin(["true", "1"])

    specs = [
        ("시도 패널: 혼인율", ["crude_marriage_rate"], "가족형성 경로"),
        ("시도 패널: 주택보유율", ["under40_homeownership_rate"], "주거 안정 경로"),
        ("시도 패널: 혼인율+주택보유율", ["crude_marriage_rate", "under40_homeownership_rate"], "근접요인과 구조요인의 결합"),
    ]

    coef_rows = []
    model_rows = []
    fit_rows = []
    for model_name, variables, family in specs:
        sub = panel[["year", "region", "crude_birth_rate"] + variables].dropna().copy()
        y = zscore(sub["crude_birth_rate"])
        x_parts = [pd.Series(1.0, index=sub.index, name="const")]
        for var in variables:
            x_parts.append(zscore(sub[var]).rename(var))
        dummies = pd.get_dummies(sub["region"], prefix="region", drop_first=True, dtype=float)
        xdf = pd.concat(x_parts + [dummies], axis=1)
        fit = ols(y.to_numpy(), xdf.to_numpy())
        pred = xdf.to_numpy() @ fit["beta"]
        if model_name.endswith("혼인율+주택보유율"):
            tmp = sub[["year", "region", "crude_birth_rate"]].copy()
            tmp["predicted_std_cbr"] = pred
            yearly = tmp.groupby("year", as_index=False).agg(
                actual_cbr=("crude_birth_rate", "mean"),
                predicted_std_cbr=("predicted_std_cbr", "mean"),
            )
            for row in yearly.to_dict("records"):
                fit_rows.append(row)
        for idx, var in enumerate(variables, start=1):
            beta = float(fit["beta"][idx])
            se = float(fit["se"][idx])
            coef_rows.append(
                {
                    "level": "시도 패널(지역 고정효과)",
                    "channel": {"crude_marriage_rate": "혼인율", "under40_homeownership_rate": "40세 미만 주택보유율"}[var],
                    "variable": var,
                    "std_beta": round(beta, 3),
                    "std_se": round(se, 3),
                    "n": int(fit["n"]),
                    "r2": round(float(fit["r2"]), 3),
                    "paper_family": family,
                    "interpretation": "지역 고정효과를 둔 뒤 시도 내 변화가 조출생률 변화와 같은 방향인지 본 값",
                }
            )
        model_rows.append(
            {
                "model": model_name,
                "equation": "z(CBR_it) = α_i + βX_it + ε_it",
                "sample": f"{int(sub['year'].min())}-{int(sub['year'].max())}, 17개 시도",
                "n": int(fit["n"]),
                "r2": round(float(fit["r2"]), 3),
                "key_coefficient": "; ".join(
                    f"{v}={round(float(fit['beta'][i + 1]), 3)}" for i, v in enumerate(variables)
                ),
                "source_model": family,
                "caution": "종속변수는 합계출산율이 아니라 조출생률이며, 지역 고정효과를 둔 탐색적 패널 모형",
            }
        )

    fit_df = pd.DataFrame(fit_rows)
    if not fit_df.empty:
        fit_df["predicted_std_cbr"] = fit_df["predicted_std_cbr"].round(3)
        write_csv(fit_df, "fertility_driver_panel_fit.csv")
    return pd.DataFrame(coef_rows), pd.DataFrame(model_rows), fit_df


def main() -> None:
    national_coef, national_models = build_national_change_models()
    panel_coef, panel_models, _ = build_panel_models()
    coef = pd.concat([panel_coef, national_coef], ignore_index=True)
    coef = coef.sort_values("std_beta", ascending=False)
    write_csv(coef, "fertility_driver_standardized_effects.csv")
    comparison = pd.concat([panel_models, national_models], ignore_index=True)
    write_csv(comparison, "fertility_driver_model_comparison.csv")
    summary = pd.DataFrame(
        [
            {
                "finding": "measured_proximate_channel",
                "result": "지역 패널에서는 혼인율 변화가 조출생률 변화와 가장 강하게 같은 방향으로 움직인다.",
            },
            {
                "finding": "structural_channel",
                "result": "주거 안정, 교육비, 청년고용, 소득은 출산율과 직접 연결되기보다 혼인과 출산 이행을 매개로 작동할 가능성이 크다.",
            },
            {
                "finding": "interpretation",
                "result": "가장 근본적인 원인은 단일 변수가 아니라 생애 이행의 병목이다. 계량모형은 혼인·주거·교육·노동 조건이 어느 경로에서 막히는지 확인하는 도구다.",
            },
        ]
    )
    write_csv(summary, "fertility_driver_summary.csv")
    print("Built fertility driver model datasets.")


if __name__ == "__main__":
    main()
