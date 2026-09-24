# Changelog

Every released version of `fsm-to-mp` (the Python tool and the web converter
ship together), newest first. Versions are
[semantic](https://semver.org/spec/v2.0.0.html): the major number moves when a
map converted by an older version would convert differently in a way that
breaks it, the minor when conversions or options are added, the patch for
fixes. Cut a release with `python scripts/release.py`.

## 0.1.1 - 2026-09-24

Release tooling only; the converter, the command-line tool and the web page
behave exactly as in 0.1.0.

The web converter is now deployed from `main` alone. In 0.1.0 the Pages
workflow also ran on the release tag, which the `github-pages` environment
rejects, so every release showed a failed deploy even though the site had
already been updated from `main`.

[Compare with v0.1.0](https://github.com/colonization-re/fsm-to-mp/compare/v0.1.0...v0.1.1)

## 0.1.0 - 2026-09-24

First release. `fsm-to-mp` converts FreeCol map-editor saves (`.fsm`) into the
original *Sid Meier's Colonization* `.MP` map format, as a Python command-line
tool and as a browser page. Python 3.11+, stdlib only, no dependencies.

```sh
python3 fsm-to-mp-0.1.0.pyz map.fsm out.MP
python3 fsm-to-mp-0.1.0.pyz --summary map.fsm
```

The web converter does the same entirely in the browser — the map never leaves
your machine: <https://colonization-re.github.io/fsm-to-mp/>.
`fsm-to-mp-web-0.1.0.zip` is the same static page for hosting yourself.

### What converts

Every FreeCol Classic terrain type maps to its Colonization terrain byte, with
hills and mountains, forests, and minor and major rivers. The output is written
as a three-plane `.MP` file and read back to validate it before the tool
reports success.

Anything original Colonization cannot represent exactly is converted to the
nearest thing and reported as a warning rather than dropped silently: lakes
become ocean, great rivers become savannah with a major river, and native
settlements, resources, regions and river connection styles are not carried
over. `docs/conversion.md` lists every rule.

### Downloads

- `fsm-to-mp-0.1.0.pyz` — the tool as one runnable file
- `fsm-to-mp-web-0.1.0.zip` — the static web converter
- `fsm-to-mp-0.1.0.zip` — the source, with docs and tests

[Commits](https://github.com/colonization-re/fsm-to-mp/commits/v0.1.0)
