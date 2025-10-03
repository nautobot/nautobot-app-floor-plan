"""Unit tests for views."""
# pylint: disable=duplicate-code

from django.test import override_settings
from django.urls import reverse
from nautobot.apps.testing import TestCase, ViewTestCases
from nautobot.users.models import User

from nautobot_floor_plan import choices, models
from nautobot_floor_plan.tests import fixtures


class FloorPlanViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    """Test the FloorPlan views."""

    model = models.FloorPlan
    bulk_edit_data = {"x_size": 10, "y_size": 10, "tile_width": 200, "tile_depth": 200}
    csv_data = (
        "location__name,x_size,x_origin_seed,x_axis_step,y_size,y_origin_seed,y_axis_step,tile_width,tile_depth",
        "Floor 4,1,1,1,2,1,1,100,100",
        "Floor 5,2,1,1,4,1,2,100,200",
        "Floor 6,3,1,1,6,1,-2,200,100",
    )
    allowed_number_of_tree_queries_per_view_type = {
        "retrieve": 1,
    }

    @classmethod
    def setUpTestData(cls):
        data = fixtures.create_prerequisites(floor_count=6)
        fixtures.create_floor_plans(data["floors"][:3])
        cls.form_data = {
            "location": data["floors"][3].pk,
            "tile_depth": 100,
            "tile_width": 100,
            "x_size": 1,
            "x_origin_seed": 1,
            "x_axis_step": 1,
            "y_size": 2,
            "y_origin_seed": 1,
            "y_axis_step": 1,
            "x_axis_labels": choices.AxisLabelsChoices.NUMBERS,
            "y_axis_labels": choices.AxisLabelsChoices.NUMBERS,
            **fixtures.get_full_formset_data(axis="x"),
            **fixtures.get_full_formset_data(axis="y"),
        }


