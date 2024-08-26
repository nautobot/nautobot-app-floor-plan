"""Extensions to Nautobot core models' filtering functionality."""

import django_filters
from nautobot.apps.filters import RelatedMembershipBooleanFilter
from nautobot.extras.plugins import PluginFilterExtension

from nautobot_floor_plan import models


class RackFilterExtension(PluginFilterExtension):
    """Add a filter to the RackFilterSet in Nautobot core."""

    model = "dcim.rack"

    filterset_fields = {
        "nautobot_floor_plan_floor_plan": django_filters.ModelChoiceFilter(
            queryset=models.FloorPlan.objects.all(),
            field_name="location__floor_plan",
            label="Floor plan",
        ),
    }

class UniqueRackFilterExtension(PluginFilterExtension):
    """Add a filter to ensure a Rack is only an option if it isn't installed."""

    model = "dcim.rack"

    filterset_fields = {
        "nautobot_floor_plan_has_floor_plan_tile": RelatedMembershipBooleanFilter(
            field_name="floor_plan_tile",
            label="Floor plan",
        ),
    }

class RackGroupFilterExtension(PluginFilterExtension):
    """Add a filter to the RackGroupFilterSet in Nautobot core."""

    model = "dcim.rackgroup"

    filterset_fields = {
        "nautobot_floor_plan_floor_plan": django_filters.ModelChoiceFilter(
            queryset=models.FloorPlan.objects.all(),
            field_name="location__floor_plan",
            label="Floor plan",
        ),
    }


filter_extensions = [RackFilterExtension, RackGroupFilterExtension, UniqueRackFilterExtension]
