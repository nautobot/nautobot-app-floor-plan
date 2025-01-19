"""Utilities module."""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def grid_number_to_letter(number):
    """Returns letter for number [1 - 26] --> [A - Z], [27 - 52] --> [AA - AZ]."""
    col_str = ""
    while number:
        remainder = number % 26
        if remainder == 0:
            remainder = 26
        col_letter = chr(ord("A") + remainder - 1)
        col_str = col_letter + col_str
        number = int((number - 1) / 26)
    return col_str


def grid_letter_to_number(letter):
    """Returns number for letter [A - Z] --> [1 - 26], [AA - AZ] --> [27 - 52]."""
    number = ord(letter[-1]) - 64
    if letter[:-1]:
        return 26 * (grid_letter_to_number(letter[:-1])) + number
    return number


def extract_prefix_and_letter(label):
    """Helper function to split a label into prefix and letter parts."""
    prefix = ""
    letters = label

    for i, char in enumerate(label):
        if char.isalpha():
            prefix = label[:i]
            letters = label[i:]
            break

    return prefix, letters


def extract_prefix_and_number(label):
    """Helper function to split a label into prefix and number parts."""
    prefix = ""
    numbers = label

    for i, char in enumerate(label):
        if char.isdigit():
            prefix = label[:i]
            numbers = label[i:]
            break

    return prefix, numbers


def letter_conversion(converted_location):
    """Returns letter conversion and handles wrap around."""
    # Set wrap around value of ZZZ
    total_cells = 18278  # Total cells for AAA-ZZZ
    # Adjust for wrap-around when working with letters A or ZZZ
    if converted_location < 1:
        converted_location = total_cells + converted_location
    elif converted_location > total_cells:
        converted_location -= total_cells
    return grid_number_to_letter(converted_location)


def axis_init_label_conversion(axis_origin, axis_location, step, is_letters):
    """Convert an axis location to its label based on the origin, step, and label type."""
    try:
        if is_letters:
            axis_location = grid_letter_to_number(axis_location)

        converted_location = axis_origin + (int(axis_location) - int(axis_origin)) * step

        if is_letters:
            return letter_conversion(converted_location)

        return converted_location
    except ValidationError as e:
        raise ValidationError(
            f"Error in axis conversion: axis_origin={axis_origin}, "
            f"axis_location={axis_location}, step={step}, is_letters={is_letters}"
        ) from e


def axis_clean_label_conversion(axis_origin, axis_label, step, is_letters, custom_ranges=None):
    """Returns the correct database label position."""
    # First check if we have custom ranges that apply
    if custom_ranges:
        for custom_range in custom_ranges:
            start = custom_range["start"]
            end = custom_range["end"]
            # If our label falls within this custom range, use it
            if start <= axis_label <= end:
                return axis_label  # Return the original label as-is

    # If no custom range applies, use the default conversion logic
    total_cells = 18278
    # Convert letters to numbers if needed
    if is_letters:
        axis_label = grid_letter_to_number(axis_label)

    # Reverse the init conversion logic to determine the numeric position
    position_difference = int(axis_label) - int(axis_origin)

    if step < 0:
        # Adjust for wrap-around when working with letters A or ZZZ
        if int(axis_label) > int(axis_origin):
            position_difference -= total_cells
    else:
        if int(axis_label) < int(axis_origin):
            position_difference += total_cells

    # Calculate the original location using the step
    original_location = axis_origin + (position_difference // step)

    # Ensure original location stays within bounds for letters
    if is_letters:
        if original_location < 1:
            original_location += total_cells
        elif original_location > total_cells:
            original_location -= total_cells
    return str(original_location)


# Depreciate in version 2.6 and remove in 2.7


def validate_not_zero(value):
    """Prevent the usage of 0 as a value in the step form field or model attribute."""
    if value == 0:
        raise ValidationError(
            _("%(value)s is not a positive or negative Integer not equal to zero"),
            params={"value": value},
        )


validate_not_zero.message = "Must be a positive or negative Integer not equal to zero."
