"""Test FloorPlan."""

from django.core.exceptions import ValidationError
from nautobot.core.testing import TestCase
from nautobot.dcim.models import Device, Location, PowerFeed, PowerPanel, Rack, RackGroup

from nautobot_floor_plan import models
from nautobot_floor_plan.tests import fixtures


class TestFloorPlan(TestCase):
    """Test FloorPlan model."""

    def setUp(self):
        """Create LocationType, Status, Location, and FloorPlan records."""
        prerequisites = fixtures.create_prerequisites()

        # Keep the most frequently used attributes as instance variables
        self.status = prerequisites["status"]
        self.floors = prerequisites["floors"]
        self.floor_plans = fixtures.create_floor_plans(self.floors)
        self.rack_group = RackGroup.objects.create(name="RackGroup 1", location=self.floors[2])
        self.rack = Rack.objects.create(
            name="Rack 1", status=self.status, rack_group=self.rack_group, location=self.floors[2]
        )

        # Store less frequently used attributes in a dictionary
        self._test_data = {
            "location": prerequisites["location"],
            "device_type": prerequisites["device_type"],
            "device_role": prerequisites["device_role"],
            "valid_rack_group": RackGroup.objects.create(name="RackGroup 2", location=self.floors[3]),
        }

    def test_create_floor_plan_valid(self):
        """Successfully create various FloorPlan records."""
        # Create new locations for these tests to avoid conflicts
        new_floors = []
        for i in range(3):
            new_floors.append(
                Location.objects.create(
                    name=f"Test Floor {i}",
                    location_type=self.floors[0].location_type,
                    status=self.status,
                    parent=self.floors[0].parent,
                )
            )

        floor_plan_minimal = models.FloorPlan(location=new_floors[0], x_size=1, y_size=1)
        floor_plan_minimal.validated_save()
        floor_plan_huge = models.FloorPlan(location=new_floors[1], x_size=100, y_size=100)
        floor_plan_huge.validated_save()
        floor_plan_pos_neg_step = models.FloorPlan(
            location=new_floors[2], x_size=20, y_size=20, x_axis_step=-1, y_axis_step=2
        )
        floor_plan_pos_neg_step.validated_save()

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
        # First floor plan is already created in setUp
        with self.assertRaises(ValidationError) as context:
            models.FloorPlan(location=self.floors[0], x_size=1, y_size=1).validated_save()

        self.assertIn("location", context.exception.message_dict)
        self.assertIn("Floor plan with this Location already exists.", context.exception.message_dict["location"])

    def test_origin_seed_x_increase(self):
        """Test that existing tile origins are updated during origin_seed updates"""
        # Create a new location for this test
        new_floor = Location.objects.create(
            name="Test Floor X Increase",
            location_type=self.floors[0].location_type,
            status=self.status,
            parent=self.floors[0].parent,
        )
        floor_plan = models.FloorPlan.objects.create(
            location=new_floor, x_size=3, y_size=3, x_origin_seed=1, y_origin_seed=1
        )

        tile_1_1_1 = models.FloorPlanTile(floor_plan=floor_plan, x_origin=1, y_origin=1, status=self.status)
        tile_2_3_1 = models.FloorPlanTile(floor_plan=floor_plan, x_origin=3, y_origin=1, status=self.status)
        tile_1_1_1.validated_save()
        tile_2_3_1.validated_save()
        tile_1_id = tile_1_1_1.id
        tile_2_id = tile_2_3_1.id

        floor_plan.x_origin_seed = 3
        floor_plan.validated_save()
        self.assertEqual(floor_plan.tiles.get(id=tile_1_id).x_origin, 3)
        self.assertEqual(floor_plan.tiles.get(id=tile_2_id).x_origin, 5)

    def test_origin_seed_y_decrease(self):
        """Test that existing tile origins are updated during origin_seed updates"""
        # Create a new location for this test
        new_floor = Location.objects.create(
            name="Test Floor Y Decrease",
            location_type=self.floors[0].location_type,
            status=self.status,
            parent=self.floors[0].parent,
        )
        floor_plan = models.FloorPlan.objects.create(
            location=new_floor, x_size=3, y_size=3, x_origin_seed=3, y_origin_seed=3
        )
        tile_1_5_5 = models.FloorPlanTile(floor_plan=floor_plan, x_origin=5, y_origin=5, status=self.status)
        tile_1_5_5.validated_save()

        floor_plan.y_origin_seed = 1
        floor_plan.validated_save()
        self.assertEqual(floor_plan.tiles.first().y_origin, 3)

    def test_origin_seed_x_increase_y_decrease(self):
        """Test that existing tile origins are updated during origin_seed updates"""
        # Create a new location for this test
        new_floor = Location.objects.create(
            name="Test Floor XY Change",
            location_type=self.floors[0].location_type,
            status=self.status,
            parent=self.floors[0].parent,
        )
        floor_plan = models.FloorPlan.objects.create(
            location=new_floor, x_size=5, y_size=5, x_origin_seed=3, y_origin_seed=3
        )

        tile_1_3_3 = models.FloorPlanTile(floor_plan=floor_plan, x_origin=3, y_origin=4, status=self.status)
        tile_2_5_3 = models.FloorPlanTile(floor_plan=floor_plan, x_origin=5, y_origin=4, status=self.status)
        tile_3_4_3 = models.FloorPlanTile(floor_plan=floor_plan, x_origin=4, y_origin=4, status=self.status)
        tile_4_4_5 = models.FloorPlanTile(floor_plan=floor_plan, x_origin=4, y_origin=5, status=self.status)
        ids = []
        for tile in (tile_1_3_3, tile_2_5_3, tile_3_4_3, tile_4_4_5):
            tile.validated_save()
            ids.append(tile.id)

        floor_plan.x_origin_seed = 4
        floor_plan.y_origin_seed = 2
        floor_plan.validated_save()
        self.assertEqual(floor_plan.tiles.get(id=ids[0]).x_origin, 4)
        self.assertEqual(floor_plan.tiles.get(id=ids[0]).y_origin, 3)
        self.assertEqual(floor_plan.tiles.get(id=ids[1]).x_origin, 6)
        self.assertEqual(floor_plan.tiles.get(id=ids[1]).y_origin, 3)
        self.assertEqual(floor_plan.tiles.get(id=ids[2]).x_origin, 5)
        self.assertEqual(floor_plan.tiles.get(id=ids[2]).y_origin, 3)
        self.assertEqual(floor_plan.tiles.get(id=ids[3]).x_origin, 5)
        self.assertEqual(floor_plan.tiles.get(id=ids[3]).y_origin, 4)

    def test_create_floor_plan_invalid_step(self):
        """A FloorPlan must not use a step value of zero."""
        with self.assertRaises(ValidationError):
            models.FloorPlan(
                location=self.floors[1], x_size=100, y_size=100, x_axis_step=0, y_axis_step=2
            ).validated_save()

    def test_resize_x_floor_plan_with_tiles(self):
        """Test that a FloorPlan cannot be resized after tiles are placed."""
        # Create a new location for this test
        new_floor = Location.objects.create(
            name="Test Floor X Resize",
            location_type=self.floors[0].location_type,
            status=self.status,
            parent=self.floors[0].parent,
        )
        floor_plan = models.FloorPlan.objects.create(
            location=new_floor, x_size=3, y_size=3, x_origin_seed=1, y_origin_seed=1
        )
        tile = models.FloorPlanTile(floor_plan=floor_plan, x_origin=1, y_origin=1, status=self.status)
        tile.validated_save()

        # Attempt to resize the FloorPlan
        floor_plan.x_size = 5
        with self.assertRaises(ValidationError):
            floor_plan.validated_save()

    def test_resize_y_floor_plan_with_tiles(self):
        """Test that a FloorPlan cannot be resized after tiles are placed."""
        # Create a new location for this test
        new_floor = Location.objects.create(
            name="Test Floor Y Resize",
            location_type=self.floors[0].location_type,
            status=self.status,
            parent=self.floors[0].parent,
        )
        floor_plan = models.FloorPlan.objects.create(
            location=new_floor, x_size=3, y_size=3, x_origin_seed=1, y_origin_seed=1
        )
        tile = models.FloorPlanTile(floor_plan=floor_plan, x_origin=1, y_origin=1, status=self.status)
        tile.validated_save()

        # Attempt to resize the FloorPlan
        floor_plan.y_size = 4
        with self.assertRaises(ValidationError):
            floor_plan.validated_save()


