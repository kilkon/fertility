# -*- coding: utf-8 -*-
"""Build age-group population trend datasets for chapter 2.

The chapter asks whether population growth is welfare-pressure growth
(65+) or economic-base growth (15-64). This script fetches KOSIS
DT_1B04006, aggregates 1-year age rows into those two groups, and
estimates a simple region-by-region time trend.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
KOREA_ROOT = ROOT.parent
if str(KOREA_ROOT) not in sys.path:
    sys.path.insert(0, str(KOREA_ROOT))

from apifunction.api_keys import resolve_api_key


START_YEAR = 2004
END_YEAR = 2024
MIN_OBSERVATIONS = 10

DATA = ROOT / "data"
DERIVED = DATA / "derived"
TOPO = DATA / "geo" / "skorea-municipalities-2018-topo-simple.json"
KOSIS_URL = "https://kosis.kr/openapi/Param/statisticsParameterData.do"

TOPO_PREFIX_TO_KOSIS_PREFIX = {
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


def parse_age(value: object) -> int | None:
    text = str(value)
    if text == "계":
        return None
    digits = "".join(ch for ch in text if ch.isdigit())
    return int(digits) if digits else None


def get_kosis_api_key() -> str:
    key = resolve_api_key(key_name="KOSIS", default_filename="kosis_api_key.txt")
    if not key:
        raise RuntimeError("KOSIS API key not found.")
    return key.strip().strip('"').strip("'")


def fetch_kosis_population_item(*, year: int, region_code: str = "ALL", age_code: str = "ALL") -> pd.DataFrame:
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
    url = f"{KOSIS_URL}?{urlencode(params)}"
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json,text/plain,*/*",
        },
    )
    try:
        with urlopen(request, timeout=90) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"KOSIS request failed for {year}: {exc}") from exc
    if isinstance(payload, dict) and payload.get("err"):
        raise RuntimeError(f"KOSIS error {payload.get('err')}: {payload.get('errMsg')}")
    return pd.DataFrame(payload)


def regression_slope(group: pd.DataFrame, value_col: str) -> pd.Series:
    g = group.sort_values("year").dropna(subset=[value_col])
    n = len(g)
    if n < MIN_OBSERVATIONS:
        return pd.Series(dtype="object")
    x = g["year"].astype(float)
    y = g[value_col].astype(float)
    x_centered = x - x.mean()
    y_centered = y - y.mean()
    denom = float((x_centered**2).sum())
    if denom == 0:
        return pd.Series(dtype="object")
    slope = float((x_centered * y_centered).sum() / denom)
    intercept = float(y.mean() - slope * x.mean())
    fitted = intercept + slope * x
    ss_res = float(((y - fitted) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - ss_res / ss_tot if ss_tot else 1.0
    first = g.iloc[0]
    last = g.iloc[-1]
    start_value = float(first[value_col])
    end_value = float(last[value_col])
    return pd.Series(
        {
            "C1_NM": last["C1_NM"],
            "C1_NM_ENG": last.get("C1_NM_ENG", ""),
            "n_years": n,
            "start_year": int(first["year"]),
            "end_year": int(last["year"]),
            "start_population": int(round(start_value)),
            "end_population": int(round(end_value)),
            "absolute_change": int(round(end_value - start_value)),
            "change_pct": round((end_value / start_value - 1) * 100, 2) if start_value else pd.NA,
            "slope_people_per_year": round(slope, 1),
            "slope_per_10k_people": round(slope / 10_000, 3),
            "r2": round(r2, 3),
        }
    )


def classify_trend(value: float) -> str:
    if value < -5000:
        return "급격한 감소"
    if value < -1000:
        return "감소"
    if value < 0:
        return "완만한 감소"
    if value < 1000:
        return "완만한 증가"
    if value < 5000:
        return "증가"
    return "급격한 증가"


def fetch_age_group_population() -> pd.DataFrame:
    DATA.mkdir(parents=True, exist_ok=True)
    DERIVED.mkdir(parents=True, exist_ok=True)
    rows: list[pd.DataFrame] = []
    failures: list[str] = []
    for year in range(START_YEAR, END_YEAR + 1):
        try:
            raw = fetch_kosis_population_item(year=year, region_code="ALL", age_code="ALL")
        except Exception as exc:  # noqa: BLE001 - preserve partial data when early years are unavailable.
            failures.append(f"{year}: {type(exc).__name__}: {exc}")
            continue
        raw["year"] = pd.to_numeric(raw["PRD_DE"], errors="coerce")
        raw["population"] = pd.to_numeric(raw["DT"], errors="coerce")
        raw["age"] = raw["C2_NM"].map(parse_age)
        raw["C1"] = raw["C1"].astype(str).str.zfill(5)
        sigungu = raw[(raw["C1"].str.len() == 5) & (~raw["C1"].str.startswith("000")) & raw["year"].eq(year)].copy()
        total = sigungu[sigungu["C2_NM"].eq("계")][["year", "C1", "C1_NM", "C1_NM_ENG", "population"]].rename(
            columns={"population": "total_population"}
        )
        age_rows = sigungu.dropna(subset=["age"]).copy()
        grouped = (
            age_rows.assign(
                working_age_population=age_rows["population"].where(age_rows["age"].between(15, 64), 0),
                older_population=age_rows["population"].where(age_rows["age"].ge(65), 0),
                child_population=age_rows["population"].where(age_rows["age"].between(0, 14), 0),
            )
            .groupby(["year", "C1", "C1_NM", "C1_NM_ENG"], as_index=False)[
                ["child_population", "working_age_population", "older_population"]
            ]
            .sum()
        )
        merged = total.merge(grouped, on=["year", "C1", "C1_NM", "C1_NM_ENG"], how="left")
        rows.append(merged)
        print(f"fetched {year}: {len(merged):,} sigungu rows")
    if not rows:
        raise RuntimeError("No KOSIS age-group population rows were fetched.")
    panel = pd.concat(rows, ignore_index=True)
    panel["year"] = panel["year"].astype(int)
    for col in ["total_population", "child_population", "working_age_population", "older_population"]:
        panel[col] = pd.to_numeric(panel[col], errors="coerce").fillna(0).round().astype(int)
    panel["older_share"] = (panel["older_population"] / panel["total_population"] * 100).round(2)
    panel["working_age_share"] = (panel["working_age_population"] / panel["total_population"] * 100).round(2)
    panel["child_share"] = (panel["child_population"] / panel["total_population"] * 100).round(2)
    panel = panel.sort_values(["C1", "year"])
    panel.to_csv(DERIVED / "sigungu_age_group_population_panel.csv", index=False, encoding="utf-8-sig")
    if failures:
        (DERIVED / "sigungu_age_group_population_fetch_failures.txt").write_text("\n".join(failures), encoding="utf-8")
    return panel


def build_slopes(panel: pd.DataFrame) -> dict[str, pd.DataFrame]:
    outputs: dict[str, pd.DataFrame] = {}
    groups = {
        "total": "total_population",
        "working_age": "working_age_population",
        "older": "older_population",
    }
    for label, value_col in groups.items():
        slope_rows = []
        for code, group in panel.groupby("C1"):
            row = regression_slope(group, value_col)
            if row.empty:
                continue
            row["C1"] = str(code).zfill(5)
            row["age_group"] = label
            row["age_group_label"] = {
                "total": "전체 인구",
                "working_age": "15-64세 생산연령인구",
                "older": "65세 이상 고령층 인구",
            }[label]
            slope_rows.append(row.to_dict())
        slopes = pd.DataFrame(slope_rows)
        slopes["trend_class"] = slopes["slope_people_per_year"].map(classify_trend)
        slopes = slopes.sort_values("slope_people_per_year", ascending=False)
        slopes.to_csv(DERIVED / f"sigungu_{label}_population_trend_slopes.csv", index=False, encoding="utf-8-sig")
        outputs[label] = slopes
    return outputs


def match_topo(slopes: pd.DataFrame, output_name: str) -> pd.DataFrame:
    if not TOPO.exists():
        return pd.DataFrame()
    topo = json.loads(TOPO.read_text(encoding="utf-8"))
    object_name = next(iter(topo.get("objects", {})))
    geoms = topo["objects"][object_name]["geometries"]
    rows = []
    for geom in geoms:
        props = geom.get("properties", {})
        topo_code = str(props.get("code", ""))
        topo_name = str(props.get("name", ""))
        kosis_prefix = TOPO_PREFIX_TO_KOSIS_PREFIX.get(topo_code[:2], "")
        all_candidates = slopes.copy()
        province_candidates = slopes[slopes["C1"].astype(str).str.startswith(kosis_prefix)].copy()
        match = None
        note = "unmatched"
        exact = all_candidates[all_candidates["C1_NM"].astype(str) == topo_name]
        if len(exact) == 1:
            match = exact.iloc[0]
            note = "global_exact_name"
        else:
            exact = province_candidates[province_candidates["C1_NM"].astype(str) == topo_name]
            if len(exact) == 1:
                match = exact.iloc[0]
                note = "province_exact_name"
            else:
                suffix = all_candidates[all_candidates["C1_NM"].astype(str).map(lambda name: topo_name.endswith(name))]
                if len(suffix) != 1:
                    suffix = province_candidates[
                        province_candidates["C1_NM"].astype(str).map(lambda name: topo_name.endswith(name))
                    ]
                if len(suffix) == 1:
                    match = suffix.iloc[0]
                    note = "suffix_name"
                elif len(suffix) > 1:
                    suffix = suffix.assign(name_len=suffix["C1_NM"].astype(str).str.len()).sort_values(
                        "name_len", ascending=False
                    )
                    match = suffix.iloc[0]
                    note = "longest_suffix_name"
        if match is None:
            rows.append({"topo_code": topo_code, "topo_name": topo_name, "match_note": note})
        else:
            row = match.to_dict()
            row.update({"topo_code": topo_code, "topo_name": topo_name, "match_note": note})
            rows.append(row)
    map_values = pd.DataFrame(rows)
    map_values.to_csv(DERIVED / output_name, index=False, encoding="utf-8-sig")
    return map_values


def build_summary(slopes_by_group: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for label, slopes in slopes_by_group.items():
        rows.append(
            {
                "age_group": label,
                "age_group_label": slopes["age_group_label"].iloc[0],
                "start_year": int(slopes["start_year"].min()),
                "end_year": int(slopes["end_year"].max()),
                "regions_analyzed": int(len(slopes)),
                "regions_positive_slope": int((slopes["slope_people_per_year"] > 0).sum()),
                "regions_negative_slope": int((slopes["slope_people_per_year"] < 0).sum()),
                "median_slope_people_per_year": round(float(slopes["slope_people_per_year"].median()), 1),
                "max_slope_region": slopes.iloc[0]["C1_NM"],
                "max_slope_people_per_year": slopes.iloc[0]["slope_people_per_year"],
                "min_slope_region": slopes.iloc[-1]["C1_NM"],
                "min_slope_people_per_year": slopes.iloc[-1]["slope_people_per_year"],
            }
        )
    summary = pd.DataFrame(rows)
    summary.to_csv(DERIVED / "sigungu_age_group_population_trend_summary.csv", index=False, encoding="utf-8-sig")
    return summary


def main() -> None:
    panel = fetch_age_group_population()
    slopes_by_group = build_slopes(panel)
    match_topo(slopes_by_group["older"], "sigungu_older_population_trend_map_values.csv")
    match_topo(slopes_by_group["working_age"], "sigungu_working_age_population_trend_map_values.csv")
    summary = build_summary(slopes_by_group)
    print("\nSummary")
    print(summary.to_string(index=False))
    print("\nOlder growth top 10")
    print(slopes_by_group["older"].head(10).to_string(index=False))
    print("\nWorking-age growth top 10")
    print(slopes_by_group["working_age"].head(10).to_string(index=False))


if __name__ == "__main__":
    main()
