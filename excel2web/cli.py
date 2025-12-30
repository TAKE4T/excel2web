from __future__ import annotations

import argparse

from .excel import ProcessOptions, process_excel, transfer_price_by_yj_code
from .rag import build_rag_index


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Fetch yakka price text for drug names in Excel.")
    p.add_argument(
        "--mode",
        default="name",
        choices=["name", "yj"],
        help="name: A列=薬品名→B列に薬価。 yj: A列=YJコード→D列にRAG薬価転記。",
    )
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
    p.add_argument(
        "--rag-dir",
        default=None,
        help="Directory that contains local master Excel files (default: disabled).",
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

    rag_index = build_rag_index(args.rag_dir) if args.rag_dir else None

    if args.mode == "yj":
        if rag_index is None:
            raise SystemExit("--mode yj requires --rag-dir")
        transfer_price_by_yj_code(
            args.input,
            args.output,
            sheet=_parse_sheet(args.sheet),
            yj_column=args.column,
            price_column=3,
            rag_index=rag_index,
        )
        return 0

    options = ProcessOptions(sheet=_parse_sheet(args.sheet), column=args.column)
    process_excel(args.input, args.output, options=options, rag_index=rag_index)
    return 0
