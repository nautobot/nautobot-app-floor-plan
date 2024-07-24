"""Test FloorPlan."""

from django.core.exceptions import ValidationError

from nautobot.dcim.models import Rack, RackGroup
from nautobot.core.testing import TestCase

from nautobot_floor_plan import models
from nautobot_floor_plan.tests import fixtures


class TestFloorPlan(TestCase):
    """Test FloorPlan model."""

    def setUp(self):
        """Create LocationType, Status, and Location records."""
        data = fixtures.create_prerequisites()
        self.floors = data["floors"]
        self.status = data["status"]

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

    def test_origin_seed_increase(self):
        """Test that existing tile origins are updated during origin_seed updates"""
        floor_plan = models.FloorPlan.objects.create(
            location=self.floors[0], x_size=3, y_size=3, x_origin_seed=1, y_origin_seed=1
        )
        tile_1_1_1 = models.FloorPlanTile(floor_plan=floor_plan, x_origin=1, y_origin=1, status=self.status)
        tile_1_1_1.validated_save()

        floor_plan.x_origin_seed = 5
        floor_plan.validated_save()
        self.assertEquals(floor_plan.tiles.first().x_origin, 5)

    def test_origin_seed_decrease(self):
        """Test that existing tile origins are updated during origin_seed updates"""
        floor_plan = models.FloorPlan.objects.create(
            location=self.floors[0], x_size=3, y_size=3, x_origin_seed=3, y_origin_seed=3
        )
        tile_1_1_1 = models.FloorPlanTile(floor_plan=floor_plan, x_origin=5, y_origin=5, status=self.status)
        tile_1_1_1.validated_save()

        floor_plan.y_origin_seed = 1
        floor_plan.validated_save()
        self.assertEquals(floor_plan.tiles.first().y_origin, 3)


