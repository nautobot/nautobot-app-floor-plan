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

    def test_filter_with_x_coordinate(self):
        """Test filtering by X coordinate value."""
        # Create the filter instance
        filter_instance = filter_extensions.FloorPlanCoordinateFilter(axis="X", field_name="x_origin")
        filter_instance.parent = MagicMock()
        filter_instance.parent.data = {"nautobot_floor_plan_floor_plan": self.floor_plan.pk}

        # Apply filter with label "1"
        # manually patch the LabelToPositionConverter for this test
        original_converter = filter_extensions.LabelToPositionConverter
        try:
            # Create a mock converter
            mock_converter = MagicMock()
            mock_instance = MagicMock()
            mock_instance.convert.return_value = (1, None)  # Return position 1
            mock_converter.return_value = mock_instance

            # Replace the original with the mock
            filter_extensions.LabelToPositionConverter = mock_converter

            # Run the test
            test_qs = models.FloorPlanTile.objects.all()
            filtered_qs = filter_instance.filter(test_qs, "1")

            # Verify that the filter was applied correctly
            self.assertEqual(filtered_qs.count(), 1)
            self.assertEqual(filtered_qs.first().x_origin, 1)

            # Verify the mock was called correctly
            mock_converter.assert_called_once_with("1", "X", self.floor_plan)
        finally:
            # Restore the original converter
            filter_extensions.LabelToPositionConverter = original_converter

    def test_filter_with_y_coordinate(self):
        """Test filtering by Y coordinate value."""
        # Create the filter instance
        filter_instance = filter_extensions.FloorPlanCoordinateFilter(axis="Y", field_name="y_origin")
        filter_instance.parent = MagicMock()
        filter_instance.parent.data = {"nautobot_floor_plan_floor_plan": self.floor_plan.pk}

        # Apply filter with label "B"
        # manually patching the LabelToPositionConverter for this test
        original_converter = filter_extensions.LabelToPositionConverter
        try:
            # Create a mock converter
            mock_converter = MagicMock()
            mock_instance = MagicMock()
            mock_instance.convert.return_value = (2, None)  # Return position 2
            mock_converter.return_value = mock_instance

            # Replace the original with the mock
            filter_extensions.LabelToPositionConverter = mock_converter

            # Run the test
            test_qs = models.FloorPlanTile.objects.all()
            filtered_qs = filter_instance.filter(test_qs, "B")

            # Verify that the filter was applied correctly
            self.assertEqual(filtered_qs.count(), 1)
            self.assertEqual(filtered_qs.first().y_origin, 2)

            # Verify the mock was called correctly
            mock_converter.assert_called_once_with("B", "Y", self.floor_plan)
        finally:
            # Restore the original converter
            filter_extensions.LabelToPositionConverter = original_converter

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

    def test_display_value_with_real_converter(self):
        """Test display_value with the actual PositionToLabelConverter."""
        # Create filter instance
        filter_instance = filter_extensions.FloorPlanCoordinateFilter(axis="Y", field_name="y_origin")
        filter_instance.parent = MagicMock()
        filter_instance.parent.data = {"nautobot_floor_plan_floor_plan": self.floor_plan.pk}

        # Test display_value
        result = filter_instance.display_value("1")  # Pass a valid value

        # Verify the result matches what we expect from the real converter
        self.assertEqual(result, "A")

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


