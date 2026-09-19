from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from django.db import transaction
from django.utils import timezone

from scraper.fetching import FetchError, fetch_html
from scraper.models import Link, Page, PageStatusEvent, Status
from scraper.parsing import parse_page
from scraper.ssrf import BlockedHostError

# 90s/100s, not just "above one request's 5s+15s timeout": the fetch step can
# make up to 4 requests (initial + the 3-hop redirect cap), so a legitimate
# slow-but-successful redirect chain needs real headroom, not a tight bound.
SOFT_TIME_LIMIT = 90
TIME_LIMIT = 100


@shared_task(soft_time_limit=SOFT_TIME_LIMIT, time_limit=TIME_LIMIT)
def scrape_page(page_id):
    updated = Page.objects.filter(id=page_id, status=Status.PENDING).update(
        status=Status.IN_PROGRESS, started_at=timezone.now()
    )
    if not updated:
        return
    PageStatusEvent.objects.create(
        page_id=page_id, from_status=Status.PENDING, to_status=Status.IN_PROGRESS
    )

    try:
        page = Page.objects.get(id=page_id)
        final_url, content = fetch_html(page.url)
        title, links = parse_page(final_url, content)

        with transaction.atomic():
            Page.objects.filter(id=page_id).update(title=title)
            page.links.all().delete()
            Link.objects.bulk_create(
                Link(page_id=page_id, href=link["href"], name_html=link["name_html"])
                for link in links
            )
    except (FetchError, BlockedHostError) as exc:
        _finish(page_id, Status.FAILED, error_message=str(exc)[:500])
        return
    except SoftTimeLimitExceeded:
        _finish(page_id, Status.FAILED, error_message="Scrape timed out")
        return

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


def enqueue_scrape(page_id):
    try:
        result = scrape_page.delay(page_id)
    except Exception as exc:
        message = str(exc)[:500]
        updated = Page.objects.filter(id=page_id, status=Status.PENDING).update(
            status=Status.FAILED, error_message=message, finished_at=timezone.now()
        )
        if updated:
            PageStatusEvent.objects.create(
                page_id=page_id,
                from_status=Status.PENDING,
                to_status=Status.FAILED,
                error_message=message,
            )
        return

    Page.objects.filter(id=page_id).update(celery_task_id=result.id)
