# -*- coding: utf-8 -*-
"""Watch markdown manuscripts and rebuild HTML pages when they change."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPTS = ROOT / "manuscripts"
BUILD_SCRIPT = ROOT / "scripts" / "build_book_pages.py"


def snapshot() -> dict[Path, float]:
    if not MANUSCRIPTS.exists():
        return {}
    return {path: path.stat().st_mtime for path in MANUSCRIPTS.rglob("*.md")}


def rebuild() -> None:
    print("[watch] markdown changed; rebuilding HTML...")
    subprocess.run([sys.executable, str(BUILD_SCRIPT)], cwd=ROOT, check=False)


def main() -> None:
    print(f"[watch] watching {MANUSCRIPTS}")
    previous = snapshot()
    try:
        while True:
            time.sleep(1.0)
            current = snapshot()
            if current != previous:
                previous = current
                rebuild()
    except KeyboardInterrupt:
        print("\n[watch] stopped")


if __name__ == "__main__":
    main()
