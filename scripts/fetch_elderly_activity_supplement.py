# -*- coding: utf-8 -*-
"""Fetch and derive elderly economic-activity supplement tables from KOSIS."""

from __future__ import annotations

import site
import sys
import time
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

SUPPLEMENT_TABLES = {
    "DT_1DE8035S": "longest_job_tenure",
    "DT_1DE8036S": "longest_job_exit_age",
    "DT_1DE8037S": "longest_job_exit_reason",
    "DT_1DE8038S": "job_search_experience",
    "DT_1DE8040S": "job_search_channel",
    "DT_1DE8042S": "employment_experience",
    "DT_1DE8044S": "future_work_intention",
    "DT_1DE8046S": "future_job_choice_criteria",
    "DT_1DE8048S": "future_job_type",
    "DT_1DE8050S": "future_desired_wage",
    "DT_1DE8057S": "desired_work_age",
    "DT_1DE8061_11": "industry_distribution",
    "DT_1DE8063_8": "occupation_distribution",
}


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def fetch_monthly_table(table_id: str) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for year in range(START_YEAR, END_YEAR + 1):
        period = f"{year}05"
        try:
            records = fetch_kosis_statistics(
                table_id,
                org_id="101",
                prd_se="M",
                start_prd_de=period,
                end_prd_de=period,
                itm_id="ALL",
                obj_l1="ALL",
                obj_l2="ALL",
                obj_l3="ALL",
                obj_l4="ALL",
                timeout=120,
            )
        except Exception as exc:
            print(f"skip {table_id} {period}: {exc}")
            continue
        frame = kosis_records_to_dataframe(records)
        frame["requested_period"] = period
        frames.append(frame)
        print(f"fetched {table_id} {period}: {len(frame)} rows")
        time.sleep(0.15)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def fetch_employment_status_context() -> pd.DataFrame:
    records = fetch_kosis_statistics(
        "DT_1DA7010S",
        org_id="101",
        prd_se="Y",
        start_prd_de=str(END_YEAR),
        end_prd_de=str(END_YEAR),
        itm_id="ALL",
        obj_l1="ALL",
        timeout=120,
    )
    return kosis_records_to_dataframe(records)


