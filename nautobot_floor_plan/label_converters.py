"""Label conversion utilities."""

import logging
import re
from typing import Dict, Type

from nautobot_floor_plan.choices import CustomAxisLabelsChoices
from nautobot_floor_plan.utils import (
    extract_prefix_and_letter,
    extract_prefix_and_number,
    grid_letter_to_number,
    grid_number_to_letter,
)

logger = logging.getLogger(__name__)


class BaseLabelConverter:
    """Base class for converting position to labels and back."""

    def __init__(self, axis, fp_obj):
        """Initializing base Label variables."""
        self.axis = axis
        self.fp_obj = fp_obj
        self.current_position = 1

    def _get_custom_ranges(self):
        """Retrieve and order custom ranges for the axis."""
        return self.fp_obj.custom_labels.filter(axis=self.axis).order_by("id")

    def _get_label_converter(self, label_type):
        """Retrieve the proper converter for label type."""
        return LabelConverterFactory.get_converter(label_type)

    def _calculate_range_size(self, custom_range):
        """Calculate the range size for the given custom range."""
        converter = self._get_label_converter(custom_range.label_type)
        if custom_range.label_type == CustomAxisLabelsChoices.ALPHANUMERIC:
            converter.set_increment_prefix(custom_range.increment_letter)
        start_value = converter.to_numeric(custom_range.start_label)
        end_value = converter.to_numeric(custom_range.end_label)
        return abs(end_value - start_value) + 1

    def _is_descending_range(self, start_value, end_value):
        """Check if the range is descending."""
        return start_value > end_value

    def _check_label_in_range(self, label_value, start_value, end_value):
        """Check if a label value falls within a numeric or letter range."""
        return min(start_value, end_value) <= label_value <= max(start_value, end_value)

    def _is_within_range(self, value, start, end):
        """Check if a value falls within a numeric range."""
        min_value, max_value = min(start, end), max(start, end)
        return min_value <= value <= max_value

    def _adjust_position(self, range_size):
        """Increment the current position by the range size."""
        self.current_position += range_size

    def _calculate_relative_position(self, value, start_value, end_value):
        """Calculate relative position based on ascending/descending range."""
        is_descending = self._is_descending_range(start_value, end_value)
        if is_descending:
            return start_value - value + 1
        return value - start_value + 1

    def _is_letter_based_type(self, label_type):
        """Check if the label type is letter-based."""
        return label_type in [CustomAxisLabelsChoices.NUMALPHA, CustomAxisLabelsChoices.LETTERS]

    def _convert_numeric_values(self, custom_range, value):
        """Convert value and range bounds to numeric values."""
        converter = self._get_label_converter(custom_range.label_type)
        converter.set_increment_prefix(custom_range.increment_letter)

        numeric_value = converter.to_numeric(value)
        start_value = converter.to_numeric(custom_range.start_label)
        end_value = converter.to_numeric(custom_range.end_label)

        return converter, numeric_value, start_value, end_value

    def _extract_prefix_and_letters(self, label, label_type):
        """Extract prefix and letters based on label type."""
        if label_type == CustomAxisLabelsChoices.NUMALPHA:
            return extract_prefix_and_letter(label)
        return "", label

    def _calculate_position_from_values(self, numeric_value, start_value, end_value):
        """Calculate position from numeric values, handling ascending/descending ranges."""
        relative_position = self._calculate_relative_position(numeric_value, start_value, end_value)
        return self.current_position + relative_position - 1


