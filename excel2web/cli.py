from __future__ import annotations

import argparse

from .excel import ProcessOptions, process_excel


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Fetch yakka price text for drug names in Excel.")
    p.add_argument("--input", required=True, help="Input .xlsx file")
    p.add_argument("--output", required=True, help="Output .xlsx file")
    p.add_argument(
        "--sheet",
        default="0",
        help="Sheet name or index (default: 0). If int-like, treated as index.",
    )
    p.add_argument(
        "--column",
        type=int,
        default=0,
        help="0-based column index for drug names (default: 0 => column A)",
    )
    return p


def _parse_sheet(value: str):
    try:
        return int(value)
    except ValueError:
        return value


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    options = ProcessOptions(sheet=_parse_sheet(args.sheet), column=args.column)
    process_excel(args.input, args.output, options=options)
    return 0
