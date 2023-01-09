"""Views for FloorPlan."""

# TODO: when minimum Nautobot version becomes 1.5.2 or later, we can use:
# from nautobot.apps import views
from nautobot.core.views.generic import ObjectView
from nautobot.core.views.viewsets import NautobotUIViewSet
from nautobot.dcim.models import Location

from nautobot_floor_plan import filters, forms, models, tables
from nautobot_floor_plan.api import serializers


class FloorPlanUIViewSet(NautobotUIViewSet):
    """TODO."""

    bulk_create_form_class = forms.FloorPlanCSVForm
    bulk_update_form_class = forms.FloorPlanBulkEditForm
    filterset_class = filters.FloorPlanFilterSet
    filterset_form_class = forms.FloorPlanFilterForm
    form_class = forms.FloorPlanForm
    lookup_field = "pk"
    queryset = models.FloorPlan.objects.all()
    serializer_class = serializers.FloorPlanSerializer
    table_class = tables.FloorPlanTable


class LocationFloorPlanTab(ObjectView):
    """Add a "Floor Plan" tab to the Location detail view."""

    queryset = Location.objects.all()
    template_name = "nautobot_floor_plan/location_floor_plan.html"
