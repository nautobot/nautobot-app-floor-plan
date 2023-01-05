"""Models for Nautobot Floor Plan."""

# Django imports
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse

# Nautobot imports
from nautobot.core.models.generics import PrimaryModel
from nautobot.extras.models import StatusModel
from nautobot.extras.utils import extras_features


@extras_features(
    "custom_fields",
    # "custom_links",  Not really needed since this doesn't have distinct views as compared to a Location.
    "custom_validators",
    "export_templates",
    "graphql",
    "relationships",
    "webhooks",
)
class FloorPlan(PrimaryModel):
    """
    Model representing the floor plan of a given Location.

    Within a FloorPlan, individual areas are defined as FloorPlanTile records.
    """

    location = models.OneToOneField(to="dcim.Location", on_delete=models.CASCADE, related_name="floor_plan")

    # Since a FloorPlan maps one-to-one to a Location, it doesn't need a separate name/slug/description of its own
    x_size = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    y_size = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])

    csv_headers = [
        "location",
        "x_size",
        "y_size",
    ]

    def get_absolute_url(self):
        """Return detail view for FloorPlan."""
        return reverse("plugins:nautobot_floor_plan:floorplan", args=[self.pk])

    def __str__(self):
        """Stringify instance."""
        return f'Floor Plan for Location "{self.location.name}"'

    def to_csv(self):
        """Convert instance to a tuple for CSV export."""
        return (
            self.location.name,
            self.x_size,
            self.y_size,
        )

    def get_tiles(self):
        """Return a two-dimensional array (`[y][x]`) of FloorPlanTiles (which may contain null entries)."""
        tiles_queryset = self.tiles.order_by("y", "x")
        # TODO: the below is fairly inefficient, we should be able to iterate over tiles_queryset directly in some way.
        result = []
        for y in range(1, self.y_size + 1):
            row = []
            for x in range(1, self.x_size + 1):
                try:
                    row.append(tiles_queryset.get(x=x, y=y))
                except ObjectDoesNotExist:
                    row.append(None)
            result.append(row)
        return result


@extras_features(
    "custom_fields",
    # "custom_links",  Not really needed since this doesn't have distinct views.
    "custom_validators",
    # "export_templates",  Not really useful here
    "graphql",
    "relationships",
    "statuses",
    "webhooks",
)
class FloorPlanTile(PrimaryModel, StatusModel):
    """Model representing a single (x, y) "tile" within a FloorPlan, its status, and any Rack that it contains."""

    floor_plan = models.ForeignKey(to=FloorPlan, on_delete=models.CASCADE, related_name="tiles")
    x = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    y = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])

    rack = models.OneToOneField(
        to="dcim.Rack", on_delete=models.CASCADE, blank=True, null=True, related_name="floor_plan_tile"
    )
    # status field is automatically provided by StatusModel

    class Meta:
        ordering = ["floor_plan", "y", "x"]
        unique_together = ["floor_plan", "x", "y"]

    csv_headers = [
        "location",
        "x",
        "y",
        "status",
        "rack",
    ]

    def get_absolute_url(self):
        """No detail view exists for a FloorPlanTile."""
        return self.floor_plan.get_absolute_url()

    def __str__(self):
        """Stringify instance."""
        representation = f'({self.x}, {self.y}) in {self.floor_plan} has Status "{self.status}"'
        if self.rack is not None:
            representation += f' and contains Rack "{self.rack}"'
        return representation

    def to_csv(self):
        """Convert instance to a tuple for CSV export."""
        return (
            self.floor_plan.location.name,
            self.x,
            self.y,
            self.get_status_display(),
            self.rack.name if self.rack is not None else None,
        )
