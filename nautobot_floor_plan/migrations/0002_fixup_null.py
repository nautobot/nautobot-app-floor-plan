from django.db import migrations

from nautobot.extras.utils import fixup_null_statuses


def _migrate_null_statuses(apps, _schema):
    status_model = apps.get_model("extras", "Status")
    ContentType = apps.get_model("contenttypes", "ContentType")
    model = apps.get_model("nautobot_floor_plan", "FloorPlanTile")
    model_ct = ContentType.objects.get_for_model(model)
    fixup_null_statuses(model=model, model_contenttype=model_ct, status_model=status_model)


class Migration(migrations.Migration):
    dependencies = [
        ("nautobot_floor_plan", "0001_initial"),
        ("dcim", "0046_fixup_null_statuses"),
    ]

    operations = [
        migrations.RunPython(_migrate_null_statuses, migrations.RunPython.noop),
    ]
