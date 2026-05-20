# -*- coding: utf-8 -*-
"""Build a sigungu origin-destination gravity model for internal migration.

The KOSIS OD table is too large to request in one call, so this script fetches
one origin municipality at a time. The model is descriptive: it tests whether
the familiar gravity regularities, size and distance, are visible in Korean
municipal migration flows after adding broad regional opportunity indicators.
"""

from __future__ import annotations

import json
import math
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
KOREA_ROOT = ROOT.parent
if str(KOREA_ROOT) not in sys.path:
    sys.path.insert(0, str(KOREA_ROOT))

from apifunction.kosis import fetch_kosis_dataframe

YEAR = 2024
OD_TABLE = "DT_1B26003_A02"
DATA = ROOT / "data"
SOURCE = DATA / "source"
DERIVED = DATA / "derived"
GEO = DATA / "geo"

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

MACRO_AREA = {
    "11": "수도권",
    "28": "수도권",
    "41": "수도권",
    "51": "강원권",
    "43": "충청권",
    "44": "충청권",
    "30": "충청권",
    "36": "충청권",
    "52": "호남권",
    "46": "호남권",
    "29": "호남권",
    "47": "대경권",
    "27": "대경권",
    "48": "동남권",
    "26": "동남권",
    "31": "동남권",
    "50": "제주권",
}

GENERAL_GU_CITIES = {
    "Suwon-si",
    "Seongnam-si",
    "Anyang-si",
    "Ansan-si",
    "Goyang-si",
    "Yongin-si",
    "Cheongju-si",
    "Cheonan-si",
    "Jeonju-si",
    "Pohang-si",
    "Changwon-si",
}


def numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str).str.replace(",", "", regex=False).str.strip(),
        errors="coerce",
    )


