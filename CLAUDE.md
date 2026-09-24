# fsm-to-mp

## Releasing

One version covers both deliverables, the Python tool and the web converter.
It is one line, `__version__` in [src/fsm_to_mp/\_\_init\_\_.py](src/fsm_to_mp/__init__.py);
`pyproject.toml` and `fsm-to-mp --version` read it from there, `web/index.html`
carries a copy (`<meta name="version">` and the header badge), and
[scripts/release.py](scripts/release.py) is the only thing that edits either.
[tests/test_release.py](tests/test_release.py) fails if they drift. One run
refuses a dirty or stale checkout, runs the tests, drafts the `CHANGELOG.md`
section from the commits since the last `v*` tag, bumps the version, commits,
and writes an annotated tag `v<version>`.

Pushing that tag is what publishes:
[.github/workflows/release.yml](.github/workflows/release.yml) re-checks the
tag against `__version__`, re-runs the tests, builds a runnable single-file
`fsm-to-mp-<version>.pyz` (`python3 -m zipapp`, on 3.11), the static
`fsm-to-mp-web-<version>.zip` and a source `.zip`, and creates the GitHub
release with the notes taken from that same changelog section (found by its
`## <version> - <date>` heading). [.github/workflows/pages.yml](.github/workflows/pages.yml)
deploys `web/` to GitHub Pages on every push to `main`, which includes the
release commit (the `github-pages` environment rejects tags). There is no PyPI package.

When the user says "release":

1. Confirm the bump level (patch/minor/major) unless given.
2. Write the changelog section as prose, not a list of commit subjects, into a
   scratch file, and show it along with
   `python scripts/release.py <bump> --dry-run --notes-file <file>`.
3. `python scripts/release.py <bump> --notes-file <file> --push`.
4. `gh run watch` the `release` and `Deploy web converter` runs and report the
   GitHub release URL and the Pages URL.

Never tag, bump versions or edit `web/vendor/col.css` by hand. A failed
release workflow publishes nothing; fix it on `main` and cut the next patch,
never move or reuse a tag.

## The web-ui stylesheet

`web/vendor/col.css` is `col.css` from a release of the shared design system,
[web-ui](https://github.com/colonization-re/web-ui), frozen by
`web/vendor/col-css.json` (tag and sha256). Change it only with
`python scripts/vendor_css.py <tag>`, which verifies the download against the
release's `SHA256SUMS.txt`, and in its own commit before a release.
`python scripts/vendor_css.py --check` runs offline and is part of the tests.
fflate is pinned by exact version in the CDN import in `web/app.js`.
