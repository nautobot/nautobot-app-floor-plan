"""Unit tests for nautobot_floor_plan."""

from django.contrib.contenttypes.models import ContentType

from nautobot.extras.models import Tag
from nautobot.utilities.testing import APIViewTestCases

from nautobot_floor_plan import models
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
    brief_fields = ["display", "id", "url", "x", "y"]
    # TODO choices_fields = ["status"]
    validation_excluded_fields = ["status"]

    @classmethod
    def setUpTestData(cls):
        data = fixtures.create_prerequisites()
        floor_plans = fixtures.create_floor_plans(data["floors"])
        cls.model.objects.create(floor_plan=floor_plans[0], status=data["status"], x=1, y=1)
        cls.model.objects.create(floor_plan=floor_plans[1], status=data["status"], x=2, y=2)
        cls.model.objects.create(floor_plan=floor_plans[2], status=data["status"], x=3, y=3)
        # TODO: add some racks as an optional field
        cls.create_data = [
            {
                "floor_plan": floor_plans[2].pk,
                "x": 1,
                "y": 1,
                "status": data["status"].slug,
            },
            {
                "floor_plan": floor_plans[2].pk,
                "x": 2,
                "y": 1,
                "status": data["status"].slug,
            },
            {
                "floor_plan": floor_plans[2].pk,
                "x": 1,
                "y": 2,
                "status": data["status"].slug,
            },
        ]
        tag = Tag.objects.create(name="Hello", slug="hello")
        tag.content_types.add(ContentType.objects.get_for_model(models.FloorPlanTile))
        cls.bulk_update_data = {"tags": [tag.pk]}
