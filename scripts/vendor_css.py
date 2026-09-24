"""Vendor ``col.css`` from a pinned ``@colonization-re/web-ui`` release.

The web converter is served as plain static files, so the stylesheet lives in
the tree. A hand-copied file has no version and no provenance, so this script
owns the copy:

    web/vendor/col-css.json   the pin: tag, asset, sha256. The only place the
                              web-ui version lives.
    web/vendor/col.css        the vendored bytes, committed.

    python scripts/vendor_css.py            re-fetch the pinned tag and verify it
    python scripts/vendor_css.py v1.2.0     bump: fetch that tag, rewrite the pin
    python scripts/vendor_css.py --check    offline: does the file match the pin?

Every web-ui release attaches ``SHA256SUMS.txt``; downloads are verified
against it before the pin is written. ``--check`` also runs from the test suite,
so a hand-edited or half-updated vendor file fails ``pytest`` and blocks a
release.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "web" / "vendor"
PIN = VENDOR / "col-css.json"

REPO = "colonization-re/web-ui"
ASSET = "col.css"
SUMS = "SHA256SUMS.txt"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_pin() -> dict:
    return json.loads(PIN.read_text(encoding="utf-8"))


def release_url(tag: str, name: str) -> str:
    return f"https://github.com/{REPO}/releases/download/{tag}/{name}"


def fetch(url: str) -> bytes:
    with urllib.request.urlopen(url) as response:
        return response.read()


def expected_hash(sums: bytes, name: str) -> str:
    for line in sums.decode("utf-8").splitlines():
        match = re.match(r"^([0-9a-f]{64})\s+\*?(.+)$", line.strip())
        if match and match.group(2) == name:
            return match.group(1)
    raise SystemExit(f"{SUMS} has no entry for {name}")


def check() -> str | None:
    """Return an error message if the vendored file does not match the pin."""
    pin = read_pin()
    path = VENDOR / pin["asset"]
    if not path.exists():
        return f"web/vendor/{pin['asset']} is missing. Run: python scripts/vendor_css.py"
    got = sha256(path.read_bytes())
    if got != pin["sha256"]:
        return (
            f"web/vendor/{pin['asset']} does not match the pin.\n"
            f"    pinned   {pin['tag']}  {pin['sha256']}\n"
            f"    on disk  {got}\n"
            "Never edit it by hand: app-local rules belong in web/styles.css.\n"
            "To restore it: python scripts/vendor_css.py"
        )
    return None


def vendor(tag: str) -> None:
    print(f"fetching {ASSET} from {REPO} {tag}")
    css = fetch(release_url(tag, ASSET))
    want = expected_hash(fetch(release_url(tag, SUMS)), ASSET)
    got = sha256(css)
    if got != want:
        raise SystemExit(f"checksum mismatch for {ASSET} at {tag}\n  expected {want}\n  got      {got}")

    previous = read_pin().get("tag") if PIN.exists() else None
    (VENDOR / ASSET).write_bytes(css)
    pin = {
        "repo": REPO,
        "tag": tag,
        "asset": ASSET,
        "sha256": got,
        "bytes": len(css),
        "vendored": dt.date.today().isoformat(),
    }
    PIN.write_text(json.dumps(pin, indent=2) + "\n", encoding="utf-8")

    moved = f"{previous} -> {tag}" if previous and previous != tag else f"vendored {tag}"
    print(f"web/vendor/{ASSET}  {len(css) // 1024} KB, sha256 verified, {moved}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("tag", nargs="?", help="web-ui release tag, e.g. v1.1.0 (default: the pinned tag)")
    parser.add_argument("--check", action="store_true", help="verify the vendored file offline")
    args = parser.parse_args(argv)

    if args.check:
        error = check()
        if error:
            print(error, file=sys.stderr)
            return 1
        print(f"col.css  {read_pin()['tag']}  sha256 ok")
        return 0

    tag = args.tag or read_pin()["tag"]
    if not re.match(r"^v\d+\.\d+\.\d+", tag):
        raise SystemExit(f"not a release tag: {tag} (expected something like v1.1.0)")
    vendor(tag)
    return 0


if __name__ == "__main__":
    sys.exit(main())
