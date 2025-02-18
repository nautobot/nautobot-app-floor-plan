"""Test floorplan general."""

import unittest

from nautobot_floor_plan.utils import general


class TestGeneralUtils(unittest.TestCase):
    """Test class."""

    def test_grid_number_to_letter(self):
        test_cases = [
            (1, "A"),
            (26, "Z"),
            (27, "AA"),
            (52, "AZ"),
            (53, "BA"),
            (78, "BZ"),
            (79, "CA"),
            (104, "CZ"),
            (703, "AAA"),
            (18278, "ZZZ"),
        ]

        for num, expected in test_cases:
            with self.subTest(num=num):
                self.assertEqual(general.grid_number_to_letter(num), expected)

    def test_gird_letter_to_number(self):
        test_cases = [
            ("A", 1),
            ("Z", 26),
            ("AA", 27),
            ("AZ", 52),
            ("BA", 53),
            ("BZ", 78),
            ("CA", 79),
            ("CZ", 104),
            ("AAA", 703),
            ("ZZZ", 18278),
        ]

        for letter, expected in test_cases:
            with self.subTest(letter=letter):
                self.assertEqual(general.grid_letter_to_number(letter), expected)

    def test_extract_prefix_and_letter(self):
        self.assertEqual(general.extract_prefix_and_letter("02A"), ("02", "A"))
        self.assertEqual(general.extract_prefix_and_letter("12A"), ("12", "A"))
        self.assertEqual(general.extract_prefix_and_letter("123A"), ("123", "A"))

    def test_extract_prefix_and_number(self):
        self.assertEqual(general.extract_prefix_and_number("A02"), ("A", "02"))
        self.assertEqual(general.extract_prefix_and_number("AA1"), ("AA", "1"))
        self.assertEqual(general.extract_prefix_and_number("B23"), ("B", "23"))

    def test_letter_conversion(self):
        self.assertEqual(general.letter_conversion(1), "A")
        self.assertEqual(general.letter_conversion(26), "Z")
        self.assertEqual(general.letter_conversion(27), "AA")
        self.assertEqual(general.letter_conversion(18278), "ZZZ")

    def test_axis_init_label_conversion(self):
        self.assertEqual(general.axis_init_label_conversion(1, 1, 1, False), 1)
        self.assertEqual(general.axis_init_label_conversion(1, 2, 1, False), 2)
        self.assertEqual(general.axis_init_label_conversion(1, "AA", 1, True), "AA")
        self.assertEqual(general.axis_init_label_conversion(1, "Z", 1, True), "Z")
        # Test for Error
        with self.assertRaises(TypeError):
            general.axis_init_label_conversion(1, None, 1, True)  # None should raise ValueError

        with self.assertRaises(TypeError):
            general.axis_init_label_conversion(1, 1.5, 1, True)  # Float should raise ValueError

    def test_axis_clean_label_conversion(self):
        # Test with letters
        self.assertEqual(general.axis_clean_label_conversion(1, "A", 1, True), "1")  # A should return 1
        self.assertEqual(general.axis_clean_label_conversion(1, "B", 1, True), "2")  # B should return 2
        self.assertEqual(general.axis_clean_label_conversion(1, "Z", 1, True), "26")  # Z should return 26
        self.assertEqual(general.axis_clean_label_conversion(1, "AA", 1, True), "27")  # AA should return 27

        # Test with numbers
        self.assertEqual(general.axis_clean_label_conversion(1, 1, 1, False), "1")  # 1 should return 1
        self.assertEqual(general.axis_clean_label_conversion(1, 2, 1, False), "2")  # 2 should return 2

        # Test with custom ranges
        custom_ranges = [{"start": "1", "end": "5"}]
        self.assertEqual(general.axis_clean_label_conversion(1, "3", 1, False, custom_ranges), "3")  # Within range
        self.assertEqual(general.axis_clean_label_conversion(1, "6", 1, False, custom_ranges), "6")  # Outside range

        # Edge cases
        self.assertEqual(general.axis_clean_label_conversion(1, "ZZZ", 1, True), "18278")
        self.assertEqual(general.axis_clean_label_conversion(1, "DDD", 1, True), "2812")
