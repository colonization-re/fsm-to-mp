"""Cut a release: run the tests, write the changelog, bump the version, tag it.

    python scripts/release.py patch              # 0.1.0 -> 0.1.1
    python scripts/release.py minor --push
    python scripts/release.py 1.0.0 --dry-run
    python scripts/release.py 0.1.0 --notes-file notes.md   # prose you wrote

One version covers both deliverables, the Python tool and the web converter.
It lives in `src/fsm_to_mp/__init__.py` (read by `pyproject.toml` and
`fsm-to-mp --version`) and is copied into `web/index.html`. This script is the
only thing that edits either.

What one run does, in order, stopping at the first thing that is wrong:

  1. refuses unless the checkout is clean, on the main branch, and not behind
     the remote (the release is pushed from here, so what is here has to be
     what everyone else has);
  2. runs the test suite, which also checks the web-ui pin and that the web
     page carries the package version;
  3. drafts the changelog section from the commits since the last `v*` tag and
     opens it in `$EDITOR` for you to turn into prose (or takes a section you
     have already written, with `--notes-file`);
  4. writes it into `CHANGELOG.md`, bumps the version in the package and the
     web page, and checks that the bumped package really reports it;
  5. commits the three files and writes an annotated tag `v<version>` carrying
     the section body.

Pushing that tag is what publishes the release: `.github/workflows/release.yml`
re-runs the tests, builds the downloads and creates the GitHub release from the
same changelog section; `.github/workflows/pages.yml` deploys the web converter.
This script pushes only when asked (`--push`), and otherwise prints the two
commands, plus how to undo the commit and the tag.
"""

from __future__ import annotations

import argparse
import datetime
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INIT = ROOT / "src" / "fsm_to_mp" / "__init__.py"
HTML = ROOT / "web" / "index.html"
CHANGELOG = ROOT / "CHANGELOG.md"
PROJECT_URL = "https://github.com/colonization-re/fsm-to-mp"
MAIN = "main"

VERSION_RE = re.compile(r'^__version__ = "(\d+\.\d+\.\d+)"$', re.M)
HTML_VERSION_RES = [
    (re.compile(r'<meta name="version" content="[^"]+">'), '<meta name="version" content="{v}">'),
    (re.compile(r"(<span[^>]*data-version>)v[^<]+(</span>)"), r"\g<1>v{v}\g<2>"),
]
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
# "feat: ...", "fix(web)!: ..." -- used only if the history happens to be
# written that way; plain subjects are listed under one heading instead.
CONVENTIONAL_RE = re.compile(r"^([a-z]+)(\([^)]*\))?(!)?: (.+)$")
SECTIONS = {
    "feat": "Added",
    "fix": "Fixed",
    "perf": "Changed",
    "refactor": "Changed",
    "docs": "Documentation",
    "test": "Tests",
    "build": "Housekeeping",
    "ci": "Housekeeping",
    "chore": "Housekeeping",
}
ORDER = ["Added", "Changed", "Fixed", "Documentation", "Tests", "Housekeeping", "Other"]

EDIT_HELP = """
<!-- Write the section above the way you want it read: this is what the tag
     message and the GitHub release will say. Commit subjects are a draft, not
     the release notes. Keep the `## <version> - <date>` heading line: the
     release workflow finds the section by it. Everything from this comment
     down is dropped. Save an empty file to abort the release. -->
"""

CHANGELOG_HEADER = """# Changelog

Every released version of `fsm-to-mp` (the Python tool and the web converter
ship together), newest first. Versions are
[semantic](https://semver.org/spec/v2.0.0.html): the major number moves when a
map converted by an older version would convert differently in a way that
breaks it, the minor when conversions or options are added, the patch for
fixes. Cut a release with `python scripts/release.py`.
"""


def fail(msg: str) -> None:
    print(f"release: {msg}", file=sys.stderr)
    sys.exit(2)


