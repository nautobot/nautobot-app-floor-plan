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

from nautobot_floor_plan import choices, models
from nautobot_floor_plan.utils import general
from nautobot_floor_plan.utils.custom_validators import RangeValidator
from nautobot_floor_plan.utils.label_converters import LabelToPositionConverter, PositionToLabelConverter


class FloorPlanForm(NautobotModelForm):
    """FloorPlan creation/edit form with support for custom axis label ranges."""

    CUSTOM_RANGES_HELP_TEXT = (
        "Enter custom label ranges in JSON format. <br>"
        "Distance between start and end cannot exceed the size of the floor plan. <br>"
        "Examples: <a href='#' data-toggle='modal' data-target='#exampleModal'>Click here for examples</a>."
    )

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
        required=True,
    )
    x_custom_ranges = forms.JSONField(
        label="Custom Ranges for X Axis",
        required=False,
        help_text=CUSTOM_RANGES_HELP_TEXT,
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
        required=True,
    )
    y_custom_ranges = forms.JSONField(
        label="Custom Ranges for Y Axis",
        required=False,
        help_text=CUSTOM_RANGES_HELP_TEXT,
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
                "tabs": (
                    ("Default Labels", ("x_axis_labels", "x_origin_seed", "x_axis_step")),
                    ("Custom Labels", ("x_custom_ranges",)),
                ),
            },
        ),
        (
            "Y Axis Settings",
            {
                "tabs": (
                    ("Default Labels", ("y_axis_labels", "y_origin_seed", "y_axis_step")),
                    ("Custom Labels", ("y_custom_ranges",)),
                ),
            },
        ),
    )

    class Meta:
        """Meta attributes."""

        model = models.FloorPlan
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        """Overwrite the constructor to set initial values and handle custom ranges."""
        super().__init__(*args, **kwargs)

        # Set initial values for select widget
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
            self.initial["x_origin_seed"] = general.grid_number_to_letter(self.instance.x_origin_seed)
        if self.y_letters and str(self.initial["y_origin_seed"]).isdigit():
            self.initial["y_origin_seed"] = general.grid_number_to_letter(self.instance.y_origin_seed)

        # Load existing custom ranges
        if self.instance.pk:
            x_ranges = list(
                self.instance.custom_labels.filter(axis="X")
                .values("start_label", "end_label", "step", "increment_letter", "label_type", "order")
                .order_by("order")
            )
            y_ranges = list(
                self.instance.custom_labels.filter(axis="Y")
                .values("start_label", "end_label", "step", "increment_letter", "label_type", "order")
                .order_by("order")
            )

            # Set the properties based on whether custom ranges exist
            self.has_x_custom_labels = bool(x_ranges)
            self.has_y_custom_labels = bool(y_ranges)

            if x_ranges:
                self.initial["x_custom_ranges"] = [
                    {
                        "start": r["start_label"],
                        "end": r["end_label"],
                        "step": r["step"],
                        "increment_letter": r["increment_letter"],
                        "label_type": r["label_type"],
                    }
                    for r in x_ranges
                ]
            if y_ranges:
                self.initial["y_custom_ranges"] = [
                    {
                        "start": r["start_label"],
                        "end": r["end_label"],
                        "step": r["step"],
                        "increment_letter": r["increment_letter"],
                        "label_type": r["label_type"],
                    }
                    for r in y_ranges
                ]

    def _clean_origin_seed(self, field_name, axis):
        """Clean method for origin seed fields."""
        value = self.cleaned_data.get(field_name)
        if not value:
            return value

        # Determine if using letters based on axis labels
        using_letters = (
            self.cleaned_data.get("x_axis_labels") == choices.AxisLabelsChoices.LETTERS
            if axis == "X"
            else self.cleaned_data.get("y_axis_labels") == choices.AxisLabelsChoices.LETTERS
        )

        # Validate format based on axis label type
        if using_letters:
            if not value.isalpha():
                raise forms.ValidationError(f"{axis} origin seed should be letters when using letter labels.")
            if not value.isupper():
                raise forms.ValidationError(f"{axis} origin seed should be uppercase letters.")
            # Convert letter to corresponding number
            return general.grid_letter_to_number(value)
        try:
            return int(value)
        except ValueError as e:
            raise forms.ValidationError(f"{axis} origin seed should be a number when using numeric labels.") from e

    def clean_x_origin_seed(self):
        """Validate the X origin seed."""
        return self._clean_origin_seed("x_origin_seed", "X")

    def clean_y_origin_seed(self):
        """Validate the Y origin seed."""
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

    def save(self, commit=True):
        """Save the FloorPlan instance along with custom ranges."""
        instance = super().save(commit=False)
        x_ranges = self.cleaned_data.get("x_custom_ranges", [])
        y_ranges = self.cleaned_data.get("y_custom_ranges", [])

        # Set increment_letter defaults
        for label_range in x_ranges:
            if label_range.get("increment_letter", True) and label_range["label_type"] == "numbers":
                label_range["increment_letter"] = False

        for label_range in y_ranges:
            if label_range.get("increment_letter", True) and label_range["label_type"] == "numbers":
                label_range["increment_letter"] = False

        if commit:
            instance.save()
            self.save_m2m()

            # Clear existing custom ranges
            models.FloorPlanCustomAxisLabel.objects.filter(floor_plan=instance).delete()

            # Save X axis custom ranges
            if x_ranges:
                self.create_custom_axis_labels(x_ranges, instance, axis="X")
            # Save Y axis custom ranges
            if y_ranges:
                self.create_custom_axis_labels(y_ranges, instance, axis="Y")

        return instance

    def create_custom_axis_labels(self, ranges, instance, axis):
        """Helper function to create custom axis labels."""
        labels = []
        for idx, custom_range in enumerate(ranges):
            labels.append(
                models.FloorPlanCustomAxisLabel(
                    floor_plan=instance,
                    axis=axis,
                    start_label=custom_range["start"],
                    end_label=custom_range["end"],
                    step=custom_range.get("step", 1),
                    label_type=custom_range["label_type"],
                    increment_letter=custom_range.get("increment_letter", True),
                    order=idx,  # Assign order based on index
                )
            )
        models.FloorPlanCustomAxisLabel.objects.bulk_create(labels)

    def _validate_custom_ranges(self, field_name):
        """Validate custom label ranges."""
        custom_ranges = self.cleaned_data.get(field_name, [])
        if not custom_ranges:
            return []

        is_x_axis = field_name == "x_custom_ranges"
        max_size = self.cleaned_data.get("x_size" if is_x_axis else "y_size")
        validator = RangeValidator(max_size)

        # First validate each individual range
        for label_range in custom_ranges:
            validator.validate_required_keys(label_range)

            start = label_range["start"]
            end = label_range["end"]
            label_type = label_range["label_type"]

            validator.validate_label_type(label_type)
            if label_type == choices.CustomAxisLabelsChoices.NUMBERS and label_range.get("increment_letter"):
                validator.validate_increment_letter_for_numbers(label_range.get("increment_letter"))
            if label_type in [choices.CustomAxisLabelsChoices.HEX, choices.CustomAxisLabelsChoices.BINARY]:
                validator.validate_numeric_range(start, end, current_range=label_range)
            else:
                validator.validate_custom_range(start, end, label_type, current_range=label_range)
            validator.validate_increment_letter(label_range, label_type)

        # Then validate that ranges don't overlap
        validator.validate_multiple_ranges(custom_ranges)

        return custom_ranges

    def clean_x_custom_ranges(self):
        """Validate the X axis custom ranges."""
        return self._validate_custom_ranges("x_custom_ranges")

    def clean_y_custom_ranges(self):
        """Validate the Y axis custom ranges."""
        return self._validate_custom_ranges("y_custom_ranges")


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

    def __init__(self, *args, **kwargs):
        """Initialize the form and handle custom label conversions."""
        super().__init__(*args, **kwargs)
        self.x_letters = False
        self.y_letters = False

        if fp_id := self.initial.get("floor_plan") or self.data.get("floor_plan"):
            fp_obj = self.fields["floor_plan"].queryset.get(id=fp_id)
            self.x_letters = fp_obj.x_axis_labels == choices.AxisLabelsChoices.LETTERS
            self.y_letters = fp_obj.y_axis_labels == choices.AxisLabelsChoices.LETTERS
            if not fp_obj.is_tile_movable:
                self.fields["x_origin"].disabled = True
                self.fields["y_origin"].disabled = True

            if self.instance.x_origin or self.instance.y_origin:
                if fp_obj.custom_labels.filter(axis="X").exists():
                    converter = PositionToLabelConverter(self.instance.x_origin, "X", fp_obj)
                    if label := converter.convert():
                        self.initial["x_origin"] = label
                else:
                    self.initial["x_origin"] = general.axis_init_label_conversion(
                        fp_obj.x_origin_seed,
                        general.grid_number_to_letter(self.instance.x_origin)
                        if self.x_letters
                        else self.initial.get("x_origin"),
                        fp_obj.x_axis_step,
                        self.x_letters,
                    )
                if fp_obj.custom_labels.filter(axis="Y").exists():
                    converter = PositionToLabelConverter(self.instance.y_origin, "Y", fp_obj)
                    if label := converter.convert():
                        self.initial["y_origin"] = label
                else:
                    self.initial["y_origin"] = general.axis_init_label_conversion(
                        fp_obj.y_origin_seed,
                        general.grid_number_to_letter(self.instance.y_origin)
                        if self.y_letters
                        else self.initial.get("y_origin"),
                        fp_obj.y_axis_step,
                        self.y_letters,
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
        cleaned_value = general.axis_clean_label_conversion(origin_seed, value, step, use_letters)
        return int(cleaned_value) if not using_letters else cleaned_value
