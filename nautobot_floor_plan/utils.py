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


def axis_init_label_conversion(axis_origin, axis_location, step, letters):
    """Returns the correct label position, converting to letters if `letters` is True."""
    if letters:
        axis_location = grid_letter_to_number(axis_location)
    # Calculate the converted location based on origin, step, and location
    converted_location = axis_origin + (int(axis_location) - int(axis_origin)) * step
    # Check if we need wrap around due to letters being chosen
    if letters:
        # Set wrap around value of ZZZ
        total_cells = 18278
        # Adjust for wrap-around when working with letters A or ZZZ
        if converted_location < 1:
            converted_location = total_cells + converted_location
        elif converted_location > total_cells:
            converted_location -= total_cells
        result_label = grid_number_to_letter(converted_location)
        return result_label
    return converted_location


def axis_clean_label_conversion(axis_origin, axis_label, step, letters):
    """Returns the correct database label position."""
    total_cells = 18278
    # Convert letters to numbers if needed
    if letters:
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
    if letters:
        if original_location < 1:
            original_location += total_cells
        elif original_location > total_cells:
            original_location -= total_cells
    return str(original_location)


def validate_not_zero(value):
    """Prevent the usage of 0 as a value in the step form field or model attribute."""
    if value == 0:
        raise ValidationError(
            _("%(value)s is not a positive or negative Integer not equal to zero"),
            params={"value": value},
        )


validate_not_zero.message = "Must be a positive or negative Integer not equal to zero."
