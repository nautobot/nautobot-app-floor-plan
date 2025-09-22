"""Models for Nautobot Floor Plan."""

import logging
from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from nautobot.apps.models import PrimaryModel, StatusField, extras_features

from nautobot_floor_plan.choices import (
    AllocationTypeChoices,
    AxisLabelsChoices,
    CustomAxisLabelsChoices,
    ObjectOrientationChoices,
)
from nautobot_floor_plan.svg import FloorPlanSVG
from nautobot_floor_plan.templatetags.seed_helpers import (
    render_axis_origin,
)
from nautobot_floor_plan.utils.custom_validators import ValidateNotZero
from nautobot_floor_plan.utils.label_generator import FloorPlanLabelGenerator

logger = logging.getLogger(__name__)


@dataclass
class TileOverlapData:
    """Data container for tile overlap validation."""

    x_min: int
    y_min: int
    x_max: int
    y_max: int
    allocation_type: str
    rack_group: object
    tile: "FloorPlanTile"

    @classmethod
    def from_tile(cls, tile: "FloorPlanTile"):
        """Create TileOverlapData from a FloorPlanTile instance."""
        x_min, y_min, x_max, y_max, allocation_type, rack_group = tile.bounds
        return cls(x_min, y_min, x_max, y_max, allocation_type, rack_group, tile)

    def overlaps_with(self, other: "TileOverlapData") -> bool:
        """Check if this tile overlaps with another tile."""
        return (
            self.x_min <= other.x_max
            and other.x_min <= self.x_max
            and self.y_min <= other.y_max
            and other.y_min <= self.y_max
        )


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

    def get_svg(self, *, user, base_url, request=None):
        """Get SVG representation of this FloorPlan."""
        return FloorPlanSVG(floor_plan=self, user=user, base_url=base_url, request=request).render()

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
    device = models.OneToOneField(
        to="dcim.Device",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="floor_plan_tile",
    )
    power_panel = models.OneToOneField(
        to="dcim.PowerPanel",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="floor_plan_tile",
    )
    power_feed = models.OneToOneField(
        to="dcim.PowerFeed",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="floor_plan_tile",
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

    object_orientation = models.CharField(
        max_length=10,
        choices=ObjectOrientationChoices,
        blank=True,
        help_text="Direction the object's front is facing on the floor plan",
    )
    allocation_type = models.CharField(
        choices=AllocationTypeChoices,
        max_length=10,
        blank=True,
        help_text="Assigns a type of either Object or RackGroup to a tile",
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
        # Reset on_group_tile to False by default
        self.on_group_tile = False

        # Assign Allocation type based off of Tile Assignment
        if self.rack_group is not None or self.status is not None:
            self.allocation_type = AllocationTypeChoices.RACKGROUP
        if any([self.rack, self.device, self.power_panel, self.power_feed]):
            self.allocation_type = AllocationTypeChoices.OBJECT

        # Ensure new tiles with just a status get an allocation type
        if not self.allocation_type and self.status:
            self.allocation_type = AllocationTypeChoices.RACKGROUP

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
        - Ensure that assigned objects belong to the correct Location.
        - Ensure that this FloorPlanTile doesn't overlap with any other FloorPlanTile in this FloorPlan.
        - Ensure that devices aren't currently installed in racks.
        - Ensure that racks belong to the correct rack group when placed on rack group tiles.
        - Ensure that object tiles don't extend beyond their containing rack group tiles.
        - Ensure that rack group tiles from different groups don't overlap.
        - Ensure proper allocation type assignment and group tile status.
        - Ensure only one object is assigned to the tile.
        """
        super().clean()
        FloorPlanTile.allocation_type_assignment(self)
        FloorPlanTile.validate_tile_placement(self)

        self._validate_installed_objects()
        self._validate_object_locations()
        self._validate_tile_overlaps()
        self._validate_rack_rackgroup()
        self._validate_single_object_assignment()

    def _validate_installed_objects(self):
        """Validate that devices aren't installed in racks."""
        if self.device and self.device.rack:
            raise ValidationError(
                {
                    "device": f"Device '{self.device}' is installed in Rack '{self.device.rack}'. "
                    "Please remove it from the rack before placing on the floor plan."
                }
            )

    def _validate_object_locations(self):
        """Validate location for all assigned objects."""
        assigned_objects = {
            "device": self.device,
            "rack": self.rack,
            "power_panel": self.power_panel,
            "power_feed": self.power_feed,
        }

        for obj_type, obj in assigned_objects.items():
            if obj is not None:
                # Power Feeds location is not required so we will check the connected power panel location instead
                if obj_type == "power_feed":
                    if obj.power_panel.location != self.floor_plan.location:
                        raise ValidationError(
                            {
                                obj_type: f"{obj.power_panel} must belong to Location {self.floor_plan.location}, not Location {obj.power_panel.location}"
                            }
                        )
                elif hasattr(obj, "location") and obj.location != self.floor_plan.location:
                    raise ValidationError(
                        {
                            obj_type: f"{obj} must belong to Location {self.floor_plan.location}, not Location {obj.location}"
                        }
                    )

    def _validate_tile_overlaps(self):
        """Validate that this FloorPlanTile doesn't overlap with any other FloorPlanTile in this FloorPlan."""
        current_tile_data = TileOverlapData.from_tile(self)

        for other in FloorPlanTile.objects.filter(floor_plan=self.floor_plan).exclude(pk=self.pk):
            other_tile_data = TileOverlapData.from_tile(other)

            if current_tile_data.overlaps_with(other_tile_data):
                # Validate based on allocation types
                self._validate_object_tile_overlap(current_tile_data, other_tile_data)
                self._validate_rackgroup_tile_overlap(current_tile_data, other_tile_data)

    def _validate_object_tile_overlap(self, current: TileOverlapData, other: TileOverlapData):
        """Validate overlaps for object tiles."""
        if current.allocation_type == AllocationTypeChoices.OBJECT:
            if other.allocation_type == AllocationTypeChoices.OBJECT:
                raise ValidationError("Object tiles cannot overlap")
            if other.allocation_type == AllocationTypeChoices.RACKGROUP:
                # Set on_group_tile for any object type overlapping with a RackGroup
                self.on_group_tile = True

                # Special handling for racks to ensure they belong to the correct rack group
                if self.rack and self.rack.rack_group:
                    if other.rack_group != self.rack.rack_group:
                        raise ValidationError(
                            f"Object tile with Rack {self.rack} cannot overlap with RackGroup tile for different group"
                        )
                    self.rack_group = self.rack.rack_group

                # Validate object tile fits within rack group bounds
                if (
                    current.x_min < other.x_min
                    or current.x_max > other.x_max
                    or current.y_min < other.y_min
                    or current.y_max > other.y_max
                ):
                    raise ValidationError("Object tile must not extend beyond the boundary of the rack group tile")

    def _validate_rackgroup_tile_overlap(self, current: TileOverlapData, other: TileOverlapData):
        """Validate overlaps for rack group tiles."""
        if current.allocation_type == AllocationTypeChoices.RACKGROUP:
            if other.allocation_type == AllocationTypeChoices.RACKGROUP:
                # Prevent any rack group tiles from overlapping
                raise ValidationError("RackGroup tiles cannot overlap")
            if other.allocation_type == AllocationTypeChoices.OBJECT and current.rack_group:
                other_tile = other.tile
                if other_tile.rack and other_tile.rack.rack_group and other_tile.rack.rack_group != current.rack_group:
                    raise ValidationError(
                        f"RackGroup tile cannot overlap with Rack {other_tile.rack} from different group"
                    )

    def _validate_rack_rackgroup(self):
        """Validate that racks belong to the correct rack group when placed on rack group tiles."""
        if not self.rack:
            return

        # If this tile has a rack_group, the rack must belong to it
        if self.rack_group and self.rack.rack_group != self.rack_group:
            raise ValidationError(
                f"Rack {self.rack} must belong to rack group {self.rack_group}, not {self.rack.rack_group}"
            )

        # Check if this rack overlaps with any rack group tiles
        overlapping_tiles = FloorPlanTile.objects.filter(
            floor_plan=self.floor_plan, allocation_type=AllocationTypeChoices.RACKGROUP
        ).exclude(pk=self.pk)

        for tile in overlapping_tiles:
            if (
                self.x_origin <= tile.x_origin + tile.x_size - 1
                and tile.x_origin <= self.x_origin + self.x_size - 1
                and self.y_origin <= tile.y_origin + tile.y_size - 1
                and tile.y_origin <= self.y_origin + self.y_size - 1
            ):
                # Only validate if the overlapping tile has a rack_group
                if tile.rack_group and self.rack.rack_group != tile.rack_group:
                    raise ValidationError(
                        f"Rack {self.rack} cannot be placed on rack group tile for {tile.rack_group} "
                        f"as it belongs to {self.rack.rack_group}"
                    )

    def _validate_single_object_assignment(self):
        """Validate that only one object is assigned to the tile."""
        assigned_objects = []
        object_fields = ["device", "rack", "power_panel", "power_feed"]

        for field in object_fields:
            if getattr(self, field) is not None:
                assigned_objects.append(field)

        if len(assigned_objects) > 1:
            object_names = {
                "device": "Device",
                "rack": "Rack",
                "power_panel": "Power Panel",
                "power_feed": "Power Feed",
            }

            # Add error to each selected field except the first one
            raise ValidationError(
                {
                    field: f"Only one object can be selected. You have already selected a {object_names[assigned_objects[0]]}."
                    for field in assigned_objects[1:]
                }
            )

    def __str__(self):
        """Stringify instance."""
        return f"Tile ({render_axis_origin(self, 'X')}, {render_axis_origin(self, 'Y')}), ({self.x_size},{self.y_size}) in {self.floor_plan}"
