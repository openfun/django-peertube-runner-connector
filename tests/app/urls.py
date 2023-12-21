"""URLs for the test app."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path

from rest_framework import routers

from django_peertube_runner_connector.urls import (
    urlpatterns as django_peertube_runner_connector_urls,
)

from .video import TestVideoViewSet


router = routers.DefaultRouter(trailing_slash=False)
router.register(r"", TestVideoViewSet)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("videos/", include(router.urls)),
]
urlpatterns += django_peertube_runner_connector_urls
urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.VIDEO_URL, document_root=settings.VIDEOS_ROOT)
