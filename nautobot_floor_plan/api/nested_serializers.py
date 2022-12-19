"""API nested serializers for nautobot_floor_plan."""
from rest_framework import serializers

from nautobot.core.api import WritableNestedSerializer

from nautobot_floor_plan import models


class NestedFloorPlanSerializer(WritableNestedSerializer):
    """FloorPlan Nested Serializer."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_floor_plan-api:floorplan-detail")

    class Meta:
        """Meta attributes."""

        model = models.FloorPlan
        fields = ["id", "url", "name", "slug"]
