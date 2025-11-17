"""Unit tests for middleware functionality."""

from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse
from django.test import RequestFactory, override_settings
from nautobot.apps.testing import TestCase

from nautobot_floor_plan.middleware import FloorPlanReturnURLMiddleware

User = get_user_model()


class FloorPlanReturnURLMiddlewareTestCase(TestCase):
    """Test cases for FloorPlanReturnURLMiddleware."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.get_response = lambda request: HttpResponse("OK")
        self.middleware = FloorPlanReturnURLMiddleware(self.get_response)

    def _add_session_to_request(self, request):
        """Add a session to a request object."""
        session_middleware = SessionMiddleware(self.get_response)
        session_middleware.process_request(request)
        request.session.save()
        return request

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_middleware_stores_floor_plan_url_from_post(self):
        """Test middleware captures floor plan return URL from POST data."""
        request = self.factory.post("/dcim/racks/edit/", {"return_url": "/plugins/floor-plan/123/"})
        request.user = self.user
        request = self._add_session_to_request(request)

        response = self.middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(request.session.get("floor_plan_return_url"), "/plugins/floor-plan/123/")

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_middleware_only_processes_post_requests(self):
        """Test middleware only processes POST requests, not GET."""
        request = self.factory.get("/dcim/racks/edit/?return_url=/plugins/floor-plan/123/")
        request.user = self.user
        request = self._add_session_to_request(request)

        response = self.middleware(request)

        self.assertEqual(response.status_code, 200)
        # GET requests should NOT be processed by this middleware
        self.assertNotIn("floor_plan_return_url", request.session)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_middleware_ignores_non_floor_plan_urls(self):
        """Test middleware doesn't store non-floor-plan URLs."""
        request = self.factory.post("/dcim/racks/edit/", {"return_url": "/dcim/racks/"})
        request.user = self.user
        request = self._add_session_to_request(request)

        response = self.middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("floor_plan_return_url", request.session)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_middleware_accepts_underscore_format(self):
        """Test middleware recognizes 'floor_plan' (underscore) format."""
        request = self.factory.post("/dcim/racks/edit/", {"return_url": "/plugins/floor_plan/123/"})
        request.user = self.user
        request = self._add_session_to_request(request)

        response = self.middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(request.session.get("floor_plan_return_url"), "/plugins/floor_plan/123/")

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_middleware_handles_missing_return_url(self):
        """Test middleware handles requests without return_url."""
        request = self.factory.post("/dcim/racks/edit/")
        request.user = self.user
        request = self._add_session_to_request(request)

        response = self.middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("floor_plan_return_url", request.session)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_middleware_updates_existing_session_value(self):
        """Test middleware updates existing floor_plan_return_url in session."""
        request = self.factory.post("/dcim/racks/edit/", {"return_url": "/plugins/floor-plan/456/"})
        request.user = self.user
        request = self._add_session_to_request(request)
        request.session["floor_plan_return_url"] = "/plugins/floor-plan/123/"
        request.session.save()

        response = self.middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(request.session.get("floor_plan_return_url"), "/plugins/floor-plan/456/")

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_middleware_only_processes_edit_urls(self):
        """Test middleware only processes URLs with /edit/ in the path."""
        # This POST request doesn't have /edit/ in the path
        request = self.factory.post("/dcim/racks/", {"return_url": "/plugins/floor-plan/123/"})
        request.user = self.user
        request = self._add_session_to_request(request)

        response = self.middleware(request)

        self.assertEqual(response.status_code, 200)
        # Should NOT store the URL because path doesn't contain /edit/
        self.assertIsNone(request.session.get("floor_plan_return_url"))
