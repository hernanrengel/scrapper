from django.core.validators import URLValidator
from rest_framework import serializers

from scraper.models import Link, Page, PageStatusEvent


class PageCreateSerializer(serializers.Serializer):
    url = serializers.CharField(validators=[URLValidator(schemes=["http", "https"])])


class PageCreatedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = ["id", "url", "status"]


class ErrorDetailSerializer(serializers.Serializer):
    detail = serializers.CharField()


class PageSummarySerializer(serializers.ModelSerializer):
    links_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Page
        fields = ["id", "title", "status", "links_count"]


class DuplicatePageSerializer(serializers.Serializer):
    detail = serializers.CharField()
    existing_page = PageSummarySerializer()


class PageListSerializer(serializers.ModelSerializer):
    links_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Page
        fields = [
            "id",
            "title",
            "url",
            "status",
            "links_count",
            "created_at",
        ]


class PageDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = [
            "id",
            "url",
            "title",
            "status",
            "error_message",
            "started_at",
            "finished_at",
            "created_at",
        ]


class LinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Link
        fields = ["id", "href", "name_html"]


class PageStatusEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageStatusEvent
        fields = [
            "from_status",
            "to_status",
            "occurred_at",
            "error_message",
        ]
