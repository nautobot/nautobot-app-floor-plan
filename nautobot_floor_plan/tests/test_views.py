"""Unit tests for views."""

from nautobot.apps.testing import ViewTestCases

from nautobot_floor_plan import choices, models
from nautobot_floor_plan.tests import fixtures


class FloorPlanViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    """Test the FloorPlan views."""

    model = models.FloorPlan
    bulk_edit_data = {"x_size": 10, "y_size": 10, "tile_width": 200, "tile_depth": 200}
    csv_data = (
        "location__name,x_size,x_origin_seed,x_axis_step,y_size,y_origin_seed,y_axis_step,tile_width,tile_depth",
        "Floor 4,1,1,1,2,1,1,100,100",
        "Floor 5,2,1,1,4,1,2,100,200",
        "Floor 6,3,1,1,6,1,-2,200,100",
    )

    @classmethod
    def setUpTestData(cls):
        data = fixtures.create_prerequisites(floor_count=6)
        fixtures.create_floor_plans(data["floors"][:3])
        cls.form_data = {
            "location": data["floors"][3].pk,
            "tile_depth": 100,
            "tile_width": 100,
            "x_size": 1,
            "x_origin_seed": 1,
            "x_axis_step": 1,
            "y_size": 2,
            "y_origin_seed": 1,
            "y_axis_step": 1,
            "x_axis_labels": choices.AxisLabelsChoices.NUMBERS,
            "y_axis_labels": choices.AxisLabelsChoices.NUMBERS,
            "x_custom_ranges": [{}],  # Placeholder for x_custom_ranges
            "y_custom_ranges": [{}],  # Placeholder for y_custom_ranges
        }
