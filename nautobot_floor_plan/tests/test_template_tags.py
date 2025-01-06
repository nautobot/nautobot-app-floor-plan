"""Test cases for template tags."""

from nautobot.core.testing import TestCase

from nautobot_floor_plan import choices, models
from nautobot_floor_plan.templatetags.seed_helpers import (
    get_fieldset_field,
    grid_location_conversion,
    render_axis_label,
    seed_conversion,
)
from nautobot_floor_plan.tests import fixtures


class TestSeedHelpers(TestCase):
    """Test cases for seed helper template tags."""

    def setUp(self):
        """Create test objects."""
        data = fixtures.create_prerequisites()
        self.floors = data["floors"]
        self.status = data["status"]

    def test_seed_conversion(self):
        """Test conversion of seed numbers to letters."""
        floor_plan = models.FloorPlan.objects.create(
            location=self.floors[0], x_size=3, y_size=3, x_origin_seed=1, y_origin_seed=1
        )
        floor_plan.validated_save()
        # Test numeric seed
        floor_plan.x_axis_labels = choices.AxisLabelsChoices.NUMBERS
        floor_plan.x_origin_seed = 1
        self.assertEqual(seed_conversion(floor_plan, "x"), "1")

        # Test letter conversion
        floor_plan.x_axis_labels = choices.AxisLabelsChoices.LETTERS
        floor_plan.x_origin_seed = 1
        self.assertEqual(seed_conversion(floor_plan, "x"), "A")

        # Test larger numbers
        floor_plan.x_origin_seed = 26
        self.assertEqual(seed_conversion(floor_plan, "x"), "Z")

        floor_plan.x_origin_seed = 27
        self.assertEqual(seed_conversion(floor_plan, "x"), "AA")

    def test_grid_location_conversion(self):
        """Test conversion of grid locations to letters."""
        floor_plan = models.FloorPlan.objects.create(
            location=self.floors[0], x_size=3, y_size=3, x_origin_seed=1, y_origin_seed=1
        )
        floor_plan.validated_save()
        floor_plan_tile = models.FloorPlanTile(floor_plan=floor_plan, x_origin=1, y_origin=1, status=self.status)
        floor_plan_tile.validated_save()
        # Test numeric grid
        floor_plan.x_axis_labels = choices.AxisLabelsChoices.NUMBERS
        floor_plan_tile.x_origin = 1
        self.assertEqual(grid_location_conversion(floor_plan_tile, "x"), "1")

        # Test letter conversion
        floor_plan.x_axis_labels = choices.AxisLabelsChoices.LETTERS
        floor_plan_tile.x_origin = 1
        self.assertEqual(grid_location_conversion(floor_plan_tile, "x"), "A")

        # Test larger numbers
        floor_plan_tile.x_origin = 26
        self.assertEqual(grid_location_conversion(floor_plan_tile, "x"), "Z")

        floor_plan_tile.x_origin = 27
        self.assertEqual(grid_location_conversion(floor_plan_tile, "x"), "AA")

    def test_get_fieldset_field(self):
        """Test retrieving fields from a form fieldset."""

        class MockForm(dict):
            """Test retrieving fields from a form fieldset."""

        form = MockForm()
        form["test_field"] = "test_value"

        # Test existing field
        self.assertEqual(get_fieldset_field(form, "test_field"), "test_value")

        # Test non-existent field
        self.assertIsNone(get_fieldset_field(form, "non_existent_field"))

    def test_render_axis_label(self):
        """Test render_axis_label template filter."""
        floor_plan = models.FloorPlan.objects.create(
            location=self.floors[1], x_size=3, y_size=3, x_origin_seed=1, y_origin_seed=1
        )
        test_cases = [
            {
                "custom_label": {"axis": "X", "label_type": "binary", "start_label": "1", "end_label": "10", "step": 1},
                "expected": "binary",
            },
            {"custom_label": None, "axis_labels": choices.AxisLabelsChoices.NUMBERS, "expected": "numbers"},
        ]

        for test in test_cases:
            if test["custom_label"]:
                models.FloorPlanCustomAxisLabel.objects.create(floor_plan=floor_plan, **test["custom_label"])
            else:
                # Set the default axis labels on the floor plan
                floor_plan.x_axis_labels = test["axis_labels"]
                floor_plan.save()

            result = render_axis_label(floor_plan, "X")
            self.assertEqual(result, test["expected"])

            # Clean up for next test
            models.FloorPlanCustomAxisLabel.objects.all().delete()
