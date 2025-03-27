"""Extensions to Nautobot core models' filtering functionality."""

import logging

import django_filters
from nautobot.apps.filters import FilterExtension, RelatedMembershipBooleanFilter

from nautobot_floor_plan import models
from nautobot_floor_plan.utils.label_converters import LabelToPositionConverter, PositionToLabelConverter

logger = logging.getLogger(__name__)


class FloorPlanCoordinateFilter(django_filters.CharFilter):
    """Custom filter that converts between human-readable labels and stored coordinates."""

    def __init__(self, *, axis, **kwargs):
        """Overwrite the constructor to set initial values."""
        super().__init__(**kwargs)
        self.axis = axis

    def filter(self, qs, value):
        """Convert label to position and filter the given queryset based on the position."""
        floor_plan_id = None
        if not value:
            return qs

        try:
            if hasattr(self, "parent") and self.parent and hasattr(self.parent, "data"):
                floor_plan_id = self.parent.data.get("nautobot_floor_plan_floor_plan")
            if not floor_plan_id:
                return qs

            floor_plan = models.FloorPlan.objects.get(pk=floor_plan_id)

            # Check if custom labels are being used for this axis
            if floor_plan.custom_labels.filter(axis=self.axis).exists():
                # Use LabelToPositionConverter for custom labels
                converter = LabelToPositionConverter(value, self.axis, floor_plan)
                position, _ = converter.convert()
            else:
                # For default labels, use the value directly
                position = value

            return super().filter(qs, position)

        except models.FloorPlan.DoesNotExist as e:
            logger.error("Floor plan not found: %s", str(e))
        except ValueError as e:
            logger.error("Value error: %s", str(e))
        return qs

    def display_value(self, value):
        """Convert stored numeric value to label for display."""
        floor_plan_id = None
        if value is None or value == "":
            return value

        try:
            if hasattr(self, "parent") and self.parent and hasattr(self.parent, "data"):
                floor_plan_id = self.parent.data.get("nautobot_floor_plan_floor_plan")
            if floor_plan_id:
                floor_plan = models.FloorPlan.objects.get(pk=floor_plan_id)

                # Check if custom labels are being used for this axis
                if floor_plan.custom_labels.filter(axis=self.axis).exists():
                    # Convert value to int and use PositionToLabelConverter
                    try:
                        numeric_value = int(value)
                        converter = PositionToLabelConverter(numeric_value, self.axis, floor_plan)
                        return converter.convert() or value
                    except (ValueError, TypeError):
                        # Handle case where value can't be converted to int
                        logger.warning("Could not convert value '%s' to int for label conversion", value)
                        return value
                # For default labels, use the value directly
                return value

        except models.FloorPlan.DoesNotExist as e:
            logger.error("Floor plan not found: %s", str(e))
        except ValueError as e:
            logger.error("Value error: %s", str(e))
        return value


class RackFilterExtension(FilterExtension):
    """Add a filter to the RackFilterSet in Nautobot core."""

    model = "dcim.rack"

    filterset_fields = {
        "nautobot_floor_plan_floor_plan": django_filters.ModelChoiceFilter(
            queryset=models.FloorPlan.objects.all(),
            field_name="location__floor_plan",
            label="Floor plan",
        ),
        "nautobot_floor_plan_has_floor_plan_tile": RelatedMembershipBooleanFilter(
            field_name="floor_plan_tile",
            label="Floor Plan Tile",
        ),
        "nautobot_floor_plan_tile_x_origin": FloorPlanCoordinateFilter(
            field_name="floor_plan_tile__x_origin",
            label="Floor Plan Tile X Origin",
            axis="X",
        ),
        "nautobot_floor_plan_tile_y_origin": FloorPlanCoordinateFilter(
            field_name="floor_plan_tile__y_origin",
            label="Floor Plan Tile Y Origin",
            axis="Y",
        ),
    }

    def __init__(self, *args, **kwargs):
        """Overwrite the constructor to set initial values."""
        super().__init__(*args, **kwargs)
        # Explicitly set 'parent' for all filters in filterset_fields
        for _, filter_field in self.filterset_fields.items():
            filter_field.parent = self


class RackGroupFilterExtension(FilterExtension):
    """Add a filter to the RackGroupFilterSet in Nautobot core."""

    model = "dcim.rackgroup"

    filterset_fields = {
        "nautobot_floor_plan_floor_plan": django_filters.ModelChoiceFilter(
            queryset=models.FloorPlan.objects.all(),
            field_name="location__floor_plan",
            label="Floor plan",
        ),
    }


class PowerPanelFilterExtension(FilterExtension):
    """Add a filter to the PowerPanelFilterSet in Nautobot core."""

    model = "dcim.powerpanel"

    filterset_fields = {
        "nautobot_floor_plan_floor_plan": django_filters.ModelChoiceFilter(
            queryset=models.FloorPlan.objects.all(),
            field_name="location__floor_plan",
            label="Floor plan",
        ),
        "nautobot_floor_plan_has_floor_plan_tile": RelatedMembershipBooleanFilter(
            field_name="floor_plan_tile",
            label="Floor Plan Tile",
        ),
    }


class PowerFeedFilterExtension(FilterExtension):
    """Add a filter to the PowerFeedFilterSet in Nautobot core."""

    model = "dcim.powerfeed"

    filterset_fields = {
        "nautobot_floor_plan_floor_plan": django_filters.ModelChoiceFilter(
            queryset=models.FloorPlan.objects.all(),
            field_name="power_panel__location__floor_plan",
            label="Floor plan",
        ),
        "nautobot_floor_plan_has_floor_plan_tile": RelatedMembershipBooleanFilter(
            field_name="floor_plan_tile",
            label="Floor Plan Tile",
        ),
    }


class DeviceFilterExtension(FilterExtension):
    """Add a filter to the DeviceFilterSet in Nautobot core."""

    model = "dcim.device"

    filterset_fields = {
        "nautobot_floor_plan_floor_plan": django_filters.ModelChoiceFilter(
            queryset=models.FloorPlan.objects.all(),
            field_name="location__floor_plan",
            label="Floor plan",
        ),
        "nautobot_floor_plan_has_floor_plan_tile": RelatedMembershipBooleanFilter(
            field_name="floor_plan_tile",
            label="Floor Plan Tile",
        ),
    }


filter_extensions = [
    RackFilterExtension,
    RackGroupFilterExtension,
    PowerPanelFilterExtension,
    PowerFeedFilterExtension,
    DeviceFilterExtension,
]
