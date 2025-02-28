"""Create fixtures for tests."""

from django.contrib.contenttypes.models import ContentType
from nautobot.dcim.models import (
    Device,
    DeviceType,
    Location,
    LocationType,
    Manufacturer,
    PowerFeed,
    PowerPanel,
    Rack,
    RackGroup,
)
from nautobot.extras.models import Role, Status

from nautobot_floor_plan import choices
from nautobot_floor_plan.models import FloorPlan, FloorPlanTile


def create_prerequisites(floor_count=4):
    """Fixture to create the various prerequisite objects needed before a FloorPlan can be created."""
    location_type_site = LocationType.objects.create(name="Site")
    parent_location_type = LocationType.objects.create(name="Building")
    location_type = LocationType.objects.create(name="Floor", parent=parent_location_type)
    location_type.content_types.add(ContentType.objects.get_for_model(Device))
    location_type.content_types.add(ContentType.objects.get_for_model(PowerFeed))
    location_type.content_types.add(ContentType.objects.get_for_model(PowerPanel))
    location_type.content_types.add(ContentType.objects.get_for_model(Rack))
    location_type.content_types.add(ContentType.objects.get_for_model(RackGroup))

    active_status = Status.objects.get(name="Active")
    active_status.content_types.add(ContentType.objects.get_for_model(FloorPlanTile))
    active_status.content_types.add(ContentType.objects.get_for_model(Device))
    active_status.content_types.add(ContentType.objects.get_for_model(PowerFeed))
    active_status.content_types.add(ContentType.objects.get_for_model(Rack))

    # Create manufacturer
    manufacturer = Manufacturer.objects.create(name="Test Manufacturer")

    # Create device role
    device_role = Role.objects.create(name="Test Role", color="ff0000")
    device_role.content_types.add(ContentType.objects.get_for_model(Device))

    # Create device type
    device_type = DeviceType.objects.create(
        manufacturer=manufacturer,
        model="Test Device Type",
    )

    location = Location.objects.create(name="Location 1", status=active_status, location_type=location_type_site)
    building = Location.objects.create(
        parent=location, location_type=parent_location_type, name="Building 1", status=active_status
    )
    floors = []
    for i in range(1, floor_count + 1):
        floors.append(
            Location.objects.create(
                location_type=location_type, parent=building, status=active_status, name=f"Floor {i}"
            )
        )

    return {
        "status": active_status,
        "floors": floors,
        "location": location,
        "building": building,
        "manufacturer": manufacturer,
        "device_role": device_role,
        "device_type": device_type,
    }


def create_floor_plans(locations):
    """Fixture to create necessary number of FloorPlan for tests."""
    size = 1
    floor_plans = []

    for location in locations:
        floor_plan = FloorPlan(location=location, x_size=size, y_size=size)
        floor_plan.validated_save()
        floor_plans.append(floor_plan)
        size += 1

    return floor_plans


def get_formset_prefix_data(prefix, total_forms="0", max_forms="1000"):
    """Generate Django formset management form data for a specific prefix.

    Args:
        prefix: The formset prefix (e.g., 'x_ranges' or 'y_ranges')
        total_forms: Number of forms in the formset (default: "0")
        max_forms: Maximum number of forms allowed (default: "1000")

    Returns:
        dict: Management form data with TOTAL_FORMS, INITIAL_FORMS, MIN_NUM_FORMS, and MAX_NUM_FORMS
    """
    return {
        f"{prefix}-TOTAL_FORMS": str(total_forms),
        f"{prefix}-INITIAL_FORMS": "0",
        f"{prefix}-MIN_NUM_FORMS": "0",
        f"{prefix}-MAX_NUM_FORMS": max_forms,
    }


def get_formset_management_data(x_total="0", y_total="0", max_forms="1000"):
    """Return combined formset management data for both x and y ranges.

    Creates the necessary Django formset management form data for both axis ranges.

    Args:
        x_total: Number of forms for x_ranges (default: "0")
        y_total: Number of forms for y_ranges (default: "0")
        max_forms: Maximum number of forms allowed (default: "1000")

    Returns:
        dict: Combined management form data for both x_ranges and y_ranges
    """
    return {
        **get_formset_prefix_data("x_ranges", x_total, max_forms),
        **get_formset_prefix_data("y_ranges", y_total, max_forms),
    }


