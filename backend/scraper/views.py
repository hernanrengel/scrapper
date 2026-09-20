from django.db import IntegrityError, transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from config.celery import app as celery_app
from scraper.models import Page, PageStatusEvent, Status
from scraper.normalization import normalize_url
from scraper.pagination import DefaultPagination
from scraper.serializers import (
    DuplicatePageSerializer,
    ErrorDetailSerializer,
    LinkSerializer,
    PageCreatedSerializer,
    PageCreateSerializer,
    PageDetailSerializer,
    PageListSerializer,
    PageStatusEventSerializer,
    PageSummarySerializer,
)
from scraper.tasks import enqueue_scrape

NOT_FOUND_RESPONSE = OpenApiResponse(ErrorDetailSerializer, description="No page with this id.")


def _find_existing_page(normalized_url):
    return (
        Page.objects.annotate(links_count=Count("links")).filter(normalized_url=normalized_url)
    ).first()


def _duplicate_response(existing_page):
    return Response(
        {
            "detail": "This URL was already scraped.",
            "existing_page": PageSummarySerializer(existing_page).data,
        },
        status=status.HTTP_409_CONFLICT,
    )


class PageListCreateView(APIView):
    pagination_class = DefaultPagination

    @extend_schema(
        operation_id="list_pages",
        summary="List scraped pages",
        responses=PageListSerializer(many=True),
    )
    def get(self, request):
        queryset = Page.objects.annotate(links_count=Count("links")).order_by("-created_at", "id")
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        serializer = PageListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        operation_id="create_page",
        summary="Submit a URL to scrape",
        request=PageCreateSerializer,
        responses={
            201: PageCreatedSerializer,
            400: OpenApiResponse(description="Invalid URL."),
            409: OpenApiResponse(DuplicatePageSerializer, description="URL already scraped."),
        },
    )
    def post(self, request):
        serializer = PageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        submitted_url = serializer.validated_data["url"]
        normalized = normalize_url(submitted_url)

        existing = _find_existing_page(normalized)
        if existing:
            return _duplicate_response(existing)

        try:
            with transaction.atomic():
                page = Page.objects.create(url=submitted_url, normalized_url=normalized)
                PageStatusEvent.objects.create(
                    page=page, from_status=None, to_status=Status.PENDING
                )
                transaction.on_commit(lambda: enqueue_scrape(page.id))
        except IntegrityError:
            return _duplicate_response(_find_existing_page(normalized))

        return Response(PageCreatedSerializer(page).data, status=status.HTTP_201_CREATED)


class PageRescrapeView(APIView):
    @extend_schema(
        operation_id="rescrape_page",
        summary="Rescrape a page",
        request=None,
        responses={
            202: OpenApiResponse(description="Rescrape enqueued."),
            404: NOT_FOUND_RESPONSE,
            409: OpenApiResponse(ErrorDetailSerializer, description="Page is already in progress."),
        },
    )
    def post(self, request, pk):
        page = get_object_or_404(Page, pk=pk)
        previous_status = page.status

        with transaction.atomic():
            updated = (
                Page.objects.filter(id=pk, status=previous_status)
                .exclude(status=Status.IN_PROGRESS)
                .update(
                    status=Status.PENDING,
                    error_message=None,
                    started_at=None,
                    finished_at=None,
                    celery_task_id=None,
                )
            )
            if not updated:
                return Response(
                    {"detail": "This page cannot be rescraped right now."},
                    status=status.HTTP_409_CONFLICT,
                )
            PageStatusEvent.objects.create(
                page_id=pk, from_status=previous_status, to_status=Status.PENDING
            )
            transaction.on_commit(lambda: enqueue_scrape(pk))

        return Response(status=status.HTTP_202_ACCEPTED)


class PageCancelView(APIView):
    @extend_schema(
        operation_id="cancel_page",
        summary="Cancel a page",
        request=None,
        responses={
            202: OpenApiResponse(description="Page cancelled."),
            404: NOT_FOUND_RESPONSE,
            409: OpenApiResponse(ErrorDetailSerializer, description="Page has already finished."),
        },
    )
    def post(self, request, pk):
        page = get_object_or_404(Page, pk=pk)
        previous_status = page.status

        with transaction.atomic():
            updated = Page.objects.filter(
                id=pk, status__in=[Status.PENDING, Status.IN_PROGRESS]
            ).update(status=Status.CANCELLED, finished_at=timezone.now())
            if not updated:
                return Response(
                    {"detail": "This page has already finished."},
                    status=status.HTTP_409_CONFLICT,
                )
            PageStatusEvent.objects.create(
                page_id=pk, from_status=previous_status, to_status=Status.CANCELLED
            )
            transaction.on_commit(lambda: _revoke_task(pk))

        return Response(status=status.HTTP_202_ACCEPTED)


def _revoke_task(pk):
    task_id = Page.objects.filter(id=pk).values_list("celery_task_id", flat=True).first()
    if task_id:
        celery_app.control.revoke(task_id, terminate=True, signal="SIGTERM")


class PageDetailView(APIView):
    @extend_schema(
        operation_id="retrieve_page",
        summary="Get a page",
        responses={200: PageDetailSerializer, 404: NOT_FOUND_RESPONSE},
    )
    def get(self, request, pk):
        page = get_object_or_404(Page, pk=pk)
        serializer = PageDetailSerializer(page)
        return Response(serializer.data)

    @extend_schema(
        operation_id="delete_page",
        summary="Delete a page",
        responses={204: None, 404: NOT_FOUND_RESPONSE},
    )
    def delete(self, request, pk):
        page = get_object_or_404(Page, pk=pk)
        page.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PageLinksView(APIView):
    pagination_class = DefaultPagination

    @extend_schema(
        operation_id="list_page_links",
        summary="List a page's links",
        responses={200: LinkSerializer(many=True), 404: NOT_FOUND_RESPONSE},
    )
    def get(self, request, pk):
        page = get_object_or_404(Page, pk=pk)
        paginator = self.pagination_class()
        paginated = paginator.paginate_queryset(page.links.all(), request)
        serializer = LinkSerializer(paginated, many=True)
        return paginator.get_paginated_response(serializer.data)


class PageStatusEventsView(APIView):
    @extend_schema(
        operation_id="list_page_status_events",
        summary="List a page's status history",
        responses={200: PageStatusEventSerializer(many=True), 404: NOT_FOUND_RESPONSE},
        examples=[
            OpenApiExample(
                "Page created",
                response_only=True,
                value={
                    "from_status": None,
                    "to_status": "pending",
                    "occurred_at": "2026-09-20T06:59:56.360717Z",
                    "error_message": None,
                },
            ),
            OpenApiExample(
                "Scrape finished successfully",
                response_only=True,
                value={
                    "from_status": "in_progress",
                    "to_status": "success",
                    "occurred_at": "2026-09-20T06:59:57.006066Z",
                    "error_message": None,
                },
            ),
            OpenApiExample(
                "Scrape failed",
                response_only=True,
                value={
                    "from_status": "in_progress",
                    "to_status": "failed",
                    "occurred_at": "2026-09-20T06:59:57.006066Z",
                    "error_message": "Could not connect to the host.",
                },
            ),
        ],
    )
    def get(self, request, pk):
        page = get_object_or_404(Page, pk=pk)
        serializer = PageStatusEventSerializer(page.status_events.all(), many=True)
        return Response(serializer.data)
