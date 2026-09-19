from urllib.parse import urljoin

from bs4 import BeautifulSoup

NAME_HTML_MAX_LENGTH = 500


def parse_page(base_url, html_content):
    soup = BeautifulSoup(html_content, "lxml")

    title = None
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    if not title:
        title = base_url

    links = [_extract_link(base_url, tag) for tag in soup.find_all("a", href=True)]

    return title, links


def _extract_link(base_url, tag):
    href = urljoin(base_url, tag["href"])
    name_html = "".join(str(child) for child in tag.contents)
    if len(name_html) > NAME_HTML_MAX_LENGTH:
        name_html = name_html[:NAME_HTML_MAX_LENGTH] + "…"
    return {"href": href, "name_html": name_html}