def normalize_name(value: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def current_sido(code: object) -> str:
    return str(code).zfill(5)[:2]


def read_population() -> pd.DataFrame:
    pop = pd.read_csv(DATA / "sigungu_population_2004_2024.csv", dtype={"C1": str})
    pop = pop[pop["year"] == YEAR].copy()
    pop["C1"] = pop["C1"].astype(str).str.zfill(5)
    pop["sido"] = pop["C1"].str[:2]
    return pop[["C1", "C1_NM", "C1_NM_ENG", "population", "sido"]].drop_duplicates("C1")


def fetch_od_by_origin(origin_code: str) -> pd.DataFrame:
    return fetch_kosis_dataframe(
        OD_TABLE,
        org_id="101",
        prd_se="Y",
        start_prd_de=str(YEAR),
        end_prd_de=str(YEAR),
        load_gubun="2",
        itm_id="T70",
        obj_l1=origin_code,
        obj_l2="ALL",
        obj_l3="0",
        timeout=120,
    )


def fetch_or_read_od(pop: pd.DataFrame) -> pd.DataFrame:
    SOURCE.mkdir(parents=True, exist_ok=True)
    path = SOURCE / f"kosis_migration_od_sigungu_{YEAR}.csv"
    if path.exists():
        return pd.read_csv(path, dtype={"C1": str, "C2": str, "C3": str})

    frames: list[pd.DataFrame] = []
    codes = sorted(pop["C1"].unique())
    for idx, code in enumerate(codes, start=1):
        try:
            df = fetch_od_by_origin(code)
        except Exception as exc:  # KOSIS sometimes reports invalid key for invalid filters.
            print(f"[warn] skip origin {code}: {exc}")
            continue
        frames.append(df)
        if idx % 25 == 0:
            print(f"fetched {idx}/{len(codes)} origins")
        time.sleep(0.08)

    if not frames:
        raise RuntimeError("No KOSIS OD migration rows were fetched.")
    od = pd.concat(frames, ignore_index=True)
    od.to_csv(path, index=False, encoding="utf-8-sig")
    return od


def decode_topo_arcs(topo: dict) -> list[list[list[float]]]:
    scale_x, scale_y = topo["transform"]["scale"]
    trans_x, trans_y = topo["transform"]["translate"]
    decoded = []
    for arc in topo["arcs"]:
        x = y = 0
        pts = []
        for dx, dy in arc:
            x += dx
            y += dy
            pts.append([x * scale_x + trans_x, y * scale_y + trans_y])
        decoded.append(pts)
    return decoded


def ring_from_arc_indices(arcs: list[list[list[float]]], arc_indices: list[int]) -> list[list[float]]:
    ring: list[list[float]] = []
    for arc_index in arc_indices:
        if arc_index >= 0:
            pts = arcs[arc_index]
        else:
            pts = list(reversed(arcs[-arc_index - 1]))
        if ring and pts and ring[-1] == pts[0]:
            ring.extend(pts[1:])
        else:
            ring.extend(pts)
    return ring


def polygon_centroid(ring: list[list[float]]) -> tuple[float, float, float]:
    if len(ring) < 3:
        if not ring:
            return 0.0, 0.0, 0.0
        xs = [p[0] for p in ring]
        ys = [p[1] for p in ring]
        return float(np.mean(xs)), float(np.mean(ys)), 0.0
    area = cx = cy = 0.0
    pts = ring if ring[0] == ring[-1] else ring + [ring[0]]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        cross = x0 * y1 - x1 * y0
        area += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    area *= 0.5
    if abs(area) < 1e-12:
        xs = [p[0] for p in ring]
        ys = [p[1] for p in ring]
        return float(np.mean(xs)), float(np.mean(ys)), 0.0
    return cx / (6 * area), cy / (6 * area), abs(area)


def geometry_centroid(geometry: dict, arcs: list[list[list[float]]]) -> tuple[float, float, float]:
    pieces = geometry["arcs"] if geometry["type"] == "MultiPolygon" else [geometry["arcs"]]
    weighted_x = weighted_y = total_area = 0.0
    fallback_points: list[list[float]] = []
    for polygon in pieces:
        if not polygon:
            continue
        outer = ring_from_arc_indices(arcs, polygon[0])
        fallback_points.extend(outer)
        cx, cy, area = polygon_centroid(outer)
        if area > 0:
            weighted_x += cx * area
            weighted_y += cy * area
            total_area += area
    if total_area > 0:
        return weighted_x / total_area, weighted_y / total_area, total_area
    xs = [p[0] for p in fallback_points]
    ys = [p[1] for p in fallback_points]
    return float(np.mean(xs)), float(np.mean(ys)), 0.0


def build_centroids(pop: pd.DataFrame) -> pd.DataFrame:
    path = DERIVED / "sigungu_centroids_approx_2018.csv"
    crosswalk_path = DERIVED / "sigungu_code_crosswalk_2018_current.csv"
    if path.exists() and crosswalk_path.exists():
        return pd.read_csv(path, dtype={"C1": str})

    raw = (GEO / "skorea-municipalities-2018-topo-simple.json").read_text(encoding="utf-8")
    topo = json.loads(raw)
    arcs = decode_topo_arcs(topo)
    geoms = topo["objects"]["skorea_municipalities_2018_geo"]["geometries"]

    topo_rows = []
    for geom in geoms:
        props = geom["properties"]
        lon, lat, area = geometry_centroid(geom, arcs)
        old_code = str(props["code"]).zfill(5)
        old_sido = old_code[:2]
        topo_rows.append(
            {
                "old_code": old_code,
                "current_sido": OLD_TO_CURRENT_SIDO.get(old_sido, old_sido),
                "name_eng": props.get("name_eng", ""),
                "norm_name": normalize_name(props.get("name_eng", "")),
                "lon": lon,
                "lat": lat,
                "area_weight": area,
            }
        )
    topo_df = pd.DataFrame(topo_rows)
    pop = pop.copy()
    pop["norm_name"] = pop["C1_NM_ENG"].map(normalize_name)

    rows = []
    crosswalk_rows = []
    for item in pop.itertuples(index=False):
        candidates = topo_df[topo_df["current_sido"] == item.sido]
        exact = candidates[candidates["norm_name"] == item.norm_name]
        quality = "exact_name"
        matched = exact
        if matched.empty and item.C1_NM_ENG in GENERAL_GU_CITIES:
            prefix = normalize_name(item.C1_NM_ENG)
            matched = candidates[candidates["norm_name"].str.startswith(prefix)]
            quality = "aggregated_general_gu"
        if matched.empty:
            matched = candidates
            quality = "province_proxy"
        if matched.empty:
            rows.append(
                {
                    "C1": item.C1,
                    "C1_NM": item.C1_NM,
                    "C1_NM_ENG": item.C1_NM_ENG,
                    "lon": np.nan,
                    "lat": np.nan,
                    "centroid_quality": "missing",
                }
            )
            continue
        if quality != "province_proxy":
            for old in matched["old_code"].drop_duplicates():
                crosswalk_rows.append(
                    {
                        "old_code": str(old).zfill(5),
                        "current_code": item.C1,
                        "current_name": item.C1_NM,
                        "current_name_eng": item.C1_NM_ENG,
                        "match_quality": quality,
                    }
                )
        weights = matched["area_weight"].clip(lower=0)
        if float(weights.sum()) <= 0:
            weights = pd.Series(1.0, index=matched.index)
        lon = float(np.average(matched["lon"], weights=weights))
        lat = float(np.average(matched["lat"], weights=weights))
        rows.append(
            {
                "C1": item.C1,
                "C1_NM": item.C1_NM,
                "C1_NM_ENG": item.C1_NM_ENG,
                "lon": lon,
                "lat": lat,
                "centroid_quality": quality,
            }
        )

    centroids = pd.DataFrame(rows)
    centroids.to_csv(path, index=False, encoding="utf-8-sig")
    pd.DataFrame(crosswalk_rows).drop_duplicates().to_csv(
        crosswalk_path, index=False, encoding="utf-8-sig"
    )
    return centroids


def haversine_km(lon1: np.ndarray, lat1: np.ndarray, lon2: np.ndarray, lat2: np.ndarray) -> np.ndarray:
    r = 6371.0088
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def read_business_density() -> pd.DataFrame:
    df = pd.read_csv(SOURCE / "kosis_business_density_sido_2015_2024.csv", dtype={"C1": str})
    rows = df[
        (df["PRD_DE"].astype(str) == str(YEAR))
        & (df["ITM_ID"].astype(str).isin(["T001", "T002"]))
    ].copy()
    rows["C1"] = rows["C1"].astype(str).str.zfill(5)
    crosswalk = pd.read_csv(DERIVED / "sigungu_code_crosswalk_2018_current.csv", dtype={"old_code": str, "current_code": str})
    rows = rows.merge(crosswalk, left_on="C1", right_on="old_code", how="left")
    pop_names = read_population()[["C1", "C1_NM", "sido"]].rename(columns={"C1": "name_match_code"})
    rows["source_sido"] = rows["C1"].str[:2].map(lambda x: OLD_TO_CURRENT_SIDO.get(x, x))
    rows = rows.merge(
        pop_names,
        left_on=["source_sido", "C1_NM"],
        right_on=["sido", "C1_NM"],
        how="left",
    )
    rows["current_code"] = rows["current_code"].fillna(rows["name_match_code"])
    rows = rows[rows["current_code"].notna()].copy()
    rows["value"] = numeric(rows["DT"])
    wide = rows.pivot_table(index="current_code", columns="ITM_ID", values="value", aggfunc="sum").reset_index()
    wide["businesses_per_1000_people"] = wide["T001"] / wide["T002"] * 1000
    return wide.rename(columns={"current_code": "C1"})[["C1", "businesses_per_1000_people"]]


def read_sido_income() -> pd.DataFrame:
    df = pd.read_csv(SOURCE / "kosis_grdp_per_capita_sido_2015_2024.csv", dtype={"C1": str})
    rows = df[(df["PRD_DE"].astype(str) == str(YEAR)) & (df["C1"].astype(str) != "00")].copy()
    rows["sido"] = rows["C1"].astype(str).str.zfill(2).map(lambda x: OLD_TO_CURRENT_SIDO.get(x, x))
    rows["grdp_per_capita_thousand_won"] = numeric(rows["DT"])
    return rows[["sido", "grdp_per_capita_thousand_won"]]


def macro_area(code: str) -> str:
    return MACRO_AREA.get(str(code).zfill(5)[:2], "기타")


def build_model_panel(od: pd.DataFrame, pop: pd.DataFrame, centroids: pd.DataFrame) -> pd.DataFrame:
    dest_codes = set(pop["C1"])
    od = od.copy()
    od["C1"] = od["C1"].astype(str).str.zfill(5)
    od["C2"] = od["C2"].astype(str).str.zfill(5)
    od["flow"] = numeric(od["DT"])
    od = od[(od["C1"].isin(dest_codes)) & (od["C2"].isin(dest_codes))].copy()
    od = od[od["C1"] != od["C2"]].copy()

    pop_origin = pop.rename(
        columns={
            "C1": "origin_code",
            "C1_NM": "origin_name",
            "C1_NM_ENG": "origin_name_eng",
            "population": "origin_population",
            "sido": "origin_sido",
        }
    )
    pop_dest = pop.rename(
        columns={
            "C1": "dest_code",
            "C1_NM": "dest_name",
            "C1_NM_ENG": "dest_name_eng",
            "population": "dest_population",
            "sido": "dest_sido",
        }
    )
    cent_o = centroids.rename(
        columns={
            "C1": "origin_code",
            "lon": "origin_lon",
            "lat": "origin_lat",
            "centroid_quality": "origin_centroid_quality",
        }
    )[["origin_code", "origin_lon", "origin_lat", "origin_centroid_quality"]]
    cent_d = centroids.rename(
        columns={
            "C1": "dest_code",
            "lon": "dest_lon",
            "lat": "dest_lat",
            "centroid_quality": "dest_centroid_quality",
        }
    )[["dest_code", "dest_lon", "dest_lat", "dest_centroid_quality"]]

    panel = od.rename(columns={"C1": "origin_code", "C2": "dest_code"})[
        ["origin_code", "dest_code", "C1_NM", "C2_NM", "flow"]
    ]
    panel = panel.merge(pop_origin, on="origin_code", how="left")
    panel = panel.merge(pop_dest, on="dest_code", how="left")
    panel = panel.merge(cent_o, on="origin_code", how="left")
    panel = panel.merge(cent_d, on="dest_code", how="left")
    business_density = read_business_density()
    panel = panel.merge(business_density.rename(columns={"C1": "dest_code"}), on="dest_code", how="left")
    sido_business_density = (
        business_density.assign(dest_sido=business_density["C1"].astype(str).str[:2])
        .groupby("dest_sido", as_index=False)["businesses_per_1000_people"]
        .mean()
        .rename(columns={"businesses_per_1000_people": "sido_businesses_per_1000_people"})
    )
    panel = panel.merge(sido_business_density, on="dest_sido", how="left")
    panel["business_density_imputed"] = panel["businesses_per_1000_people"].isna()
    panel["businesses_per_1000_people"] = panel["businesses_per_1000_people"].fillna(
        panel["sido_businesses_per_1000_people"]
    )
    panel = panel.merge(read_sido_income().rename(columns={"sido": "dest_sido"}), on="dest_sido", how="left")

    panel["distance_km"] = haversine_km(
        panel["origin_lon"].to_numpy(float),
        panel["origin_lat"].to_numpy(float),
        panel["dest_lon"].to_numpy(float),
        panel["dest_lat"].to_numpy(float),
    )
    panel["origin_macro"] = panel["origin_code"].map(macro_area)
    panel["dest_macro"] = panel["dest_code"].map(macro_area)
    panel["same_sido"] = (panel["origin_sido"] == panel["dest_sido"]).astype(float)
    panel["same_macro_area"] = (panel["origin_macro"] == panel["dest_macro"]).astype(float)
    panel["capital_destination"] = panel["dest_sido"].isin(["11", "28", "41"]).astype(float)

    panel["log_flow"] = np.log(panel["flow"].where(panel["flow"] > 0))
    panel["log_flow_plus_one"] = np.log1p(panel["flow"].clip(lower=0))
    panel["log_origin_population"] = np.log(panel["origin_population"])
    panel["log_dest_population"] = np.log(panel["dest_population"])
    panel["log_distance_km"] = np.log(panel["distance_km"].clip(lower=0.5))
    panel["log_dest_grdp_pc"] = np.log(panel["grdp_per_capita_thousand_won"])
    panel["log_dest_business_density"] = np.log(panel["businesses_per_1000_people"])

    panel = panel.replace([np.inf, -np.inf], np.nan)
    out = DERIVED / f"migration_gravity_panel_sigungu_{YEAR}.csv"
    panel.to_csv(out, index=False, encoding="utf-8-sig")
    return panel


def ols_fit(df: pd.DataFrame, y_col: str, x_cols: list[str], fixed_effects: list[str] | None = None) -> dict:
    work = df[[y_col] + x_cols + (fixed_effects or [])].dropna().copy()
    y = work[y_col].to_numpy(dtype=float)
    parts = [pd.Series(1.0, index=work.index, name="const")]
    for col in x_cols:
        values = work[col].astype(float)
        if col.startswith("log_"):
            values = values - values.mean()
        parts.append(values.rename(col))
    for fe in fixed_effects or []:
        parts.append(pd.get_dummies(work[fe].astype(str), prefix=fe, drop_first=True, dtype=float))
    x = pd.concat(parts, axis=1)
    x_arr = x.to_numpy(dtype=float)
    beta = np.linalg.lstsq(x_arr, y, rcond=None)[0]
    fitted = x_arr @ beta
    residual = y - fitted
    ss_res = float(np.sum(residual**2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot else np.nan
    dof = max(len(y) - x_arr.shape[1], 1)
    sigma2 = ss_res / dof
    xtx_inv = np.linalg.pinv(x_arr.T @ x_arr)
    se = np.sqrt(np.diag(xtx_inv) * sigma2)
    return {
        "work": work,
        "names": list(x.columns),
        "beta": beta,
        "se": se,
        "n": len(y),
        "r2": r2,
        "fitted": fitted,
        "residual": residual,
    }


def ppml_fit(df: pd.DataFrame, y_col: str, x_cols: list[str], max_iter: int = 80) -> dict:
    work = df[[y_col] + x_cols].dropna().copy()
    y = work[y_col].to_numpy(dtype=float)
    parts = [pd.Series(1.0, index=work.index, name="const")]
    for col in x_cols:
        values = work[col].astype(float)
        if col.startswith("log_"):
            values = values - values.mean()
        parts.append(values.rename(col))
    x = pd.concat(parts, axis=1)
    x_arr = x.to_numpy(dtype=float)
    init = ols_fit(work.assign(_log_y=np.log1p(y)), "_log_y", x_cols)
    beta = init["beta"]
    for _ in range(max_iter):
        eta = np.clip(x_arr @ beta, -30, 20)
        mu = np.exp(eta)
        z = eta + (y - mu) / np.clip(mu, 1e-9, None)
        wx = x_arr * np.sqrt(mu)[:, None]
        wz = z * np.sqrt(mu)
        new_beta = np.linalg.lstsq(wx, wz, rcond=None)[0]
        if np.max(np.abs(new_beta - beta)) < 1e-8:
            beta = new_beta
            break
        beta = new_beta
    eta = np.clip(x_arr @ beta, -30, 20)
    mu = np.exp(eta)
    xtwx_inv = np.linalg.pinv((x_arr * mu[:, None]).T @ x_arr)
    se = np.sqrt(np.diag(xtwx_inv))
    pseudo_r2 = float(np.corrcoef(y, mu)[0, 1] ** 2) if len(y) > 1 else np.nan
    return {"work": work, "names": list(x.columns), "beta": beta, "se": se, "n": len(y), "r2": pseudo_r2}


def p_value_from_z(z: float) -> float:
    return math.erfc(abs(z) / math.sqrt(2))


def model_rows(model_name: str, fit: dict, labels: dict[str, str], notes: str) -> list[dict]:
    rows = []
    for name, beta, se in zip(fit["names"], fit["beta"], fit["se"]):
        if name == "const" or name not in labels:
            continue
        stat = beta / se if se else np.nan
        rows.append(
            {
                "model": model_name,
                "variable": name,
                "variable_label": labels[name],
                "coefficient": float(beta),
                "standard_error": float(se),
                "p_value": float(p_value_from_z(stat)) if np.isfinite(stat) else np.nan,
                "n": int(fit["n"]),
                "r2": round(float(fit["r2"]), 3) if np.isfinite(fit["r2"]) else "",
                "model_note": notes,
            }
        )
    return rows


def fit_models(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    x_cols = [
        "log_origin_population",
        "log_dest_population",
        "log_distance_km",
        "same_sido",
        "same_macro_area",
        "log_dest_grdp_pc",
        "log_dest_business_density",
        "capital_destination",
    ]
    labels = {
        "log_origin_population": "전출지 인구(로그)",
        "log_dest_population": "전입지 인구(로그)",
        "log_distance_km": "중심거리(로그)",
        "same_sido": "같은 광역시도",
        "same_macro_area": "같은 권역",
        "log_dest_grdp_pc": "전입지 1인당 GRDP(광역)",
        "log_dest_business_density": "전입지 사업체밀도",
        "capital_destination": "전입지가 수도권",
    }
    work = panel[panel["distance_km"].gt(0)].dropna(subset=x_cols + ["flow"]).copy()
    log_work = work[work["flow"].gt(0)].copy()
    log_fit = ols_fit(log_work, "log_flow", x_cols)
    ppml = ppml_fit(work, "flow", x_cols)
    fe_cols = ["log_distance_km", "same_sido", "same_macro_area"]
    fe_labels = {
        "log_distance_km": "중심거리(로그)",
        "same_sido": "같은 광역시도",
        "same_macro_area": "같은 권역",
    }
    fe_fit = ols_fit(log_work, "log_flow", fe_cols, fixed_effects=["origin_code", "dest_code"])

    rows = []
    rows.extend(model_rows("로그 OLS", log_fit, labels, "양의 이동량만 사용한 로그-선형 중력모형"))
    rows.extend(model_rows("PPML", ppml, labels, "0 이동쌍을 포함할 수 있는 포아송 유사최대우도 중력모형"))
    rows.extend(model_rows("출발·도착지 고정효과 OLS", fe_fit, fe_labels, "출발지와 도착지의 고정 특성을 통제한 로그-선형 모형"))
    coef = pd.DataFrame(rows)
    coef.to_csv(DERIVED / "migration_gravity_coefficients.csv", index=False, encoding="utf-8-sig")

    top = (
        work.sort_values("flow", ascending=False)
        .head(20)
        .assign(route=lambda d: d["origin_name"] + " → " + d["dest_name"])
        [
            [
                "route",
                "origin_code",
                "dest_code",
                "origin_name",
                "dest_name",
                "origin_sido",
                "dest_sido",
                "distance_km",
                "flow",
            ]
        ]
    )
    top.to_csv(DERIVED / "migration_gravity_top_flows.csv", index=False, encoding="utf-8-sig")

    summary = pd.DataFrame(
        [
            {"metric": "year", "value": YEAR},
            {"metric": "od_pairs", "value": len(work)},
            {"metric": "positive_od_pairs", "value": int(work["flow"].gt(0).sum())},
            {"metric": "origins", "value": work["origin_code"].nunique()},
            {"metric": "destinations", "value": work["dest_code"].nunique()},
            {"metric": "log_ols_r2", "value": round(float(log_fit["r2"]), 3)},
            {"metric": "ppml_corr_r2", "value": round(float(ppml["r2"]), 3)},
            {"metric": "fe_log_ols_r2", "value": round(float(fe_fit["r2"]), 3)},
            {
                "metric": "province_proxy_centroids",
                "value": int(
                    (work["origin_centroid_quality"].eq("province_proxy") | work["dest_centroid_quality"].eq("province_proxy")).sum()
                ),
            },
            {"metric": "business_density_imputed_pairs", "value": int(work["business_density_imputed"].sum())},
        ]
    )
    summary.to_csv(DERIVED / "migration_gravity_summary.csv", index=False, encoding="utf-8-sig")
    return coef, top, summary


def main() -> None:
    SOURCE.mkdir(parents=True, exist_ok=True)
    DERIVED.mkdir(parents=True, exist_ok=True)
    pop = read_population()
    od = fetch_or_read_od(pop)
    centroids = build_centroids(pop)
    panel = build_model_panel(od, pop, centroids)
    coef, top, summary = fit_models(panel)
    print(coef.to_string(index=False))
    print(summary.to_string(index=False))
    print(top.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
