"""Django urlpatterns declaration for nautobot_floor_plan plugin."""

from nautobot.apps.urls import NautobotUIViewSetRouter

from nautobot_floor_plan import views


app_name = "floor_plan"
router = NautobotUIViewSetRouter()
router.register("models", views.FloorPlanUIViewSet)
urlpatterns = []
urlpatterns += router.urls
