"""API serializers for nautobot_floor_plan."""
from rest_framework import serializers

from nautobot.dcim.api.serializers import NestedLocationSerializer
from nautobot.extras.api.serializers import NautobotModelSerializer, TaggedObjectSerializer

from nautobot_floor_plan import models

from .nested_serializers import NestedFloorPlanSerializer  # noqa: F401, pylint: disable=unused-import


class FloorPlanSerializer(NautobotModelSerializer, TaggedObjectSerializer):  # pylint: disable=too-many-ancestors
    """FloorPlan Serializer."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_floor_plan-api:floorplan-detail")
    location = NestedLocationSerializer()

    class Meta:
        """Meta attributes."""

        model = models.FloorPlan
        fields = "__all__"

        # Option for disabling write for certain fields:
        # read_only_fields = []
