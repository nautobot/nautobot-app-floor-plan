"""ChoiceSet definitions for nautobot_floor_plan."""

from nautobot.apps.choices import ChoiceSet


class RackOrientationChoices(ChoiceSet):
    """Choices for the orientation of a Rack relative to its associated FloorPlan."""

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


class AxisLabelsChoices(ChoiceSet):
    """Choices for grid numbering style."""

    NUMBERS = "numbers"
    LETTERS = "letters"

    CHOICES = (
        (NUMBERS, "Numbers"),
        (LETTERS, "Letters"),
    )


class AllocationTypeChoices(ChoiceSet):
    """Choices for tile allocation type."""

    RACK = "rack"
    RACKGROUP = "rackgroup"

    CHOICES = (
        (RACK, "rack"),
        (RACKGROUP, "rackgroup"),
    )
