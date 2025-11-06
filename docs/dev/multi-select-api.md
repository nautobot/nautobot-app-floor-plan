# Multi-Select API Documentation

This document provides technical documentation for the Floor Plan multi-select feature, including API references for the JavaScript classes and guidance for developers who want to extend or modify the functionality.

## Architecture Overview

The multi-select feature consists of two main JavaScript classes that work together:

```mermaid
graph TB
    subgraph FloorPlanView["Floor Plan View"]
        ModeManager["FloorPlanModeManager<br/>━━━━━━━━━━━━━━━━<br/>• Mode switching<br/>• Event handling<br/>• State management"]
        MultiSelect["FloorPlanMultiSelect<br/>━━━━━━━━━━━━━━━━<br/>• Drag selection<br/>• Object grouping<br/>• Bulk edit UI"]
        SVG["SVG Floor Plan<br/>━━━━━━━━━━━━━━━━<br/>Tiles, Objects, Selection Rectangle"]
        
        ModeManager <-->|Custom Events| MultiSelect
        ModeManager -->|Manages| SVG
        MultiSelect -->|Interacts with| SVG
    end
    
    User([User]) -->|Keyboard/Mouse| ModeManager
    User -->|Drag Selection| MultiSelect
    MultiSelect -->|Redirects to| BulkEdit[Nautobot Bulk Edit Forms]
    
    style ModeManager fill:#4a90e2,stroke:#2e5c8a,color:#fff
    style MultiSelect fill:#50c878,stroke:#2d7a4a,color:#fff
    style SVG fill:#f39c12,stroke:#c87f0a,color:#fff
    style BulkEdit fill:#9b59b6,stroke:#6c3483,color:#fff
```

### Component Interaction

1. **FloorPlanModeManager** manages the overall interaction mode (navigation vs selection)
    - Handles keyboard shortcuts (S key to toggle modes)
    - Manages pan/zoom navigation handlers
    - Dispatches `floorplan:modechange` events

2. **FloorPlanMultiSelect** handles selection logic and bulk edit UI
    - Listens for mode change events
    - Implements drag-to-select functionality
    - Groups selected objects by type
    - Shows adaptive bulk edit buttons based on permissions

3. **Communication** happens via custom events dispatched on the document
    - `floorplan:modechange` - Notifies when mode switches
    - `floorplan:svgloaded` - Notifies when SVG is ready

4. **SVG Floor Plan** is the shared DOM element both classes interact with
    - Contains tiles, objects, and selection rectangles
    - Receives mouse/keyboard events
    - Updates visual state based on selections

## FloorPlanModeManager API

The `FloorPlanModeManager` class manages switching between navigation and selection modes.

### Constructor

```javascript
new FloorPlanModeManager(svgElement, navigationHandlers)
```

**Parameters:**

- `svgElement` (SVGElement): The SVG element representing the floor plan
- `navigationHandlers` (Object): Object containing navigation event handlers
    - `mousedown` (Function): Mouse down handler for pan/zoom
    - `mousemove` (Function): Mouse move handler for panning
    - `mouseup` (Function): Mouse up handler to end panning
    - `mouseleave` (Function): Mouse leave handler
    - `wheel` (Function): Mouse wheel handler for zoom

**Example:**

```javascript
const modeManager = new FloorPlanModeManager(
    document.querySelector('svg'),
    {
        mousedown: handlePanStart,
        mousemove: handlePanning,
        mouseup: handlePanEnd,
        mouseleave: handleMouseLeave,
        wheel: handleZoom
    }
);
```

### Methods

#### `toggleMode()`

Toggles between navigation and selection modes.

**Returns:** `void`

**Example:**

```javascript
modeManager.toggleMode();
```

#### `switchToSelectionMode()`

Switches to selection mode, disabling navigation handlers.

**Returns:** `void`

**Side Effects:**

- Removes navigation event listeners
- Disables zoom/pan controls
- Updates button UI
- Changes cursor to crosshair
- Dispatches `floorplan:modechange` event

**Example:**

```javascript
modeManager.switchToSelectionMode();
```

#### `switchToNavigationMode()`

Switches to navigation mode, re-enabling navigation handlers.

