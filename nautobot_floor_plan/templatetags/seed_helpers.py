"""Helper for seed conversion to letters."""

from django import template

from nautobot_floor_plan import choices, label_converters, utils

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


@register.filter()
def count_children_floor_plans(location):
    """Returns count of Children with FloorPlans for a given location."""
    count = location.children.filter(floor_plan__isnull=False).count()
    return count


@register.filter()
def get_fieldset_field(form, field_name):
    """Retrieve a field from the form using a dynamic field name."""
    try:
        return form[field_name]
    except KeyError:
        return None


@register.filter
def render_origin_seed(obj, axis):
    """Render custom seed info for the specified axis if it exists, otherwise display the default seed."""
    custom_label = obj.custom_labels.filter(axis=axis.upper()).first()
    if custom_label:
        try:
            converter = label_converters.LabelConverterFactory.get_converter(custom_label.label_type)
            # Convert and display the custom label start
            numeric_value = converter.to_numeric(custom_label.start_label)
            display_label = converter.from_numeric(numeric_value)

            # Preserve prefix for numalpha labels
            if custom_label.label_type == choices.CustomAxisLabelsChoices.NUMALPHA:
                prefix, _ = utils.extract_prefix_and_letter(custom_label.start_label)
                _, letters = utils.extract_prefix_and_letter(display_label)
                return f"{prefix}{letters}"
            return display_label
        except ValueError:
            return custom_label.start_label
        # Fall back to default seed
    return seed_conversion(obj, axis.lower())


@register.filter
def render_axis_label(obj, axis):
    """Render custom label for the specified axis if it exists, otherwise display the default label."""
    custom_label = obj.custom_labels.filter(axis=axis.upper()).first()
    if custom_label:
        return custom_label.label_type
    return getattr(obj, f"{axis.lower()}_axis_labels")


@register.filter
def render_axis_step(obj, axis):
    """Render custom step for the specified axis if it exists, otherwise display the default step."""
    custom_label = obj.custom_labels.filter(axis=axis.upper()).first()
    if custom_label:
        return custom_label.step
    return getattr(obj, f"{axis.lower()}_axis_step")
