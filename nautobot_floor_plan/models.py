"""Models for Nautobot Floor Plan."""

import logging

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from nautobot.apps.models import PrimaryModel, StatusField, extras_features

from nautobot_floor_plan.choices import (
    AllocationTypeChoices,
    AxisLabelsChoices,
    CustomAxisLabelsChoices,
    RackOrientationChoices,
)
from nautobot_floor_plan.custom_validators import ValidateNotZero
from nautobot_floor_plan.label_generator import FloorPlanLabelGenerator
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
        max_length=12,
        choices=AxisLabelsChoices,
        default=AxisLabelsChoices.NUMBERS,
        help_text="Grid labels of X axis (horizontal).",
    )
    y_axis_labels = models.CharField(
        max_length=12,
        choices=AxisLabelsChoices,
        default=AxisLabelsChoices.NUMBERS,
        help_text="Grid labels of Y axis (vertical).",
    )
    x_origin_seed = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0)], default=1, help_text="User defined starting value for grid labeling"
    )
    y_origin_seed = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0)], default=1, help_text="User defined starting value for grid labeling"
    )
    x_axis_step = models.IntegerField(
        validators=[ValidateNotZero(0)],
        default=1,
        help_text="Positive or negative integer that will be used to step labeling.",
    )
    y_axis_step = models.IntegerField(
        validators=[ValidateNotZero(0)],
        default=1,
        help_text="Positive or negative integer that will be used to step labeling.",
    )
    is_tile_movable = models.BooleanField(default=True, help_text="Determines if Tiles can be moved once placed")

    class Meta:
        """Metaclass attributes."""

        ordering = ["location___name"]

    def __str__(self):
        """Stringify instance."""
        return f'Floor Plan for Location "{self.location.name}"'

    def get_svg(self, *, user, base_url):
        """Get SVG representation of this FloorPlan."""
        return FloorPlanSVG(floor_plan=self, user=user, base_url=base_url).render()

    def clean(self):
        """Validate the floor plan dimensions and other constraints."""
        super().clean()
        self.validate_no_resizing_with_tiles()

    def save(self, *args, **kwargs):
        """Override save in order to update any existing tiles."""
        if self.present_in_database:
            # Get origin_seed pre/post values
            initial_instance = self.__class__.objects.get(pk=self.pk)
            x_initial = initial_instance.x_origin_seed
            y_initial = initial_instance.y_origin_seed
            changed = x_initial != self.x_origin_seed or y_initial != self.y_origin_seed
        else:
            changed = False

        with transaction.atomic():
            super().save(**kwargs)

            if changed:
                tiles = self.update_tile_origins(x_initial, self.x_origin_seed, y_initial, self.y_origin_seed)
                for tile in tiles:
                    tile.validated_save()

    def update_tile_origins(self, x_initial, x_updated, y_initial, y_updated):
        """Update any existing tiles if axis_origin_seed was modified."""
        tiles = self.tiles.all()
        x_delta = x_updated - x_initial
        y_delta = y_updated - y_initial

        if x_delta > 0:
            tiles = tiles.order_by("-x_origin")
        if y_delta > 0:
            tiles = tiles.order_by("-y_origin")

        for tile in tiles:
            tile.x_origin += x_delta
            tile.y_origin += y_delta

        return tiles

    def validate_no_resizing_with_tiles(self):
        """Prevent resizing the floor plan dimensions if tiles have been placed."""
        if self.tiles.exists():
            # Check for original instance
            original = self.__class__.objects.filter(pk=self.pk).first()
            if original:
                # Don't allow resize if tile is placed
                if self.x_size != original.x_size or self.y_size != original.y_size:
                    raise ValidationError(
                        "Cannot resize a FloorPlan after tiles have been placed. "
                        f"FloorPlan must maintain original size: ({original.x_size}, {original.y_size}), "
                    )

    def generate_labels(self, axis, count):
        """
        Generate labels for the specified axis.

        This method creates an instance of FloorPlanLabelGenerator and uses it to generate labels
        based on the specified axis and count. It will first check for any custom labels defined
        for the axis and use them if available; otherwise, it will generate default labels.
        """
        generator = FloorPlanLabelGenerator(self)
        return generator.generate_labels(axis, count)

    def reset_seed_for_custom_labels(self):
        """Reset seed and step values when custom labels are added."""
        # Only proceed if there are custom labels
        if not self.custom_labels.exists():
            return

        changed = False
        x_has_custom = self.custom_labels.filter(axis="X").exists()
        y_has_custom = self.custom_labels.filter(axis="Y").exists()

        if x_has_custom and (self.x_origin_seed != 1 or self.x_axis_step != 1):
            self.x_origin_seed = 1
            self.x_axis_step = 1
            changed = True

        if y_has_custom and (self.y_origin_seed != 1 or self.y_axis_step != 1):
            self.y_origin_seed = 1
            self.y_axis_step = 1
            changed = True

        if changed:
            # Get the current values before updating
            initial_instance = self.__class__.objects.get(pk=self.pk)
            x_initial = initial_instance.x_origin_seed
            y_initial = initial_instance.y_origin_seed

            # Update tile positions only for axes that have custom labels
            tiles = self.update_tile_origins(
                x_initial=x_initial if x_has_custom else self.x_origin_seed,
                x_updated=1 if x_has_custom else self.x_origin_seed,
                y_initial=y_initial if y_has_custom else self.y_origin_seed,
                y_updated=1 if y_has_custom else self.y_origin_seed,
            )

            # Save without triggering another reset
            super().save()

            # Update tiles
            for tile in tiles:
                tile.validated_save()


