"""Unit tests for floor plan multi-select functionality."""

import unittest

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from nautobot.dcim.models import Device, PowerFeed, PowerPanel, Rack

from nautobot_floor_plan.models import FloorPlanTile
from nautobot_floor_plan.tests.fixtures import create_floor_plans, create_prerequisites
from nautobot_floor_plan.tests.utils import is_nautobot_version_less_than

User = get_user_model()


@unittest.skipIf(is_nautobot_version_less_than("2.3.1"), "Nautobot version is less than 2.3.1")
class FloorPlanMultiSelectViewTestCase(TestCase):
    """Test that the multi-select JavaScript and CSS are loaded in floor plan views."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.user.is_superuser = True
        self.user.save()
        self.client.login(username="testuser", password="testpass")

        # Create test data
        prerequisites = create_prerequisites(floor_count=1)
        self.floors = prerequisites["floors"]
        self.floor_plans = create_floor_plans(self.floors)
        self.floor_plan = self.floor_plans[0]

    def test_multiselect_resources_loaded(self):
        """Test that multiselect.js and multiselect.css are loaded in floor plan view."""
        url = reverse("plugins:nautobot_floor_plan:floorplan", kwargs={"pk": self.floor_plan.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "floorplan-multiselect.js")
        self.assertContains(response, "multiselect.css")

    def test_permissions_context_loaded(self):
        """Test that FLOOR_PLAN_PERMISSIONS are passed to the template."""
        url = reverse("plugins:nautobot_floor_plan:floorplan", kwargs={"pk": self.floor_plan.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "FLOOR_PLAN_PERMISSIONS")
        self.assertContains(response, "canEditRacks")
        self.assertContains(response, "canEditDevices")
        self.assertContains(response, "canEditPowerPanels")
        self.assertContains(response, "canEditPowerFeeds")

    def test_permissions_for_superuser(self):
        """Test that superuser has all permissions."""
        url = reverse("plugins:nautobot_floor_plan:floorplan", kwargs={"pk": self.floor_plan.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Superuser should have all permissions set to true
        self.assertContains(response, "canEditRacks: true")
        self.assertContains(response, "canEditDevices: true")
        self.assertContains(response, "canEditPowerPanels: true")
        self.assertContains(response, "canEditPowerFeeds: true")


@unittest.skipIf(is_nautobot_version_less_than("2.3.1"), "Nautobot version is less than 2.3.1")
class FloorPlanMultiSelectDataTestCase(TestCase):  # pylint: disable=too-many-instance-attributes
    """Test that floor plan tiles have correct data attributes for multi-select."""

    def setUp(self):
        """Set up test data with various object types."""
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.user.is_superuser = True
        self.user.save()
        self.client.login(username="testuser", password="testpass")

        # Create test data
        # pylint: disable=duplicate-code
        prerequisites = create_prerequisites(floor_count=1)
        self.floors = prerequisites["floors"]
        self.status = prerequisites["status"]
        self.manufacturer = prerequisites["manufacturer"]
        self.device_role = prerequisites["device_role"]
        self.device_type = prerequisites["device_type"]
        # pylint: enable=duplicate-code

        self.floor_plans = create_floor_plans(self.floors)
        self.floor_plan = self.floor_plans[0]

        # Create a rack
        self.rack = Rack.objects.create(
            name="Test Rack",
            location=self.floors[0],
            status=self.status,
        )

        # Create a device
        self.device = Device.objects.create(
            name="Test Device",
            device_type=self.device_type,
            role=self.device_role,
            location=self.floors[0],
            status=self.status,
        )

        # Create a power panel
        self.power_panel = PowerPanel.objects.create(
            name="Test Power Panel",
            location=self.floors[0],
        )

        # Create a power feed
        self.power_feed = PowerFeed.objects.create(
            name="Test Power Feed",
            power_panel=self.power_panel,
            status=self.status,
        )

        # Create floor plan tiles for each object
        # pylint: disable=duplicate-code
        self.rack_tile = FloorPlanTile.objects.create(
            floor_plan=self.floor_plan,
            x_origin=1,
            y_origin=1,
            x_size=1,
            y_size=1,
            status=self.status,
            rack=self.rack,
        )
        # pylint: enable=duplicate-code

        self.device_tile = FloorPlanTile.objects.create(
            floor_plan=self.floor_plan,
            x_origin=2,
            y_origin=1,
            x_size=1,
            y_size=1,
            status=self.status,
            device=self.device,
        )

        self.power_panel_tile = FloorPlanTile.objects.create(
            floor_plan=self.floor_plan,
            x_origin=3,
            y_origin=1,
            x_size=1,
            y_size=1,
            status=self.status,
            power_panel=self.power_panel,
        )

        self.power_feed_tile = FloorPlanTile.objects.create(
            floor_plan=self.floor_plan,
            x_origin=4,
            y_origin=1,
            x_size=1,
            y_size=1,
            status=self.status,
            power_feed=self.power_feed,
        )

    def test_rack_tile_has_correct_id(self):
        """Test that rack tiles have IDs starting with 'rack-'."""
        url = reverse("plugins-api:nautobot_floor_plan-api:floorplan-svg", kwargs={"pk": self.floor_plan.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        svg_content = response.content.decode("utf-8")
        self.assertIn(f'id="rack-{self.rack.pk}"', svg_content)

    def test_device_tile_has_correct_id(self):
        """Test that device tiles have IDs starting with 'device-'."""
        url = reverse("plugins-api:nautobot_floor_plan-api:floorplan-svg", kwargs={"pk": self.floor_plan.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        svg_content = response.content.decode("utf-8")
        self.assertIn(f'id="device-{self.device.pk}"', svg_content)

    def test_power_panel_tile_has_correct_id(self):
        """Test that power panel tiles have IDs starting with 'powerpanel-'."""
        url = reverse("plugins-api:nautobot_floor_plan-api:floorplan-svg", kwargs={"pk": self.floor_plan.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        svg_content = response.content.decode("utf-8")
        self.assertIn(f'id="powerpanel-{self.power_panel.pk}"', svg_content)

    def test_power_feed_tile_has_correct_id(self):
        """Test that power feed tiles have IDs starting with 'powerfeed-'."""
        url = reverse("plugins-api:nautobot_floor_plan-api:floorplan-svg", kwargs={"pk": self.floor_plan.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        svg_content = response.content.decode("utf-8")
        self.assertIn(f'id="powerfeed-{self.power_feed.pk}"', svg_content)

    def test_all_object_types_present(self):
        """Test that all object types are present in the SVG."""
        url = reverse("plugins-api:nautobot_floor_plan-api:floorplan-svg", kwargs={"pk": self.floor_plan.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        svg_content = response.content.decode("utf-8")

        # Check that all object types are present
        self.assertIn('id="rack-', svg_content)
        self.assertIn('id="device-', svg_content)
        self.assertIn('id="powerpanel-', svg_content)
        self.assertIn('id="powerfeed-', svg_content)
