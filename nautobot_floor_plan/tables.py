"""Tables for nautobot_floor_plan."""

import django_tables2 as tables
from nautobot.apps.tables import BaseTable, ButtonsColumn, TagColumn, ToggleColumn
from nautobot.core.templatetags.helpers import hyperlinked_object

from nautobot_floor_plan import models
from nautobot_floor_plan.templatetags.seed_helpers import (
    grid_location_conversion,
    render_axis_step,
    render_origin_seed,
)


class FloorPlanTable(BaseTable):
    # pylint: disable=too-few-public-methods
    """Table for list view."""

    pk = ToggleColumn()
    floor_plan = tables.Column(empty_values=[], orderable=False)
    location = tables.Column(linkify=True)
    x_origin_seed = tables.Column(accessor="x_origin_seed", verbose_name="X Origin Seed")
    y_origin_seed = tables.Column(accessor="y_origin_seed", verbose_name="Y Origin Seed")
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
    # pylint: disable=too-few-public-methods
    """Table for list view."""

    floor_plan_tile = tables.Column(verbose_name="Tile", empty_values=[])
    floor_plan = tables.Column(linkify=True)
    location = tables.Column(accessor="floor_plan__location", linkify=True)
    x_origin = tables.Column()
    y_origin = tables.Column()
    rack = tables.Column(linkify=True)
    tags = TagColumn()
    actions = ButtonsColumn(models.FloorPlanTile)

    def render_floor_plan_tile(self, record):
        """Render a link to the detail view for the FloorPlanTile record itself."""
        return hyperlinked_object(record)

    def render_x_origin(self, record):
        """Render x_origin in letters if requried."""
        return grid_location_conversion(record, "x")

    def render_y_origin(self, record):
        """Render y_origin in letters if requried."""
        return grid_location_conversion(record, "y")

    class Meta(BaseTable.Meta):
        """Meta attributes."""

        model = models.FloorPlanTile
        # pylint: disable=nb-use-fields-all
        fields = (
            "floor_plan_tile",
            "floor_plan",
            "location",
            "x_origin",
            "y_origin",
            "x_size",
            "y_size",
            "rack",
            "rack_group",
            "rack_orientation",
            "rack.tenant",
            "rack.tenant.tenant_group",
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
            "rack",
            "rack_group",
            "tags",
            "actions",
        )
