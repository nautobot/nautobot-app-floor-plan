"""Django urlpatterns declaration for nautobot_floor_plan plugin."""

# TODO: when minimum Nautobot version becomes 1.5.2 or later, we can use:
# from nautobot.apps.urls import NautobotUIViewSetRouter
from nautobot.core.views.routers import NautobotUIViewSetRouter

from nautobot_floor_plan import views


app_name = "floor_plan"
router = NautobotUIViewSetRouter()
router.register("models", views.FloorPlanUIViewSet)
urlpatterns = []
urlpatterns += router.urls
