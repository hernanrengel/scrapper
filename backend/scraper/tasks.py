from celery import shared_task
from django.utils import timezone

from scraper.models import Page, PageStatusEvent, Status


@shared_task
def scrape_page(page_id):
    updated = Page.objects.filter(id=page_id, status=Status.PENDING).update(
        status=Status.IN_PROGRESS, started_at=timezone.now()
    )
    if not updated:
        return
    PageStatusEvent.objects.create(
        page_id=page_id, from_status=Status.PENDING, to_status=Status.IN_PROGRESS
    )

    # Stub: real fetch+parse logic lands in B8. For now, just succeed.
    Page.objects.filter(id=page_id, status=Status.IN_PROGRESS).update(
        status=Status.SUCCESS, finished_at=timezone.now()
    )
    PageStatusEvent.objects.create(
        page_id=page_id, from_status=Status.IN_PROGRESS, to_status=Status.SUCCESS
    )
