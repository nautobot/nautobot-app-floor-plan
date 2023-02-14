# Uninstall the App from Nautobot

Here you will find any steps necessary to cleanly remove the App from your Nautobot environment.

## Database Cleanup

Delete any and all ObjectChange records relating to the models provided by this App. This can be done manually through the Nautobot UI, or by running commands through `nautobot-server nbshell` such as:

```python
>>> from django.contrib.contenttypes.models import ContentType
>>> from nautobot.extras.models import ObjectChange
>>> from nautobot_floor_plan.models import FloorPlan, FloorPlanTile
>>> ct = ContentType.objects.get_for_model(FloorPlan)
>>> ct2 = ContentType.objects.get_for_model(FloorPlanTile)
>>> ObjectChange.objects.filter(changed_object_type__in=(ct, ct2)).delete()
```

Additionally, remove the `nautobot_floor_plan | floor_plan_tile` content-type from any and all Status records in Nautobot. This can be done manually through the Nautobot UI, or by running commands through `nautobot-server nbshell` such as:

```python
>>> from django.contrib.contenttypes.models import ContentType
>>> from nautobot.extras.models import Status
>>> from nautobot_floor_plan.models import FloorPlanTile
>>> ct = ContentType.objects.get_for_model(FloorPlanTile)
>>> for status in Status.objects.filter(content_types=ct):
...     status.content_types.remove(ct)
...
>>>
```

If you've defined any Nautobot extensibility features (webhooks, export templates, custom fields, relationships, etc.) that use or relate to the models included by this App, be sure to delete those records as well.

Finally, run the command `nautobot-server migrate nautobot_floor_plan zero` to remove the database tables added by this App from your Nautobot database.

## Uninstall Guide

After performing the above database cleanup, you can then remove the App from the Nautobot environment:

- Remove `"nautobot_floor_plan"` from the `PLUGINS` list in your `nautobot_config.py` and restart the Nautobot services.
- Run `nautobot-server post_upgrade`.
- Optionally, uninstall the plugin from your environment with `pip remove nautobot-floor-plan` or equivalent.
