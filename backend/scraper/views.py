from django.db import IntegrityError, transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from scraper.models import Page, PageStatusEvent, Status
from scraper.normalization import normalize_url
from scraper.pagination import DefaultPagination
from scraper.serializers import (
    LinkSerializer,
    PageCreateSerializer,
    PageDetailSerializer,
    PageListSerializer,
    PageStatusEventSerializer,
    PageSummarySerializer,
)
from scraper.tasks import scrape_page


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
    def get(self, request):
        queryset = Page.objects.annotate(links_count=Count("links")).order_by("-created_at", "id")
        paginator = DefaultPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = PageListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

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
                transaction.on_commit(lambda: scrape_page.delay(page.id))
        except IntegrityError:
            return _duplicate_response(_find_existing_page(normalized))

        return Response(
            {"id": page.id, "url": page.url, "status": page.status},
            status=status.HTTP_201_CREATED,
        )


class PageDetailView(APIView):
    def get(self, request, pk):
        page = get_object_or_404(Page, pk=pk)
        serializer = PageDetailSerializer(page)
        return Response(serializer.data)


class PageLinksView(APIView):
    def get(self, request, pk):
        page = get_object_or_404(Page, pk=pk)
        paginator = DefaultPagination()
        paginated = paginator.paginate_queryset(page.links.all(), request)
        serializer = LinkSerializer(paginated, many=True)
        return paginator.get_paginated_response(serializer.data)


class PageStatusEventsView(APIView):
    def get(self, request, pk):
        page = get_object_or_404(Page, pk=pk)
        serializer = PageStatusEventSerializer(page.status_events.all(), many=True)
        return Response(serializer.data)
