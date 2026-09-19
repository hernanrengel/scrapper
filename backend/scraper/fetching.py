from urllib.parse import urljoin

import requests

from scraper.ssrf import assert_host_is_safe

MAX_REDIRECTS = 3
MAX_RESPONSE_BYTES = 5 * 1024 * 1024
REQUEST_TIMEOUT = (5, 15)
USER_AGENT = "scrapper/1.0"


class FetchError(Exception):
    pass


def fetch_html(url):
    current_url = url
    redirects_followed = 0

    while True:
        assert_host_is_safe(current_url)

        try:
            response = requests.get(
                current_url,
                timeout=REQUEST_TIMEOUT,
                stream=True,
                allow_redirects=False,
                headers={"User-Agent": USER_AGENT},
            )
        except requests.RequestException as exc:
            raise FetchError(f"Request failed: {exc}") from exc

        if response.is_redirect:
            response.close()
            if redirects_followed >= MAX_REDIRECTS:
                raise FetchError("Too many redirects")
            location = response.headers.get("Location")
            if not location:
                raise FetchError("Redirect response missing a Location header")
            redirects_followed += 1
            current_url = urljoin(current_url, location)
            continue

        if not response.ok:
            response.close()
            raise FetchError(f"Unexpected status code: {response.status_code}")

        content_type = response.headers.get("Content-Type", "")
        if not content_type.startswith("text/html"):
            response.close()
            raise FetchError(f"Unsupported content type: {content_type or '(missing)'}")

        content = _read_capped(response)
        return current_url, content


def _read_capped(response):
    chunks = []
    total = 0
    for chunk in response.iter_content(chunk_size=8192):
        total += len(chunk)
        if total > MAX_RESPONSE_BYTES:
            response.close()
            raise FetchError("Response exceeded the maximum allowed size")
        chunks.append(chunk)
    return b"".join(chunks)
