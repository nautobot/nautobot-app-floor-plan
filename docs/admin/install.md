# Installing the App in Nautobot

Here you will find detailed instructions on how to **install** and **configure** the App within your Nautobot environment.

## Prerequisites

- The app is compatible with Nautobot 2.0.0 and higher.
- Databases supported: PostgreSQL, MySQL

!!! note
    Please check the [dedicated page](compatibility_matrix.md) for a full compatibility matrix and the deprecation policy.

## Install Guide

!!! note
    Apps can be installed manually or using Python's `pip`. See the [Nautobot documentation](https://nautobot.readthedocs.io/en/latest/plugins/#install-the-package) for more details. The pip package name for this app is [`nautobot-floor-plan`](https://pypi.org/project/nautobot-floor-plan/).

The app is available as a Python package via PyPI and can be installed with `pip`:

```shell
pip install nautobot-floor-plan
```

To ensure Nautobot Floor Plan is automatically re-installed during future upgrades, create a file named `local_requirements.txt` (if not already existing) in the Nautobot root directory (alongside `requirements.txt`) and list the `nautobot-floor-plan` package:

```shell
echo nautobot-floor-plan >> local_requirements.txt
```

Once installed, the app needs to be enabled in your Nautobot configuration. The following block of code below shows the additional configuration required to be added to your `nautobot_config.py` file:

- Append `"nautobot_floor_plan"` to the `PLUGINS` list.

```python
# In your nautobot_config.py
PLUGINS = ["nautobot_floor_plan"]
```

Once the Nautobot configuration is updated, run the Post Upgrade command (`nautobot-server post_upgrade`) to run migrations and clear any cache:

```shell
nautobot-server post_upgrade
```

Then restart the Nautobot services which may include:

- Nautobot
- Nautobot Workers
- Nautobot Scheduler

```shell
sudo systemctl restart nautobot nautobot-worker nautobot-scheduler
```

If the App has been installed successfully, the Nautobot web UI should now show a new "Location Floor Plans" menu item under the "Organization" menu.
