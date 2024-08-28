"""django-peertube-runner-connector URL configuration"""

from django.urls import include, re_path

from rest_framework import routers

from django_peertube_runner_connector.views import RunnerJobViewSet, RunnerViewSet


router = routers.DefaultRouter(trailing_slash=False)
router.register(r"runners/jobs", RunnerJobViewSet, basename="runner-jobs")
router.register(r"runners", RunnerViewSet)

urlpatterns = [
    re_path(r"api/v1/", include(router.urls)),
]
