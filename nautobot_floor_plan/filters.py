"""Filtering for nautobot_floor_plan."""

import django_filters

from nautobot.dcim.models import Location, Rack
from nautobot.extras.filters import NautobotFilterSet
from nautobot.apps.filters import NaturalKeyOrPKMultipleChoiceFilter, SearchFilter
from nautobot.core.filters import TagFilter

from nautobot_floor_plan import models


class FloorPlanFilterSet(NautobotFilterSet):
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
    tag = TagFilter()

    class Meta:
        """Meta attributes for filter."""

        model = models.FloorPlan
        fields = ["x_size", "y_size", "tile_width", "tile_depth"]


class FloorPlanTileFilterSet(NautobotFilterSet):
    """Filter for FloorPlanTile."""

    q = SearchFilter(
        filter_predicates={
            "floor_plan__location__name": "icontains",
            "rack__name": "icontains",
        },
    )
    floor_plan = django_filters.ModelMultipleChoiceFilter(queryset=models.FloorPlan.objects.all())
    location = NaturalKeyOrPKMultipleChoiceFilter(
        field_name="floor_plan__location",
        queryset=Location.objects.all(),
        label="Location (name or ID)",
    )
    rack = NaturalKeyOrPKMultipleChoiceFilter(
        queryset=Rack.objects.all(),
        to_field_name="name",
        label="Rack (name or ID)",
    )
    tag = TagFilter()

    class Meta:
        """Meta attributes."""

        model = models.FloorPlanTile
        fields = ["x_origin", "y_origin"]
