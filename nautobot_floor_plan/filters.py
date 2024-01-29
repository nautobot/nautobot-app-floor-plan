"""Filtering for nautobot_floor_plan."""

from nautobot.apps.filters import NautobotFilterSet, NameSearchFilterSet

from nautobot_floor_plan import models


class FloorPlanFilterSet(NautobotFilterSet, NameSearchFilterSet):  # pylint: disable=too-many-ancestors
    """Filter for FloorPlan."""

    q = SearchFilter(
        filter_predicates={
            "location__name": "icontains",
        },
    )
    location = NaturalKeyOrPKMultipleChoiceFilter(
        queryset=Location.objects.all(),
        label="Location (name or ID)",
    )

    class Meta:
        """Meta attributes for filter."""

        model = models.FloorPlan
        fields = ["x_size", "y_size", "tile_width", "tile_depth", "tags"]

        # add any fields from the model that you would like to filter your searches by using those
        fields = ["id", "name", "description"]
