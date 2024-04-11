"""Utilities module."""


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
