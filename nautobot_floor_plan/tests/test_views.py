"""Unit tests for views."""

import unittest

from nautobot.utilities.testing import ViewTestCases

from nautobot_floor_plan import models
from nautobot_floor_plan.tests import fixtures


class FloorPlanViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    """Test the FloorPlan views."""

    model = models.FloorPlan
    bulk_edit_data = {"x_size": 10, "y_size": 10, "tile_width": 200, "tile_depth": 200}
    csv_data = (
        "location.name,x_size,y_size,tile_width,tile_depth",
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
        }

    @unittest.skip("See https://github.com/nautobot/nautobot/issues/3083")
    def test_get_object_with_permission(self):
        """Skipped temporarily due to https://github.com/nautobot/nautobot/issues/3083."""
