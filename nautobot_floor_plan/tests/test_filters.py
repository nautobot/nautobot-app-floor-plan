"""Test FloorPlan Filter."""

from nautobot.apps.testing import FilterTestCases

from nautobot_floor_plan import filters, models
from nautobot_floor_plan.tests import fixtures


class FloorPlanFilterTestCase(FilterTestCases.FilterTestCase):
    """FloorPlan Filter Test Case."""

    queryset = models.FloorPlan.objects.all()
    filterset = filters.FloorPlanFilterSet
    generic_filter_tests = (
        ("id",),
        ("created",),
        ("last_updated",),
        ("name",),
    )

    @classmethod
    def setUpTestData(cls):
        """Setup test data for FloorPlan Model."""
        fixtures.create_floorplan()

    def test_q_search_name(self):
        """Test using Q search with name of FloorPlan."""
        params = {"q": "Test One"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_q_invalid(self):
        """Test using invalid Q search for FloorPlan."""
        params = {"q": "test-five"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)
