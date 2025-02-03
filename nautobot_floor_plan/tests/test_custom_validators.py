"""Test FloorPlan Filter."""

from django.core.exceptions import ValidationError
from django.test import TestCase
from nautobot.dcim.models import Rack

from nautobot_floor_plan import models
from nautobot_floor_plan.tests import fixtures


class RackValidatorTest(TestCase):
    """RackValidator Test Case."""

    def setUp(self):
        # Create initial objects
        data = fixtures.create_prerequisites()
        self.floors = data["floors"]
        self.status = data["status"]
        self.location2 = self.floors[1]
        self.floor_plan = models.FloorPlan.objects.create(
            location=self.floors[0], x_size=10, y_size=10, x_origin_seed=1, y_origin_seed=1
        )
        self.rack = Rack.objects.create(name="Test Rack", location=self.floors[0], status=self.status)
        self.rack.validated_save()
        models.FloorPlanTile(
            floor_plan=self.floor_plan, x_origin=2, y_origin=2, status=self.status, rack=self.rack
        ).validated_save()

    def test_location_change_not_allowed(self):
        self.rack.location = self.location2  # Attempt to change the location
        with self.assertRaises(ValidationError) as cm:
            self.rack.validated_save()  # Triggers the custom validator
        self.assertIn("Cannot move Rack as it is currently installed in a FloorPlan.", str(cm.exception))

    def test_location_unchanged_allowed(self):
        # No exception should be raised when location remains unchanged
        self.rack.validated_save()  # Should pass validation
