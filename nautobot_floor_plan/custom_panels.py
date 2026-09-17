"""Panel for Floor Plan visualization."""

from nautobot.apps.ui import Panel


class AxisConfigurationPanel(Panel):
    """Panel for displaying Floor Plan axis configuration."""

    def __init__(self, **kwargs):
        """Initialize the panel, setting the template path and label."""
        kwargs.setdefault("label", "Axis Configuration")
        kwargs.setdefault("template_path", "nautobot_floor_plan/inc/floorplan_axis_config_panel.html")
        super().__init__(**kwargs)


class RelatedItemsPanel(Panel):
    """Panel for displaying Floor Plan related items."""

    def __init__(self, **kwargs):
        """Initialize the panel, setting the template path and label."""
        kwargs.setdefault("label", "Related Items")
        kwargs.setdefault("template_path", "nautobot_floor_plan/inc/floorplan_related_panel.html")
        super().__init__(**kwargs)


class FloorPlanVisualizationPanel(Panel):
    """Custom panel for floor plan visualization."""

    def __init__(self, **kwargs):
        """Initialize the panel, setting the template path."""
        kwargs.setdefault("template_path", "nautobot_floor_plan/inc/floorplan_svg.html")
        super().__init__(**kwargs)


class TileObjectDetailsPanel(Panel):
    """Panel for displaying Floor Plan Tile object details."""

    def __init__(self, **kwargs):
        """Initialize the panel, setting the template path and label."""
        kwargs.setdefault("label", "Tile Object Information")
        kwargs.setdefault("template_path", "nautobot_floor_plan/inc/floorplan_tile_detail_panel.html")
        super().__init__(**kwargs)
