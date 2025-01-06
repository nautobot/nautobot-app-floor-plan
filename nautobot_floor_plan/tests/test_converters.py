"""Test floorplan converters."""

from nautobot.core.testing import TestCase

from nautobot_floor_plan import choices, forms, label_converters, utils
from nautobot_floor_plan.tests import fixtures


class TestLabelConverters(TestCase):
    """Test custom label conversion utilities."""

    def setUp(self):
        """Create test data."""
        data = fixtures.create_prerequisites()
        self.floors = data["floors"]

    def test_binary_converter(self):
        """Test binary label conversion."""
        converter = label_converters.BinaryConverter()
        test_cases = [
            ("0b0001", 1),
            ("0b0010", 2),
            ("0b1010", 10),
        ]
        for label, number in test_cases:
            self.assertEqual(converter.to_numeric(label), number)
            self.assertEqual(converter.from_numeric(number), label)

    def test_hex_converter(self):
        """Test Hexadecimal label conversion."""
        converter = label_converters.HexConverter()
        test_cases = [
            ("0x0001", 1),
            ("0x000A", 10),
            ("0x000F", 15),
        ]
        for label, number in test_cases:
            self.assertEqual(converter.to_numeric(label), number)
            self.assertEqual(converter.from_numeric(number), label)

    def test_numalpha_converter(self):
        """Test numalpha label conversion."""
        converter = label_converters.NumalphaConverter()
        test_cases = [
            ("07A", 1),
            ("07B", 2),
            ("07Z", 26),
            ("08A", 1),
        ]
        for label, expected_number in test_cases:
            # Test conversion to numeric
            self.assertEqual(converter.to_numeric(label), expected_number)

            # Test conversion back to label (with prefix preservation)
            prefix, _ = utils.extract_prefix_and_letter(label)
            converted_label = converter.from_numeric(expected_number, prefix=prefix)
            self.assertEqual(converted_label, label)

            # Test prefix extraction
            extracted_prefix, letter = utils.extract_prefix_and_letter(label)
            self.assertEqual(extracted_prefix + letter, label)

    def test_roman_converter(self):
        """Test roman numeral conversion."""
        converter = label_converters.RomanConverter()
        test_cases = [
            ("I", 1),
            ("V", 5),
            ("X", 10),
            ("L", 50),
        ]
        for label, number in test_cases:
            self.assertEqual(converter.to_numeric(label), number)
            self.assertEqual(converter.from_numeric(number), label)

    def test_alphanumeric_converter(self):
        """Test alphanumeric label conversion."""
        converter = label_converters.AlphanumericConverter()

        # Test with increment_letter=True (default, incrementing numbers)
        converter.set_increment_prefix(False)
        converter.to_numeric("A1")  # Initialize format without leading zeros
        self.assertEqual(converter.from_numeric(1), "A1")
        self.assertEqual(converter.from_numeric(5), "A5")
        self.assertEqual(converter.to_numeric("A1"), 1)
        self.assertEqual(converter.to_numeric("A5"), 5)

        # Test with increment_letter=False (incrementing prefix)
        converter.set_increment_prefix(True)
        converter.to_numeric("A1")  # Initialize format without leading zeros
        self.assertEqual(converter.from_numeric(1), "A1")
        self.assertEqual(converter.from_numeric(2), "B1")
        self.assertEqual(converter.to_numeric("A1"), 1)
        self.assertEqual(converter.to_numeric("B1"), 2)

        # Test with leading zeros
        converter.set_increment_prefix(False)
        converter.to_numeric("A01")  # Initialize format with leading zeros
        self.assertEqual(converter.from_numeric(1), "A01")
        self.assertEqual(converter.from_numeric(5), "A05")

        # Test prefix incrementing with leading zeros
        converter.set_increment_prefix(True)
        converter.to_numeric("A01")  # Initialize format with leading zeros
        self.assertEqual(converter.from_numeric(1), "A01")
        self.assertEqual(converter.from_numeric(2), "B01")

        # Test invalid input
        with self.assertRaises(ValueError):
            converter.to_numeric("ABC")  # No number


