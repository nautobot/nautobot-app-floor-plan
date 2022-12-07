"""Filtering for nautobot_floor_plan."""

from nautobot.utilities.filters import BaseFilterSet, NameSlugSearchFilterSet

from nautobot_floor_plan import models


class FloorPlanFilterSet(BaseFilterSet, NameSlugSearchFilterSet):
    """Filter for FloorPlan."""

    class Meta:
        """Meta attributes for filter."""

        model = models.FloorPlan

        # add any fields from the model that you would like to filter your searches by using those
        fields = ["id", "name", "slug", "description"]
