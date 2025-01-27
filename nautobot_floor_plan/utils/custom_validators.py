"""Validators for nautobot_floor_plan."""

from dataclasses import dataclass

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import BaseValidator
from nautobot.apps.models import CustomValidator
from nautobot.dcim.models import Rack

from nautobot_floor_plan import choices, models
from nautobot_floor_plan.utils import general
from nautobot_floor_plan.utils.label_converters import LabelConverterFactory


class RangeValidator:
    """Helper class to validate custom ranges."""

    def __init__(self, max_size):
        """Initialize validator with max size."""
        self.max_size = max_size
        self.current_range = None

    def validate_required_keys(self, label_range):
        """Validate that all required keys are present in the range."""
        required_keys = {"start", "end", "label_type"}
        if not all(k in label_range for k in required_keys):
            raise forms.ValidationError(f"Range is missing required keys {required_keys}.")

    def validate_label_type(self, label_type):
        """Validate the label type is valid."""
        if label_type not in dict(choices.CustomAxisLabelsChoices.CHOICES):
            raise forms.ValidationError(
                f"Invalid label type '{label_type}' ."
                f"Valid types are: {', '.join(choices.CustomAxisLabelsChoices.values())}"
            )

    @dataclass
    class RangeData:
        """
        Represents data required for range calculations.

        Attributes:
            start (str): The starting label of the range.
            end (str): The ending label of the range.
            start_num (int): The numeric equivalent of the starting label.
            end_num (int): The numeric equivalent of the ending label.
            step (int): The step interval for generating range labels.
            label_type (str): The type of labels (e.g., 'alphanumeric', 'numbers').
        """

        start: str
        end: str
        start_num: int
        end_num: int
        step: int
        label_type: str

    def validate_numeric_range(self, start, end, current_range=None):
        """Validate numeric ranges (hex, binary) considering step size."""
        self.current_range = current_range
        try:
            start_num = int(start)
            end_num = int(end)
            step = self.get_step_from_range()

            range_data = self.RangeData(
                start=start, end=end, start_num=start_num, end_num=end_num, step=step, label_type=""
            )

            effective_size = self._calculate_numeric_range_size(
                range_data.start_num, range_data.end_num, range_data.step
            )

            if effective_size > self.max_size:
                raise ValidationError(
                    f"Range from {start} to {end} has effective size {effective_size}, "
                    f"exceeding maximum size of {self.max_size}"
                )
        except ValueError as e:
            raise ValidationError(f"Invalid numeric values - {str(e)}") from e

    def get_step_from_range(self):
        """Get step value from the range."""
        return self.current_range.get("step", 1) if self.current_range else 1

    def validate_numalpha_prefix(self, start, end, _):
        """Validate that numalpha prefixes match."""
        start_prefix, _ = general.extract_prefix_and_letter(start)
        end_prefix, _ = general.extract_prefix_and_letter(end)

        if start_prefix != end_prefix:
            raise ValidationError(
                f"Range: '{start_prefix}' != '{end_prefix}'. Use separate ranges for different prefixes"
            )

    def validate_increment_letter_for_numbers(self, increment_letter):
        """Validate increment_letter for numbers."""
        if increment_letter:
            raise ValidationError("increment_letter must be False when using numeric labels")

    def validate_custom_range(self, start, end, label_type, current_range=None):
        """Validate custom label ranges considering step size and prefix matching."""
        self.current_range = current_range
        try:
            converter = LabelConverterFactory.get_converter(label_type)

            # Set number-only mode for number labels
            if label_type == choices.CustomAxisLabelsChoices.NUMBERS:
                converter.set_number_only_mode(True)

            # Get numeric values and create range data
            range_data = self.RangeData(
                start=start,
                end=end,
                start_num=converter.to_numeric(start),
                end_num=converter.to_numeric(end),
                step=self.get_step_from_range(),
                label_type=label_type,
            )

            # Check numalpha prefix matching
            if label_type == choices.CustomAxisLabelsChoices.NUMALPHA:
                self.validate_numalpha_prefix(start, end, current_range)

            # Check alphanumeric labels for valid letters
            if label_type == choices.CustomAxisLabelsChoices.ALPHANUMERIC:
                if not (self._contains_letter(start) and self._contains_letter(end)):
                    raise ValidationError(
                        f"Invalid alphanumeric range: '{start}' to '{end}' must include alphabetic characters. "
                        f"Use label_type '{choices.CustomAxisLabelsChoices.NUMBERS}' if no letters are needed."
                    )

            effective_size = self._calculate_effective_size(range_data)

            if effective_size > self.max_size:
                raise ValidationError(
                    f"Range from {start} to {end} has effective size {effective_size}, "
                    f"exceeding maximum size of {self.max_size}"
                )
        except ValueError as e:
            raise ValidationError(f"Invalid values for {label_type} - {str(e)}") from e

    def _contains_letter(self, label):
        """Check if a label contains at least one alphabetic character."""
        return any(char.isalpha() for char in label)

    def _calculate_effective_size(self, range_data: RangeData):
        """Calculate the effective size of the range based on label type and configuration."""
        if range_data.label_type in [choices.CustomAxisLabelsChoices.LETTERS, choices.CustomAxisLabelsChoices.NUMALPHA]:
            return self._calculate_letter_range_size(range_data.start, range_data.end)
        return self._calculate_numeric_range_size(range_data.start_num, range_data.end_num, range_data.step)

    def _calculate_letter_range_size(self, start, end):
        """Calculate the size of letter-based ranges."""
        _, start_letters = general.extract_prefix_and_letter(start)
        _, end_letters = general.extract_prefix_and_letter(end)

        # Check if this is a letters-only range
        if self.current_range and self.current_range.get("label_type") == choices.CustomAxisLabelsChoices.LETTERS:
            if not start.isalpha() or not end.isalpha():
                raise ValidationError(f"Invalid values for letters: '{start}, {end}'")

        if self.current_range and self.current_range.get("increment_letter"):
            # For increment_letter=True, use full grid_letter_to_number conversion
            start_pos = general.grid_letter_to_number(start_letters)
            end_pos = general.grid_letter_to_number(end_letters)
        else:
            # For increment_letter=False, only look at first character
            start_pos = general.grid_letter_to_number(start_letters[0])
            end_pos = general.grid_letter_to_number(end_letters[0])

        step = self.get_step_from_range()
        range_size = end_pos - start_pos + 1

        if step and step < 0:
            return range_size if start_pos >= end_pos else 0
        return range_size if start_pos <= end_pos else 0

    def _calculate_numeric_range_size(self, start_num, end_num, step):
        """Calculate the size of numeric ranges."""
        range_data = self.RangeData(
            start=str(start_num),
            end=str(end_num),
            start_num=start_num,
            end_num=end_num,
            step=step,
            label_type="",
        )

        if range_data.step and range_data.step < 0:
            if range_data.start_num < range_data.end_num:
                raise ValidationError(
                    f"With negative step {range_data.step}, start value must be greater than end value"
                )
            return len(range(range_data.start_num, range_data.end_num - 1, range_data.step))

        if range_data.start_num > range_data.end_num:
            raise ValidationError(f"With positive step {range_data.step}, start value must be less than end value")
        return len(range(range_data.start_num, range_data.end_num + 1, abs(range_data.step) if range_data.step else 1))

    def validate_increment_letter(self, label_range, label_type):
        """Validate increment_letter if present for letter type."""
        if label_type == choices.CustomAxisLabelsChoices.LETTERS:
            increment_letter = label_range.get("increment_letter")
            if increment_letter is not None and not isinstance(increment_letter, bool):
                raise forms.ValidationError("increment_letter at must be a boolean value.")

    def check_range_overlap(self, range1, range2):
        """Check if two ranges overlap."""
        # Only check overlap for ranges of the same label type
        if range1["label_type"] != range2["label_type"]:
            return False

        label_type = range1["label_type"]
        converter = LabelConverterFactory.get_converter(label_type)

        def alphanumeric_overlap(range1, range2):
            """Check overlap for alphanumeric ranges."""
            # Extract prefix and numbers using the utility function
            prefix1, num1 = general.extract_prefix_and_number(range1["start"])
            _, num1_end = general.extract_prefix_and_number(range1["end"])
            prefix2, num2 = general.extract_prefix_and_number(range2["start"])
            _, num2_end = general.extract_prefix_and_number(range2["end"])

            # Different prefixes can't overlap
            if prefix1 != prefix2:
                return False

            # Convert to integers for comparison
            num1_start = int(num1)
            num1_end = int(num1_end)
            num2_start = int(num2)
            num2_end = int(num2_end)

            # Check numeric overlap
            return not (num1_end < num2_start or num2_end < num1_start)

        def numalpha_overlap(range1, range2):
            """Check overlap for numalpha ranges."""
            # Extract prefix (numbers) and letters
            prefix1, letter1_start = general.extract_prefix_and_letter(range1["start"])
            _, letter1_end = general.extract_prefix_and_letter(range1["end"])
            prefix2, letter2_start = general.extract_prefix_and_letter(range2["start"])
            _, letter2_end = general.extract_prefix_and_letter(range2["end"])

            # Different numeric prefixes can't overlap
            if prefix1 != prefix2:
                return False

            # For numalpha ranges, we need to consider the direction (step)
            step1 = range1.get("step", 1)
            step2 = range2.get("step", 1)

            # Convert letters to numeric values using existing utility function
            start1 = general.grid_letter_to_number(letter1_start)
            end1 = general.grid_letter_to_number(letter1_end)
            start2 = general.grid_letter_to_number(letter2_start)
            end2 = general.grid_letter_to_number(letter2_end)

            # Adjust ranges based on step direction
            if step1 < 0:
                start1, end1 = end1, start1
            if step2 < 0:
                start2, end2 = end2, start2

            # Check for overlap
            return not (end1 < start2 or end2 < start1)

        if label_type == choices.CustomAxisLabelsChoices.ALPHANUMERIC:
            return alphanumeric_overlap(range1, range2)

        if label_type == choices.CustomAxisLabelsChoices.NUMALPHA:
            return numalpha_overlap(range1, range2)

        if label_type == choices.CustomAxisLabelsChoices.NUMBERS:
            converter.set_number_only_mode(True)

        def create_range_data(range_info):
            """Helper to create a RangeData object."""
            # Validate step value first
            step = range_info.get("step", 1)
            if step == 0:
                raise ValidationError("Step value must be a non-zero integer.")

            return self.RangeData(
                start=range_info["start"],
                end=range_info["end"],
                start_num=converter.to_numeric(range_info["start"]),
                end_num=converter.to_numeric(range_info["end"]),
                step=step,
                label_type=label_type,
            )

        try:
            range1_data = create_range_data(range1)
            range2_data = create_range_data(range2)

            def generate_labels(range_data):
                """Generate label set for a range."""
                return {
                    converter.from_numeric(i)
                    for i in range(range_data.start_num, range_data.end_num + 1, range_data.step)
                }

            labels1 = generate_labels(range1_data)
            labels2 = generate_labels(range2_data)

            # Check for any common labels
            return bool(labels1.intersection(labels2))
        except ValueError as e:
            raise ValidationError(f"Invalid values for {label_type} - {str(e)}") from e

    def validate_multiple_ranges(self, ranges):
        """Validate that multiple ranges don't overlap."""
        if not ranges or len(ranges) <= 1:
            return

        # Check each pair of ranges for overlap
        for i, range1 in enumerate(ranges):
            for range2 in ranges[i + 1 :]:
                if self.check_range_overlap(range1, range2):
                    raise ValidationError("Ranges overlap")


class ValidateNotZero(BaseValidator):
    """Ensure that the field's value is not zero."""

    message = "Must be a positive or negative Integer not equal to zero."
    code = "zero_not_allowed"

    def __call__(self, value):
        """Ensure that the field's value is not zero."""
        if value == 0:
            raise ValidationError(
                self.message,
                code=self.code,
            )


class RackValidator(CustomValidator):
    """Custom Validator to verify a Rack is not installed on a Floor Plan before allowing the changing of Location."""

    model = "dcim.rack"

    def clean(self):
        """
        Validate that the Rack's location is not changed if it is installed on a Floor Plan.

        Raises:
            ValidationError: If the Rack is installed on a Floor Plan and its location is being changed.
        """
        rack = self.context["object"]

        # Skip validation if the Rack is new
        if rack.present_in_database:
            # Get the original instance of the rack
            original_instance = Rack.objects.get(pk=rack.pk)

            # Check if the location is being changed
            if (
                original_instance.location_id != rack.location_id
                and models.FloorPlanTile.objects.filter(rack=rack).exists()
            ):
                self.validation_error({"location": "Cannot move Rack as it is currently installed in a FloorPlan."})


custom_validators = [RackValidator]
