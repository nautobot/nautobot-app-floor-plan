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
                "x_custom_ranges": "null",
                "y_axis_labels": choices.AxisLabelsChoices.NUMBERS,
                "y_origin_seed": 1,
                "y_axis_step": 1,
                "y_custom_ranges": "null",
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
        self.assertEqual(len(x_axis_settings["tabs"]), 2)

        # Test Y Axis Settings tabs
        y_axis_settings = form.fieldsets[2][1]
        self.assertIn("tabs", y_axis_settings)
        self.assertEqual(len(y_axis_settings["tabs"]), 2)

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
                "x_custom_ranges": [
                    {"start": "01", "end": "05", "step": 1, "label_type": "numbers"},
                ],
                "y_axis_labels": choices.AxisLabelsChoices.NUMBERS,
                "y_origin_seed": 3,
                "y_axis_step": -1,
                "y_custom_ranges": [],
            }
        )

        self.assertTrue(initial_form.is_valid())
        initial_form.save()

        floor_plan = models.FloorPlan.objects.get(location=self.floors[0])

        # Retrieve the custom label created
        custom_label = models.FloorPlanCustomAxisLabel.objects.get(floor_plan=floor_plan, axis="X")

        # Assert that increment_letter is False for numeric labels
        self.assertEqual(custom_label.increment_letter, False)

    def test_custom_ranges_validation(self):
        """Test validation of custom range inputs."""
        test_cases = [
            # Valid cases
            {"x_custom_ranges": '[{"start": "1", "end": "10", "step": 1, "label_type": "hex"}]', "valid": True},
            {"x_custom_ranges": '[{"start": "3", "end": "12", "step": 1, "label_type": "binary"}]', "valid": True},
            {
                "x_custom_ranges": '[{"start": "07A", "end": "07J", "step": 1, "increment_letter": false, "label_type": "numalpha"}]',
                "valid": True,
            },
            # Invalid cases
            {
                "x_custom_ranges": '[{"start": "07A", "end": "08Z", "step": 1, "increment_letter": false, "label_type": "numalpha"}]',
                "valid": False,
                "error": "Range: &#x27;07&#x27; != &#x27;08&#x27;. Use separate ranges for different prefixes",
            },
            {
                "x_custom_ranges": '[{"start": "1", "end": "10", "step": 1, "label_type": "let"}]',
                "valid": False,
                "error": "Invalid label type",
            },
        ]

        for test_case in test_cases:
            form_data = {
                "location": self.floors[0].pk,
                "x_size": 10,
                "y_size": 10,
                "tile_depth": 100,
                "tile_width": 100,
                "x_axis_labels": choices.AxisLabelsChoices.NUMBERS,
                "y_axis_labels": choices.AxisLabelsChoices.NUMBERS,
                "x_origin_seed": 1,
                "y_origin_seed": 1,
                "x_axis_step": 1,
                "y_axis_step": 1,
                "x_custom_ranges": test_case["x_custom_ranges"],
            }

            form = forms.FloorPlanForm(data=form_data)
            is_valid = form.is_valid()

            self.assertEqual(is_valid, test_case["valid"])
            if not is_valid and "error" in test_case:
                errors = str(form.errors)
                self.assertIn(test_case["error"], errors)

    def test_step_aware_range_validation(self):
        """Test that range validation correctly considers step values."""
        test_cases = [
            {
                "range": [{"start": "1", "end": "20", "step": 2, "label_type": "binary", "increment_letter": True}],
                "size": 10,
                "should_pass": True,
            },
            {
                "range": [{"start": "1", "end": "20", "step": 1, "label_type": "binary", "increment_letter": True}],
                "size": 10,
                "should_pass": False,
                "error": "has effective size 20",
            },
            {
                "range": [
                    {"start": "07A", "end": "07Z", "step": 1, "label_type": "numalpha", "increment_letter": False}
                ],
                "size": 26,
                "should_pass": True,
            },
            {
                "range": [
                    {"start": "02AA", "end": "02ZZ", "step": 1, "label_type": "numalpha", "increment_letter": False}
                ],
                "size": 26,
                "should_pass": True,
            },
            {
                "range": [{"start": "AA", "end": "ZZ", "step": 1, "label_type": "letters", "increment_letter": False}],
                "size": 26,
                "should_pass": True,
            },
            {
                "range": [
                    {"start": "07A", "end": "08A", "step": 1, "label_type": "numalpha", "increment_letter": True}
                ],
                "size": 10,
                "should_pass": False,
                "error": "Range: &#x27;07&#x27; != &#x27;08&#x27;. Use separate ranges for different prefixes",
            },
        ]

        for test in test_cases:
            form_data = {
                "location": self.floors[0].pk,
                "x_size": test["size"],
                "y_size": test["size"],
                "tile_depth": 100,
                "tile_width": 100,
                "x_axis_labels": choices.AxisLabelsChoices.NUMBERS,
                "y_axis_labels": choices.AxisLabelsChoices.NUMBERS,
                "x_origin_seed": 1,
                "y_origin_seed": 1,
                "x_axis_step": 1,
                "y_axis_step": 1,
                "x_custom_ranges": test["range"],
            }
            form = forms.FloorPlanForm(data=form_data)
            is_valid = form.is_valid()

            if test["should_pass"]:
                self.assertTrue(is_valid, f"Form should be valid for range: {test['range']}")
            else:
                self.assertFalse(is_valid, f"Form should be invalid for range: {test['range']}")
                self.assertIn(test["error"], str(form.errors))

    def test_alphanumeric_range_validation(self):
        """Test validation of alphanumeric range inputs."""
        test_cases = [
            # Valid cases
            {
                "x_custom_ranges": '[{"start": "A1", "end": "A5", "step": 1, "increment_letter": true, "label_type": "alphanumeric"},{"start": "B1", "end": "B5", "step": 1, "increment_letter": true, "label_type": "alphanumeric"}]',
                "valid": True,
            },
            {
                "x_custom_ranges": '[{"start": "A1", "end": "J1", "step": 1, "increment_letter": false, "label_type": "alphanumeric"}]',
                "valid": True,
            },
            # Invalid cases - range too large
            {
                "x_custom_ranges": '[{"start": "A1", "end": "A20", "step": 1, "increment_letter": true, "label_type": "alphanumeric"}]',
                "valid": False,
                "error": "Range from A1 to A20 has effective size 20, exceeding maximum size of 10",
            },
            # Invalid cases - non-alphanumeric input
            {
                "x_custom_ranges": '[{"start": "123", "end": "456", "step": 1, "increment_letter": true, "label_type": "alphanumeric"}]',
                "valid": False,
                "error": "Invalid alphanumeric range: &#x27;123&#x27; to &#x27;456&#x27; must include alphabetic characters. Use label_type &#x27;numbers&#x27; if no letters are needed.",
            },
        ]

        for test_case in test_cases:
            form_data = {
                "location": self.floors[0].pk,
                "x_size": 10,
                "y_size": 10,
                "tile_depth": 100,
                "tile_width": 100,
                "x_axis_labels": choices.AxisLabelsChoices.NUMBERS,
                "y_axis_labels": choices.AxisLabelsChoices.NUMBERS,
                "x_origin_seed": 1,
                "y_origin_seed": 1,
                "x_axis_step": 1,
                "y_axis_step": 1,
                "x_custom_ranges": test_case["x_custom_ranges"],
            }

            form = forms.FloorPlanForm(data=form_data)
            is_valid = form.is_valid()

            if test_case["valid"]:
                self.assertTrue(is_valid, f"Form should be valid for {test_case['x_custom_ranges']}")
            else:
                self.assertFalse(is_valid, f"Form should be invalid for {test_case['x_custom_ranges']}")
                if "error" in test_case:
                    self.assertIn(test_case["error"], str(form.errors))

    def test_custom_number_range_validation(self):
        """Test validation of custom number range inputs."""
        test_cases = [
            # Valid cases
            {
                "x_custom_ranges": '[{"start": "1", "end": "5", "step": 1, "increment_letter": false, "label_type": "numbers"},{"start": "10", "end": "15", "step": 1, "increment_letter": false, "label_type": "numbers"}]',
                "valid": True,
            },
            {
                "x_custom_ranges": '[{"start": "01", "end": "05", "step": 1, "increment_letter": false, "label_type": "numbers"}]',
                "valid": True,
            },
            # Invalid cases - range too large
            {
                "x_custom_ranges": '[{"start": "1", "end": "20", "step": 1, "increment_letter": false, "label_type": "numbers"}]',
                "valid": False,
                "error": "Range from 1 to 20 has effective size 20, exceeding maximum size of 10",
            },
            # Invalid cases - non-numeric input
            {
                "x_custom_ranges": '[{"start": "ABC", "end": "DEF", "step": 1, "increment_letter": false, "label_type": "numbers"}]',
                "valid": False,
                "error": "Invalid number format",
            },
            # Invalid cases - overlapping ranges
            {
                "x_custom_ranges": '[{"start": "1", "end": "5", "step": 1, "increment_letter": false, "label_type": "numbers"},{"start": "3", "end": "7", "step": 1, "increment_letter": false, "label_type": "numbers"}]',
                "valid": False,
                "error": "Ranges overlap",
            },
            # Invalid cases - invalid increment_letter
            {
                "x_custom_ranges": '[{"start": "01", "end": "05", "step": 1, "increment_letter": true, "label_type": "numbers"}]',
                "valid": False,
                "error": "increment_letter must be False when using numeric labels",
            },
        ]

        for test_case in test_cases:
            form_data = {
                "location": self.floors[0].pk,
                "x_size": 10,
                "y_size": 10,
                "tile_depth": 100,
                "tile_width": 100,
                "x_axis_labels": choices.AxisLabelsChoices.NUMBERS,
                "y_axis_labels": choices.AxisLabelsChoices.NUMBERS,
                "x_origin_seed": 1,
                "y_origin_seed": 1,
                "x_axis_step": 1,
                "y_axis_step": 1,
                "x_custom_ranges": test_case["x_custom_ranges"],
            }

            form = forms.FloorPlanForm(data=form_data)
            is_valid = form.is_valid()

            if test_case["valid"]:
                self.assertTrue(is_valid, f"Form should be valid for {test_case['x_custom_ranges']}")
            else:
                self.assertFalse(is_valid, f"Form should be invalid for {test_case['x_custom_ranges']}")
                if "error" in test_case:
                    self.assertIn(test_case["error"], str(form.errors))

    def test_roman_range_validation(self):
        """Test validation of Roman numeral range inputs."""
        test_cases = [
            # Valid cases
            {
                "x_custom_ranges": '[{"start": "I", "end": "V", "step": 1, "increment_letter": true, "label_type": "roman"},{"start": "XI", "end": "XV", "step": 1, "increment_letter": true, "label_type": "roman"}]',
                "valid": True,
            },
            # Invalid cases
            {
                "x_custom_ranges": '[{"start": "I", "end": "XX", "step": 1, "increment_letter": true, "label_type": "roman"}]',
                "valid": False,
                "error": "Range from I to XX has effective size 20, exceeding maximum size of 10",
            },
            {
                "x_custom_ranges": '[{"start": "ABC", "end": "DEF", "step": 1, "increment_letter": true, "label_type": "roman"}]',
                "valid": False,
                "errors": [
                    "Invalid values for roman - Invalid Roman numeral: ABC",
                    "Invalid values for roman - Invalid Roman numeral character at position 0 in: ABC",
                ],
            },
        ]

        for test_case in test_cases:
            form_data = {
                "location": self.floors[0].pk,
                "x_size": 10,
                "y_size": 10,
                "tile_depth": 100,
                "tile_width": 100,
                "x_axis_labels": choices.AxisLabelsChoices.NUMBERS,
                "y_axis_labels": choices.AxisLabelsChoices.NUMBERS,
                "x_origin_seed": 1,
                "y_origin_seed": 1,
                "x_axis_step": 1,
                "y_axis_step": 1,
                "x_custom_ranges": test_case["x_custom_ranges"],
            }

            form = forms.FloorPlanForm(data=form_data)
            is_valid = form.is_valid()

            if test_case["valid"]:
                self.assertTrue(is_valid, f"Form should be valid for {test_case['x_custom_ranges']}")
            else:
                self.assertFalse(is_valid, f"Form should be invalid for {test_case['x_custom_ranges']}")
                if "error" in test_case:
                    self.assertIn(test_case["error"], str(form.errors))
                elif "errors" in test_case:
                    error_str = str(form.errors)
                    self.assertTrue(
                        any(error in error_str for error in test_case["errors"]),
                        f"Expected one of {test_case['errors']} in error message, but got: {error_str}",
                    )

    def test_letters_range_validation(self):
        """Test validation of letter range inputs."""
        test_cases = [
            # Valid cases
            {
                "x_custom_ranges": '[{"start": "A", "end": "Z", "step": 1, "increment_letter": false, "label_type": "letters"},{"start": "AA", "end": "AZ", "step": 1, "increment_letter": false, "label_type": "letters"}]',
                "valid": True,
            },
            {
                "x_custom_ranges": '[{"start": "A", "end": "Z", "step": 1, "increment_letter": false, "label_type": "letters"},{"start": "AA", "end": "ZZ", "step": 1, "increment_letter": false, "label_type": "letters"}]',
                "valid": True,
            },
            # Invalid cases - range too large
            {
                "x_custom_ranges": '[{"start": "A", "end": "AAA", "step": 1, "increment_letter": true, "label_type": "letters"}]',
                "valid": False,
                "error": "Range from A to AAA has effective size 703, exceeding maximum size of 52",
            },
            # Invalid cases - non-letter input
            {
                "x_custom_ranges": '[{"start": "123", "end": "456", "step": 1, "increment_letter": false, "label_type": "letters"}]',
                "valid": False,
                "error": "Invalid values for letters: &#x27;123, 456&#x27",
            },
        ]

        for test_case in test_cases:
            form_data = {
                "location": self.floors[0].pk,
                "x_size": 52,
                "y_size": 52,
                "tile_depth": 100,
                "tile_width": 100,
                "x_axis_labels": choices.AxisLabelsChoices.NUMBERS,
                "y_axis_labels": choices.AxisLabelsChoices.NUMBERS,
                "x_origin_seed": 1,
                "y_origin_seed": 1,
                "x_axis_step": 1,
                "y_axis_step": 1,
                "x_custom_ranges": test_case["x_custom_ranges"],
            }

            form = forms.FloorPlanForm(data=form_data)
            is_valid = form.is_valid()

            if test_case["valid"]:
                self.assertTrue(is_valid, f"Form should be valid for {test_case['x_custom_ranges']}")
            else:
                self.assertFalse(is_valid, f"Form should be invalid for {test_case['x_custom_ranges']}")
                if "error" in test_case:
                    self.assertIn(test_case["error"], str(form.errors))

    def test_binary_range_validation(self):
        """Test validation of binary range inputs."""
        test_cases = [
            # Valid cases
            {
                "x_custom_ranges": '[{"start": "1", "end": "5", "step": 1, "increment_letter": true, "label_type": "binary"},{"start": "6", "end": "10", "step": 1, "increment_letter": true, "label_type": "binary"}]',
                "valid": True,
            },
            # Invalid cases
            {
                "x_custom_ranges": '[{"start": "1", "end": "20", "step": 1, "increment_letter": true, "label_type": "binary"}]',
                "valid": False,
                "error": "Range from 1 to 20 has effective size 20, exceeding maximum size of 10",
            },
            {
                "x_custom_ranges": '[{"start": "abc", "end": "def", "step": 1, "increment_letter": true, "label_type": "binary"}]',
                "valid": False,
                "error": "Invalid numeric values - invalid literal for int() with base 10: &#x27;abc&#x27;",
            },
        ]

        for test_case in test_cases:
            form_data = {
                "location": self.floors[0].pk,
                "x_size": 10,
                "y_size": 10,
                "tile_depth": 100,
                "tile_width": 100,
                "x_axis_labels": choices.AxisLabelsChoices.NUMBERS,
                "y_axis_labels": choices.AxisLabelsChoices.NUMBERS,
                "x_origin_seed": 1,
                "y_origin_seed": 1,
                "x_axis_step": 1,
                "y_axis_step": 1,
                "x_custom_ranges": test_case["x_custom_ranges"],
            }

            form = forms.FloorPlanForm(data=form_data)
            is_valid = form.is_valid()

            if test_case["valid"]:
                self.assertTrue(is_valid, f"Form should be valid for {test_case['x_custom_ranges']}")
            else:
                self.assertFalse(is_valid, f"Form should be invalid for {test_case['x_custom_ranges']}")
                if "error" in test_case:
                    self.assertIn(test_case["error"], str(form.errors))

    def test_hex_range_validation(self):
        """Test validation of hexadecimal range inputs."""
        test_cases = [
            # Valid cases
            {
                "x_custom_ranges": '[{"start": "1", "end": "15", "step": 1, "increment_letter": true, "label_type": "hex"},{"start": "16", "end": "30", "step": 1, "increment_letter": true, "label_type": "hex"}]',
                "valid": True,
            },
            # Invalid cases
            {
                "x_custom_ranges": '[{"start": "0G", "end": "1F", "step": 1, "increment_letter": true, "label_type": "hex"}]',
                "valid": False,
                "error": "Invalid numeric values - invalid literal for int() with base 10: &#x27;0G&#x27;",
            },
            {
                "x_custom_ranges": '[{"start": "XX", "end": "YY", "step": 1, "increment_letter": true, "label_type": "hex"}]',
                "valid": False,
                "error": "Invalid numeric values - invalid literal for int() with base 10: &#x27;XX&#x27;",
            },
        ]

        for test_case in test_cases:
            form_data = {
                "location": self.floors[0].pk,
                "x_size": 32,
                "y_size": 32,
                "tile_depth": 100,
                "tile_width": 100,
                "x_axis_labels": choices.AxisLabelsChoices.NUMBERS,
                "y_axis_labels": choices.AxisLabelsChoices.NUMBERS,
                "x_origin_seed": 1,
                "y_origin_seed": 1,
                "x_axis_step": 1,
                "y_axis_step": 1,
                "x_custom_ranges": test_case["x_custom_ranges"],
            }

            form = forms.FloorPlanForm(data=form_data)
            is_valid = form.is_valid()

            if test_case["valid"]:
                self.assertTrue(is_valid, f"Form should be valid for {test_case['x_custom_ranges']}")
            else:
                self.assertFalse(is_valid, f"Form should be invalid for {test_case['x_custom_ranges']}")
                if "error" in test_case:
                    self.assertIn(test_case["error"], str(form.errors))

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
            }
        )
        self.assertTrue(form.is_valid())
        floor_plan = form.save()
        self.assertIsNotNone(floor_plan)
        self.assertEqual(floor_plan.x_size, 300)
        self.assertEqual(floor_plan.y_size, 300)


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
