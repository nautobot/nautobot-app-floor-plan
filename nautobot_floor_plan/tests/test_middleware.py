"""Test floorplan middleware."""

from django.contrib import messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.shortcuts import redirect
from django.test import RequestFactory, TestCase
from django.urls import reverse
from nautobot.dcim.models import Rack

from nautobot_floor_plan.middleware import RackLocationValidationMiddleware
from nautobot_floor_plan.models import FloorPlan, FloorPlanTile
from nautobot_floor_plan.tests import fixtures


class RackLocationValidationMiddlewareTest(TestCase):
    """Test case for RackLocationValidationMiddleware to ensure proper validation of Rack location changes."""

    def setUp(self):
        """Set up the test environment by creating necessary objects."""
        self.factory = RequestFactory()
        self.middleware = RackLocationValidationMiddleware(get_response=lambda request: None)

        # Create prerequisites for the tests
        data = fixtures.create_prerequisites()
        self.active_status = data["status"]
        self.floors = data["floors"]
        self.location = data["location"]
        self.floor_plan = FloorPlan(location=self.floors[0], x_size=10, y_size=10)
        self.floor_plan.validated_save()
        self.rack = Rack.objects.create(name="Rack 1", status=self.active_status, location=self.floors[0])
        tile_1 = FloorPlanTile(
            floor_plan=self.floor_plan, x_origin=2, y_origin=2, status=self.active_status, rack=self.rack
        )
        tile_1.validated_save()

    def test_rack_location_change_validation(self):
        """Test that an error message is set when trying to change the location of a Rack installed in a FloorPlan."""
        # Simulate a POST request to edit the Rack
        request = self.factory.post(
            reverse("dcim:rack_edit", args=[self.rack.pk]),
            {
                "location": 2  # Attempt to change the location
            },
        )
        # Add session and message middleware to the request
        add_middleware(request)
        # Apply the middleware
        response = self.middleware(request)

        # Check that the response is a redirect
        self.assertIsInstance(response, type(redirect("/")))  # Check if it's a redirect

        # Check that the error message is set
        self.assertEqual(len(messages.get_messages(request)), 1)
        message = list(messages.get_messages(request))[0]
        self.assertEqual(message.message, "Cannot move Rack as it is currently installed in a FloorPlan.")
        self.assertEqual(message.tags, "danger")  # Check if the message is an error

    def test_rack_location_change_no_validation(self):
        """Test that no error message is set when the location remains the same."""
        # Simulate a POST request to edit the Rack with a valid location change
        request = self.factory.post(
            reverse("dcim:rack_edit", args=[self.rack.pk]),
            {
                "location": self.rack.location.pk  # Valid location (same as current)
            },
        )
        # Add session and message middleware to the request
        add_middleware(request)
        # Apply the middleware
        response = self.middleware(request)

        # Check that the response is None (no redirect)
        self.assertIsNone(response)


def add_middleware(request):
    """Attach session and message middleware to the request."""
    # Add session middleware
    session_middleware = SessionMiddleware(lambda request: None)  # Pass a no-op callable
    session_middleware.process_request(request)
    request.session.save()

    # Add message middleware using FallbackStorage
    setattr(request, "_messages", FallbackStorage(request))
