"""Test floorplan form range validations."""

from django.test import TestCase

from nautobot_floor_plan import choices, forms
from nautobot_floor_plan.tests import fixtures


class TestRangeValidations(TestCase):
    """Test range validation functionality."""

    def setUp(self):
        """Create prerequisites for testing."""
        data = fixtures.create_prerequisites()
        self.floors = data["floors"]

    def _test_ranges(self, test_cases, base_data=None):
        """Helper method to test range validation cases."""
        for test_case in test_cases:
            form_data = fixtures.prepare_formset_data(test_case["ranges"], base_data=base_data, floors=self.floors)
            form = forms.FloorPlanForm(data=form_data)
            is_valid = form.is_valid()

            if test_case["valid"]:
                self.assertTrue(is_valid, f"Form should be valid for ranges: {test_case['ranges']}")
            else:
                self.assertFalse(is_valid, f"Form should be invalid for ranges: {test_case['ranges']}")
                if "error" in test_case:
                    form_errors = str(form.errors)
                    formset_errors = str([f.errors for f in form.x_ranges.forms])
                    self.assertTrue(
                        test_case["error"] in form_errors or test_case["error"] in formset_errors,
                        f"Expected error '{test_case['error']}' not found in form errors: {form_errors} or formset errors: {formset_errors}",
                    )

    def test_custom_ranges_validation(self):
        """Test validation of custom range inputs."""
        test_cases = [
            # Valid cases
            {
                "ranges": [
                    {
                        "start": "1",
                        "end": "10",
                        "step": "1",
                        "label_type": choices.CustomAxisLabelsChoices.HEX,
                        "increment_letter": True,
                    }
                ],
                "valid": True,
            },
            {
                "ranges": [
                    {
                        "start": "3",
                        "end": "12",
                        "step": "1",
                        "label_type": choices.CustomAxisLabelsChoices.BINARY,
                        "increment_letter": True,
                    }
                ],
                "valid": True,
            },
            {
                "ranges": [
                    {
                        "start": "07A",
                        "end": "07J",
                        "step": "1",
                        "label_type": choices.CustomAxisLabelsChoices.NUMALPHA,
                        "increment_letter": False,
                    }
                ],
                "valid": True,
            },
            # Invalid cases
            {
                "ranges": [
                    {
                        "start": "07A",
                        "end": "08Z",
                        "step": "1",
                        "label_type": choices.CustomAxisLabelsChoices.NUMALPHA,
                        "increment_letter": False,
                    }
                ],
                "valid": False,
                "error": "Range: '07' != '08'. Use separate ranges for different prefixes",
            },
            {
                "ranges": [
                    {
                        "start": "1",
                        "end": "10",
                        "step": "1",
                        "label_type": "let",  # Invalid label type
                        "increment_letter": True,
                    }
                ],
                "valid": False,
                "error": "Select a valid choice. let is not one of the available choices.",
            },
        ]

        for test_case in test_cases:
            form_data = fixtures.prepare_formset_data(test_case["ranges"], base_data=None, floors=self.floors)
            form = forms.FloorPlanForm(data=form_data)
            is_valid = form.is_valid()

            self.assertEqual(is_valid, test_case["valid"])
            if not is_valid and "error" in test_case:
                form_errors = str(form.errors)
                formset_errors = str([f.errors for f in form.x_ranges.forms])
                self.assertTrue(
                    test_case["error"] in form_errors or test_case["error"] in formset_errors,
                    f"Expected error '{test_case['error']}' not found in form errors: {form_errors} or formset errors: {formset_errors}",
                )

    def test_step_aware_range_validation(self):
        """Test that range validation correctly considers step values."""
        test_cases = [
            {
                "ranges": [
                    {
                        "start": "1",
                        "end": "20",
                        "step": "2",
                        "label_type": choices.CustomAxisLabelsChoices.BINARY,
                        "increment_letter": True,
                    }
                ],
                "size": 10,
                "should_pass": True,
            },
            {
                "ranges": [
                    {
                        "start": "1",
                        "end": "20",
                        "step": "1",
                        "label_type": choices.CustomAxisLabelsChoices.BINARY,
                        "increment_letter": True,
                    }
                ],
                "size": 10,
                "should_pass": False,
                "error": "has effective size 20",
            },
            {
                "ranges": [
                    {
                        "start": "07A",
                        "end": "07Z",
                        "step": "1",
                        "label_type": choices.CustomAxisLabelsChoices.NUMALPHA,
                        "increment_letter": False,
                    }
                ],
                "size": 26,
                "should_pass": True,
            },
            {
                "ranges": [
                    {
                        "start": "02AA",
                        "end": "02ZZ",
                        "step": "1",
                        "label_type": choices.CustomAxisLabelsChoices.NUMALPHA,
                        "increment_letter": False,
                    }
                ],
                "size": 26,
                "should_pass": True,
            },
            {
                "ranges": [
                    {
                        "start": "AA",
                        "end": "ZZ",
                        "step": "1",
                        "label_type": choices.CustomAxisLabelsChoices.LETTERS,
                        "increment_letter": False,
                    }
                ],
                "size": 26,
                "should_pass": True,
            },
            {
                "ranges": [
                    {
                        "start": "07A",
                        "end": "08A",
                        "step": "1",
                        "label_type": choices.CustomAxisLabelsChoices.NUMALPHA,
                        "increment_letter": True,
                    }
                ],
                "size": 10,
                "should_pass": False,
                "error": "Range: '07' != '08'. Use separate ranges for different prefixes",
            },
        ]

        for test in test_cases:
            base_data = fixtures.get_default_floor_plan_data(self.floors, x_size=test["size"], y_size=test["size"])
            form_data = fixtures.prepare_formset_data(test["ranges"], base_data=base_data, floors=self.floors)
            form = forms.FloorPlanForm(data=form_data)
            is_valid = form.is_valid()

            if test["should_pass"]:
                self.assertTrue(is_valid, f"Form should be valid for range: {test['ranges']}")
            else:
                self.assertFalse(is_valid, f"Form should be invalid for range: {test['ranges']}")
                form_errors = str(form.errors)
                formset_errors = str([f.errors for f in form.x_ranges.forms])
                self.assertTrue(
                    test["error"] in form_errors or test["error"] in formset_errors,
                    f"Expected error '{test['error']}' not found in form errors: {form_errors} or formset errors: {formset_errors}",
                )

    def test_alphanumeric_range_validation(self):
        """Test validation of alphanumeric range inputs."""
        test_cases = [
            # Valid cases
            {
                "ranges": [
                    {
                        "start": "A1",
                        "end": "A5",
                        "step": "1",
                        "label_type": choices.CustomAxisLabelsChoices.ALPHANUMERIC,
                        "increment_letter": False,
                    },
                    {
                        "start": "B01",
                        "end": "B05",
                        "step": "1",
                        "label_type": choices.CustomAxisLabelsChoices.ALPHANUMERIC,
                        "increment_letter": False,
                    },
                ],
                "valid": True,
            },
            {
                "ranges": [
                    {
                        "start": "A1",
                        "end": "J1",
                        "step": "1",
                        "label_type": choices.CustomAxisLabelsChoices.ALPHANUMERIC,
                        "increment_letter": True,
                    }
                ],
                "valid": True,
            },
            # Invalid cases - range too large
            {
                "ranges": [
                    {
                        "start": "A1",
                        "end": "A20",
                        "step": "1",
                        "label_type": choices.CustomAxisLabelsChoices.ALPHANUMERIC,
                        "increment_letter": False,
                    }
                ],
                "valid": False,
                "error": "Range from A1 to A20 has effective size 20, exceeding maximum size of 10",
            },
            # Invalid cases - non-alphanumeric input
            {
                "ranges": [
                    {
                        "start": "123",
                        "end": "456",
                        "step": "1",
                        "label_type": choices.CustomAxisLabelsChoices.ALPHANUMERIC,
                        "increment_letter": True,
                    }
                ],
                "valid": False,
                "error": "Invalid alphanumeric range: '123' to '456' must include alphabetic characters. Use label_type 'numbers' if no letters are needed.",
            },
        ]

        for test_case in test_cases:
            form_data = fixtures.prepare_formset_data(test_case["ranges"], base_data=None, floors=self.floors)
            form = forms.FloorPlanForm(data=form_data)
            is_valid = form.is_valid()

            if test_case["valid"]:
                self.assertTrue(is_valid, f"Form should be valid for ranges: {test_case['ranges']}")
            else:
                self.assertFalse(is_valid, f"Form should be invalid for ranges: {test_case['ranges']}")
                if "error" in test_case:
                    form_errors = str(form.errors)
                    formset_errors = str([f.errors for f in form.x_ranges.forms])
                    self.assertTrue(
                        test_case["error"] in form_errors or test_case["error"] in formset_errors,
                        f"Expected error '{test_case['error']}' not found in form errors: {form_errors} or formset errors: {formset_errors}",
                    )

    def test_custom_number_range_validation(self):
        """Test validation of custom number range inputs."""
        test_cases = [
            # Valid cases
            {
                "ranges": [
                    {
                        "start": "1",
                        "end": "5",
                        "step": "1",
                        "label_type": choices.CustomAxisLabelsChoices.NUMBERS,
                        "increment_letter": False,
                    },
                    {
                        "start": "10",
                        "end": "15",
                        "step": "1",
                        "label_type": choices.CustomAxisLabelsChoices.NUMBERS,
                        "increment_letter": False,
                    },
                ],
                "valid": True,
            },
            {
                "ranges": [
                    {
                        "start": "01",
                        "end": "05",
                        "step": "1",
                        "label_type": choices.CustomAxisLabelsChoices.NUMBERS,
                        "increment_letter": False,
                    }
                ],
                "valid": True,
            },
            # Invalid cases - range too large
            {
                "ranges": [
                    {
                        "start": "1",
                        "end": "20",
                        "step": "1",
                        "label_type": choices.CustomAxisLabelsChoices.NUMBERS,
                        "increment_letter": False,
                    }
                ],
                "valid": False,
                "error": "Range from 1 to 20 has effective size 20, exceeding maximum size of 10",
            },
            # Invalid cases - non-numeric input
            {
                "ranges": [
                    {
                        "start": "ABC",
                        "end": "DEF",
                        "step": "1",
                        "label_type": choices.CustomAxisLabelsChoices.NUMBERS,
                        "increment_letter": False,
                    }
                ],
                "valid": False,
                "error": "Invalid number format",
            },
            # Invalid cases - overlapping ranges
            {
                "ranges": [
                    {
                        "start": "1",
                        "end": "5",
                        "step": "1",
                        "label_type": choices.CustomAxisLabelsChoices.NUMBERS,
                        "increment_letter": False,
                    },
                    {
                        "start": "3",
                        "end": "7",
                        "step": "1",
                        "label_type": choices.CustomAxisLabelsChoices.NUMBERS,
                        "increment_letter": False,
                    },
                ],
                "valid": False,
                "error": "Ranges overlap",
            },
            # Invalid cases - invalid increment_letter
            {
                "ranges": [
                    {
                        "start": "01",
                        "end": "05",
                        "step": "1",
                        "label_type": choices.CustomAxisLabelsChoices.NUMBERS,
                        "increment_letter": True,
                    }
                ],
                "valid": False,
                "error": "increment_letter must be False when using numeric labels",
            },
        ]

        for test_case in test_cases:
            form_data = fixtures.prepare_formset_data(test_case["ranges"], base_data=None, floors=self.floors)
            form = forms.FloorPlanForm(data=form_data)
            is_valid = form.is_valid()

            if test_case["valid"]:
                self.assertTrue(is_valid, f"Form should be valid for ranges: {test_case['ranges']}")
            else:
                self.assertFalse(is_valid, f"Form should be invalid for ranges: {test_case['ranges']}")
                if "error" in test_case:
                    form_errors = str(form.errors)
                    formset_errors = str([f.errors for f in form.x_ranges.forms])
                    self.assertTrue(
                        test_case["error"] in form_errors or test_case["error"] in formset_errors,
                        f"Expected error '{test_case['error']}' not found in form errors: {form_errors} or formset errors: {formset_errors}",
                    )

    def test_roman_range_validation(self):
        """Test validation of Roman numeral range inputs."""
        test_cases = [
            # Valid cases
            {
                "ranges": [
                    {
                        "start": "I",
                        "end": "V",
                        "step": "1",
                        "label_type": choices.CustomAxisLabelsChoices.ROMAN,
                        "increment_letter": True,
                    },
                    {
                        "start": "XI",
                        "end": "XV",
                        "step": "1",
                        "label_type": choices.CustomAxisLabelsChoices.ROMAN,
                        "increment_letter": True,
                    },
                ],
                "valid": True,
            },
            # Invalid cases
            {
                "ranges": [
                    {
                        "start": "I",
                        "end": "XX",
                        "step": "1",
                        "label_type": choices.CustomAxisLabelsChoices.ROMAN,
                        "increment_letter": True,
                    }
                ],
                "valid": False,
                "error": "Range from I to XX has effective size 20, exceeding maximum size of 10",
            },
            {
                "ranges": [
                    {
                        "start": "ABC",
                        "end": "DEF",
                        "step": "1",
                        "label_type": choices.CustomAxisLabelsChoices.ROMAN,
                        "increment_letter": True,
                    }
                ],
                "valid": False,
                "errors": [
                    "Invalid values for roman - Invalid Roman numeral: ABC",
                    "Invalid values for roman - Invalid Roman numeral character at position 0 in: ABC",
                ],
            },
        ]

        for test_case in test_cases:
            form_data = fixtures.prepare_formset_data(test_case["ranges"], base_data=None, floors=self.floors)
            form = forms.FloorPlanForm(data=form_data)
            is_valid = form.is_valid()

            if test_case["valid"]:
                self.assertTrue(is_valid, f"Form should be valid for ranges: {test_case['ranges']}")
            else:
                self.assertFalse(is_valid, f"Form should be invalid for ranges: {test_case['ranges']}")
                if "error" in test_case:
                    form_errors = str(form.errors)
                    formset_errors = str([f.errors for f in form.x_ranges.forms])
                    self.assertTrue(
                        test_case["error"] in form_errors or test_case["error"] in formset_errors,
                        f"Expected error '{test_case['error']}' not found in form errors: {form_errors} or formset errors: {formset_errors}",
                    )
                elif "errors" in test_case:
                    error_str = str(form.errors)
                    formset_errors = str([f.errors for f in form.x_ranges.forms])
                    self.assertTrue(
                        any(error in error_str or error in formset_errors for error in test_case["errors"]),
                        f"Expected one of {test_case['errors']} in error messages, but got: form errors: {error_str}, formset errors: {formset_errors}",
                    )

    def test_letters_range_validation(self):
        """Test validation of letter range inputs."""
        test_cases = [
            # Valid cases
            {
                "ranges": [
                    {
                        "start": "A",
                        "end": "Z",
                        "step": "1",
                        "label_type": choices.CustomAxisLabelsChoices.LETTERS,
                        "increment_letter": False,
                    },
                    {
                        "start": "AA",
                        "end": "AZ",
                        "step": "1",
                        "label_type": choices.CustomAxisLabelsChoices.LETTERS,
                        "increment_letter": False,
                    },
                ],
                "valid": True,
            },
            {
                "ranges": [
                    {
                        "start": "A",
                        "end": "Z",
                        "step": "1",
                        "label_type": choices.CustomAxisLabelsChoices.LETTERS,
                        "increment_letter": False,
                    },
                    {
                        "start": "AA",
                        "end": "ZZ",
                        "step": "1",
                        "label_type": choices.CustomAxisLabelsChoices.LETTERS,
                        "increment_letter": False,
                    },
                ],
                "valid": True,
            },
            # Invalid cases - range too large
            {
                "ranges": [
                    {
                        "start": "A",
                        "end": "AAA",
                        "step": "1",
                        "label_type": choices.CustomAxisLabelsChoices.LETTERS,
                        "increment_letter": True,
                    }
                ],
                "valid": False,
                "error": "Range from A to AAA has effective size 703, exceeding maximum size of 52",
            },
            # Invalid cases - non-letter input
            {
                "ranges": [
                    {
                        "start": "123",
                        "end": "456",
                        "step": "1",
                        "label_type": choices.CustomAxisLabelsChoices.LETTERS,
                        "increment_letter": False,
                    }
                ],
                "valid": False,
                "error": "Invalid values for letters: '123, 456'",
            },
        ]

        for test_case in test_cases:
            base_data = fixtures.get_default_floor_plan_data(
                self.floors,
                x_size=52,  # Specific size needed for letter tests
                y_size=52,
            )
            form_data = fixtures.prepare_formset_data(test_case["ranges"], base_data=base_data, floors=self.floors)
            form = forms.FloorPlanForm(data=form_data)
            is_valid = form.is_valid()

            if test_case["valid"]:
                self.assertTrue(is_valid, f"Form should be valid for ranges: {test_case['ranges']}")
            else:
                self.assertFalse(is_valid, f"Form should be invalid for ranges: {test_case['ranges']}")
                if "error" in test_case:
                    form_errors = str(form.errors)
                    formset_errors = str([f.errors for f in form.x_ranges.forms])
                    self.assertTrue(
                        test_case["error"] in form_errors or test_case["error"] in formset_errors,
                        f"Expected error '{test_case['error']}' not found in form errors: {form_errors} or formset errors: {formset_errors}",
                    )

    def test_binary_range_validation(self):
        """Test validation of binary range inputs."""
        test_cases = [
            # Valid cases
            {
                "ranges": [
                    {
                        "start": "1",
                        "end": "5",
                        "step": "1",
                        "label_type": choices.CustomAxisLabelsChoices.BINARY,
                        "increment_letter": True,
                    },
                    {
                        "start": "6",
                        "end": "10",
                        "step": "1",
                        "label_type": choices.CustomAxisLabelsChoices.BINARY,
                        "increment_letter": True,
                    },
                ],
                "valid": True,
            },
            # Invalid cases
            {
                "ranges": [
                    {
                        "start": "1",
                        "end": "20",
                        "step": "1",
                        "label_type": choices.CustomAxisLabelsChoices.BINARY,
                        "increment_letter": True,
                    }
                ],
                "valid": False,
                "error": "Range from 1 to 20 has effective size 20, exceeding maximum size of 10",
            },
            {
                "ranges": [
                    {
                        "start": "abc",
                        "end": "def",
                        "step": "1",
                        "label_type": choices.CustomAxisLabelsChoices.BINARY,
                        "increment_letter": True,
                    }
                ],
                "valid": False,
                "error": "Invalid numeric values - invalid literal for int() with base 10: 'abc'",
            },
        ]

        for test_case in test_cases:
            form_data = fixtures.prepare_formset_data(test_case["ranges"], base_data=None, floors=self.floors)
            form = forms.FloorPlanForm(data=form_data)
            is_valid = form.is_valid()

            if test_case["valid"]:
                self.assertTrue(is_valid, f"Form should be valid for ranges: {test_case['ranges']}")
            else:
                self.assertFalse(is_valid, f"Form should be invalid for ranges: {test_case['ranges']}")
                if "error" in test_case:
                    form_errors = str(form.errors)
                    formset_errors = str([f.errors for f in form.x_ranges.forms])
                    self.assertTrue(
                        test_case["error"] in form_errors or test_case["error"] in formset_errors,
                        f"Expected error '{test_case['error']}' not found in form errors: {form_errors} or formset errors: {formset_errors}",
                    )

    def test_hex_range_validation(self):
        """Test validation of hexadecimal range inputs."""
        test_cases = [
            # Valid cases
            {
                "ranges": [
                    {
                        "start": "1",
                        "end": "15",
                        "step": "1",
                        "label_type": choices.CustomAxisLabelsChoices.HEX,
                        "increment_letter": True,
                    },
                    {
                        "start": "16",
                        "end": "30",
                        "step": "1",
                        "label_type": choices.CustomAxisLabelsChoices.HEX,
                        "increment_letter": True,
                    },
                ],
                "valid": True,
            },
            # Invalid cases
            {
                "ranges": [
                    {
                        "start": "0G",
                        "end": "1F",
                        "step": "1",
                        "label_type": choices.CustomAxisLabelsChoices.HEX,
                        "increment_letter": True,
                    }
                ],
                "valid": False,
                "error": "Invalid numeric values - invalid literal for int() with base 10: '0G'",
            },
            {
                "ranges": [
                    {
                        "start": "XX",
                        "end": "YY",
                        "step": "1",
                        "label_type": choices.CustomAxisLabelsChoices.HEX,
                        "increment_letter": True,
                    }
                ],
                "valid": False,
                "error": "Invalid numeric values - invalid literal for int() with base 10: 'XX'",
            },
        ]

        for test_case in test_cases:
            base_data = fixtures.get_default_floor_plan_data(
                self.floors,
                x_size=32,  # Specific size needed for hex tests
                y_size=32,
            )
            form_data = fixtures.prepare_formset_data(test_case["ranges"], base_data=base_data, floors=self.floors)
            form = forms.FloorPlanForm(data=form_data)
            is_valid = form.is_valid()

            if test_case["valid"]:
                self.assertTrue(is_valid, f"Form should be valid for ranges: {test_case['ranges']}")
            else:
                self.assertFalse(is_valid, f"Form should be invalid for ranges: {test_case['ranges']}")
                if "error" in test_case:
                    form_errors = str(form.errors)
                    formset_errors = str([f.errors for f in form.x_ranges.forms])
                    self.assertTrue(
                        test_case["error"] in form_errors or test_case["error"] in formset_errors,
                        f"Expected error '{test_case['error']}' not found in form errors: {form_errors} or formset errors: {formset_errors}",
                    )
