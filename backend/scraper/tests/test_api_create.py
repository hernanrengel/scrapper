from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

import scraper.views as views_module
from scraper.models import Page, Status
from scraper.tests.factories import PageFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return APIClient()


def test_create_page_happy_path(client, django_capture_on_commit_callbacks):
    scrape = patch.multiple(
        "scraper.tasks",
        fetch_html=lambda url: (url, "<html></html>"),
        parse_page=lambda base_url, content: ("Example", []),
    )
    with scrape, django_capture_on_commit_callbacks(execute=True):
        response = client.post("/api/v1/pages/", {"url": "https://example.com/"})

    assert response.status_code == 201
    assert response.data["status"] == Status.PENDING

    page = Page.objects.get(id=response.data["id"])
    assert page.normalized_url == "https://example.com/"
    # The task ran synchronously (eager mode + captured on_commit), so by now
    # all 3 transitions already happened even though the response above
    # reported the pre-task "pending" snapshot.
    transitions = list(
        page.status_events.order_by("occurred_at").values_list("from_status", "to_status")
    )
    assert transitions == [
        (None, Status.PENDING),
        (Status.PENDING, Status.IN_PROGRESS),
        (Status.IN_PROGRESS, Status.SUCCESS),
    ]
    page.refresh_from_db()
    assert page.status == Status.SUCCESS
    assert page.title == "Example"


def test_create_page_duplicate_url_returns_409(client):
    existing = PageFactory(normalized_url="https://example.com/", title="Example")

    response = client.post("/api/v1/pages/", {"url": "https://example.com/"})

    assert response.status_code == 409
    assert response.data["existing_page"]["id"] == str(existing.id)
    assert Page.objects.count() == 1


def test_create_page_invalid_url_returns_400(client):
    response = client.post("/api/v1/pages/", {"url": "not-a-url"})

    assert response.status_code == 400


def test_create_page_race_returns_409_not_500(client):
    conflicting = PageFactory(normalized_url="https://example.com/")
    real_find_existing_page = views_module._find_existing_page
    calls = []

    def fake_find_existing_page(normalized_url):
        calls.append(normalized_url)
        if len(calls) == 1:
            return None
        return real_find_existing_page(normalized_url)

    with patch("scraper.views._find_existing_page", side_effect=fake_find_existing_page):
        response = client.post("/api/v1/pages/", {"url": "https://example.com"})

    assert response.status_code == 409
    assert response.data["existing_page"]["id"] == str(conflicting.id)
    assert Page.objects.count() == 1
