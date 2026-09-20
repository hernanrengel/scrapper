from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from scraper.models import Status
from scraper.tests.factories import PageFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return APIClient()


def _mock_scrape():
    return patch.multiple(
        "scraper.tasks",
        fetch_html=lambda url: (url, b"<html></html>"),
        parse_page=lambda base_url, content: ("Example", []),
    )


@pytest.mark.parametrize("previous_status", [Status.SUCCESS, Status.FAILED, Status.CANCELLED])
def test_rescrape_resets_from_any_terminal_state(
    client, previous_status, django_capture_on_commit_callbacks
):
    page = PageFactory(status=previous_status, error_message="old error")

    with _mock_scrape(), django_capture_on_commit_callbacks(execute=True):
        response = client.post(f"/api/v1/pages/{page.id}/rescrape/")

    assert response.status_code == 202
    transitions = list(
        page.status_events.order_by("occurred_at").values_list("from_status", "to_status")
    )
    assert transitions[0] == (previous_status, Status.PENDING)
    page.refresh_from_db()
    # The mocked scrape ran synchronously (eager + captured on_commit), so by
    # now the page has already moved past "pending" again.
    assert page.status == Status.SUCCESS
    assert page.error_message is None


def test_rescrape_rejects_an_in_progress_page(client):
    page = PageFactory(status=Status.IN_PROGRESS)

    response = client.post(f"/api/v1/pages/{page.id}/rescrape/")

    assert response.status_code == 409
    page.refresh_from_db()
    assert page.status == Status.IN_PROGRESS
    assert page.status_events.count() == 0


def test_rescrape_404_for_unknown_page(client):
    response = client.post("/api/v1/pages/00000000-0000-0000-0000-000000000000/rescrape/")

    assert response.status_code == 404


def test_concurrent_rescrapes_only_one_wins(client, django_capture_on_commit_callbacks):
    page = PageFactory(status=Status.FAILED)

    with _mock_scrape(), django_capture_on_commit_callbacks(execute=True):
        first_response = client.post(f"/api/v1/pages/{page.id}/rescrape/")
    assert first_response.status_code == 202

    stale_read = PageFactory.build(id=page.id, status=Status.FAILED)
    with patch("scraper.views.get_object_or_404", return_value=stale_read):
        second_response = client.post(f"/api/v1/pages/{page.id}/rescrape/")

    assert second_response.status_code == 409
