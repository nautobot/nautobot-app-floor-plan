# Generated by Django 4.2.14 on 2024-08-07 15:39

import django.db.models.deletion
import nautobot.extras.models.statuses
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("nautobot_floor_plan", "0005_add_rackgroup"),
    ]

    operations = [
        migrations.AlterField(
            model_name="floorplantile",
            name="status",
            field=nautobot.extras.models.statuses.StatusField(
                on_delete=django.db.models.deletion.PROTECT, to="extras.status"
            ),
        ),
    ]
