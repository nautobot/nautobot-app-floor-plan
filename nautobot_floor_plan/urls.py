"""Django urlpatterns declaration for nautobot_floor_plan app."""

from nautobot.apps.urls import NautobotUIViewSetRouter
from nautobot.extras.views import ObjectChangeLogView, ObjectNotesView

from nautobot_floor_plan import models, views

router = NautobotUIViewSetRouter()
router.register("floor-plans", views.FloorPlanUIViewSet)
router.register("floor-plan-tiles", views.FloorPlanTileUIViewSet)
urlpatterns = [
    path(
        "models/<uuid:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="floorplan_changelog",
        kwargs={"model": models.FloorPlan},
    ),
    path(
        "models/<uuid:pk>/notes/",
        ObjectNotesView.as_view(),
        name="floorplan_notes",
        kwargs={"model": models.FloorPlan},
    ),
    path("locations/<uuid:pk>/floor_plan/", views.LocationFloorPlanTab.as_view(), name="location_floor_plan_tab"),
    path("docs/", RedirectView.as_view(url=static("nautobot_floor_plan/docs/index.html")), name="docs"),
]
urlpatterns += router.urls
