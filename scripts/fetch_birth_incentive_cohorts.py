# -*- coding: utf-8 -*-
"""Build 0-to-4 cohort checks for municipalities with active birth incentives."""

from __future__ import annotations

import site
import sys
from pathlib import Path

USER_SITE = site.getusersitepackages()
if USER_SITE and USER_SITE not in sys.path:
    sys.path.append(USER_SITE)

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DERIVED = DATA / "derived"

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from fetch_population_book_data import KOSIS_URL, fetch_kosis_population_item, get_kosis_api_key, parse_age, write_csv


SELECTED_REGIONS = [
    {
        "region_code": "46870",
        "region": "영광군",
        "policy_basis": "2019년 결혼장려금 500만원 및 신생아 양육비 첫째 500만원 이상 확대",
        "policy_source_url": "https://www.newsis.com/view/NISX20190121_0000536348",
    },
    {
        "region_code": "46810",
        "region": "강진군",
        "policy_basis": "2025년 강진군 육아수당과 전남 출생기본수당을 합쳐 0-6세 월 60만원 지원",
        "policy_source_url": "https://www.yna.co.kr/view/AKR20250121099200054",
    },
    {
        "region_code": "46770",
        "region": "고흥군",
        "policy_basis": "출산장려금 첫째-셋째 1,080만원, 넷째 이상 1,440만원과 출생기본수당 운영",
        "policy_source_url": "https://www.fnnews.com/news/202501061517133878",
    },
    {
        "region_code": "46820",
        "region": "해남군",
        "policy_basis": "출생기본수당, 신생아 양육비, 임신·출산 지원을 결합한 생애초기 지원체계 운영",
        "policy_source_url": "https://www.asiae.co.kr/article/2025010713084158881",
    },
    {
        "region_code": "46900",
        "region": "진도군",
        "policy_basis": "2023년부터 첫째·둘째 출산장려금 1,000만원, 셋째 2,000만원으로 상향",
        "policy_source_url": "https://www.fnnews.com/news/202301051127005918",
    },
]


