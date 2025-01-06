"""Test floorplan label generator."""

from nautobot.core.testing import TestCase

from nautobot_floor_plan import models
from nautobot_floor_plan.custom_validators import RangeValidator
from nautobot_floor_plan.tests import fixtures


class TestNumericLabelGenerator(TestCase):
    """Test cases for numeric label generation (numbers and alphanumeric)."""

    def setUp(self):
        """Create LocationType, Status, and Location records."""
        data = fixtures.create_prerequisites()
        self.floors = data["floors"]
        self.status = data["status"]
        self.floor_plan = models.FloorPlan(location=self.floors[0], x_size=10, y_size=10)
        self.floor_plan.validated_save()
        self.validator = RangeValidator(max_size=10)

    def create_custom_labels(self, labels_config, axis="X"):
        """Helper to create custom labels from config."""
        for config in labels_config:
            models.FloorPlanCustomAxisLabel.objects.create(
                floor_plan=self.floor_plan,
                axis=axis,
                start_label=config["start"],
                end_label=config["end"],
                step=config["step"],
                increment_letter=config["increment_letter"],
                label_type=config["label_type"],
            )

    def test_custom_number_ranges(self):
        """Test custom number ranges with basic incrementing."""
        config = [{"start": "1", "end": "5", "step": 1, "increment_letter": True, "label_type": "numbers"}]
        self.create_custom_labels(config)
        labels = self.floor_plan.generate_labels("X", 5)
        expected = ["1", "2", "3", "4", "5"]
        self.assertEqual(labels[: len(expected)], expected)

    def test_custom_number_ranges_with_leading_zeros(self):
        """Test custom number ranges with leading zeros."""
        config = [{"start": "01", "end": "05", "step": 1, "increment_letter": True, "label_type": "numbers"}]
        self.create_custom_labels(config)
        labels = self.floor_plan.generate_labels("X", 5)
        expected = ["01", "02", "03", "04", "05"]
        self.assertEqual(labels[: len(expected)], expected)

    def test_custom_number_ranges_negative_step(self):
        """Test custom number ranges with negative steps."""
        config = [{"start": "5", "end": "1", "step": -1, "increment_letter": True, "label_type": "numbers"}]
        self.create_custom_labels(config)
        labels = self.floor_plan.generate_labels("X", 5)
        expected = ["5", "4", "3", "2", "1"]
        self.assertEqual(labels[: len(expected)], expected)

    def test_custom_number_ranges_with_leading_zeros_negative_step(self):
        """Test custom number ranges with leading zeros and negative steps."""
        config = [{"start": "05", "end": "01", "step": -1, "increment_letter": False, "label_type": "numbers"}]
        self.create_custom_labels(config)
        labels = self.floor_plan.generate_labels("X", 5)
        expected = ["05", "04", "03", "02", "01"]
        self.assertEqual(labels[: len(expected)], expected)

    def test_custom_number_ranges_multiple_ranges(self):
        """Test multiple custom number ranges."""
        config = [
            {"start": "01", "end": "03", "step": 1, "increment_letter": True, "label_type": "numbers"},
            {"start": "10", "end": "12", "step": 1, "increment_letter": True, "label_type": "numbers"},
        ]
        self.create_custom_labels(config)
        labels = self.floor_plan.generate_labels("X", 6)
        expected = ["01", "02", "03", "10", "11", "12"]
        self.assertEqual(labels[: len(expected)], expected)

    def test_custom_number_ranges_mixed_formats(self):
        """Test custom number ranges with mixed formats."""
        config = [
            {"start": "1", "end": "3", "step": 1, "increment_letter": True, "label_type": "numbers"},
            {"start": "04", "end": "06", "step": 1, "increment_letter": True, "label_type": "numbers"},
        ]
        self.create_custom_labels(config)
        labels = self.floor_plan.generate_labels("X", 6)
        expected = ["1", "2", "3", "04", "05", "06"]
        self.assertEqual(labels[: len(expected)], expected)

    def test_custom_alphanumeric_ranges(self):
        """Test custom alphanumeric ranges with number incrementing."""
        config = [{"start": "A01", "end": "A05", "step": 1, "increment_letter": False, "label_type": "alphanumeric"}]
        self.create_custom_labels(config)
        labels = self.floor_plan.generate_labels("X", 5)
        expected = ["A01", "A02", "A03", "A04", "A05"]
        self.assertEqual(labels[: len(expected)], expected)

    def test_custom_alphanumeric_ranges_no_leading_zero(self):
        """Test custom alphanumeric ranges without leading zeros."""
        config = [{"start": "A1", "end": "A5", "step": 1, "increment_letter": False, "label_type": "alphanumeric"}]
        self.create_custom_labels(config)
        labels = self.floor_plan.generate_labels("X", 5)
        expected = ["A1", "A2", "A3", "A4", "A5"]
        self.assertEqual(labels[: len(expected)], expected)

    def test_custom_alphanumeric_ranges_increment_prefix(self):
        """Test custom alphanumeric ranges with prefix incrementing."""
        config = [{"start": "A01", "end": "E01", "step": 1, "increment_letter": True, "label_type": "alphanumeric"}]
        self.create_custom_labels(config)
        labels = self.floor_plan.generate_labels("X", 5)
        expected = ["A01", "B01", "C01", "D01", "E01"]
        self.assertEqual(labels[: len(expected)], expected)

    def test_custom_alphanumeric_ranges_increment_prefix_no_leading_zero(self):
        """Test custom alphanumeric ranges with prefix incrementing and no leading zeros."""
        config = [{"start": "A1", "end": "E1", "step": 1, "increment_letter": True, "label_type": "alphanumeric"}]
        self.create_custom_labels(config)
        labels = self.floor_plan.generate_labels("X", 5)
        expected = ["A1", "B1", "C1", "D1", "E1"]
        self.assertEqual(labels[: len(expected)], expected)

    def test_custom_alphanumeric_ranges_negative(self):
        """Test custom alphanumeric ranges with negative steps."""
        config = [{"start": "A05", "end": "A01", "step": -1, "increment_letter": False, "label_type": "alphanumeric"}]
        self.create_custom_labels(config)
        labels = self.floor_plan.generate_labels("X", 5)
        expected = ["A05", "A04", "A03", "A02", "A01"]
        self.assertEqual(labels[: len(expected)], expected)

    def test_custom_alphanumeric_ranges_negative_prefix(self):
        """Test custom alphanumeric ranges with negative steps and prefix incrementing."""
        config = [{"start": "E01", "end": "A01", "step": -1, "increment_letter": True, "label_type": "alphanumeric"}]
        self.create_custom_labels(config)
        labels = self.floor_plan.generate_labels("X", 5)
        expected = ["E01", "D01", "C01", "B01", "A01"]
        self.assertEqual(labels[: len(expected)], expected)


