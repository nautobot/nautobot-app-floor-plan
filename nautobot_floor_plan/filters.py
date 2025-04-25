"""Filtering for nautobot_floor_plan."""

from nautobot.apps.filters import NameSearchFilterSet, NautobotFilterSet

from nautobot_floor_plan import models


class FloorPlanFilterSet(NameSearchFilterSet, NautobotFilterSet):  # pylint: disable=too-many-ancestors
    """Filter for FloorPlan."""

    class Meta:
        """Meta attributes for filter."""

        model = models.FloorPlan

        # add any fields from the model that you would like to filter your searches by using those
        fields = "__all__"
