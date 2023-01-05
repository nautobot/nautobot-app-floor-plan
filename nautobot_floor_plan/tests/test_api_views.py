"""Unit tests for nautobot_floor_plan."""
from nautobot.utilities.testing import APIViewTestCases

from nautobot_floor_plan import models
from nautobot_floor_plan.tests import fixtures


class FloorPlanAPIViewTest(APIViewTestCases.APIViewTestCase):  # pylint: disable=too-many-ancestors
    """Test the API viewsets for FloorPlan."""

    model = models.FloorPlan
    bulk_update_data = {"x_size": 10, "y_size": 1}
    brief_fields = ["display", "id", "url", "x_size", "y_size"]

    @classmethod
    def setUpTestData(cls):
        data = fixtures.create_prerequisites(floor_count=6)
        fixtures.create_floor_plans(data["floors"][:3])
        cls.create_data = [
            {
                "location": data["floors"][3].pk,
                "x_size": 1,
                "y_size": 2,
            },
            {
                "location": data["floors"][4].pk,
                "x_size": 3,
                "y_size": 4,
            },
            {
                "location": data["floors"][5].pk,
                "x_size": 4,
                "y_size": 5,
            },
        ]
