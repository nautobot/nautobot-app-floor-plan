"""Unit tests for views."""

from nautobot.apps.testing import ViewTestCases

from nautobot_floor_plan import models
from nautobot_floor_plan.tests import fixtures


class FloorPlanViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    # pylint: disable=too-many-ancestors
    """Test the FloorPlan views."""

    model = models.FloorPlan
    bulk_edit_data = {"description": "Bulk edit views"}
    form_data = {
        "name": "Test 1",
        "description": "Initial model",
    }

    update_data = {
        "name": "Test 2",
        "description": "Updated model",
    }

    @classmethod
    def setUpTestData(cls):
        fixtures.create_floorplan()
