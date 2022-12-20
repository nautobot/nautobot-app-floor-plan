"""Django urlpatterns declaration for nautobot_floor_plan plugin."""

from django.urls import path

# TODO: when minimum Nautobot version becomes 1.5.2 or later, we can use:
# from nautobot.apps.urls import NautobotUIViewSetRouter
from nautobot.core.views.routers import NautobotUIViewSetRouter
from nautobot.extras.views import ObjectChangeLogView, ObjectNotesView

from nautobot_floor_plan import models, views


app_name = "floor_plan"
router = NautobotUIViewSetRouter()
router.register("models", views.FloorPlanUIViewSet)
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
]
urlpatterns += router.urls
