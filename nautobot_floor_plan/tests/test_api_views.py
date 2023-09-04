"""Unit tests for nautobot_floor_plan."""
from django.contrib.contenttypes.models import ContentType

from nautobot.dcim.models import Rack
from nautobot.extras.models import Tag
from nautobot.apps.testing import APIViewTestCases

from nautobot_floor_plan import choices, models
from nautobot_floor_plan.tests import fixtures


class FloorPlanAPIViewTest(APIViewTestCases.APIViewTestCase):
    """Test the API viewsets for FloorPlan."""

    model = models.FloorPlan
    bulk_update_data = {"x_size": 10, "y_size": 1}
    brief_fields = ["display", "id", "url", "x_size", "y_size"]

    @classmethod
    def setUpTestData(cls):
        data = fixtures.create_prerequisites(floor_count=6)
        fixtures.create_floor_plans(data["floors"][:3])
        cls.create_data = [
            {
                "location": data["floors"][3].pk,
                "x_size": 1,
                "y_size": 2,
            },
            {
                "location": data["floors"][4].pk,
                "x_size": 3,
                "y_size": 4,
            },
            {
                "location": data["floors"][5].pk,
                "x_size": 4,
                "y_size": 5,
            },
        ]


class FloorPlanTileAPIViewTest(APIViewTestCases.APIViewTestCase):
    """Test the API viewsets for FloorPlanTile."""

    model = models.FloorPlanTile
    brief_fields = ["display", "id", "url", "x_origin", "x_size", "y_origin", "y_size"]
    choices_fields = ["rack_orientation"]
    # TODO choices_fields = ["rack_orientation", "status"]
    validation_excluded_fields = ["status"]

    @classmethod
    def setUpTestData(cls):
        data = fixtures.create_prerequisites()
        floor_plans = fixtures.create_floor_plans(data["floors"])
        cls.rack_2_2_2 = Rack(name="Rack 1", status=data["status"], location=data["floors"][1])
        cls.rack_2_2_2.validated_save()
        cls.model.objects.create(floor_plan=floor_plans[0], status=data["status"], x_origin=1, y_origin=1)
        cls.model.objects.create(
            floor_plan=floor_plans[1], status=data["status"], x_origin=2, y_origin=2, rack=cls.rack_2_2_2
        )
        cls.model.objects.create(floor_plan=floor_plans[2], status=data["status"], x_origin=3, y_origin=3)
        cls.rack_3_1_1 = Rack(name="Rack 2", status=data["status"], location=data["floors"][2])
        cls.rack_3_1_1.validated_save()
        cls.create_data = [
            {
                "floor_plan": floor_plans[2].pk,
                "x_origin": 1,
                "y_origin": 1,
                "status": data["status"].name,
                "rack": cls.rack_3_1_1.pk,
                "rack_orientation": choices.RackOrientationChoices.RIGHT,
            },
            {
                "floor_plan": floor_plans[2].pk,
                "x_origin": 2,
                "y_origin": 1,
                "x_size": 1,
                "y_size": 1,
                "status": data["status"].name,
            },
            {
                "floor_plan": floor_plans[3].pk,
                "x_origin": 2,
                "y_origin": 2,
                "x_size": 2,
                "y_size": 2,
                "status": data["status"].name,
            },
        ]
        tag = Tag.objects.create(name="Hello")
        tag.content_types.add(ContentType.objects.get_for_model(models.FloorPlanTile))
        cls.bulk_update_data = {"tags": [tag.pk]}
