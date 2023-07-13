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

    @classmethod
    def setUpTestData(cls):
        fixtures.create_floorplan()

    def test_bulk_import_objects_with_constrained_permission(self):
        """Auto-generated model does not implement `bulk_import`."""

    def test_bulk_import_objects_with_permission(self):
        """Auto-generated model does not implement `bulk_import`."""

    def test_bulk_import_objects_without_permission(self):
        """Auto-generated model does not implement `bulk_import`."""

    def test_bulk_import_objects_with_permission_csv_file(self):
        """Auto-generated model does not implement `bulk_import`."""

    def test_has_advanced_tab(self):
        """Auto-generated model does not implement an advanced tab."""
