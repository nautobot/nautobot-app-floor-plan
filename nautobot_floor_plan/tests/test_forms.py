"""Test floorplan forms."""

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from nautobot.core.testing import TestCase
from nautobot.extras.models import Tag

from nautobot_floor_plan import choices, forms, models
from nautobot_floor_plan.tests import fixtures


class TestFloorPlanForm(TestCase):
    """Test FloorPlan forms."""

    def setUp(self):
        """Create LocationType, Status, and Location records."""
        data = fixtures.create_prerequisites()
        self.floors = data["floors"]

    def test_valid_minimal_inputs(self):
        """Test creation with minimal input data."""
        form_data = {
            # Main form required fields
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
            **fixtures.get_full_formset_data(axis="x"),
            **fixtures.get_full_formset_data(axis="y"),
        }

        form = forms.FloorPlanForm(data=form_data)

        # Validate form
        self.assertTrue(form.is_valid(), msg=f"Form errors: {form.errors}")

        # Save the form
        form.save()

        # Verify saved data
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

        # Verify no custom ranges were created
        self.assertEqual(floor_plan.custom_labels.count(), 0)

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
                "x_custom_ranges": "null",
                "y_axis_labels": choices.AxisLabelsChoices.NUMBERS,
                "y_origin_seed": 1,
                "y_axis_step": 1,
                "y_custom_ranges": "null",
                "tags": [tag],
                **fixtures.get_full_formset_data(axis="x"),
                **fixtures.get_full_formset_data(axis="y"),
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

    def test_form_fieldsets_structure(self):
        """Test that the form's fieldset structure is correct."""
        form = forms.FloorPlanForm()

        # Test basic fieldset structure
        self.assertEqual(len(form.fieldsets), 3)

        # Test Floor Plan Details tab
        self.assertIn("Floor Plan", dict(form.fieldsets))
        self.assertIn("location", form.fieldsets[0][1])
        self.assertIn("x_size", form.fieldsets[0][1])

        # Test X Axis Settings tabs
        x_axis_settings = form.fieldsets[1][1]
        self.assertIn("tabs", x_axis_settings)
        self.assertEqual(len(x_axis_settings["tabs"]), 1)

        # Test Y Axis Settings tabs
        y_axis_settings = form.fieldsets[2][1]
        self.assertIn("tabs", y_axis_settings)
        self.assertEqual(len(y_axis_settings["tabs"]), 1)

    def test_seed_step_reset_with_custom_labels(self):
        """Test resetting of seed and step when custom labels are configured."""

        initial_form = forms.FloorPlanForm(
            data={
                "location": self.floors[0].pk,
                "x_size": 10,
                "y_size": 10,
                "tile_depth": 100,
                "tile_width": 200,
                "x_axis_labels": choices.AxisLabelsChoices.NUMBERS,
                "x_origin_seed": 4,
                "x_axis_step": 2,
                "x_custom_ranges": {},
                "y_axis_labels": choices.AxisLabelsChoices.NUMBERS,
                "y_origin_seed": 3,
                "y_axis_step": -1,
                "y_custom_ranges": {},
                **fixtures.get_full_formset_data(axis="x"),
                **fixtures.get_full_formset_data(axis="y"),
            }
        )

        self.assertTrue(initial_form.is_valid())
        initial_form.save()

        floor_plan = models.FloorPlan.objects.get(location=self.floors[0])

        models.FloorPlanCustomAxisLabel.objects.create(
            floor_plan=floor_plan,
            axis="X",
            label_type=choices.CustomAxisLabelsChoices.BINARY,
            start_label="1",
            end_label="10",
            step=1,
            increment_letter=True,
            order=1,
        )

        self.assertEqual(floor_plan.y_origin_seed, 3)
        self.assertEqual(floor_plan.y_axis_step, -1)

        models.FloorPlanCustomAxisLabel.objects.create(
            floor_plan=floor_plan,
            axis="Y",
            label_type=choices.CustomAxisLabelsChoices.HEX,
            start_label="3",
            end_label="12",
            step=1,
            increment_letter=True,
            order=1,
        )

        self.assertEqual(floor_plan.x_origin_seed, 1)
        self.assertEqual(floor_plan.y_origin_seed, 1)
        self.assertEqual(floor_plan.x_axis_step, 1)
        self.assertEqual(floor_plan.y_axis_step, 1)

    def test_increment_letter_default_false_for_numbers(self):
        """Test setting increment_letter to False when label_type is numbers."""
        # Prepare the range data
        ranges = [
            {
                "start": "06",
                "end": "10",
                "step": "1",
                "label_type": choices.CustomAxisLabelsChoices.NUMBERS,
                "increment_letter": False,
            }
        ]

        # Create form data using fixtures
        form_data = fixtures.prepare_formset_data(
            ranges,
            base_data=fixtures.get_default_floor_plan_data(
                self.floors,
                x_origin_seed=4,
                x_axis_step=2,
                y_origin_seed=3,
                y_axis_step=-1,
            ),
        )

        # Create and validate the form
        form = forms.FloorPlanForm(data=form_data)
        self.assertTrue(form.is_valid(), msg=f"Form errors: {form.errors}")

        # Save the form and verify custom label
        floor_plan = form.save()
        custom_labels = models.FloorPlanCustomAxisLabel.objects.filter(floor_plan=floor_plan, axis="X")
        self.assertEqual(custom_labels.count(), 1)

        custom_label = custom_labels.first()
        self.assertEqual(custom_label.increment_letter, False, "increment_letter should be False for numeric labels")
        self.assertEqual(custom_label.start_label, "06")
        self.assertEqual(custom_label.end_label, "10")
        self.assertEqual(custom_label.step, 1)
        self.assertEqual(custom_label.label_type, choices.CustomAxisLabelsChoices.NUMBERS)

    def test_create_floor_plan_with_limits(self):
        """Test that a floor plan cannot be created if it exceeds configured limits."""
        # Set limits in the settings
        settings.PLUGINS_CONFIG["nautobot_floor_plan"]["x_size_limit"] = 100
        settings.PLUGINS_CONFIG["nautobot_floor_plan"]["y_size_limit"] = 100

        form = forms.FloorPlanForm(
            data={
                "location": self.floors[0].pk,
                "x_size": 150,
                "y_size": 50,
                "tile_depth": 100,
                "tile_width": 200,
                "x_axis_labels": "numbers",
                "x_origin_seed": 1,
                "x_axis_step": 1,
                "y_axis_labels": "numbers",
                "y_origin_seed": 1,
                "y_axis_step": 1,
                **fixtures.get_formset_management_data(),
                **fixtures.get_default_formset_data(axis="x"),
                **fixtures.get_default_formset_data(axis="y"),
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("x_size", form.errors)
        self.assertEqual(form.errors["x_size"], ["X size cannot exceed 100 as defined in nautobot_config.py."])

    def test_create_large_floor_plan_with_no_limit(self):
        """Test that a large floor plan can be created if limits are set to None."""

        settings.PLUGINS_CONFIG["nautobot_floor_plan"]["x_size_limit"] = None
        settings.PLUGINS_CONFIG["nautobot_floor_plan"]["y_size_limit"] = None

        form = forms.FloorPlanForm(
            data={
                "location": self.floors[0].pk,
                "x_size": 300,
                "y_size": 300,
                "tile_depth": 100,
                "tile_width": 200,
                "x_axis_labels": "numbers",
                "x_origin_seed": 1,
                "x_axis_step": 1,
                "y_axis_labels": "numbers",
                "y_origin_seed": 1,
                "y_axis_step": 1,
                **fixtures.get_formset_management_data(),
                **fixtures.get_default_formset_data(axis="x"),
                **fixtures.get_default_formset_data(axis="y"),
            }
        )
        self.assertTrue(form.is_valid())
        floor_plan = form.save()
        self.assertIsNotNone(floor_plan)
        self.assertEqual(floor_plan.x_size, 300)
        self.assertEqual(floor_plan.y_size, 300)

    def test_formset_management_form(self):
        """Test that formset management form data is properly handled."""
        # Test missing management form data
        form_data = fixtures.get_default_floor_plan_data(self.floors)

        form = forms.FloorPlanForm(data=form_data)
        # Validation should fail due to missing formset management data
        self.assertFalse(form.is_valid())

        # Add management form data for x_ranges
        form_data.update(fixtures.get_formset_management_data())

        # Form should now be valid
        form = forms.FloorPlanForm(data=form_data)
        self.assertTrue(form.is_valid())

        # Test invalid management form data
        form_data = {
            **fixtures.get_default_floor_plan_data(self.floors),
            **fixtures.get_formset_management_data(x_total="invalid"),
        }
        form = forms.FloorPlanForm(data=form_data)
        self.assertFalse(form.is_valid())


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

    def test_immovable_tiles(self):
        """Test handling of immovable tiles."""
        # Set floor plan to immovable
        self.floor_plan.is_tile_movable = False
        self.floor_plan.save()

        form = forms.FloorPlanTileForm(initial={"floor_plan": self.floor_plan.pk})

        self.assertTrue(form.fields["x_origin"].disabled)
        self.assertTrue(form.fields["y_origin"].disabled)