def git(*args: str) -> str:
    out = subprocess.run(["git", *args], cwd=ROOT, check=True, stdout=subprocess.PIPE)
    return out.stdout.decode("utf-8", "replace").strip()


def git_ok(*args: str) -> bool:
    return subprocess.run(["git", *args], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


# ---------------------------------------------------------------------- #
# versions


def current_version() -> str:
    match = VERSION_RE.search(INIT.read_text(encoding="utf-8"))
    if not match:
        fail(f'no `__version__ = "x.y.z"` line in {INIT.relative_to(ROOT)}')
    return match.group(1)


def parts(version: str) -> tuple[int, ...]:
    return tuple(int(p) for p in version.split("."))


def next_version(cur: str, spec: str) -> str:
    if SEMVER_RE.match(spec):
        return spec
    major, minor, patch = parts(cur)
    if spec == "major":
        return f"{major + 1}.0.0"
    if spec == "minor":
        return f"{major}.{minor + 1}.0"
    if spec == "patch":
        return f"{major}.{minor}.{patch + 1}"
    fail(f"{spec!r} is neither major, minor, patch nor an x.y.z version")


def write_version(new: str) -> None:
    text, n = VERSION_RE.subn(f'__version__ = "{new}"', INIT.read_text(encoding="utf-8"), count=1)
    if n != 1:
        fail(f"could not rewrite the version in {INIT.relative_to(ROOT)}")
    INIT.write_text(text, encoding="utf-8")

    html = HTML.read_text(encoding="utf-8")
    for pattern, repl in HTML_VERSION_RES:
        html, n = pattern.subn(repl.replace("{v}", new), html, count=1)
        if n != 1:
            fail(f"could not rewrite {pattern.pattern!r} in {HTML.relative_to(ROOT)}")
    HTML.write_text(html, encoding="utf-8")


# ---------------------------------------------------------------------- #
# preconditions


def check_tree(args: argparse.Namespace, version: str) -> str:
    if not git_ok("rev-parse", "--git-dir"):
        fail(f"{ROOT} is not a git checkout")
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    if branch != MAIN and not args.allow_branch:
        fail(f"on branch {branch}, not {MAIN} -- releases are cut from {MAIN} (--allow-branch to override)")
    dirty = git("status", "--porcelain")
    if dirty:
        fail(f"the checkout has uncommitted changes:\n{dirty}")
    tag = f"v{version}"
    if git_ok("rev-parse", "--verify", "--quiet", f"refs/tags/{tag}"):
        fail(f"tag {tag} already exists -- that version is released")

    if args.no_fetch:
        return branch
    if not git_ok("remote", "get-url", "origin"):
        print("release: no origin remote; skipping the up-to-date check")
        return branch
    print("release: fetching origin")
    if not git_ok("fetch", "--quiet", "origin", "--tags"):
        fail("git fetch origin failed (--no-fetch to skip the check)")
    remote = f"origin/{branch}"
    if not git_ok("rev-parse", "--verify", "--quiet", remote):
        return branch
    behind = git("rev-list", "--count", f"HEAD..{remote}")
    if behind != "0":
        fail(f"{remote} is {behind} commit(s) ahead of this checkout -- pull first")
    if git_ok("rev-parse", "--verify", "--quiet", f"refs/tags/{tag}"):
        fail(f"tag {tag} exists on origin -- that version is released")
    return branch


def run_tests() -> None:
    cmd = [sys.executable, "-m", "pytest", "-q"]
    print(f"release: {' '.join(cmd)}")
    if subprocess.run(cmd, cwd=ROOT).returncode != 0:
        fail("the tests failed -- not releasing")
    if subprocess.run([sys.executable, "-m", "fsm_to_mp", "--help"], cwd=ROOT, stdout=subprocess.DEVNULL).returncode != 0:
        fail("python -m fsm_to_mp --help failed -- not releasing")


# ---------------------------------------------------------------------- #
# changelog


def previous_tag() -> str | None:
    out = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0", "--match", "v[0-9]*"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if out.returncode != 0:
        return None
    return out.stdout.decode().strip() or None


def commits_since(tag: str | None) -> list[tuple[str, str]]:
    span = [f"{tag}..HEAD"] if tag else ["HEAD"]
    out = git("log", "--no-merges", "--reverse", "--pretty=%h\x1f%s", *span)
    commits = []
    for line in out.splitlines():
        if "\x1f" not in line:
            continue
        sha, subject = line.split("\x1f", 1)
        if subject.startswith("Release "):
            continue
        commits.append((sha, subject))
    return commits


def group(commits: list[tuple[str, str]]) -> dict[str, list[tuple[str, str]]]:
    """Group by conventional-commit type, or return one 'Other' bucket."""
    grouped: dict[str, list[tuple[str, str]]] = {}
    conventional = 0
    for sha, subject in commits:
        match = CONVENTIONAL_RE.match(subject)
        if match and match.group(1) in SECTIONS:
            conventional += 1
            heading = SECTIONS[match.group(1)]
            text = match.group(4) + (" (breaking)" if match.group(3) else "")
        else:
            heading = "Other"
            text = subject
        grouped.setdefault(heading, []).append((sha, text))
    if conventional < len(commits) / 2:
        return {"Other": commits}
    return grouped


def compare_link(prev: str | None, version: str) -> str:
    if prev:
        return f"[Compare with {prev}]({PROJECT_URL}/compare/{prev}...v{version})"
    return f"[Commits]({PROJECT_URL}/commits/v{version})"


def draft(version: str, date: str, commits: list[tuple[str, str]], prev: str | None) -> str:
    lines = [f"## {version} - {date}", ""]
    if not commits:
        lines += [f"- Nothing recorded since {prev or 'the first commit'}.", ""]
    else:
        grouped = group(commits)
        for heading in ORDER:
            if heading not in grouped:
                continue
            if list(grouped) != ["Other"]:
                lines += [f"### {heading}", ""]
            lines += [f"- {text} ({sha})" for sha, text in grouped[heading]]
            lines.append("")
    lines.append(compare_link(prev, version))
    return "\n".join(lines).rstrip() + "\n"


def notes_from(path: str, version: str, date: str, prev: str | None) -> str:
    """A section written by hand instead of drafted from the commits.

    The file is the body of the section; the heading and the compare link are
    added around it. A file that brings its own `## <version> - <date>` heading
    is taken exactly as it stands.
    """
    try:
        text = Path(path).read_text(encoding="utf-8").strip()
    except OSError as error:
        fail(f"cannot read {path}: {error}")
    if not text:
        fail(f"{path} is empty")
    if text.startswith("## "):
        heading = text.split("\n", 1)[0]
        if not heading.startswith(f"## {version} "):
            fail(f"{path} leads with {heading!r}; the release workflow looks for a '## {version} - <date>' heading")
        return text + "\n"
    return "\n".join([f"## {version} - {date}", "", text, "", compare_link(prev, version)]) + "\n"


def edit(text: str) -> str:
    editor = os.environ.get("EDITOR") or os.environ.get("VISUAL")
    if not editor:
        print("release: $EDITOR is not set; keeping the draft as it stands")
        return text
    fd, path = tempfile.mkstemp(prefix="fsm-to-mp-release-", suffix=".md")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text + EDIT_HELP)
        if subprocess.run(f"{editor} {path}", shell=True).returncode != 0:
            fail(f"{editor} exited non-zero -- nothing has been changed")
        edited = Path(path).read_text(encoding="utf-8")
    finally:
        os.unlink(path)
    edited = edited.split("<!--")[0].strip()
    if not edited:
        fail("the changelog section came back empty -- release aborted")
    return edited + "\n"