class TestFloorPlanTile(TestCase):
    """Test FloorPlanTile model."""

    def setUp(self):
        """Create LocationType, Status, Location, and FloorPlan records."""
        prerequisites = fixtures.create_prerequisites()

        # Keep only the most essential attributes as instance variables
        self.status = prerequisites["status"]
        self.floors = prerequisites["floors"]
        self.floor_plans = fixtures.create_floor_plans(self.floors)
        self.rack = None  # Will be set after rack_group is created

        # Store all other test data in the dictionary
        self._test_data = {
            "location": prerequisites["location"],
            "device_type": prerequisites["device_type"],
            "device_role": prerequisites["device_role"],
            "valid_rack_group": RackGroup.objects.create(name="RackGroup 2", location=self.floors[3]),
            "rack_group": RackGroup.objects.create(name="RackGroup 1", location=self.floors[2]),
        }

        # Create rack after rack_group is in _test_data
        self.rack = Rack.objects.create(
            name="Rack 1", status=self.status, rack_group=self._test_data["rack_group"], location=self.floors[2]
        )

    def test_create_floor_plan_single_tiles_valid(self):
        """A FloorPlanTile can be created for each legal position in a FloorPlan."""
        tile_1_1_1 = models.FloorPlanTile(floor_plan=self.floor_plans[0], x_origin=1, y_origin=1, status=self.status)
        tile_1_1_1.validated_save()
        tile_2_1_1 = models.FloorPlanTile(floor_plan=self.floor_plans[1], x_origin=1, y_origin=1, status=self.status)
        tile_2_1_1.validated_save()
        tile_2_2_1 = models.FloorPlanTile(floor_plan=self.floor_plans[1], x_origin=2, y_origin=1, status=self.status)
        tile_2_2_1.validated_save()
        tile_2_1_2 = models.FloorPlanTile(floor_plan=self.floor_plans[1], x_origin=1, y_origin=2, status=self.status)
        tile_2_1_2.validated_save()
        tile_2_2_2 = models.FloorPlanTile(floor_plan=self.floor_plans[1], x_origin=2, y_origin=2, status=self.status)
        tile_2_2_2.validated_save()
        tile_3_2_2 = models.FloorPlanTile(
            floor_plan=self.floor_plans[2], x_origin=2, y_origin=2, status=self.status, rack=self.rack
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
            name="Rack 3",
            status=self.status,
            rack_group=self._test_data["valid_rack_group"],
            location=self.floors[3],
        )
        models.FloorPlanTile(
            floor_plan=self.floor_plans[3],
            status=self.status,
            rack_group=self._test_data["valid_rack_group"],
            x_origin=2,
            y_origin=2,
            x_size=2,
            y_size=2,
        ).validated_save()
        models.FloorPlanTile(
            floor_plan=self.floor_plans[3],
            status=self.status,
            rack_group=self._test_data["valid_rack_group"],
            rack=valid_rack,
            x_origin=2,
            y_origin=2,
            x_size=2,
            y_size=2,
        ).validated_save()
        models.FloorPlanTile(
            floor_plan=self.floor_plans[3], status=self.status, x_origin=1, y_origin=1, x_size=3, y_size=1
        ).validated_save()
        models.FloorPlanTile(
            floor_plan=self.floor_plans[3], status=self.status, x_origin=1, y_origin=2, x_size=1, y_size=3
        ).validated_save()
        models.FloorPlanTile(
            floor_plan=self.floor_plans[3], status=self.status, x_origin=4, y_origin=1, x_size=1, y_size=3
        ).validated_save()
        models.FloorPlanTile(
            floor_plan=self.floor_plans[3],
            status=self.status,
            rack_group=self._test_data["valid_rack_group"],
            x_origin=2,
            y_origin=4,
            x_size=3,
            y_size=1,
        ).validated_save()

    def test_create_floor_plan_single_tile_invalid_duplicate_position(self):
        """Two FloorPlanTiles cannot occupy the same position in the same FloorPlan."""
        models.FloorPlanTile(
            floor_plan=self.floor_plans[0], x_origin=1, y_origin=1, status=self.status
        ).validated_save()
        with self.assertRaises(ValidationError):
            models.FloorPlanTile(
                floor_plan=self.floor_plans[0], x_origin=1, y_origin=1, status=self.status
            ).validated_save()

    def test_create_floor_plan_tile_invalid_duplicate_rack(self):
        """Each Rack can only associate to at most one FloorPlanTile."""
        models.FloorPlanTile(
            floor_plan=self.floor_plans[2], x_origin=1, y_origin=1, status=self.status, rack=self.rack
        ).validated_save()
        with self.assertRaises(ValidationError):
            models.FloorPlanTile(
                floor_plan=self.floor_plans[2], x_origin=2, y_origin=2, status=self.status, rack=self.rack
            ).validated_save()

    def test_create_floor_plan_tile_invalid_rack_rackgroup(self):
        """A Rack being placed on a Rackgroup tile must also be in the rack_group."""
        valid_rack = Rack.objects.create(
            name="Rack 3", status=self.status, rack_group=self._test_data["valid_rack_group"], location=self.floors[3]
        )
        models.FloorPlanTile(
            floor_plan=self.floor_plans[2],
            x_origin=1,
            y_origin=1,
            x_size=1,
            y_size=1,
            status=self.status,
            rack_group=self._test_data["rack_group"],
        ).validated_save()
        # How about a rack without the correct rack group?
        non_rack_group_rack = Rack.objects.create(name="Rack 2", status=self.status, location=self.floors[2])
        with self.assertRaises(ValidationError):
            models.FloorPlanTile(
                floor_plan=self.floor_plans[2],
                x_origin=1,
                y_origin=1,
                x_size=1,
                y_size=1,
                status=self.status,
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
                status=self.status,
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
                status=self.status,
                rack_group=self._test_data["valid_rack_group"],
                rack=valid_rack,
            ).validated_save()

    def test_create_floor_plan_tile_invalid_illegal_position(self):
        """A FloorPlanTile cannot be created outside the bounds of its FloorPlan."""
        # x_origin too small
        with self.assertRaises(ValidationError):
            models.FloorPlanTile(
                floor_plan=self.floor_plans[0], status=self.status, x_origin=0, y_origin=1
            ).validated_save()
        # x_origin too large
        with self.assertRaises(ValidationError):
            models.FloorPlanTile(
                floor_plan=self.floor_plans[0],
                status=self.status,
                x_origin=self.floor_plans[0].x_size + 1,
                y_origin=1,
            ).validated_save()
        # x_origin + x_size too large
        with self.assertRaises(ValidationError):
            models.FloorPlanTile(
                floor_plan=self.floor_plans[0],
                status=self.status,
                x_origin=self.floor_plans[0].x_size,
                y_origin=1,
                x_size=2,
            ).validated_save()
        # y_origin too small
        with self.assertRaises(ValidationError):
            models.FloorPlanTile(
                floor_plan=self.floor_plans[0], status=self.status, x_origin=1, y_origin=0
            ).validated_save()
        # y_origin too large
        with self.assertRaises(ValidationError):
            models.FloorPlanTile(
                floor_plan=self.floor_plans[0],
                status=self.status,
                x_origin=1,
                y_origin=self.floor_plans[0].y_size + 1,
            ).validated_save()
        # y_origin + y_size too large
        with self.assertRaises(ValidationError):
            models.FloorPlanTile(
                floor_plan=self.floor_plans[0],
                status=self.status,
                x_origin=1,
                y_origin=self.floor_plans[0].y_size,
                y_size=2,
            ).validated_save()

    def test_create_floor_plan_tile_invalid_overlapping_tiles(self):
        """FloorPlanTiles cannot overlap one another."""
        models.FloorPlanTile(
            floor_plan=self.floor_plans[3],
            status=self.status,
            x_origin=2,
            y_origin=2,
            x_size=2,
            y_size=2,
        ).validated_save()
        with self.assertRaises(ValidationError):
            models.FloorPlanTile(
                floor_plan=self.floor_plans[3],
                status=self.status,
                x_origin=1,
                y_origin=1,
                x_size=2,
                y_size=2,
            ).validated_save()
        with self.assertRaises(ValidationError):
            models.FloorPlanTile(
                floor_plan=self.floor_plans[3],
                status=self.status,
                x_origin=1,
                y_origin=3,
                x_size=2,
                y_size=2,
            ).validated_save()
        with self.assertRaises(ValidationError):
            models.FloorPlanTile(
                floor_plan=self.floor_plans[3],
                status=self.status,
                x_origin=3,
                y_origin=1,
                x_size=2,
                y_size=2,
            ).validated_save()
        with self.assertRaises(ValidationError):
            models.FloorPlanTile(
                floor_plan=self.floor_plans[3],
                status=self.status,
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
                floor_plan=self.floor_plans[0], status=self.status, x_origin=1, y_origin=1, rack=self.rack
            ).validated_save()
        # How about a rack with no Location at all?
        non_located_rack = Rack.objects.create(name="Rack 2", status=self.status, location=self._test_data["location"])
        with self.assertRaises(ValidationError):
            models.FloorPlanTile(
                floor_plan=self.floor_plans[0], status=self.status, x_origin=1, y_origin=1, rack=non_located_rack
            ).validated_save()

    def test_allocation_type_assignment_rack_group(self):
        """Test that allocation type is correctly assigned for rack group tiles."""
        tile = models.FloorPlanTile(
            floor_plan=self.floor_plans[3],
            status=self.status,
            x_origin=2,
            y_origin=2,
            rack_group=self._test_data["valid_rack_group"],
        )
        tile.validated_save()
        self.assertEqual(tile.allocation_type, models.AllocationTypeChoices.RACKGROUP)

    def test_allocation_type_assignment_object(self):
        """Test that allocation type is correctly assigned for object tiles."""
        # Create a rack in the correct location
        rack = Rack.objects.create(
            name="Test Rack for Allocation",
            status=self.status,
            location=self.floor_plans[3].location,
        )

        tile = models.FloorPlanTile(
            floor_plan=self.floor_plans[3],
            status=self.status,
            x_origin=2,
            y_origin=2,
            rack=rack,
        )
        tile.validated_save()
        self.assertEqual(tile.allocation_type, models.AllocationTypeChoices.OBJECT)

    def test_allocation_type_assignment_status_only(self):
        """Test that allocation type is correctly assigned for tiles with only status."""
        tile = models.FloorPlanTile(
            floor_plan=self.floor_plans[3],
            status=self.status,
            x_origin=2,
            y_origin=2,
        )
        tile.validated_save()
        self.assertEqual(tile.allocation_type, models.AllocationTypeChoices.RACKGROUP)

    def test_rack_on_rackgroup_tile_valid(self):
        """Test that a rack can be placed on a rack group tile if it belongs to that group."""
        # Create a rack group tile
        rackgroup_tile = models.FloorPlanTile(
            floor_plan=self.floor_plans[3],
            status=self.status,
            x_origin=2,
            y_origin=2,
            rack_group=self._test_data["valid_rack_group"],
            allocation_type=models.AllocationTypeChoices.RACKGROUP,
        )
        rackgroup_tile.validated_save()

        # Create a rack in the same group
        rack = Rack.objects.create(
            name="Test Rack",
            status=self.status,
            location=self.floor_plans[3].location,
            rack_group=self._test_data["valid_rack_group"],
        )

        # Place rack on the rack group tile
        rack_tile = models.FloorPlanTile(
            floor_plan=self.floor_plans[3],
            status=self.status,
            x_origin=2,
            y_origin=2,
            rack=rack,
        )
        rack_tile.validated_save()  # Should not raise ValidationError
        self.assertTrue(rack_tile.on_group_tile)
        self.assertEqual(rack_tile.rack_group, self._test_data["valid_rack_group"])

    def test_rack_on_rackgroup_tile_invalid_group(self):
        """Test that a rack cannot be placed on a rack group tile if it belongs to a different group."""
        # Create a different rack group
        other_rack_group = RackGroup.objects.create(
            name="Other Rack Group",
            location=self.floor_plans[3].location,
        )

        # Create a rack group tile
        rackgroup_tile = models.FloorPlanTile(
            floor_plan=self.floor_plans[3],
            status=self.status,
            x_origin=2,
            y_origin=2,
            rack_group=self._test_data["rack_group"],
            allocation_type=models.AllocationTypeChoices.RACKGROUP,
        )
        rackgroup_tile.validated_save()

        # Create a rack in a different group
        rack = Rack.objects.create(
            name="Test Rack",
            status=self.status,
            location=self.floor_plans[3].location,
            rack_group=other_rack_group,
        )

        # Try to place rack on the rack group tile
        rack_tile = models.FloorPlanTile(
            floor_plan=self.floor_plans[3],
            status=self.status,
            x_origin=2,
            y_origin=2,
            rack=rack,
        )
        with self.assertRaisesRegex(
            ValidationError, "Object tile with Rack .* cannot overlap with RackGroup tile for different group"
        ):
            rack_tile.clean()

    def test_object_tile_within_rackgroup_bounds(self):
        """Test that an object tile must fit within the bounds of its rack group tile."""
        # Create a rack group tile
        models.FloorPlanTile(
            floor_plan=self.floor_plans[3],
            status=self.status,
            x_origin=2,
            y_origin=2,
            x_size=1,
            y_size=1,
            rack_group=self._test_data["valid_rack_group"],
            allocation_type=models.AllocationTypeChoices.RACKGROUP,
        ).validated_save()

        # Create a rack in the correct location for this test
        rack = Rack.objects.create(
            name="Test Rack in Floor 4",
            status=self.status,
            location=self.floor_plans[3].location,
        )

        # Try to create an object tile that extends beyond the rack group tile
        object_tile = models.FloorPlanTile(
            floor_plan=self.floor_plans[3],
            status=self.status,
            x_origin=2,
            y_origin=2,
            x_size=2,
            y_size=3,
            rack=rack,
        )

        with self.assertRaisesRegex(
            ValidationError, "Object tile must not extend beyond the boundary of the rack group tile"
        ):
            object_tile.clean()

    def test_rackgroup_tiles_cannot_overlap(self):
        """Test that rack group tiles cannot overlap with each other."""
        # Create first rack group tile
        models.FloorPlanTile.objects.create(
            floor_plan=self.floor_plans[3],
            status=self.status,
            x_origin=2,
            y_origin=2,
            rack_group=self._test_data["valid_rack_group"],
            allocation_type=models.AllocationTypeChoices.RACKGROUP,
        )

        # Create another rack group
        other_rack_group = RackGroup.objects.create(
            name="Other Rack Group",
            location=self.floor_plans[3].location,
        )

        # Try to create an overlapping rack group tile
        overlapping_tile = models.FloorPlanTile(
            floor_plan=self.floor_plans[3],
            status=self.status,
            x_origin=2,
            y_origin=2,
            rack_group=other_rack_group,
            allocation_type=models.AllocationTypeChoices.RACKGROUP,
        )

        with self.assertRaisesRegex(ValidationError, "RackGroup tiles cannot overlap"):
            overlapping_tile.clean()

    def test_object_tiles_cannot_overlap(self):
        """Test that object tiles cannot overlap with each other."""
        # Create first object tile with a rack
        rack = Rack.objects.create(
            name="Test Rack for Overlap",
            status=self.status,
            location=self.floor_plans[3].location,
        )
        models.FloorPlanTile.objects.create(
            floor_plan=self.floor_plans[3],
            status=self.status,
            x_origin=2,
            y_origin=2,
            rack=rack,
            allocation_type=models.AllocationTypeChoices.OBJECT,
        )

        # Try to create an overlapping object tile with a device
        device = Device.objects.create(
            name="Test Device",
            device_type=self._test_data["device_type"],
            role=self._test_data["device_role"],
            status=self.status,
            location=self.floor_plans[3].location,
        )
        overlapping_tile = models.FloorPlanTile(
            floor_plan=self.floor_plans[3],
            status=self.status,
            x_origin=2,
            y_origin=2,
            device=device,
            allocation_type=models.AllocationTypeChoices.OBJECT,
        )

        with self.assertRaisesRegex(ValidationError, "Object tiles cannot overlap"):
            overlapping_tile.clean()


