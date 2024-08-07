"""Signals for the Floor Plan App."""

from django.apps import apps as global_apps
from django.conf import settings

PLUGIN_SETTINGS = settings.PLUGINS_CONFIG["nautobot_floor_plan"]


def post_migrate_create__add_statuses(sender, *, apps=global_apps, **kwargs):
    """Callback function for post_migrate() -- create default Statuses."""
    # pylint: disable=invalid-name
    if not apps:
        return

    Status = apps.get_model("extras", "Status")
    ContentType = apps.get_model("contenttypes", "ContentType")

    for model_name, default_statuses in PLUGIN_SETTINGS.get("default_statuses", {}).items():
        model = sender.get_model(model_name)
        for status in default_statuses:
            ct_status, _ = Status.objects.get_or_create(name=status["name"], defaults={"color": status["color"]})
            ct_model = ContentType.objects.get_for_model(model)
            if ct_model not in ct_status.content_types.all():
                ct_status.content_types.add(ct_model)
                ct_status.save()