class PositionToLabelConverter(BaseLabelConverter):
    """Class to modify the position to proper custom label in forms."""

    def __init__(self, position, axis, fp_obj):
        """Initialize Position to Label Converter variables."""
        super().__init__(axis, fp_obj)
        self.position = position

    def convert(self):
        """Main method to convert a position to its display label."""
        for custom_range in self._get_custom_ranges():
            range_size = self._calculate_range_size(custom_range)

            if self._position_in_range(range_size):
                return self._calculate_label(custom_range)

            self._adjust_position(range_size)

        return None

    def _position_in_range(self, range_size):
        """Check if the position falls within the current range."""
        return self.current_position <= self.position < self.current_position + range_size

    def _calculate_relative_numeric_value(self, start_value, end_value, relative_position):
        """Calculate numeric value based on ascending/descending range."""
        is_descending = self._is_descending_range(start_value, end_value)
        if is_descending:
            numeric_value = start_value - (relative_position - 1)
            return max(numeric_value, end_value)

        numeric_value = start_value + (relative_position - 1)
        return min(numeric_value, end_value)

    def _calculate_label(self, custom_range):
        """Generate the display label for the position."""
        relative_position = self.position - self.current_position + 1
        converter = self._get_label_converter(custom_range.label_type)
        converter.set_increment_prefix(custom_range.increment_letter)

        start_value = converter.to_numeric(custom_range.start_label)
        end_value = converter.to_numeric(custom_range.end_label)

        if not custom_range.increment_letter:
            numeric_value = self._calculate_relative_numeric_value(start_value, end_value, relative_position)
        else:
            # Use existing incrementing logic for letter-based labels
            is_descending = self._is_descending_range(start_value, end_value)
            numeric_value = (
                start_value - (relative_position - 1) if is_descending else start_value + (relative_position - 1)
            )

        return converter.from_numeric(numeric_value)


