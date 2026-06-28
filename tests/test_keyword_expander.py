import pytest

from pixharbor.keyword_expander import expand_keywords, normalize_keyword


def test_normalize_keyword() -> None:
    assert normalize_keyword("  cooling   tower  ") == "cooling tower"


def test_expand_keywords_uses_templates_and_limit() -> None:
    assert expand_keywords("cooling tower", limit=3) == [
        "cooling tower",
        "industrial cooling tower",
        "power plant cooling tower",
    ]


def test_expand_keywords_adds_domain_terms() -> None:
    results = expand_keywords("cooling tower", limit=20)

    assert "menara pendingin" in results
    assert "hyperbolic cooling tower" in results


def test_expand_keywords_filters_negative_terms() -> None:
    results = expand_keywords("cooling tower", limit=10, negative_keywords=["factory"])

    assert "cooling tower factory" not in results


def test_expand_keywords_rejects_empty_keyword() -> None:
    with pytest.raises(ValueError):
        expand_keywords("   ")
