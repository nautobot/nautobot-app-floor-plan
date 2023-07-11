"""Django API urlpatterns declaration for nautobot_floor_plan plugin."""

from nautobot.core.api import OrderedDefaultRouter

from nautobot_floor_plan.api import views

router = OrderedDefaultRouter()
# add the name of your api endpoint, usually hyphenated model name in plural, e.g. "my-model-classes"
router.register("floor-plans", views.FloorPlanViewSet)
router.register("floor-plan-tiles", views.FloorPlanTileViewSet)

urlpatterns = router.urls