class TestLetterLabelGenerator(TestCase):
    """Test cases for letter-based label generation (letters and numalpha)."""

    def setUp(self):
        """Create LocationType, Status, and Location records."""
        data = fixtures.create_prerequisites()
        self.floors = data["floors"]
        self.status = data["status"]
        self.floor_plan = models.FloorPlan(location=self.floors[0], x_size=10, y_size=10)
        self.floor_plan.validated_save()
        self.validator = RangeValidator(max_size=10)

    def create_custom_labels(self, labels_config, axis="X"):
        """Helper to create custom labels from config."""
        for config in labels_config:
            models.FloorPlanCustomAxisLabel.objects.create(
                floor_plan=self.floor_plan,
                axis=axis,
                start_label=config["start"],
                end_label=config["end"],
                step=config["step"],
                increment_letter=config["increment_letter"],
                label_type=config["label_type"],
            )

    def test_custom_letter_ranges(self):
        """Test custom letter ranges with different configurations."""
        config = [{"start": "C", "end": "Z", "step": 1, "increment_letter": True, "label_type": "letters"}]
        self.create_custom_labels(config)
        labels = self.floor_plan.generate_labels("X", 24)
        expected = [chr(65 + i) for i in range(2, 26)]  # C through Z
        self.assertEqual(labels[: len(expected)], expected)

    def test_custom_letter_ranges_negative_step(self):
        """Test custom letter ranges with negative steps."""
        config = [{"start": "E", "end": "A", "step": -1, "increment_letter": True, "label_type": "letters"}]
        self.create_custom_labels(config)
        labels = self.floor_plan.generate_labels("X", 5)
        expected = ["E", "D", "C", "B", "A"]
        self.assertEqual(labels[: len(expected)], expected)

    def test_custom_letter_ranges_multiple_ranges(self):
        """Test multiple custom letter ranges."""
        config = [
            {"start": "A", "end": "C", "step": 1, "increment_letter": True, "label_type": "letters"},
            {"start": "X", "end": "Z", "step": 1, "increment_letter": True, "label_type": "letters"},
        ]
        self.create_custom_labels(config)
        labels = self.floor_plan.generate_labels("X", 6)
        expected = ["A", "B", "C", "X", "Y", "Z"]
        self.assertEqual(labels[: len(expected)], expected)

    def test_custom_numalpha_ranges(self):
        """Test custom numalpha ranges with letter incrementing."""
        config = [{"start": "02A", "end": "02E", "step": 1, "increment_letter": True, "label_type": "numalpha"}]
        self.create_custom_labels(config)
        labels = self.floor_plan.generate_labels("X", 5)
        expected = ["02A", "02B", "02C", "02D", "02E"]
        self.assertEqual(labels[: len(expected)], expected)

    def test_custom_numalpha_ranges_no_leading_zero(self):
        """Test custom numalpha ranges without leading zeros."""
        config = [{"start": "2A", "end": "2E", "step": 1, "increment_letter": True, "label_type": "numalpha"}]
        self.create_custom_labels(config)
        labels = self.floor_plan.generate_labels("X", 5)
        expected = ["2A", "2B", "2C", "2D", "2E"]
        self.assertEqual(labels[: len(expected)], expected)

    def test_multiple_numalpha_ranges(self):
        """Test multiple numalpha ranges."""
        config = [
            {"start": "01A", "end": "01C", "step": 1, "increment_letter": True, "label_type": "numalpha"},
            {"start": "02X", "end": "02Z", "step": 1, "increment_letter": True, "label_type": "numalpha"},
        ]
        self.create_custom_labels(config)
        labels = self.floor_plan.generate_labels("X", 6)
        expected = ["01A", "01B", "01C", "02X", "02Y", "02Z"]
        self.assertEqual(labels[: len(expected)], expected)

    def test_custom_numalpha_ranges_multi_letter_negative_step(self):
        """Test custom numalpha ranges with multi-letter sequences and negative steps."""
        config = [
            {"start": "02EE", "end": "02EA", "step": -1, "increment_letter": True, "label_type": "numalpha"},
            {"start": "02E", "end": "02A", "step": -1, "increment_letter": False, "label_type": "numalpha"},
        ]
        self.create_custom_labels(config)
        labels = self.floor_plan.generate_labels("X", 10)
        expected = ["02EE", "02ED", "02EC", "02EB", "02EA", "02E", "02D", "02C", "02B", "02A"]
        self.assertEqual(labels[: len(expected)], expected)

    def test_custom_numalpha_ranges_multi_letter_negative_step_all_letters(self):
        """Test custom numalpha ranges with multi-letter sequences and negative steps, decrementing all letters."""
        config = [
            {"start": "02EE", "end": "02AA", "step": -1, "increment_letter": False, "label_type": "numalpha"},
            {"start": "02E", "end": "02A", "step": -1, "increment_letter": False, "label_type": "numalpha"},
        ]
        self.create_custom_labels(config)
        labels = self.floor_plan.generate_labels("X", 10)
        expected = ["02EE", "02DD", "02CC", "02BB", "02AA", "02E", "02D", "02C", "02B", "02A"]
        self.assertEqual(labels[: len(expected)], expected)


