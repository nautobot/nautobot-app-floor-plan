"""Test floorplan forms."""

from django.test import TestCase

from nautobot_floor_plan import forms


class FloorPlanTest(TestCase):
    """Test FloorPlan forms."""

    def test_specifying_all_fields_success(self):
        form = forms.FloorPlanForm(
            data={
                "name": "Development",
                "description": "Development Testing",
            }
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_specifying_only_required_success(self):
        form = forms.FloorPlanForm(
            data={
                "name": "Development",
            }
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_validate_name_floorplan_is_required(self):
        form = forms.FloorPlanForm(data={"description": "Development Testing"})
        self.assertFalse(form.is_valid())
        self.assertIn("This field is required.", form.errors["name"])
