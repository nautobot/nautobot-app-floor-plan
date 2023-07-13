"""Views for FloorPlan."""

from nautobot.core.views import generic

from nautobot_floor_plan import filters, forms, models, tables


class FloorPlanListView(generic.ObjectListView):
    """List view."""

    queryset = models.FloorPlan.objects.all()
    # These aren't needed for simple models, but we can always add
    # this search functionality.
    filterset = filters.FloorPlanFilterSet
    filterset_form = forms.FloorPlanFilterForm
    table = tables.FloorPlanTable

    # Option for modifying the top right buttons on the list view:
    # action_buttons = ("add", "import", "export")


class FloorPlanView(generic.ObjectView):
    """Detail view."""

    queryset = models.FloorPlan.objects.all()


class FloorPlanCreateView(generic.ObjectEditView):
    """Create view."""

    model = models.FloorPlan
    queryset = models.FloorPlan.objects.all()
    model_form = forms.FloorPlanForm


class FloorPlanDeleteView(generic.ObjectDeleteView):
    """Delete view."""

    model = models.FloorPlan
    queryset = models.FloorPlan.objects.all()


class FloorPlanEditView(generic.ObjectEditView):
    """Edit view."""

    model = models.FloorPlan
    queryset = models.FloorPlan.objects.all()
    model_form = forms.FloorPlanForm


class FloorPlanBulkDeleteView(generic.BulkDeleteView):
    """View for deleting one or more FloorPlan records."""

    queryset = models.FloorPlan.objects.all()
    table = tables.FloorPlanTable


class FloorPlanBulkEditView(generic.BulkEditView):
    """View for editing one or more FloorPlan records."""

    queryset = models.FloorPlan.objects.all()
    table = tables.FloorPlanTable
    form = forms.FloorPlanBulkEditForm
