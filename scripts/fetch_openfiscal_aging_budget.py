# -*- coding: utf-8 -*-
"""Fetch OpenFiscal detailed budget programs related to aging policy.

Dataset requested by the book section:
- ds: VW_OPFI940
- odtId: 5Y5A50K2L4CW2IRKI2J0F2C8T
- actual Open API service resolved from the portal: TotalExpenditure5
"""

from __future__ import annotations

import json
import math
import re
import site
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

USER_SITE = site.getusersitepackages()
if USER_SITE and USER_SITE not in sys.path:
    sys.path.append(USER_SITE)

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[0]
DATA = ROOT / "data"
DERIVED = DATA / "derived"
if str(REPO) not in sys.path:
    sys.path.append(str(REPO))

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from apifunction.openfiscal import get_openfiscal_api_key


SERVICE_URL = "https://openapi.openfiscaldata.go.kr/TotalExpenditure5"
ODT_ID = "5Y5A50K2L4CW2IRKI2J0F2C8T"
DS_ID = "VW_OPFI940"
START_YEAR = 2007
PAGE_SIZE = 1000
KEYWORD_PATTERN = re.compile(
    r"노인|고령|고령자|어르신|기초연금|기초노령연금|장기요양|치매|경로당|독거노인|노인돌봄|노인맞춤돌봄"
)


def parse_openfiscal_payload(text: str) -> dict[str, Any]:
    payload = json.loads(text)
    if isinstance(payload, str):
        payload = json.loads(payload)
    if not isinstance(payload, dict):
        raise ValueError("OpenFiscal response is not a JSON object")
    return payload


def rows_and_total(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], int]:
    if "RESULT" in payload:
        result = payload["RESULT"]
        code = result.get("CODE")
        if code == "INFO-200":
            return [], 0
        raise RuntimeError(f"OpenFiscal error {code}: {result.get('MESSAGE')}")
    blocks = payload.get("TotalExpenditure5") or []
    if len(blocks) < 2:
        return [], 0
    head = blocks[0].get("head") or []
    total = 0
    for item in head:
        if "list_total_count" in item:
            total = int(item["list_total_count"])
            break
    rows = blocks[1].get("row") or []
    return rows, total


def make_session() -> requests.Session:
    retry = Retry(
        total=4,
        connect=4,
        read=4,
        backoff_factor=0.7,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods={"GET"},
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("https://", adapter)
    session.headers.update(
        {
            "Accept": "application/json,text/plain,*/*",
            "User-Agent": "Mozilla/5.0 OpenFiscal aging budget collector",
        }
    )
    return session


def fetch_year(session: requests.Session, key: str, year: int) -> list[dict[str, Any]]:
    params = {
        "Key": key,
        "Type": "json",
        "pIndex": "1",
        "pSize": str(PAGE_SIZE),
        "FSCL_YY": str(year),
        "ANEXP_INQ_STND_CD": "1",
        "BDG_FND_DIV_CD": "0",
    }
    def request_page(page: int) -> tuple[list[dict[str, Any]], int]:
        params["pIndex"] = str(page)
        last_error: Exception | None = None
        for attempt in range(1, 5):
            try:
                response = session.get(SERVICE_URL, params=params, timeout=60)
                response.raise_for_status()
                return rows_and_total(parse_openfiscal_payload(response.text))
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                time.sleep(1.2 * attempt)
        raise RuntimeError(f"{year} page {page} failed after retries: {last_error}")

    first_rows, total = request_page(1)
    if total <= PAGE_SIZE:
        return first_rows

    rows = list(first_rows)
    for page in range(2, math.ceil(total / PAGE_SIZE) + 1):
        page_rows, _ = request_page(page)
        rows.extend(page_rows)
    return rows


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
    DATA.mkdir(parents=True, exist_ok=True)
    DERIVED.mkdir(parents=True, exist_ok=True)

    key = get_openfiscal_api_key()
    session = make_session()
    current_year = datetime.now().year
    all_rows: list[dict[str, Any]] = []
    for year in range(START_YEAR, current_year + 1):
        rows = fetch_year(session, key, year)
        print(f"{year}: {len(rows):,} rows")
        all_rows.extend(rows)

    raw = pd.DataFrame(all_rows)
    if raw.empty:
        raise RuntimeError("No OpenFiscal rows were downloaded.")

    raw["FSCL_YY"] = pd.to_numeric(raw["FSCL_YY"], errors="coerce").astype("Int64")
    raw["SACTV_NM"] = raw["SACTV_NM"].fillna("").astype(str)
    amount_col = "Y_YY_DFN_MEDI_KCUR_AMT"
    fallback_col = "Y_YY_MEDI_KCUR_AMT"
    raw[amount_col] = pd.to_numeric(raw[amount_col], errors="coerce")
    raw[fallback_col] = pd.to_numeric(raw[fallback_col], errors="coerce")
    raw["budget_amount_thousand_krw"] = raw[amount_col].fillna(raw[fallback_col]).fillna(0)

    matches = raw[raw["SACTV_NM"].str.contains(KEYWORD_PATTERN, na=False)].copy()
    if matches.empty:
        raise RuntimeError("No aging-related programs matched the keyword filter.")

    matches["aging_budget_category"] = matches["SACTV_NM"].map(classify_program)
    matches["program_key"] = (
        matches["OFFC_NM"].fillna("").astype(str)
        + "|"
        + matches["FSCL_NM"].fillna("").astype(str)
        + "|"
        + matches["ACTV_NM"].fillna("").astype(str)
        + "|"
        + matches["SACTV_NM"].fillna("").astype(str)
    )
    matches["budget_amount_trillion_krw"] = matches["budget_amount_thousand_krw"] / 1_000_000_000

    useful_columns = [
        "FSCL_YY",
        "OFFC_NM",
        "FSCL_NM",
        "ACCT_NM",
        "FLD_NM",
        "SECT_NM",
        "PGM_NM",
        "ACTV_NM",
        "SACTV_NM",
        "BZ_CLS_NM",
        "aging_budget_category",
        "budget_amount_thousand_krw",
        "budget_amount_trillion_krw",
        "Y_PREY_FIRST_KCUR_AMT",
        "Y_PREY_FNL_FRC_AMT",
        "Y_YY_MEDI_KCUR_AMT",
        "Y_YY_DFN_MEDI_KCUR_AMT",
    ]
    matches[useful_columns].to_csv(
        DATA / "openfiscal_VW_OPFI940_aging_budget_matches.csv",
        index=False,
        encoding="utf-8-sig",
    )

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

    print(f"matched rows: {len(matches):,}")
    print(f"latest year: {latest_year}")
    print(trend.tail(3).to_string(index=False))
    print(f"source ds={DS_ID}, odtId={ODT_ID}, service=TotalExpenditure5")


if __name__ == "__main__":
    main()
