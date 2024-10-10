"""App declaration for nautobot_floor_plan."""

# Metadata is inherited from Nautobot. If not including Nautobot in the environment, this should be added
from importlib import metadata

from django.core.exceptions import ImproperlyConfigured
from django.db.models.signals import post_migrate
from nautobot.apps import NautobotAppConfig
from nautobot.apps.config import get_app_settings_or_config

from nautobot_floor_plan.choices import AxisLabelsChoices

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
        "default_x_axis_labels": AxisLabelsChoices.NUMBERS,
        "default_y_axis_labels": AxisLabelsChoices.NUMBERS,
        "default_statuses": {
            "FloorPlanTile": [
                {"name": "Active", "color": "4caf50"},
                {"name": "Reserved", "color": "00bcd4"},
                {"name": "Decommissioning", "color": "ffc107"},
                {"name": "Unavailable", "color": "111111"},
                {"name": "Planned", "color": "00bcd4"},
            ],
        },
    }
    caching_config = {}
    docs_view_name = "plugins:nautobot_floor_plan:docs"


config = FloorPlanConfig  # pylint:disable=invalid-name
