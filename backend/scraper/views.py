from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from scraper.models import Page
from scraper.pagination import DefaultPagination
from scraper.serializers import (
    LinkSerializer,
    PageDetailSerializer,
    PageListSerializer,
    PageStatusEventSerializer,
)


class PageListView(APIView):
    def get(self, request):
        queryset = Page.objects.annotate(links_count=Count("links")).order_by("-created_at", "id")
        paginator = DefaultPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = PageListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


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
