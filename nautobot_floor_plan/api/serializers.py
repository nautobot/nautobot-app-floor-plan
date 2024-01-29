"""API serializers for nautobot_floor_plan."""
from nautobot.apps.api import NautobotModelSerializer, TaggedModelSerializerMixin

from nautobot_floor_plan import models


class FloorPlanSerializer(NautobotModelSerializer, TaggedModelSerializerMixin):  # pylint: disable=too-many-ancestors
    """FloorPlan Serializer."""

    class Meta:
        """Meta attributes."""

        model = models.FloorPlan
        fields = "__all__"

        # Option for disabling write for certain fields:
        # read_only_fields = []
