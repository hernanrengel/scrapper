import pytest

from scraper.normalization import normalize_url


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://Example.com/path", "https://example.com/path"),
        ("https://example.com/path/", "https://example.com/path"),
        ("https://example.com", "https://example.com/"),
        ("https://example.com/", "https://example.com/"),
        ("https://example.com:443/path", "https://example.com/path"),
        ("http://example.com:80/path", "http://example.com/path"),
        ("https://example.com:8443/path", "https://example.com:8443/path"),
        ("https://example.com/path#section", "https://example.com/path"),
        ("https://example.com/path?", "https://example.com/path"),
        ("https://example.com/Path", "https://example.com/Path"),
    ],
)
def test_normalize_url(url, expected):
    assert normalize_url(url) == expected


def test_different_query_strings_are_not_equal():
    assert normalize_url("https://example.com/page?a=1") != normalize_url(
        "https://example.com/page?a=2"
    )


def test_path_case_is_preserved_and_distinguishes_urls():
    assert normalize_url("https://example.com/Page") != normalize_url("https://example.com/page")
