# -*- coding: utf-8 -*-
"""Fetch additional KOSIS tables for nationwide population-policy analysis."""

from __future__ import annotations

import json
import site
import sys
from pathlib import Path

USER_SITE = site.getusersitepackages()
if USER_SITE and USER_SITE not in sys.path:
    sys.path.append(USER_SITE)

ROOT = Path(__file__).resolve().parents[1]
KOREA_ROOT = ROOT.parent
if str(KOREA_ROOT) not in sys.path:
    sys.path.insert(0, str(KOREA_ROOT))

from apifunction.kosis import fetch_kosis_table  # noqa: E402

DATA = ROOT / "data"


TABLES = {
    "fertility_by_mother_age_DT_1B81A21": ("DT_1B81A21", "A", 2000, 2024),
    "mean_birth_age_DT_1B81A20": ("DT_1B81A20", "A", 1993, 2024),
    "vital_rates_DT_1B8000H": ("DT_1B8000H", "A", 1990, 2024),
    "domestic_migration_age_DT_1B26001_A03": ("DT_1B26001_A03", "A", 2000, 2025),
    "households_INH_1JC1501": ("INH_1JC1501", "A", 2015, 2024),
    "future_households_DT_1BZ0503": ("DT_1BZ0503", "A", 2000, 2050),
    "national_transfer_accounts_DT_1NTA03": ("DT_1NTA03", "A", 2010, 2024),
    "international_marriage_DT_1B83A24": ("DT_1B83A24", "A", 2000, 2024),
    "foreign_wife_nationality_DT_1B83B29": ("DT_1B83B29", "A", 1993, 2024),
}


def main() -> None:
    DATA.mkdir(exist_ok=True)
    manifest: dict[str, object] = {"outputs": {}, "errors": {}}
    for stem, (table_id, cycle, start, end) in TABLES.items():
        try:
            df = fetch_kosis_table(table_id, cycle=cycle, start_year=start, end_year=end)
            path = DATA / f"{stem}.csv"
            df.to_csv(path, index=False, encoding="utf-8-sig")
            manifest["outputs"][stem] = str(path)
        except Exception as exc:  # noqa: BLE001
            manifest["errors"][stem] = f"{type(exc).__name__}: {exc}"
    (DATA / "policy_depth_fetch_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
