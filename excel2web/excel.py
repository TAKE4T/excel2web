from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .yakka import YakkaClient


@dataclass(frozen=True)
class ProcessOptions:
    sheet: str | int | None = 0
    column: int = 0  # 0-based; 0 means column A


def process_excel(
    input_file: str,
    output_file: str,
    *,
    options: ProcessOptions | None = None,
    client: YakkaClient | None = None,
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

        try:
            result = client.search_price_text(drug_name)
            prices.append(result.price_text)
        except Exception:
            prices.append("Error")

    df[options.column + 1] = prices
    df.to_excel(output_file, index=False, header=False)
