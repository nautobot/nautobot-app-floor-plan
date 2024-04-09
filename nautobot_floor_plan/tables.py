"""Tables for nautobot_floor_plan."""

import django_tables2 as tables
from nautobot.apps.tables import BaseTable, ButtonsColumn, TagColumn, ToggleColumn
from nautobot.core.templatetags.helpers import hyperlinked_object

from nautobot_floor_plan import models


class FloorPlanTable(BaseTable):
    # pylint: disable=R0903
    """Table for list view."""

    pk = ToggleColumn()
    floor_plan = tables.Column(empty_values=[])
    location = tables.Column(linkify=True)
    tags = TagColumn()
    actions = ButtonsColumn(models.FloorPlan)

    def render_floor_plan(self, record):
        """Render a link to the detail view for the FloorPlan record itself."""
        return hyperlinked_object(record)

    class Meta(BaseTable.Meta):
        """Meta attributes."""

        model = models.FloorPlan
        fields = (
            "pk",
            "floor_plan",
            "location",
            "x_size",
            "y_size",
            "tile_width",
            "tile_depth",
            "tags",
            "actions",
        )
        default_columns = (
            "pk",
            "floor_plan",
            "location",
            "tags",
            "actions",
        )


class FloorPlanTileTable(BaseTable):
    # pylint: disable=R0903
    """Table for list view."""

    floor_plan_tile = tables.Column(empty_values=[])
    floor_plan = tables.Column(empty_values=[])
    rack = tables.Column(linkify=True)
    tags = TagColumn()
    actions = ButtonsColumn(models.FloorPlanTile)

    def render_floor_plan_tile(self, record):
        """Render a link to the detail view for the FloorPlanTile record itself."""
        return hyperlinked_object(record)

    def render_floor_plan(self, record):
        """Render a link to the detail view for the FloorPlan record itself."""
        return hyperlinked_object(record.floor_plan)

    class Meta(BaseTable.Meta):
        """Meta attributes."""

        model = models.FloorPlanTile
        fields = (
            "floor_plan_tile",
            "floor_plan",
            "x_origin",
            "y_origin",
            "x_size",
            "y_size",
            "rack",
            "rack_orientation",
            "tags",
            "actions",
        )
        default_columns = (
            "floor_plan_tile",
            "floor_plan",
            "x_origin",
            "y_origin",
            "x_size",
            "y_size",
            "rack",
            "tags",
            "actions",
        )
