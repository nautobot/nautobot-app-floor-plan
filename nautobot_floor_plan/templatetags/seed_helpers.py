"""Helper for seed conversion to letters."""

from django import template

from nautobot_floor_plan import choices, utils

register = template.Library()


@register.filter()
def seed_conversion(floor_plan, axis):
    """Convert seed number to letter if necessary."""
    letters = getattr(floor_plan, f"{axis}_axis_labels")
    seed = getattr(floor_plan, f"{axis}_origin_seed")

    if letters == choices.AxisLabelsChoices.LETTERS:
        seed = utils.grid_number_to_letter(seed)

    return f"{seed}"

@register.filter()
def grid_location_conversion(floor_plan_tile, axis):
    """Convert FloorPlanTile coordinate to letter if necessary."""
    letters = getattr(floor_plan_tile.floor_plan, f"{axis}_axis_labels")
    grid = getattr(floor_plan_tile, f"{axis}_origin")

    if letters == choices.AxisLabelsChoices.LETTERS:
        grid = utils.grid_number_to_letter(grid)

    return f"{grid}"
