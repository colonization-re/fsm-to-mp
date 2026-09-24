from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import fsm_to_mp

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_web_version_matches_package():
    html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
    meta = re.search(r'<meta name="version" content="([^"]+)">', html).group(1)
    badge = re.search(r"<span[^>]*data-version>v([^<]+)</span>", html).group(1)
    assert meta == badge == fsm_to_mp.__version__


def test_vendored_web_ui_matches_pin():
    assert load_script("vendor_css").check() is None
