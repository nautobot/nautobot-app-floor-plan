"""Unit tests for nautobot_floor_plan."""
from nautobot.utilities.testing import APIViewTestCases

from nautobot_floor_plan import models
from nautobot_floor_plan.tests import fixtures


class FloorPlanAPIViewTest(APIViewTestCases.APIViewTestCase):
    # pylint: disable=too-many-ancestors
    """Test the API viewsets for FloorPlan."""

    model = models.FloorPlan
    create_data = [
        {
            "name": "Test Model 1",
            "slug": "test-model-1",
        },
        {
            "name": "Test Model 2",
            "slug": "test-model-2",
        },
    ]
    bulk_update_data = {"description": "Test Bulk Update"}
    brief_fields = ["created", "description", "display", "id", "last_updated", "name", "slug", "url"]

    @classmethod
    def setUpTestData(cls):
        fixtures.create_floorplan()
