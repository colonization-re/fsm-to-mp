from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from fsm_to_mp import __version__
from fsm_to_mp.convert import convert_map, encode_plane0
from fsm_to_mp.fsm.reader import read_fsm, summarize_fsm
from fsm_to_mp.mp.reader import read_mp
from fsm_to_mp.mp.writer import write_mp
from fsm_to_mp.validation import validate_written_mp, warning_counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert FreeCol .fsm maps to Colonization .MP maps.")
    parser.add_argument("input", type=Path, help="FreeCol .fsm input map")
    parser.add_argument("output", type=Path, nargs="?", help="Colonization .MP output path")
    parser.add_argument("--summary", action="store_true", help="print a JSON summary of the .fsm and exit")
    parser.add_argument("--warnings", choices=("summary", "all", "none"), default="summary")
    parser.add_argument("--version", action="version", version=f"fsm-to-mp {__version__}")
    args = parser.parse_args(argv)

    if args.summary:
        print(json.dumps(summarize_fsm(args.input), indent=2, sort_keys=True))
        return 0

    if args.output is None:
        parser.error("output is required unless --summary is used")

    source = read_fsm(args.input)
    result = convert_map(source)
    plane0 = encode_plane0(result.map)
    write_mp(args.output, result.map, plane0)
    validate_written_mp(read_mp(args.output), source.width, source.height)

    if args.warnings == "summary":
        counts = warning_counts(result)
        if counts:
            print(json.dumps(counts, indent=2, sort_keys=True), file=sys.stderr)
    elif args.warnings == "all":
        for warning in result.warnings:
            print(f"{warning.x},{warning.y}: {warning.code}: {warning.message}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
