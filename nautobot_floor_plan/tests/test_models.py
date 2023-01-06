"""Test FloorPlan."""

from django.core.exceptions import ValidationError

from nautobot.utilities.testing import TestCase

from nautobot_floor_plan import models
from nautobot_floor_plan.tests import fixtures


class TestFloorPlan(TestCase):
    """Test FloorPlan model."""

    def setUp(self):
        """Create LocationType, Status, and Location records."""
        data = fixtures.create_prerequisites()
        self.floors = data["floors"]

    def test_create_floor_plan_valid(self):
        """Successfully create various FloorPlan records."""
        floor_plan_minimal = models.FloorPlan(location=self.floors[0], x_size=1, y_size=1)
        floor_plan_minimal.validated_save()
        floor_plan_huge = models.FloorPlan(location=self.floors[1], x_size=100, y_size=100)
        floor_plan_huge.validated_save()

    def test_create_floor_plan_invalid_no_location(self):
        """Can't create a FloorPlan with no Location."""
        with self.assertRaises(ValidationError):
            models.FloorPlan(x_size=1, y_size=1).validated_save()

    def test_create_floor_plan_invalid_x_size(self):
        """A FloorPlan must have an x_size greater than zero."""
        with self.assertRaises(ValidationError):
            models.FloorPlan(location=self.floors[0], x_size=0, y_size=1).validated_save()

    def test_create_floor_plan_invalid_y_size(self):
        """A FloorPlan must have a y_size greater than zero."""
        with self.assertRaises(ValidationError):
            models.FloorPlan(location=self.floors[0], x_size=1, y_size=0).validated_save()

    def test_create_floor_plan_invalid_duplicate_location(self):
        """Only one FloorPlan per Location can be created."""
        models.FloorPlan(location=self.floors[0], x_size=1, y_size=1).validated_save()
        with self.assertRaises(ValidationError):
            models.FloorPlan(location=self.floors[0], x_size=2, y_size=2).validated_save()

    def test_floor_plan_get_tiles_empty(self):
        """The get_tiles() API works even when no FloorPlanTiles have been created."""
        floor_plan_minimal = models.FloorPlan(location=self.floors[0], x_size=1, y_size=1)
        self.assertEqual(floor_plan_minimal.get_tiles(), [[None]])

        floor_plan_larger = models.FloorPlan(location=self.floors[1], x_size=3, y_size=3)
        self.assertEqual(floor_plan_larger.get_tiles(), [[None, None, None], [None, None, None], [None, None, None]])


class TestFloorPlanTile(TestCase):
    """Test FloorPlanTile model."""

    def setUp(self):
        """Create LocationType, Status, Location, and FloorPlan records."""
        data = fixtures.create_prerequisites()
        self.active_status = data["status"]
        self.floor_plans = fixtures.create_floor_plans(data["floors"])

    def test_create_floor_plan_tile_valid(self):
        """A FloorPlanTile can be created for each legal position in a FloorPlan."""
        tile_1_1_1 = models.FloorPlanTile(floor_plan=self.floor_plans[0], x=1, y=1, status=self.active_status)
        tile_1_1_1.validated_save()
        self.assertEqual(self.floor_plans[0].get_tiles(), [[tile_1_1_1]])
        tile_2_1_1 = models.FloorPlanTile(floor_plan=self.floor_plans[1], x=1, y=1, status=self.active_status)
        tile_2_1_1.validated_save()
        tile_2_2_1 = models.FloorPlanTile(floor_plan=self.floor_plans[1], x=2, y=1, status=self.active_status)
        tile_2_2_1.validated_save()
        self.assertEqual(self.floor_plans[1].get_tiles(), [[tile_2_1_1, tile_2_2_1], [None, None]])
        tile_2_1_2 = models.FloorPlanTile(floor_plan=self.floor_plans[1], x=1, y=2, status=self.active_status)
        tile_2_1_2.validated_save()
        tile_2_2_2 = models.FloorPlanTile(floor_plan=self.floor_plans[1], x=2, y=2, status=self.active_status)
        tile_2_2_2.validated_save()
        self.assertEqual(self.floor_plans[1].get_tiles(), [[tile_2_1_1, tile_2_2_1], [tile_2_1_2, tile_2_2_2]])

    def test_create_floor_plan_tile_invalid_duplicate_position(self):
        """Two FloorPlanTiles cannot occupy the same position in the same FloorPlan."""
        models.FloorPlanTile(floor_plan=self.floor_plans[0], x=1, y=1, status=self.active_status).validated_save()
        with self.assertRaises(ValidationError):
            models.FloorPlanTile(floor_plan=self.floor_plans[0], x=1, y=1, status=self.active_status).validated_save()

    def test_create_floor_plan_tile_invalid_illegal_position(self):
        """A FloorPlanTile cannot be created outside the bounds of its FloorPlan."""
        with self.assertRaises(ValidationError):
            models.FloorPlanTile(floor_plan=self.floor_plans[0], status=self.active_status, x=0, y=1).validated_save()
        with self.assertRaises(ValidationError):
            models.FloorPlanTile(
                floor_plan=self.floor_plans[0], status=self.active_status, x=self.floor_plans[0].x_size + 1, y=1
            ).validated_save()
        with self.assertRaises(ValidationError):
            models.FloorPlanTile(floor_plan=self.floor_plans[0], status=self.active_status, x=1, y=0).validated_save()
        with self.assertRaises(ValidationError):
            models.FloorPlanTile(
                floor_plan=self.floor_plans[0], status=self.active_status, x=1, y=self.floor_plans[0].y_size + 1
            ).validated_save()
