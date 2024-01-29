"""Unit tests for nautobot_floor_plan."""
from nautobot.apps.testing import APIViewTestCases

from nautobot_floor_plan import models
from nautobot_floor_plan.tests import fixtures


class FloorPlanAPIViewTest(APIViewTestCases.APIViewTestCase):
    # pylint: disable=too-many-ancestors
    """Test the API viewsets for FloorPlan."""

    model = models.FloorPlan
    create_data = [
        {
            "name": "Test Model 1",
            "description": "test description",
        },
        {
            "name": "Test Model 2",
        },
    ]
    bulk_update_data = {"description": "Test Bulk Update"}

    @classmethod
    def setUpTestData(cls):
        fixtures.create_floorplan()