class LabelToPositionConverter(BaseLabelConverter):
    """Convert a label to its absolute position based on custom ranges."""

    def __init__(self, label, axis, fp_obj):
        """Initialize the label-to-position converter."""
        super().__init__(axis, fp_obj)
        self.label = label

    def convert(self):
        """Main method to convert a label to its absolute position."""
        for custom_range in self._get_custom_ranges():
            try:
                converter = self._get_label_converter(custom_range.label_type)
                converter.set_increment_prefix(custom_range.increment_letter)

                if self._label_in_range(custom_range):
                    absolute_position = self._calculate_position(custom_range, converter)
                    return absolute_position, self.label

                self._adjust_position(self._calculate_range_size(custom_range))

            except ValueError as e:
                logger.error("Error processing range: %s", e)
                continue

        raise ValueError(f"Value {self.label} is not within any defined range")

    def _label_in_range(self, custom_range):
        """Check if label is within the given range."""
        if custom_range.label_type in [CustomAxisLabelsChoices.ALPHANUMERIC, CustomAxisLabelsChoices.NUMBERS]:
            return self._label_in_alphanumeric_range(custom_range)
        if self._is_letter_based_type(custom_range.label_type):
            return self._label_in_letter_range(custom_range)
        return self._label_in_numeric_range(custom_range)

    def _calculate_position(self, custom_range, converter):
        """Calculate absolute position for any label type."""
        if custom_range.label_type in [CustomAxisLabelsChoices.ALPHANUMERIC, CustomAxisLabelsChoices.NUMBERS]:
            return self._calculate_alphanumeric_position(custom_range)

        numeric_value = converter.to_numeric(self.label)
        start_value = converter.to_numeric(custom_range.start_label)
        end_value = converter.to_numeric(custom_range.end_label)

        return self._calculate_position_from_values(numeric_value, start_value, end_value)

    def _label_in_letter_range(self, custom_range):
        """Check if the label is within a letter-based range."""
        if custom_range.label_type == CustomAxisLabelsChoices.LETTERS:
            _, value, start_value, end_value = self._convert_numeric_values(custom_range, self.label)
            return self._check_label_in_range(value, start_value, end_value)

        # Original logic for NUMALPHA
        start_prefix, start_letters = self._extract_prefix_and_letters(
            custom_range.start_label, custom_range.label_type
        )
        value_prefix, value_letters = self._extract_prefix_and_letters(self.label, custom_range.label_type)

        return value_prefix == start_prefix and len(value_letters) == len(start_letters)

    def _label_in_numeric_range(self, custom_range):
        """Check if the label is within a numeric range."""
        try:
            _, numeric_value, start_value, end_value = self._convert_numeric_values(custom_range, self.label)
            return self._check_label_in_range(numeric_value, start_value, end_value)
        except ValueError as e:
            logger.error("Error converting numeric values: %s", e)
            return False

    def _extract_alphanumeric_parts(self, label, custom_range):
        """Extract and convert alphanumeric parts from label and range."""
        # Extract parts
        parts = {
            "label": extract_prefix_and_number(str(label)),
            "start": extract_prefix_and_number(custom_range.start_label),
            "end": extract_prefix_and_number(custom_range.end_label),
        }

        # Convert numeric parts
        try:
            numbers = {
                "label": int(parts["label"][1]),
                "start": int(parts["start"][1]),
                "end": int(parts["end"][1]),
            }
            prefixes = {
                "label": parts["label"][0],
                "start": parts["start"][0],
                "end": parts["end"][0],
            }
            return prefixes, numbers
        except ValueError:
            return None, None

    def _check_letter_based_range(self, prefixes, numbers, start_num):
        """Check if label is within a letter-based range."""
        if numbers["label"] != start_num:
            return False

        converter = self._get_label_converter(CustomAxisLabelsChoices.LETTERS)
        values = {
            "label": converter.to_numeric(prefixes["label"]),
            "start": converter.to_numeric(prefixes["start"]),
            "end": converter.to_numeric(prefixes["end"]),
        }
        return self._check_label_in_range(values["label"], values["start"], values["end"])

    def _label_in_alphanumeric_range(self, custom_range):
        """Check if the label is within an alphanumeric range."""
        try:
            prefixes, numbers = self._extract_alphanumeric_parts(self.label, custom_range)
            if not prefixes or not numbers:
                return False

            if custom_range.increment_letter:
                return self._check_letter_based_range(prefixes, numbers, numbers["start"])

            # Incrementing numbers: check letter equality and number range
            if prefixes["label"] != prefixes["start"]:
                return False

            return self._check_label_in_range(numbers["label"], numbers["start"], numbers["end"])

        except (ValueError, AttributeError) as e:
            logger.error("Error in _label_in_alphanumeric_range: %s", e)
            return False

    def _calculate_letter_based_position(self, prefixes):
        """Calculate position for letter-based labels."""
        converter = self._get_label_converter(CustomAxisLabelsChoices.LETTERS)
        values = {
            "label": converter.to_numeric(prefixes["label"]),
            "start": converter.to_numeric(prefixes["start"]),
            "end": converter.to_numeric(prefixes["end"]),
        }
        return self._calculate_position_from_values(values["label"], values["start"], values["end"])

    def _calculate_alphanumeric_position(self, custom_range):
        """Calculate position for alphanumeric labels."""
        try:
            prefixes, numbers = self._extract_alphanumeric_parts(self.label, custom_range)
            if not prefixes or not numbers:
                return None

            if custom_range.increment_letter:
                return self._calculate_letter_based_position(prefixes)

            # Handle ascending/descending number ranges
            return self._calculate_position_from_values(numbers["label"], numbers["start"], numbers["end"])

        except (ValueError, AttributeError) as e:
            logger.error("Error in _calculate_alphanumeric_position: %s", e)
            return None


class LabelConverter:
    """Base class for label conversion."""

    def __init__(self):
        """Initialize converter."""
        self._increment_prefix = False
        self.current_label = None

    def to_numeric(self, label: str) -> int:
        """Convert label to numeric value."""
        raise NotImplementedError

    def from_numeric(self, number: int) -> str:
        """Convert numeric value to label."""
        raise NotImplementedError

    def set_increment_prefix(self, increment_prefix: bool) -> None:
        """Set whether to increment the prefix instead of the number."""
        raise NotImplementedError


