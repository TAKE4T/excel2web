# excel2web

ExcelファイルのA列にある薬品名を読み取り、`https://yakka-search.com/` から薬価らしき値を検索してB列に書き込み、別名でExcelを出力するツールです。

> 注意: 本プロジェクトのスクレイピングは対象サイトの利用規約/robots.txt/負荷に配慮してください。HTML構造が変わると取得できなくなる可能性があります。

## できること

- 入力Excel（A列=薬品名）→ 出力Excel（B列=取得結果）
- タイムアウト、リトライ、簡易レート制御
- 取得失敗時は `Not Found` / `Error` を出力

## セットアップ

Python 3.10+ を想定。

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
```

## 使い方

```bash
excel2web --input input.xlsx --output output.xlsx
```

### ローカルの薬価マスタ（RAG）を優先したい場合

このリポジトリには `RAG/` に薬価マスタExcel（例: `tp*.xlsx`）を置けます。
`--rag-dir` を指定すると、まずRAGから品名一致を探し、見つからない場合のみWeb検索します。

```bash
excel2web --input input.xlsx --output output.xlsx --rag-dir RAG
```

### YJコードで薬価を転記したい場合（A列→D列）

- 入力: `input.xlsx` の A列 = YJコード
- 出力: `output.xlsx` の D列 = 薬価（RAGから転記）

```bash
excel2web --mode yj --input input.xlsx --output output.xlsx --rag-dir RAG
```

- `--sheet` でシート名/番号を指定できます。
- `--column` で薬品名の列（0始まり）を指定できます（既定 0 = A列）。

## 開発

```bash
pip install -e '.[dev]'
pytest
```

## 免責

本ツールの出力は参考情報です。正確性は保証しません。
