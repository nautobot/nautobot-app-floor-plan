"""Forms for nautobot_floor_plan."""
from django import forms
from nautobot.apps.forms import NautobotBulkEditForm, NautobotFilterForm, NautobotModelForm, TagsBulkEditFormMixin

from nautobot_floor_plan import models


class FloorPlanForm(NautobotModelForm):  # pylint: disable=too-many-ancestors
    """FloorPlan creation/edit form."""

    class Meta:
        """Meta attributes."""

        model = models.FloorPlan
        fields = [
            "name",
            "description",
        ]


class FloorPlanBulkEditForm(TagsBulkEditFormMixin, NautobotBulkEditForm):  # pylint: disable=too-many-ancestors
    """FloorPlan bulk edit form."""

    pk = forms.ModelMultipleChoiceField(queryset=models.FloorPlan.objects.all(), widget=forms.MultipleHiddenInput)
    description = forms.CharField(required=False)

    class Meta:
        """Meta attributes."""

        nullable_fields = [
            "description",
        ]


class FloorPlanFilterForm(NautobotFilterForm):
    """Filter form to filter searches."""

    model = models.FloorPlan
    field_order = ["q", "name"]

    q = forms.CharField(
        required=False,
        label="Search",
        help_text="Search within Name or Slug.",
    )
    name = forms.CharField(required=False, label="Name")
