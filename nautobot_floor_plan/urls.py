"""Django urlpatterns declaration for nautobot_floor_plan app."""

from nautobot.apps.urls import NautobotUIViewSetRouter

from nautobot_floor_plan import views

router = NautobotUIViewSetRouter()
router.register("floorplan", views.FloorPlanUIViewSet)

urlpatterns = router.urls
