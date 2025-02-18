"""Filtering for nautobot_floor_plan."""

from __future__ import annotations

import django_filters
from nautobot.apps.filters import NaturalKeyOrPKMultipleChoiceFilter, NautobotFilterSet, SearchFilter
from nautobot.dcim.models import Location, Rack, RackGroup

from nautobot_floor_plan import models


class FloorPlanFilterSet(NautobotFilterSet):  # pylint: disable=too-many-ancestors
    """Filter for FloorPlan."""

    q: SearchFilter = SearchFilter(
        filter_predicates={
            "location__name": "icontains",
        },
    )
    location: NaturalKeyOrPKMultipleChoiceFilter = NaturalKeyOrPKMultipleChoiceFilter(
        queryset=Location.objects.all(),
        label="Location (name or ID)",
    )

    parent_location: NaturalKeyOrPKMultipleChoiceFilter = NaturalKeyOrPKMultipleChoiceFilter(
        queryset=Location.objects.all(),
        label="Parent Location",
        field_name="location__parent",
        to_field_name="pk",
    )

    class Meta:
        """Meta attributes for filter."""

        model = models.FloorPlan
        fields: list[str] = ["x_size", "y_size", "tile_width", "tile_depth", "tags"]  # pylint: disable=nb-use-fields-all


class FloorPlanTileFilterSet(NautobotFilterSet):
    """Filter for FloorPlanTile."""

    q: SearchFilter = SearchFilter(
        filter_predicates={
            "floor_plan__location__name": "icontains",
            "rack__name": "icontains",
            "rack_group__name": "icontains",
        },
    )
    floor_plan: django_filters.ModelMultipleChoiceFilter = django_filters.ModelMultipleChoiceFilter(
        queryset=models.FloorPlan.objects.all()
    )
    location: NaturalKeyOrPKMultipleChoiceFilter = NaturalKeyOrPKMultipleChoiceFilter(
        field_name="floor_plan__location",
        queryset=Location.objects.all(),
        label="Location (name or ID)",
    )
    rack: NaturalKeyOrPKMultipleChoiceFilter = NaturalKeyOrPKMultipleChoiceFilter(
        queryset=Rack.objects.all(),
        to_field_name="name",
        label="Rack (name or ID)",
    )

    rack_group: NaturalKeyOrPKMultipleChoiceFilter = NaturalKeyOrPKMultipleChoiceFilter(
        queryset=RackGroup.objects.all(),
        to_field_name="name",
        label="RackGroup (name or ID)",
    )

    class Meta:
        """Meta attributes."""

        model = models.FloorPlanTile
        fields: list[str] = ["x_origin", "y_origin", "tags"]  # pylint: disable=nb-use-fields-all
