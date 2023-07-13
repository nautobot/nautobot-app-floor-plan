"""Django urlpatterns declaration for nautobot_floor_plan plugin."""
from django.urls import path
from nautobot.extras.views import ObjectChangeLogView

from nautobot_floor_plan import models
from nautobot_floor_plan.views import floorplan

urlpatterns = [
    # FloorPlan URLs
    path("floorplan/", floorplan.FloorPlanListView.as_view(), name="floorplan_list"),
    # Order is important for these URLs to work (add/delete/edit) to be before any that require uuid/slug
    path("floorplan/add/", floorplan.FloorPlanCreateView.as_view(), name="floorplan_add"),
    path("floorplan/delete/", floorplan.FloorPlanBulkDeleteView.as_view(), name="floorplan_bulk_delete"),
    path("floorplan/edit/", floorplan.FloorPlanBulkEditView.as_view(), name="floorplan_bulk_edit"),
    path("floorplan/<slug:slug>/", floorplan.FloorPlanView.as_view(), name="floorplan"),
    path("floorplan/<slug:slug>/delete/", floorplan.FloorPlanDeleteView.as_view(), name="floorplan_delete"),
    path("floorplan/<slug:slug>/edit/", floorplan.FloorPlanEditView.as_view(), name="floorplan_edit"),
    path(
        "floorplan/<slug:slug>/changelog/",
        ObjectChangeLogView.as_view(),
        name="floorplan_changelog",
        kwargs={"model": models.FloorPlan},
    ),
]
