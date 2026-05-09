# -*- coding: utf-8 -*-
"""Fetch resident-registration age data used for the 2010 discontinuity section."""

from __future__ import annotations

import site
import sys
from pathlib import Path

USER_SITE = site.getusersitepackages()
if USER_SITE and USER_SITE not in sys.path:
    sys.path.append(USER_SITE)

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from scripts.fetch_population_book_data import fetch_kosis_population_item


def main() -> None:
    frames: list[pd.DataFrame] = []
    for year in range(2008, 2026):
        frame = fetch_kosis_population_item(year=year, region_code="00", age_code="ALL")
        frames.append(frame)

    raw = pd.concat(frames, ignore_index=True)
    raw["year"] = pd.to_numeric(raw["PRD_DE"], errors="coerce").astype("Int64")
    raw["population"] = pd.to_numeric(raw["DT"], errors="coerce")
    raw = raw[
        [
            "year",
            "C1",
            "C1_NM",
            "C2",
            "C2_NM",
            "population",
            "UNIT_NM",
            "UNIT_NM_ENG",
            "ITM_ID",
            "ITM_NM",
        ]
    ].sort_values(["year", "C2"])
    out = DATA / "resident_registration_national_age_DT_1B04006.csv"
    raw.to_csv(out, index=False, encoding="utf-8-sig")
    print(out)


if __name__ == "__main__":
    main()
