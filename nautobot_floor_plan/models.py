"""Models for Nautobot Floor Plan."""

import logging

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse

from nautobot.core.models.generics import PrimaryModel
from nautobot.extras.models import StatusModel
from nautobot.extras.utils import extras_features

from nautobot_floor_plan.choices import RackOrientationChoices
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
    """Model representing a single rectangular "tile" within a FloorPlan, its status, and any Rack that it contains."""

    floor_plan = models.ForeignKey(to=FloorPlan, on_delete=models.CASCADE, related_name="tiles")
    # TODO: for efficiency we could consider using something like GeoDjango, rather than inventing geometry from
    # first principles, but since that requires changing settings.DATABASES and installing libraries, avoid it for now.
    x_origin = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    y_origin = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    x_size = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        default=1,
        help_text="Number of tile spaces that this spans horizontally",
    )
    y_size = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        default=1,
        help_text="Number of tile spaces that this spans vertically",
    )

    rack = models.OneToOneField(
        to="dcim.Rack", on_delete=models.CASCADE, blank=True, null=True, related_name="floor_plan_tile"
    )
    rack_orientation = models.CharField(
        max_length=10,
        choices=RackOrientationChoices,
        blank=True,
        help_text="Direction the rack's front is facing on the floor plan",
    )
    # status field is automatically provided by StatusModel

    class Meta:
        """Metaclass attributes."""

        ordering = ["floor_plan", "y_origin", "x_origin"]
        unique_together = ["floor_plan", "x_origin", "y_origin"]

    csv_headers = [
        "location",
        "x_origin",
        "y_origin",
        "x_size",
        "y_size",
        "status",
        "rack",
        "rack_orientation",
    ]

    @property
    def bounds(self):
        """Get the tuple representing the set of grid spaces occupied by this FloorPlanTile."""
        return (self.x_origin, self.y_origin, self.x_origin + self.x_size - 1, self.y_origin + self.y_size - 1)

    def clean(self):
        """
        Validate parameters above and beyond what the database can provide.

        - Ensure that the bounds of this FloorPlanTile lie within the parent FloorPlan's bounds.
        - Ensure that the Rack if any belongs to the correct Location.
        - Ensure that this FloorPlanTile doesn't overlap with any other FloorPlanTile in this FloorPlan.
        """
        # x <= 0, y <= 0 are covered by the base field definitions
        super().clean()
        if self.x_origin > self.floor_plan.x_size:
            raise ValidationError({"x_origin": f"Too large for {self.floor_plan}"})
        if self.y_origin > self.floor_plan.y_size:
            raise ValidationError({"y_origin": f"Too large for {self.floor_plan}"})
        if self.x_origin + self.x_size - 1 > self.floor_plan.x_size:
            raise ValidationError({"x_size": f"Extends beyond the edge of {self.floor_plan}"})
        if self.y_origin + self.y_size - 1 > self.floor_plan.y_size:
            raise ValidationError({"y_size": f"Extends beyond the edge of {self.floor_plan}"})

        if self.rack is not None:
            if self.rack.location != self.floor_plan.location:
                raise ValidationError(
                    {"rack": f"Must belong to Location {self.floor_plan.location}, not Location {self.rack.location}"}
                )

        # Check for overlapping tiles.
        # TODO: this would be a lot more efficient using something like GeoDjango,
        # but since this is only checked at write time it's acceptable for now.
        x_min, y_min, x_max, y_max = self.bounds
        for other in FloorPlanTile.objects.filter(floor_plan=self.floor_plan).exclude(pk=self.pk):
            ox_min, oy_min, ox_max, oy_max = other.bounds
            # Is either bounds rectangle completely to the right of the other?
            if x_min > ox_max or ox_min > x_max:
                continue
            # Is either bounds rectangle completely below the other?
            if y_min > oy_max or oy_min > y_max:
                continue
            # Else they must overlap
            raise ValidationError("Tile overlaps with another defined tile.")

    def get_absolute_url(self):
        """Return detail view for FloorPlanTile."""
        return reverse("plugins:nautobot_floor_plan:floorplantile", args=[self.pk])

    def __str__(self):
        """Stringify instance."""
        return f"Tile {self.bounds} in {self.floor_plan}"

    def to_csv(self):
        """Convert instance to a tuple for CSV export."""
        return (
            self.floor_plan.location.name,
            self.x_origin,
            self.y_origin,
            self.x_size,
            self.y_size,
            self.status.name,
            self.rack.name if self.rack is not None else None,
            self.rack_orientation,
        )
