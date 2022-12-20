"""API views for nautobot_floor_plan."""

from nautobot.extras.api.views import NautobotModelViewSet

from nautobot_floor_plan import filters, models

from nautobot_floor_plan.api import serializers


class FloorPlanViewSet(NautobotModelViewSet):  # pylint: disable=too-many-ancestors
    """FloorPlan viewset."""

    queryset = models.FloorPlan.objects.all()
    serializer_class = serializers.FloorPlanSerializer
    filterset_class = filters.FloorPlanFilterSet

    # Option for modifying the default HTTP methods:
    # http_method_names = ["get", "post", "put", "patch", "delete", "head", "options", "trace"]
