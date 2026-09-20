import pytest
from rest_framework.test import APIClient

from scraper.models import Link, Page, PageStatusEvent
from scraper.tests.factories import LinkFactory, PageFactory, PageStatusEventFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return APIClient()


def test_delete_page_cascades_links_and_status_events(client):
    page = PageFactory()
    LinkFactory.create_batch(2, page=page)
    PageStatusEventFactory(page=page)

    response = client.delete(f"/api/v1/pages/{page.id}/")

    assert response.status_code == 204
    assert not Page.objects.filter(id=page.id).exists()
    assert Link.objects.filter(page_id=page.id).count() == 0
    assert PageStatusEvent.objects.filter(page_id=page.id).count() == 0


def test_delete_404_for_unknown_page(client):
    response = client.delete("/api/v1/pages/00000000-0000-0000-0000-000000000000/")

    assert response.status_code == 404
