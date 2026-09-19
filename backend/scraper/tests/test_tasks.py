from unittest.mock import patch

import pytest

from scraper.fetching import FetchError
from scraper.models import Link, Status
from scraper.tasks import scrape_page
from scraper.tests.factories import LinkFactory, PageFactory

pytestmark = pytest.mark.django_db


def _mock_scrape(title="Example", links=None):
    links = links if links is not None else [{"href": "https://example.com/a", "name_html": "A"}]
    return patch.multiple(
        "scraper.tasks",
        fetch_html=lambda url: (url, b"<html></html>"),
        parse_page=lambda base_url, content: (title, links),
    )


def test_scrape_page_transitions_pending_to_success():
    page = PageFactory(status=Status.PENDING)

    with _mock_scrape(title="Example Domain"):
        scrape_page(page.id)

    page.refresh_from_db()
    assert page.status == Status.SUCCESS
    assert page.title == "Example Domain"
    assert page.started_at is not None
    assert page.finished_at is not None
    transitions = list(
        page.status_events.order_by("occurred_at").values_list("from_status", "to_status")
    )
    assert transitions == [
        (Status.PENDING, Status.IN_PROGRESS),
        (Status.IN_PROGRESS, Status.SUCCESS),
    ]


def test_scrape_page_creates_links():
    page = PageFactory(status=Status.PENDING)
    links = [
        {"href": "https://example.com/a", "name_html": "A"},
        {"href": "https://example.com/b", "name_html": "B"},
    ]

    with _mock_scrape(links=links):
        scrape_page(page.id)

    saved = list(page.links.order_by("href").values_list("href", "name_html"))
    assert saved == [("https://example.com/a", "A"), ("https://example.com/b", "B")]


def test_scrape_page_replaces_links_wholesale_on_rerun():
    page = PageFactory(status=Status.PENDING)
    stale = LinkFactory(page=page, href="https://example.com/stale")

    with _mock_scrape(links=[{"href": "https://example.com/fresh", "name_html": "Fresh"}]):
        scrape_page(page.id)

    hrefs = list(page.links.values_list("href", flat=True))
    assert hrefs == ["https://example.com/fresh"]
    assert not Link.objects.filter(id=stale.id).exists()


def test_scrape_page_is_a_noop_if_not_pending():
    page = PageFactory(status=Status.CANCELLED)

    scrape_page(page.id)

    page.refresh_from_db()
    assert page.status == Status.CANCELLED
    assert page.status_events.count() == 0


def test_scrape_page_marks_failed_on_fetch_error():
    page = PageFactory(status=Status.PENDING)

    with patch("scraper.tasks.fetch_html", side_effect=FetchError("boom")):
        scrape_page(page.id)

    page.refresh_from_db()
    assert page.status == Status.FAILED
    assert page.error_message == "boom"
    transitions = list(
        page.status_events.order_by("occurred_at").values_list("from_status", "to_status")
    )
    assert transitions == [
        (Status.PENDING, Status.IN_PROGRESS),
        (Status.IN_PROGRESS, Status.FAILED),
    ]


def test_scrape_page_runs_synchronously_via_delay_in_eager_mode():
    page = PageFactory(status=Status.PENDING)

    with _mock_scrape():
        result = scrape_page.delay(page.id)

    assert result.successful()
    page.refresh_from_db()
    assert page.status == Status.SUCCESS