class NumalphaConverter(LabelConverter):
    """Numalpha (e.g., 02A, 02AA) conversion."""

    def __init__(self):
        """Initialize the converter."""
        super().__init__()
        self._prefix = ""
        self._current_label = None
        self._start_label = None
        self._end_label = None

    def _handle_letter_only_conversion(self, letters):
        """Handle conversion for letter-only labels."""
        return grid_letter_to_number(letters)

    def _handle_mixed_conversion(self, letters):
        """Handle conversion for mixed alphanumeric labels."""
        if not letters:
            return 1
        if self._increment_prefix:
            return grid_letter_to_number(letters)
        return ord(letters[0]) - ord("A") + 1

    def to_numeric(self, label: str) -> int:
        """Convert alphanumeric label to numeric value."""
        self._current_label = label
        if not self._start_label:
            self._start_label = label
        self._end_label = label

        prefix, letters = extract_prefix_and_letter(label)

        if not letters:
            raise ValueError(f"Invalid numalpha label: {label}")

        # Store the prefix for use in from_numeric
        self._prefix = prefix

        # For letters type, always use grid_letter_to_number
        if self._current_label.isalpha():
            numeric_value = self._handle_letter_only_conversion(letters)
        else:
            numeric_value = self._handle_mixed_conversion(letters)

        return numeric_value

    def _generate_letter_pattern(self, number: int, pattern_letters: str) -> str:
        """Generate the letter pattern based on the numeric value."""
        if not self._increment_prefix:
            # Use the pattern from start label
            letter_length = len(pattern_letters)
            if letter_length:
                letter = grid_number_to_letter(number)
                return letter * letter_length
        return grid_number_to_letter(number)

    def from_numeric(self, number: int, prefix: str = "") -> str:
        """Convert numeric value to Numalpha label."""
        if number < 1:
            raise ValueError("Number must be positive")

        # Use provided prefix if given, otherwise use stored prefix
        use_prefix = prefix if prefix else self._prefix

        # Extract pattern letters from the start label
        _, pattern_letters = extract_prefix_and_letter(self._start_label)

        result_letters = self._generate_letter_pattern(number, pattern_letters)
        result = f"{use_prefix}{result_letters}"
        return result

    def set_increment_prefix(self, increment_prefix: bool) -> None:
        """Set whether to increment the prefix instead of the number."""
        self._increment_prefix = increment_prefix


class RomanConverter(LabelConverter):
    """Roman numeral conversion."""

    ROMAN_VALUES = [
        ("M", 1000),
        ("CM", 900),
        ("D", 500),
        ("CD", 400),
        ("C", 100),
        ("XC", 90),
        ("L", 50),
        ("XL", 40),
        ("X", 10),
        ("IX", 9),
        ("V", 5),
        ("IV", 4),
        ("I", 1),
    ]

    def __init__(self):
        """Initialize the converter."""
        super().__init__()
        self._current_value = None

    def _convert_next_numeral(self, label: str, index: int) -> tuple[int, int]:
        """Convert next Roman numeral and return its value and new index."""
        # Try two character combinations first
        if index + 1 < len(label):
            double_char = label[index : index + 2]
            for roman, value in self.ROMAN_VALUES:
                if double_char == roman:
                    return value, index + 2

        # Try single character
        single_char = label[index]
        for roman, value in self.ROMAN_VALUES:
            if single_char == roman:
                return value, index + 1

        raise ValueError(f"Invalid Roman numeral character at position {index} in: {label}")

    def to_numeric(self, label: str) -> int:
        """Convert Roman numeral to integer."""
        if not label:
            raise ValueError("Roman numeral cannot be empty")

        result = 0
        index = 0
        label = label.upper()

        while index < len(label):
            value, index = self._convert_next_numeral(label, index)
            result += value

        self._current_value = result
        return result

    def from_numeric(self, number: int, prefix: str = "") -> str:
        """Convert integer to Roman numeral."""
        if not 0 < number < 4000:
            raise ValueError("Number must be between 1 and 3999")

        result = []
        remaining = number

        for roman, value in self.ROMAN_VALUES:
            while remaining >= value:
                result.append(roman)
                remaining -= value

        roman_numeral = "".join(result)
        return f"{prefix}{roman_numeral}" if prefix else roman_numeral

    def set_increment_prefix(self, increment_prefix: bool) -> None:
        """Set whether to increment the prefix instead of the number.

        For Roman numerals, this setting has no effect as Roman numerals
        are always incremented as a whole number.
        """


