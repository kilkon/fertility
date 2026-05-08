# -*- coding: utf-8 -*-
"""Fetch public data for the population, low fertility, and aging book.

The notebook that inspired this project used SAS in places, but the durable
part of the workflow is the public-data boundary: KOSIS, ECOS, e-Nara, and
OpenFiscal. This script keeps those calls in one place so the static site can
be rebuilt from official sources when network/API-key access is available.
"""

from __future__ import annotations

import json
import sys
import site
from pathlib import Path

USER_SITE = site.getusersitepackages()
if USER_SITE and USER_SITE not in sys.path:
    sys.path.append(USER_SITE)

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
KOREA_ROOT = ROOT.parent
if str(KOREA_ROOT) not in sys.path:
    sys.path.insert(0, str(KOREA_ROOT))

from apifunction.ecos import fetch_ecos_statistic_search
from apifunction.enara import fetch_enara_table
from apifunction.kosis import fetch_kosis_table, get_kosis_api_key
from apifunction.openfiscal import fetch_openfiscal_service

DATA = ROOT / "data"
KOSIS_URL = "https://kosis.kr/openapi/Param/statisticsParameterData.do"


def write_csv(df: pd.DataFrame, name: str) -> None:
    DATA.mkdir(exist_ok=True)
    df.to_csv(DATA / name, index=False, encoding="utf-8-sig")


def parse_age(value: object) -> int | None:
    text = str(value)
    if text == "계":
        return None
    digits = "".join(ch for ch in text if ch.isdigit())
    return int(digits) if digits else None


def fetch_kosis_population_item(
    *,
    year: int,
    region_code: str = "ALL",
    age_code: str = "ALL",
) -> pd.DataFrame:
    """Fetch DT_1B04006 total-population rows with direct item filtering."""
    params = {
        "method": "getList",
        "apiKey": get_kosis_api_key(),
        "tblId": "DT_1B04006",
        "orgId": "101",
        "startPrdDe": str(year),
        "endPrdDe": str(year),
        "itmId": "T2",
        "format": "json",
        "jsonVD": "Y",
        "prdSe": "Y",
        "loadGubun": "2",
        "objL1": region_code,
        "objL2": age_code,
    }
    resp = requests.get(KOSIS_URL, params=params, timeout=60)
    resp.raise_for_status()
    payload = resp.json()
    if isinstance(payload, dict) and payload.get("err"):
        raise RuntimeError(f"KOSIS error {payload.get('err')}: {payload.get('errMsg')}")
    return pd.DataFrame(payload)


def build_yeonggwang_official_outputs(start_year: int = 2013, end_year: int = 2024) -> dict[str, str]:
    frames = [
        fetch_kosis_population_item(year=year, region_code="46870", age_code="ALL")
        for year in range(start_year, end_year + 1)
    ]
    raw = pd.concat(frames, ignore_index=True)
    raw["DT"] = pd.to_numeric(raw["DT"], errors="coerce")
    raw["age"] = raw["C2_NM"].map(parse_age)
    raw["year"] = pd.to_numeric(raw["PRD_DE"], errors="coerce")
    write_csv(raw, "kosis_yeonggwang_population_age.csv")

    rows: list[dict[str, object]] = []
    for year, group in raw.groupby("year"):
        total = float(group.loc[group["C2_NM"] == "계", "DT"].sum())
        age_rows = group.dropna(subset=["age"]).copy()
        child = float(age_rows.loc[age_rows["age"].between(0, 14), "DT"].sum())
        working = float(age_rows.loc[age_rows["age"].between(15, 64), "DT"].sum())
        older = float(age_rows.loc[age_rows["age"] >= 65, "DT"].sum())
        rows.append(
            {
                "year": int(year),
                "region": "영광군",
                "total_population": int(total),
                "child_population": int(child),
                "working_age_population": int(working),
                "older_population": int(older),
                "child_share": round(child / total * 100, 2),
                "working_age_share": round(working / total * 100, 2),
                "older_share": round(older / total * 100, 2),
                "aging_rate": round(older / total * 100, 2),
                "old_age_dependency_ratio": round(older / working * 100, 2) if working else None,
            }
        )
    structure = pd.DataFrame(rows)
    write_csv(structure, "yeonggwang_population_structure_by_year.csv")
    write_csv(
        structure[
            [
                "year",
                "region",
                "total_population",
                "child_population",
                "working_age_population",
                "older_population",
                "aging_rate",
                "old_age_dependency_ratio",
            ]
        ],
        "yeonggwang_aging_indicators_by_year.csv",
    )

    cohort_rows: list[dict[str, object]] = []
    indexed = raw.dropna(subset=["age"]).set_index(["year", "age"])["DT"]
    for birth_year in range(start_year, end_year - 4 + 1):
        pop0 = indexed.get((birth_year, 0))
        pop4 = indexed.get((birth_year + 4, 4))
        if pd.isna(pop0) or pd.isna(pop4):
            continue
        decrease = float(pop0) - float(pop4)
        cohort_rows.append(
            {
                "birth_year": birth_year,
                "pop_0": int(pop0),
                "pop_4": int(pop4),
                "pop_decrease": int(decrease),
                "decrease_ratio": round(decrease / float(pop0) * 100, 2) if float(pop0) else None,
            }
        )
    write_csv(pd.DataFrame(cohort_rows), "yeonggwang_birth_cohort_summary.csv")

    return {
        "kosis_yeonggwang_population_age": str(DATA / "kosis_yeonggwang_population_age.csv"),
        "yeonggwang_population_structure_by_year": str(DATA / "yeonggwang_population_structure_by_year.csv"),
        "yeonggwang_aging_indicators_by_year": str(DATA / "yeonggwang_aging_indicators_by_year.csv"),
        "yeonggwang_birth_cohort_summary": str(DATA / "yeonggwang_birth_cohort_summary.csv"),
    }


