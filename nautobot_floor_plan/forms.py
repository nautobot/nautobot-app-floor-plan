# TBD: Remove after releasing pylint-nautobot v0.3.0
# https://github.com/nautobot/pylint-nautobot/commit/48efc016fffa0b9df02f61bdaa9c4a0933351d29
# pylint: disable=nb-incorrect-base-class

"""Forms for nautobot_floor_plan."""

import json
import logging

from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.forms import formset_factory
from nautobot.apps.config import get_app_settings_or_config
from nautobot.apps.forms import (
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
    NautobotBulkEditForm,
    NautobotFilterForm,
    NautobotModelForm,
    TagFilterField,
    TagsBulkEditFormMixin,
    add_blank_choice,
)
from nautobot.dcim.models import Device, Location, PowerFeed, PowerPanel, Rack, RackGroup

from nautobot_floor_plan import choices, models
from nautobot_floor_plan.utils import general
from nautobot_floor_plan.utils.custom_validators import RangeValidator, ValidateNotZero
from nautobot_floor_plan.utils.label_converters import LabelToPositionConverter, PositionToLabelConverter

logger = logging.getLogger(__name__)


class FloorPlanForm(NautobotModelForm):
    """FloorPlan creation/edit form with support for custom axis label ranges."""

    location = DynamicModelChoiceField(queryset=Location.objects.all())

    # X Axis Fields
    x_origin_seed = forms.CharField(
        label="X Axis Seed",
        help_text="The first value to begin X Axis at.",
        required=True,
    )
    x_axis_step = forms.IntegerField(
        label="X Axis Step",
        help_text="A positive or negative integer, excluding zero",
        validators=[ValidateNotZero(0)],
        required=True,
    )
    # Y Axis Fields
    y_origin_seed = forms.CharField(
        label="Y Axis Seed",
        help_text="The first value to begin Y Axis at.",
        required=True,
    )
    y_axis_step = forms.IntegerField(
        label="Y Axis Step",
        help_text="A positive or negative integer, excluding zero",
        validators=[ValidateNotZero(0)],
        required=True,
    )

    is_tile_movable = forms.BooleanField(
        required=False,
        label="Movable Tiles",
        help_text="If true tiles can be edited and moved once placed on the Floorplan.",
    )

    fieldsets = (
        ("Floor Plan", ("location", "x_size", "y_size", "tile_width", "tile_depth", "is_tile_movable")),
        (
            "X Axis Settings",
            {
                "tabs": (("Default Labels", ("x_axis_labels", "x_origin_seed", "x_axis_step")),),
            },
        ),
        (
            "Y Axis Settings",
            {
                "tabs": (("Default Labels", ("y_axis_labels", "y_origin_seed", "y_axis_step")),),
            },
        ),
    )

    class Meta:
        """Meta attributes."""

        model = models.FloorPlan
        fields = "__all__"