class TestPositionAndLabelConverters(TestCase):
    """Test position-to-label and label-to-position conversion."""

    def setUp(self):
        """Create test data."""
        data = fixtures.create_prerequisites()
        self.floors = data["floors"]

        # Create and save a form instance
        self.form = forms.FloorPlanForm(
            data={
                "location": self.floors[1].pk,
                "x_size": 10,
                "y_size": 20,
                "tile_depth": 1,
                "tile_width": 2,
                "x_origin_seed": 1,
                "x_axis_step": 1,
                "x_axis_labels": choices.AxisLabelsChoices.NUMBERS,
                "x_custom_ranges": "null",
                "y_origin_seed": 1,
                "y_axis_step": 1,
                "y_axis_labels": choices.AxisLabelsChoices.NUMBERS,
                "y_custom_ranges": "null",
            }
        )
        if self.form.is_valid():
            self.floor_plan = self.form.save(commit=True)  # Save the instance to the database
        else:
            self.fail(f"Form validation failed: {self.form.errors}")

    def test_numeric_ranges(self):
        """Test numeric ranges with both ascending and descending steps."""
        numeric_ranges = [
            {"start": "01", "end": "05", "step": 1, "increment_letter": False, "label_type": "numbers"},
            {"start": "15", "end": "11", "step": -1, "increment_letter": False, "label_type": "numbers"},
        ]
        self.form.create_custom_axis_labels(numeric_ranges, self.floor_plan, axis="X")

        # Test position to label conversion
        test_cases = [
            {"position": 1, "expected": "01"},
            {"position": 3, "expected": "03"},
            {"position": 5, "expected": "05"},
            {"position": 6, "expected": "15"},
            {"position": 8, "expected": "13"},
            {"position": 10, "expected": "11"},
        ]
        self._test_position_to_label_conversion(test_cases)
        self._test_label_to_position_conversion(test_cases)
        self._test_out_of_range_values()

    def test_alphanumeric_ranges(self):
        """Test alphanumeric ranges with both ascending and descending steps."""
        alphanumeric_ranges = [
            {"start": "A01", "end": "A05", "step": 1, "increment_letter": False, "label_type": "alphanumeric"},
            {"start": "B05", "end": "B01", "step": -1, "increment_letter": False, "label_type": "alphanumeric"},
        ]
        self.form.create_custom_axis_labels(alphanumeric_ranges, self.floor_plan, axis="X")

        test_cases = [
            {"position": 1, "expected": "A01"},
            {"position": 3, "expected": "A03"},
            {"position": 5, "expected": "A05"},
            {"position": 6, "expected": "B05"},
            {"position": 8, "expected": "B03"},
            {"position": 10, "expected": "B01"},
        ]
        self._test_position_to_label_conversion(test_cases)
        self._test_label_to_position_conversion(test_cases)
        self._test_out_of_range_values()

    def test_alphanumeric_incrementing_prefix_ranges(self):
        """Test alphanumeric ranges with both ascending and descending steps and incrementing prefix."""
        alphanumeric_ranges = [
            {"start": "A01", "end": "E01", "step": 1, "increment_letter": True, "label_type": "alphanumeric"},
            {"start": "F05", "end": "F01", "step": -1, "increment_letter": False, "label_type": "alphanumeric"},
        ]
        self.form.create_custom_axis_labels(alphanumeric_ranges, self.floor_plan, axis="X")

        test_cases = [
            {"position": 1, "expected": "A01"},
            {"position": 3, "expected": "C01"},
            {"position": 5, "expected": "E01"},
            {"position": 6, "expected": "F05"},
            {"position": 8, "expected": "F03"},
            {"position": 10, "expected": "F01"},
        ]
        self._test_position_to_label_conversion(test_cases)
        self._test_label_to_position_conversion(test_cases)
        self._test_out_of_range_values()

    def test_numalpha_ranges(self):
        """Test numalpha ranges with both ascending and descending steps."""
        numalpha_ranges = [
            {"start": "02A", "end": "02E", "step": 1, "increment_letter": True, "label_type": "numalpha"},
            {"start": "03E", "end": "03A", "step": -1, "increment_letter": True, "label_type": "numalpha"},
        ]
        self.form.create_custom_axis_labels(numalpha_ranges, self.floor_plan, axis="X")

        test_cases = [
            {"position": 1, "expected": "02A"},
            {"position": 3, "expected": "02C"},
            {"position": 5, "expected": "02E"},
            {"position": 6, "expected": "03E"},
            {"position": 8, "expected": "03C"},
            {"position": 10, "expected": "03A"},
        ]
        self._test_position_to_label_conversion(test_cases)
        self._test_label_to_position_conversion(test_cases)
        self._test_out_of_range_values()

    def test_letter_ranges(self):
        """Test letter ranges with both ascending and descending steps."""
        letter_ranges = [
            {"start": "A", "end": "E", "step": 1, "increment_letter": True, "label_type": "letters"},
            {"start": "K", "end": "G", "step": -1, "increment_letter": True, "label_type": "letters"},
        ]
        self.form.create_custom_axis_labels(letter_ranges, self.floor_plan, axis="X")

        test_cases = [
            {"position": 1, "expected": "A"},
            {"position": 3, "expected": "C"},
            {"position": 5, "expected": "E"},
            {"position": 6, "expected": "K"},
            {"position": 8, "expected": "I"},
            {"position": 10, "expected": "G"},
        ]
        self._test_position_to_label_conversion(test_cases)
        self._test_label_to_position_conversion(test_cases)
        self._test_out_of_range_values()

    def test_roman_ranges(self):
        """Test roman numeral ranges with both ascending and descending steps."""
        roman_ranges = [
            {"start": "I", "end": "V", "step": 1, "increment_letter": True, "label_type": "roman"},
            {"start": "X", "end": "VI", "step": -1, "increment_letter": True, "label_type": "roman"},
        ]
        self.form.create_custom_axis_labels(roman_ranges, self.floor_plan, axis="X")

        test_cases = [
            {"position": 1, "expected": "I"},
            {"position": 3, "expected": "III"},
            {"position": 5, "expected": "V"},
            {"position": 6, "expected": "X"},
            {"position": 8, "expected": "VIII"},
            {"position": 10, "expected": "VI"},
        ]
        self._test_position_to_label_conversion(test_cases)
        self._test_label_to_position_conversion(test_cases)
        self._test_out_of_range_values()

    def test_hex_ranges(self):
        """Test hexadecimal ranges with both ascending and descending steps."""
        hex_ranges = [
            {"start": "1", "end": "5", "step": 1, "increment_letter": True, "label_type": "hex"},
            {"start": "10", "end": "6", "step": -1, "increment_letter": True, "label_type": "hex"},
        ]
        self.form.create_custom_axis_labels(hex_ranges, self.floor_plan, axis="X")

        test_cases = [
            {"position": 1, "expected": "0x0001"},
            {"position": 3, "expected": "0x0003"},
            {"position": 5, "expected": "0x0005"},
            {"position": 6, "expected": "0x000A"},
            {"position": 8, "expected": "0x0008"},
            {"position": 10, "expected": "0x0006"},
        ]
        self._test_position_to_label_conversion(test_cases)
        self._test_label_to_position_conversion(test_cases)
        self._test_out_of_range_values()

    def test_binary_ranges(self):
        """Test binary ranges with both ascending and descending steps."""
        binary_ranges = [
            {"start": "1", "end": "5", "step": 1, "increment_letter": True, "label_type": "binary"},
            {"start": "10", "end": "6", "step": -1, "increment_letter": True, "label_type": "binary"},
        ]
        self.form.create_custom_axis_labels(binary_ranges, self.floor_plan, axis="X")

        test_cases = [
            {"position": 1, "expected": "0b0001"},
            {"position": 3, "expected": "0b0011"},
            {"position": 5, "expected": "0b0101"},
            {"position": 6, "expected": "0b1010"},
            {"position": 8, "expected": "0b1000"},
            {"position": 10, "expected": "0b0110"},
        ]
        self._test_position_to_label_conversion(test_cases)
        self._test_label_to_position_conversion(test_cases)
        self._test_out_of_range_values()

    def test_greek_ranges(self):
        """Test Greek letter ranges with both ascending and descending steps."""
        greek_ranges = [
            {"start": "α", "end": "ε", "step": 1, "increment_letter": True, "label_type": "greek"},
            {"start": "κ", "end": "ζ", "step": -1, "increment_letter": True, "label_type": "greek"},
        ]
        self.form.create_custom_axis_labels(greek_ranges, self.floor_plan, axis="X")

        test_cases = [
            {"position": 1, "expected": "α"},  # alpha
            {"position": 3, "expected": "γ"},  # gamma
            {"position": 5, "expected": "ε"},  # epsilon
            {"position": 6, "expected": "κ"},  # kappa
            {"position": 8, "expected": "θ"},  # theta
            {"position": 10, "expected": "ζ"},  # zeta
        ]
        self._test_position_to_label_conversion(test_cases)
        self._test_label_to_position_conversion(test_cases)
        self._test_out_of_range_values()

    def _test_position_to_label_conversion(self, test_cases):
        """Helper method to test position to label conversion."""
        for test in test_cases:
            with self.subTest(test=test):
                converter = label_converters.PositionToLabelConverter(test["position"], "X", self.floor_plan)
                label = converter.convert()
                self.assertEqual(
                    label,
                    test["expected"],
                    f"Position {test['position']} converted to {label}, expected {test['expected']}",
                )

    def _test_label_to_position_conversion(self, test_cases):
        """Helper method to test label to position conversion."""
        for test in test_cases:
            with self.subTest(test=test):
                converter = label_converters.LabelToPositionConverter(test["expected"], "X", self.floor_plan)
                position, label = converter.convert()
                self.assertEqual(
                    position,
                    test["position"],
                    f"Label {test['expected']} converted to position {position}, expected {test['position']}",
                )
                self.assertEqual(label, test["expected"])

    def _test_out_of_range_values(self):
        """Helper method to test out of range values."""
        # Test position beyond all ranges
        converter = label_converters.PositionToLabelConverter(20, "X", self.floor_plan)
        label = converter.convert()
        self.assertIsNone(label)

        # Test label not in any range
        converter = label_converters.LabelToPositionConverter("25", "X", self.floor_plan)
        with self.assertRaises(ValueError) as context:
            converter.convert()
        self.assertIn("not within any defined range", str(context.exception))