class LocationFloorPlanTabTest(TestCase):
    """Test the Location Floor Plan tab views."""

    def setUp(self):
        super().setUp()
        data = fixtures.create_prerequisites()
        self.location = data["floors"][0]
        self.floor_plan = fixtures.create_floor_plans([self.location])[0]

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_floor_plan_tab(self):
        """Test that the floor plan tab renders correctly."""
        url = reverse("plugins:nautobot_floor_plan:location_floor_plan_tab", kwargs={"pk": self.location.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "nautobot_floor_plan/location_floor_plan.html")

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_child_floor_plan_tab(self):
        """Test that the child floor plan tab renders correctly."""
        url = reverse("plugins:nautobot_floor_plan:location_child_floor_plan_tab", kwargs={"pk": self.location.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "nautobot_floor_plan/location_child_floor_plan.html")


class FloorPlanTabActivationTest(TestCase):
    """Test the tab activation logic in FloorPlan views."""

    model = models.FloorPlan

    def setUp(self):
        """Create prerequisites and base form data."""
        super().setUp()

        self.user = User.objects.create_superuser(
            username="testuser", email="testuser@example.com", password="testpass"
        )
        self.client.force_login(self.user)

        data = fixtures.create_prerequisites()
        self.floors = data["floors"]
        self.form_data = {
            "location": self.floors[0].pk,
            "x_size": 1,
            "y_size": 2,
            "tile_depth": 100,
            "tile_width": 200,
            "x_axis_labels": choices.AxisLabelsChoices.NUMBERS,
            "y_axis_labels": choices.AxisLabelsChoices.NUMBERS,
            "x_origin_seed": "1",
            "y_origin_seed": "1",
            "x_axis_step": 1,
            "y_axis_step": 1,
            **fixtures.get_formset_management_data(),
            **fixtures.get_default_formset_data(axis="x"),
            **fixtures.get_default_formset_data(axis="y"),
        }

    def test_default_tabs_active(self):
        """Test that default tabs are active when no custom labels exist."""
        response = self.client.get(reverse("plugins:nautobot_floor_plan:floorplan_add"))
        self.assertContains(response, "Default Labels")
        self.assertTrue(response.context["x_activate_default_tab"])
        self.assertFalse(response.context["x_activate_custom_tab"])
        self.assertTrue(response.context["y_activate_default_tab"])
        self.assertFalse(response.context["y_activate_custom_tab"])

    def test_custom_labels_activate_custom_tab(self):
        """Test that custom tabs are active when custom labels exist."""
        # Create a floor plan with custom labels
        floor_plan = models.FloorPlan.objects.create(
            location=self.floors[0],
            x_size=1,
            y_size=2,
            tile_depth=100,
            tile_width=200,
            x_axis_labels=choices.AxisLabelsChoices.NUMBERS,
            y_axis_labels=choices.AxisLabelsChoices.NUMBERS,
            x_origin_seed=1,
            y_origin_seed=1,
            x_axis_step=1,
            y_axis_step=1,
        )
        floor_plan.save()

        custom_label = models.FloorPlanCustomAxisLabel.objects.create(
            floor_plan=floor_plan,
            axis="X",
            start_label="1",
            end_label="10",
            step=1,
            label_type=choices.CustomAxisLabelsChoices.NUMBERS,
            order=1,
        )
        custom_label.save()

        # Refresh the floor plan from the database to ensure relationships are loaded
        floor_plan.refresh_from_db()

        response = self.client.get(reverse("plugins:nautobot_floor_plan:floorplan_edit", kwargs={"pk": floor_plan.pk}))
        self.assertContains(response, "Custom Labels")
        self.assertFalse(response.context["x_activate_default_tab"])
        self.assertTrue(response.context["x_activate_custom_tab"])
        self.assertTrue(response.context["y_activate_default_tab"])
        self.assertFalse(response.context["y_activate_custom_tab"])

    def test_default_tab_errors(self):
        """Test that default tab remains active when it has errors."""
        data = {
            **self.form_data,
            "x_origin_seed": "",
        }
        response = self.client.post(
            reverse("plugins:nautobot_floor_plan:floorplan_add"),
            data=data,
            follow=True,  # Follow the redirect
        )
        self.assertContains(response, "Default Labels")
        self.assertTrue(response.context["x_activate_default_tab"])
        self.assertFalse(response.context["x_activate_custom_tab"])
        self.assertTrue(response.context["y_activate_default_tab"])
        self.assertFalse(response.context["y_activate_custom_tab"])

    def test_custom_tab_errors(self):
        """Test that default tab remains active when there are validation errors in new custom labels."""
        data = {
            **self.form_data,  # Base form data
            # X-axis custom range formset data
            "x_ranges-TOTAL_FORMS": "1",
            "x_ranges-INITIAL_FORMS": "0",
            "x_ranges-MIN_NUM_FORMS": "0",
            "x_ranges-MAX_NUM_FORMS": "1000",
            "x_ranges-0-start": "invalid",  # This will cause validation error
            "x_ranges-0-end": "10",
            "x_ranges-0-step": "1",
            "x_ranges-0-label_type": choices.CustomAxisLabelsChoices.NUMBERS,
            "y_ranges-TOTAL_FORMS": "0",
            "y_ranges-INITIAL_FORMS": "0",
            "y_ranges-MIN_NUM_FORMS": "0",
            "y_ranges-MAX_NUM_FORMS": "1000",
        }

        response = self.client.post(reverse("plugins:nautobot_floor_plan:floorplan_add"), data=data, follow=True)

        # Assert that we see the error message for custom labels
        self.assertContains(response, "There are validation errors in the Custom Labels tab")

        # Assert that default tab remains active (since there are no existing valid custom labels)
        self.assertTrue(response.context["x_activate_default_tab"])
        self.assertFalse(response.context["x_activate_custom_tab"])
        self.assertTrue(response.context["y_activate_default_tab"])
        self.assertFalse(response.context["y_activate_custom_tab"])

        # Verify we have the expected validation error
        self.assertTrue(response.context["form"].x_ranges.errors)

    def test_custom_tab_errors_with_existing_labels(self):
        """Test that custom tab becomes active when there are existing custom labels and validation errors."""
        # Create a floor plan with custom labels
        floor_plan = models.FloorPlan.objects.create(
            location=self.floors[0],
            x_size=1,
            y_size=2,
            tile_depth=100,
            tile_width=200,
            x_axis_labels=choices.AxisLabelsChoices.NUMBERS,
            y_axis_labels=choices.AxisLabelsChoices.NUMBERS,
            x_origin_seed=1,
            y_origin_seed=1,
            x_axis_step=1,
            y_axis_step=1,
        )
        floor_plan.save()

        custom_label = models.FloorPlanCustomAxisLabel.objects.create(
            floor_plan=floor_plan,
            axis="X",
            start_label="1",
            end_label="10",
            step=1,
            label_type=choices.CustomAxisLabelsChoices.NUMBERS,
            order=1,
        )
        custom_label.save()

        # Refresh the floor plan from the database to ensure relationships are loaded
        floor_plan.refresh_from_db()

        # Now try to update with invalid data
        data = {
            **self.form_data,
            "x_ranges-TOTAL_FORMS": "1",
            "x_ranges-INITIAL_FORMS": "1",
            "x_ranges-MIN_NUM_FORMS": "0",
            "x_ranges-MAX_NUM_FORMS": "1000",
            "x_ranges-0-start": "invalid",  # Invalid start value
            "x_ranges-0-end": "10",
            "x_ranges-0-step": "1",
            "x_ranges-0-label_type": choices.CustomAxisLabelsChoices.NUMBERS,
            "x_ranges-0-DELETE": "",
        }

        response = self.client.post(
            reverse("plugins:nautobot_floor_plan:floorplan_edit", kwargs={"pk": floor_plan.pk}), data=data, follow=True
        )

        # Assert that we see the error message
        self.assertContains(response, "There are validation errors in the Custom Labels tab")

        # Assert that custom tab is active (since we have existing custom labels)
        self.assertFalse(response.context["x_activate_default_tab"])
        self.assertTrue(response.context["x_activate_custom_tab"])
        self.assertTrue(response.context["y_activate_default_tab"])
        self.assertFalse(response.context["y_activate_custom_tab"])

        # Verify we have the expected validation error
        self.assertTrue(response.context["form"].x_ranges.errors)
