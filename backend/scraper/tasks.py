from celery import shared_task
from django.db import transaction
from django.utils import timezone

from scraper.fetching import FetchError, fetch_html
from scraper.models import Link, Page, PageStatusEvent, Status
from scraper.parsing import parse_page
from scraper.ssrf import BlockedHostError


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

    page = Page.objects.get(id=page_id)

    try:
        final_url, content = fetch_html(page.url)
        title, links = parse_page(final_url, content)
    except (FetchError, BlockedHostError) as exc:
        _finish(page_id, Status.FAILED, error_message=str(exc)[:500])
        return

    # Replace the page s links wholesale applies to both a first scrape and
    # a re scrape, so there's no diffing logic to keep in sync separately.
    with transaction.atomic():
        Page.objects.filter(id=page_id).update(title=title)
        page.links.all().delete()
        Link.objects.bulk_create(
            Link(page_id=page_id, href=link["href"], name_html=link["name_html"]) for link in links
        )

    _finish(page_id, Status.SUCCESS)


def _finish(page_id, to_status, error_message=None):
    # Conditional on still being "in_progress", so a task that finishes after
    # the page was already cancelled (0 rows affected) doesn't resurrect it.
    updated = Page.objects.filter(id=page_id, status=Status.IN_PROGRESS).update(
        status=to_status, finished_at=timezone.now(), error_message=error_message
    )
    if updated:
        PageStatusEvent.objects.create(
            page_id=page_id,
            from_status=Status.IN_PROGRESS,
            to_status=to_status,
            error_message=error_message,
        )
