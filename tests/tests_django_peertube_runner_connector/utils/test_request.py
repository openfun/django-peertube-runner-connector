"""Test the request utils file."""

from django.test import RequestFactory, TestCase

from django_peertube_runner_connector.utils.request import get_client_ip


class VideoStateTestCase(TestCase):
    """Test the request utils file."""

    def test_get_client_ip(self):
        """Should return the client ip."""
        fake_request = RequestFactory().get("/path/to/endpoint")

        self.assertEqual(get_client_ip(fake_request), "127.0.0.1")

    def test_get_client_ip_wi(self):
        """Should return the client ip."""
        fake_request = RequestFactory().get("/path/to/endpoint")

        fake_request.META["HTTP_X_FORWARDED_FOR"] = (
            "203.0.113.195, 70.41.3.18, 150.172.238.178"
        )
        self.assertEqual(get_client_ip(fake_request), "203.0.113.195")
