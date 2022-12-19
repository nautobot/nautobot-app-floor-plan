"""Unit tests for nautobot_floor_plan."""
import unittest

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
        {
            "name": "Test Model 3",
            "slug": "test-model-3",
        },
    ]
    bulk_update_data = {"description": "Test Bulk Update"}
    brief_fields = ["display", "id", "name", "slug", "url"]

    @classmethod
    def setUpTestData(cls):
        fixtures.create_floorplan()

    @unittest.skip("TODO")
    def test_notes_url_on_object(self):
        """Not yet implemented."""
