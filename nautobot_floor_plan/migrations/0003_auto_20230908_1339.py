# Generated by Django 3.2.20 on 2023-09-08 13:39

import django.db.models.deletion
import nautobot.core.models.fields
import nautobot.extras.models.statuses
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("extras", "0098_rename_data_jobresult_result"),
        ("nautobot_floor_plan", "0002_fixup_null"),
    ]

    operations = [
        migrations.AlterField(
            model_name="floorplan",
            name="created",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AlterField(
            model_name="floorplan",
            name="tags",
            field=nautobot.core.models.fields.TagsField(through="extras.TaggedItem", to="extras.Tag"),
        ),
        migrations.AlterField(
            model_name="floorplantile",
            name="created",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AlterField(
            model_name="floorplantile",
            name="status",
            field=nautobot.extras.models.statuses.StatusField(
                on_delete=django.db.models.deletion.PROTECT, related_name="floor_plan_tiles", to="extras.status"
            ),
        ),
        migrations.AlterField(
            model_name="floorplantile",
            name="tags",
            field=nautobot.core.models.fields.TagsField(through="extras.TaggedItem", to="extras.Tag"),
        ),
    ]
