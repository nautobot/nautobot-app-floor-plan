"""Django urlpatterns declaration for nautobot_floor_plan app."""

from django.templatetags.static import static
from django.urls import path
from django.views.generic import RedirectView
from nautobot.apps.urls import NautobotUIViewSetRouter
from nautobot.extras.views import ObjectChangeLogView, ObjectNotesView

from nautobot_floor_plan import models, views

app_name = "floor_plan"
router = NautobotUIViewSetRouter()
router.register("floorplan", views.FloorPlanUIViewSet)

urlpatterns = [
    path("docs/", RedirectView.as_view(url=static("nautobot_floor_plan/docs/index.html")), name="docs"),
]

urlpatterns += router.urls
