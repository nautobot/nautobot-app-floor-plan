"""Unit tests for views."""

from nautobot.apps.testing import ViewTestCases

from nautobot_floor_plan import models, choices
from nautobot_floor_plan.tests import fixtures


class FloorPlanViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    """Test the FloorPlan views."""

    model = models.FloorPlan
    bulk_edit_data = {"x_size": 10, "y_size": 10, "tile_width": 200, "tile_depth": 200}
    csv_data = (
        "location__name,x_size,y_size,tile_width,tile_depth",
        "Floor 4,1,2,100,100",
        "Floor 5,2,4,100,200",
        "Floor 6,3,6,200,100",
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
            "y_size": 2,
            "x_axis_labels": choices.AxisLabelsChoices.NUMBERS,
            "y_axis_labels": choices.AxisLabelsChoices.NUMBERS,
            "x_origin_start": 1,
            "y_origin_start": 1,
        }
