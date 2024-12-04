"""Test FloorPlan Filter."""

from django.test import TestCase
from nautobot.dcim.models import Rack, RackGroup
from nautobot.extras.models import Tag

from nautobot_floor_plan import filters, models
from nautobot_floor_plan.tests import fixtures


class TestFloorPlanFilterSet(TestCase):
    """FloorPlan Filter Test Case."""

    queryset = models.FloorPlan.objects.all()
    filterset = filters.FloorPlanFilterSet

    @classmethod
    def setUpTestData(cls):
        """Setup test data for FloorPlan Model."""
        data = fixtures.create_prerequisites()
        cls.floors = data["floors"]
        cls.building = data["building"]
        fixtures.create_floor_plans(cls.floors)

    def test_q_search_location_name(self):
        """Test using Q search with name of Location."""
        params = {"q": "Floor"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)
        params = {"q": "Floor 1"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_q_invalid(self):
        """Test using invalid Q search for FloorPlan."""
        params = {"q": "not-a-location"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_location(self):
        """Test filtering by Location."""
        params = {"location": [self.floors[0].name, self.floors[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_tags(self):
        """Test filtering by Tags."""
        self.floors[0].floor_plan.tags.add(Tag.objects.create(name="Planned"))
        params = {"tags": ["Planned"]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_x_size(self):
        """Test filtering by x_size."""
        params = {"x_size": [1, 2]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"x_size": [11]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_y_size(self):
        """Test filtering by y_size."""
        params = {"y_size": [1, 2]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"y_size": [11]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_filter_by_parent_location(self):
        """Test filtering by parent location."""
        params = {
            "parent_location": self.building.pk,
        }
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)


class TestFloorPlanTileFilterSet(TestCase):
    """FloorPlanTile FilterSet test case."""

    queryset = models.FloorPlanTile.objects.all()
    filterset = filters.FloorPlanTileFilterSet

    @classmethod
    def setUpTestData(cls):
        """Set up test data for FloorPlanTile model."""
        data = fixtures.create_prerequisites()
        cls.floors = data["floors"]
        cls.active_status = data["status"]
        cls.floor_plans = fixtures.create_floor_plans(cls.floors)
        for floor_plan in cls.floor_plans:
            for y in range(1, floor_plan.y_size + 1):
                for x in range(1, floor_plan.x_size + 1):
                    if (x + y) % 2 == 0:
                        rack = Rack.objects.create(
                            name=f"Rack ({x}, {y}) for floor {floor_plan.location}",
                            status=cls.active_status,
                            location=floor_plan.location,
                        )
                        rack_group = RackGroup.objects.create(
                            name=f"RackGroup ({x}, {y}) for floor {floor_plan.location}",
                            location=floor_plan.location,
                        )
                    else:
                        rack = None
                        rack_group = None
                    floor_plan_tile = models.FloorPlanTile(
                        floor_plan=floor_plan,
                        status=cls.active_status,
                        x_origin=x,
                        y_origin=y,
                        rack=rack,
                        rack_group=rack_group,
                    )
                    floor_plan_tile.validated_save()

    def test_q_search_location_name(self):
        """Test using Q search with name of Location."""
        params = {"q": "Floor"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 30)
        params = {"q": "Floor 1"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_q_invalid(self):
        """Test using invalid Q search."""
        params = {"q": "no-matching"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_location(self):
        """Test filtering by Location."""
        params = {"location": [self.floors[0].name, self.floors[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 5)

    def test_rack(self):
        """Test filtering by Rack."""
        params = {"rack": list(Rack.objects.all()[:3])}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_rack_group(self):
        """Test filtering by RackGroup."""
        params = {"rack_group": list(RackGroup.objects.all()[:3])}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_tags(self):
        """Test filtering by Tags."""
        self.queryset.first().tags.add(Tag.objects.create(name="Relevant"))
        params = {"tags": ["Relevant"]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_floor_plan(self):
        """Test filtering by FloorPlan."""
        params = {"floor_plan": [self.floor_plans[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)

    def test_x_origin(self):
        """Test filtering by x_origin position."""
        params = {"x_origin": [1]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 10)

    def test_y_origin(self):
        """Test filtering by y_origin position."""
        params = {"y_origin": [1]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 10)
