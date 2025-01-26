# Installing the App in Nautobot

This section provides detailed instructions on how to **install** and **configure** the app in your Nautobot environment.

## Prerequisites

- Compatible with Nautobot **2.0.0 and higher**.
- Supported databases: **PostgreSQL** and **MySQL**.

!!! note
    For a full compatibility matrix and details about the deprecation policy, refer to the [Compatibility Matrix](compatibility_matrix.md).

## Install Guide

!!! note
    Apps can be installed from the [Python Package Index (PyPI)](https://pypi.org/) or locally. For more details, see the official [Nautobot App Installation Guide](https://docs.nautobot.com/projects/core/en/stable/user-guide/administration/installation/app-install/).  
    The pip package name for this app is [`nautobot-floor-plan`](https://pypi.org/project/nautobot-floor-plan/).

### Step 1: Install the App

Install the app via PyPI using `pip`:

```shell
pip install nautobot-floor-plan
```

To ensure Nautobot Floor Plan is automatically re-installed during future upgrades, create a file named `local_requirements.txt` (if not already existing) in the Nautobot root directory (alongside `requirements.txt`) and list the `nautobot-floor-plan` package:

```shell
echo nautobot-floor-plan >> local_requirements.txt
```

### Step 2: Configure the App

Once installed, the app needs to be enabled in your Nautobot configuration. The following block of code below shows the additional configuration required to be added to your `nautobot_config.py` file:

- Append `"nautobot_floor_plan"` to the `PLUGINS` list.

```python
# In your nautobot_config.py
PLUGINS = ["nautobot_floor_plan"]

# Optionally you can override default settings for config items to make grid labels like a chessboard (as seen in this example)
PLUGINS_CONFIG = {
    "nautobot_floor_plan": {
        "default_x_axis_labels": "letters",
        "default_statuses": {
            "FloorPlanTile": [
                {"name": "Active", "color": "4caf50"},
            ],
        },
        "x_size_limit": 100,
        "y_size_limit": 100,
    }
}
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

# Nautobot Floor Plan App Configuration and Customization

## Verifying Installation

Once the app is successfully installed, the Nautobot web UI will display a new "Location Floor Plans" menu item under the **Organization** menu.

## App Configuration Details

The app behavior can be customized with the following configuration settings:

| Key                    | Example                                   | Default     | Description                                                                                                                                    |
|------------------------|-------------------------------------------|-------------|------------------------------------------------------------------------------------------------------------------------------------------------|
| `default_x_axis_labels` | `"letters"`                               | `"numbers"` | Defines the label style for the X-axis of the floor plan grid. Options are `numbers` or `letters`. This sets the default value in the create form. |
| `default_y_axis_labels` | `"numbers"`                               | `"numbers"` | Defines the label style for the Y-axis of the floor plan grid. Options are `numbers` or `letters`. This sets the default value in the create form. |
| x_size_limit | 100 | None | An integer that sets the maximum allowable "x_size" for a Floor Plan. If set to None, there is no limit.|
| y_size_limit | 100 | None | An integer that sets the maximum allowable "y_size" for a Floor Plan. If set to None, there is no limit.|
|enable_rack_validation_middleware| True | True| Boolean value that loads Floor Plan rack movement validation into Django Middleware.|
| `default_statuses`      | `{"name": "Active", "color": "4caf50"}`   | See note below | A list of name and color key-value pairs for the **FloorPlanTile** model.                                                                      |

!!! note
    Default statuses are configured as follows:

    ```python
    "default_statuses": {
        "FloorPlanTile": [
            {"name": "Active", "color": "4caf50"},
            {"name": "Reserved", "color": "00bcd4"},
            {"name": "Decommissioning", "color": "ffc107"},
            {"name": "Unavailable", "color": "111111"},
            {"name": "Planned", "color": "00bcd4"},
        ],
    }
    ```

## Custom Labels

The app supports custom label types, defined in `choices.py`:

```python
class CustomAxisLabelsChoices(ChoiceSet):
    """Choices for custom axis label types."""

    ROMAN = "roman"
    GREEK = "greek"
    BINARY = "binary"
    HEX = "hex"
    NUMALPHA = "numalpha"
    LETTERS = "letters"
    ALPHANUMERIC = "alphanumeric"
    NUMBERS = "numbers"

    CHOICES = (
        (ROMAN, "Roman (e.g., I, II, III)"),
        (GREEK, "Greek (e.g., α, β, γ)"),
        (BINARY, "Binary (e.g., 1, 10, 11)"),
        (HEX, "Hexadecimal (e.g., 1, A, F)"),
        (NUMALPHA, "numalpha (e.g., 02A)"),
        (LETTERS, "Letters (e.g., A, B, C)"),
        (ALPHANUMERIC, "Alphanumeric (e.g., A01, B02)"),
        (NUMBERS, "Numbers (e.g., 1, 2, 3)"),
    )
```

### Adding New Custom Labels

To define new custom label types:

1. Add the new choice to the `CustomAxisLabelsChoices` class in `choices.py`.
2. Implement a corresponding converter class in `label_converters.py`.

#### Label Converter Base Class

All label converters inherit from the base `LabelConverter` class:

```python
class LabelConverter:
    """Base class for label conversion."""

    def __init__(self):
        """Initialize converter."""
        self.current_label = None

    def to_numeric(self, label: str) -> int:
        """Convert label to numeric value."""
        raise NotImplementedError

    def from_numeric(self, number: int) -> str:
        """Convert numeric value to label."""
        raise NotImplementedError
```

The to_numeric and from_numeric methods handle:

- Converting database integer values to display labels on the Floor Plan grid.
- Converting labels back to the corresponding integer values for database storage.

### Label Factory

LabelConverterFactory located in label_converters.py is used to lookup the correct converter that will be used based off of the CustomAxisLabelsChoices class from choices.py to the proper converter class in label_converters.py.

### Validation Logic

Custom label validation is handled in custom_validators.py, ensuring that the labels meet the required format and rules before being applied to the Floor Plan.
