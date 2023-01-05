"""Filtering for nautobot_floor_plan."""

from nautobot.extras.filters import NautobotFilterSet

from nautobot_floor_plan import models


class FloorPlanFilterSet(NautobotFilterSet):
    """Filter for FloorPlan."""

    class Meta:
        """Meta attributes for filter."""

        model = models.FloorPlan

        # add any fields from the model that you would like to filter your searches by using those
        fields = ["location", "x_size", "y_size"]