class TestLabelRangeOrder(TestCase):
    """Test cases for custom label range ordering."""

    def setUp(self):
        """Create LocationType, Status, and Location records."""
        data = fixtures.create_prerequisites()
        self.floors = data["floors"]
        self.status = data["status"]
        self.floor_plan = models.FloorPlan(location=self.floors[0], x_size=10, y_size=10)
        self.floor_plan.validated_save()

    def create_custom_labels(self, labels_config, axis="X"):
        """Helper to create custom labels from config."""
        for config in labels_config:
            models.FloorPlanCustomAxisLabel.objects.create(
                floor_plan=self.floor_plan,
                axis=axis,
                start_label=config["start"],
                end_label=config["end"],
                step=config["step"],
                increment_last_letter=config["increment_last_letter"],
                label_type=config["label_type"],
                order=config["order"],
            )


def test_custom_range_order_consistency(self):
    """Test that custom range order is maintained when saving and retrieving."""
    # Create initial ranges in specific order
    config = [
        {
            "start": "02EE",
            "end": "02AA",
            "step": -1,
            "increment_last_letter": True,
            "label_type": "numalpha",
            "order": 1,
        },
        {
            "start": "02E",
            "end": "02A",
            "step": -1,
            "increment_last_letter": False,
            "label_type": "numalpha",
            "order": 2,
        },
    ]
    self.create_custom_labels(config)

    # Verify order in database
    ranges = self.floor_plan.get_custom_ranges("X")
    self.assertEqual(len(ranges), 2)
    self.assertEqual(ranges[0].start_label, "02EE")
    self.assertEqual(ranges[1].start_label, "02E")

    # Verify order in JSON representation
    json_ranges = self.floor_plan.get_custom_ranges_as_json("X")
    self.assertEqual(json_ranges[0]["start"], "02EE")
    self.assertEqual(json_ranges[1]["start"], "02E")


def test_custom_range_order_mixed_types(self):
    """Test that custom range order is maintained with different label types."""
    config = [
        {
            "start": "A01",
            "end": "A05",
            "step": 1,
            "increment_last_letter": True,
            "label_type": "alphanumeric",
            "order": 1,
        },
        {"start": "01", "end": "05", "step": 1, "increment_last_letter": True, "label_type": "numbers", "order": 2},
        {"start": "02A", "end": "02E", "step": 1, "increment_last_letter": True, "label_type": "numalpha", "order": 3},
    ]
    self.create_custom_labels(config)

    # Verify order in database
    ranges = self.floor_plan.get_custom_ranges("X")
    self.assertEqual(len(ranges), 3)
    self.assertEqual(ranges[0].start_label, "A01")
    self.assertEqual(ranges[1].start_label, "01")
    self.assertEqual(ranges[2].start_label, "02A")

    # Verify label generation maintains order
    labels = self.floor_plan.generate_labels("X", 15)
    expected = ["A01", "A02", "A03", "A04", "A05", "01", "02", "03", "04", "05", "02A", "02B", "02C", "02D", "02E"]
    self.assertEqual(labels, expected)
