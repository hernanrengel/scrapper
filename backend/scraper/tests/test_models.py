import pytest
from django.db import IntegrityError

from scraper.models import Link, PageStatusEvent, Status
from scraper.tests.factories import LinkFactory, PageFactory, PageStatusEventFactory

pytestmark = pytest.mark.django_db


def test_page_default_status_is_pending():
    page = PageFactory()

    assert page.status == Status.PENDING


def test_normalized_url_must_be_unique():
    PageFactory(normalized_url="https://example.com/dup")

    with pytest.raises(IntegrityError):
        PageFactory(normalized_url="https://example.com/dup")


def test_deleting_page_cascades_links_and_status_events():
    page = PageFactory()
    LinkFactory(page=page)
    PageStatusEventFactory(page=page)

    page.delete()

    assert Link.objects.count() == 0
    assert PageStatusEvent.objects.count() == 0


def test_page_status_event_records_transition():
    page = PageFactory()
    event = PageStatusEventFactory(
        page=page, from_status=Status.PENDING, to_status=Status.IN_PROGRESS
    )

    assert event.from_status == Status.PENDING
    assert event.to_status == Status.IN_PROGRESS
    assert page.status_events.count() == 1
