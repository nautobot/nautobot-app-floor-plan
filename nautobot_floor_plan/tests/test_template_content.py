"""Tests for template content extensions in the Nautobot Floor Plan app."""

from unittest import mock

from django.test import TestCase

from nautobot_floor_plan.template_content import LocationFloorPlanTab


class TestLocationFloorPlanTab(TestCase):
    """Test the LocationFloorPlanTab template extension."""

    def setUp(self):
        """Set up test case."""
        # Create a mock context to pass to the constructor
        self.mock_context = {
            "object": mock.MagicMock(),
            "request": mock.MagicMock(),
        }
        # Initialize with the mock context
        self.template_extension = LocationFloorPlanTab(context=self.mock_context)

    @mock.patch("nautobot_floor_plan.template_content.reverse")
    def test_buttons_with_floor_plan(self, mock_reverse):
        """Test buttons method when location has a floor plan."""
        # Set up mocks
        mock_location = mock.MagicMock()
        mock_floor_plan = mock.MagicMock()
        mock_floor_plan.pk = "test-pk"
        mock_location.floor_plan = mock_floor_plan
        self.template_extension.context["object"] = mock_location
        self.template_extension.context["request"].user.has_perm.return_value = True

        # Set up reverse return values
        mock_reverse.side_effect = lambda name, kwargs=None: f"/mock/{name}/{kwargs.get('pk', '')}"

        # Call the method
        result = self.template_extension.buttons()

        # Verify the result contains the delete button
        self.assertIn("Delete Floor Plan", result)
        self.assertIn("/mock/plugins:nautobot_floor_plan:floorplan_delete/test-pk", result)

    def test_buttons_no_permission(self):
        """Test buttons method when user does not have permission."""
        # Set up mocks
        mock_location = mock.MagicMock()
        mock_floor_plan = mock.MagicMock()
        mock_location.floor_plan = mock_floor_plan
        self.template_extension.context["object"] = mock_location
        self.template_extension.context["request"].user.has_perm.return_value = False

        # Call the method
        result = self.template_extension.buttons()

        # Verify the result is empty
        self.assertEqual(result, "")

    @mock.patch("nautobot_floor_plan.template_content.reverse")
    def test_detail_tabs_with_floor_plan(self, mock_reverse):
        """Test detail_tabs method when location has a floor plan."""
        # Set up mocks
        mock_location = mock.MagicMock()
        mock_location.floor_plan = mock.MagicMock()
        mock_location.children.filter.return_value.exists.return_value = False
        self.template_extension.context["object"] = mock_location

        # Set up reverse return values
        mock_reverse.side_effect = lambda name, kwargs=None: f"/mock/{name}/{kwargs.get('pk', '')}"

        # Call the method
        result = self.template_extension.detail_tabs()

        # Verify the result contains the floor plan tab
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "Floor Plan")

    @mock.patch("nautobot_floor_plan.template_content.reverse")
    def test_detail_tabs_with_child_floor_plans(self, mock_reverse):
        """Test detail_tabs method when location has child floor plans."""
        # Set up mocks
        mock_location = mock.MagicMock()
        mock_location.floor_plan = None
        mock_location.children.filter.return_value.exists.return_value = True
        self.template_extension.context["object"] = mock_location

        # Set up reverse return values
        mock_reverse.side_effect = lambda name, kwargs=None: f"/mock/{name}/{kwargs.get('pk', '')}"

        # Call the method
        result = self.template_extension.detail_tabs()

        # Verify the result contains the child floor plans tab
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "Child Floor Plan(s)")

    @mock.patch("nautobot_floor_plan.template_content.reverse")
    def test_detail_tabs_with_both(self, mock_reverse):
        """Test detail_tabs method when location has both a floor plan and child floor plans."""
        # Set up mocks
        mock_location = mock.MagicMock()
        mock_location.floor_plan = mock.MagicMock()
        mock_location.children.filter.return_value.exists.return_value = True
        self.template_extension.context["object"] = mock_location

        # Set up reverse return values
        mock_reverse.side_effect = lambda name, kwargs=None: f"/mock/{name}/{kwargs.get('pk', '')}"

        # Call the method
        result = self.template_extension.detail_tabs()

        # Verify the result contains both tabs
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["title"], "Floor Plan")
        self.assertEqual(result[1]["title"], "Child Floor Plan(s)")

    def test_detail_tabs_with_neither(self):
        """Test detail_tabs method when location has neither a floor plan nor child floor plans."""
        # Set up mocks
        mock_location = mock.MagicMock()
        mock_location.floor_plan = None
        mock_location.children.filter.return_value.exists.return_value = False
        self.template_extension.context["object"] = mock_location

        # Call the method
        result = self.template_extension.detail_tabs()

        # Verify the result is empty
        self.assertEqual(result, [])