class FloorPlanBulkEditForm(TagsBulkEditFormMixin, NautobotBulkEditForm):  # pylint: disable=too-many-ancestors
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
    rack_group = DynamicModelChoiceField(
        queryset=RackGroup.objects.all(),
        required=False,
        label="Search",
        help_text="Search within Name.",
    )

    x_origin = forms.CharField()
    y_origin = forms.CharField()

    # Object selection fields (only one will be used per tab)
    device = DynamicModelChoiceField(
        queryset=Device.objects.all(),
        required=False,
        query_params={
            "nautobot_floor_plan_floor_plan": "$floor_plan",
            "nautobot_floor_plan_has_floor_plan_tile": False,
        },
    )
    rack = DynamicModelChoiceField(
        queryset=Rack.objects.all(),
        required=False,
        query_params={
            "nautobot_floor_plan_floor_plan": "$floor_plan",
            "nautobot_floor_plan_has_floor_plan_tile": False,
            "rack_group": "$rack_group",
        },
    )
    power_panel = DynamicModelChoiceField(
        queryset=PowerPanel.objects.all(),
        required=False,
        query_params={
            "nautobot_floor_plan_floor_plan": "$floor_plan",
            "nautobot_floor_plan_has_floor_plan_tile": False,
            "rack_group": "$rack_group",
        },
    )
    power_feed = DynamicModelChoiceField(
        queryset=PowerFeed.objects.all(),
        required=False,
        query_params={
            "nautobot_floor_plan_floor_plan": "$floor_plan",
            "nautobot_floor_plan_has_floor_plan_tile": False,
            "power_panel__location": "$floor_plan__location",
        },
    )

    field_order = [
        "floor_plan",
        "x_origin",
        "y_origin",
        "x_size",
        "y_size",
        "status",
        "rack_group",
        "object_orientation",
    ]

    class Meta:
        """Meta attributes."""

        model = models.FloorPlanTile
        fields = "__all__"
        exclude = ["allocation_type", "on_group_tile"]  # pylint: disable=modelform-uses-exclude

    fieldsets = (
        (
            "Floor Plan Tile",
            (
                "floor_plan",
                "x_origin",
                "y_origin",
                "x_size",
                "y_size",
                "status",
                "rack_group",
            ),
        ),
    )

    def __init__(self, *args, **kwargs):
        """Initialize the form, handling both the object-type field setup and custom label conversions."""
        super().__init__(*args, **kwargs)
        self._setup_custom_label_conversions()

    def _setup_custom_label_conversions(self):
        """Setup custom label conversions and handle axis letter configurations."""
        self.axis_letters = {"x": False, "y": False}

        fp_id = self.initial.get("floor_plan") or self.data.get("floor_plan")
        if not fp_id:
            return

        try:
            fp_obj = self.fields["floor_plan"].queryset.get(id=fp_id)
        except ObjectDoesNotExist:
            logger.error("Floor plan with ID %s does not exist", fp_id)
            self.add_error("floor_plan", f"Floor plan with ID {fp_id} does not exist")
            return

        self._configure_axis_settings(fp_obj)
        self._handle_origin_values(fp_obj)

    def _configure_axis_settings(self, fp_obj):
        """Configure axis settings and handle immovable tiles."""
        self.axis_letters["x"] = fp_obj.x_axis_labels == choices.AxisLabelsChoices.LETTERS
        self.axis_letters["y"] = fp_obj.y_axis_labels == choices.AxisLabelsChoices.LETTERS

        if not fp_obj.is_tile_movable:
            self.fields["x_origin"].disabled = True
            self.fields["y_origin"].disabled = True

    def _handle_origin_values(self, fp_obj):
        """Handle origin values for both axes."""
        if not (self.instance.x_origin or self.instance.y_origin):
            return

        for axis in ["X", "Y"]:
            self._process_axis_origin(fp_obj, axis)

    def _process_axis_origin(self, fp_obj, axis):
        """Process origin value for a specific axis."""
        lower_axis = axis.lower()
        origin_value = getattr(self.instance, f"{lower_axis}_origin")

        if fp_obj.custom_labels.filter(axis=axis).exists():
            converter = PositionToLabelConverter(origin_value, axis, fp_obj)
            if label := converter.convert():
                self.initial[f"{lower_axis}_origin"] = label
        else:
            value = (
                general.grid_number_to_letter(origin_value)
                if self.axis_letters[lower_axis]
                else self.initial.get(f"{lower_axis}_origin")
            )
            self.initial[f"{lower_axis}_origin"] = general.axis_init_label_conversion(
                getattr(fp_obj, f"{lower_axis}_origin_seed"),
                value,
                getattr(fp_obj, f"{lower_axis}_axis_step"),
                self.axis_letters[lower_axis],
            )

    def _convert_label_to_position(self, value, axis, fp_obj):
        """Wrapper for the LabelToPositionConverter."""
        try:
            converter = LabelToPositionConverter(value, axis, fp_obj)
            absolute_position, _ = converter.convert()
            return absolute_position, None  # Return None for the error when successful
        except ValueError as e:
            return None, forms.ValidationError(str(e))

    def _clean_custom_origin(self, field_name, axis):
        """Clean method for custom label origins."""
        fp_obj = self.cleaned_data.get("floor_plan")
        value = self.cleaned_data.get(field_name)

        try:
            position, error = self._convert_label_to_position(value, axis, fp_obj)
            if error:
                raise error

            # Validate against floor plan size
            max_size = fp_obj.x_size if axis == "X" else fp_obj.y_size
            if position > max_size:
                raise forms.ValidationError(
                    f"Position {value} (absolute: {position}) exceeds floor plan {axis} size of {max_size}"
                )

            return position

        except ValueError as e:
            raise forms.ValidationError(f"Invalid {axis}-axis value: {str(e)}")

    def clean_x_origin(self):
        """Clean method for x_origin field."""
        fp_obj = self.cleaned_data.get("floor_plan")
        if fp_obj.custom_labels.filter(axis="X").exists():
            return self._clean_custom_origin("x_origin", "X")
        return self._clean_origin("x_origin", "X")

    def clean_y_origin(self):
        """Clean method for y_origin field."""
        fp_obj = self.cleaned_data.get("floor_plan")
        if fp_obj.custom_labels.filter(axis="Y").exists():
            return self._clean_custom_origin("y_origin", "Y")
        return self._clean_origin("y_origin", "Y")

    def letter_validator(self, field, value, axis):
        """Validate that origin uses combination of letters."""
        if not str(value).isupper():
            self.add_error(field, f"{axis} origin should use capital letters.")
            return False
        return True

    def number_validator(self, field, value, axis):
        """Validate that origin uses combination of positive or negative numbers."""
        if not str(value).replace("-", "").isnumeric():
            self.add_error(field, f"{axis} origin should use numbers.")
            return False
        return True

    def _clean_origin(self, field_name, axis):
        """Common clean method for origin fields."""
        # Retrieve floor plan object if available
        fp_id = self.initial.get("floor_plan") or self.data.get("floor_plan")
        if not fp_id:
            return 0

        try:
            fp_obj = self.fields["floor_plan"].queryset.get(id=fp_id)
        except ObjectDoesNotExist:
            logger.error("Floor plan with ID %s does not exist", fp_id)
            self.add_error("floor_plan", f"Floor plan with ID {fp_id} does not exist")
            return 0

        value = self.cleaned_data.get(field_name)

        # Determine if letters are being used for x or y axis labels
        using_letters = (field_name == "x_origin" and self.axis_letters["x"]) or (
            field_name == "y_origin" and self.axis_letters["y"]
        )

        # Perform validation based on the type (letters or numbers)
        validator = self.letter_validator if using_letters else self.number_validator
        if not validator(field_name, value, axis):
            return 0  # Required to pass model clean() method

        # Select the appropriate axis seed and step
        if field_name == "x_origin":
            origin_seed, step, use_letters = fp_obj.x_origin_seed, fp_obj.x_axis_step, self.axis_letters["x"]
        else:
            origin_seed, step, use_letters = fp_obj.y_origin_seed, fp_obj.y_axis_step, self.axis_letters["y"]

        # Convert and return the label position using the specified conversion function
        cleaned_value = general.axis_clean_label_conversion(origin_seed, value, step, use_letters)
        return int(cleaned_value) if not using_letters else cleaned_value


class CustomLabelRangeForm(forms.Form):
    """Form for handling individual custom label ranges."""

    start = forms.CharField(required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    end = forms.CharField(required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    step = forms.IntegerField(
        required=True,
        initial=1,
        validators=[ValidateNotZero(0)],
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    label_type = forms.ChoiceField(
        choices=choices.CustomAxisLabelsChoices.CHOICES,
        required=True,
        widget=forms.Select(attrs={"class": "form-control", step: 1}),
    )
    increment_letter = forms.BooleanField(
        required=False, initial=True, widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )


CustomLabelRangeFormSetWithExtra = formset_factory(
    CustomLabelRangeForm,
    extra=1,
    can_delete=True,
    validate_min=False,
)

CustomLabelRangeFormSetNoExtra = formset_factory(
    CustomLabelRangeForm,
    extra=0,
    can_delete=True,
    validate_min=False,
)
