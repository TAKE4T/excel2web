from excel2web.yakka import extract_price_text


def test_extract_price_text_from_simple_span():
    html = """
    <html><body>
      <span class='yakka-price'>100円</span>
    </body></html>
    """
    assert extract_price_text(html) == "100円"


def test_extract_price_text_from_whole_text_fallback():
    html = """
    <html><body>
      <div>薬価は 1,234円 です</div>
    </body></html>
    """
    assert extract_price_text(html) == "1,234円"
