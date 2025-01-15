# TBD: Remove after releasing pylint-nautobot v0.3.0
# https://github.com/nautobot/pylint-nautobot/commit/48efc016fffa0b9df02f61bdaa9c4a0933351d29
# pylint: disable=nb-incorrect-base-class

"""Forms for nautobot_floor_plan."""

from django import forms
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
from nautobot.dcim.models import Location, Rack, RackGroup

from nautobot_floor_plan import choices, models, utils


class FloorPlanForm(NautobotModelForm):
    """FloorPlan creation/edit form."""

    location = DynamicModelChoiceField(queryset=Location.objects.all())

    x_origin_seed = forms.CharField(
        label="X Axis Seed",
        help_text="The first value to begin X Axis at.",
        required=True,
    )
    y_origin_seed = forms.CharField(
        label="Y Axis Seed",
        help_text="The first value to begin Y Axis at.",
        required=True,
    )
    x_axis_step = forms.IntegerField(
        label="X Axis Step",
        help_text="A positive or negative integer, excluding zero",
        required=True,
    )
    y_axis_step = forms.IntegerField(
        label="Y Axis Step",
        help_text="A positive or negative integer, excluding zero",
        required=True,
    )

    field_order = [
        "location",
        "x_size",
        "y_size",
        "tile_width",
        "tile_depth",
        "x_axis_labels",
        "x_origin_seed",
        "x_axis_step",
        "y_axis_labels",
        "y_origin_seed",
        "y_axis_step",
    ]

    class Meta:
        """Meta attributes."""

        model = models.FloorPlan
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        """Overwrite the constructor to set initial values for select widget."""
        super().__init__(*args, **kwargs)

        if not self.instance.created:
            self.initial["x_axis_labels"] = get_app_settings_or_config("nautobot_floor_plan", "default_x_axis_labels")
            self.initial["y_axis_labels"] = get_app_settings_or_config("nautobot_floor_plan", "default_y_axis_labels")
            self.x_letters = self.initial["x_axis_labels"] == choices.AxisLabelsChoices.LETTERS
            self.y_letters = self.initial["y_axis_labels"] == choices.AxisLabelsChoices.LETTERS
            self.initial["x_origin_seed"] = "A" if self.x_letters else "1"
            self.initial["y_origin_seed"] = "A" if self.y_letters else "1"
        else:
            self.x_letters = self.instance.x_axis_labels == choices.AxisLabelsChoices.LETTERS
            self.y_letters = self.instance.y_axis_labels == choices.AxisLabelsChoices.LETTERS

        if self.x_letters and str(self.initial["y_origin_seed"]).isdigit():
            self.initial["x_origin_seed"] = utils.grid_number_to_letter(self.instance.x_origin_seed)
        if self.y_letters and str(self.initial["y_origin_seed"]).isdigit():
            self.initial["y_origin_seed"] = utils.grid_number_to_letter(self.instance.y_origin_seed)

    def _clean_origin_seed(self, field_name, axis):
        """Common clean method for origin_seed fields."""
        value = self.cleaned_data.get(field_name)
        if not value:
            return 1

        self.x_letters = self.cleaned_data.get("x_axis_labels") == choices.AxisLabelsChoices.LETTERS
        self.y_letters = self.cleaned_data.get("y_axis_labels") == choices.AxisLabelsChoices.LETTERS

        if self.x_letters and field_name == "x_origin_seed" or self.y_letters and field_name == "y_origin_seed":
            if not str(value).isupper():
                self.add_error(field_name, f"{axis} origin start should use capital letters.")
                return 0
            return utils.grid_letter_to_number(value)

        if not str(value).replace("-", "").isnumeric():
            self.add_error(field_name, f"{axis} origin start should use numbers.")
            return 0
        return int(value)

    def clean_x_origin_seed(self):
        """Validate input and convert y_origin to an integer."""
        return self._clean_origin_seed("x_origin_seed", "X")

    def clean_y_origin_seed(self):
        """Validate input and convert y_origin to an integer."""
        return self._clean_origin_seed("y_origin_seed", "Y")

    def clean(self):
        """Custom clean method to validate floor plan dimensions."""
        cleaned_data = super().clean()
        x_size = self.cleaned_data.get("x_size")
        y_size = self.cleaned_data.get("y_size")

        # Get the configured limits
        x_size_limit = get_app_settings_or_config("nautobot_floor_plan", "x_size_limit")
        y_size_limit = get_app_settings_or_config("nautobot_floor_plan", "y_size_limit")

        # Validate X size only if a limit is set
        if x_size_limit is not None and x_size is not None and x_size > x_size_limit:
            self.add_error("x_size", f"X size cannot exceed {x_size_limit}.")

        # Validate Y size only if a limit is set
        if y_size_limit is not None and y_size is not None and y_size > y_size_limit:
            self.add_error("y_size", f"Y size cannot exceed {y_size_limit}.")

        return cleaned_data


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
    rack = DynamicModelChoiceField(
        queryset=Rack.objects.all(),
        required=False,
        query_params={
            "nautobot_floor_plan_floor_plan": "$floor_plan",
            "nautobot_floor_plan_has_floor_plan_tile": False,
            "rack_group": "$rack_group",
        },
    )
    rack_group = DynamicModelChoiceField(
        queryset=RackGroup.objects.all(),
        required=False,
        query_params={"nautobot_floor_plan_floor_plan": "$floor_plan", "racks": "$rack"},
    )
    x_origin = forms.CharField()
    y_origin = forms.CharField()

    field_order = [
        "floor_plan",
        "x_origin",
        "y_origin",
        "x_size",
        "y_size",
        "status",
        "rack",
        "rack_group",
        "rack_orientation",
    ]

    class Meta:
        """Meta attributes."""

        model = models.FloorPlanTile
        fields = "__all__"
        exclude = ["allocation_type", "on_group_tile"]  # pylint: disable=modelform-uses-exclude

    def __init__(self, *args, **kwargs):
        """Overwrite the constructor to define grid numbering style."""
        super().__init__(*args, **kwargs)
        self.x_letters = False
        self.y_letters = False

        if fp_id := self.initial.get("floor_plan") or self.data.get("floor_plan"):
            fp_obj = self.fields["floor_plan"].queryset.get(id=fp_id)
            self.x_letters = fp_obj.x_axis_labels == choices.AxisLabelsChoices.LETTERS
            self.y_letters = fp_obj.y_axis_labels == choices.AxisLabelsChoices.LETTERS

        if self.instance.x_origin or self.instance.y_origin:
            self.initial["x_origin"] = utils.axis_init_label_conversion(
                fp_obj.x_origin_seed,
                utils.grid_number_to_letter(self.instance.x_origin) if self.x_letters else self.initial.get("x_origin"),
                fp_obj.x_axis_step,
                self.x_letters,
            )
            self.initial["y_origin"] = utils.axis_init_label_conversion(
                fp_obj.y_origin_seed,
                utils.grid_number_to_letter(self.instance.y_origin) if self.y_letters else self.initial.get("y_origin"),
                fp_obj.y_axis_step,
                self.y_letters,
            )
        elif self.initial.get("x_origin") and self.initial.get("y_origin"):
            self.initial["x_origin"] = utils.axis_init_label_conversion(
                fp_obj.x_origin_seed, self.initial.get("x_origin"), fp_obj.x_axis_step, self.x_letters
            )
            self.initial["y_origin"] = utils.axis_init_label_conversion(
                fp_obj.y_origin_seed, self.initial.get("y_origin"), fp_obj.y_axis_step, self.y_letters
            )

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

        fp_obj = self.fields["floor_plan"].queryset.get(id=fp_id)
        value = self.cleaned_data.get(field_name)

        # Determine if letters are being used for x or y axis labels
        using_letters = (field_name == "x_origin" and self.x_letters) or (field_name == "y_origin" and self.y_letters)

        # Perform validation based on the type (letters or numbers)
        validator = self.letter_validator if using_letters else self.number_validator
        if not validator(field_name, value, axis):
            return 0  # Required to pass model clean() method

        # Select the appropriate axis seed and step
        if field_name == "x_origin":
            origin_seed, step, use_letters = fp_obj.x_origin_seed, fp_obj.x_axis_step, self.x_letters
        else:
            origin_seed, step, use_letters = fp_obj.y_origin_seed, fp_obj.y_axis_step, self.y_letters

        # Convert and return the label position using the specified conversion function
        cleaned_value = utils.axis_clean_label_conversion(origin_seed, value, step, use_letters)
        return int(cleaned_value) if not using_letters else cleaned_value

    def clean_x_origin(self):
        """Validate input and convert x_origin to an integer."""
        return self._clean_origin("x_origin", "X")

    def clean_y_origin(self):
        """Validate input and convert y_origin to an integer."""
        return self._clean_origin("y_origin", "Y")
