from excel2web.rag import RagIndex, normalize_name


def test_normalize_name():
    assert normalize_name("  ユーロジン１ｍｇ錠 ") == normalize_name("ユーロジン１ｍｇ錠")


def test_rag_exact_match():
    idx = RagIndex(name_to_price={normalize_name("ユーロジン１ｍｇ錠"): "6.1"}, yj_to_price={})
    assert idx.name_to_price[normalize_name("ユーロジン１ｍｇ錠")] == "6.1"
