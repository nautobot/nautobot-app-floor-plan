"""API serializers for nautobot_floor_plan."""
from rest_framework import serializers

from nautobot.dcim.api.serializers import NestedLocationSerializer, NestedRackSerializer
from nautobot.extras.api.serializers import NautobotModelSerializer, StatusModelSerializerMixin, TaggedObjectSerializer

from nautobot_floor_plan import models

from .nested_serializers import *  # noqa: F403, pylint: disable=unused-import,unused-wildcard-import,wildcard-import


class FloorPlanSerializer(NautobotModelSerializer, TaggedObjectSerializer):
    """FloorPlan Serializer."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_floor_plan-api:floorplan-detail")
    location = NestedLocationSerializer()

    class Meta:
        """Meta attributes."""

        model = models.FloorPlan
        fields = "__all__"


class FloorPlanTileSerializer(NautobotModelSerializer, StatusModelSerializerMixin, TaggedObjectSerializer):
    """FloorPlanTile Serializer."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_floor_plan-api:floorplantile-detail")
    floor_plan = NestedFloorPlanSerializer()  # noqa: F405
    rack = NestedRackSerializer(required=False)

    class Meta:
        """Meta attributes."""

        model = models.FloorPlanTile
        fields = "__all__"
