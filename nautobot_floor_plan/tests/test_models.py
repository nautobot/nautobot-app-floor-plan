"""Test FloorPlan."""

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

from nautobot.dcim.models import Location, LocationType, Site
from nautobot.extras.models import Status
from nautobot.utilities.testing import TestCase

from nautobot_floor_plan import models


class TestFloorPlan(TestCase):
    """Test FloorPlan model."""

    def setUp(self):
        """Create LocationType, Status, and Location records."""
        self.parent_location_type = LocationType.objects.create(name="Building")
        self.location_type = LocationType.objects.create(name="Floor", parent=self.parent_location_type)
        self.active_status = Status.objects.get(name="Active")
        self.site = Site.objects.create(name="Site 1", status=self.active_status)
        self.building = Location.objects.create(
            site=self.site, location_type=self.parent_location_type, name="Building 1", status=self.active_status
        )
        self.floor_1 = Location.objects.create(
            location_type=self.location_type, parent=self.building, name="Floor 1", status=self.active_status
        )
        self.floor_2 = Location.objects.create(
            location_type=self.location_type, parent=self.building, name="Floor 2", status=self.active_status
        )

    def test_create_floor_plan_valid(self):
        """Successfully create various FloorPlan records."""
        floor_plan_minimal = models.FloorPlan(location=self.floor_1, x_size=1, y_size=1)
        floor_plan_minimal.validated_save()
        floor_plan_huge = models.FloorPlan(location=self.floor_2, x_size=100, y_size=100)
        floor_plan_huge.validated_save()

    def test_create_floor_plan_invalid_no_location(self):
        """Can't create a FloorPlan with no Location."""
        with self.assertRaises(ValidationError):
            models.FloorPlan(x_size=1, y_size=1).validated_save()

    def test_create_floor_plan_invalid_x_size(self):
        with self.assertRaises(ValidationError):
            models.FloorPlan(location=self.building, x_size=0, y_size=1).validated_save()

    def test_create_floor_plan_invalid_y_size(self):
        with self.assertRaises(ValidationError):
            models.FloorPlan(location=self.building, x_size=1, y_size=0).validated_save()

    def test_create_floor_plan_invalid_duplicate_location(self):
        models.FloorPlan(location=self.floor_1, x_size=1, y_size=1).validated_save()
        with self.assertRaises(ValidationError):
            models.FloorPlan(location=self.floor_1, x_size=2, y_size=2).validated_save()

    def test_floor_plan_tiles_empty(self):
        floor_plan_minimal = models.FloorPlan(location=self.floor_1, x_size=1, y_size=1)
        self.assertEqual(floor_plan_minimal.get_tiles(), [[None]])

        floor_plan_larger = models.FloorPlan(location=self.floor_2, x_size=3, y_size=3)
        self.assertEqual(floor_plan_larger.get_tiles(), [[None, None, None], [None, None, None], [None, None, None]])


class TestFloorPlanTile(TestCase):
    """Test FloorPlanTile model."""

    def setUp(self):
        """Create LocationType, Status, Location, and FloorPlan records."""
        # TODO: refactor to reduce duplicate code across test cases
        self.parent_location_type = LocationType.objects.create(name="Building")
        self.location_type = LocationType.objects.create(name="Floor", parent=self.parent_location_type)

        self.active_status = Status.objects.get(name="Active")
        self.active_status.content_types.add(ContentType.objects.get_for_model(models.FloorPlanTile))

        self.site = Site.objects.create(name="Site 1", status=self.active_status)
        self.building = Location.objects.create(
            site=self.site, location_type=self.parent_location_type, name="Building 1", status=self.active_status
        )
        self.floor_1 = Location.objects.create(
            location_type=self.location_type, parent=self.building, name="Floor 1", status=self.active_status
        )
        self.floor_2 = Location.objects.create(
            location_type=self.location_type, parent=self.building, name="Floor 2", status=self.active_status
        )
        self.floor_plan_1 = models.FloorPlan(location=self.floor_1, x_size=1, y_size=1)
        self.floor_plan_1.validated_save()
        self.floor_plan_2 = models.FloorPlan(location=self.floor_2, x_size=2, y_size=2)
        self.floor_plan_2.validated_save()

    def test_create_floor_plan_tile_valid(self):
        tile_1_1_1 = models.FloorPlanTile(floor_plan=self.floor_plan_1, x=1, y=1, status=self.active_status)
        tile_1_1_1.validated_save()
        self.assertEqual(self.floor_plan_1.get_tiles(), [[tile_1_1_1]])
        tile_2_1_1 = models.FloorPlanTile(floor_plan=self.floor_plan_2, x=1, y=1, status=self.active_status)
        tile_2_1_1.validated_save()
        tile_2_2_1 = models.FloorPlanTile(floor_plan=self.floor_plan_2, x=2, y=1, status=self.active_status)
        tile_2_2_1.validated_save()
        self.assertEqual(self.floor_plan_2.get_tiles(), [[tile_2_1_1, tile_2_2_1], [None, None]])
        tile_2_1_2 = models.FloorPlanTile(floor_plan=self.floor_plan_2, x=1, y=2, status=self.active_status)
        tile_2_1_2.validated_save()
        tile_2_2_2 = models.FloorPlanTile(floor_plan=self.floor_plan_2, x=2, y=2, status=self.active_status)
        tile_2_2_2.validated_save()
        self.assertEqual(self.floor_plan_2.get_tiles(), [[tile_2_1_1, tile_2_2_1], [tile_2_1_2, tile_2_2_2]])

    def test_create_floor_plan_tile_invalid_duplicate_position(self):
        models.FloorPlanTile(floor_plan=self.floor_plan_1, x=1, y=1, status=self.active_status).validated_save()
        with self.assertRaises(ValidationError):
            models.FloorPlanTile(floor_plan=self.floor_plan_1, x=1, y=1, status=self.active_status).validated_save()
