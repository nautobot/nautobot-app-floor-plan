"""API views for nautobot_floor_plan."""

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.clickjacking import xframe_options_sameorigin
from drf_spectacular.utils import extend_schema
from nautobot.apps.api import NautobotModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response

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

    @action(detail=False, methods=["post"])
    def generate_preview(self, request):
        """
        Generate a preview of custom axis labels based on the provided ranges.
        Expects a payload with 'axis' and 'ranges'.
        """
        try:
            axis = request.data.get("axis")
            ranges = request.data.get("ranges", [])

            # Replace with the actual logic to generate preview labels
            labels = []
            for r in ranges:
                labels.extend(generate_labels(r))  # Replace with your implementation

            return Response({"success": True, "labels": labels})
        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=400)


class FloorPlanTileViewSet(NautobotModelViewSet):
    """FloorPlanTile viewset."""

    queryset = models.FloorPlanTile.objects.all()
    serializer_class = serializers.FloorPlanTileSerializer
    filterset_class = filters.FloorPlanTileFilterSet
