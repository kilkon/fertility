# -*- coding: utf-8 -*-
"""Build a small region-level population and innovation analysis for section 1.3.

The analysis intentionally stays simple. It asks whether larger population
and youth population pools are associated with more patent applications across
Korean provinces in 2024. The design is cross-sectional and descriptive, not
causal.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
KOREA_ROOT = ROOT.parent
if str(KOREA_ROOT) not in sys.path:
    sys.path.insert(0, str(KOREA_ROOT))

from apifunction.kosis import fetch_kosis_dataframe


YEAR = 2024
DATA = ROOT / "data"
SOURCE = DATA / "source"
DERIVED = DATA / "derived"

PATENT_TABLE = "DT_1YL202109E"  # 특허출원건수(시도)
YOUTH_TABLE = "DT_1YL20643"  # 인구총조사 청년인구비율(시도/시/군/구)

REGION_FULL_NAME = {
    "서울": "서울특별시",
    "부산": "부산광역시",
    "대구": "대구광역시",
    "인천": "인천광역시",
    "광주": "광주광역시",
    "대전": "대전광역시",
    "울산": "울산광역시",
    "세종": "세종특별자치시",
    "경기": "경기도",
    "강원": "강원특별자치도",
    "충북": "충청북도",
    "충남": "충청남도",
    "전북": "전북특별자치도",
    "전남": "전라남도",
    "경북": "경상북도",
    "경남": "경상남도",
    "제주": "제주특별자치도",
}


def ols(y: pd.Series | np.ndarray, x: pd.DataFrame | pd.Series | np.ndarray) -> tuple[np.ndarray, float]:
    y_arr = np.asarray(y, dtype=float)
    x_arr = np.asarray(x, dtype=float)
    if x_arr.ndim == 1:
        x_arr = x_arr.reshape(-1, 1)
    design = np.column_stack([np.ones(len(x_arr)), x_arr])
    beta = np.linalg.lstsq(design, y_arr, rcond=None)[0]
    fitted = design @ beta
    ss_res = float(np.sum((y_arr - fitted) ** 2))
    ss_tot = float(np.sum((y_arr - y_arr.mean()) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot else 1.0
    return beta, r2


def one_var_standardized_beta(y: pd.Series, x: pd.Series) -> float:
    return float(np.corrcoef(np.asarray(x, dtype=float), np.asarray(y, dtype=float))[0, 1])


def multiple_standardized_betas(y: pd.Series, x: pd.DataFrame) -> np.ndarray:
    y_arr = np.asarray(y, dtype=float)
    x_arr = np.asarray(x, dtype=float)
    y_z = (y_arr - y_arr.mean()) / y_arr.std(ddof=0)
    x_z = (x_arr - x_arr.mean(axis=0)) / x_arr.std(axis=0, ddof=0)
    beta, _ = ols(y_z, x_z)
    return beta[1:]


def fetch_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    SOURCE.mkdir(parents=True, exist_ok=True)
    patents = fetch_kosis_dataframe(
        PATENT_TABLE,
        org_id="101",
        prd_se="Y",
        start_prd_de=str(YEAR),
        end_prd_de=str(YEAR),
        load_gubun="2",
        itm_id="ALL",
        obj_l1="ALL",
        obj_l2="ALL",
        timeout=120,
    )
    youth = fetch_kosis_dataframe(
        YOUTH_TABLE,
        org_id="101",
        prd_se="Y",
        start_prd_de=str(YEAR),
        end_prd_de=str(YEAR),
        load_gubun="2",
        itm_id="ALL",
        obj_l1="ALL",
        timeout=120,
    )
    patents.to_csv(SOURCE / f"kosis_patent_applications_sido_{YEAR}.csv", index=False, encoding="utf-8-sig")
    youth.to_csv(SOURCE / f"kosis_youth_population_sido_{YEAR}.csv", index=False, encoding="utf-8-sig")
    return patents, youth


def build_dataset(patents: pd.DataFrame, youth: pd.DataFrame) -> pd.DataFrame:
    patent_rows = patents[
        (patents["C2"].astype(str) == "15138AG1AA")
        & (patents["C1_NM"].astype(str) != "계")
    ][["C1_NM", "DT"]].copy()
    patent_rows["region"] = patent_rows["C1_NM"].map(REGION_FULL_NAME)
    patent_rows = patent_rows.rename(columns={"DT": "patent_applications"})[
        ["region", "patent_applications"]
    ]

    province_youth = youth[
        (youth["C1"].astype(str).str.len() == 2)
        & (youth["C1"].astype(str) != "00")
        & (youth["C2"].astype(str).isin(["11", "12", "13"]))
    ][["C1_NM", "C2", "DT"]].copy()
    pivot = province_youth.pivot_table(index="C1_NM", columns="C2", values="DT", aggfunc="first").reset_index()
    pivot = pivot.rename(
        columns={
            "C1_NM": "region",
            "11": "youth_share_19_39",
            "12": "youth_population_19_39",
            "13": "total_population",
        }
    )

    merged = patent_rows.merge(pivot, on="region", how="inner")
    numeric_cols = [
        "patent_applications",
        "total_population",
        "youth_population_19_39",
        "youth_share_19_39",
    ]
    for col in numeric_cols:
        merged[col] = pd.to_numeric(merged[col], errors="coerce")
    merged["patents_per_100k"] = merged["patent_applications"] / merged["total_population"] * 100000
    merged = merged.sort_values("patent_applications", ascending=False)
    return merged


def build_model_summary(df: pd.DataFrame) -> pd.DataFrame:
    y_log_patents = np.log(df["patent_applications"] + 1)
    rows: list[dict[str, object]] = []

    for name, variable, formula in [
        ("규모 모형 A", "total_population", "ln(특허출원+1) = α + β ln(전체인구)"),
        ("규모 모형 B", "youth_population_19_39", "ln(특허출원+1) = α + β ln(19-39세 청년인구)"),
    ]:
        x = np.log(df[variable])
        beta, r2 = ols(y_log_patents, x)
        rows.append(
            {
                "model": name,
                "formula": formula,
                "coefficient": round(float(beta[1]), 3),
                "standardized_beta": round(one_var_standardized_beta(y_log_patents, x), 3),
                "r2": round(r2, 3),
                "n_regions": len(df),
            }
        )

    beta, r2 = ols(df["patents_per_100k"], df["youth_share_19_39"])
    rows.append(
        {
            "model": "집약도 모형",
            "formula": "인구 10만 명당 특허출원 = α + β 청년인구비율",
            "coefficient": round(float(beta[1]), 3),
            "standardized_beta": round(
                one_var_standardized_beta(df["patents_per_100k"], df["youth_share_19_39"]),
                3,
            ),
            "r2": round(r2, 3),
            "n_regions": len(df),
        }
    )

    x_multi = pd.DataFrame(
        {
            "log_total_population": np.log(df["total_population"]),
            "youth_share_19_39": df["youth_share_19_39"],
        }
    )
    beta, r2 = ols(y_log_patents, x_multi)
    std_betas = multiple_standardized_betas(y_log_patents, x_multi)
    rows.extend(
        [
            {
                "model": "복합 모형: 인구",
                "formula": "ln(특허출원+1) = α + β1 ln(전체인구) + β2 청년인구비율",
                "coefficient": round(float(beta[1]), 3),
                "standardized_beta": round(float(std_betas[0]), 3),
                "r2": round(r2, 3),
                "n_regions": len(df),
            },
            {
                "model": "복합 모형: 청년비중",
                "formula": "동일 모형의 β2",
                "coefficient": round(float(beta[2]), 3),
                "standardized_beta": round(float(std_betas[1]), 3),
                "r2": round(r2, 3),
                "n_regions": len(df),
            },
        ]
    )

    without_seoul_gyeonggi = df[~df["region"].isin(["서울특별시", "경기도"])].copy()
    for variable, label in [
        ("total_population", "수도권 핵심 제외: 전체인구"),
        ("youth_population_19_39", "수도권 핵심 제외: 청년인구"),
    ]:
        x = np.log(without_seoul_gyeonggi[variable])
        y = np.log(without_seoul_gyeonggi["patent_applications"] + 1)
        beta, r2 = ols(y, x)
        rows.append(
            {
                "model": label,
                "formula": f"서울·경기 제외, ln(특허출원+1) = α + β ln({variable})",
                "coefficient": round(float(beta[1]), 3),
                "standardized_beta": round(one_var_standardized_beta(y, x), 3),
                "r2": round(r2, 3),
                "n_regions": len(without_seoul_gyeonggi),
            }
        )

    return pd.DataFrame(rows)


def main() -> None:
    DERIVED.mkdir(parents=True, exist_ok=True)
    patents, youth = fetch_inputs()
    dataset = build_dataset(patents, youth)
    summary = build_model_summary(dataset)

    dataset.to_csv(DERIVED / "population_innovation_sido_2024.csv", index=False, encoding="utf-8-sig")
    summary.to_csv(DERIVED / "population_innovation_model_summary_2024.csv", index=False, encoding="utf-8-sig")

    print("Dataset")
    print(dataset.to_string(index=False))
    print("\nModel summary")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