**Returns:** `void`

**Side Effects:**

- Restores navigation event listeners
- Enables zoom/pan controls
- Updates button UI
- Restores default cursor
- Dispatches `floorplan:modechange` event

**Example:**

```javascript
modeManager.switchToNavigationMode();
```

#### `isSelectionMode()`

Checks if currently in selection mode.

**Returns:** `boolean` - `true` if in selection mode, `false` if in navigation mode

**Example:**

```javascript
if (modeManager.isSelectionMode()) {
    // Do something in selection mode
}
```

#### `cleanup()`

Removes event listeners and cleans up resources.

**Returns:** `void`

**Example:**

```javascript
// When destroying the floor plan view
modeManager.cleanup();
```

### Events

#### `floorplan:modechange`

Dispatched when the mode changes.

**Event Detail:**

```javascript
{
    mode: 'navigation' | 'selection',
    previousMode: 'navigation' | 'selection'
}
```

**Example:**

```javascript
document.addEventListener('floorplan:modechange', (event) => {
    console.log(`Mode changed from ${event.detail.previousMode} to ${event.detail.mode}`);
});
```

## FloorPlanMultiSelect API

The `FloorPlanMultiSelect` class handles drag selection and bulk edit operations.

### Constructor

```javascript
new FloorPlanMultiSelect(svgElement, modeManager, options)
```

**Parameters:**

- `svgElement` (SVGElement): The SVG element representing the floor plan
- `modeManager` (FloorPlanModeManager): The mode manager instance to coordinate with
- `options` (Object, optional): Configuration options
    - `selectableSelector` (String): CSS selector for selectable elements (auto-generated if not provided)
    - `debug` (Boolean): Enable debug logging (default: false)

**Note:** User permissions are automatically read from `window.FLOOR_PLAN_PERMISSIONS` which should be set in the template.

**Example:**

```javascript
// Permissions should be set globally in the template
window.FLOOR_PLAN_PERMISSIONS = {
    canEditRacks: true,
    canEditDevices: true,
    canEditPowerPanels: false,
    canEditPowerFeeds: false
};

const modeManager = new FloorPlanModeManager(svgElement, navigationHandlers);
const multiSelect = new FloorPlanMultiSelect(
    document.querySelector('svg'),
    modeManager,
    {
        debug: false
    }
);
```

### Methods

#### `enableSelectionMode()`

Enables multi-select functionality. Typically called automatically by mode change event.

**Returns:** `void`

**Side Effects:**

- Adds mouse event listeners for drag selection
- Prepares for selection rectangle creation

**Example:**

```javascript
// Usually called automatically via mode change events
multiSelect.enableSelectionMode();
```

#### `disableSelectionMode()`

Disables multi-select functionality. Typically called automatically by mode change event.

**Returns:** `void`

**Side Effects:**

- Removes mouse event listeners
- Clears any active selection
- Removes selection rectangle

**Example:**

```javascript
// Usually called automatically via mode change events
multiSelect.disableSelectionMode();
```

#### `clearSelection()`

Clears the current selection.

**Returns:** `void`

**Side Effects:**

- Removes selection highlights from tiles
- Hides bulk edit UI
- Removes selection rectangle if present

**Example:**

```javascript
multiSelect.clearSelection();
```

#### `getSelectedObjectsByType()`

Gets selected objects grouped by type.

**Returns:** `Object` - Object with keys for each object type and arrays of PKs

```javascript
{
    rack: [1, 2, 3],
    device: [4, 5],
    power_panel: [],
    power_feed: []
}
```

**Example:**

```javascript
const selected = multiSelect.getSelectedObjectsByType();
console.log(`Selected ${selected.rack.length} racks and ${selected.device.length} devices`);
```

#### `submitBulkEditForType(objectType)`

Submits bulk edit form for a specific object type.

**Parameters:**

- `objectType` (String): One of `'rack'`, `'device'`, `'power_panel'`, `'power_feed'`

**Returns:** `void`

**Side Effects:**

- Creates and submits a form to Nautobot's bulk edit endpoint
- Stores return URL in localStorage
- Navigates to bulk edit page

**Example:**

