"""Forms for nautobot_floor_plan."""
from django import forms

from nautobot.dcim.models import Location
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
    x_size = forms.IntegerField(min_value=1)
    y_size = forms.IntegerField(min_value=1)

    class Meta:
        """Meta attributes."""

        fields = ["pk", "x_size", "y_size", "tags"]


class FloorPlanFilterForm(NautobotFilterForm):
    """Filter form to filter searches."""

    model = models.FloorPlan
    field_order = ["q", "location", "x_size", "y_size"]

    q = forms.CharField(required=False, label="Search")
    location = DynamicModelMultipleChoiceField(queryset=Location.objects.all(), to_field_name="slug", required=False)
    tag = TagFilterField(model)
