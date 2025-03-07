"""Extensions to Nautobot core models' filtering functionality."""

import django_filters
from nautobot.apps.filters import FilterExtension, RelatedMembershipBooleanFilter

from nautobot_floor_plan import models
from nautobot_floor_plan.models import FloorPlan


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
    }


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
            queryset=FloorPlan.objects.all(),
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
            queryset=FloorPlan.objects.all(),
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
            queryset=FloorPlan.objects.all(),
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
