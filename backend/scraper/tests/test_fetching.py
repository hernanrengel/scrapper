from unittest.mock import patch

import pytest
import responses

from scraper.fetching import FetchError, fetch_html
from scraper.ssrf import BlockedHostError


@pytest.fixture(autouse=True)
def bypass_ssrf_check(monkeypatch):
    monkeypatch.setattr("scraper.fetching.assert_host_is_safe", lambda url: None)


@responses.activate
def test_fetch_html_happy_path():
    responses.add(
        responses.GET,
        "https://example.com/",
        body="<html><title>Hi</title></html>",
        status=200,
        content_type="text/html",
    )

    final_url, content = fetch_html("https://example.com/")

    assert final_url == "https://example.com/"
    assert b"<title>Hi</title>" in content


@responses.activate
def test_fetch_html_follows_redirects_within_limit():
    responses.add(
        responses.GET,
        "https://example.com/a",
        status=302,
        headers={"Location": "https://example.com/b"},
    )
    responses.add(
        responses.GET,
        "https://example.com/b",
        body="<html></html>",
        status=200,
        content_type="text/html",
    )

    final_url, _ = fetch_html("https://example.com/a")

    assert final_url == "https://example.com/b"


@responses.activate
def test_fetch_html_fails_after_too_many_redirects():
    for n in range(1, 5):
        responses.add(
            responses.GET,
            f"https://example.com/{n}",
            status=302,
            headers={"Location": f"https://example.com/{n + 1}"},
        )

    with pytest.raises(FetchError):
        fetch_html("https://example.com/1")


@responses.activate
def test_fetch_html_rejects_non_html_content_type():
    responses.add(
        responses.GET,
        "https://example.com/file.png",
        body=b"binary",
        status=200,
        content_type="image/png",
    )

    with pytest.raises(FetchError):
        fetch_html("https://example.com/file.png")


@responses.activate
def test_fetch_html_rejects_non_2xx_status():
    responses.add(responses.GET, "https://example.com/missing", status=404)

    with pytest.raises(FetchError):
        fetch_html("https://example.com/missing")


@responses.activate
def test_fetch_html_rejects_oversized_response():
    huge_body = b"a" * (6 * 1024 * 1024)
    responses.add(
        responses.GET,
        "https://example.com/huge",
        body=huge_body,
        status=200,
        content_type="text/html",
    )

    with pytest.raises(FetchError):
        fetch_html("https://example.com/huge")


@responses.activate
def test_fetch_html_blocks_a_redirect_target_pointing_at_a_private_ip():
    calls = []

    def fake_assert_host_is_safe(url):
        calls.append(url)
        if len(calls) == 2:
            raise BlockedHostError("blocked")

    responses.add(
        responses.GET,
        "https://example.com/a",
        status=302,
        headers={"Location": "http://169.254.169.254/secret"},
    )

    with patch("scraper.fetching.assert_host_is_safe", side_effect=fake_assert_host_is_safe):
        with pytest.raises(BlockedHostError):
            fetch_html("https://example.com/a")

    assert calls == ["https://example.com/a", "http://169.254.169.254/secret"]
    # The redirect target was never actually requested over HTTP.
    assert len(responses.calls) == 1
