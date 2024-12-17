"""Views for FloorPlan."""

from django_tables2 import RequestConfig
from nautobot.apps.views import (
    NautobotUIViewSet,
    ObjectChangeLogViewMixin,
    ObjectDestroyViewMixin,
    ObjectDetailViewMixin,
    ObjectEditViewMixin,
    ObjectListViewMixin,
    ObjectNotesViewMixin,
    ObjectView,
)
from nautobot.core.views.paginator import EnhancedPaginator, get_paginate_count
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


class ChildLocationFloorPlanTab(ObjectView):
    """Add a "Child Floor Plan" tab to the Location detail view."""

    queryset = Location.objects.without_tree_fields().all()
    template_name = "nautobot_floor_plan/location_child_floor_plan.html"

    def get_extra_context(self, request, instance):
        """Return child locations that have floor plans."""
        children = (
            Location.objects.restrict(request.user, "view")
            .without_tree_fields()
            .filter(parent=instance, floor_plan__isnull=False)
            .select_related("parent", "location_type")
        )

        children_table = tables.FloorPlanTable(models.FloorPlan.objects.filter(location__in=children.all()))

        paginate = {
            "paginator_class": EnhancedPaginator,
            "per_page": get_paginate_count(request),
        }
        RequestConfig(request, paginate).configure(children_table)

        return {
            "children_table": children_table,
            "active_tab": "nautobot_floor_plan:2",
            **super().get_extra_context(request, instance),
        }


class FloorPlanTileUIViewSet(
    ObjectDetailViewMixin,
    ObjectListViewMixin,
    ObjectEditViewMixin,
    ObjectDestroyViewMixin,
    ObjectChangeLogViewMixin,
    ObjectNotesViewMixin,
):
    # pylint: disable=abstract-method
    """ViewSet for FloorPlanTile views."""

    filterset_class = filters.FloorPlanTileFilterSet
    form_class = forms.FloorPlanTileForm
    lookup_field = "pk"
    queryset = models.FloorPlanTile.objects.all()
    serializer_class = serializers.FloorPlanTileSerializer
    table_class = tables.FloorPlanTileTable
    action_buttons = ()
