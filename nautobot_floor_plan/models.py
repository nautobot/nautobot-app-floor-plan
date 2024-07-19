"""Models for Nautobot Floor Plan."""

import logging

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction

from nautobot.apps.models import extras_features
from nautobot.apps.models import PrimaryModel
from nautobot.apps.models import StatusField

from nautobot_floor_plan.choices import RackOrientationChoices, AxisLabelsChoices, AllocationTypeChoices
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
    x_axis_labels = models.CharField(
        max_length=10,
        choices=AxisLabelsChoices,
        default=AxisLabelsChoices.NUMBERS,
        help_text="Grid labels of X axis (horizontal).",
    )
    y_axis_labels = models.CharField(
        max_length=10,
        choices=AxisLabelsChoices,
        default=AxisLabelsChoices.NUMBERS,
        help_text="Grid labels of Y axis (vertical).",
    )    
    x_origin_start = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)], default=1)
    y_origin_start = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)], default=1)

    class Meta:
        """Metaclass attributes."""

        ordering = ["location___name"]

    def __str__(self):
        """Stringify instance."""
        return f'Floor Plan for Location "{self.location.name}"'

    def get_svg(self, *, user, base_url):
        """Get SVG representation of this FloorPlan."""
        return FloorPlanSVG(floor_plan=self, user=user, base_url=base_url).render()

    def save(self, **kwargs):
        if not self.created:
            super().save(**kwargs)
            return
        # Get origin_start pre/post values
        initial_instance = self.__class__.objects.get(pk=self.pk)
        x_initial = initial_instance.x_origin_start
        y_initial = initial_instance.y_origin_start
        x_updated = self.x_origin_start
        y_updated = self.y_origin_start

        super().save(**kwargs)

        if x_initial != x_updated or y_initial != y_updated:
            self.update_tile_origins(x_initial, x_updated, y_initial, y_updated)
            
    def update_tile_origins(self, x_initial, x_updated, y_initial, y_updated):
        tiles = self.tiles.all()
        x_delta = x_updated - x_initial
        y_delta = y_updated - y_initial

        # should bulk_update these instead?
        with transaction.atomic():
            for tile in tiles:
                tile.x_origin += x_delta
                tile.y_origin += y_delta

                tile.validated_save()

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
# TBD: Remove after releasing pylint-nautobot v0.3.0
# pylint: disable-next=nb-string-field-blank-null
class FloorPlanTile(PrimaryModel):
    """Model representing a single rectangular "tile" within a FloorPlan, its status, and any Rack that it contains."""

    status = StatusField(blank=False, null=False)
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
        to="dcim.Rack",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="floor_plan_tile",
    )

    rack_group = models.ForeignKey(
        to="dcim.RackGroup",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="rack_groups",
    )
    rack_orientation = models.CharField(
        max_length=10,
        choices=RackOrientationChoices,
        blank=True,
        help_text="Direction the rack's front is facing on the floor plan",
    )
    allocation_type = models.CharField(
        choices=AllocationTypeChoices,
        max_length=10,
        blank=True,
        help_text="Assigns a type of either Rack or RackGroup to a tile",
    )

    on_group_tile = models.BooleanField(
        default=False, blank=True, help_text="Determines if a tile is placed on top of another tile"
    )

    class Meta:
        """Metaclass attributes."""

        ordering = ["floor_plan", "y_origin", "x_origin"]
        unique_together = ["floor_plan", "x_origin", "y_origin", "allocation_type"]

    def allocation_type_assignment(self):
        """Assign the appropriate tile allocation type when saving in clean."""
        # Assign Allocation type based off of Tile Assignemnt
        if self.rack_group is not None or self.status is not None:
            self.allocation_type = AllocationTypeChoices.RACKGROUP
        if self.rack is not None:
            self.allocation_type = AllocationTypeChoices.RACK
            self.on_group_tile = False

    @property
    def bounds(self):
        """Get the tuple representing the set of grid spaces occupied by this FloorPlanTile.

        This function also serves to return the allocation_type and rack_group of the underlying tile
        to ensure non-like allocation_types can overlap and non-like rack_group are unable to overlap.
        """
        return (
            self.x_origin,
            self.y_origin,
            self.x_origin + self.x_size - 1,
            self.y_origin + self.y_size - 1,
            self.allocation_type,
            self.rack_group,
        )

    def clean(self):
        """
        Validate parameters above and beyond what the database can provide.

        - Ensure that the bounds of this FloorPlanTile lie within the parent FloorPlan's bounds.
        - Ensure that the Rack if any belongs to the correct Location.
        - Ensure that this FloorPlanTile doesn't overlap with any other FloorPlanTile in this FloorPlan.
        """
        super().clean()
        FloorPlanTile.allocation_type_assignment(self)

        def group_tile_bounds(rack, rack_group):
            """Validate the overlapping of group tiles."""
            if rack is not None:
                # Set the tile rack_group equal to the rack.rack_group if the rack is in a rack_group
                if rack.rack_group is not None:
                    rack_group = rack.rack_group
                    self.rack_group = rack.rack_group
                if x_max > ox_max or x_min < ox_min:
                    raise ValidationError(
                        {f"Rack {self.rack} must not extend beyond the boundary of the defined group tiles"}
                    )
                if y_max > oy_max or y_min < oy_min:
                    raise ValidationError(
                        {f"Rack {self.rack} must not extend beyond the boundary of the defined group tiles"}
                    )
                self.on_group_tile = True
                if orack_group is not None:
                    if orack_group != rack_group or rack.rack_group != orack_group:
                        # Is tile assigned to a rack_group? Racks must be assigned to the same rack_group
                        raise ValidationError({"rack_group": f"Rack {self.rack} must belong to {orack_group}"})
            if rack is None:
                # RACKGROUP tiles can grow and shrink but not overlap other RACKGROUP tiles or Racks that are not assigned to the correct rackgroup
                if x_max > ox_max or x_min < ox_min:
                    if oallocation_type == AllocationTypeChoices.RACK and orack_group != rack_group:
                        raise ValidationError("Tile overlaps a Rack that is not in the specified RackGroup")
                if y_max > oy_max or y_min < oy_min:
                    if oallocation_type == AllocationTypeChoices.RACK and orack_group != rack_group:
                        raise ValidationError("Tile overlaps a Rack that is not in the specified RackGroup")
                if allocation_type == oallocation_type:
                    raise ValidationError("Tile overlaps with another defined tile.")

        # x <= 0, y <= 0 are covered by the base field definitions
        if self.x_origin > self.floor_plan.x_size + self.floor_plan.x_origin_start - 1:
            raise ValidationError({"x_origin": f"Too large for {self.floor_plan}"})
        if self.y_origin > self.floor_plan.y_size + self.floor_plan.y_origin_start - 1:
            raise ValidationError({"y_origin": f"Too large for {self.floor_plan}"})
        if self.x_origin < self.floor_plan.x_origin_start:
            raise ValidationError({"x_origin": f"Too small for {self.floor_plan}"})
        if self.y_origin < self.floor_plan.y_origin_start:
            raise ValidationError({"y_origin": f"Too small for {self.floor_plan}"})
        if self.x_origin + self.x_size - 1 > self.floor_plan.x_size + self.floor_plan.x_origin_start - 1:
            raise ValidationError({"x_size": f"Extends beyond the edge of {self.floor_plan}"})
        if self.y_origin + self.y_size - 1 > self.floor_plan.y_size + self.floor_plan.y_origin_start - 1:
            raise ValidationError({"y_size": f"Extends beyond the edge of {self.floor_plan}"})

        if self.rack is not None:
            if self.rack.location != self.floor_plan.location:
                raise ValidationError(
                    {"rack": f"Must belong to Location {self.floor_plan.location}, not Location {self.rack.location}"}
                )
        # Check for overlapping tiles.
        # TODO: this would be a lot more efficient using something like GeoDjango,
        # but since this is only checked at write time it's acceptable for now.
        x_min, y_min, x_max, y_max, allocation_type, rack_group = self.bounds
        for other in FloorPlanTile.objects.filter(floor_plan=self.floor_plan).exclude(pk=self.pk):
            ox_min, oy_min, ox_max, oy_max, oallocation_type, orack_group = other.bounds
            # Is either bounds rectangle completely to the right of the other?
            if x_min > ox_max or ox_min > x_max:
                continue
            # Is either bounds rectangle completely below the other?
            if y_min > oy_max or oy_min > y_max:
                continue
            # Are tiles in the same rackgroup?
            # If they are in the same rackgroup, do they overlap tiles?
            if allocation_type != oallocation_type:
                if self.rack is not None:
                    group_tile_bounds(self.rack, rack_group)
                    continue
                if self.rack is None:
                    group_tile_bounds(self.rack, rack_group)
                    continue
            # Else they must overlap
            raise ValidationError("Tile overlaps with another defined tile.")

    def __str__(self):
        """Stringify instance."""
        return f"Tile {self.bounds} in {self.floor_plan}"
