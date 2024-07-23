"""Helper for seed conversion to letters."""
from django import template

from nautobot_floor_plan import choices, utils
register = template.Library()

@register.filter()
def seed_conversion(object, axis):
    """Convert seed number to letter if necessary."""
    letters = getattr(object, f"{axis}_axis_labels")
    seed = getattr(object, f"{axis}_origin_seed")

    if letters == choices.AxisLabelsChoices.LETTERS:
        seed = utils.grid_number_to_letter(seed)
        
    return f"{seed}" 
