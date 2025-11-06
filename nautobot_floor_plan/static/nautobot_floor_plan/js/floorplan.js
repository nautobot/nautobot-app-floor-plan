// @ts-check

/**
 * Floor Plan Interactive Viewer
 * Provides pan, zoom, and navigation capabilities for SVG floor plans
 * Integrates with multi-select functionality for object selection
 *
 * Note: FloorPlanLogger is defined in floorplan-multiselect.js which loads first
 */

document.addEventListener("DOMContentLoaded", function () {
  const svgContainer = document.getElementById("floor-plan-svg");
  if (!svgContainer) return;

  const svgUrl = svgContainer.getAttribute("data-svg-url");
  if (!svgUrl) return;

  // Debug flag (can be enabled via window.FLOOR_PLAN_DEBUG = true)
  const DEBUG =
    typeof window.FLOOR_PLAN_DEBUG !== "undefined"
      ? window.FLOOR_PLAN_DEBUG
      : false;

  // Initialize logger
  const logger = new FloorPlanLogger("Viewer", DEBUG);

  // Animation duration constants (can be overridden by template)
  const ZOOM_DURATION =
    typeof window.ZOOM_DURATION !== "undefined" ? window.ZOOM_DURATION : 0.5;
  const HIGHLIGHT_DURATION =
    typeof window.HIGHLIGHT_DURATION !== "undefined"
      ? window.HIGHLIGHT_DURATION
      : 2;

  /** @type {Object} Configuration constants for floor plan behavior */
  const CONFIG = {
    MIN_ZOOM: 10, // Minimum zoom level to prevent going too small
    ZOOM_PERCENTAGE: 0.05, // Zoom in/out percentage per scroll
    INIT_DELAY_MS: 200, // Delay before initialization
    HIGHLIGHT_OFFSET: 15046, // Offset for highlight calculations
    DEFAULT_VIEWBOX_SIZE: 15046, // Default viewBox size if not specified
    MIN_BBOX_SIZE: 10, // Minimum bounding box size
    MIN_PADDING_FACTOR: 1, // Minimum padding factor for highlights
    MAX_PADDING_FACTOR: 10, // Maximum padding factor for highlights
    PADDING_DIVISOR: 100, // Divisor for calculating padding factor
  };

  /**
   * FloorPlanViewer - Main viewer class that manages the floor plan
   * Encapsulates all viewer state and provides public API
   */
  class FloorPlanViewer {
    constructor() {
      this.isPanning = false;
      this.startPoint = { x: 0, y: 0 };
      this.endPoint = { x: 0, y: 0 };
      this.boxZoomMode = false; // Box zoom mode (separate from selection mode)
      this.selectionRect = null;
      this.tippyInstances = [];
      this.svgElement = null;
      this.viewBox = null;
      this.originalViewBoxString = null;
      this.modeManager = null;

      // Bind methods
      this.resetZoom = this.resetZoom.bind(this);
      this.handleModeChange = this.handleModeChange.bind(this);
    }

    /**
     * Initialize the viewer with an SVG element
     * @param {SVGElement} svgElement - The SVG element to manage
     * @returns {void}
     */
    initialize(svgElement) {
      this.svgElement = svgElement;
      this.originalViewBoxString = svgElement.getAttribute("viewBox");

      // Initialize box zoom toggle button (separate from selection mode)
      this.initializeBoxZoomToggle();

      // Listen for mode changes from FloorPlanModeManager
      document.addEventListener("floorplan:modechange", this.handleModeChange);
    }

    /**
     * Initialize the box zoom toggle button
     * @returns {void}
     */
    initializeBoxZoomToggle() {
      const toggleButton = document.getElementById("toggle-zoom-mode");
      if (toggleButton) {
        toggleButton.textContent = "Enable Box Zoom";
        toggleButton.classList.remove("btn-info");

        toggleButton.addEventListener("click", () => {
          this.boxZoomMode = !this.boxZoomMode;
          toggleButton.textContent = this.boxZoomMode
            ? "Switch to Pan Mode"
            : "Enable Box Zoom";
          toggleButton.classList.toggle("btn-info");
          logger.log(
            "Box zoom mode:",
            this.boxZoomMode ? "enabled" : "disabled"
          );
        });
      }
    }

    /**
     * Handle mode changes from FloorPlanModeManager
     * @param {CustomEvent} e - Mode change event
     * @returns {void}
     */
    handleModeChange(e) {
      const toggleButton = document.getElementById("toggle-zoom-mode");
      const resetButton = document.getElementById("reset-zoom");

      if (e.detail.mode === "selection") {
        // Disable box zoom when entering selection mode
        if (this.boxZoomMode) {
          this.boxZoomMode = false;
        }
        if (toggleButton) {
          toggleButton.textContent = "Enable Box Zoom";
          toggleButton.classList.remove("btn-info");
          toggleButton.disabled = true;
          toggleButton.title = "Box zoom disabled in selection mode";
        }
        if (resetButton) {
          resetButton.disabled = true;
          resetButton.title = "Reset view disabled in selection mode";
        }
      } else if (e.detail.mode === "navigation") {
        // Re-enable controls when returning to navigation mode
        if (toggleButton) {
          toggleButton.disabled = false;
          toggleButton.title = "Toggle box zoom mode";
        }
        if (resetButton) {
          resetButton.disabled = false;
          resetButton.title = "Reset view to default";
        }
      }
    }

    /**
     * Reset zoom to original viewBox
     * @returns {void}
     */
    resetZoom() {
      if (!this.svgElement || !this.originalViewBoxString) {
        logger.warn("Cannot reset zoom: SVG or original viewBox not available");
        return;
      }

      try {
        this.svgElement.setAttribute("viewBox", this.originalViewBoxString);
        logger.log("Zoom reset to original viewBox");
      } catch (error) {
        logger.error("Error resetting zoom:", error);
      }
    }

    /**
     * Check if in box zoom mode
     * @returns {boolean}
     */
    isBoxZoomMode() {
      return this.boxZoomMode;
    }

    /**
     * Cleanup resources
     * @returns {void}
     */
    cleanup() {
      document.removeEventListener(
        "floorplan:modechange",
        this.handleModeChange
      );
      this.tippyInstances.forEach((instance) => instance.destroy());
      this.tippyInstances = [];
    }
  }

  // Create viewer instance
  const viewer = new FloorPlanViewer();

  /**
   * Load and initialize the SVG floor plan
   * @param {string} url - URL of the SVG file
   * @returns {Promise<void>}
   */
  async function loadFloorPlan(url) {
    try {
      logger.log("Loading floor plan from:", url);

      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const svgContent = await response.text();

      if (!svgContent || svgContent.trim().length === 0) {
        throw new Error("Empty SVG content received");
      }

      // Insert the SVG content into the container
      svgContainer.innerHTML = svgContent;

      // Get the SVG element
      const svgElement = svgContainer.querySelector("svg");
      if (!svgElement) {
        throw new Error("No SVG element found in loaded content");
      }

      // Make sure the SVG fills the container
      svgElement.setAttribute("width", "100%");
      svgElement.setAttribute("height", "100%");

      // Store the original viewBox
      const originalViewBox = svgElement.getAttribute("viewBox");
      if (originalViewBox) {
        svgElement.dataset.originalViewBox = originalViewBox;
        logger.log("Stored original viewBox:", originalViewBox);
      } else {
        logger.warn("No viewBox attribute found on SVG");
      }

      // Initialize the SVG functionality once we're sure the SVG is loaded
      setTimeout(() => {
        try {
          viewer.initialize(svgElement);
          initializeSVG(svgElement);
          highlightElementFromURL();
          logger.log("Floor plan initialized successfully");

          // Dispatch event to notify that SVG is loaded and ready for tooltips
          document.dispatchEvent(new CustomEvent("floorplan:svgloaded"));
        } catch (error) {
          logger.error("Error during SVG initialization:", error);
          showErrorMessage(
            "Error initializing floor plan. Some features may not work correctly."
          );
        }
      }, CONFIG.INIT_DELAY_MS);
    } catch (error) {
      logger.error("Error loading SVG:", error);
      showErrorMessage(
        "Error loading floor plan. Please try refreshing the page.",
        error.message
      );
    }
  }

  /**
   * Show an error message to the user
   * @param {string} message - User-friendly error message
   * @param {string} [details] - Technical details (optional)
   * @returns {void}
   */
  function showErrorMessage(message, details) {
    const errorHtml = `
      <div class="alert alert-danger" role="alert">
        <h4 class="alert-heading">Floor Plan Error</h4>
        <p>${message}</p>
        ${
          details
            ? `<hr><p class="mb-0"><small>Details: ${details}</small></p>`
            : ""
        }
      </div>
    `;
    svgContainer.innerHTML = errorHtml;
  }

  // Load the floor plan
  loadFloorPlan(svgUrl);

  /**
   * Initialize SVG floor plan with pan/zoom and tooltip functionality
   * Sets up event handlers, viewBox management, and mode manager integration
   * @param {SVGElement} svgElement - The SVG element to initialize
   * @returns {void}
   */
  function initializeSVG(svgElement) {
    const svgDisplaySize = {
      w: svgContainer.clientWidth,
      h: svgContainer.clientHeight,
    };

    // Get the original viewBox
    const originalViewBox = svgElement.getAttribute("viewBox");
    if (!originalViewBox) return;

    // Store the exact original viewBox string for reset functionality
    const originalViewBoxString = originalViewBox;

    // Properly handle viewBox with both space and comma separators
    const viewBoxValues = originalViewBox
      .replace(/,/g, " ")
      .split(/\s+/)
      .filter((v) => v !== "")
      .map(Number);
    var viewBox = {
      x: viewBoxValues[0] || 0,
      y: viewBoxValues[1] || 0,
      w: viewBoxValues[2] || svgDisplaySize.w,
      h: viewBoxValues[3] || svgDisplaySize.h,
    };

    const svgActualSize = {
      w: viewBox.w,
      h: viewBox.h,
    };

    // Initialize scale variable for zoom calculations
    let scale = svgDisplaySize.w / viewBox.w;

    // Store navigation handlers for mode manager
    const navigationHandlers = {
      mousedown: null,
      mousemove: null,
      mouseup: null,
      mouseleave: null,
      wheel: null,
    };

    let modeManager = null;

    // Initialize tooltips
    initTooltips();

    /**
     * Initialize Tippy.js tooltips for all SVG elements with tooltip data
     * Handles both native SVG title elements and data-tooltip attributes
     * @returns {void}
     */
    function initTooltips() {
      // Clear any existing tooltip instances
      viewer.tippyInstances.forEach((instance) => instance.destroy());
      viewer.tippyInstances = [];

      // Find all elements with tooltips in the SVG
      const tooltipElements = svgElement.querySelectorAll(
        ".object-tooltip, [data-tooltip]"
      );

      tooltipElements.forEach((element) => {
        let content;

        // Check if element has a title element (native SVG tooltip)
        const titleElement = element.querySelector("title");
        if (titleElement) {
          content = titleElement.textContent;
          // Hide the native tooltip
          titleElement.textContent = "";
        }
        // Otherwise check for data-tooltip attribute
        else if (element.hasAttribute("data-tooltip")) {
          try {
            const tooltipData = JSON.parse(
              element.getAttribute("data-tooltip")
            );
            content = formatTooltipContent(tooltipData);
          } catch (e) {
            content = element.getAttribute("data-tooltip");
          }
        }

        if (content) {
          // Create a tippy instance for this element
          const instance = tippy(element, {
            content: content,
            allowHTML: true,
            theme: "light",
            placement: "top",
            arrow: true,
            interactive: true,
            appendTo: document.body,
            popperOptions: {
              modifiers: [
                {
                  name: "preventOverflow",
                  options: {
                    boundary: "viewport",
                  },
                },
              ],
            },
          });

          viewer.tippyInstances.push(instance);
        }
      });
    }

    /**
     * Format tooltip content from JSON data into HTML
     * @param {Object} data - Tooltip data object with key-value pairs
     * @returns {string} Formatted HTML string
     */
    function formatTooltipContent(data) {
      let html = '<div style="text-align: left;">';
      for (const [key, value] of Object.entries(data)) {
        if (Array.isArray(value)) {
          html += `<strong>${key.replace(/_/g, " ")}:</strong> ${value.join(
            ", "
          )}<br>`;
        } else {
          html += `<strong>${key.replace(/_/g, " ")}:</strong> ${value}<br>`;
        }
      }
      html += "</div>";
      return html;
    }

    /**
     * Update the SVG viewBox with boundary constraints
     * Prevents zooming out past original size and panning beyond edges
     * @param {Object} candidateViewBox - Proposed viewBox values
     * @param {number} candidateViewBox.x - X coordinate
     * @param {number} candidateViewBox.y - Y coordinate
     * @param {number} candidateViewBox.w - Width
     * @param {number} candidateViewBox.h - Height
     * @returns {Object} The actual applied viewBox values
     */
    function updateViewBox(candidateViewBox) {
      // Don't allow zooming out past the zoom that fits the entire SVG in the window.
      var newW = Math.max(
        CONFIG.MIN_ZOOM,
        Math.min(candidateViewBox.w, svgActualSize.w)
      );
      var newH = Math.max(
        CONFIG.MIN_ZOOM,
        Math.min(candidateViewBox.h, svgActualSize.h)
      );

      // Don't allow panning beyond the edges of the SVG either.
      var newViewBox = {
        x: Math.min(Math.max(candidateViewBox.x, 0), svgActualSize.w - newW),
        y: Math.min(Math.max(candidateViewBox.y, 0), svgActualSize.h - newH),
        w: newW,
        h: newH,
      };

      // Set the viewBox on the SVG element
      svgElement.setAttribute(
        "viewBox",
        `${newViewBox.x} ${newViewBox.y} ${newViewBox.w} ${newViewBox.h}`
      );

      // Update the current viewBox
      viewBox = {
        x: newViewBox.x,
        y: newViewBox.y,
        w: newViewBox.w,
        h: newViewBox.h,
      };

      // Update scale after changing viewBox
      scale = Math.min(
        svgDisplaySize.w / viewBox.w,
        svgDisplaySize.h / viewBox.h
      );

      return newViewBox;
    }

    /**
     * Reset zoom to the original default view
     * Restores the original viewBox from when the SVG was loaded
     * @returns {void}
     */
    function resetZoom() {
      // Restore the exact original viewBox string
      svgElement.setAttribute("viewBox", originalViewBoxString);

      // Update our viewBox object to match
      viewBox = {
        x: viewBoxValues[0],
        y: viewBoxValues[1],
        w: viewBoxValues[2],
        h: viewBoxValues[3],
      };

      // Update scale
      scale = svgDisplaySize.w / viewBox.w;

      logger.log("Zoom reset to original viewBox");
    }

    // Connect reset button to resetZoom function
    const resetButton = document.getElementById("reset-zoom");
    if (resetButton) {
      resetButton.onclick = resetZoom;
    }

    // On scroll wheel in the SVG, zoom in or out
    navigationHandlers.wheel = function (e) {
      if (!e.shiftKey) return;

      // Prevent default scrolling behavior
      e.preventDefault();
      e.stopPropagation();

      const rect = svgContainer.getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;

      const dw = viewBox.w * Math.sign(e.deltaY) * -CONFIG.ZOOM_PERCENTAGE;
      const dh = viewBox.h * Math.sign(e.deltaY) * -CONFIG.ZOOM_PERCENTAGE;

      const dx = (dw * mx) / svgDisplaySize.w;
      const dy = (dh * my) / svgDisplaySize.h;

      const scaledViewBox = {
        x: viewBox.x + dx,
        y: viewBox.y + dy,
        w: viewBox.w - dw,
        h: viewBox.h - dh,
      };

      // Animate the viewBox update with GSAP
      gsap.to(svgElement, {
        duration: 0.3,
        attr: {
          viewBox: `${scaledViewBox.x} ${scaledViewBox.y} ${scaledViewBox.w} ${scaledViewBox.h}`,
        },
        ease: "power2.out",
      });

      viewBox = scaledViewBox;
    };
    svgElement.addEventListener("wheel", navigationHandlers.wheel, {
      passive: false,
    });

    // On click in the SVG, record the click location and begin panning or box selection
    navigationHandlers.mousedown = function (e) {
      // Don't interfere with clicks on links or other interactive elements
      if (e.target.closest("a") || e.target.closest("button")) return;

      e.preventDefault();

      if (viewer.isBoxZoomMode()) {
        // In ZOOM mode - Create a selection rectangle
        // Create an SVG point at the mouse position
        const pt = svgElement.createSVGPoint();
        pt.x = e.clientX;
        pt.y = e.clientY;

        // Get the CTM
        const ctm = svgElement.getScreenCTM();
        if (!ctm) return;

        // Convert to SVG document coordinates
        const svgP = pt.matrixTransform(ctm.inverse());

        viewer.startPoint = { x: svgP.x, y: svgP.y };

        // Create selection rectangle
        viewer.selectionRect = document.createElementNS(
          "http://www.w3.org/2000/svg",
          "rect"
        );
        viewer.selectionRect.setAttribute("x", viewer.startPoint.x);
        viewer.selectionRect.setAttribute("y", viewer.startPoint.y);
        viewer.selectionRect.setAttribute("width", 0);
        viewer.selectionRect.setAttribute("height", 0);
        viewer.selectionRect.setAttribute("fill", "rgba(0, 123, 255, 0.2)");
        viewer.selectionRect.setAttribute("stroke", "#007bff");
        viewer.selectionRect.setAttribute("stroke-width", "1");
        viewer.selectionRect.setAttribute("pointer-events", "none");
        svgElement.appendChild(viewer.selectionRect);
      } else {
        // In PAN mode - Start panning
        viewer.isPanning = true;

        // Store the initial mouse position
        viewer.startPoint = {
          x: e.clientX,
          y: e.clientY,
        };

        // Store the current viewBox values
        viewer.endPoint = {
          x: viewBox.x,
          y: viewBox.y,
        };
      }
    };
    svgElement.addEventListener("mousedown", navigationHandlers.mousedown);

    // On dragging the mouse, update the panning location or selection rectangle
    navigationHandlers.mousemove = function (e) {
      if (!viewer.isPanning && !viewer.selectionRect) return;

      e.preventDefault();

      if (viewer.isBoxZoomMode() && viewer.selectionRect) {
        // In ZOOM mode - Update the selection rectangle
        // Create an SVG point at the mouse position
        const pt = svgElement.createSVGPoint();
        pt.x = e.clientX;
        pt.y = e.clientY;
        // Get the CTM
        const ctm = svgElement.getScreenCTM();
        if (!ctm) return;
        // Convert to SVG document coordinates
        const svgP = pt.matrixTransform(ctm.inverse());

        viewer.endPoint = { x: svgP.x, y: svgP.y };
        // Update selection rectangle
        const width = viewer.endPoint.x - viewer.startPoint.x;
        const height = viewer.endPoint.y - viewer.startPoint.y;

        // Animate the rectangle size and position with GSAP
        gsap.to(viewer.selectionRect, {
          duration: 0.2,
          attr: {
            width: Math.abs(width),
            height: Math.abs(height),
            x: width < 0 ? viewer.endPoint.x : viewer.startPoint.x,
            y: height < 0 ? viewer.endPoint.y : viewer.startPoint.y,
          },
          ease: "power2.out",
        });
      } else if (viewer.isPanning) {
        // In PAN mode - Pan the floor plan
        // Calculate the movement in screen pixels
        const dx = viewer.startPoint.x - e.clientX;
        const dy = viewer.startPoint.y - e.clientY;
        // Calculate the movement factor based on the current zoom level
        const panFactor = viewBox.w / svgDisplaySize.w;
        // Calculate movement in SVG coordinates
        const movedViewBox = {
          x: viewer.endPoint.x + dx * panFactor,
          y: viewer.endPoint.y + dy * panFactor,
          w: viewBox.w, // Maintain original width
          h: viewBox.h, // Maintain original height
        };
        // Add boundary checks
        const maxX = svgActualSize.w - viewBox.w;
        const maxY = svgActualSize.h - viewBox.h;
        movedViewBox.x = Math.max(0, Math.min(movedViewBox.x, maxX));
        movedViewBox.y = Math.max(0, Math.min(movedViewBox.y, maxY));

        // Animate panning with GSAP
        gsap.to(svgElement, {
          duration: 0.3,
          attr: {
            viewBox: `${movedViewBox.x} ${movedViewBox.y} ${movedViewBox.w} ${movedViewBox.h}`,
          },
          ease: "power2.out",
        });

        viewBox = movedViewBox;
      }
    };
    svgElement.addEventListener("mousemove", navigationHandlers.mousemove);

    // On releasing the mouse button, update the panning location or zoom to selection
    navigationHandlers.mouseup = function (e) {
      if (!viewer.isPanning && !viewer.selectionRect) return;

      e.preventDefault();

      if (viewer.isBoxZoomMode() && viewer.selectionRect) {
        // In ZOOM mode - Finalize the zoom box
        // Create an SVG point at the mouse position
        const pt = svgElement.createSVGPoint();
        pt.x = e.clientX;
        pt.y = e.clientY;

        // Get the CTM
        const ctm = svgElement.getScreenCTM();
        if (!ctm) return;
        // Convert to SVG document coordinates
        const svgP = pt.matrixTransform(ctm.inverse());

        viewer.endPoint = { x: svgP.x, y: svgP.y };
        // Get the selection rectangle dimensions
        let selWidth = Math.abs(viewer.endPoint.x - viewer.startPoint.x);
        let selHeight = Math.abs(viewer.endPoint.y - viewer.startPoint.y);

        // Minimum selection size check
        if (selWidth > 10 && selHeight > 10) {
          // Get the top-left corner of the selection
          const minX = Math.min(viewer.startPoint.x, viewer.endPoint.x);
          const minY = Math.min(viewer.startPoint.y, viewer.endPoint.y);
          // The coordinates are already in SVG space, so we can use them directly
          viewBox = updateViewBox({
            x: minX,
            y: minY,
            w: selWidth,
            h: selHeight,
          });

          // Animate final zoom with GSAP
          gsap.to(svgElement, {
            duration: 0.3,
            attr: {
              viewBox: `${minX} ${minY} ${selWidth} ${selHeight}`,
            },
            ease: "power2.out",
          });
        }

        // Remove the selection rectangle with GSAP
        gsap.to(viewer.selectionRect, {
          duration: 0.2,
          opacity: 0,
          onComplete: function () {
            if (viewer.selectionRect && viewer.selectionRect.parentNode) {
              viewer.selectionRect.parentNode.removeChild(viewer.selectionRect);
            }
            viewer.selectionRect = null;
          },
        });
      }

      viewer.isPanning = false;
    };
    svgElement.addEventListener("mouseup", navigationHandlers.mouseup);

    // Handle mouse leaving the SVG area
    navigationHandlers.mouseleave = function (e) {
      viewer.isPanning = false;

      if (viewer.selectionRect && viewer.selectionRect.parentNode) {
        gsap.to(viewer.selectionRect, {
          duration: 0.2,
          opacity: 0,
          onComplete: function () {
            viewer.selectionRect.parentNode.removeChild(viewer.selectionRect);
            viewer.selectionRect = null;
          },
        });
      }
    };
    svgElement.addEventListener("mouseleave", navigationHandlers.mouseleave);

    // Set up a MutationObserver to watch for changes in the SVG
    // This helps when elements are added or modified dynamically
    const observer = new MutationObserver(() => {
      initTooltips();
    });

    observer.observe(svgElement, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["data-tooltip"],
    });

    // Initialize mode manager
    if (typeof FloorPlanModeManager !== "undefined") {
      viewer.modeManager = new FloorPlanModeManager(
        svgElement,
        navigationHandlers
      );
      logger.log("Floor Plan Mode Manager initialized");
    } else {
      logger.error(
        "FloorPlanModeManager class not found. Make sure floorplan-multiselect.js is loaded."
      );
    }

    // Initialize multi-select handler
    if (typeof FloorPlanMultiSelect !== "undefined" && viewer.modeManager) {
      const multiSelect = new FloorPlanMultiSelect(
        svgElement,
        viewer.modeManager
      );
      logger.log("Floor Plan Multi-Select initialized");
    }
  }

  /**
   * Find an element in the SVG by ID
   * @param {SVGElement} svg - The SVG element to search in
   * @param {string} elementId - The ID of the element to find
   * @returns {Element|null} The found element or null
   */
  function findElementById(svg, elementId) {
    try {
      return (
        svg.getElementById(elementId) ||
        svg.querySelector(`[data-id="${elementId}"]`)
      );
    } catch (error) {
      logger.error("Error finding element:", error);
      return null;
    }
  }

  /**
   * Validate and sanitize bounding box values
   * @param {DOMRect} bbox - The bounding box to validate
   * @returns {Object} Sanitized bounding box values
   */
  function sanitizeBBox(bbox) {
    return {
      x: isNaN(bbox.x) ? 0 : Number(bbox.x),
      y: isNaN(bbox.y) ? 0 : Number(bbox.y),
      width: isNaN(bbox.width) ? CONFIG.MIN_BBOX_SIZE : Number(bbox.width),
      height: isNaN(bbox.height) ? CONFIG.MIN_BBOX_SIZE : Number(bbox.height),
    };
  }

  /**
   * Calculate highlight viewBox dimensions with padding
   * @param {Object} bbox - Sanitized bounding box
   * @param {Object} originalViewBox - Original viewBox dimensions
   * @returns {Object} Calculated viewBox for highlight
   */
  function calculateHighlightViewBox(bbox, originalViewBox) {
    // Dynamically adjust padding factor based on element size
    const paddingFactor = Math.max(
      CONFIG.MIN_PADDING_FACTOR,
      Math.min(
        CONFIG.MAX_PADDING_FACTOR,
        (bbox.width + bbox.height) / CONFIG.PADDING_DIVISOR
      )
    );

    const startX = bbox.x - bbox.width * paddingFactor;
    const startY = bbox.y - bbox.height * paddingFactor;
    const endX = bbox.x + bbox.width * (1 + paddingFactor);
    const endY = bbox.y + bbox.height * (1 + paddingFactor);

    // Compute width and height safely
    const computedW = Math.max(CONFIG.MIN_BBOX_SIZE, endX - startX);
    const computedH = Math.max(CONFIG.MIN_BBOX_SIZE, endY - startY);

    return {
      x: startX,
      y: startY,
      width: Math.min(originalViewBox.width, computedW),
      height: Math.min(originalViewBox.height, computedH),
    };
  }

  /**
   * Parse and validate original viewBox string
   * @param {string} viewBoxString - ViewBox string from SVG
   * @returns {Object|null} Parsed viewBox or null if invalid
   */
  function parseViewBox(viewBoxString) {
    if (!viewBoxString) {
      logger.warn("No viewBox string provided");
      return null;
    }

    try {
      const [x, y, width, height] = viewBoxString.split(" ").map(Number);

      // Validate all values are numbers
      if ([x, y, width, height].some(isNaN)) {
        logger.error("Invalid viewBox values:", viewBoxString);
        return null;
      }

      return {
        x: x || 0,
        y: y || 0,
        width: width && width > 0 ? width : CONFIG.DEFAULT_VIEWBOX_SIZE,
        height: height && height > 0 ? height : CONFIG.DEFAULT_VIEWBOX_SIZE,
      };
    } catch (error) {
      logger.error("Error parsing viewBox:", error);
      return null;
    }
  }

  /**
   * Apply zoom animation to highlight an element
   * @param {SVGElement} svg - The SVG element
   * @param {Object} viewBox - ViewBox dimensions to zoom to
   * @returns {Promise<void>} Promise that resolves when animation completes
   */
  function applyHighlightZoom(svg, viewBox) {
    return new Promise((resolve, reject) => {
      try {
        if (typeof gsap === "undefined") {
          reject(new Error("GSAP library not loaded"));
          return;
        }

        gsap.to(svg, {
          duration: 1,
          attr: {
            viewBox: `${viewBox.x} ${viewBox.y} ${viewBox.width} ${viewBox.height}`,
          },
          ease: "power2.inOut",
          onComplete: resolve,
          onInterrupt: resolve,
        });
      } catch (error) {
        logger.error("Error applying zoom animation:", error);
        reject(error);
      }
    });
  }

  /**
   * Scroll to the floor plan anchor element
   * @returns {void}
   */
  function scrollToFloorPlan() {
    try {
      const anchorElement = document.getElementById("zoom-anchor");
      if (anchorElement) {
        if (typeof gsap !== "undefined") {
          gsap.delayedCall(1.1, () => {
            anchorElement.scrollIntoView({
              behavior: "smooth",
              block: "start",
            });
          });
        } else {
          // Fallback if GSAP not available
          setTimeout(() => {
            anchorElement.scrollIntoView({
              behavior: "smooth",
              block: "start",
            });
          }, 1100);
        }
      }
    } catch (error) {
      logger.error("Error scrolling to floor plan:", error);
    }
  }

  /**
   * Highlight a specific element in the SVG with zoom and visual effects
   * Zooms to the element, adds spotlight and border effects, then resets
   * @param {string} elementId - The ID of the element to highlight
   * @returns {void}
   */
  function highlightElement(elementId) {
    try {
      const svg = document
        .getElementById("floor-plan-svg")
        ?.querySelector("svg");
      if (!svg) {
        logger.error("SVG element not found");
        return;
      }

      const element = findElementById(svg, elementId);
      if (!element) {
        logger.log(`Could not find element: ${elementId}`);
        return;
      }

      logger.log(`Found element to highlight: ${elementId}`);

      // Get and validate bounding box
      const rawBBox = element.getBBox();
      const bbox = sanitizeBBox(rawBBox);
      logger.log("Element BBox:", bbox);

      // Parse original viewBox
      const originalViewBoxString = svg.dataset.originalViewBox;
      const originalViewBox = parseViewBox(originalViewBoxString);

      if (!originalViewBox) {
        logger.error("Could not parse original viewBox");
        return;
      }

      logger.log("Original ViewBox:", originalViewBox);

      // Calculate highlight viewBox
      const highlightViewBox = calculateHighlightViewBox(bbox, originalViewBox);
      logger.log("Calculated highlight viewBox:", highlightViewBox);

      // Disable zoom and pan during highlight operation
      disableZoomAndPan();

      // Apply zoom animation
      applyHighlightZoom(svg, highlightViewBox)
        .then(() => {
          // Apply highlight effects
          const effects = createHighlightEffects(element, svg);

          // Restore original view after zoom duration
          setTimeout(() => {
            logger.log("Resetting viewBox");
            try {
              resetZoom();
              enableZoomAndPan();
            } catch (error) {
              logger.error("Error resetting zoom:", error);
              enableZoomAndPan(); // Ensure we re-enable even if reset fails
            }
          }, ZOOM_DURATION * 1000);

          // Clean up effects after highlight duration
          setTimeout(() => {
            logger.log("Cleanup triggered");
            try {
              completeCleanup(element, effects.elements, effects.animations);
              resetZoom(); // Backup reset in case first one was missed
            } catch (error) {
              logger.error("Error during cleanup:", error);
            }
          }, HIGHLIGHT_DURATION * 1000);

          // Scroll to floor plan
          scrollToFloorPlan();
        })
        .catch((error) => {
          logger.error("Error during highlight animation:", error);
          enableZoomAndPan(); // Re-enable interactions on error
        });
    } catch (error) {
      logger.error("Error in highlightElement:", error);
      enableZoomAndPan(); // Ensure we re-enable on any error
    }
  }
  /**
   * Disable zoom and pan interactions temporarily
   * Used during highlight animations to prevent user interference
   * @returns {void}
   */
  function disableZoomAndPan() {
    // Temporarily remove mouse listeners for zoom and pan
    document.querySelector("#floor-plan-svg").style.pointerEvents = "none"; // Disable pointer events
  }

  /**
   * Re-enable zoom and pan interactions
   * Called after highlight animations complete
   * @returns {void}
   */
  function enableZoomAndPan() {
    // Restore mouse listeners for zoom and pan
    document.querySelector("#floor-plan-svg").style.pointerEvents = "auto"; // Re-enable pointer events
  }
  /**
   * Complete cleanup of all highlighting effects
   * Stops animations and removes visual effect elements
   * @param {SVGElement} element - The highlighted element
   * @param {Array<SVGElement>} effectElements - Array of effect elements to remove
   * @param {Array<Animation>} animations - Array of animations to cancel
   * @returns {void}
   */
  function completeCleanup(element, effectElements, animations) {
    try {
      logger.log("Performing complete cleanup of highlighting");

      // Stop all animations
      if (Array.isArray(animations)) {
        animations.forEach((anim) => {
          try {
            if (anim && typeof anim.cancel === "function") {
              anim.cancel();
            }
          } catch (error) {
            logger.warn("Error canceling animation:", error);
          }
        });
      }

      // Remove all visual effect elements
      if (Array.isArray(effectElements)) {
        effectElements.forEach((el) => {
          try {
            if (el && el.parentNode) {
              el.parentNode.removeChild(el);
            }
          } catch (error) {
            logger.warn("Error removing effect element:", error);
          }
        });
      }

      logger.log("Cleanup complete");
    } catch (error) {
      logger.error("Error during cleanup:", error);
    }
  }

  /**
   * Create all visual highlight effects (spotlight, border, arrow)
   * Returns references to created elements and animations for cleanup
   * @param {SVGElement} element - The element to highlight
   * @param {SVGElement} svg - The SVG container
   * @returns {Object} Object containing arrays of effect elements and animations
   * @returns {Array<SVGElement>} return.elements - Created effect elements
   * @returns {Array<Animation>} return.animations - Created animations
   */
  function createHighlightEffects(element, svg) {
    const effectElements = [];
    const effectAnimations = [];

    try {
      // Get element's bounding box
      const bbox = element.getBBox();
      const centerX = bbox.x + bbox.width / 2;
      const centerY = bbox.y + bbox.height / 2;

      // Create a spotlight circle
      const spotlight = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "circle"
      );
      spotlight.setAttribute("cx", centerX);
      spotlight.setAttribute("cy", centerY);
      spotlight.setAttribute("r", Math.max(bbox.width, bbox.height) * 1.5);
      spotlight.classList.add("spotlight-effect");
      spotlight.setAttribute("data-highlight-effect", "true");

      // Insert spotlight at the beginning of SVG
      if (svg.firstChild) {
        svg.insertBefore(spotlight, svg.firstChild);
      } else {
        svg.appendChild(spotlight);
      }
      effectElements.push(spotlight);

      // Animate the spotlight - using opacity only to avoid r animation errors
      try {
        const spotlightAnim = spotlight.animate(
          [
            { opacity: 0.5 },
            { opacity: 0.3 },
            { opacity: 0.1 },
            { opacity: 0.3 },
            { opacity: 0.5 },
            { opacity: 0.1 },
          ],
          {
            delay: 300,
            duration: 3000,
            iterations: Infinity,
          }
        );
        effectAnimations.push(spotlightAnim);
      } catch (animError) {
        logger.log("Spotlight animation not supported:", animError);
      }

      // Create animated border
      const border = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "rect"
      );
      border.setAttribute("x", bbox.x - 5);
      border.setAttribute("y", bbox.y - 5);
      border.setAttribute("width", bbox.width + 10);
      border.setAttribute("height", bbox.height + 10);
      border.classList.add("highlight-border");
      border.setAttribute("data-highlight-effect", "true");

      svg.appendChild(border);
      effectElements.push(border);

      // Animate the border using only stroke properties to avoid errors
      try {
        const borderAnim = border.animate(
          [
            { strokeWidth: "2px", strokeOpacity: 1 },
            { strokeWidth: "6px", strokeOpacity: 0.7 },
            { strokeWidth: "2px", strokeOpacity: 1 },
          ],
          {
            duration: 2000,
            iterations: Infinity,
          }
        );
        effectAnimations.push(borderAnim);
      } catch (animError) {
        logger.log("Border animation not supported:", animError);
      }

      // Add a pulsing arrow pointing down toward the element
      const arrowY = bbox.y - 30;

      const arrow = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "path"
      );
      arrow.setAttribute(
        "d",
        `M${centerX},${arrowY + 20} L${centerX - 10},${arrowY} L${
          centerX + 10
        },${arrowY} Z`
      );
      arrow.classList.add("indicator-arrow");
      arrow.setAttribute("data-highlight-effect", "true");

      svg.appendChild(arrow);
      effectElements.push(arrow);

      // Animate the arrow
      try {
        const arrowAnim = arrow.animate(
          [
            { transform: "translateY(0px)" },
            { transform: "translateY(10px)" },
            { transform: "translateY(0px)" },
          ],
          {
            duration: 1500,
            iterations: Infinity,
          }
        );
        effectAnimations.push(arrowAnim);
      } catch (animError) {
        logger.log("Arrow animation not supported:", animError);
      }

      return {
        elements: effectElements,
        animations: effectAnimations,
      };
    } catch (error) {
      console.error("Error creating highlight effects:", error);
      return {
        elements: [],
        animations: [],
      };
    }
  }
  /**
   * Check URL parameters and highlight the specified element
   * Supports highlight_rack, highlight_device, highlight_powerpanel, highlight_powerfeed params
   * @returns {void}
   */
  function highlightElementFromURL() {
    // Get query parameters from URL
    const urlParams = new URLSearchParams(window.location.search);

    // Check for various highlight parameters
    const rackId = urlParams.get("highlight_rack");
    const deviceId = urlParams.get("highlight_device");
    const powerPanelId = urlParams.get("highlight_powerpanel");
    const powerFeedId = urlParams.get("highlight_powerfeed");

    // Find and highlight the SVG element based on these IDs
    if (rackId) {
      highlightElement(`rack-${rackId}`, "rack");
    } else if (deviceId) {
      highlightElement(`device-${deviceId}`, "device");
    } else if (powerPanelId) {
      highlightElement(`powerpanel-${powerPanelId}`, "powerpanel");
    } else if (powerFeedId) {
      highlightElement(`powerfeed-${powerFeedId}`, "powerfeed");
    }
  }

  // Call the function when the page loads
  highlightElementFromURL();

  /**
   * Get the current theme (light or dark)
   * Checks localStorage preference and system preference
   * @returns {string} 'light' or 'dark'
   */
  function getCurrentTheme() {
    // First check localStorage for user preference
    const currentTheme = localStorage.getItem("theme");
    if (currentTheme && currentTheme !== "system") {
      return currentTheme;
    }

    // If system theme, check system preference
    if (
      window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: dark)").matches
    ) {
      return "dark";
    }

    // Default to light
    return "light";
  }

  /**
   * Update the SVG's CSS based on current theme
   * Dynamically loads dark_svg.css or svg.css
   * @returns {void}
   */
  function updateSvgTheme() {
    const isDarkMode = getCurrentTheme() === "dark";
    const svgElement = document.querySelector("#floor-plan-svg");
    if (svgElement) {
      // Find the style element within the SVG
      const styleElement = svgElement.querySelector("style");
      if (styleElement) {
        // Fetch the appropriate CSS file
        const cssFile = isDarkMode ? "dark_svg.css" : "svg.css";
        fetch(`/static/nautobot_floor_plan/css/${cssFile}`)
          .then((response) => response.text())
          .then((css) => {
            styleElement.textContent = css;
          })
          .catch((err) => {
            console.warn("Failed to load floor plan theme CSS:", err);
          });
      }
    }
  }

  // Call this when the page loads
  updateSvgTheme();
});