@extras_features(
    "custom_fields",
    "custom_validators",
    "graphql",
    "relationships",
    "webhooks",
)
class FloorPlanCustomAxisLabel(models.Model):
    """Model allowing for the creation of custom grid labels."""

    floor_plan = models.ForeignKey(
        to="FloorPlan",
        on_delete=models.CASCADE,
        related_name="custom_labels",
    )
    axis = models.CharField(
        max_length=1,
        choices=(("X", "X Axis"), ("Y", "Y Axis")),
    )
    label_type = models.CharField(
        max_length=20,
        choices=CustomAxisLabelsChoices,
        default=AxisLabelsChoices.LETTERS,
        help_text="Type of labeling system to use",
    )
    start_label = models.CharField(
        max_length=10,
        help_text="Starting label for this custom label range.",
    )
    end_label = models.CharField(
        max_length=10,
        help_text="Ending label for this custom label range.",
    )
    step = models.IntegerField(
        validators=[ValidateNotZero(0)],
        default=1,
        help_text="Positive or negative step for this label range.",
    )
    increment_letter = models.BooleanField(
        default=True,
        help_text="For letter-based labels, determines increment pattern.",
    )

    order = models.PositiveIntegerField(
        default=0,
        help_text="Order of the custom label range.",
    )

    class Meta:
        """Meta attributes."""

        ordering = ["floor_plan", "axis", "order"]

    def save(self, *args, **kwargs):
        """Override save to reset seed values when custom labels are added."""
        super().save(*args, **kwargs)
        # Reset the corresponding seed value to 1
        self.floor_plan.reset_seed_for_custom_labels()

    def clean(self):
        """Add validation to ensure seed values are reset."""
        super().clean()
        # If this is a new custom label (no pk) or the axis has changed
        if not self.pk or (self.pk and self._state.fields_cache.get("axis") != self.axis):
            if self.axis == "X" and self.floor_plan.x_origin_seed != 1:
                self.floor_plan.x_origin_seed = 1
            elif self.axis == "Y" and self.floor_plan.y_origin_seed != 1:
                self.floor_plan.y_origin_seed = 1


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
class FloorPlanTile(PrimaryModel):
    """Model representing a single rectangular "tile" within a FloorPlan, its status, and any Rack that it contains."""

    status = StatusField(blank=False, null=False)
    floor_plan = models.ForeignKey(to=FloorPlan, on_delete=models.CASCADE, related_name="tiles")
    # TODO: for efficiency we could consider using something like GeoDjango, rather than inventing geometry from
    # first principles, but since that requires changing settings.DATABASES and installing libraries, avoid it for now.
    x_origin = models.PositiveSmallIntegerField(validators=[MinValueValidator(0)])
    y_origin = models.PositiveSmallIntegerField(validators=[MinValueValidator(0)])
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

    def validate_tile_placement(self):
        """Check that tile fits within the floorplan."""
        if self.x_origin > self.floor_plan.x_size + self.floor_plan.x_origin_seed - 1:
            raise ValidationError({"x_origin": f"Too large for {self.floor_plan}"})
        if self.y_origin > self.floor_plan.y_size + self.floor_plan.y_origin_seed - 1:
            raise ValidationError({"y_origin": f"Too large for {self.floor_plan}"})
        if self.x_origin < self.floor_plan.x_origin_seed:
            raise ValidationError({"x_origin": f"Too small for {self.floor_plan}"})
        if self.y_origin < self.floor_plan.y_origin_seed:
            raise ValidationError({"y_origin": f"Too small for {self.floor_plan}"})
        if self.x_origin + self.x_size - 1 > self.floor_plan.x_size + self.floor_plan.x_origin_seed - 1:
            raise ValidationError({"x_size": f"Extends beyond the edge of {self.floor_plan}"})
        if self.y_origin + self.y_size - 1 > self.floor_plan.y_size + self.floor_plan.y_origin_seed - 1:
            raise ValidationError({"y_size": f"Extends beyond the edge of {self.floor_plan}"})

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
        FloorPlanTile.validate_tile_placement(self)

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
