"""Views for nautobot_floor_plan."""
from nautobot.apps.views import NautobotUIViewSet

from nautobot_floor_plan import filters, forms, models, tables
from nautobot_floor_plan.api import serializers


class FloorPlanUIViewSet(NautobotUIViewSet):
    """ViewSet for FloorPlan views."""

    bulk_update_form_class = forms.FloorPlanBulkEditForm
    filterset_class = filters.FloorPlanFilterSet
    filterset_form_class = forms.FloorPlanFilterForm
    form_class = forms.FloorPlanForm
    lookup_field = "pk"
    queryset = models.FloorPlan.objects.all()
    serializer_class = serializers.FloorPlanSerializer
    table_class = tables.FloorPlanTable
