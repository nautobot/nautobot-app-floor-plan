"""API views for nautobot_floor_plan."""

from nautobot.extras.api.views import NautobotModelViewSet

from nautobot_floor_plan import filters, models

from nautobot_floor_plan.api import serializers


class FloorPlanViewSet(NautobotModelViewSet):
    """FloorPlan viewset."""

    queryset = models.FloorPlan.objects.all()
    serializer_class = serializers.FloorPlanSerializer
    filterset_class = filters.FloorPlanFilterSet


class FloorPlanTileViewSet(NautobotModelViewSet):
    """FloorPlanTile viewset."""

    queryset = models.FloorPlanTile.objects.all()
    serializer_class = serializers.FloorPlanTileSerializer
    filterset_class = filters.FloorPlanTileFilterSet