def get_range_field_data(prefix, index=0, **field_values):
    """Generate form field data for a single range in a formset.

    Creates the field data for a single range form, with customizable field values.

    Args:
        prefix: The formset prefix (e.g., 'x_ranges' or 'y_ranges')
        index: The form index in the formset (default: 0)
        **field_values: Override values for any of the range fields

    Returns:
        dict: Field data with proper formset prefixing (e.g., 'x_ranges-0-start')
    """
    defaults = {
        "start": "",
        "end": "",
        "step": "1",
        "label_type": choices.CustomAxisLabelsChoices.NUMBERS,
        "increment_letter": False,
    }
    defaults.update(field_values)
    return {f"{prefix}-{index}-{key}": value for key, value in defaults.items()}


def get_default_formset_data(axis="x", index=0):
    """Return default range field data for a specific axis.

    A convenience wrapper around get_range_field_data for single-axis use.

    Args:
        axis: Which axis to generate data for ('x' or 'y') (default: "x")
        index: The form index in the formset (default: 0)

    Returns:
        dict: Default range field data for the specified axis
    """
    prefix = f"{axis}_ranges"
    return get_range_field_data(prefix, index)


def get_full_formset_data(axis="x", total_forms=1):
    """Return complete formset data including management form and default field data.

    Combines management form data and default field data for a complete formset.

    Args:
        axis: Which axis to generate data for ('x' or 'y') (default: "x")
        total_forms: Number of forms in the formset (default: 1)

    Returns:
        dict: Complete formset data ready for form submission
    """
    return {
        **get_formset_management_data(
            x_total=total_forms if axis == "x" else "0", y_total=total_forms if axis == "y" else "0"
        ),
        **get_default_formset_data(axis),
    }


def get_default_floor_plan_data(floors=None, **overrides):
    """Return default floor plan data with optional overrides.

    This function provides a consistent base configuration for floor plan tests.
    It's used to avoid duplicate code across test files and ensure consistent test data.

    Args:
        floors: List of floor objects, uses first floor's PK for location if provided
        **overrides: Key-value pairs to override default settings (e.g., x_size, y_size)

    Example:
        base_data = get_default_floor_plan_data(
            floors,
            x_size=32,  # Override default size of 10
            y_size=32,
        )
    """
    defaults = {
        "location": floors[0].pk if floors else None,
        "x_size": 10,
        "y_size": 10,
        "tile_depth": 100,
        "tile_width": 100,
        "x_axis_labels": choices.AxisLabelsChoices.NUMBERS,
        "y_axis_labels": choices.AxisLabelsChoices.NUMBERS,
        "x_origin_seed": 1,
        "y_origin_seed": 1,
        "x_axis_step": 1,
        "y_axis_step": 1,
    }
    defaults.update(overrides)
    return defaults


def prepare_formset_data(ranges, base_data=None, floors=None):
    """Helper method to prepare form data with formset fields.

    Combines floor plan base data with formset management data and range configurations.
    Used primarily in range validation tests to test different label configurations.

    Args:
        ranges: List of range configurations to test
        base_data: Optional pre-configured base data, if None uses get_default_floor_plan_data
        floors: List of floor objects, passed to get_default_floor_plan_data if base_data is None

    Example:
        form_data = prepare_formset_data(
            ranges=[{"start": "1", "end": "10", "step": "1"}],
            base_data=custom_base_data,
            floors=test_floors
        )
    """
    base = base_data if base_data is not None else get_default_floor_plan_data(floors)
    form_data = {
        **base,
        **get_formset_management_data(x_total=len(ranges)),
    }

    # Add range data for each range configuration
    for i, range_data in enumerate(ranges):
        form_data.update(get_range_field_data("x_ranges", i, **range_data))

    return form_data
