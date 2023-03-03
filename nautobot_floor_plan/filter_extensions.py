"""Extensions to Nautobot core models' filtering functionality."""
import django_filters

from nautobot.extras.plugins import FilterExtension

from nautobot_floor_plan import models


class RackFilterExtension(FilterExtension):
    """Add a filter to the RackFilterSet in Nautobot core."""

    model = "dcim.rack"

    filterset_fields = {
        "nautobot_floor_plan_floor_plan": django_filters.ModelChoiceFilter(
            queryset=models.FloorPlan.objects.all(),
            field_name="location__floor_plan",
            label="Floor plan",
        ),
    }


filter_extensions = [RackFilterExtension]