class TestFloorPlanCoordinateFilterDefaultLabels(TestCase):
    """Test FloorPlanCoordinateFilter with default (non-custom) letter and number labels.

    Regression test for the bug where clicking an X-axis letter label (e.g. "A") on
    the SVG floor plan returned ALL racks instead of only the racks in that column.
    The filter was passing the raw letter string directly to the DB IntegerField query.
    """

    @classmethod
    def setUpTestData(cls):
        """Set up a 5x5 floor plan with letter X-axis and numeric Y-axis, and 25 rack tiles."""
        data = fixtures.create_prerequisites()
        cls.active_status = data["status"]

        # Floor plan with X=letters (A-E), Y=numbers (1-5)
        cls.floor_plan = models.FloorPlan(
            location=data["floors"][0],
            x_size=5,
            y_size=5,
            x_axis_labels=choices.AxisLabelsChoices.LETTERS,
            y_axis_labels=choices.AxisLabelsChoices.NUMBERS,
            x_origin_seed=1,
            y_origin_seed=1,
        )
        cls.floor_plan.validated_save()

        # Create 25 tiles: x_origin 1-5 maps to labels A-E, y_origin 1-5 maps to labels 1-5
        for y in range(1, 6):
            for x in range(1, 6):
                models.FloorPlanTile.objects.create(
                    floor_plan=cls.floor_plan,
                    x_origin=x,
                    y_origin=y,
                    status=cls.active_status,
                )

    def _make_filter(self, axis, field_name):
        """Return a FloorPlanCoordinateFilter with its parent wired to cls.floor_plan."""
        f = filter_extensions.FloorPlanCoordinateFilter(axis=axis, field_name=field_name)
        f.parent = MagicMock()
        f.parent.data = {"nautobot_floor_plan_floor_plan": self.floor_plan.pk}
        return f

    # ------------------------------------------------------------------
    # X-axis (letter labels) – this was broken, reports in issue #211
    # ------------------------------------------------------------------

    def test_x_letter_label_returns_only_matching_column(self):
        """Clicking column 'A' (x_origin=1) must return exactly 5 tiles, not all 25."""
        f = self._make_filter("X", "x_origin")
        qs = models.FloorPlanTile.objects.filter(floor_plan=self.floor_plan)
        result = f.filter(qs, "A")
        self.assertEqual(result.count(), 5)
        self.assertEqual(set(result.values_list("x_origin", flat=True)), {1})

    def test_x_letter_label_mid_column(self):
        """Clicking column 'C' (x_origin=3) must return exactly the 5 tiles in that column."""
        f = self._make_filter("X", "x_origin")
        qs = models.FloorPlanTile.objects.filter(floor_plan=self.floor_plan)
        result = f.filter(qs, "C")
        self.assertEqual(result.count(), 5)
        self.assertEqual(set(result.values_list("x_origin", flat=True)), {3})

    def test_x_letter_label_last_column(self):
        """Clicking column 'E' (x_origin=5) must return exactly 5 tiles."""
        f = self._make_filter("X", "x_origin")
        qs = models.FloorPlanTile.objects.filter(floor_plan=self.floor_plan)
        result = f.filter(qs, "E")
        self.assertEqual(result.count(), 5)
        self.assertEqual(set(result.values_list("x_origin", flat=True)), {5})

    # ------------------------------------------------------------------
    # Y-axis (numeric labels) – was already working; verify the fix didn't break it
    # ------------------------------------------------------------------

    def test_y_numeric_label_returns_only_matching_row(self):
        """Clicking row '1' (y_origin=1) must return exactly 5 tiles."""
        f = self._make_filter("Y", "y_origin")
        qs = models.FloorPlanTile.objects.filter(floor_plan=self.floor_plan)
        result = f.filter(qs, "1")
        self.assertEqual(result.count(), 5)
        self.assertEqual(set(result.values_list("y_origin", flat=True)), {1})

    def test_y_numeric_label_mid_row(self):
        """Clicking row '3' (y_origin=3) must return exactly 5 tiles."""
        f = self._make_filter("Y", "y_origin")
        qs = models.FloorPlanTile.objects.filter(floor_plan=self.floor_plan)
        result = f.filter(qs, "3")
        self.assertEqual(result.count(), 5)
        self.assertEqual(set(result.values_list("y_origin", flat=True)), {3})


