import pytest

from scraper.models import Status
from scraper.tasks import scrape_page
from scraper.tests.factories import PageFactory

pytestmark = pytest.mark.django_db


def test_scrape_page_transitions_pending_to_success():
    page = PageFactory(status=Status.PENDING)

    scrape_page(page.id)

    page.refresh_from_db()
    assert page.status == Status.SUCCESS
    assert page.started_at is not None
    assert page.finished_at is not None
    transitions = list(
        page.status_events.order_by("occurred_at").values_list("from_status", "to_status")
    )
    assert transitions == [
        (Status.PENDING, Status.IN_PROGRESS),
        (Status.IN_PROGRESS, Status.SUCCESS),
    ]


def test_scrape_page_is_a_noop_if_not_pending():
    page = PageFactory(status=Status.CANCELLED)

    scrape_page(page.id)

    page.refresh_from_db()
    assert page.status == Status.CANCELLED
    assert page.status_events.count() == 0


def test_scrape_page_runs_synchronously_via_delay_in_eager_mode():
    page = PageFactory(status=Status.PENDING)

    result = scrape_page.delay(page.id)

    assert result.successful()
    page.refresh_from_db()
    assert page.status == Status.SUCCESS