def prepare(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    df["year"] = df["PRD_DE"].astype(str).str[:4].astype(int)
    df["value"] = pd.to_numeric(df["DT"], errors="coerce")
    return df


def sex_filter(df: pd.DataFrame, sex: str = "계") -> pd.DataFrame:
    if "C1_NM" not in df.columns:
        return df.copy()
    if sex in set(df["C1_NM"].dropna().astype(str)):
        return df[df["C1_NM"].astype(str) == sex].copy()
    return df.copy()


def age55_filter(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for column in ["C1_NM", "C2_NM", "C3_NM"]:
        if column in out.columns:
            labels = out[column].dropna().astype(str)
            if any(labels.str.contains("55~79", regex=False)):
                return out[out[column].astype(str).str.contains("55~79", regex=False)].copy()
    return out


def item_value(df: pd.DataFrame, item: str, year: int | None = None) -> float | None:
    g = df.copy()
    if year is not None:
        g = g[g["year"] == year]
    if "ITM_NM" not in g.columns:
        return None
    row = g[g["ITM_NM"].astype(str) == item]
    if row.empty:
        return None
    value = row["value"].dropna()
    return float(value.iloc[0]) if not value.empty else None


def pct(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return round(numerator / denominator * 100, 1)


def build_life_course(raws: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    tenure = age55_filter(sex_filter(prepare(raws["DT_1DE8035S"])))
    exit_age = age55_filter(sex_filter(prepare(raws["DT_1DE8036S"])))
    search = sex_filter(prepare(raws["DT_1DE8038S"]))
    employment_exp = sex_filter(prepare(raws["DT_1DE8042S"]))
    future = sex_filter(prepare(raws["DT_1DE8044S"]))
    desired_age = prepare(raws["DT_1DE8057S"])

    for year in range(START_YEAR, END_YEAR + 1):
        population = item_value(search, "55~79세인구", year) or item_value(future, "55~79세인구", year)
        longest_job_total = item_value(tenure, "전체", year)
        left_main_job = item_value(exit_age, "전체", year)
        avg_tenure_months = item_value(tenure, "평균 근속기간", year)
        avg_exit_age = item_value(exit_age, "평균이직연령", year)
        search_yes = item_value(search, "지난1년간구직경험있음", year)
        employment_yes = item_value(employment_exp, "지난1년간취업경험있음", year)
        future_yes = item_value(future, "장래근로 원함", year)

        desired_rows = desired_age[desired_age["year"] == year]
        desired_rows = desired_rows[desired_rows["ITM_NM"].astype(str).str.contains("평균", regex=False)] if "ITM_NM" in desired_rows.columns else desired_rows
        desired_work_age = None
        for column in ["C1_NM", "C2_NM"]:
            if column in desired_rows.columns:
                candidate = desired_rows[desired_rows[column].astype(str).str.contains("55~79", regex=False)]
                if not candidate.empty:
                    desired_work_age = float(candidate["value"].dropna().iloc[0])
                    break
        if desired_work_age is None and not desired_rows.empty:
            desired_work_age = float(desired_rows["value"].dropna().iloc[0])

        rows.append(
            {
                "year": year,
                "population_55_79_thousand": population,
                "longest_job_total_thousand": longest_job_total,
                "left_main_job_thousand": left_main_job,
                "avg_tenure_years": round(avg_tenure_months / 12, 1) if avg_tenure_months is not None else None,
                "avg_exit_age": avg_exit_age,
                "left_main_job_share_pct": pct(left_main_job, longest_job_total),
                "job_search_experience_thousand": search_yes,
                "job_search_experience_pct": pct(search_yes, population),
                "employment_experience_thousand": employment_yes,
                "employment_experience_pct": pct(employment_yes, population),
                "future_work_hope_thousand": future_yes,
                "future_work_hope_pct": pct(future_yes, population),
                "desired_work_age": desired_work_age,
            }
        )
    return pd.DataFrame(rows)


def build_reason_table(raw: pd.DataFrame, denominator_item: str, table_group: str, latest_year: int = END_YEAR) -> pd.DataFrame:
    df = age55_filter(sex_filter(prepare(raw)))
    df = df[df["year"] == latest_year].copy()
    denominator = item_value(df, denominator_item)
    rows = []
    for _, row in df.iterrows():
        item = str(row.get("ITM_NM", ""))
        if item == denominator_item or "인구" in item or "원하지" in item:
            continue
        value = float(row["value"]) if pd.notna(row["value"]) else None
        rows.append(
            {
                "year": latest_year,
                "group": table_group,
                "category": item,
                "value_thousand": value,
                "share_pct": pct(value, denominator),
                "table_id": row.get("TBL_ID", ""),
                "table_name": row.get("TBL_NM", ""),
            }
        )
    return pd.DataFrame(rows)


def build_job_preferences(raws: dict[str, pd.DataFrame], latest_year: int = END_YEAR) -> pd.DataFrame:
    specs = [
        ("DT_1DE8046S", "일자리 선택기준", "장래근로희망자"),
        ("DT_1DE8048S", "희망 일자리 형태", "장래근로희망자"),
        ("DT_1DE8050S", "희망 임금수준", "장래근로희망자"),
    ]
    rows = []
    for table_id, group_name, denominator_item in specs:
        df = prepare(raws[table_id])
        if "C1_NM" not in df.columns:
            continue
        df = df[df["year"] == latest_year].copy()
        for sex in ["계", "남자", "여자"]:
            g = df[df["C1_NM"].astype(str) == sex].copy()
            if g.empty:
                continue
            denominator = item_value(g, denominator_item)
            for _, row in g.iterrows():
                item = str(row.get("ITM_NM", ""))
                if item == denominator_item:
                    continue
                value = float(row["value"]) if pd.notna(row["value"]) else None
                rows.append(
                    {
                        "year": latest_year,
                        "sex": sex,
                        "group": group_name,
                        "category": item,
                        "value_thousand": value,
                        "share_pct": pct(value, denominator),
                        "table_id": table_id,
                    }
                )
    return pd.DataFrame(rows)


def build_employment_structure(raws: dict[str, pd.DataFrame], latest_year: int = END_YEAR) -> pd.DataFrame:
    specs = [
        ("DT_1DE8061_11", "산업"),
        ("DT_1DE8063_8", "직업"),
    ]
    rows = []
    for table_id, dimension in specs:
        df = prepare(raws[table_id])
        df = df[df["year"] == latest_year].copy()
        if df.empty:
            continue

        category_col = "C1_NM" if "C1_NM" in df.columns else None
        if category_col is None or "ITM_NM" not in df.columns:
            continue

        total_elderly = None
        total_row = df[
            (df[category_col].astype(str) == "계")
            & (df["ITM_NM"].astype(str).str.contains("55~79", regex=False))
        ]
        if not total_row.empty:
            total_elderly = float(total_row["value"].dropna().iloc[0])

        for category in sorted(set(df[category_col].dropna().astype(str))):
            if category == "계":
                continue
            cat = df[df[category_col].astype(str) == category]
            total = cat[cat["ITM_NM"].astype(str) == "전체 취업자"]["value"]
            elderly = cat[cat["ITM_NM"].astype(str).str.contains("55~79", regex=False)]["value"]
            age_55_64 = cat[cat["ITM_NM"].astype(str).str.contains("55~64", regex=False)]["value"]
            age_65_79 = cat[cat["ITM_NM"].astype(str).str.contains("65~79", regex=False)]["value"]
            total_value = float(total.iloc[0]) if not total.empty else None
            elderly_value = float(elderly.iloc[0]) if not elderly.empty else None
            rows.append(
                {
                    "year": latest_year,
                    "dimension": dimension,
                    "category": category,
                    "total_employed_thousand": total_value,
                    "elderly_55_79_thousand": elderly_value,
                    "age_55_64_thousand": float(age_55_64.iloc[0]) if not age_55_64.empty else None,
                    "age_65_79_thousand": float(age_65_79.iloc[0]) if not age_65_79.empty else None,
                    "elderly_share_of_category_pct": pct(elderly_value, total_value),
                    "category_share_of_elderly_pct": pct(elderly_value, total_elderly),
                    "table_id": table_id,
                }
            )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values(["dimension", "category_share_of_elderly_pct"], ascending=[True, False])


def main() -> None:
    raws: dict[str, pd.DataFrame] = {}
    for table_id, slug in SUPPLEMENT_TABLES.items():
        raw_path = DATA / f"elderly_activity_supplement_{table_id}_{slug}.csv"
        if raw_path.exists():
            raw = pd.read_csv(raw_path)
            print(f"reuse {raw_path}: {len(raw)} rows")
        else:
            raw = fetch_monthly_table(table_id)
            write_csv(raw, raw_path)
        raws[table_id] = raw

    context = fetch_employment_status_context()
    write_csv(context, DATA / "employment_status_DT_1DA7010S_2025.csv")

    outputs = {
        "life_course": build_life_course(raws),
        "exit_reasons": build_reason_table(raws["DT_1DE8037S"], "전체", "주된 일자리를 그만둔 이유"),
        "future_work_reasons": build_reason_table(raws["DT_1DE8044S"], "장래근로 원함", "장래근로 희망 이유"),
        "job_preferences": build_job_preferences(raws),
        "employment_structure": build_employment_structure(raws),
    }
    paths = {
        "life_course": DERIVED / "elderly_activity_life_course_indicators.csv",
        "exit_reasons": DERIVED / "elderly_activity_exit_reasons_2025.csv",
        "future_work_reasons": DERIVED / "elderly_activity_future_work_reasons_2025.csv",
        "job_preferences": DERIVED / "elderly_activity_job_preferences_2025.csv",
        "employment_structure": DERIVED / "elderly_employment_structure_2025.csv",
    }
    for key, frame in outputs.items():
        write_csv(frame, paths[key])
        print(f"{key}: {paths[key]} ({len(frame)} rows)")
    print(f"context: {DATA / 'employment_status_DT_1DA7010S_2025.csv'}")


if __name__ == "__main__":
    main()
