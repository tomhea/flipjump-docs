"""CLI: dump the parsed STL index as JSON.

Usage:
    python -m fj_stl_extract --dump-json
    python -m fj_stl_extract --dump-json --stl-root path/to/flipjump/stl --output index.json
    python -m fj_stl_extract --dump-json --pretty
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .pipeline import extract_stl, to_json_dict


def _default_stl_root() -> Path:
    """Best-effort default: vendor/flip-jump/flipjump/stl/ relative to
    this package's repo. Walk up from __file__ looking for `vendor`."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "vendor" / "flip-jump" / "flipjump" / "stl"
        if candidate.is_dir():
            return candidate
    # Fall back to a relative path — argparse will surface the missing
    # file via extract_stl's FileNotFoundError.
    return Path("vendor/flip-jump/flipjump/stl").resolve()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="fj_stl_extract")
    p.add_argument("--dump-json", action="store_true",
                   help="Parse the STL and dump the index as JSON.")
    p.add_argument("--stl-root", type=Path, default=_default_stl_root(),
                   help="Path to the flipjump/stl/ directory inside a "
                        "flip-jump checkout. Defaults to the in-tree submodule.")
    p.add_argument("--output", "-o", type=Path,
                   help="Write JSON to this file instead of stdout.")
    p.add_argument("--pretty", action="store_true",
                   help="Pretty-print the JSON output (indent=2).")
    args = p.parse_args(argv)

    if not args.dump_json:
        p.error("No action specified. Pass --dump-json.")

    try:
        index = extract_stl(args.stl_root)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    data = to_json_dict(index)
    text = json.dumps(data, indent=2 if args.pretty else None,
                      sort_keys=False, ensure_ascii=False)

    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
