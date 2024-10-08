# Generated by Django 3.2.25 on 2024-07-23 21:59

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("nautobot_floor_plan", "0006_alter_floorplantile_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="floorplan",
            name="x_origin_seed",
            field=models.PositiveSmallIntegerField(default=1, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name="floorplan",
            name="y_origin_seed",
            field=models.PositiveSmallIntegerField(default=1, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name="floorplantile",
            name="x_origin",
            field=models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name="floorplantile",
            name="y_origin",
            field=models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(0)]),
        ),
    ]
