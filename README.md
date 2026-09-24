# fsm-to-mp

Python tooling to convert FreeCol map-editor saves (`.fsm`) into the original
Sid Meier's Colonization `.MP` map format.

The converter is intentionally small and dependency-free at runtime. It reads
the FreeCol ZIP/XML container directly, converts terrain into a neutral map
model, writes a three-plane `.MP` file, and can read the generated `.MP` back
for validation.

## Quick Start

```bash
python -m pip install -e ".[dev]"
python -m fsm_to_mp path/to/map.fsm out.MP
python -m fsm_to_mp --summary path/to/map.fsm
pytest
```

The CLI prints conversion warnings for information that original Colonization
cannot represent exactly, such as FreeCol lakes, great rivers, native
settlements, resources, regions, and river connection styles.

## Web Converter

The static browser version lives in `web/`. It vendors the shared
`@colonization-re/web-ui` stylesheet, pinned to a release tag and sha256 in
`web/vendor/col-css.json` (update with `python scripts/vendor_css.py <tag>`),
so it can be served as plain files without a build step or package install.

```bash
python -m http.server 8000 -d web
```

GitHub Pages is deployed automatically from `web/` by
`.github/workflows/pages.yml`.

## Releases

The Python tool and the web converter share one version and are released
together with `python scripts/release.py patch|minor|major`. Each
[GitHub release](https://github.com/colonization-re/fsm-to-mp/releases)
carries a runnable `fsm-to-mp-<version>.pyz` (`python3 fsm-to-mp-<version>.pyz
map.fsm out.MP`), the static `fsm-to-mp-web-<version>.zip` for self-hosting,
and a source `.zip`; notes come from `CHANGELOG.md`.

## Documentation

- `docs/formats.md` documents the researched FreeCol `.fsm` and Colonization
  `.MP` formats.
- `docs/conversion.md` documents every terrain conversion rule.
- `scripts/download_test_maps.py` downloads fixed upstream FreeCol maps and
  verifies SHA-256 hashes for local/manual fixture testing.
