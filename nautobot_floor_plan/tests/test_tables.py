"""Test floorplan tables."""
# pylint: disable=duplicate-code

from nautobot.core.templatetags.helpers import hyperlinked_object, placeholder
from nautobot.core.testing import TestCase
from nautobot.dcim.models import Rack, RackGroup

from nautobot_floor_plan import models
from nautobot_floor_plan.tables import FloorPlanTable, FloorPlanTileTable
from nautobot_floor_plan.tests import fixtures


class TestFloorPlanTable(TestCase):
    """Test FloorPlan Table."""

    def setUp(self):
        """Create LocationType, Status, and Location records."""
        data = fixtures.create_prerequisites()
        self.floors = data["floors"]
        self.status = data["status"]

    def test_floor_plan_table_rendering(self):
        """Test FloorPlanTable renders correct values for custom labels."""
        floor_plan = models.FloorPlan(location=self.floors[0], x_size=1, y_size=1)
        floor_plan.validated_save()
        test_cases = [
            {
                "custom_label": {
                    "axis": "X",
                    "label_type": "numalpha",
                    "start_label": "07A",
                    "end_label": "07Z",
                    "step": 2,
                },
                "expected_seed": "07A",
                "expected_step": 2,
            },
            {"custom_label": None, "expected_seed": "1", "expected_step": 1},
        ]

        table = FloorPlanTable([floor_plan])

        for test in test_cases:
            if test["custom_label"]:
                models.FloorPlanCustomAxisLabel.objects.create(floor_plan=floor_plan, **test["custom_label"])

            rendered_seed = table.render_x_origin_seed(floor_plan)
            rendered_step = table.render_x_axis_step(floor_plan)

            self.assertEqual(rendered_seed, test["expected_seed"])
            self.assertEqual(rendered_step, test["expected_step"])

            # Clean up for next test
            if test["custom_label"]:
                models.FloorPlanCustomAxisLabel.objects.all().delete()


class TestFloorPlanTileTable(TestCase):
    """Test FloorPlanTile Table."""

    def setUp(self):
        """Create necessary records for testing."""
        data = fixtures.create_prerequisites()
        self.floors = data["floors"]
        self.status = data["status"]
        self.floor_plan = models.FloorPlan(location=self.floors[0], x_size=10, y_size=10)
        self.floor_plan.validated_save()

        # Store all other test data in the dictionary
        self._test_data = {
            "location": data["location"],
            "rack_group": RackGroup.objects.create(name="RackGroup 1", location=self.floors[0]),
        }

        # Create rack after rack_group is in _test_data
        self.rack = Rack.objects.create(
            name="Rack 1", status=self.status, rack_group=self._test_data["rack_group"], location=self.floors[0]
        )

        # Create FloorPlanTile instances
        self.object_floor_plan_tile = models.FloorPlanTile(
            floor_plan=self.floor_plan,
            x_origin=5,
            y_origin=5,
            status=self.status,
            allocation_type="object",
            rack=self.rack,
        )
        self.object_floor_plan_tile.validated_save()

        self.rack_group_floor_plan_tile = models.FloorPlanTile(
            floor_plan=self.floor_plan,
            x_origin=1,
            y_origin=1,
            status=self.status,
            allocation_type="object",
            rack_group=self._test_data["rack_group"],
        )
        self.rack_group_floor_plan_tile.validated_save()

    def test_floor_plan_tile_table_rendering(self):
        """Test FloorPlanTileTable renders correct values."""
        table = FloorPlanTileTable([self.object_floor_plan_tile, self.rack_group_floor_plan_tile])

        # Test object tile rendering
        self.assertEqual(
            table.render_floor_plan_tile(self.object_floor_plan_tile), hyperlinked_object(self.object_floor_plan_tile)
        )
        self.assertEqual(table.render_x_origin(self.object_floor_plan_tile), (self.object_floor_plan_tile.x_origin))
        self.assertEqual(table.render_y_origin(self.object_floor_plan_tile), (self.object_floor_plan_tile.y_origin))
        self.assertEqual(
            table.render_allocation_type(self.object_floor_plan_tile),
            self.object_floor_plan_tile.get_allocation_type_display(),
        )
        self.assertEqual(table.render_allocated_object(self.object_floor_plan_tile), hyperlinked_object(self.rack))

        # Test rack group tile rendering
        self.assertEqual(
            table.render_floor_plan_tile(self.rack_group_floor_plan_tile),
            hyperlinked_object(self.rack_group_floor_plan_tile),
        )
        self.assertEqual(
            table.render_x_origin(self.rack_group_floor_plan_tile), (self.rack_group_floor_plan_tile.x_origin)
        )
        self.assertEqual(
            table.render_y_origin(self.rack_group_floor_plan_tile), (self.rack_group_floor_plan_tile.y_origin)
        )
        self.assertEqual(
            table.render_allocation_type(self.rack_group_floor_plan_tile),
            self.rack_group_floor_plan_tile.get_allocation_type_display(),
        )
        self.assertEqual(table.render_allocated_object(self.rack_group_floor_plan_tile), placeholder)
