"""Create fixtures for tests."""

from django.contrib.contenttypes.models import ContentType
from nautobot.dcim.models import Location, LocationType, Rack, RackGroup
from nautobot.extras.models import Status

from nautobot_floor_plan.models import FloorPlan, FloorPlanTile


def create_prerequisites(floor_count=4):
    """Fixture to create the various prerequisite objects needed before a FloorPlan can be created."""
    location_type_site = LocationType.objects.create(name="Site")
    parent_location_type = LocationType.objects.create(name="Building")
    location_type = LocationType.objects.create(name="Floor", parent=parent_location_type)
    location_type.content_types.add(ContentType.objects.get_for_model(Rack))
    location_type.content_types.add(ContentType.objects.get_for_model(RackGroup))

    active_status = Status.objects.get(name="Active")
    active_status.content_types.add(ContentType.objects.get_for_model(FloorPlanTile))

    location = Location.objects.create(name="Location 1", status=active_status, location_type=location_type_site)
    building = Location.objects.create(
        parent=location, location_type=parent_location_type, name="Building 1", status=active_status
    )
    floors = []
    for i in range(1, floor_count + 1):
        floors.append(
            Location.objects.create(
                location_type=location_type, parent=building, status=active_status, name=f"Floor {i}"
            )
        )

    return {
        "status": active_status,
        "floors": floors,
        "location": location,
    }


def create_floor_plans(locations):
    """Fixture to create necessary number of FloorPlan for tests."""
    size = 1
    floor_plans = []

    for location in locations:
        floor_plan = FloorPlan(location=location, x_size=size, y_size=size)
        floor_plan.validated_save()
        floor_plans.append(floor_plan)
        size += 1

    return floor_plans
