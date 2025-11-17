# Floor Plan Tooltips

## Overview

The floor plan interface uses [Tippy.js](https://atomiks.github.io/tippyjs/) to provide rich, interactive tooltips for all UI elements. Tooltips enhance usability by providing contextual help and keyboard shortcut hints.

## Implementation

### Core Module

The tooltip system is implemented in `floorplan-tooltips.js`, which provides:

- `initializeFloorPlanTooltips()` - Initializes all static tooltips on page load
- `initializeBulkEditTooltip(button, objectType, count)` - Adds tooltips to dynamically created bulk edit buttons
- `updateModeTooltip(mode)` - Updates the mode toggle button tooltip based on current mode

### Tooltip Locations

#### Static Tooltips (initialized on page load)

1. **Edit Floorplan button** - "Edit floor plan layout and grid settings"
2. **Add Tile button** - "Add objects to the floor plan" with hint about grid plus symbols
3. **Enable Box Zoom button** - "Enable box zoom mode" with usage hint
4. **Reset View button** - "Reset zoom and pan to default view"
5. **Selection Mode button** - "Toggle selection mode" with keyboard shortcut (S key)
6. **Row labels** - "Click to view rack elevations for this row"

#### Dynamic Tooltips (created on demand)

1. **Bulk Edit buttons** - Shows object type, count, and action
2. **Bulk Edit dropdown** - Shows total object count and instructions

### Tooltip Styling

Tooltips use Tippy.js default styling with:

- Arrow indicators pointing to the target element
- HTML content support for rich formatting
- Keyboard shortcuts displayed in `<kbd>` tags with custom styling
- Appropriate placement (top, bottom, left, right) based on UI context

### Integration with Multi-Select

The multi-select feature integrates with tooltips in two ways:

1. **Mode changes** - When switching between navigation and selection modes, the mode toggle button tooltip updates to reflect the current state
2. **Bulk edit UI** - When bulk edit buttons appear, tooltips are automatically added showing what will be edited

## Usage

### Adding New Tooltips

To add a tooltip to a new UI element:

```javascript
// For static elements (in initializeFloorPlanTooltips)
const myButton = document.getElementById("my-button");
if (myButton) {
  tippy(myButton, {
    content: "My helpful tooltip text",
    placement: "bottom",
    arrow: true,
  });
}

// For dynamic elements (when creating the element)
const button = document.createElement("button");
// ... configure button ...
if (typeof tippy !== "undefined") {
  tippy(button, {
    content: "Dynamic tooltip",
    placement: "top",
    arrow: true,
  });
}
```

### HTML Content in Tooltips

Tooltips support HTML for rich formatting:

```javascript
tippy(element, {
  content: 'Main text<br><small>Additional details</small>',
  allowHTML: true,
  arrow: true,
});
```

### Keyboard Shortcuts in Tooltips

Display keyboard shortcuts with styled `<kbd>` tags:

```javascript
tippy(element, {
  content: 'Press <kbd style="background: #f0f0f0; padding: 2px 6px; border-radius: 3px; border: 1px solid #ccc;">S</kbd> to toggle',
  allowHTML: true,
  arrow: true,
});
```

## Benefits

1. **Reduced UI Clutter** - Removed verbose instructional text from the main interface
2. **Contextual Help** - Users get help exactly when and where they need it
3. **Keyboard Shortcut Discovery** - Tooltips reveal keyboard shortcuts without cluttering the UI
4. **Better UX** - Consistent, attractive tooltips across all UI elements
5. **Accessibility** - Tooltips work with keyboard navigation and screen readers

## Browser Compatibility

Tippy.js is compatible with all modern browsers:

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

The tooltip system gracefully degrades if Tippy.js fails to load - the UI remains functional with basic browser tooltips via the `title` attribute.
