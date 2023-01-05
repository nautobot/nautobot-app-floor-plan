"""Filtering for nautobot_floor_plan."""

from nautobot.extras.filters import NautobotFilterSet
from nautobot.utilities.filters import SearchFilter

from nautobot_floor_plan import models


class FloorPlanFilterSet(NautobotFilterSet):
    """Filter for FloorPlan."""

    q = SearchFilter(
        filter_predicates={
            "location__name": "icontains",
            "location__slug": "icontains",
        },
    )

    class Meta:
        """Meta attributes for filter."""

        model = models.FloorPlan

        # add any fields from the model that you would like to filter your searches by using those
        fields = ["location", "x_size", "y_size"]
