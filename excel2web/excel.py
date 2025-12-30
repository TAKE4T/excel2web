from __future__ import annotations

from dataclasses import dataclass
import sys

import pandas as pd

from .rag import RagIndex, normalize_name
from .yakka import YakkaClient


@dataclass(frozen=True)
class ProcessOptions:
    sheet: str | int | None = 0
    column: int = 0  # 0-based; 0 means column A


def transfer_price_by_yj_code(
    input_file: str,
    output_file: str,
    *,
    sheet: str | int | None = 0,
    yj_column: int = 0,
    price_column: int = 3,  # D列
    rag_index: RagIndex,
) -> None:
    """Transfer price from local RAG index by YJ code.

    - input A列（0）: YJコード
    - output D列（3）: 薬価
    """

    df = pd.read_excel(input_file, header=None, sheet_name=sheet)

    out: list[str] = []
    for v in df[yj_column].tolist():
        if pd.isna(v):
            out.append("")
            continue
        yj = str(v).strip()
        if not yj or yj.lower() == "yjコード":
            out.append("薬価(円)")
            continue

        out.append(rag_index.yj_to_price.get(yj, ""))

    df[price_column] = out
    df.to_excel(output_file, index=False, header=False)


def process_excel(
    input_file: str,
    output_file: str,
    *,
    options: ProcessOptions | None = None,
    client: YakkaClient | None = None,
    rag_index: RagIndex | None = None,
) -> None:
    """Read Excel, fetch prices, and write results.

    Input:
      - input_file: path to .xlsx
      - output_file: path to .xlsx

    Behavior:
      - Reads the specified `sheet`
      - Reads drug names from `column`
      - Writes fetched price texts into the next column (column+1)
    """

    options = options or ProcessOptions()
    client = client or YakkaClient()
    rag_index = rag_index or RagIndex(name_to_price={}, yj_to_price={})

    df = pd.read_excel(input_file, header=None, sheet_name=options.sheet)

    prices: list[str] = []
    for value in df[options.column].tolist():
        if pd.isna(value):
            prices.append("")
            continue
        drug_name = str(value).strip()
        if not drug_name:
            prices.append("")
            continue

        # Prefer local RAG master (exact match after normalization)
        rag_key = normalize_name(drug_name)
        if rag_key in rag_index.name_to_price:
            prices.append(rag_index.name_to_price[rag_key])
            continue

        try:
            result = client.search_price_text(drug_name)
            prices.append(result.price_text)
        except Exception as e:
            print(f"[excel2web] failed for '{drug_name}': {e}", file=sys.stderr)
            prices.append("Error")

    df[options.column + 1] = prices
    df.to_excel(output_file, index=False, header=False)
