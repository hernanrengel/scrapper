from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from scraper.models import Status
from scraper.tasks import _finish
from scraper.tests.factories import PageFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def mock_revoke():
    with patch("scraper.views.celery_app.control.revoke") as revoke:
        yield revoke


def test_cancel_pending_page(client, mock_revoke, django_capture_on_commit_callbacks):
    page = PageFactory(status=Status.PENDING, celery_task_id="task-abc")

    with django_capture_on_commit_callbacks(execute=True):
        response = client.post(f"/api/v1/pages/{page.id}/cancel/")

    assert response.status_code == 202
    page.refresh_from_db()
    assert page.status == Status.CANCELLED
    assert list(page.status_events.values_list("from_status", "to_status")) == [
        (Status.PENDING, Status.CANCELLED)
    ]
    mock_revoke.assert_called_once_with("task-abc", terminate=True, signal="SIGTERM")


def test_cancel_in_progress_page_sends_terminate(
    client, mock_revoke, django_capture_on_commit_callbacks
):
    page = PageFactory(status=Status.IN_PROGRESS, celery_task_id="task-xyz")

    with django_capture_on_commit_callbacks(execute=True):
        response = client.post(f"/api/v1/pages/{page.id}/cancel/")

    assert response.status_code == 202
    page.refresh_from_db()
    assert page.status == Status.CANCELLED
    mock_revoke.assert_called_once_with("task-xyz", terminate=True, signal="SIGTERM")


@pytest.mark.parametrize("terminal_status", [Status.SUCCESS, Status.FAILED, Status.CANCELLED])
def test_cancel_terminal_state_returns_409(client, mock_revoke, terminal_status):
    page = PageFactory(status=terminal_status)

    response = client.post(f"/api/v1/pages/{page.id}/cancel/")

    assert response.status_code == 409
    page.refresh_from_db()
    assert page.status == terminal_status
    mock_revoke.assert_not_called()


def test_cancel_404_for_unknown_page(client):
    response = client.post("/api/v1/pages/00000000-0000-0000-0000-000000000000/cancel/")

    assert response.status_code == 404


def test_cancel_without_a_stored_task_id_skips_revoke(
    client, mock_revoke, django_capture_on_commit_callbacks
):
    page = PageFactory(status=Status.PENDING, celery_task_id=None)

    with django_capture_on_commit_callbacks(execute=True):
        response = client.post(f"/api/v1/pages/{page.id}/cancel/")

    assert response.status_code == 202
    mock_revoke.assert_not_called()


def test_cancel_then_late_task_completion_does_not_resurrect(client, mock_revoke):
    page = PageFactory(status=Status.IN_PROGRESS, celery_task_id="task-late")

    response = client.post(f"/api/v1/pages/{page.id}/cancel/")
    assert response.status_code == 202

    # The task itself finishes anyway (e.g. it was already past its
    # cancellation check when SIGTERM was sent) — its own conditional write
    # must not resurrect a page that's already cancelled.
    _finish(page.id, Status.SUCCESS)

    page.refresh_from_db()
    assert page.status == Status.CANCELLED