```javascript
// Typically called internally, but can be called manually
multiSelect.submitBulkEditForType('rack');
```

### Internal Methods

These methods are used internally but documented for reference:

#### `handleMouseDown(event)`

Handles mouse down event to start drag selection.

#### `handleMouseMove(event)`

Handles mouse move event to update selection rectangle.

#### `handleMouseUp(event)`

Handles mouse up event to complete selection.

#### `createSelectionRectangle(x, y)`

Creates the visual selection rectangle SVG element.

#### `updateSelectionRectangle(x, y)`

Updates the selection rectangle dimensions during drag.

#### `finalizeSelection()`

Completes the selection and shows bulk edit UI.

#### `checkIntersection(tile, rect)`

Checks if a tile intersects with the selection rectangle.

#### `showBulkEditButtons(selectedByType)`

Shows appropriate bulk edit UI based on selected object types.

## Configuration

### Global Configuration

The multi-select feature is configured via global JavaScript variables set in the template:

```javascript
// Set in the template (floorplan_svg.html)
window.FLOOR_PLAN_PERMISSIONS = {
    canEditRacks: true,
    canEditDevices: true,
    canEditPowerPanels: true,
    canEditPowerFeeds: true
};
```

These permissions are automatically checked by the multi-select feature when displaying bulk edit buttons.

### Complete Initialization Example

```javascript
// 1. Initialize mode manager with navigation handlers
if (typeof FloorPlanModeManager !== 'undefined') {
    viewer.modeManager = new FloorPlanModeManager(
        svgElement,
        navigationHandlers
    );
    logger.log('Floor Plan Mode Manager initialized');
}

// 2. Initialize multi-select handler (requires mode manager)
if (typeof FloorPlanMultiSelect !== 'undefined' && viewer.modeManager) {
    const multiSelect = new FloorPlanMultiSelect(
        svgElement,
        viewer.modeManager
    );
    logger.log('Floor Plan Multi-Select initialized');
}
```

**Important:** The mode manager must be initialized before the multi-select handler, as multi-select depends on mode change events.

### Debug Mode

Enable debug logging for troubleshooting by setting the global debug flag:

```javascript
// Set before loading the floor plan scripts
window.FLOOR_PLAN_DEBUG = true;
```

Or pass debug option when creating instances:

```javascript
const multiSelect = new FloorPlanMultiSelect(
    svgElement,
    modeManager,
    { debug: true }
);
```

Debug mode logs:

- Mode changes
- Selection events
- Object grouping
- Permission checks
- Bulk edit submissions
- Mouse event handling

## Extending the Feature

### Adding Support for New Object Types

To add support for a new object type (e.g., `circuit`), you need to update the `SELECTABLE_OBJECT_TYPES` configuration object in `floorplan-multiselect.js`:

1. **Add to the configuration object**

```javascript
const SELECTABLE_OBJECT_TYPES = {
    // ... existing types
    circuit: {
        idPrefix: "circuit-",
        apiKey: "circuit",
        bulkEditUrl: "/dcim/circuits/edit/",
        permissionKey: "canEditCircuits",
        displayName: "Circuits",
        icon: "mdi-connection",
    }
};
```

2. **Add permission to template** (floorplan_svg.html):

```django
window.FLOOR_PLAN_PERMISSIONS = {
    canEditRacks: {% if perms.dcim.change_rack %}true{% else %}false{% endif %},
    canEditDevices: {% if perms.dcim.change_device %}true{% else %}false{% endif %},
    canEditPowerPanels: {% if perms.dcim.change_powerpanel %}true{% else %}false{% endif %},
    canEditPowerFeeds: {% if perms.dcim.change_powerfeed %}true{% else %}false{% endif %},
    canEditCircuits: {% if perms.circuits.change_circuit %}true{% else %}false{% endif %}
};
```

3. **Ensure SVG tiles have correct IDs:**

SVG elements must have IDs matching the `idPrefix` pattern:

```xml
<a id="circuit-123" class="object-tile" data-object-type="circuit" data-pk="123">
    <!-- circuit tile content -->
</a>
```

The rest is handled automatically by the configuration-driven system!

### Customizing Selection Behavior

Override selection behavior by extending the class:

