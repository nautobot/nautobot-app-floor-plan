"""Misc Utilities for the testing."""

from importlib.metadata import version as get_version


def is_nautobot_version_less_than(required_version: str) -> bool:
    """Check if the current Nautobot version is less than the required version."""
    return get_version("nautobot") < required_version
