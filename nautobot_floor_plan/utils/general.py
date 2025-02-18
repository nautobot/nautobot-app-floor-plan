"""Utilities module."""

from __future__ import annotations

from typing import List, Optional, Tuple, TypedDict, Union

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class CustomRange(TypedDict, total=False):
    """
    Optional dictionary for specifying custom axis range parameters.

    Keys:
        - start: The starting value (int or str).
        - end: The ending value (int or str).
        - step: The step value (int).
        - label_type: The type of label (str).
        - increment_letter: Whether the letter should increment (bool).
    """

    start: Union[int, str]
    end: Union[int, str]
    step: int
    label_type: str
    increment_letter: bool


def grid_number_to_letter(number: int) -> str:
    """Returns letter for number [1 - 26] --> [A - Z], [27 - 52] --> [AA - AZ]."""
    col_str: str = ""
    while number:
        remainder: int = number % 26
        if remainder == 0:
            remainder = 26
        col_letter: str = chr(ord("A") + remainder - 1)
        col_str = col_letter + col_str
        number = int((number - 1) / 26)
    return col_str


def grid_letter_to_number(letter: str) -> int:
    """Returns number for letter [A - Z] --> [1 - 26], [AA - AZ] --> [27 - 52]."""
    number: int = ord(letter[-1]) - 64
    if letter[:-1]:
        return 26 * grid_letter_to_number(letter[:-1]) + number
    return number


def extract_prefix_and_letter(label: str) -> Tuple[str, str]:
    """Helper function to split a label into prefix and letter parts."""
    prefix: str = ""
    letters: str = label

    for i, char in enumerate(label):
        if char.isalpha():
            prefix = label[:i]
            letters = label[i:]
            break

    return prefix, letters


def extract_prefix_and_number(label: str) -> Tuple[str, str]:
    """Helper function to split a label into prefix and number parts."""
    prefix: str = ""
    numbers: str = label

    for i, char in enumerate(label):
        if char.isdigit():
            prefix = label[:i]
            numbers = label[i:]
            break

    return prefix, numbers


def letter_conversion(converted_location: int) -> str:
    """Returns letter conversion and handles wrap around."""
    # Set wrap around value of ZZZ
    total_cells: int = 18278  # Total cells for AAA-ZZZ
    # Adjust for wrap-around when working with letters A or ZZZ
    if converted_location < 1:
        converted_location = total_cells + converted_location
    elif converted_location > total_cells:
        converted_location -= total_cells
    return grid_number_to_letter(converted_location)


def axis_init_label_conversion(
    axis_origin: int, axis_location: Union[int, str], step: int, is_letters: bool
) -> Union[str, int]:
    """Convert an axis location to its label based on the origin, step, and label type."""
    # Explicit type checks:
    if not isinstance(axis_origin, int):
        raise TypeError("axis_origin must be int")
    if not isinstance(axis_location, (int, str)):
        raise TypeError("axis_location must be int or str")
    if not isinstance(step, int):
        raise TypeError("step must be int")
    if not isinstance(is_letters, bool):
        raise TypeError("is_letters must be bool")

    try:
        if is_letters:
            # If using letters, ensure axis_location is converted from str to int via grid_letter_to_number.
            axis_location = grid_letter_to_number(str(axis_location))
        converted_location: int = axis_origin + (int(axis_location) - int(axis_origin)) * step

        if is_letters:
            return letter_conversion(converted_location)
        return converted_location
    except Exception as e:
        raise e


def axis_clean_label_conversion(
    axis_origin: int,
    axis_label: Union[int, str],
    step: int,
    is_letters: bool,
    custom_ranges: Optional[List[CustomRange]] = None,
) -> str:
    """Returns the correct database label position."""
    # First check if we have custom ranges that apply
    if custom_ranges:
        for custom_range in custom_ranges:
            if "start" not in custom_range or "end" not in custom_range:
                continue
            if is_letters:
                start_val = grid_letter_to_number(str(custom_range["start"]))
                end_val = grid_letter_to_number(str(custom_range["end"]))
                label_val = grid_letter_to_number(str(axis_label))
            else:
                try:
                    start_val = int(custom_range["start"])
                    end_val = int(custom_range["end"])
                    label_val = int(axis_label)
                except (ValueError, TypeError):
                    continue

            if start_val <= label_val <= end_val:
                return str(axis_label)

    # If no custom range applies, use the default conversion logic
    total_cells: int = 18278
    # Convert letters to numbers if needed
    if is_letters:
        axis_label = grid_letter_to_number(str(axis_label))

    # Reverse the init conversion logic to determine the numeric position
    position_difference: int = int(axis_label) - int(axis_origin)

    if step < 0:
        # Adjust for wrap-around when working with letters A or ZZZ
        if int(axis_label) > int(axis_origin):
            position_difference -= total_cells
    else:
        if int(axis_label) < int(axis_origin):
            position_difference += total_cells

    # Calculate the original location using the step
    original_location: int = axis_origin + (position_difference // step)

    # Ensure original location stays within bounds for letters
    if is_letters:
        if original_location < 1:
            original_location += total_cells
        elif original_location > total_cells:
            original_location -= total_cells
    return str(original_location)


# Depreciate in version 2.6 and remove in 2.7


def validate_not_zero(value: int) -> None:
    """Prevent the usage of 0 as a value in the step form field or model attribute."""
    if value == 0:
        raise ValidationError(
            _("%(value)s is not a positive or negative Integer not equal to zero"),
            params={"value": value},
        )


validate_not_zero.message = "Must be a positive or negative Integer not equal to zero."
