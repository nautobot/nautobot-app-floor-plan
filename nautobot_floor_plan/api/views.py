"""API views for nautobot_floor_plan."""

from nautobot.apps.api import NautobotModelViewSet

from nautobot_floor_plan import filters, models
from nautobot_floor_plan.api import serializers


class FloorPlanViewSet(NautobotModelViewSet):  # pylint: disable=too-many-ancestors
    """FloorPlan viewset."""

    queryset = models.FloorPlan.objects.all()
    serializer_class = serializers.FloorPlanSerializer
    filterset_class = filters.FloorPlanFilterSet

    @extend_schema(exclude=True)
    @action(detail=True)
    @xframe_options_sameorigin
    def svg(self, request, *, pk):
        """SVG representation of a FloorPlan."""
        floor_plan = get_object_or_404(self.queryset, pk=pk)
        drawing = floor_plan.get_svg(user=request.user, base_url=request.build_absolute_uri("/"))
        return HttpResponse(drawing.tostring(), content_type="image/svg+xml; charset=utf-8")


class FloorPlanTileViewSet(NautobotModelViewSet):
    """FloorPlanTile viewset."""

    queryset = models.FloorPlanTile.objects.all()
    serializer_class = serializers.FloorPlanTileSerializer
    filterset_class = filters.FloorPlanTileFilterSet
