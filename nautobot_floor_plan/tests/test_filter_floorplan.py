"""Test FloorPlan Filter."""
from django.test import TestCase
from nautobot_floor_plan import filters
from nautobot_floor_plan import models
from nautobot_floor_plan.tests import fixtures


class FloorPlanFilterTestCase(TestCase):
    """FloorPlan Filter Test Case."""

    queryset = models.FloorPlan.objects.all()
    filterset = filters.FloorPlanFilterSet

    @classmethod
    def setUpTestData(cls):
        """Setup test data for FloorPlan Model."""
        fixtures.create_floorplan()

    def test_q_search_name(self):
        """Test using Q search with name of FloorPlan."""
        params = {"q": "Test One"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_q_search_slug(self):
        """Test using Q search with slug of FloorPlan."""
        params = {"q": "test-one"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_q_invalid(self):
        """Test using invalid Q search for FloorPlan."""
        params = {"q": "test-five"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)
