# TBD: Remove after releasing pylint-nautobot v0.3.0
# https://github.com/nautobot/pylint-nautobot/commit/48efc016fffa0b9df02f61bdaa9c4a0933351d29
# pylint: disable=nb-incorrect-base-class

"""Forms for nautobot_floor_plan."""

import json

from django import forms
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

    @property
    def x_ranges(self):
        """Return the X axis ranges formset."""
        return getattr(self, "_x_ranges", None)

    @x_ranges.setter
    def x_ranges(self, value):
        """Set the X axis ranges formset."""
        self._x_ranges = value

    @property
    def y_ranges(self):
        """Return the Y axis ranges formset."""
        return getattr(self, "_y_ranges", None)

    @y_ranges.setter
    def y_ranges(self, value):
        """Set the Y axis ranges formset."""
        self._y_ranges = value

    def __init__(self, *args, **kwargs):
        """Overwrite the constructor to set initial values and handle custom ranges."""
        super().__init__(*args, **kwargs)

        # Initialize axis configuration
        self.axis_letters = {"x": False, "y": False}

        # Set initial values for select widget
        if not self.instance.created:
            self.initial["x_axis_labels"] = get_app_settings_or_config("nautobot_floor_plan", "default_x_axis_labels")
            self.initial["y_axis_labels"] = get_app_settings_or_config("nautobot_floor_plan", "default_y_axis_labels")
            self.axis_letters["x"] = self.initial["x_axis_labels"] == choices.AxisLabelsChoices.LETTERS
            self.axis_letters["y"] = self.initial["y_axis_labels"] == choices.AxisLabelsChoices.LETTERS
            self.initial["x_origin_seed"] = "A" if self.axis_letters["x"] else "1"
            self.initial["y_origin_seed"] = "A" if self.axis_letters["y"] else "1"
        else:
            self.axis_letters["x"] = self.instance.x_axis_labels == choices.AxisLabelsChoices.LETTERS
            self.axis_letters["y"] = self.instance.y_axis_labels == choices.AxisLabelsChoices.LETTERS

        if self.axis_letters["x"] and str(self.initial["x_origin_seed"]).isdigit():
            self.initial["x_origin_seed"] = general.grid_number_to_letter(self.instance.x_origin_seed)
        if self.axis_letters["y"] and str(self.initial["y_origin_seed"]).isdigit():
            self.initial["y_origin_seed"] = general.grid_number_to_letter(self.instance.y_origin_seed)

        # Initialize formsets for X and Y axis ranges
        if self.instance.pk:
            x_initial = [
                {
                    "start": label_range.start_label,
                    "end": label_range.end_label,
                    "step": label_range.step,
                    "label_type": label_range.label_type,
                    "increment_letter": label_range.increment_letter,
                }
                for label_range in self.instance.custom_labels.filter(axis="X").order_by("order")
            ]
            y_initial = [
                {
                    "start": label_range.start_label,
                    "end": label_range.end_label,
                    "step": label_range.step,
                    "label_type": label_range.label_type,
                    "increment_letter": label_range.increment_letter,
                }
                for label_range in self.instance.custom_labels.filter(axis="Y").order_by("order")
            ]
        else:
            x_initial = []
            y_initial = []

        # Choose formset class based on whether there's existing data
        FormSetClass = CustomLabelRangeFormSetNoExtra if x_initial else CustomLabelRangeFormSetWithExtra
        self.x_ranges = FormSetClass(prefix="x_ranges", initial=x_initial, data=kwargs.get("data"))

        FormSetClass = CustomLabelRangeFormSetNoExtra if y_initial else CustomLabelRangeFormSetWithExtra
        self.y_ranges = FormSetClass(prefix="y_ranges", initial=y_initial, data=kwargs.get("data"))

        # Set has_x_custom_labels based on whether there are actual values in the formset
        self.has_x_custom_labels = any(
            form.initial.get("start") and form.initial.get("end")
            for form in self.x_ranges.forms
            if hasattr(form, "initial")
        )
        self.has_y_custom_labels = any(
            form.initial.get("start") and form.initial.get("end")
            for form in self.y_ranges.forms
            if hasattr(form, "initial")
        )

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
            self.add_error("x_size", f"X size cannot exceed {x_size_limit} as defined in nautobot_config.py.")

        # Validate Y size only if a limit is set
        if y_size_limit is not None and y_size is not None and y_size > y_size_limit:
            self.add_error("y_size", f"Y size cannot exceed {y_size_limit} as defined in nautobot_config.py.")

        return cleaned_data

    def _post_clean(self):
        """Process formset data after Django's validation."""
        super()._post_clean()

        def process_ranges(formset, axis):
            """Process formset data into a list of range dictionaries."""
            ranges_data = []

            for form in formset.forms:
                if not form.is_valid():
                    continue  # Skip invalid forms

                delete = form.cleaned_data.get("DELETE", False)
                if delete:
                    continue  # Skip deleted forms

                start = form.cleaned_data.get("start", "")
                end = form.cleaned_data.get("end", "")

                if start and end:
                    range_data = {
                        "start": start,
                        "end": end,
                        "step": form.cleaned_data.get("step", 1),
                        "label_type": form.cleaned_data.get("label_type"),
                        "increment_letter": form.cleaned_data.get("increment_letter", False),
                        "form_index": formset.forms.index(form),
                    }
                    ranges_data.append(range_data)

            if ranges_data:
                try:
                    validated_ranges = self._validate_custom_ranges(ranges_data, axis)
                    if validated_ranges:
                        self.cleaned_data[f"{axis}_custom_ranges"] = json.dumps(validated_ranges)
                    return validated_ranges
                except forms.ValidationError as e:
                    form = formset.forms[ranges_data[0]["form_index"]]
                    error_field = "start" if "start" in str(e).lower() else "end"
                    form.add_error(error_field, e)
                    return []

            return ranges_data

        # Process X and Y ranges
        process_ranges(self.x_ranges, "X")
        process_ranges(self.y_ranges, "Y")

    def is_valid(self):
        """Custom is_valid to ensure both form and formsets are valid."""
        # Check main form validity
        form_valid = super().is_valid()

        # Check formset validity
        x_ranges_valid = self.x_ranges.is_valid()
        y_ranges_valid = self.y_ranges.is_valid()

        # Only return True if everything is valid
        is_valid = all(
            [
                form_valid,
                x_ranges_valid,
                y_ranges_valid,
            ]
        )
        return is_valid

    def save(self, *args, **kwargs):
        """Custom save method to handle formsets."""
        instance = super().save(*args, **kwargs)

        # Clear existing custom ranges and labels
        instance.custom_labels.all().delete()

        # Process X ranges from the form's cleaned data
        x_ranges = self.cleaned_data.get("X_custom_ranges")
        if x_ranges:
            try:
                x_ranges = json.loads(x_ranges)
                valid_ranges = [r for r in x_ranges if r["start"] and r["end"]]
                if valid_ranges:
                    instance.x_custom_ranges = json.dumps(valid_ranges)
                    self.create_custom_axis_labels(valid_ranges, instance, "X")
            except json.JSONDecodeError as e:
                self.add_error(None, f"Invalid X axis range format: {e}")

        # Process Y ranges from the form's cleaned data
        y_ranges = self.cleaned_data.get("Y_custom_ranges")
        if y_ranges:
            try:
                y_ranges = json.loads(y_ranges)
                valid_ranges = [r for r in y_ranges if r["start"] and r["end"]]
                if valid_ranges:
                    instance.y_custom_ranges = json.dumps(valid_ranges)
                    self.create_custom_axis_labels(valid_ranges, instance, "Y")
            except json.JSONDecodeError as e:
                self.add_error(None, f"Invalid Y axis range format: {e}")

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

    def _validate_custom_ranges(self, ranges, axis):
        """Validate custom label ranges."""
        if not ranges:
            return []

        is_x_axis = axis == "X"

        max_size = self.cleaned_data.get("x_size" if is_x_axis else "y_size")
        validator = RangeValidator(max_size)

        # First validate each individual range
        for label_range in ranges:
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
        validator.validate_multiple_ranges(ranges)

        return ranges


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
        query_params={"nautobot_floor_plan_floor_plan": "$floor_plan", "racks": "$rack"},
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

        fp_obj = self.fields["floor_plan"].queryset.get(id=fp_id)
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

        fp_obj = self.fields["floor_plan"].queryset.get(id=fp_id)
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
