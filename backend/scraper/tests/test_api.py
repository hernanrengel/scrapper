import pytest
from rest_framework.test import APIClient

from scraper.models import Status
from scraper.tests.factories import LinkFactory, PageFactory, PageStatusEventFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return APIClient()


def test_list_pages_includes_links_count(client):
    empty_page = PageFactory()
    busy_page = PageFactory()
    LinkFactory.create_batch(3, page=busy_page)

    response = client.get("/api/v1/pages/")

    assert response.status_code == 200
    by_id = {row["id"]: row for row in response.data["results"]}
    assert by_id[str(empty_page.id)]["links_count"] == 0
    assert by_id[str(busy_page.id)]["links_count"] == 3


def test_list_pages_is_paginated(client):
    PageFactory.create_batch(15)

    response = client.get("/api/v1/pages/")

    assert response.status_code == 200
    assert response.data["count"] == 15
    assert len(response.data["results"]) == 10


def test_retrieve_page_detail(client):
    page = PageFactory(status=Status.FAILED, error_message="timed out")

    response = client.get(f"/api/v1/pages/{page.id}/")

    assert response.status_code == 200
    assert response.data["status"] == Status.FAILED
    assert response.data["error_message"] == "timed out"
    assert "links_count" not in response.data


def test_retrieve_page_detail_404_for_unknown_id(client):
    response = client.get("/api/v1/pages/00000000-0000-0000-0000-000000000000/")

    assert response.status_code == 404


def test_list_links_for_a_page_is_paginated(client):
    page = PageFactory()
    other_page = PageFactory()
    LinkFactory.create_batch(2, page=page)
    LinkFactory(page=other_page)

    response = client.get(f"/api/v1/pages/{page.id}/links/")

    assert response.status_code == 200
    assert response.data["count"] == 2


def test_links_404_for_unknown_page(client):
    response = client.get("/api/v1/pages/00000000-0000-0000-0000-000000000000/links/")

    assert response.status_code == 404


def test_status_events_are_newest_first(client):
    page = PageFactory()
    PageStatusEventFactory(page=page, from_status=None, to_status=Status.PENDING)
    PageStatusEventFactory(page=page, from_status=Status.PENDING, to_status=Status.IN_PROGRESS)

    response = client.get(f"/api/v1/pages/{page.id}/status-events/")

    assert response.status_code == 200
    assert [event["to_status"] for event in response.data] == [
        Status.IN_PROGRESS,
        Status.PENDING,
    ]


def test_status_events_404_for_unknown_page(client):
    response = client.get("/api/v1/pages/00000000-0000-0000-0000-000000000000/status-events/")

    assert response.status_code == 404
