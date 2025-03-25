"""Test FloorPlan Filter."""

from unittest.mock import MagicMock, patch

from django.test import TestCase
from nautobot.dcim.models import Rack, RackGroup
from nautobot.extras.models import Tag

from nautobot_floor_plan import choices, filter_extensions, filters, models
from nautobot_floor_plan.choices import CustomAxisLabelsChoices
from nautobot_floor_plan.tests import fixtures, utils


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
        cls.device_type = data["device_type"]
        cls.device_role = data["device_role"]
        cls.manufacturer = data["manufacturer"]
        cls.floor_plans = fixtures.create_floor_plans(cls.floors)

        # Create rack and rack group tiles
        for floor_plan in cls.floor_plans:
            for y in range(1, floor_plan.y_size + 1):
                for x in range(1, floor_plan.x_size + 1):
                    if (x + y) % 2 == 0:
                        rack_group = RackGroup.objects.create(
                            name=f"RackGroup ({x}, {y}) for floor {floor_plan.location}",
                            location=floor_plan.location,
                        )
                        rack = Rack.objects.create(
                            name=f"Rack ({x}, {y}) for floor {floor_plan.location}",
                            status=cls.active_status,
                            location=floor_plan.location,
                            rack_group=rack_group,
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
        # Create a rack group
        rack_group = RackGroup.objects.create(name="Test Rack Group", location=self.floors[0])

        # Create three tiles with the rack group
        for i in range(3):
            models.FloorPlanTile.objects.create(
                floor_plan=self.floor_plans[0],
                status=self.active_status,
                x_origin=i,
                y_origin=0,
                rack_group=rack_group,
                allocation_type=choices.AllocationTypeChoices.RACKGROUP,
            )

        # Create a tile without a rack group
        models.FloorPlanTile.objects.create(
            floor_plan=self.floor_plans[0],
            status=self.active_status,
            x_origin=3,
            y_origin=0,
        )

        params = {"rack_group": [rack_group.pk]}
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


class TestFloorPlanCoordinateFilter(TestCase):
    """Test FloorPlanCoordinateFilter functionality."""

    @classmethod
    def setUpTestData(cls):
        """Setup test data for FloorPlan and FloorPlanCoordinateFilter."""
        data = fixtures.create_prerequisites()
        cls.floor_plan = fixtures.create_floor_plans(data["floors"])[0]

        # Create custom labels for testing
        utils.create_custom_labels(
            cls.floor_plan,
            [
                {
                    "start": "1",
                    "end": "5",
                    "step": 1,
                    "increment_letter": False,
                    "label_type": CustomAxisLabelsChoices.NUMBERS,
                },
            ],
            axis="X",
        )

        utils.create_custom_labels(
            cls.floor_plan,
            [
                {
                    "start": "A",
                    "end": "E",
                    "step": 1,
                    "increment_letter": True,
                    "label_type": CustomAxisLabelsChoices.LETTERS,
                },
            ],
            axis="Y",
        )

        # Create some floor plan tiles for testing
        cls.tile1 = models.FloorPlanTile.objects.create(
            floor_plan=cls.floor_plan, x_origin=1, y_origin=1, status=data["status"]
        )

        cls.tile2 = models.FloorPlanTile.objects.create(
            floor_plan=cls.floor_plan, x_origin=2, y_origin=2, status=data["status"]
        )

    @patch("nautobot_floor_plan.filter_extensions.LabelToPositionConverter")
    @patch("nautobot_floor_plan.models.FloorPlan.objects.get")
    def test_filter_with_x_coordinate(self, mock_get, mock_converter):
        """Test filtering by X coordinate value."""
        # Setup mocks
        mock_get.return_value = self.floor_plan
        converter_instance = MagicMock()
        converter_instance.convert.return_value = (1, None)  # Return position 1
        mock_converter.return_value = converter_instance

        # Create the filter instance
        filter_instance = filter_extensions.FloorPlanCoordinateFilter(axis="X", field_name="x_origin")
        filter_instance.parent = MagicMock()
        filter_instance.parent.data = {"nautobot_floor_plan_floor_plan": self.floor_plan.pk}

        # Apply filter with label "1"
        test_qs = models.FloorPlanTile.objects.all()
        filtered_qs = filter_instance.filter(test_qs, "1")

        # Verify that the filter was applied correctly
        self.assertEqual(filtered_qs.count(), 1)
        self.assertEqual(filtered_qs.first().x_origin, 1)

    @patch("nautobot_floor_plan.filter_extensions.LabelToPositionConverter")
    @patch("nautobot_floor_plan.models.FloorPlan.objects.get")
    def test_filter_with_y_coordinate(self, mock_get, mock_converter):
        """Test filtering by Y coordinate value."""
        # Setup mocks
        mock_get.return_value = self.floor_plan
        converter_instance = MagicMock()
        converter_instance.convert.return_value = (2, None)  # Return position 2
        mock_converter.return_value = converter_instance

        # Create the filter instance
        filter_instance = filter_extensions.FloorPlanCoordinateFilter(axis="Y", field_name="y_origin")
        filter_instance.parent = MagicMock()
        filter_instance.parent.data = {"nautobot_floor_plan_floor_plan": self.floor_plan.pk}

        # Apply filter with label "B" or "2" (depends on your label system)
        test_qs = models.FloorPlanTile.objects.all()
        filtered_qs = filter_instance.filter(test_qs, "B")

        # Verify that the filter was applied correctly
        self.assertEqual(filtered_qs.count(), 1)
        self.assertEqual(filtered_qs.first().y_origin, 2)

    @patch("nautobot_floor_plan.models.FloorPlan.objects.get")
    def test_filter_with_invalid_floor_plan(self, mock_get):
        """Test filtering when the FloorPlan does not exist."""
        mock_get.side_effect = models.FloorPlan.DoesNotExist

        # Create filter instance
        filter_instance = filter_extensions.FloorPlanCoordinateFilter(axis="X", field_name="x_origin")
        filter_instance.parent = MagicMock()
        filter_instance.parent.data = {"nautobot_floor_plan_floor_plan": self.floor_plan.pk}

        # Test the filter with a non-existent floor plan
        test_qs = models.FloorPlanTile.objects.all()
        filtered_qs = filter_instance.filter(test_qs, "1")

        # The original queryset should be returned unchanged
        self.assertEqual(list(filtered_qs), list(test_qs))

    @patch("nautobot_floor_plan.filter_extensions.PositionToLabelConverter")
    @patch("nautobot_floor_plan.models.FloorPlan.objects.get")
    def test_display_value_with_valid_value(self, mock_get, mock_converter):
        """Test display_value with a valid position value."""
        # Setup mocks
        mock_get.return_value = self.floor_plan
        converter_instance = MagicMock()
        converter_instance.convert.return_value = "A"  # Return label "A"
        mock_converter.return_value = converter_instance

        # Create filter instance
        filter_instance = filter_extensions.FloorPlanCoordinateFilter(axis="Y", field_name="y_origin")
        filter_instance.parent = MagicMock()
        filter_instance.parent.data = {"nautobot_floor_plan_floor_plan": self.floor_plan.pk}

        # Test display_value
        result = filter_instance.display_value("1")

        # Verify the result
        self.assertEqual(result, "A")
        mock_converter.assert_called_once_with(1, "Y", self.floor_plan)

    @patch("nautobot_floor_plan.models.FloorPlan.objects.get")
    def test_display_value_with_invalid_floor_plan(self, mock_get):
        """Test display_value when the FloorPlan does not exist."""
        mock_get.side_effect = models.FloorPlan.DoesNotExist

        # Create filter instance
        filter_instance = filter_extensions.FloorPlanCoordinateFilter(axis="X", field_name="x_origin")
        filter_instance.parent = MagicMock()
        filter_instance.parent.data = {"nautobot_floor_plan_floor_plan": self.floor_plan.pk}

        # Test display_value with a non-existent floor plan
        result = filter_instance.display_value("1")

        # Original value should be returned
        self.assertEqual(result, "1")
