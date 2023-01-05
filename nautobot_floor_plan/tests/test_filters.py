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
        data = fixtures.create_prerequisites()
        fixtures.create_floor_plans(data["floors"])

    def test_q_search_location_name(self):
        """Test using Q search with name of Location."""
        params = {"q": "Floor"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)
        params = {"q": "Floor 1"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_q_search_location_slug(self):
        """Test using Q search with slug of Location."""
        params = {"q": "building-1"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)
        params = {"q": "building-1-floor-1"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_q_invalid(self):
        """Test using invalid Q search for FloorPlan."""
        params = {"q": "not-a-location"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)
