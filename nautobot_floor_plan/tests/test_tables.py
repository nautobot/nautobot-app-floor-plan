"""Test floorplan tables."""

from nautobot.core.testing import TestCase

from nautobot_floor_plan import models
from nautobot_floor_plan.tables import FloorPlanTable
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
