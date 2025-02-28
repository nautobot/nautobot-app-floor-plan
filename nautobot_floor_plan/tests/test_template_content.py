"""Tests for template content extensions in the Nautobot Floor Plan app."""

import unittest
from unittest.mock import MagicMock, PropertyMock, patch

from django.core.exceptions import ObjectDoesNotExist

from nautobot_floor_plan.template_content import LocationFloorPlanTab


class LocationFloorPlanTabTestCase(unittest.TestCase):
    """Test cases for LocationFloorPlanTab template extension."""

    def setUp(self):
        """Set up test environment."""
        # Create mock location
        self.location = MagicMock()
        self.location.pk = 1

        # Create mock request with user
        self.request = MagicMock()
        self.user = MagicMock()
        self.request.user = self.user

        # Create context
        self.context = {"object": self.location, "request": self.request}

        # Create extension instance
        self.extension = LocationFloorPlanTab(self.context)

    @patch("nautobot_floor_plan.template_content.reverse")
    def test_buttons_with_floor_plan_and_delete_permission(self, mock_reverse):
        """Test buttons method when user has floor plan and delete permission."""
        # Setup
        self.location.floor_plan = MagicMock()
        self.location.floor_plan.pk = 2
        self.user.has_perm.return_value = True

        # Mock reverse URLs
        mock_reverse.side_effect = lambda *args, **kwargs: f"/mock/{args[0]}/{kwargs.get('kwargs', {}).get('pk', '')}"

        # Call the method
        result = self.extension.buttons()

        # Assertions
        self.user.has_perm.assert_called_once_with("nautobot_floor_plan.delete_floorplan")
        self.assertIn("Delete Floor Plan", result)
        self.assertIn("btn btn-danger", result)
        self.assertIn("mdi-checkerboard-remove", result)

    @patch("nautobot_floor_plan.template_content.reverse")
    def test_buttons_with_floor_plan_without_delete_permission(self, mock_reverse):
        """Test buttons method when user has floor plan but no delete permission."""
        # Setup
        self.location.floor_plan = MagicMock()
        self.user.has_perm.return_value = False

        # Mock reverse URLs (even though not used in this test path, it is set up for consistency)
        mock_reverse.side_effect = lambda *args, **kwargs: f"/mock/{args[0]}/{kwargs.get('kwargs', {}).get('pk', '')}"

        # Call the method
        result = self.extension.buttons()

        # Assertions
        self.user.has_perm.assert_called_once_with("nautobot_floor_plan.delete_floorplan")
        self.assertEqual(result, "")

    @patch("nautobot_floor_plan.template_content.reverse")
    def test_buttons_without_floor_plan_with_add_permission(self, mock_reverse):
        """Test buttons method when user has no floor plan but has add permission."""
        # Setup - make accessing floor_plan raise ObjectDoesNotExist
        type(self.location).floor_plan = PropertyMock(side_effect=ObjectDoesNotExist())
        self.user.has_perm.return_value = True

        # Mock reverse URLs
        mock_reverse.side_effect = lambda *args, **kwargs: f"/mock/{args[0]}/{kwargs.get('kwargs', {}).get('pk', '')}"

        # Call the method
        result = self.extension.buttons()

        # Assertions
        self.user.has_perm.assert_called_once_with("nautobot_floor_plan.add_floorplan")
        self.assertIn("Add Floor Plan", result)
        self.assertIn("btn btn-success", result)
        self.assertIn("mdi-checkerboard-plus", result)

    @patch("nautobot_floor_plan.template_content.reverse")
    def test_buttons_without_floor_plan_no_permission(self, mock_reverse):
        """Test buttons method when location has no floor plan and user lacks add permission."""
        # Setup - make accessing floor_plan raise ObjectDoesNotExist
        type(self.location).floor_plan = PropertyMock(side_effect=ObjectDoesNotExist())
        self.user.has_perm.return_value = False

        # Mock reverse URLs (even though not used in this test path, it is set up for consistency)
        mock_reverse.side_effect = lambda *args, **kwargs: f"/mock/{args[0]}/{kwargs.get('kwargs', {}).get('pk', '')}"

        # Call the method
        result = self.extension.buttons()

        # Assertions
        self.user.has_perm.assert_called_once_with("nautobot_floor_plan.add_floorplan")
        self.assertEqual(result, "")

    @patch("nautobot_floor_plan.template_content.reverse")
    def test_detail_tabs_with_floor_plan_no_children(self, mock_reverse):
        """Test detail_tabs method when location has floor plan but no children with floor plans."""
        # Setup
        self.location.floor_plan = MagicMock()

        # Mock children queryset
        children_mock = MagicMock()
        children_mock.filter().exists.return_value = False
        self.location.children = children_mock

        # Mock reverse URL
        mock_reverse.side_effect = lambda viewname, kwargs: f"/{viewname}/{kwargs['pk']}/"

        # Call the method
        tabs = self.extension.detail_tabs()

        # Assertions
        self.assertEqual(len(tabs), 1)
        self.assertEqual(tabs[0]["title"], "Floor Plan")
        self.assertTrue(tabs[0]["url"].startswith("/plugins:nautobot_floor_plan:location_floor_plan_tab/"))

    @patch("nautobot_floor_plan.template_content.reverse")
    def test_detail_tabs_no_floor_plan_with_children(self, mock_reverse):
        """Test detail_tabs method when location has no floor plan but has children with floor plans."""
        # Setup - location has no floor plan
        self.location.floor_plan = None

        # Mock children queryset
        children_mock = MagicMock()
        children_mock.filter().exists.return_value = True
        self.location.children = children_mock

        # Mock reverse URL
        mock_reverse.side_effect = lambda viewname, kwargs: f"/{viewname}/{kwargs['pk']}/"

        # Call the method
        tabs = self.extension.detail_tabs()

        # Assertions
        self.assertEqual(len(tabs), 1)
        self.assertEqual(tabs[0]["title"], "Child Floor Plan(s)")
        self.assertTrue(tabs[0]["url"].startswith("/plugins:nautobot_floor_plan:location_child_floor_plan_tab/"))

    @patch("nautobot_floor_plan.template_content.reverse")
    def test_detail_tabs_with_floor_plan_and_children(self, mock_reverse):
        """Test detail_tabs method when location has both floor plan and children with floor plans."""
        # Setup
        self.location.floor_plan = MagicMock()

        # Mock children queryset
        children_mock = MagicMock()
        children_mock.filter().exists.return_value = True
        self.location.children = children_mock

        # Mock reverse URL
        mock_reverse.side_effect = lambda viewname, kwargs: f"/{viewname}/{kwargs['pk']}/"

        # Call the method
        tabs = self.extension.detail_tabs()

        # Assertions
        self.assertEqual(len(tabs), 2)
        self.assertEqual(tabs[0]["title"], "Floor Plan")
        self.assertEqual(tabs[1]["title"], "Child Floor Plan(s)")

    @patch("nautobot_floor_plan.template_content.reverse")
    def test_detail_tabs_no_floor_plan_no_children(self, mock_reverse):
        """Test detail_tabs method when location has neither floor plan nor children with floor plans."""
        # Setup
        self.location.floor_plan = None

        # Mock children queryset
        children_mock = MagicMock()
        children_mock.filter().exists.return_value = False
        self.location.children = children_mock

        # Mock reverse URL (even though not used in this test path, it is set up for consistency)
        mock_reverse.side_effect = lambda viewname, kwargs: f"/{viewname}/{kwargs['pk']}/"

        # Call the method
        tabs = self.extension.detail_tabs()

        # Assertions
        self.assertEqual(tabs, [])