class GreekConverter(LabelConverter):
    """Greek letter conversion."""

    GREEK_LETTERS = "αβγδεζηθικλμνξοπρστυφχψω"
    GREEK_LETTER_MAP = {letter: i + 1 for i, letter in enumerate(GREEK_LETTERS)}

    def __init__(self):
        """Initialize the converter."""
        super().__init__()
        self._current_value = None
        self._prefix = ""

    def to_numeric(self, label: str) -> int:
        """Convert Greek letter to numeric value."""
        if not label:
            raise ValueError("Greek letter cannot be empty")

        # Handle prefixed numbers (like α1, β2)
        prefix = ""
        greek_part = label.lower()

        # Split numeric suffix if exists
        for i, char in enumerate(label):
            if char.isdigit():
                prefix = label[i:]
                greek_part = label[:i].lower()
                break

        try:
            base_value = self.GREEK_LETTER_MAP.get(greek_part)
            if base_value is None:
                raise ValueError(f"Invalid Greek letter: {greek_part}")

            self._current_value = base_value
            if prefix:
                self._prefix = prefix
                return int(f"{base_value}{prefix}")
            return base_value

        except ValueError as e:
            raise ValueError(f"Invalid Greek letter: {label}") from e

    def from_numeric(self, number: int, prefix: str = "") -> str:
        """Convert numeric value to Greek letter."""
        if number < 1 or number > len(self.GREEK_LETTERS):
            raise ValueError(f"Number must be between 1 and {len(self.GREEK_LETTERS)}")

        greek_letter = self.GREEK_LETTERS[number - 1]
        if prefix:
            return f"{prefix}{greek_letter}"
        if self._prefix:
            return f"{greek_letter}{self._prefix}"
        return greek_letter

    def set_increment_prefix(self, increment_prefix: bool) -> None:
        """Set whether to increment the prefix instead of the number.

        For Greek letters, this setting has no effect as Greek letters
        are always incremented as a whole.
        """


class BinaryConverter(LabelConverter):
    """Binary number conversion."""

    def __init__(self, min_digits: int = 4):
        """Initialize the converter with a minimum digit width."""
        super().__init__()
        self.min_digits = min_digits

    def to_numeric(self, label: str) -> int:
        """Convert a label to a numeric value."""
        try:
            # If the label starts with '0b', interpret as binary
            if isinstance(label, str) and label.startswith("0b"):
                return int(label, 2)
            # Otherwise treat as decimal
            return int(label)
        except ValueError as e:
            raise ValueError(f"Label must be an integer or binary value, received: {label}") from e

    def from_numeric(self, number: int, prefix: str = "") -> str:
        """Convert a numeric value to a binary string with a '0b' prefix."""
        if number < 0:
            raise ValueError("Binary conversion requires positive numbers")

        binary = bin(number)[2:].zfill(self.min_digits)  # Ensure minimum digit width
        return f"{prefix}0b{binary}" if prefix else f"0b{binary}"

    def set_increment_prefix(self, increment_prefix: bool) -> None:
        """Set whether to increment the prefix instead of the number.

        For binary numbers, this setting has no effect as binary numbers
        are always incremented as a whole number.
        """


class HexConverter(LabelConverter):
    """Hexadecimal number conversion."""

    def __init__(self, min_digits: int = 4):
        """Initialize the converter with a minimum digit width."""
        super().__init__()
        self.min_digits = min_digits

    def to_numeric(self, label: str) -> int:
        """Convert a label to a numeric value."""
        try:
            # If the label starts with '0x', interpret as hex
            if isinstance(label, str) and label.startswith("0x"):
                return int(label, 16)
            # Otherwise treat as decimal
            return int(label)
        except ValueError as e:
            raise ValueError(f"Label must be an integer or hex value, received: {label}") from e

    def from_numeric(self, number: int, prefix: str = "") -> str:
        """Convert numeric value to hex string."""
        if number < 0:
            raise ValueError("Hex conversion requires positive numbers")

        hex_val = hex(number)[2:].upper().zfill(self.min_digits)
        return f"{prefix}0x{hex_val}" if prefix else f"0x{hex_val}"

    def set_increment_prefix(self, increment_prefix: bool) -> None:
        """Set whether to increment the prefix instead of the number.

        For hex numbers, this setting has no effect as hex numbers
        are always incremented as a whole number.
        """


