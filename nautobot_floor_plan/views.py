"""Views for FloorPlan."""

from nautobot.apps.views import (
    NautobotUIViewSet,
    ObjectListViewMixin,
    ObjectDetailViewMixin,
    ObjectEditViewMixin,
    ObjectDestroyViewMixin,
    ObjectChangeLogViewMixin,
    ObjectNotesViewMixin,
    ObjectPermissionRequiredMixin,
)
from nautobot.apps.views import ObjectView
from nautobot.dcim.models import Location

from nautobot_floor_plan import filters, forms, models, tables
from nautobot_floor_plan.api import serializers


class FloorPlanUIViewSet(NautobotUIViewSet):  # TODO we only need a subset of views
    """ViewSet for FloorPlan views."""

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


class FloorPlanTileUIViewSet(
    ObjectListViewMixin,
    ObjectDetailViewMixin,
    ObjectEditViewMixin,
    ObjectDestroyViewMixin,
    ObjectChangeLogViewMixin,
    ObjectNotesViewMixin,
    ObjectPermissionRequiredMixin,
):
    # pylint: disable=W0223
    """ViewSet for FloorPlanTile views."""

    filterset_class = filters.FloorPlanTileFilterSet
    form_class = forms.FloorPlanTileForm
    lookup_field = "pk"
    queryset = models.FloorPlanTile.objects.all()
    serializer_class = serializers.FloorPlanTileSerializer
    table_class = tables.FloorPlanTileTable
    action_buttons = ()