```javascript
class CustomMultiSelect extends FloorPlanMultiSelect {
    checkIntersection(tile, rect) {
        // Custom intersection logic
        // For example, require full containment instead of partial overlap
        const tileRect = tile.getBoundingClientRect();
        return (
            tileRect.left >= rect.left &&
            tileRect.right <= rect.right &&
            tileRect.top >= rect.top &&
            tileRect.bottom <= rect.bottom
        );
    }
}
```

### Custom Bulk Edit Actions

Add custom actions beyond standard bulk edit:

```javascript
class ExtendedMultiSelect extends FloorPlanMultiSelect {
    showBulkEditButtons(selectedByType) {
        super.showBulkEditButtons(selectedByType);

        // Add custom action button
        if (selectedByType.rack && selectedByType.rack.length > 0) {
            const customButton = document.createElement('button');
            customButton.textContent = 'Custom Action';
            customButton.onclick = () => this.performCustomAction(selectedByType.rack);
            // Add button to UI
        }
    }

    performCustomAction(rackIds) {
        // Custom logic here
        console.log('Performing custom action on racks:', rackIds);
    }
}
```

## Best Practices

### Performance

1. **Debounce selection updates** for large floor plans:

```javascript
let selectionTimeout;
handleMouseMove(event) {
    clearTimeout(selectionTimeout);
    selectionTimeout = setTimeout(() => {
        this.updateSelectionRectangle(event.clientX, event.clientY);
    }, 16); // ~60fps
}
```

2. **Use efficient selectors** - ID-based selectors are fastest

3. **Minimize DOM manipulation** - Batch updates when possible

### Error Handling

Always wrap bulk edit submissions in try-catch:

```javascript
try {
    this.submitBulkEditForType(objectType);
} catch (error) {
    console.error('Bulk edit submission failed:', error);
    alert('Failed to submit bulk edit. Please try again.');
}
```

### Testing

Test multi-select functionality:

```javascript
// Unit test example
describe('FloorPlanMultiSelect', () => {
    it('should group selected objects by type', () => {
        const multiSelect = new FloorPlanMultiSelect(mockSvg);
        // ... perform selection
        const grouped = multiSelect.getSelectedObjectsByType();
        expect(grouped.rack).toHaveLength(3);
        expect(grouped.device).toHaveLength(2);
    });
});
```

## Troubleshooting

### Selection Mode Button Not Appearing

**Symptom:** The "Selection Mode" button doesn't appear next to the "Reset View" button.

**Causes:**
1. **SVG still loading** - The button is created after SVG initialization, which happens asynchronously
2. **Slow network/database** - Large floor plans may take time to fetch and render

**Solutions:**
- The button appears automatically once the SVG loads (after ~200ms initialization delay)
- Check browser console for errors in FloorPlanModeManager initialization
- Verify the "Reset View" button exists (the selection button is inserted after it)

### Selection Not Working

1. Check that selection mode is enabled (button should be highlighted)
2. Verify SVG element is correctly passed to constructor
3. Check browser console for JavaScript errors
4. Enable debug mode to see event flow: `window.FLOOR_PLAN_DEBUG = true`

### Bulk Edit Buttons Not Appearing

1. Verify user has appropriate permissions in `window.FLOOR_PLAN_PERMISSIONS`
2. Check that objects are actually selected (tiles should have highlight styling)
3. Verify permission object is correctly configured in the template
4. Check browser console for permission-related logs (enable debug mode)
5. Ensure selected objects have valid `data-pk` attributes

### Selection Rectangle Not Visible

1. Check CSS for `.selection-rectangle` class in multiselect.css
2. Verify SVG namespace is correct (`http://www.w3.org/2000/svg`)
3. Check z-index/stacking order in SVG (rectangle should be above tiles)
4. Ensure you're in selection mode (not navigation mode)

## Additional Resources

- [Nautobot Bulk Edit Documentation](https://docs.nautobot.com/)
- [SVG Coordinate Systems](https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorial/Positions)
- [JavaScript Custom Events](https://developer.mozilla.org/en-US/docs/Web/API/CustomEvent)
- [GSAP Animation Library](https://greensock.com/gsap/) (used for smooth animations)
