"""Models for Nautobot Floor Plan."""

import logging

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse

from nautobot.core.models.generics import PrimaryModel
from nautobot.extras.models import StatusModel
from nautobot.extras.utils import extras_features

from nautobot_floor_plan.svg import FloorPlanSVG


logger = logging.getLogger(__name__)


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
    x_size = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        help_text='Absolute width of the floor plan, in "tiles"',
    )
    y_size = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        help_text='Absolute depth of the floor plan, in "tiles"',
    )
    tile_width = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        default=100,
        help_text='Relative width of each "tile" in the floor plan (cm, inches, etc.)',
    )
    tile_depth = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        default=100,
        help_text='Relative depth of each "tile" in the floor plan (cm, inches, etc.)',
    )

    class Meta:
        """Metaclass attributes."""

        ordering = ["location___name"]

    csv_headers = [
        "location",
        "x_size",
        "y_size",
        "tile_width",
        "tile_depth",
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
            self.tile_width,
            self.tile_depth,
        )

    def get_tiles(self):
        """Return a two-dimensional array (`[y][x]`) of FloorPlanTiles (which may contain null entries)."""
        logger.debug("Getting tiles...")
        tiles_queryset = self.tiles.order_by("y", "x").select_related("rack", "floor_plan")
        logger.debug("Constructing grid...")
        result = []
        row = []
        x = 1
        y = 1
        for tile in tiles_queryset.all():
            # Fill in null entries up to the current tile, if needed
            while y < tile.y:
                while x < self.x_size + 1:
                    row.append(None)
                    x += 1
                result.append(row)
                row = []
                y += 1
                x = 1
            while x < tile.x:
                row.append(None)
                x += 1

            # Fill in the current tile
            row.append(tile)
            x += 1
            if x > self.x_size:
                result.append(row)
                row = []
                y += 1
                x = 1

        # Fill in null entries after the last tile, if needed
        while y < self.y_size + 1:
            while x < self.x_size + 1:
                row.append(None)
                x += 1
            result.append(row)
            row = []
            y += 1
            x = 1

        logger.debug("Grid assembled!")
        return result

    def get_svg(self, *, user, base_url):
        """Get SVG representation of this FloorPlan."""
        return FloorPlanSVG(floor_plan=self, user=user, base_url=base_url).render()


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
        """Metaclass attributes."""

        ordering = ["floor_plan", "y", "x"]
        unique_together = ["floor_plan", "x", "y"]

    csv_headers = [
        "location",
        "x",
        "y",
        "status",
        "rack",
    ]

    def clean(self):
        """
        Validate parameters above and beyond what the database can provide.

        - Ensure that the x, y coordinates of this FloorPlanTile lie within the parent FloorPlan's bounds.
        - Ensure that the Rack if any belongs to the correct Location
        """
        # x <= 0, y <= 0 are covered by the base field definitions
        super().clean()
        if self.x > self.floor_plan.x_size:
            raise ValidationError({"x": f"Too large for {self.floor_plan}"})
        if self.y > self.floor_plan.y_size:
            raise ValidationError({"y": f"Too large for {self.floor_plan}"})

        if self.rack is not None:
            if self.rack.location != self.floor_plan.location:
                raise ValidationError(
                    {"rack": f"Must belong to Location {self.floor_plan.location}, not Location {self.rack.location}"}
                )

    def get_absolute_url(self):
        """Return detail view for FloorPlanTile."""
        return reverse("plugins:nautobot_floor_plan:floorplantile", args=[self.pk])

    def __str__(self):
        """Stringify instance."""
        return f"Tile ({self.x}, {self.y}) in {self.floor_plan}"

    def to_csv(self):
        """Convert instance to a tuple for CSV export."""
        return (
            self.floor_plan.location.name,
            self.x,
            self.y,
            self.get_status_display(),
            self.rack.name if self.rack is not None else None,
        )
