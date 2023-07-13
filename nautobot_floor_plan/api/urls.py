"""Django API urlpatterns declaration for nautobot_floor_plan plugin."""

from nautobot.core.api import OrderedDefaultRouter

from nautobot_floor_plan.api import views

router = OrderedDefaultRouter()
# add the name of your api endpoint, usually hyphenated model name in plural, e.g. "my-model-classes"
router.register("floorplan", views.FloorPlanViewSet)


app_name = "nautobot_floor_plan-api"
urlpatterns = router.urls
