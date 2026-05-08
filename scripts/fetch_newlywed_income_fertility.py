# -*- coding: utf-8 -*-
"""Fetch KOSIS newlywed fertility by income for the education chapter."""

from __future__ import annotations

import csv
import json
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KOREA_ROOT = ROOT.parent
DATA = ROOT / "data"
KEY_FILE = KOREA_ROOT / "apifunction" / "kosis_api_key.txt"
KOSIS_URL = "https://kosis.kr/openapi/Param/statisticsParameterData.do"


def fetch() -> list[dict[str, str]]:
    key = KEY_FILE.read_text(encoding="utf-8").strip()
    params = {
        "method": "getList",
        "apiKey": key,
        "tblId": "DT_1NW2016",
        "orgId": "101",
        "startPrdDe": "2015",
        "endPrdDe": "2024",
        "itmId": "ALL",
        "format": "json",
        "jsonVD": "Y",
        "prdSe": "Y",
        "loadGubun": "2",
        "objL1": "ALL",
        "objL2": "ALL",
    }
    url = KOSIS_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if isinstance(payload, dict) and payload.get("err"):
        raise RuntimeError(f"KOSIS error {payload.get('err')}: {payload.get('errMsg')}")
    if not isinstance(payload, list):
        raise RuntimeError(f"Unexpected KOSIS payload: {type(payload)!r}")
    return payload


def main() -> None:
    rows = fetch()
    out = DATA / "kosis_newlywed_income_children_DT_1NW2016.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for row in rows for key in row})
    with out.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {out} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
