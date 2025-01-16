"""Test floorplan utils."""

import unittest

from nautobot_floor_plan.utils import general


class TestUtils(unittest.TestCase):
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
