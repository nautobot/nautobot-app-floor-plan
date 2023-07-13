"""Forms for nautobot_floor_plan."""
from django import forms
from nautobot.utilities.forms import (
    BootstrapMixin,
    BulkEditForm,
    SlugField,
)

from nautobot_floor_plan import models


class FloorPlanForm(BootstrapMixin, forms.ModelForm):
    """FloorPlan creation/edit form."""

    slug = SlugField()

    class Meta:
        """Meta attributes."""

        model = models.FloorPlan
        fields = [
            "name",
            "slug",
            "description",
        ]


class FloorPlanBulkEditForm(BootstrapMixin, BulkEditForm):
    """FloorPlan bulk edit form."""

    pk = forms.ModelMultipleChoiceField(queryset=models.FloorPlan.objects.all(), widget=forms.MultipleHiddenInput)
    description = forms.CharField(required=False)

    class Meta:
        """Meta attributes."""

        nullable_fields = [
            "description",
        ]


class FloorPlanFilterForm(BootstrapMixin, forms.ModelForm):
    """Filter form to filter searches."""

    q = forms.CharField(
        required=False,
        label="Search",
        help_text="Search within Name or Slug.",
    )
    name = forms.CharField(required=False, label="Name")
    slug = forms.CharField(required=False, label="Slug")

    class Meta:
        """Meta attributes."""

        model = models.FloorPlan
        # Define the fields above for ordering and widget purposes
        fields = [
            "q",
            "name",
            "slug",
            "description",
        ]
