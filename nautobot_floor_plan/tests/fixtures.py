"""Create fixtures for tests."""
from nautobot_floor_plan.models import FloorPlan


def create_floorplan():
    """Fixture to create necessary number of FloorPlan for tests."""
    FloorPlan.objects.create(name="Test One", slug="test-one")
    FloorPlan.objects.create(name="Test Two", slug="test-two")
    FloorPlan.objects.create(name="Test Three", slug="test-three")
