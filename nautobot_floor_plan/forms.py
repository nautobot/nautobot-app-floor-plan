"""Forms for nautobot_floor_plan."""
from django import forms

from nautobot.dcim.models import Location, Rack
from nautobot.extras.forms import (
    CustomFieldModelCSVForm,
    NautobotBulkEditForm,
    NautobotFilterForm,
    NautobotModelForm,
    TagsBulkEditFormMixin,
)
from nautobot.utilities.forms import (
    CSVModelChoiceField,
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
    TagFilterField,
)

from nautobot_floor_plan import models


class FloorPlanForm(NautobotModelForm):
    """FloorPlan creation/edit form."""

    location = DynamicModelChoiceField(queryset=Location.objects.all())

    class Meta:
        """Meta attributes."""

        model = models.FloorPlan
        fields = [
            "location",
            "x_size",
            "y_size",
            "tile_width",
            "tile_depth",
            "tags",
        ]


class FloorPlanCSVForm(CustomFieldModelCSVForm):
    """FloorPlan CSV export form."""

    location = CSVModelChoiceField(queryset=Location.objects.all(), to_field_name="name")

    class Meta:
        """Meta attributes."""

        model = models.FloorPlan
        fields = models.FloorPlan.csv_headers


class FloorPlanBulkEditForm(TagsBulkEditFormMixin, NautobotBulkEditForm):
    """FloorPlan bulk edit form."""

    pk = forms.ModelMultipleChoiceField(queryset=models.FloorPlan.objects.all(), widget=forms.MultipleHiddenInput)
    x_size = forms.IntegerField(min_value=1, required=False)
    y_size = forms.IntegerField(min_value=1, required=False)
    tile_width = forms.IntegerField(min_value=1, required=False)
    tile_depth = forms.IntegerField(min_value=1, required=False)

    class Meta:
        """Meta attributes."""

        fields = ["pk", "x_size", "y_size", "tile_width", "tile_depth", "tags"]


class FloorPlanFilterForm(NautobotFilterForm):
    """Filter form to filter searches."""

    model = models.FloorPlan
    field_order = ["q", "location", "x_size", "y_size"]

    q = forms.CharField(required=False, label="Search")
    location = DynamicModelMultipleChoiceField(queryset=Location.objects.all(), to_field_name="slug", required=False)
    tag = TagFilterField(model)


class FloorPlanTileForm(NautobotModelForm):
    """FloorPlanTile creation/edit form."""

    floor_plan = DynamicModelChoiceField(queryset=models.FloorPlan.objects.all())
    # TODO: query_params probably doesn't work as written here
    rack = DynamicModelChoiceField(
        queryset=Rack.objects.all(), required=False, query_params={"location": "$floor_plan.location"}
    )

    class Meta:
        """Meta attributes."""

        model = models.FloorPlanTile
        fields = [
            "floor_plan",
            "x_origin",
            "y_origin",
            "x_size",
            "y_size",
            "status",
            "rack",
            "tags",
        ]
