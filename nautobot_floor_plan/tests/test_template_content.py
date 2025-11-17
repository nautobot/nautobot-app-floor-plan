"""Unit tests for template content functionality."""

from unittest.mock import MagicMock

from django.contrib.auth import get_user_model
from django.test import RequestFactory, override_settings
from nautobot.apps.testing import TestCase

from nautobot_floor_plan.template_content import ReturnToFloorPlanButton
from nautobot_floor_plan.tests.fixtures import create_floor_plans, create_prerequisites

User = get_user_model()


class ReturnToFloorPlanButtonTestCase(TestCase):
    """Test cases for ReturnToFloorPlanButton."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="testuser", password="testpass")

        # Create test floor plan
        prerequisites = create_prerequisites(floor_count=1)
        self.floors = prerequisites["floors"]
        self.floor_plans = create_floor_plans(self.floors)
        self.floor_plan = self.floor_plans[0]

    def _create_mock_session(self, data=None):
        """Create a mock session object."""
        session = MagicMock()
        session.get = lambda key, default=None: (data or {}).get(key, default)
        return session

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_get_link_with_get_parameter(self):
        """Test getting return URL from GET parameters."""
        button = ReturnToFloorPlanButton()
        request = self.factory.get("/?return_url=/plugins/floor-plan/123/")
        request.user = self.user
        request.session = self._create_mock_session()

        context = {"request": request}
        link = button.get_link(context)

        self.assertEqual(link, "/plugins/floor-plan/123/")

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_get_link_with_post_data(self):
        """Test getting return URL from POST data."""
        button = ReturnToFloorPlanButton()
        request = self.factory.post("/", {"return_url": "/plugins/floor-plan/123/"})
        request.user = self.user
        request.session = self._create_mock_session()

        context = {"request": request}
        link = button.get_link(context)

        self.assertEqual(link, "/plugins/floor-plan/123/")

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_get_link_from_session(self):
        """Test getting return URL from session."""
        button = ReturnToFloorPlanButton()
        request = self.factory.get("/")
        request.user = self.user
        request.session = self._create_mock_session({"floor_plan_return_url": "/plugins/floor-plan/123/"})

        context = {"request": request}
        link = button.get_link(context)

        self.assertEqual(link, "/plugins/floor-plan/123/")

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_get_link_from_http_referer(self):
        """Test getting return URL from HTTP referer."""
        button = ReturnToFloorPlanButton()
        request = self.factory.get("/")
        request.META["HTTP_REFERER"] = "http://testserver/plugins/floor-plan/123/"
        request.user = self.user
        request.session = self._create_mock_session()

        context = {"request": request}
        link = button.get_link(context)

        self.assertIsNotNone(link)
        self.assertIn("floor-plan", link)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_get_link_no_request(self):
        """Test get_link returns None when no request in context."""
        button = ReturnToFloorPlanButton()
        context = {}

        link = button.get_link(context)

        self.assertIsNone(link)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_get_link_non_floor_plan_url(self):
        """Test get_link returns None for non-floor-plan URLs."""
        button = ReturnToFloorPlanButton()
        request = self.factory.get("/?return_url=/dcim/racks/")
        request.user = self.user
        request.session = self._create_mock_session()

        context = {"request": request}
        link = button.get_link(context)

        self.assertIsNone(link)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_get_link_from_job_result(self):
        """Test getting return URL from job result object."""
        button = ReturnToFloorPlanButton()
        request = self.factory.get("/")
        request.user = self.user
        request.session = self._create_mock_session()

        # Create a mock job result with job_kwargs
        job_result = type("JobResult", (), {"job_kwargs": {"return_url": "/plugins/floor-plan/123/"}})()

        context = {"request": request, "object": job_result}
        link = button.get_link(context)

        self.assertEqual(link, "/plugins/floor-plan/123/")

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_should_render_with_valid_link_and_permission(self):
        """Test button should render when user has permission and valid link exists."""
        self.add_permissions("nautobot_floor_plan.view_floorplan")

        button = ReturnToFloorPlanButton()
        request = self.factory.get("/?return_url=/plugins/floor-plan/123/")
        request.user = self.user
        request.session = self._create_mock_session()

        context = {"request": request}
        should_render = button.should_render(context)

        self.assertTrue(should_render)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_should_render_no_request(self):
        """Test button should not render when no request in context."""
        button = ReturnToFloorPlanButton()
        context = {}

        should_render = button.should_render(context)

        self.assertFalse(should_render)

    def test_should_render_no_permission(self):
        """Test button should not render when user lacks permission."""
        # Don't use @override_settings here - we want to actually test permissions
        # Create user without permission
        user_no_perm = User.objects.create_user(username="noperm", password="testpass")

        button = ReturnToFloorPlanButton()
        request = self.factory.get("/?return_url=/plugins/floor-plan/123/")
        request.user = user_no_perm
        request.session = self._create_mock_session()

        context = {"request": request}
        should_render = button.should_render(context)

        self.assertFalse(should_render)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_should_render_no_link(self):
        """Test button should not render when no valid link exists."""
        button = ReturnToFloorPlanButton()
        request = self.factory.get("/")  # No return URL
        request.user = self.user
        request.session = self._create_mock_session()

        context = {"request": request}
        should_render = button.should_render(context)

        self.assertFalse(should_render)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_get_link_with_floor_plan_underscore_format(self):
        """Test that URLs with 'floor_plan' (underscore) are also recognized."""
        button = ReturnToFloorPlanButton()
        request = self.factory.get("/?return_url=/plugins/floor_plan/123/")
        request.user = self.user
        request.session = self._create_mock_session()

        context = {"request": request}
        link = button.get_link(context)

        self.assertEqual(link, "/plugins/floor_plan/123/")

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_get_link_priority_order(self):
        """Test that GET parameters take priority over other sources."""
        button = ReturnToFloorPlanButton()
        request = self.factory.get("/?return_url=/plugins/floor-plan/from-get/")
        request.user = self.user
        request.session = self._create_mock_session({"floor_plan_return_url": "/plugins/floor-plan/from-session/"})
        request.META["HTTP_REFERER"] = "http://testserver/plugins/floor-plan/from-referer/"

        context = {"request": request}
        link = button.get_link(context)

        # Should get the one from GET parameter
        self.assertEqual(link, "/plugins/floor-plan/from-get/")