def prepend_changelog(section: str) -> None:
    old = CHANGELOG.read_text(encoding="utf-8") if CHANGELOG.exists() else CHANGELOG_HEADER
    head, sep, rest = old.partition("\n## ")
    body = head.rstrip() + "\n\n" + section.rstrip() + "\n"
    if sep:
        body += "\n## " + rest.lstrip("\n")
    CHANGELOG.write_text(body, encoding="utf-8")


# ---------------------------------------------------------------------- #


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="release.py",
        description="Cut an fsm-to-mp release: test, changelog, bump, tag.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="The tag is what publishes: pushing v<version> makes the release workflow build the "
        "downloads and write the release notes from CHANGELOG.md, and redeploys the web converter.",
    )
    parser.add_argument("version", help="major, minor, patch, or an exact x.y.z")
    parser.add_argument("--push", action="store_true", help="push the branch and the tag when everything is done")
    parser.add_argument("--dry-run", action="store_true", help="say what would happen; write nothing, tag nothing")
    parser.add_argument("--no-edit", action="store_true", help="keep the drafted changelog section as it is")
    parser.add_argument(
        "--notes-file",
        metavar="PATH",
        help="a changelog section you have written, in place of the drafted commit list (implies --no-edit)",
    )
    parser.add_argument("--skip-tests", action="store_true", help="do not run the test suite first")
    parser.add_argument("--no-fetch", action="store_true", help="do not fetch origin before checking the tree")
    parser.add_argument("--allow-branch", action="store_true", help=f"release from a branch other than {MAIN}")
    args = parser.parse_args(argv)

    cur = current_version()
    new = next_version(cur, args.version)
    if parts(new) < parts(cur):
        fail(f"{new} is older than the current {cur}")
    branch = check_tree(args, new)
    prev = previous_tag()
    commits = commits_since(prev)
    print(f"release: {cur} -> {new}, {len(commits)} commit(s) since {prev or 'the first commit'}")

    if args.skip_tests:
        print("release: skipping the tests (--skip-tests)")
    else:
        run_tests()

    date = datetime.date.today().isoformat()
    if args.notes_file:
        section = notes_from(args.notes_file, new, date, prev)
    else:
        section = draft(new, date, commits, prev)
        if not args.no_edit and not args.dry_run:
            section = edit(section)

    if args.dry_run:
        print("\nrelease: --dry-run, nothing written. The section would be:\n")
        print(section)
        print(
            f"release: would bump {INIT.relative_to(ROOT)} and {HTML.relative_to(ROOT)} to {new}, "
            f"commit them with CHANGELOG.md, and tag v{new}"
        )
        return 0

    prepend_changelog(section)
    write_version(new)
    reported = subprocess.run(
        [sys.executable, "-m", "fsm_to_mp", "--version"], cwd=ROOT, stdout=subprocess.PIPE
    ).stdout.decode().strip()
    if reported != f"fsm-to-mp {new}":
        fail(
            f"after the bump fsm-to-mp reports {reported!r}, not {'fsm-to-mp ' + new!r} -- "
            "the working tree is edited but nothing is committed"
        )

    git("add", "CHANGELOG.md", str(INIT.relative_to(ROOT)), str(HTML.relative_to(ROOT)))
    git("commit", "-m", f"Release {new}")
    fd, path = tempfile.mkstemp(prefix="fsm-to-mp-tag-")
    try:
        message = section.split("\n", 1)[1].strip()
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(f"fsm-to-mp {new}\n\n{message}\n")
        git("tag", "-a", f"v{new}", "-F", path)
    finally:
        os.unlink(path)
    print(f"release: committed and tagged v{new}")

    if args.push:
        git("push", "origin", branch)
        git("push", "origin", f"v{new}")
        print(f"release: pushed. The release workflow is building {PROJECT_URL}/releases")
    else:
        print(
            "\nNothing is pushed yet. To publish:\n"
            f"    git push origin {branch}\n"
            f"    git push origin v{new}\n"
            "\nTo undo, before pushing:\n"
            f"    git tag -d v{new} && git reset --hard HEAD~1"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
