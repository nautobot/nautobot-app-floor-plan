"""Filtering for nautobot_floor_plan."""

from nautobot.apps.filters import NameSearchFilterSet, NautobotFilterSet

from nautobot_floor_plan import models


class FloorPlanFilterSet(
    NautobotFilterSet, NameSearchFilterSet
):  # pylint: disable=too-many-ancestors
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


class FloorPlanTileFilterSet(NautobotFilterSet):
    """Filter for FloorPlanTile."""

    q = SearchFilter(
        filter_predicates={
            "floor_plan__location__name": "icontains",
            "rack__name": "icontains",
            "rack_group__name": "icontains",
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

    rack_group = NaturalKeyOrPKMultipleChoiceFilter(
        queryset=RackGroup.objects.all(),
        to_field_name="name",
        label="RackGroup (name or ID)",
    )

    class Meta:
        """Meta attributes."""

        model = models.FloorPlanTile
        fields = ["x_origin", "y_origin", "tags"]
