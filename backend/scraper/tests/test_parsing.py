from scraper.parsing import NAME_HTML_MAX_LENGTH, parse_page


def test_parse_page_extracts_title_and_link():
    html = """
    <html><head><title>My Page</title></head>
    <body><a href="https://other.example/page">Visit</a></body></html>
    """

    title, links = parse_page("https://example.com/", html)

    assert title == "My Page"
    assert links == [{"href": "https://other.example/page", "name_html": "Visit"}]


def test_parse_page_resolves_relative_href_against_base_url():
    html = '<html><body><a href="/products/1">Product</a></body></html>'

    _, links = parse_page("https://example.com/shop", html)

    assert links[0]["href"] == "https://example.com/products/1"


def test_parse_page_captures_nested_html_in_link_body():
    html = '<html><body><a href="/x"><img src="pic.png" alt="pic"></a></body></html>'

    _, links = parse_page("https://example.com/", html)

    assert links[0]["name_html"] == '<img alt="pic" src="pic.png"/>'


def test_parse_page_truncates_long_link_body():
    html = f'<html><body><a href="/x">{"a" * 600}</a></body></html>'

    _, links = parse_page("https://example.com/", html)

    assert len(links[0]["name_html"]) == NAME_HTML_MAX_LENGTH + 1
    assert links[0]["name_html"].endswith("…")


def test_parse_page_skips_anchors_without_href():
    html = '<html><body><a name="top">No href</a></body></html>'

    _, links = parse_page("https://example.com/", html)

    assert links == []


def test_parse_page_falls_back_to_url_when_title_is_missing():
    html = "<html><body>No title here</body></html>"

    title, _ = parse_page("https://example.com/no-title", html)

    assert title == "https://example.com/no-title"


def test_parse_page_falls_back_to_url_when_title_is_empty():
    html = "<html><head><title></title></head><body></body></html>"

    title, _ = parse_page("https://example.com/empty-title", html)

    assert title == "https://example.com/empty-title"