class TestFloorPlanTilePower(TestCase):
    """Test power-related functionality of FloorPlanTile model."""

    def setUp(self):
        """Create LocationType, Status, Location, and FloorPlan records."""
        prerequisites = fixtures.create_prerequisites()

        # Keep only the most essential attributes as instance variables
        self.status = prerequisites["status"]
        self.floors = prerequisites["floors"]
        self.floor_plans = fixtures.create_floor_plans(self.floors)

        # Store all other test data in the dictionary
        self._test_data = {
            "location": prerequisites["location"],
            "device_type": prerequisites["device_type"],
            "device_role": prerequisites["device_role"],
            "valid_rack_group": RackGroup.objects.create(name="RackGroup 2", location=self.floors[3]),
        }

    def test_power_objects_on_tiles(self):
        """Test that power panels and power feeds can be placed on tiles and validate overlap rules."""
        # Create a power panel
        power_panel = PowerPanel.objects.create(
            name="Test Power Panel",
            location=self.floor_plans[3].location,
        )

        # Create a power feed connected to the panel
        power_feed = PowerFeed.objects.create(
            name="Test Power Feed",
            status=self.status,
            power_panel=power_panel,
        )

        # Place power panel on a tile
        panel_tile = models.FloorPlanTile(
            floor_plan=self.floor_plans[3],
            status=self.status,
            x_origin=2,
            y_origin=2,
            power_panel=power_panel,
            allocation_type=models.AllocationTypeChoices.OBJECT,
        )
        panel_tile.validated_save()

        # Try to place power feed on the same tile - should fail
        feed_tile_overlapping = models.FloorPlanTile(
            floor_plan=self.floor_plans[3],
            status=self.status,
            x_origin=2,
            y_origin=2,
            power_feed=power_feed,
            allocation_type=models.AllocationTypeChoices.OBJECT,
        )
        with self.assertRaisesRegex(ValidationError, "Object tiles cannot overlap"):
            feed_tile_overlapping.clean()

        # Place power feed on a different tile - should succeed
        feed_tile = models.FloorPlanTile(
            floor_plan=self.floor_plans[3],
            status=self.status,
            x_origin=3,
            y_origin=3,
            power_feed=power_feed,
            allocation_type=models.AllocationTypeChoices.OBJECT,
        )
        feed_tile.validated_save()

        # Verify allocation types are set correctly
        self.assertEqual(panel_tile.allocation_type, models.AllocationTypeChoices.OBJECT)
        self.assertEqual(feed_tile.allocation_type, models.AllocationTypeChoices.OBJECT)

        # Try to place another object on the power panel tile - should fail
        device = Device.objects.create(
            name="Test Device",
            device_type=self._test_data["device_type"],
            role=self._test_data["device_role"],
            status=self.status,
            location=self.floor_plans[3].location,
        )
        device_tile = models.FloorPlanTile(
            floor_plan=self.floor_plans[3],
            status=self.status,
            x_origin=2,
            y_origin=2,
            device=device,
            allocation_type=models.AllocationTypeChoices.OBJECT,
        )
        with self.assertRaisesRegex(ValidationError, "Object tiles cannot overlap"):
            device_tile.clean()

    def test_power_panel_with_rack_group(self):
        """Test that power panels respect rack group assignments and tile validation."""
        # Create a rack group tile
        rackgroup_tile = models.FloorPlanTile(
            floor_plan=self.floor_plans[3],
            status=self.status,
            x_origin=2,
            y_origin=2,
            rack_group=self._test_data["valid_rack_group"],
            allocation_type=models.AllocationTypeChoices.RACKGROUP,
        )
        rackgroup_tile.validated_save()

        # Create a power panel in the correct rack group
        power_panel = PowerPanel.objects.create(
            name="Test Power Panel",
            location=self.floor_plans[3].location,
            rack_group=self._test_data["valid_rack_group"],
        )
        power_panel.validated_save()

        # Place power panel on the rack group tile - should succeed
        panel_tile = models.FloorPlanTile(
            floor_plan=self.floor_plans[3],
            status=self.status,
            x_origin=2,
            y_origin=2,
            power_panel=power_panel,
            allocation_type=models.AllocationTypeChoices.OBJECT,
        )
        panel_tile.validated_save()

        self.assertEqual(rackgroup_tile.rack_group, self._test_data["valid_rack_group"])
        self.assertEqual(power_panel.rack_group, rackgroup_tile.rack_group)
        self.assertTrue(panel_tile.on_group_tile)

        # Create a power panel in a different rack group
        other_rack_group = RackGroup.objects.create(
            name="Other Rack Group",
            location=self.floor_plans[3].location,
        )
        other_power_panel = PowerPanel.objects.create(
            name="Other Power Panel",
            location=self.floor_plans[3].location,
            rack_group=other_rack_group,
        )

        # Try to place power panel from different rack group on the tile - should fail
        invalid_panel_tile = models.FloorPlanTile(
            floor_plan=self.floor_plans[3],
            status=self.status,
            x_origin=2,
            y_origin=2,
            power_panel=other_power_panel,
            allocation_type=models.AllocationTypeChoices.OBJECT,
        )
        with self.assertRaisesRegex(ValidationError, "Object tiles cannot overlap"):
            invalid_panel_tile.clean()
