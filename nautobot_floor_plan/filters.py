"""Filtering for nautobot_floor_plan."""

from nautobot.apps.filters import NautobotFilterSet, NameSearchFilterSet

from nautobot_floor_plan import models


class FloorPlanFilterSet(NautobotFilterSet, NameSearchFilterSet):  # pylint: disable=too-many-ancestors
    """Filter for FloorPlan."""

    class Meta:
        """Meta attributes for filter."""

        model = models.FloorPlan

        # add any fields from the model that you would like to filter your searches by using those
        fields = ["id", "name", "description"]
