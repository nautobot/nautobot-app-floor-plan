"""Tables for nautobot_floor_plan."""

import django_tables2 as tables
from nautobot.apps.tables import BaseTable, ButtonsColumn, TagColumn, ToggleColumn
from nautobot.core.templatetags.helpers import hyperlinked_object, placeholder

from nautobot_floor_plan import models
from nautobot_floor_plan.templatetags.seed_helpers import (
    render_axis_origin,
    render_axis_step,
    render_origin_seed,
)


class FloorPlanTable(BaseTable):
    # pylint: disable=too-few-public-methods
    """Table for list view."""

    pk = ToggleColumn()
    floor_plan = tables.Column(empty_values=[], orderable=False)
    location = tables.Column(linkify=True)
    x_origin_seed = tables.Column(verbose_name="X Origin Seed")
    y_origin_seed = tables.Column(verbose_name="Y Origin Seed")
    tags = TagColumn()
    actions = ButtonsColumn(models.FloorPlan)

    def render_floor_plan(self, record):
        """Render a link to the detail view for the FloorPlan record itself."""
        return hyperlinked_object(record)

    def render_x_origin_seed(self, record):
        """Render x_origin seed or converted custom start label if defined."""
        return render_origin_seed(record, "x")

    def render_x_axis_step(self, record):
        """Render x_axis step or custom step if defined."""
        return render_axis_step(record, "x")

    def render_y_origin_seed(self, record):
        """Render y_origin seed or converted custom start label if defined."""
        return render_origin_seed(record, "y")

    def render_y_axis_step(self, record):
        """Render y_axis step or custom step if defined."""
        return render_axis_step(record, "y")

    class Meta(BaseTable.Meta):
        """Meta attributes."""

        model = models.FloorPlan
        # pylint: disable=nb-use-fields-all
        fields = (
            "pk",
            "floor_plan",
            "location",
            "x_size",
            "y_size",
            "x_origin_seed",
            "x_axis_step",
            "y_origin_seed",
            "y_axis_step",
            "tile_width",
            "tile_depth",
            "tags",
            "actions",
        )
        default_columns = (
            "pk",
            "floor_plan",
            "location",
            "x_size",
            "y_size",
            "x_origin_seed",
            "x_axis_step",
            "y_origin_seed",
            "y_axis_step",
            "tile_width",
            "tile_depth",
            "tags",
            "actions",
        )


class FloorPlanTileTable(BaseTable):
    """Table for list view."""

    floor_plan_tile = tables.Column(verbose_name="Tile", empty_values=[])
    floor_plan = tables.Column(linkify=True)
    location = tables.Column(accessor="floor_plan__location", linkify=True)
    x_origin = tables.Column()
    y_origin = tables.Column()
    allocation_type = tables.Column()
    allocated_object = tables.Column(
        empty_values=[],
        verbose_name="Object",
        accessor="object_name",  # Use the annotated field for sorting
    )
    tags = TagColumn()
    actions = ButtonsColumn(models.FloorPlanTile)

    def render_floor_plan_tile(self, record):
        """Render a link to the detail view for the FloorPlanTile record itself."""
        return hyperlinked_object(record)

    def render_x_origin(self, record):
        """Render x_origin using the generalized render_axis_origin method."""
        return render_axis_origin(record, "X")

    def render_y_origin(self, record):
        """Render y_origin using the generalized render_axis_origin method."""
        return render_axis_origin(record, "Y")

    def render_allocation_type(self, record):
        """Render the allocation type display value."""
        return record.get_allocation_type_display()

    def render_allocated_object(self, record):
        """Dynamically render the allocated object based on type."""
        if record.allocation_type != "object":
            return placeholder

        allocated_object = record.device or record.rack or record.power_panel or record.power_feed
        return hyperlinked_object(allocated_object) if allocated_object else placeholder

    class Meta(BaseTable.Meta):
        """Meta attributes."""

        model = models.FloorPlanTile
        fields = (
            "floor_plan_tile",
            "floor_plan",
            "location",
            "x_origin",
            "y_origin",
            "x_size",
            "y_size",
            "allocation_type",
            "allocated_object",
            "tags",
            "actions",
        )
        default_columns = (
            "floor_plan_tile",
            "floor_plan",
            "location",
            "x_origin",
            "y_origin",
            "x_size",
            "y_size",
            "allocation_type",
            "allocated_object",
            "tags",
            "actions",
        )
