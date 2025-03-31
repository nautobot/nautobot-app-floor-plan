"""Views for FloorPlan."""

from django.db.models import Case, CharField, Value, When
from django_tables2 import RequestConfig
from nautobot.apps.config import get_app_settings_or_config
from nautobot.apps.ui import ObjectDetailContent, ObjectFieldsPanel, Panel, SectionChoices
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


class FloorPlanUIViewSet(NautobotUIViewSet):
    """ViewSet for FloorPlan views using UI Component Framework."""

    bulk_update_form_class = forms.FloorPlanBulkEditForm
    filterset_class = filters.FloorPlanFilterSet
    filterset_form_class = forms.FloorPlanFilterForm
    form_class = forms.FloorPlanForm
    lookup_field = "pk"
    queryset = models.FloorPlan.objects.all()
    serializer_class = serializers.FloorPlanSerializer
    table_class = tables.FloorPlanTable

    object_detail_content = ObjectDetailContent(
        panels=[
            ObjectFieldsPanel(
                weight=100,
                section=SectionChoices.LEFT_HALF,
                fields=["location", "x_size", "y_size", "tile_width", "tile_depth"],
            ),
            Panel(
                label="Axis Configuration",
                weight=200,
                section=SectionChoices.RIGHT_HALF,
                template_path="nautobot_floor_plan/inc/floorplan_axis_config_panel.html",
            ),
            Panel(
                label="Related Items",
                weight=300,
                section=SectionChoices.LEFT_HALF,
                template_path="nautobot_floor_plan/inc/floorplan_related_panel.html",
            ),
            Panel(
                label="Floor Plan Visualization",
                weight=400,
                section=SectionChoices.FULL_WIDTH,
                template_path="nautobot_floor_plan/inc/floorplan_svg.html",
            ),
        ]
    )

    def get_extra_context(self, request, instance=None):
        """Add custom context data to the view."""
        context = super().get_extra_context(request, instance)
        context.update(
            {
                "zoom_duration": get_app_settings_or_config("nautobot_floor_plan", "zoom_duration"),
                "highlight_duration": get_app_settings_or_config("nautobot_floor_plan", "highlight_duration"),
            }
        )
        return context


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
):  # pylint: disable=abstract-method
    """ViewSet for FloorPlanTile views."""

    filterset_class = filters.FloorPlanTileFilterSet
    form_class = forms.FloorPlanTileForm
    lookup_field = "pk"
    queryset = models.FloorPlanTile.objects.all()
    serializer_class = serializers.FloorPlanTileSerializer
    table_class = tables.FloorPlanTileTable
    action_buttons = ()

    object_detail_content = ObjectDetailContent(
        panels=[
            Panel(
                label="Floor Plan Tile",
                weight=100,
                section=SectionChoices.LEFT_HALF,
                template_path="nautobot_floor_plan/inc/floorplan_tile_detail_panel.html",
            ),
        ]
    )

    def get_extra_context(self, request, instance=None):
        """Add custom context data to the view."""
        context = super().get_extra_context(request, instance)
        if instance:
            context["tenant"] = instance.rack.tenant if instance.rack else None
            context["tenant_group"] = (
                instance.rack.tenant.tenant_group if instance.rack and instance.rack.tenant else None
            )
        return context

    def get_queryset(self):
        """Annotate queryset with object_name for sorting."""
        return (
            super()
            .get_queryset()
            .annotate(
                object_name=Case(
                    When(device__isnull=False, then="device__name"),
                    When(rack__isnull=False, then="rack__name"),
                    When(power_panel__isnull=False, then="power_panel__name"),
                    When(power_feed__isnull=False, then="power_feed__name"),
                    default=Value(""),
                    output_field=CharField(),
                )
            )
        )
