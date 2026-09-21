#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from pathlib import Path
import urllib.request


FREECOL_COMMIT = "db87a4da4a18af61a622a3781455090670436247"
BASE_URL = f"https://raw.githubusercontent.com/FreeCol/freecol/{FREECOL_COMMIT}/data/maps"
TARGET_DIR = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "freecol"

MAPS = {
    "S_Caribbean_Phil.fsm": "ab62beecd06199a4db81f3a829d5ded76b4da7bed5239597c22a0deab08135df",
    "M_America_Mazim.fsm": "ca0d4c4db4237a3eccaab69b79f668a88c186d27dcf8ade585ea638a4b6fa401",
    "XL_GigaEarth_Mazim.fsm": "067e44f93164f6977ee3692ee6fb4a330f0258822b496f858e6cbd547b1b3fee",
}


def main() -> int:
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    for name, expected in MAPS.items():
        url = f"{BASE_URL}/{name}"
        target = TARGET_DIR / name
        print(f"download {url}")
        data = urllib.request.urlopen(url, timeout=30).read()
        actual = hashlib.sha256(data).hexdigest()
        if actual != expected:
            raise SystemExit(f"{name}: expected {expected}, got {actual}")
        target.write_bytes(data)
        print(f"wrote {target} ({len(data)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
