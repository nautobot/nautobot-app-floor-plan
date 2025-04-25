"""Filtering for nautobot_floor_plan."""

import django_filters
from nautobot.apps.filters import NaturalKeyOrPKMultipleChoiceFilter, NautobotFilterSet, SearchFilter
from nautobot.dcim.models import Device, Location, PowerFeed, PowerPanel, Rack, RackGroup

from nautobot_floor_plan import models


class FloorPlanFilterSet(NameSearchFilterSet, NautobotFilterSet):  # pylint: disable=too-many-ancestors
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

    parent_location = NaturalKeyOrPKMultipleChoiceFilter(
        queryset=Location.objects.all(),
        label="Parent Location",
        field_name="location__parent",
        to_field_name="pk",
    )

    class Meta:
        """Meta attributes for filter."""

        model = models.FloorPlan
        fields = ["x_size", "y_size", "tile_width", "tile_depth", "tags"]  # pylint: disable=nb-use-fields-all

        # add any fields from the model that you would like to filter your searches by using those
        fields = "__all__"