class TestFloorPlanTile(TestCase):
    """Test FloorPlanTile model."""

    def setUp(self):
        """Create LocationType, Status, Location, and FloorPlan records."""
        data = fixtures.create_prerequisites()
        self.active_status = data["status"]
        self.floors = data["floors"]
        self.location = data["location"]
        self.floor_plans = fixtures.create_floor_plans(self.floors)
        self.rack_group = RackGroup.objects.create(name="RackGroup 1", location=self.floors[2])
        self.rack = Rack.objects.create(
            name="Rack 1", status=self.active_status, rack_group=self.rack_group, location=self.floors[2]
        )
        self.valid_rack_group = RackGroup.objects.create(name="RackGroup 2", location=self.floors[3])

    def test_create_floor_plan_single_tiles_valid(self):
        """A FloorPlanTile can be created for each legal position in a FloorPlan."""
        tile_1_1_1 = models.FloorPlanTile(
            floor_plan=self.floor_plans[0], x_origin=1, y_origin=1, status=self.active_status
        )
        tile_1_1_1.validated_save()
        tile_2_1_1 = models.FloorPlanTile(
            floor_plan=self.floor_plans[1], x_origin=1, y_origin=1, status=self.active_status
        )
        tile_2_1_1.validated_save()
        tile_2_2_1 = models.FloorPlanTile(
            floor_plan=self.floor_plans[1], x_origin=2, y_origin=1, status=self.active_status
        )
        tile_2_2_1.validated_save()
        tile_2_1_2 = models.FloorPlanTile(
            floor_plan=self.floor_plans[1], x_origin=1, y_origin=2, status=self.active_status
        )
        tile_2_1_2.validated_save()
        tile_2_2_2 = models.FloorPlanTile(
            floor_plan=self.floor_plans[1], x_origin=2, y_origin=2, status=self.active_status
        )
        tile_2_2_2.validated_save()
        tile_3_2_2 = models.FloorPlanTile(
            floor_plan=self.floor_plans[2], x_origin=2, y_origin=2, status=self.active_status, rack=self.rack
        )
        tile_3_2_2.validated_save()

    def test_create_floor_plan_spanning_tiles_valid(self):
        """
        FloorPlanTiles can span multiple squares so long as they do not overlap.
        Racks can be installed on RackGroup Tiles if the Rack is in the correct RackGroup
        +-+-+-+-+
        |2|2|2|4|
        +-+-+-+-+
        |3|1|1|4|
        +-+-+-+-+
        |3|1|1|4|
        +-+-+-+-+
        |3|5|5|5|
        +-+-+-+-+
        """
        valid_rack = Rack.objects.create(
            name="Rack 3", status=self.active_status, rack_group=self.valid_rack_group, location=self.floors[3]
        )
        models.FloorPlanTile(
            floor_plan=self.floor_plans[3],
            status=self.active_status,
            rack_group=self.valid_rack_group,
            x_origin=2,
            y_origin=2,
            x_size=2,
            y_size=2,
        ).validated_save()
        models.FloorPlanTile(
            floor_plan=self.floor_plans[3],
            status=self.active_status,
            rack_group=self.valid_rack_group,
            rack=valid_rack,
            x_origin=2,
            y_origin=2,
            x_size=2,
            y_size=2,
        ).validated_save()
        models.FloorPlanTile(
            floor_plan=self.floor_plans[3], status=self.active_status, x_origin=1, y_origin=1, x_size=3, y_size=1
        ).validated_save()
        models.FloorPlanTile(
            floor_plan=self.floor_plans[3], status=self.active_status, x_origin=1, y_origin=2, x_size=1, y_size=3
        ).validated_save()
        models.FloorPlanTile(
            floor_plan=self.floor_plans[3], status=self.active_status, x_origin=4, y_origin=1, x_size=1, y_size=3
        ).validated_save()
        models.FloorPlanTile(
            floor_plan=self.floor_plans[3],
            status=self.active_status,
            rack_group=self.valid_rack_group,
            x_origin=2,
            y_origin=4,
            x_size=3,
            y_size=1,
        ).validated_save()

    def test_create_floor_plan_single_tile_invalid_duplicate_position(self):
        """Two FloorPlanTiles cannot occupy the same position in the same FloorPlan."""
        models.FloorPlanTile(
            floor_plan=self.floor_plans[0], x_origin=1, y_origin=1, status=self.active_status
        ).validated_save()
        with self.assertRaises(ValidationError):
            models.FloorPlanTile(
                floor_plan=self.floor_plans[0], x_origin=1, y_origin=1, status=self.active_status
            ).validated_save()

    def test_create_floor_plan_tile_invalid_duplicate_rack(self):
        """Each Rack can only associate to at most one FloorPlanTile."""
        models.FloorPlanTile(
            floor_plan=self.floor_plans[2], x_origin=1, y_origin=1, status=self.active_status, rack=self.rack
        ).validated_save()
        with self.assertRaises(ValidationError):
            models.FloorPlanTile(
                floor_plan=self.floor_plans[2], x_origin=2, y_origin=2, status=self.active_status, rack=self.rack
            ).validated_save()

    def test_create_floor_plan_tile_invalid_rack_rackgroup(self):
        """A Rack being placed on a Rackgroup tile must also be in the rack_group."""
        valid_rack = Rack.objects.create(
            name="Rack 3", status=self.active_status, rack_group=self.valid_rack_group, location=self.floors[3]
        )
        models.FloorPlanTile(
            floor_plan=self.floor_plans[2],
            x_origin=1,
            y_origin=1,
            x_size=1,
            y_size=1,
            status=self.active_status,
            rack_group=self.rack_group,
        ).validated_save()
        # How about a rack without the correct rack group?
        non_rack_group_rack = Rack.objects.create(name="Rack 2", status=self.active_status, location=self.floors[2])
        with self.assertRaises(ValidationError):
            models.FloorPlanTile(
                floor_plan=self.floor_plans[2],
                x_origin=1,
                y_origin=1,
                x_size=1,
                y_size=1,
                status=self.active_status,
                rack=non_rack_group_rack,
            ).validated_save()
        # How about a tile with with a rack and the incorrect rackgroup
        invalid_rack_group = RackGroup.objects.create(name="RackGroup 2", location=self.floors[2])
        with self.assertRaises(ValidationError):
            models.FloorPlanTile(
                floor_plan=self.floor_plans[2],
                x_origin=1,
                y_origin=1,
                x_size=1,
                y_size=1,
                status=self.active_status,
                rack_group=invalid_rack_group,
                rack=valid_rack,
            ).validated_save()
        # How about a rack extending beyond the bounds of the rackgroup tile
        with self.assertRaises(ValidationError):
            models.FloorPlanTile(
                floor_plan=self.floor_plans[2],
                x_origin=1,
                y_origin=1,
                x_size=2,
                y_size=1,
                status=self.active_status,
                rack_group=self.valid_rack_group,
                rack=valid_rack,
            ).validated_save()

    def test_create_floor_plan_tile_invalid_illegal_position(self):
        """A FloorPlanTile cannot be created outside the bounds of its FloorPlan."""
        # x_origin too small
        with self.assertRaises(ValidationError):
            models.FloorPlanTile(
                floor_plan=self.floor_plans[0], status=self.active_status, x_origin=0, y_origin=1
            ).validated_save()
        # x_origin too large
        with self.assertRaises(ValidationError):
            models.FloorPlanTile(
                floor_plan=self.floor_plans[0],
                status=self.active_status,
                x_origin=self.floor_plans[0].x_size + 1,
                y_origin=1,
            ).validated_save()
        # x_origin + x_size too large
        with self.assertRaises(ValidationError):
            models.FloorPlanTile(
                floor_plan=self.floor_plans[0],
                status=self.active_status,
                x_origin=self.floor_plans[0].x_size,
                y_origin=1,
                x_size=2,
            ).validated_save()
        # y_origin too small
        with self.assertRaises(ValidationError):
            models.FloorPlanTile(
                floor_plan=self.floor_plans[0], status=self.active_status, x_origin=1, y_origin=0
            ).validated_save()
        # y_origin too large
        with self.assertRaises(ValidationError):
            models.FloorPlanTile(
                floor_plan=self.floor_plans[0],
                status=self.active_status,
                x_origin=1,
                y_origin=self.floor_plans[0].y_size + 1,
            ).validated_save()
        # y_origin + y_size too large
        with self.assertRaises(ValidationError):
            models.FloorPlanTile(
                floor_plan=self.floor_plans[0],
                status=self.active_status,
                x_origin=1,
                y_origin=self.floor_plans[0].y_size,
                y_size=2,
            ).validated_save()

    def test_create_floor_plan_tile_invalid_overlapping_tiles(self):
        """FloorPlanTiles cannot overlap one another."""
        models.FloorPlanTile(
            floor_plan=self.floor_plans[3],
            status=self.active_status,
            x_origin=2,
            y_origin=2,
            x_size=2,
            y_size=2,
        ).validated_save()
        with self.assertRaises(ValidationError):
            models.FloorPlanTile(
                floor_plan=self.floor_plans[3],
                status=self.active_status,
                x_origin=1,
                y_origin=1,
                x_size=2,
                y_size=2,
            ).validated_save()
        with self.assertRaises(ValidationError):
            models.FloorPlanTile(
                floor_plan=self.floor_plans[3],
                status=self.active_status,
                x_origin=1,
                y_origin=3,
                x_size=2,
                y_size=2,
            ).validated_save()
        with self.assertRaises(ValidationError):
            models.FloorPlanTile(
                floor_plan=self.floor_plans[3],
                status=self.active_status,
                x_origin=3,
                y_origin=1,
                x_size=2,
                y_size=2,
            ).validated_save()
        with self.assertRaises(ValidationError):
            models.FloorPlanTile(
                floor_plan=self.floor_plans[3],
                status=self.active_status,
                x_origin=3,
                y_origin=3,
                x_size=2,
                y_size=2,
            ).validated_save()

    def test_create_floor_plan_tile_invalid_rack_location_mismatch(self):
        """The Rack, if any, attached to a FloorPlanTile must belong to the same location as the FloorPlan."""
        # self.rack is attached to self.floors[-1], not self.floors[0]
        with self.assertRaises(ValidationError):
            models.FloorPlanTile(
                floor_plan=self.floor_plans[0], status=self.active_status, x_origin=1, y_origin=1, rack=self.rack
            ).validated_save()
        # How about a rack with no Location at all?
        non_located_rack = Rack.objects.create(name="Rack 2", status=self.active_status, location=self.location)
        with self.assertRaises(ValidationError):
            models.FloorPlanTile(
                floor_plan=self.floor_plans[0], status=self.active_status, x_origin=1, y_origin=1, rack=non_located_rack
            ).validated_save()
