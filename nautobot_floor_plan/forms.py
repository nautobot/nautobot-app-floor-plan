# TBD: Remove after releasing pylint-nautobot v0.3.0
# https://github.com/nautobot/pylint-nautobot/commit/48efc016fffa0b9df02f61bdaa9c4a0933351d29
# pylint: disable=nb-incorrect-base-class

"""Forms for nautobot_floor_plan."""
from django import forms

from nautobot.dcim.models import Location, Rack
from nautobot.apps.forms import (
    NautobotBulkEditForm,
    NautobotFilterForm,
    NautobotModelForm,
    TagsBulkEditFormMixin,
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
    TagFilterField,
    add_blank_choice,
)
from nautobot.apps.config import get_app_settings_or_config

from nautobot_floor_plan import models, choices, utils


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
            "x_axis_labels",
            "y_axis_labels",
            "tags",
        ]

    def __init__(self, *args, **kwargs):
        """Overwrite the constructor to set initial values for select widget."""
        super().__init__(*args, **kwargs)
        self.initial["x_axis_labels"] = get_app_settings_or_config("nautobot_floor_plan", "grid_x_axis_labels")
        self.initial["y_axis_labels"] = get_app_settings_or_config("nautobot_floor_plan", "grid_y_axis_labels")


class FloorPlanBulkEditForm(TagsBulkEditFormMixin, NautobotBulkEditForm):
    """FloorPlan bulk edit form."""

    pk = forms.ModelMultipleChoiceField(queryset=models.FloorPlan.objects.all(), widget=forms.MultipleHiddenInput)
    x_size = forms.IntegerField(min_value=1, required=False)
    y_size = forms.IntegerField(min_value=1, required=False)
    tile_width = forms.IntegerField(min_value=1, required=False)
    tile_depth = forms.IntegerField(min_value=1, required=False)
    x_axis_labels = forms.ChoiceField(choices=add_blank_choice(choices.AxisLabelsChoices), required=False)
    y_axis_labels = forms.ChoiceField(choices=add_blank_choice(choices.AxisLabelsChoices), required=False)

    class Meta:
        """Meta attributes."""

        fields = ["pk", "x_size", "y_size", "tile_width", "tile_depth", "tags"]


class FloorPlanFilterForm(NautobotFilterForm):
    """Filter form to filter searches."""

    model = models.FloorPlan
    field_order = ["q", "location", "x_size", "y_size"]

    q = forms.CharField(required=False, label="Search")
    location = DynamicModelMultipleChoiceField(queryset=Location.objects.all(), to_field_name="pk", required=False)
    tag = TagFilterField(model)


class FloorPlanTileForm(NautobotModelForm):
    """FloorPlanTile creation/edit form."""

    floor_plan = DynamicModelChoiceField(queryset=models.FloorPlan.objects.all())
    rack = DynamicModelChoiceField(
        queryset=Rack.objects.all(), required=False, query_params={"nautobot_floor_plan_floor_plan": "$floor_plan"}
    )
    x_origin = forms.CharField()
    y_origin = forms.CharField()

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
            "rack_orientation",
            "tags",
        ]

    def __init__(self, *args, **kwargs):
        """Overwrite the constructor to define grid numbering style."""
        super().__init__(*args, **kwargs)
        self.x_letters = False
        self.y_letters = False

        if fp_id := self.initial["floor_plan"] or self.data["floor_plan"]:
            fp_obj = self.fields["floor_plan"].queryset.get(id=fp_id)
            self.x_letters = fp_obj.x_axis_labels == choices.AxisLabelsChoices.LETTERS
            self.y_letters = fp_obj.y_axis_labels == choices.AxisLabelsChoices.LETTERS

    def clean_x_origin(self):
        """Convert x_origin to an integer."""
        if self.x_letters:
            return utils.column_letter_to_num(self.cleaned_data.get("x_origin"))
        return int(self.cleaned_data["x_origin"])

    def clean_y_origin(self):
        """Convert y_origin to an integer."""
        if self.y_letters:
            return utils.column_letter_to_num(self.cleaned_data.get("y_origin"))
        return int(self.cleaned_data["y_origin"])
