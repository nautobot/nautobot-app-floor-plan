"""App declaration for nautobot_floor_plan."""
# Metadata is inherited from Nautobot. If not including Nautobot in the environment, this should be added
from importlib import metadata

from nautobot.apps import NautobotAppConfig
from nautobot_floor_plan import choices

__version__ = metadata.version(__name__)


class FloorPlanConfig(NautobotAppConfig):
    """App configuration for the nautobot_floor_plan app."""

    name = "nautobot_floor_plan"
    verbose_name = "Floor Plans"
    version = __version__
    author = "Network to Code, LLC"
    description = "Nautobot App for representing rack positions on per-location floor plan grids."
    base_url = "floor-plan"
    required_settings = []
    min_version = "2.0.0"
    max_version = "2.9999"
    default_settings = {
        "grid_x_axis_labels": choices.AxisLabelsChoices.NUMBERS,
        "grid_y_axis_labels": choices.AxisLabelsChoices.NUMBERS,
    }
    caching_config = {}


config = FloorPlanConfig  # pylint:disable=invalid-name