def build_birth_incentive_cohorts(start_year: int = 2013, end_year: int = 2024) -> dict[str, str]:
    """Fetch KOSIS one-year age population and compute birth cohort retention.

    The cohort check uses resident registered population at age 0 in birth year
    and age 4 four years later. It is not a causal estimate by itself; it is a
    consistency check for whether birth support is followed by local retention.
    """

    frames: list[pd.DataFrame] = []
    for region in SELECTED_REGIONS:
        for year in range(start_year, end_year + 1):
            frame = fetch_kosis_population_item(
                year=year,
                region_code=region["region_code"],
                age_code="ALL",
            )
            frame["selected_region"] = region["region"]
            frame["policy_basis"] = region["policy_basis"]
            frame["policy_source_url"] = region["policy_source_url"]
            frames.append(frame)

    raw = pd.concat(frames, ignore_index=True)
    raw["DT"] = pd.to_numeric(raw["DT"], errors="coerce")
    raw["age"] = raw["C2_NM"].map(parse_age)
    raw["year"] = pd.to_numeric(raw["PRD_DE"], errors="coerce").astype("Int64")
    raw = raw.rename(columns={"C1": "region_code", "C1_NM": "region"})
    write_csv(raw, "kosis_birth_incentive_regions_age.csv")

    age_rows = raw.dropna(subset=["age"]).copy()
    age_rows["age"] = age_rows["age"].astype(int)
    indexed = age_rows.set_index(["region_code", "year", "age"])["DT"]
    cohort_rows: list[dict[str, object]] = []
    for region in SELECTED_REGIONS:
        for birth_year in range(start_year, end_year - 4 + 1):
            pop0 = indexed.get((region["region_code"], birth_year, 0))
            pop4 = indexed.get((region["region_code"], birth_year + 4, 4))
            if pd.isna(pop0) or pd.isna(pop4):
                continue
            pop0 = float(pop0)
            pop4 = float(pop4)
            decrease = pop0 - pop4
            cohort_rows.append(
                {
                    "region_code": region["region_code"],
                    "region": region["region"],
                    "policy_basis": region["policy_basis"],
                    "policy_source_url": region["policy_source_url"],
                    "birth_year": birth_year,
                    "age0_year": birth_year,
                    "age4_year": birth_year + 4,
                    "pop_0": int(pop0),
                    "pop_4": int(pop4),
                    "pop_decrease": int(decrease),
                    "retention_rate": round(pop4 / pop0 * 100, 2) if pop0 else None,
                    "decrease_ratio": round(decrease / pop0 * 100, 2) if pop0 else None,
                }
            )

    cohort = pd.DataFrame(cohort_rows).sort_values(["region", "birth_year"])
    DERIVED.mkdir(parents=True, exist_ok=True)
    cohort_path = DERIVED / "birth_incentive_region_cohort_0_to_4.csv"
    cohort.to_csv(cohort_path, index=False, encoding="utf-8-sig")

    summary = (
        cohort.groupby(["region_code", "region", "policy_basis", "policy_source_url"], as_index=False)
        .agg(
            birth_cohorts=("birth_year", "count"),
            avg_pop_0=("pop_0", "mean"),
            avg_pop_4=("pop_4", "mean"),
            avg_retention_rate=("retention_rate", "mean"),
            avg_decrease_ratio=("decrease_ratio", "mean"),
            min_retention_rate=("retention_rate", "min"),
            max_retention_rate=("retention_rate", "max"),
        )
        .round(2)
        .sort_values("avg_retention_rate", ascending=False)
    )
    summary_path = DERIVED / "birth_incentive_region_cohort_summary.csv"
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")

    rate_frames: list[pd.DataFrame] = []
    for year in range(start_year, end_year - 4 + 1):
        params = {
            "method": "getList",
            "apiKey": get_kosis_api_key(),
            "tblId": "DT_1B8000I",
            "orgId": "101",
            "startPrdDe": str(year),
            "endPrdDe": str(year),
            "itmId": "ALL",
            "format": "json",
            "jsonVD": "Y",
            "prdSe": "Y",
            "loadGubun": "2",
            "objL1": "ALL",
        }
        resp = requests.get(KOSIS_URL, params=params, timeout=60)
        resp.raise_for_status()
        payload = resp.json()
        if isinstance(payload, dict) and payload.get("err"):
            raise RuntimeError(f"KOSIS error {payload.get('err')}: {payload.get('errMsg')}")
        rate_frames.append(pd.DataFrame(payload))

    crude_birth = pd.concat(rate_frames, ignore_index=True)
    selected_names = {region["region"] for region in SELECTED_REGIONS}
    crude_birth = crude_birth[crude_birth["C1_NM"].isin(selected_names)].copy()
    crude_birth["DT"] = pd.to_numeric(crude_birth["DT"], errors="coerce")
    crude_birth["year"] = pd.to_numeric(crude_birth["PRD_DE"], errors="coerce").astype("Int64")
    crude_birth = crude_birth.rename(columns={"C1": "vital_region_code", "C1_NM": "region"})
    crude_birth_path = DATA / "kosis_birth_incentive_crude_birth_rate.csv"
    crude_birth.to_csv(crude_birth_path, index=False, encoding="utf-8-sig")

    vital_pivot = (
        crude_birth.pivot_table(
            index=["region", "year", "vital_region_code"],
            columns="ITM_ID",
            values="DT",
            aggfunc="first",
        )
        .reset_index()
        .rename(
            columns={
                "year": "birth_year",
                "T10": "births",
                "T11": "crude_birth_rate",
            }
        )
    )
    vital_pivot["crude_birth_implied_denominator"] = (
        vital_pivot["births"] / vital_pivot["crude_birth_rate"] * 1000
    ).round(0)
    validation = vital_pivot[
        ["region", "birth_year", "vital_region_code", "births", "crude_birth_rate", "crude_birth_implied_denominator"]
    ].sort_values(["region", "birth_year"])
    validation_path = DERIVED / "birth_incentive_region_birth_rate_validation.csv"
    validation.to_csv(validation_path, index=False, encoding="utf-8-sig")

    rate = vital_pivot[["region", "birth_year", "births", "crude_birth_rate", "crude_birth_implied_denominator", "vital_region_code"]]
    panel = cohort.merge(rate, on=["region", "birth_year"], how="left")
    panel = panel[
        [
            "region_code",
            "region",
            "vital_region_code",
            "policy_basis",
            "policy_source_url",
            "birth_year",
            "age4_year",
            "births",
            "crude_birth_rate",
            "crude_birth_implied_denominator",
            "retention_rate",
            "decrease_ratio",
            "pop_0",
            "pop_4",
        ]
    ].sort_values(["region", "birth_year"])
    panel_path = DERIVED / "birth_incentive_region_panel_cbr_retention.csv"
    panel.to_csv(panel_path, index=False, encoding="utf-8-sig")

    return {
        "raw": str(DATA / "kosis_birth_incentive_regions_age.csv"),
        "crude_birth_rate": str(crude_birth_path),
        "birth_rate_validation": str(validation_path),
        "cohort": str(cohort_path),
        "summary": str(summary_path),
        "panel": str(panel_path),
    }


if __name__ == "__main__":
    for key, value in build_birth_incentive_cohorts().items():
        print(f"{key}: {value}")
