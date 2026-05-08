from __future__ import annotations

import sys
from pathlib import Path
import json

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
KOREA_ROOT = ROOT.parent
if str(KOREA_ROOT) not in sys.path:
    sys.path.insert(0, str(KOREA_ROOT))

from apifunction.kosis import fetch_kosis_table


START_YEAR = 2004
END_YEAR = 2024
MIN_OBSERVATIONS = 10

DATA = ROOT / "data"
DERIVED = DATA / "derived"
TOPO = DATA / "geo" / "skorea-municipalities-2018-topo-simple.json"

TOPO_PREFIX_TO_KOSIS_PREFIX = {
    "11": "11",  # Seoul
    "21": "26",  # Busan
    "22": "27",  # Daegu
    "23": "28",  # Incheon
    "24": "29",  # Gwangju
    "25": "30",  # Daejeon
    "26": "31",  # Ulsan
    "29": "36",  # Sejong
    "31": "41",  # Gyeonggi
    "32": "51",  # Gangwon Special Self-Governing Province
    "33": "43",  # Chungbuk
    "34": "44",  # Chungnam
    "35": "52",  # Jeonbuk State
    "36": "46",  # Jeonnam
    "37": "47",  # Gyeongbuk
    "38": "48",  # Gyeongnam
    "39": "50",  # Jeju
}


def regression_slope(group: pd.DataFrame) -> pd.Series:
    g = group.sort_values("year").dropna(subset=["population"])
    n = len(g)
    if n < MIN_OBSERVATIONS:
        return pd.Series(dtype="object")
    x = g["year"].astype(float)
    y = g["population"].astype(float)
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
    return pd.Series(
        {
            "C1_NM": last["C1_NM"],
            "C1_NM_ENG": last.get("C1_NM_ENG", ""),
            "n_years": n,
            "start_year": int(first["year"]),
            "end_year": int(last["year"]),
            "start_population": int(first["population"]),
            "end_population": int(last["population"]),
            "absolute_change": int(last["population"] - first["population"]),
            "change_pct": round((last["population"] / first["population"] - 1) * 100, 2)
            if first["population"]
            else pd.NA,
            "slope_people_per_year": round(slope, 1),
            "slope_per_10k_people": round(slope / 10_000, 3),
            "r2": round(r2, 3),
        }
    )


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    DERIVED.mkdir(parents=True, exist_ok=True)
    raw = fetch_kosis_table("DT_1B040A3", cycle="A", start_year=START_YEAR, end_year=END_YEAR)
    raw["year"] = pd.to_numeric(raw["PRD_DE"], errors="coerce")
    raw["population"] = pd.to_numeric(raw["DT"], errors="coerce")
    sigungu = raw[
        (raw["C1"].astype(str).str.len() == 5)
        & (raw["ITM_NM"].astype(str) == "총인구수")
        & (raw["year"].between(START_YEAR, END_YEAR))
    ][["year", "C1", "C1_NM", "C1_NM_ENG", "population"]].copy()
    sigungu["year"] = sigungu["year"].astype(int)
    sigungu["C1"] = sigungu["C1"].astype(str)
    sigungu = sigungu.sort_values(["C1", "year"])
    sigungu.to_csv(DATA / "sigungu_population_2004_2024.csv", index=False, encoding="utf-8-sig")

    slope_rows = []
    for code, group in sigungu.groupby("C1"):
        row = regression_slope(group)
        if row.empty:
            continue
        row["C1"] = code
        slope_rows.append(row.to_dict())
    slopes = pd.DataFrame(slope_rows)
    slopes["C1"] = slopes["C1"].astype(str)
    slopes["trend_class"] = pd.cut(
        slopes["slope_people_per_year"],
        bins=[-10**9, -5000, -1000, 0, 1000, 5000, 10**9],
        labels=[
            "급격한 감소",
            "감소",
            "완만한 감소",
            "완만한 증가",
            "증가",
            "급격한 증가",
        ],
        right=False,
    )
    slopes = slopes.sort_values("slope_people_per_year", ascending=False)
    slopes.to_csv(DERIVED / "sigungu_population_trend_slopes.csv", index=False, encoding="utf-8-sig")
    if TOPO.exists():
        topo = json.loads(TOPO.read_text(encoding="utf-8"))
        object_name = next(iter(topo.get("objects", {})))
        geoms = topo["objects"][object_name]["geometries"]
        map_rows = []
        for geom in geoms:
            props = geom.get("properties", {})
            topo_code = str(props.get("code", ""))
            topo_name = str(props.get("name", ""))
            kosis_prefix = TOPO_PREFIX_TO_KOSIS_PREFIX.get(topo_code[:2], "")
            all_candidates = slopes.copy()
            province_candidates = slopes[slopes["C1"].str.startswith(kosis_prefix)].copy()
            exact = all_candidates[all_candidates["C1_NM"].astype(str) == topo_name]
            suffix = pd.DataFrame()
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
                    match = None
                    note = "unmatched"
                if len(suffix) == 1:
                    match = suffix.iloc[0]
                    note = "suffix_name"
                elif len(suffix) > 1:
                    suffix = suffix.assign(name_len=suffix["C1_NM"].astype(str).str.len()).sort_values("name_len", ascending=False)
                    match = suffix.iloc[0]
                    note = "longest_suffix_name"
            if match is None:
                map_rows.append({"topo_code": topo_code, "topo_name": topo_name, "match_note": note})
            else:
                row = match.to_dict()
                row.update({"topo_code": topo_code, "topo_name": topo_name, "match_note": note})
                map_rows.append(row)
        map_values = pd.DataFrame(map_rows)
        map_values.to_csv(DERIVED / "sigungu_population_trend_map_values.csv", index=False, encoding="utf-8-sig")

    summary = pd.DataFrame(
        [
            {
                "start_year": START_YEAR,
                "end_year": END_YEAR,
                "regions_analyzed": int(len(slopes)),
                "regions_positive_slope": int((slopes["slope_people_per_year"] > 0).sum()),
                "regions_negative_slope": int((slopes["slope_people_per_year"] < 0).sum()),
                "median_slope_people_per_year": round(float(slopes["slope_people_per_year"].median()), 1),
                "max_slope_region": slopes.iloc[0]["C1_NM"],
                "max_slope_people_per_year": slopes.iloc[0]["slope_people_per_year"],
                "min_slope_region": slopes.iloc[-1]["C1_NM"],
                "min_slope_people_per_year": slopes.iloc[-1]["slope_people_per_year"],
            }
        ]
    )
    summary.to_csv(DERIVED / "sigungu_population_trend_summary.csv", index=False, encoding="utf-8-sig")
    print("Top growth")
    print(slopes.head(12).to_string(index=False))
    print("\nTop decline")
    print(slopes.tail(12).sort_values("slope_people_per_year").to_string(index=False))
    print("\nSummary")
    print(summary.to_string(index=False))
    if TOPO.exists():
        print("\nMap matching")
        print(map_values["match_note"].value_counts(dropna=False).to_string())


if __name__ == "__main__":
    main()
