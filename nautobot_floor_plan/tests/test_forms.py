"""Test floorplan forms."""

from django.contrib.contenttypes.models import ContentType

from nautobot.extras.models import Tag
from nautobot.utilities.testing import TestCase

from nautobot_floor_plan import forms, models
from nautobot_floor_plan.tests import fixtures


class TestFloorPlanForm(TestCase):
    """Test FloorPlan forms."""

    def setUp(self):
        """Create LocationType, Status, and Location records."""
        data = fixtures.create_prerequisites()
        self.floors = data["floors"]

    def test_valid_minimal_inputs(self):
        """Test creation with minimal input data."""
        form = forms.FloorPlanForm(
            data={"location": self.floors[0].pk, "x_size": 1, "y_size": 2, "tile_depth": 100, "tile_width": 200}
        )
        self.assertTrue(form.is_valid())
        form.save()
        floor_plan = models.FloorPlan.objects.get(location=self.floors[0])
        self.assertEqual(floor_plan.x_size, 1)
        self.assertEqual(floor_plan.y_size, 2)
        self.assertEqual(floor_plan.tile_depth, 100)
        self.assertEqual(floor_plan.tile_width, 200)

    def test_valid_extra_inputs(self):
        """Test creation with additional optional input data."""
        tag = Tag.objects.create(name="DC Floorplan")
        tag.content_types.add(ContentType.objects.get_for_model(models.FloorPlan))
        form = forms.FloorPlanForm(
            data={
                "location": self.floors[0].pk,
                "x_size": 1,
                "y_size": 2,
                "tile_depth": 1,
                "tile_width": 2,
                "tags": [tag],
            }
        )
        self.assertTrue(form.is_valid())
        form.save()
        floor_plan = models.FloorPlan.objects.get(location=self.floors[0])
        self.assertEqual(floor_plan.x_size, 1)
        self.assertEqual(floor_plan.y_size, 2)
        self.assertEqual(floor_plan.tile_width, 2)
        self.assertEqual(floor_plan.tile_depth, 1)
        self.assertEqual(list(floor_plan.tags.all()), [tag])

    def test_invalid_required_fields(self):
        """Test form validation with missing required fields."""
        form = forms.FloorPlanForm(data={})
        self.assertFalse(form.is_valid())
        self.assertEqual(["location", "tile_depth", "tile_width", "x_size", "y_size"], sorted(form.errors.keys()))
        for message in form.errors.values():
            self.assertIn("This field is required.", message)