def build_sigungu_aging_map(year: int = 2024) -> dict[str, str]:
    raw = fetch_kosis_population_item(year=year, region_code="ALL", age_code="ALL")
    raw["DT"] = pd.to_numeric(raw["DT"], errors="coerce")
    raw["age"] = raw["C2_NM"].map(parse_age)
    raw = raw[raw["C1"].astype(str).str.len() == 5].copy()
    total = raw[raw["C2_NM"] == "계"][["C1", "C1_NM", "DT"]].rename(columns={"DT": "total_population"})
    older = (
        raw[raw["age"] >= 65]
        .groupby(["C1", "C1_NM"], as_index=False)["DT"]
        .sum()
        .rename(columns={"DT": "older_population"})
    )
    merged = total.merge(older, on=["C1", "C1_NM"], how="left")
    merged["aging_rate"] = (merged["older_population"] / merged["total_population"] * 100).round(2)
    write_csv(merged, f"sigungu_aging_{year}.csv")
    by_code = {
        str(row.C1): float(row.aging_rate)
        for row in merged.itertuples(index=False)
        if pd.notna(row.aging_rate)
    }
    js = (
        "window.populationBookSigunguAging = "
        + json.dumps(
            {
                "title": f"{year}년 시군구 65세 이상 인구 비중",
                "itemName": "65세 이상 인구 비중",
                "unit": "%",
                "prdLabel": str(year),
                "palette": "amber",
                "byCode": by_code,
            },
            ensure_ascii=False,
            indent=2,
        )
        + ";\n"
    )
    (ROOT / "map_data.js").write_text(js, encoding="utf-8")
    return {
        f"sigungu_aging_{year}": str(DATA / f"sigungu_aging_{year}.csv"),
        "map_data_js": str(ROOT / "map_data.js"),
    }


def fetch_kosis_sources() -> dict[str, str]:
    """Fetch the core KOSIS tables referenced by the source notebook."""
    outputs: dict[str, str] = {}
    errors: dict[str, str] = {}
    tables = {
        "registered_population_age": ("DT_1B04006", "A", 2013, 2025),
        "population_midyear_age_sex": ("DT_1B040M1", "A", 2013, 2025),
        "population_projection_indicators": ("DT_1BPB002", "A", 2000, 2072),
        "oecd_fertility": ("DT_2KAA202_OECD", "A", 2000, 2025),
        "elderly_economic_activity": ("DT_1YL202005", "A", 2015, 2025),
    }
    for stem, (tbl_id, cycle, start, end) in tables.items():
        try:
            df = fetch_kosis_table(tbl_id, cycle=cycle, start_year=start, end_year=end)
            filename = f"{stem}.csv"
            write_csv(df, filename)
            outputs[stem] = str(DATA / filename)
        except Exception as exc:  # noqa: BLE001 - manifest should preserve API failures.
            errors[stem] = f"{type(exc).__name__}: {exc}"
    try:
        outputs.update(build_yeonggwang_official_outputs())
    except Exception as exc:  # noqa: BLE001
        errors["yeonggwang_filtered_outputs"] = f"{type(exc).__name__}: {exc}"
    try:
        outputs.update(build_sigungu_aging_map())
    except Exception as exc:  # noqa: BLE001
        errors["sigungu_aging_map"] = f"{type(exc).__name__}: {exc}"
    if errors:
        outputs["_errors"] = json.dumps(errors, ensure_ascii=False)
    return outputs


def fetch_context_sources() -> dict[str, str]:
    """Fetch non-KOSIS context tables used by later chapters."""
    outputs: dict[str, str] = {}
    errors: dict[str, str] = {}

    try:
        ecos = fetch_ecos_statistic_search(
            "200Y101",
            cycle="A",
            start_time="2000",
            end_time="2025",
        )
        write_csv(ecos, "ecos_macro_context.csv")
        outputs["ecos_macro_context"] = str(DATA / "ecos_macro_context.csv")
    except Exception as exc:  # noqa: BLE001
        errors["ecos_macro_context"] = f"{type(exc).__name__}: {exc}"

    try:
        enara = fetch_enara_table(149501, 1495)
        write_csv(enara, "enara_population_policy_indicator.csv")
        outputs["enara_population_policy_indicator"] = str(DATA / "enara_population_policy_indicator.csv")
    except Exception as exc:  # noqa: BLE001
        errors["enara_population_policy_indicator"] = f"{type(exc).__name__}: {exc}"

    try:
        fiscal = fetch_openfiscal_service("OPFI152")
        write_csv(fiscal, "openfiscal_population_budget.csv")
        outputs["openfiscal_population_budget"] = str(DATA / "openfiscal_population_budget.csv")
    except Exception as exc:  # noqa: BLE001
        errors["openfiscal_population_budget"] = f"{type(exc).__name__}: {exc}"

    if errors:
        outputs["_errors"] = json.dumps(errors, ensure_ascii=False)
    return outputs


def main() -> None:
    manifest = {
        "kosis": fetch_kosis_sources(),
        "context": fetch_context_sources(),
    }
    (DATA / "fetch_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
