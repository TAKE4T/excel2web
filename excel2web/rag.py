from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class RagIndex:
    """In-memory index built from local files.

    key: normalized drug/product name (品名)
    value: price (薬価)
    """

    name_to_price: dict[str, str]


def normalize_name(name: str) -> str:
    return "".join(str(name).strip().split()).lower()


def build_rag_index(
    rag_dir: str | Path,
    *,
    sheet_name: str | int = 0,
    name_column: str = "品名",
    price_column: str = "薬価",
) -> RagIndex:
    rag_path = Path(rag_dir)
    if not rag_path.exists() or not rag_path.is_dir():
        return RagIndex(name_to_price={})

    mapping: dict[str, str] = {}

    for xlsx in sorted(rag_path.glob("*.xlsx")):
        df = pd.read_excel(xlsx, sheet_name=sheet_name, header=0)
        if name_column not in df.columns or price_column not in df.columns:
            # Skip unknown format
            continue

        # Keep first occurrence (latest file order wins only if key not present)
        for _, row in df[[name_column, price_column]].dropna().iterrows():
            k = normalize_name(row[name_column])
            if not k:
                continue
            if k in mapping:
                continue
            mapping[k] = str(row[price_column]).strip()

    return RagIndex(name_to_price=mapping)
