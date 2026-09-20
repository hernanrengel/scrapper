from django.urls import path

from scraper.views import (
    PageDetailView,
    PageLinksView,
    PageListCreateView,
    PageRescrapeView,
    PageStatusEventsView,
)

urlpatterns = [
    path("pages/", PageListCreateView.as_view(), name="page-list"),
    path("pages/<uuid:pk>/", PageDetailView.as_view(), name="page-detail"),
    path("pages/<uuid:pk>/links/", PageLinksView.as_view(), name="page-links"),
    path(
        "pages/<uuid:pk>/status-events/",
        PageStatusEventsView.as_view(),
        name="page-status-events",
    ),
    path(
        "pages/<uuid:pk>/rescrape/",
        PageRescrapeView.as_view(),
        name="page-rescrape",
    ),
]
