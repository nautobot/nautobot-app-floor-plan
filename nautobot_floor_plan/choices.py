"""ChoiceSet definitions for nautobot_floor_plan."""

from nautobot.apps.choices import ChoiceSet


class ObjectOrientationChoices(ChoiceSet):
    """Choices for the orientation of a FloorPlan-eligible Object relative to its associated FloorPlan."""

    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"

    CHOICES = (
        (UP, "up"),
        (DOWN, "down"),
        (LEFT, "left"),
        (RIGHT, "right"),
    )


class CustomAxisLabelsChoices(ChoiceSet):
    """Choices for custom axis label types."""

    ROMAN = "roman"
    GREEK = "greek"
    BINARY = "binary"
    HEX = "hex"
    NUMALPHA = "numalpha"
    LETTERS = "letters"
    ALPHANUMERIC = "alphanumeric"
    NUMBERS = "numbers"

    CHOICES = (
        (NUMBERS, "Numbers (e.g. 1, 2, 3)"),
        (LETTERS, "Letters (e.g., A, B, C)"),
        (NUMALPHA, "Numalpha (e.g., 02A)"),
        (ALPHANUMERIC, "Alphanumeric (e.g., A01, B02)"),
        (ROMAN, "Roman (e.g., I, II, III)"),
        (GREEK, "Greek (e.g., α, β, γ)"),
        (BINARY, "Binary (e.g., 1, 10, 11)"),
        (HEX, "Hexadecimal (e.g., 1, A, F)"),
    )


class AxisLabelsChoices(ChoiceSet):
    """Choices for axis labels."""

    NUMBERS = "numbers"
    LETTERS = "letters"

    CHOICES = (
        (NUMBERS, "Numbers"),
        (LETTERS, "Letters"),
    )


class AllocationTypeChoices(ChoiceSet):
    """Choices for tile allocation types."""

    OBJECT = "object"
    RACKGROUP = "rackgroup"

    CHOICES = (
        (OBJECT, "Object"),
        (RACKGROUP, "RackGroup"),
    )


class ObjectTypeChoices(ChoiceSet):
    """Choices for FloorPlanTile object types."""

    DEVICE = "device"
    POWER_PANEL = "power_panel"
    POWER_FEED = "power_feed"
    RACK = "rack"

    CHOICES = (
        ("", "---------"),
        (DEVICE, "Device"),
        (POWER_PANEL, "Power Panel"),
        (POWER_FEED, "Power Feed"),
        (RACK, "Rack"),
    )
