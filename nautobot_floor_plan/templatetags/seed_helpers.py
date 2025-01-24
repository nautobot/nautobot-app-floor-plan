"""Helper for seed conversion to letters."""

from django import template

from nautobot_floor_plan import choices
from nautobot_floor_plan.utils import general, label_converters

register = template.Library()


@register.filter()
def seed_conversion(floor_plan, axis):
    """Convert seed number to letter if necessary."""
    letters = getattr(floor_plan, f"{axis}_axis_labels")
    seed = getattr(floor_plan, f"{axis}_origin_seed")

    if letters == choices.AxisLabelsChoices.LETTERS:
        seed = general.grid_number_to_letter(seed)

    return f"{seed}"


@register.filter()
def render_axis_origin(record, axis):
    """
    Generalized function to render axis origin using PositionToLabelConverter or default conversion.

    Args:
        record: The record containing the axis origin.
        axis (str): The axis ('X' or 'Y').

    Returns:
        str: The converted axis label.
    """
    # Determine axis-specific attributes
    axis_seed = getattr(record.floor_plan, f"{axis.lower()}_origin_seed")
    axis_step = getattr(record.floor_plan, f"{axis.lower()}_axis_step")
    axis_labels_choice = getattr(record.floor_plan, f"{axis.lower()}_axis_labels")
    origin_value = getattr(record, f"{axis.lower()}_origin")

    # Check if custom labels exist for the axis
    if record.floor_plan.custom_labels.filter(axis=axis).exists():
        converter = label_converters.PositionToLabelConverter(origin_value, axis, record.floor_plan)
        return converter.convert()

    is_letters = axis_labels_choice == choices.AxisLabelsChoices.LETTERS
    origin_value_str = str(origin_value)  # Convert to string for checking

    if is_letters:
        converted_location = axis_seed + (int(origin_value_str) - axis_seed) * axis_step
        return general.letter_conversion(converted_location)  # Return the numeric value directly

    # Proceed with axis_init_label_conversion if it's not a digit
    return general.axis_init_label_conversion(axis_seed, origin_value_str, axis_step, is_letters)


@register.simple_tag
def render_axis_origin_tag(record, axis):
    """
    Template tag to render an axis origin label.

    This tag generates the label for a specified axis ('X' or 'Y') of a record's floor plan.
    It handles custom labels, letter-based conversions, and numeric conversions based on the
    floor plan's configuration.

    Args:
        record (object): The record containing the axis origin and associated floor plan.
        axis (str): The axis for which to render the label ('X' or 'Y').

    Returns:
        str: The converted axis label, either a custom label, letter-based label,
             or numeric label depending on the floor plan's settings.
    """
    return render_axis_origin(record, axis)


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
            display_label = converter.from_numeric(int(custom_label.start_label))

            # Preserve prefix for numalpha labels
            if custom_label.label_type == choices.CustomAxisLabelsChoices.NUMALPHA:
                prefix, _ = general.extract_prefix_and_letter(custom_label.start_label)
                _, letters = general.extract_prefix_and_letter(display_label)
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
