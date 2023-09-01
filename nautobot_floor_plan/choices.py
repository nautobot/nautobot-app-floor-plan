"""ChoiceSet definitions for nautobot_floor_plan."""

from nautobot.core.choices import ChoiceSet


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
