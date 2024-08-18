"""Test floorplan forms."""

from django.contrib.contenttypes.models import ContentType

from nautobot.extras.models import Tag
from nautobot.core.testing import TestCase

from nautobot_floor_plan import forms, models, choices
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
            data={
                "location": self.floors[0].pk,
                "x_size": 1,
                "y_size": 2,
                "tile_depth": 100,
                "tile_width": 200,
                "x_axis_labels": choices.AxisLabelsChoices.NUMBERS,
                "x_origin_seed": 1,
                "x_axis_step": 1,
                "y_axis_labels": choices.AxisLabelsChoices.NUMBERS,
                "y_origin_seed": 1,
                "y_axis_step": 1,
            }
        )
        self.assertTrue(form.is_valid())
        form.save()
        floor_plan = models.FloorPlan.objects.get(location=self.floors[0])
        self.assertEqual(floor_plan.x_size, 1)
        self.assertEqual(floor_plan.y_size, 2)
        self.assertEqual(floor_plan.tile_depth, 100)
        self.assertEqual(floor_plan.tile_width, 200)
        self.assertEqual(floor_plan.x_axis_labels, choices.AxisLabelsChoices.NUMBERS)
        self.assertEqual(floor_plan.y_axis_labels, choices.AxisLabelsChoices.NUMBERS)
        self.assertEqual(floor_plan.x_origin_seed, 1)
        self.assertEqual(floor_plan.y_origin_seed, 1)
        self.assertEqual(floor_plan.x_axis_step, 1)
        self.assertEqual(floor_plan.y_axis_step, 1)

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
                "x_axis_labels": choices.AxisLabelsChoices.NUMBERS,
                "x_origin_seed": 1,
                "x_axis_step": 1,
                "y_axis_labels": choices.AxisLabelsChoices.NUMBERS,
                "y_origin_seed": 1,
                "y_axis_step": 1,
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
        self.assertEqual(floor_plan.x_axis_labels, choices.AxisLabelsChoices.NUMBERS)
        self.assertEqual(floor_plan.y_axis_labels, choices.AxisLabelsChoices.NUMBERS)
        self.assertEqual(floor_plan.x_origin_seed, 1)
        self.assertEqual(floor_plan.y_origin_seed, 1)
        self.assertEqual(floor_plan.x_axis_step, 1)
        self.assertEqual(floor_plan.x_axis_step, 1)
        self.assertEqual(list(floor_plan.tags.all()), [tag])

    def test_invalid_required_fields(self):
        """Test form validation with missing required fields."""
        form = forms.FloorPlanForm(data={})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            [
                "location",
                "tile_depth",
                "tile_width",
                "x_axis_labels",
                "x_axis_step",
                "x_origin_seed",
                "x_size",
                "y_axis_labels",
                "y_axis_step",
                "y_origin_seed",
                "y_size",
            ],
            sorted(form.errors.keys()),
        )
        for message in form.errors.values():
            self.assertIn("This field is required.", message)


class TestFloorPlanTileForm(TestCase):
    """Test FloorPlanTileForm forms."""

    def setUp(self):
        """Create LocationType, Status, Location and FloorPlan records."""
        data = fixtures.create_prerequisites()
        self.status = data["status"]
        self.floor_plan = models.FloorPlan.objects.create(
            location=data["floors"][0],
            x_size=8,
            y_size=8,
            tile_depth=100,
            tile_width=100,
            x_axis_labels=choices.AxisLabelsChoices.LETTERS,
            y_axis_labels=choices.AxisLabelsChoices.NUMBERS,
        )

    def test_valid_minimal_inputs(self):
        """Test creation with minimal input data."""
        form = forms.FloorPlanTileForm(
            data={
                "floor_plan": self.floor_plan.pk,
                "x_origin": "A",
                "y_origin": 1,
                "x_size": 1,
                "y_size": 1,
                "status": self.status.pk,
            }
        )
        self.assertTrue(form.is_valid())
        form.save()
        tile = models.FloorPlanTile.objects.get(floor_plan=self.floor_plan)
        self.assertEqual(tile.floor_plan, self.floor_plan)
        self.assertEqual(tile.x_origin, 1)  # model uses integers.
        self.assertEqual(tile.x_size, 1)
        self.assertEqual(tile.y_size, 1)
        self.assertEqual(tile.status, self.status)

    def test_invalid_input_with_number(self):
        """Test creation with number when X axis uses letter labels."""
        form = forms.FloorPlanTileForm(
            data={
                "floor_plan": self.floor_plan.pk,
                "x_origin": 1,  # 1 instead of "A"
                "y_origin": 1,
                "x_size": 1,
                "y_size": 1,
                "status": self.status.pk,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("X origin should use capital letters.", form.errors.get("x_origin"))

    def test_invalid_input_with_letter(self):
        """Test creation with letter when Y axis uses number labels."""
        form = forms.FloorPlanTileForm(
            data={
                "floor_plan": self.floor_plan.pk,
                "x_origin": "A",
                "y_origin": "A",  # "A" instead of 1
                "x_size": 1,
                "y_size": 1,
                "status": self.status.pk,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Y origin should use numbers.", form.errors.get("y_origin"))

    def test_tile_outside_of_floor_plan(self):
        """Test a tile located outside the floor plan space."""
        form = forms.FloorPlanTileForm(
            data={
                "floor_plan": self.floor_plan.pk,
                "x_origin": "A",
                "y_origin": 9,  # out of range
                "x_size": 1,
                "y_size": 1,
                "status": self.status.pk,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn(['Too large for Floor Plan for Location "Floor 1"'], form.errors.values())
