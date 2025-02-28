"""Tests for the SVG rendering functionality of the Nautobot Floor Plan app."""

from unittest.mock import MagicMock, patch

from django.test import TestCase

from nautobot_floor_plan.choices import ObjectOrientationChoices
from nautobot_floor_plan.svg import FloorPlanSVG

# pylint: disable=protected-access


@patch("nautobot_floor_plan.svg.reverse", return_value="/mock/url/")
class FloorPlanSVGTestCase(TestCase):
    """Test cases for FloorPlanSVG class."""

    def setUp(self):
        """Set up test environment."""
        # Create mock floor plan
        self.floor_plan = MagicMock()
        self.floor_plan.x_size = 5
        self.floor_plan.y_size = 5
        self.floor_plan.tile_width = 100
        self.floor_plan.tile_depth = 100
        self.floor_plan.x_origin_seed = 1
        self.floor_plan.y_origin_seed = 1

        # Mock location
        self.location = MagicMock()
        self.location.pk = 1
        self.floor_plan.location = self.location

        # Create mock user
        self.user = MagicMock()

        # Base URL for testing
        self.base_url = "http://testserver"

        # Mock drawing
        self.drawing = MagicMock()

    def test_setup_drawing(self, _):
        """Test the _setup_drawing method."""
        # Create SVG renderer with mocked reverse
        svg = FloorPlanSVG(floor_plan=self.floor_plan, user=self.user, base_url=self.base_url)

        # Call method
        with patch("svgwrite.Drawing") as mock_drawing_class:
            mock_drawing = MagicMock()
            mock_drawing_class.return_value = mock_drawing

            result = svg._setup_drawing(width=500, depth=500)

            # Assertions
            mock_drawing_class.assert_called_once_with(size=(500, 500), debug=False)
            mock_drawing.viewbox.assert_called_once_with(0, 0, width=500, height=500)
            mock_drawing.rect.assert_called()  # Check that rect was called for the border

            self.assertEqual(result, mock_drawing)

    def test_setup_drawing_adds_stylesheet(self, _):
        """Test that _setup_drawing adds the CSS stylesheet."""
        # Create SVG renderer with mocked reverse
        svg = FloorPlanSVG(floor_plan=self.floor_plan, user=self.user, base_url=self.base_url)

        # Setup mocks
        with patch("os.path.join") as mock_path_join, patch("builtins.open") as mock_open, patch(
            "svgwrite.Drawing"
        ) as mock_drawing_class:
            mock_path_join.return_value = "/mock/path/to/svg.css"
            mock_file = MagicMock()
            mock_file.__enter__.return_value.read.return_value = "mock css content"
            mock_open.return_value = mock_file

            mock_drawing = MagicMock()
            mock_drawing_class.return_value = mock_drawing
            mock_style = MagicMock()
            mock_drawing.style.return_value = mock_style

            # Call method
            svg._setup_drawing(width=500, depth=500)

            # Assertions
            mock_path_join.assert_called()
            mock_open.assert_called_with("/mock/path/to/svg.css", "r", encoding="utf-8")
            mock_drawing.style.assert_called_with("mock css content")
            mock_drawing.defs.add.assert_called_with(mock_style)

    def test_draw_grid(self, _):
        """Test the _draw_grid method."""
        # Create SVG renderer with mocked reverse
        svg = FloorPlanSVG(floor_plan=self.floor_plan, user=self.user, base_url=self.base_url)

        # Setup
        mock_drawing = MagicMock()

        # Mock the methods called by _draw_grid
        svg._draw_grid_lines = MagicMock()
        svg._generate_axis_labels = MagicMock(return_value=(["A", "B", "C"], ["1", "2", "3"]))
        svg._draw_axis_labels = MagicMock()
        svg._draw_tile_links = MagicMock()

        # Call method
        svg._draw_grid(mock_drawing)

        # Assertions
        svg._draw_grid_lines.assert_called_once_with(mock_drawing)
        svg._generate_axis_labels.assert_called_once()
        svg._draw_axis_labels.assert_called_once_with(mock_drawing, ["A", "B", "C"], ["1", "2", "3"])
        svg._draw_tile_links.assert_called_once_with(mock_drawing, ["A", "B", "C"], ["1", "2", "3"])

    def test_generate_axis_labels(self, _):
        """Test the _generate_axis_labels method."""
        # Create SVG renderer with mocked reverse
        svg = FloorPlanSVG(floor_plan=self.floor_plan, user=self.user, base_url=self.base_url)

        # Setup
        self.floor_plan.generate_labels = MagicMock()
        self.floor_plan.generate_labels.side_effect = lambda axis, _: (
            ["A", "B", "C", "D", "E"] if axis == "X" else ["1", "2", "3", "4", "5"]
        )

        # Call method
        x_labels, y_labels = svg._generate_axis_labels()

        # Assertions
        self.assertEqual(x_labels, ["A", "B", "C", "D", "E"])
        self.assertEqual(y_labels, ["1", "2", "3", "4", "5"])
        self.floor_plan.generate_labels.assert_any_call("X", 5)
        self.floor_plan.generate_labels.assert_any_call("Y", 5)

    def test_draw_grid_lines(self, _):
        """Test the _draw_grid_lines method."""
        # Create SVG renderer with mocked reverse
        svg = FloorPlanSVG(floor_plan=self.floor_plan, user=self.user, base_url=self.base_url)

        # Setup
        mock_drawing = MagicMock()

        # Call method
        svg._draw_grid_lines(mock_drawing)

        # Assertions - should draw x_size + y_size + 2 lines
        expected_calls = self.floor_plan.x_size + 1 + self.floor_plan.y_size + 1
        self.assertEqual(mock_drawing.line.call_count, expected_calls)
        self.assertEqual(mock_drawing.add.call_count, expected_calls)

    def test_draw_axis_labels(self, _):
        """Test the _draw_axis_labels method."""
        # Create SVG renderer with mocked reverse
        svg = FloorPlanSVG(floor_plan=self.floor_plan, user=self.user, base_url=self.base_url)

        # Setup
        mock_drawing = MagicMock()
        x_labels = ["A", "B", "C", "D", "E"]
        y_labels = ["1", "2", "3", "4", "5"]

        # Call method
        svg._draw_axis_labels(mock_drawing, x_labels, y_labels)

        # Assertions - should add text for each label
        expected_calls = len(x_labels) + len(y_labels)
        self.assertEqual(mock_drawing.text.call_count, expected_calls)
        self.assertEqual(mock_drawing.add.call_count, expected_calls)

    def test_draw_tile_link(self, _):
        """Test the _draw_tile_link method."""
        # Create SVG renderer with mocked reverse
        svg = FloorPlanSVG(floor_plan=self.floor_plan, user=self.user, base_url=self.base_url)

        # Setup
        mock_drawing = MagicMock()
        axis = {"x": "A", "y": "1", "x_idx": 0, "y_idx": 0}

        # Mock the add method to return a link object
        mock_link = MagicMock()
        mock_drawing.add.return_value = mock_link

        # Call method
        svg._draw_tile_link(mock_drawing, axis)

        # Assertions
        mock_drawing.a.assert_called_once()  # Should create an anchor
        mock_drawing.add.assert_called_once()  # Should add the anchor to the drawing
        mock_link.add.assert_called()  # Should add elements to the link

    def test_draw_tile(self, _):
        """Test the _draw_tile method."""
        # Create SVG renderer with mocked reverse
        svg = FloorPlanSVG(floor_plan=self.floor_plan, user=self.user, base_url=self.base_url)

        # Setup
        mock_drawing = MagicMock()
        mock_tile = MagicMock()
        mock_tile.on_group_tile = False
        mock_tile.rack = None
        mock_tile.device = None
        mock_tile.power_panel = None
        mock_tile.power_feed = None

        # Mock the methods called by _draw_tile
        svg._draw_defined_rackgroup_tile = MagicMock()
        svg._draw_edit_delete_button = MagicMock()
        svg._draw_object_tile = MagicMock()

        # Call method
        svg._draw_tile(mock_drawing, mock_tile)

        # Assertions
        svg._draw_defined_rackgroup_tile.assert_called_once_with(mock_drawing, mock_tile)
        svg._draw_edit_delete_button.assert_called_once_with(mock_drawing, mock_tile, 0, 0)
        svg._draw_object_tile.assert_not_called()  # No objects on this tile

    def test_draw_object_tile(self, _):
        """Test the _draw_object_tile method with different object types."""
        # Create SVG renderer with mocked reverse
        svg = FloorPlanSVG(floor_plan=self.floor_plan, user=self.user, base_url=self.base_url)

        # Setup
        mock_drawing = MagicMock()

        # Test cases for different object types
        test_cases = [
            {"object_type": "rack", "expected_obj_type": "Rack"},
            {"object_type": "device", "expected_obj_type": "Device"},
            {"object_type": "power_panel", "expected_obj_type": "Power Panel"},
            {"object_type": "power_feed", "expected_obj_type": "Power Feed"},
        ]

        for case in test_cases:
            # Create mock tile with the specified object
            mock_tile = MagicMock()
            mock_tile.x_origin = 1
            mock_tile.y_origin = 1
            mock_tile.x_size = 1
            mock_tile.y_size = 1
            mock_tile.on_group_tile = True

            # Set all object attributes to None
            mock_tile.rack = None
            mock_tile.device = None
            mock_tile.power_panel = None
            mock_tile.power_feed = None

            # Set the specific object for this test case
            obj_type = case["object_type"]
            mock_obj = MagicMock()
            mock_obj.name = f"Test {obj_type.replace('_', ' ').title()}"

            # Create a proper status object with a string color value
            mock_status = MagicMock()
            mock_status.color = "ff0000"  # Use a valid hex color string
            mock_obj.status = mock_status

            setattr(mock_tile, obj_type, mock_obj)

            # Set the tile status with a proper color string
            mock_tile_status = MagicMock()
            mock_tile_status.color = "ff0000"  # Use a valid hex color string
            mock_tile.status = mock_tile_status

            # Mock methods called by _draw_object_tile
            svg._draw_object_orientation = MagicMock()
            svg._draw_object_text = MagicMock()
            svg._draw_edit_delete_button = MagicMock()

            # Call method
            svg._draw_object_tile(mock_drawing, mock_tile)

            # Assertions
            mock_drawing.a.assert_called()  # Should create an anchor
            mock_drawing.add.assert_called()  # Should add the anchor to the drawing
            svg._draw_object_text.assert_called_once()  # Should add text
            svg._draw_edit_delete_button.assert_called_once()  # Should add buttons

    def test_draw_object_orientation(self, _):
        """Test the _draw_object_orientation method with different orientations."""
        # Create SVG renderer with mocked reverse
        svg = FloorPlanSVG(floor_plan=self.floor_plan, user=self.user, base_url=self.base_url)

        # Setup
        mock_drawing = MagicMock()
        mock_link = MagicMock()
        mock_tile = MagicMock()
        mock_tile.x_origin = 1
        mock_tile.y_origin = 1
        mock_tile.x_size = 1
        mock_tile.y_size = 1
        mock_tile.status.color = "ff0000"
        origin = (50, 50)  # Example origin coordinates

        # Test each orientation
        orientations = [
            ObjectOrientationChoices.UP,
            ObjectOrientationChoices.DOWN,
            ObjectOrientationChoices.LEFT,
            ObjectOrientationChoices.RIGHT,
        ]

        for orientation in orientations:
            mock_tile.object_orientation = orientation

            # Call method
            svg._draw_object_orientation(mock_drawing, mock_tile, mock_link, origin)

            # Assertions
            mock_link.add.assert_called()  # Should add orientation indicator

    def test_render(self, _):
        """Test the complete render method."""
        # Create SVG renderer with mocked reverse
        svg = FloorPlanSVG(floor_plan=self.floor_plan, user=self.user, base_url=self.base_url)

        # Setup
        mock_drawing = MagicMock()

        # Mock tiles
        mock_tile1 = MagicMock()
        mock_tile2 = MagicMock()
        self.floor_plan.tiles.all.return_value = [mock_tile1, mock_tile2]

        # Mock methods called by render
        svg._setup_drawing = MagicMock(return_value=mock_drawing)
        svg._draw_underlay_tiles = MagicMock()
        svg._draw_grid = MagicMock()
        svg._draw_tile = MagicMock()

        # Call method
        result = svg.render()

        # Assertions
        svg._setup_drawing.assert_called_once()
        self.assertEqual(svg._draw_underlay_tiles.call_count, 2)  # Called for each tile
        svg._draw_grid.assert_called_once_with(mock_drawing)
        self.assertEqual(svg._draw_tile.call_count, 2)  # Called for each tile
        self.assertEqual(result, mock_drawing)