class TestFloorPlanCoordinateFilterSeedAndStep(TestCase):
    """Test FloorPlanCoordinateFilter with non-default seed and step values.

    The label generation formula is: label = seed + (position - seed) * step
    The inverse is handled by axis_clean_label_conversion() in utils/general.py.

    Each test method covers one configuration so data stays isolated.
    """

    @classmethod
    def setUpTestData(cls):
        """Shared prerequisites for all seed/step tests."""
        cls.data = fixtures.create_prerequisites()
        cls.active_status = cls.data["status"]

    def _make_floor_plan(self, floor_idx, x_size, y_size, **kwargs):
        """Create and return a validated FloorPlan on the given floor index."""
        fp = models.FloorPlan(
            location=self.data["floors"][floor_idx],
            x_size=x_size,
            y_size=y_size,
            **kwargs,
        )
        fp.validated_save()
        return fp

    def _make_tiles(self, floor_plan):
        """Create one tile per grid cell for the given floor plan."""
        for y in range(floor_plan.y_origin_seed, floor_plan.y_origin_seed + floor_plan.y_size):
            for x in range(floor_plan.x_origin_seed, floor_plan.x_origin_seed + floor_plan.x_size):
                models.FloorPlanTile.objects.create(
                    floor_plan=floor_plan, x_origin=x, y_origin=y, status=self.active_status
                )

    def _make_filter(self, floor_plan, axis, field_name):
        """Return a wired FloorPlanCoordinateFilter for the given floor plan."""
        f = filter_extensions.FloorPlanCoordinateFilter(axis=axis, field_name=field_name)
        f.parent = MagicMock()
        f.parent.data = {"nautobot_floor_plan_floor_plan": floor_plan.pk}
        return f

    # ------------------------------------------------------------------
    # Non-default seed, letter X-axis
    # label = seed + (position - seed) * 1  →  C(3),D(4),E(5),F(6),G(7)
    # ------------------------------------------------------------------

    def test_letter_axis_non_default_seed(self):
        """seed=3 (C), step=1: label 'E' must resolve to x_origin=5."""
        fp = self._make_floor_plan(
            0,
            x_size=5,
            y_size=3,
            x_axis_labels=choices.AxisLabelsChoices.LETTERS,
            y_axis_labels=choices.AxisLabelsChoices.NUMBERS,
            x_origin_seed=3,
            y_origin_seed=1,
        )
        self._make_tiles(fp)
        f = self._make_filter(fp, "X", "x_origin")
        qs = models.FloorPlanTile.objects.filter(floor_plan=fp)

        result = f.filter(qs, "C")  # first column, x_origin=3
        self.assertEqual(result.count(), 3)
        self.assertEqual(set(result.values_list("x_origin", flat=True)), {3})

        result = f.filter(qs, "E")  # third column, x_origin=5
        self.assertEqual(result.count(), 3)
        self.assertEqual(set(result.values_list("x_origin", flat=True)), {5})

    # ------------------------------------------------------------------
    # Non-default step=2, letter X-axis
    # position 1→A(1), 2→C(3), 3→E(5), 4→G(7), 5→I(9)
    # ------------------------------------------------------------------

    def test_letter_axis_step_2(self):
        """seed=1, step=2: label 'C' must resolve to x_origin=2, 'E' to x_origin=3."""
        fp = self._make_floor_plan(
            1,
            x_size=5,
            y_size=3,
            x_axis_labels=choices.AxisLabelsChoices.LETTERS,
            y_axis_labels=choices.AxisLabelsChoices.NUMBERS,
            x_origin_seed=1,
            y_origin_seed=1,
            x_axis_step=2,
        )
        self._make_tiles(fp)
        f = self._make_filter(fp, "X", "x_origin")
        qs = models.FloorPlanTile.objects.filter(floor_plan=fp)

        result = f.filter(qs, "C")  # step=2: C(3) → x_origin=2
        self.assertEqual(result.count(), 3)
        self.assertEqual(set(result.values_list("x_origin", flat=True)), {2})

        result = f.filter(qs, "E")  # step=2: E(5) → x_origin=3
        self.assertEqual(result.count(), 3)
        self.assertEqual(set(result.values_list("x_origin", flat=True)), {3})

    # ------------------------------------------------------------------
    # Non-default seed, numeric Y-axis
    # seed=5, step=1: positions 5,6,7,8,9 → labels 5,6,7,8,9
    # ------------------------------------------------------------------

    def test_numeric_axis_non_default_seed(self):
        """seed=5, step=1: label '7' must resolve to y_origin=7."""
        fp = self._make_floor_plan(
            2,
            x_size=3,
            y_size=5,
            x_axis_labels=choices.AxisLabelsChoices.NUMBERS,
            y_axis_labels=choices.AxisLabelsChoices.NUMBERS,
            x_origin_seed=1,
            y_origin_seed=5,
        )
        self._make_tiles(fp)
        f = self._make_filter(fp, "Y", "y_origin")
        qs = models.FloorPlanTile.objects.filter(floor_plan=fp)

        result = f.filter(qs, "5")  # first row, y_origin=5
        self.assertEqual(result.count(), 3)
        self.assertEqual(set(result.values_list("y_origin", flat=True)), {5})

        result = f.filter(qs, "7")  # third row, y_origin=7
        self.assertEqual(result.count(), 3)
        self.assertEqual(set(result.values_list("y_origin", flat=True)), {7})

    # ------------------------------------------------------------------
    # Non-default step=2, numeric Y-axis
    # position 1→1, 2→3, 3→5, 4→7, 5→9
    # ------------------------------------------------------------------

    def test_numeric_axis_step_2(self):
        """seed=1, step=2: label '5' must resolve to y_origin=3, label '9' to y_origin=5."""
        fp = self._make_floor_plan(
            3,
            x_size=3,
            y_size=5,
            x_axis_labels=choices.AxisLabelsChoices.NUMBERS,
            y_axis_labels=choices.AxisLabelsChoices.NUMBERS,
            x_origin_seed=1,
            y_origin_seed=1,
            y_axis_step=2,
        )
        self._make_tiles(fp)
        f = self._make_filter(fp, "Y", "y_origin")
        qs = models.FloorPlanTile.objects.filter(floor_plan=fp)

        result = f.filter(qs, "5")  # step=2: label 5 → y_origin=3
        self.assertEqual(result.count(), 3)
        self.assertEqual(set(result.values_list("y_origin", flat=True)), {3})

        result = f.filter(qs, "9")  # step=2: label 9 → y_origin=5
        self.assertEqual(result.count(), 3)
        self.assertEqual(set(result.values_list("y_origin", flat=True)), {5})
