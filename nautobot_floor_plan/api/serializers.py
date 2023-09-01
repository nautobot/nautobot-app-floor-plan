"""API serializers for nautobot_floor_plan."""
from nautobot.core.api.serializers import NautobotModelSerializer
from nautobot_floor_plan import models


class FloorPlanSerializer(NautobotModelSerializer):
    """FloorPlan Serializer."""

    class Meta:
        """Meta attributes."""

        model = models.FloorPlan
        fields = "__all__"


class FloorPlanTileSerializer(NautobotModelSerializer):
    """FloorPlanTile Serializer."""

    class Meta:
        """Meta attributes."""

        model = models.FloorPlanTile
        fields = "__all__"
