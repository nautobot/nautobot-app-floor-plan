"""Django urlpatterns declaration for nautobot_floor_plan app."""

from django.templatetags.static import static
from django.urls import path
from django.views.generic import RedirectView
from nautobot.apps.urls import NautobotUIViewSetRouter

from nautobot_floor_plan import views

app_name = "nautobot_floor_plan"
router = NautobotUIViewSetRouter()

router.register("floor-plans", views.FloorPlanUIViewSet)
router.register("floor-plan-tiles", views.FloorPlanTileUIViewSet)

urlpatterns = [
    path("locations/<uuid:pk>/floor_plan/", views.LocationFloorPlanTab.as_view(), name="location_floor_plan_tab"),
    path(
        "locations/<uuid:pk>/child_floor_plan/",
        views.ChildLocationFloorPlanTab.as_view(),
        name="location_child_floor_plan_tab",
    ),
    path("docs/", RedirectView.as_view(url=static("nautobot_floor_plan/docs/index.html")), name="docs"),
]
urlpatterns += router.urls