class AlphanumericConverter(LabelConverter):
    """Alphanumeric (e.g., A01, A1) and pure number (e.g., 01, 1) conversion."""

    def __init__(self):
        """Initialize the converter."""
        super().__init__()
        self._prefix = ""
        self._use_leading_zeros = None
        self._number = None
        self._is_number_only = False
        self._increment_prefix = False

    def to_numeric(self, label: str) -> int:
        """Convert alphanumeric or numeric label to numeric value."""
        if self._is_number_only:
            if not label.isdigit():
                raise ValueError(f"Invalid number format: {label}")
            self._use_leading_zeros = len(label) > 1 and label[0] == "0"
            self._number = label
            return int(label)

        prefix, number = extract_prefix_and_number(label)
        if not number.isdigit():
            raise ValueError(f"Invalid alphanumeric label: {label}. Must have a numeric part.")

        self._prefix = prefix
        self._use_leading_zeros = len(number) > 1 and number[0] == "0"
        self._number = number

        if self._increment_prefix:
            return sum((ord(c) - ord("A") + 1) * (26**i) for i, c in enumerate(reversed(prefix)))
        return int(number)

    def from_numeric(self, number: int, prefix: str = "") -> str:
        """Convert numeric value to alphanumeric or numeric label."""
        if number < 1:
            raise ValueError("Number must be positive")

        if self._is_number_only:
            return f"{number:02d}" if self._use_leading_zeros else str(number)

        if self._increment_prefix:
            prefix = self._generate_prefix(number)
            return f"{prefix}{self._number if self._use_leading_zeros else int(self._number)}"

        return f"{self._prefix}{number:02d}" if self._use_leading_zeros else f"{self._prefix}{number}"

    def _generate_prefix(self, number: int) -> str:
        """Generate alphabetic prefix for a given numeric value."""
        if number < 1:
            raise ValueError("Number must be positive")
        return grid_number_to_letter(number)

    def set_increment_prefix(self, increment_prefix: bool) -> None:
        """Set whether to increment the prefix instead of the number."""
        self._increment_prefix = increment_prefix

    def set_number_only_mode(self, is_number_only: bool) -> None:
        """Set whether the converter should handle pure numbers."""
        self._is_number_only = is_number_only

    def set_prefix(self, prefix: str) -> None:
        """Set the prefix for the label converter."""
        if not re.match(r"^[A-Z]+$", prefix):
            raise ValueError("Prefix must be a non-empty string of uppercase letters")
        self._prefix = prefix


class LabelConverterFactory:
    """Factory for creating label converters."""

    _converters: Dict[str, Type[LabelConverter]] = {
        CustomAxisLabelsChoices.ROMAN: RomanConverter,
        CustomAxisLabelsChoices.GREEK: GreekConverter,
        CustomAxisLabelsChoices.BINARY: BinaryConverter,
        CustomAxisLabelsChoices.HEX: HexConverter,
        CustomAxisLabelsChoices.NUMALPHA: NumalphaConverter,
        CustomAxisLabelsChoices.LETTERS: NumalphaConverter,
        CustomAxisLabelsChoices.ALPHANUMERIC: AlphanumericConverter,
        CustomAxisLabelsChoices.NUMBERS: AlphanumericConverter,
    }

    @classmethod
    def get_converter(cls, label_type: str) -> LabelConverter:
        """Get the appropriate converter for the label type."""
        converter_class = cls._converters.get(label_type)
        if not converter_class:
            raise ValueError(
                f"Unsupported label type: {label_type}. " f"Supported types are: {', '.join(cls._converters.keys())}"
            )
        return converter_class()
