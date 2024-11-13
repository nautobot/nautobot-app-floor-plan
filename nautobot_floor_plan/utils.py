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
    converted_location = axis_origin + (int(axis_location) - int(axis_origin)) * step

    # Check if we need to convert the position to a letter
    if letters:
        # Special case for 0 --> 'Z'
        if converted_location == 0:
            return grid_number_to_letter(26)
        return grid_number_to_letter(converted_location)

    # Return as-is for numeric values
    return converted_location


def axis_clean_label_conversion(axis_origin, axis_location, step, letters):
    """Convert the visible grid label back to the database-stored numeric index, handling negative steps with letter wrapping logic."""
    original_location = 0
    max_steps = 100  # safety limit for steps to prevent infinite loops
    # Step 1: Convert letters to numbers if needed
    if letters:
        axis_location = grid_letter_to_number(axis_location)
        # Step 2: Calculate the distance between origin and location with step handling
        if step < 0 and (axis_location > axis_origin):
            # Initialize step count and position trackers
            current_position = axis_origin
            steps_taken = 0
            # Move towards the target position with wrapping logic
            while current_position != axis_location:
                current_position += step
                print(f"current_position {current_position}")
                print(f"axis_location {axis_location}")
                steps_taken += 1
                # Wrap around if below 1 (A in alphabet grid)
                if current_position < 1:
                    current_position += 26  # Wrap to 'Z' (26)
                    print(f'We had to wrap around {current_position}')

                # Final position in the grid, counting total steps taken
                print(f'Steps Taken {steps_taken}')
                original_location = axis_origin + steps_taken
                print(f'axis_origin {axis_origin}')
                print(f"letters original_location {original_location}")
                if steps_taken >= max_steps:
                    raise ValueError("Infinite loop detected: check step size and wrapping logic.")
            return original_location
   
    original_location = axis_origin + int(
        (int(axis_location) - int(axis_origin)) / step
    )
    print(f"numbers original_location {original_location}")
    return str(original_location) if not letters else original_location

def validate_not_zero(value):
    """Prevent the usage of 0 as a value in the step form field or model attribute."""
    if value == 0:
        raise ValidationError(
            _("%(value)s is not a positive or negative Integer not equal to zero"),
            params={"value": value},
        )

validate_not_zero.message = "Must be a positive or negative Integer not equal to zero."
