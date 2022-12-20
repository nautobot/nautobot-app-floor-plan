"""API serializers for nautobot_floor_plan."""
from rest_framework import serializers

from nautobot.extras.api.serializers import NautobotModelSerializer

from nautobot_floor_plan import models

from .nested_serializers import NestedFloorPlanSerializer  # noqa: F401, pylint: disable=unused-import


class FloorPlanSerializer(NautobotModelSerializer):  # pylint: disable=too-many-ancestors
    """FloorPlan Serializer."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_floor_plan-api:floorplan-detail")

    class Meta:
        """Meta attributes."""

        model = models.FloorPlan
        fields = "__all__"

        # Option for disabling write for certain fields:
        # read_only_fields = []
