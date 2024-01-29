"""Tables for nautobot_floor_plan."""

import django_tables2 as tables
from nautobot.apps.tables import BaseTable, ButtonsColumn, ToggleColumn

from nautobot_floor_plan import models


class FloorPlanTable(BaseTable):
    # pylint: disable=R0903
    """Table for list view."""

    pk = ToggleColumn()
    name = tables.Column(linkify=True)
    actions = ButtonsColumn(
        models.FloorPlan,
        # Option for modifying the default action buttons on each row:
        # buttons=("changelog", "edit", "delete"),
        # Option for modifying the pk for the action buttons:
        pk_field="pk",
    )

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
