"""Misc Utilities for the testing."""

from importlib.metadata import version as get_version

from nautobot_floor_plan import models


def is_nautobot_version_less_than(required_version: str) -> bool:
    """Check if the current Nautobot version is less than the required version."""
    return get_version("nautobot") < required_version


def create_custom_labels(floor_plan, labels_config, axis="X"):
    """Helper to create custom labels from config."""

    for config in labels_config:
        models.FloorPlanCustomAxisLabel.objects.create(
            floor_plan=floor_plan,
            axis=axis,
            start_label=config["start"],
            end_label=config["end"],
            step=config["step"],
            increment_letter=config["increment_letter"],
            label_type=config["label_type"],
        )
