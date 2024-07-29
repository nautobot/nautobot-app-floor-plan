"""Signals for the Floor Plan App."""

from django.apps import apps as global_apps
from django.conf import settings

PLUGIN_SETTINGS = settings.PLUGINS_CONFIG["nautobot_floor_plan"]

MODEL_NAME = "FloorPlanTile"


def post_migrate_create__add_statuses(sender, *, apps=global_apps, **kwargs):
    """Callback function for post_migrate() -- create default Statuses."""
    # pylint: disable=invalid-name
    if not apps:
        return

    Status = apps.get_model("extras", "Status")

    for default_statuses in PLUGIN_SETTINGS["default_statuses"]:
        model = sender.get_model(MODEL_NAME)

        if default_statuses == "Unavailable":
            Status.objects.update_or_create(name="Unavailable", defaults={"color": "111111"})
        ContentType = apps.get_model("contenttypes", "ContentType")
        ct_model = ContentType.objects.get_for_model(model)
        try:
            status = Status.objects.get(name=default_statuses)
        except Status.DoesNotExist:
            print(f"nautobot_floor_plan: Unable to find status: {default_statuses} .. SKIPPING")
            continue

        if ct_model not in status.content_types.all():
            status.content_types.add(ct_model)
            status.save()
