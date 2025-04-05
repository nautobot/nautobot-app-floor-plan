"""Views for FloorPlan."""

from types import SimpleNamespace

from django_tables2 import RequestConfig
from nautobot.apps.config import get_app_settings_or_config
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

from .choices import CustomAxisLabelsChoices


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

    def safe_get_errors(self, obj, attr):
        """Safely retrieves the 'errors' attribute from a given attribute of an object."""
        return getattr(obj, attr, SimpleNamespace(errors=None)).errors

    def get_extra_context(self, request, instance=None):
        """Add custom context data to the view."""
        context = super().get_extra_context(request, instance)
        context["label_type_choices"] = [
            {"value": choice[0], "label": choice[1]} for choice in CustomAxisLabelsChoices.CHOICES
        ]
        context["zoom_duration"] = get_app_settings_or_config("nautobot_floor_plan", "zoom_duration")
        context["highlight_duration"] = get_app_settings_or_config("nautobot_floor_plan", "highlight_duration")

        # Default to showing the default tab
        context.update(
            {
                "x_activate_default_tab": True,
                "x_activate_custom_tab": False,
                "y_activate_default_tab": True,
                "y_activate_custom_tab": False,
            }
        )

        # Check for custom labels on the instance first
        if instance and instance.pk:
            has_x_custom_labels = instance.custom_labels.filter(axis="X").exists()
            has_y_custom_labels = instance.custom_labels.filter(axis="Y").exists()

            if has_x_custom_labels:
                context.update(
                    {
                        "x_activate_default_tab": False,
                        "x_activate_custom_tab": True,
                    }
                )

            if has_y_custom_labels:
                context.update(
                    {
                        "y_activate_default_tab": False,
                        "y_activate_custom_tab": True,
                    }
                )

        # Then check form state if available
        form = context.get("form")
        if form:
            # X-axis tab activation logic
            x_default_tab_errors = (
                self.safe_get_errors(form, "x_origin_seed")
                or self.safe_get_errors(form, "x_axis_step")
                or self.safe_get_errors(form, "x_axis_labels")
            )

            x_custom_tab_errors = form.x_ranges.errors if hasattr(form, "x_ranges") else False

            # Switch to custom tab if:
            # 1. There are custom labels and no default errors, or
            # 2. There are custom tab errors
            if (form.has_x_custom_labels and not x_default_tab_errors) or x_custom_tab_errors:
                context.update(
                    {
                        "x_activate_default_tab": False,
                        "x_activate_custom_tab": True,
                    }
                )

            # Y-axis logic tab activation logic
            y_default_tab_errors = (
                self.safe_get_errors(form, "y_origin_seed")
                or self.safe_get_errors(form, "y_axis_step")
                or self.safe_get_errors(form, "y_axis_labels")
            )
            y_custom_tab_errors = form.y_ranges.errors if hasattr(form, "y_ranges") else False

            # Switch to custom tab if:
            # 1. There are custom labels and no default errors, or
            # 2. There are custom tab errors
            if (form.has_y_custom_labels and not y_default_tab_errors) or y_custom_tab_errors:
                context.update(
                    {
                        "y_activate_default_tab": False,
                        "y_activate_custom_tab": True,
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
