"""Test FloorPlan."""

from django.test import TestCase

from nautobot_floor_plan import models


class TestFloorPlan(TestCase):
    """Test FloorPlan."""

    def test_create_floorplan_only_required(self):
        """Create with only required fields, and validate null description and __str__."""
        floorplan = models.FloorPlan.objects.create(name="Development")
        self.assertEqual(floorplan.name, "Development")
        self.assertEqual(floorplan.description, "")
        self.assertEqual(str(floorplan), "Development")

    def test_create_floorplan_all_fields_success(self):
        """Create FloorPlan with all fields."""
        floorplan = models.FloorPlan.objects.create(
            name="Development", description="Development Test"
        )
        self.assertEqual(floorplan.name, "Development")
        self.assertEqual(floorplan.description, "Development Test")
