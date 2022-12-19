"""Unit tests for views."""
from nautobot.utilities.testing import ViewTestCases

from nautobot_floor_plan import models
from nautobot_floor_plan.tests import fixtures


class FloorPlanViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    # pylint: disable=too-many-ancestors
    """Test the FloorPlan views."""

    model = models.FloorPlan
    bulk_edit_data = {"description": "Bulk edit views"}
    form_data = {
        "name": "Test 1",
        "slug": "test-1",
        "description": "Initial model",
    }
    csv_data = (
        "name,slug",
        "Test 2,test-2",
        "Test 3,test-3",
        "Test 4,test-4",
    )

    @classmethod
    def setUpTestData(cls):
        fixtures.create_floorplan()

    def test_bulk_import_objects_with_constrained_permission(self):
        pass

    def test_bulk_import_objects_with_permission(self):
        pass

    def test_bulk_import_objects_without_permission(self):
        pass
