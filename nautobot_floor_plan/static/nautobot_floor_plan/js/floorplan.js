document.addEventListener('DOMContentLoaded', function() {
    const svgContainer = document.getElementById("floor-plan-svg");
    if (!svgContainer) return;

    const svgUrl = svgContainer.getAttribute('data-svg-url');
    if (!svgUrl) return;
    var isPanning = true;
    var startPoint = {x: 0, y: 0};
    var endPoint = {x: 0, y: 0};
    let zoomMode = false; // Start in PAN mode by default
    let selectionRect = null;
    let tippyInstances = [];

    // Add toggle button event listener
    const toggleButton = document.getElementById('toggle-zoom-mode');
    if (toggleButton) {
        // Make sure the button text reflects the initial state (PAN mode)
        toggleButton.textContent = 'Enable Box Zoom';
        toggleButton.classList.remove('btn-info');

        toggleButton.addEventListener('click', function() {
            zoomMode = !zoomMode;
            this.textContent = zoomMode ? 'Switch to Pan Mode' : 'Enable Box Zoom';
            this.classList.toggle('btn-info');
        });
    }

    // Fetch the SVG content and insert it into the page
    fetch(svgUrl)
        .then(response => response.text())
        .then(svgContent => {
            // Insert the SVG content into the container
            svgContainer.innerHTML = svgContent;
            // Get the SVG element
            const svgElement = svgContainer.querySelector('svg');
            if (!svgElement) return;
            // Make sure the SVG fills the container
            svgElement.setAttribute('width', '100%');
            svgElement.setAttribute('height', '100%');
            // Store the original viewBox
            const originalViewBox = svgElement.getAttribute('viewBox');
            if (originalViewBox) {
                // Store the original viewBox for reset operations
                svgElement.dataset.originalViewBox = originalViewBox;
            }
            // Initialize the SVG functionality once we're sure the SVG is loaded
            // and the viewBox is properly set
            setTimeout(() => {
                initializeSVG(svgElement);

                // Check for highlight parameters after SVG is fully initialized
                highlightElementFromURL();
            }, 200);
        })
        .catch(error => {
            console.error('Error loading SVG:', error);
            svgContainer.innerHTML = '<p>Error loading floor plan. Please try refreshing the page.</p>';
        });

    function initializeSVG(svgElement) {
        const svgDisplaySize = {
            w: svgContainer.clientWidth,
            h: svgContainer.clientHeight,
        };

        // Get the original viewBox
        const originalViewBox = svgElement.getAttribute('viewBox');
        if (!originalViewBox) return;

        // Store the exact original viewBox string for reset functionality
        const originalViewBoxString = originalViewBox;

        // Properly handle viewBox with both space and comma separators
        const viewBoxValues = originalViewBox.replace(/,/g, ' ').split(/\s+/).filter(v => v !== '').map(Number);
        var viewBox = {
            x: viewBoxValues[0] || 0,
            y: viewBoxValues[1] || 0,
            w: viewBoxValues[2] || svgDisplaySize.w,
            h: viewBoxValues[3] || svgDisplaySize.h,
        };

        const svgActualSize = {
            w: viewBox.w,
            h: viewBox.h
        };


        // Initialize tooltips
        initTooltips();

        // Function to initialize tooltips
        function initTooltips() {
            // Clear any existing tooltip instances
            tippyInstances.forEach(instance => instance.destroy());
            tippyInstances = [];

            // Find all elements with tooltips in the SVG
            const tooltipElements = svgElement.querySelectorAll('.object-tooltip, [data-tooltip]');

            tooltipElements.forEach(element => {
                let content;

                // Check if element has a title element (native SVG tooltip)
                const titleElement = element.querySelector('title');
                if (titleElement) {
                    content = titleElement.textContent;
                    // Hide the native tooltip
                    titleElement.textContent = '';
                }
                // Otherwise check for data-tooltip attribute
                else if (element.hasAttribute('data-tooltip')) {
                    try {
                        const tooltipData = JSON.parse(element.getAttribute('data-tooltip'));
                        content = formatTooltipContent(tooltipData);
                    } catch (e) {
                        content = element.getAttribute('data-tooltip');
                    }
                }

                if (content) {
                    // Create a tippy instance for this element
                    const instance = tippy(element, {
                        content: content,
                        allowHTML: true,
                        theme: 'light',
                        placement: 'top',
                        arrow: true,
                        interactive: true,
                        appendTo: document.body,
                        popperOptions: {
                            modifiers: [{
                                name: 'preventOverflow',
                                options: {
                                    boundary: 'viewport',
                                }
                            }]
                        }
                    });

                    tippyInstances.push(instance);
                }
            });
        }

        // Function to format tooltip content from JSON data
        function formatTooltipContent(data) {
            let html = '<div style="text-align: left;">';
            for (const [key, value] of Object.entries(data)) {
                if (Array.isArray(value)) {
                    html += `<strong>${key.replace(/_/g, ' ')}:</strong> ${value.join(', ')}<br>`;
                } else {
                    html += `<strong>${key.replace(/_/g, ' ')}:</strong> ${value}<br>`;
                }
            }
            html += '</div>';
            return html;
        }

        // Helper function for consistent panning and zooming of the SVG.
        function updateViewBox(candidateViewBox) {
            // Don't allow zooming out past the zoom that fits the entire SVG in the window.
            var minZoom = 10; // Minimum zoom to prevent going too small
            var newW = Math.max(minZoom, Math.min(candidateViewBox.w, svgActualSize.w));
            var newH = Math.max(minZoom, Math.min(candidateViewBox.h, svgActualSize.h));

            // Don't allow panning beyond the edges of the SVG either.
            var newViewBox = {
                x: Math.min(Math.max(candidateViewBox.x, 0), svgActualSize.w - newW),
                y: Math.min(Math.max(candidateViewBox.y, 0), svgActualSize.h - newH),
                w: newW,
                h: newH,
            };

            // Set the viewBox on the SVG element
            svgElement.setAttribute('viewBox', `${newViewBox.x} ${newViewBox.y} ${newViewBox.w} ${newViewBox.h}`);

            // Update the current viewBox
            viewBox = {
                x: newViewBox.x,
                y: newViewBox.y,
                w: newViewBox.w,
                h: newViewBox.h
            };

            // Update scale after changing viewBox
            scale = Math.min(svgDisplaySize.w / viewBox.w, svgDisplaySize.h / viewBox.h);

            return newViewBox;
        }


        // Function to reset zoom to default view
        window.resetZoom = function() {
            // Restore the exact original viewBox string
            svgElement.setAttribute('viewBox', originalViewBoxString);

            // Update our viewBox object to match
            viewBox = {
                x: viewBoxValues[0],
                y: viewBoxValues[1],
                w: viewBoxValues[2],
                h: viewBoxValues[3]
            };

            // Update scale
            scale = svgDisplaySize.w / viewBox.w;
        }

        // Connect reset button to resetZoom function
        const resetButton = document.getElementById('reset-zoom');
        if (resetButton) {
            resetButton.onclick = resetZoom;
        }

        // On scroll wheel in the SVG, zoom in or out
        svgElement.addEventListener("wheel", function(e) {
            if (!e.shiftKey) return;

            // Prevent default scrolling behavior
            e.preventDefault();
            e.stopPropagation();

            const rect = svgContainer.getBoundingClientRect();
            const mx = e.clientX - rect.left;
            const my = e.clientY - rect.top;

            const zoomPercentage = 0.05; // 5% zoom per wheel tick
            const dw = viewBox.w * Math.sign(e.deltaY) * -zoomPercentage;
            const dh = viewBox.h * Math.sign(e.deltaY) * -zoomPercentage;

            const dx = dw * mx / svgDisplaySize.w;
            const dy = dh * my / svgDisplaySize.h;

            const scaledViewBox = {
                x: viewBox.x + dx,
                y: viewBox.y + dy,
                w: viewBox.w - dw,
                h: viewBox.h - dh
            };

            // Animate the viewBox update with GSAP
            gsap.to(svgElement, {
                duration: 0.3,
                attr: {
                    viewBox: `${scaledViewBox.x} ${scaledViewBox.y} ${scaledViewBox.w} ${scaledViewBox.h}`
                },
                ease: "power2.out"
            });

            viewBox = scaledViewBox;
        }, { passive: false });

        // On click in the SVG, record the click location and begin panning or box selection
        svgElement.onmousedown = function (e) {
            // Don't interfere with clicks on links or other interactive elements
            if (e.target.closest('a') || e.target.closest('button')) return;

            e.preventDefault();

            if (zoomMode) {
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

                startPoint = {x: svgP.x, y: svgP.y};

                // Create selection rectangle
                selectionRect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
                selectionRect.setAttribute("x", startPoint.x);
                selectionRect.setAttribute("y", startPoint.y);
                selectionRect.setAttribute("width", 0);
                selectionRect.setAttribute("height", 0);
                selectionRect.setAttribute("fill", "rgba(0, 123, 255, 0.2)");
                selectionRect.setAttribute("stroke", "#007bff");
                selectionRect.setAttribute("stroke-width", "1");
                selectionRect.setAttribute("pointer-events", "none");
                svgElement.appendChild(selectionRect);
            } else {
                // In PAN mode - Start panning
                isPanning = true;

                // Store the initial mouse position
                startPoint = {
                    x: e.clientX,
                    y: e.clientY
                };

                // Store the current viewBox values
                endPoint = {
                    x: viewBox.x,
                    y: viewBox.y
                };
            }
        };

        // On dragging the mouse, update the panning location or selection rectangle
        svgElement.onmousemove = function(e){
            if (!isPanning && !selectionRect) return;

            e.preventDefault();

            if (zoomMode && selectionRect) {
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

                endPoint = {x: svgP.x, y: svgP.y};
                // Update selection rectangle
                const width = endPoint.x - startPoint.x;
                const height = endPoint.y - startPoint.y;

                // Animate the rectangle size and position with GSAP
                gsap.to(selectionRect, {
                    duration: 0.2,
                    attr: {
                        width: Math.abs(width),
                        height: Math.abs(height),
                        x: width < 0 ? endPoint.x : startPoint.x,
                        y: height < 0 ? endPoint.y : startPoint.y
                    },
                    ease: "power2.out"
                });
            } else if (isPanning) {
                // In PAN mode - Pan the floor plan
                // Calculate the movement in screen pixels
                const dx = startPoint.x - e.clientX;
                const dy = startPoint.y - e.clientY;
                // Calculate the movement factor based on the current zoom level
                const panFactor = viewBox.w / svgDisplaySize.w;
                // Calculate movement in SVG coordinates
                const movedViewBox = {
                    x: endPoint.x + (dx * panFactor),
                    y: endPoint.y + (dy * panFactor),
                    w: viewBox.w,  // Maintain original width
                    h: viewBox.h   // Maintain original height
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
                        viewBox: `${movedViewBox.x} ${movedViewBox.y} ${movedViewBox.w} ${movedViewBox.h}`
                    },
                    ease: "power2.out"
                });

                viewBox = movedViewBox;
            }
        };

        // On releasing the mouse button, update the panning location or zoom to selection
        svgElement.onmouseup = function(e){
            if (!isPanning && !selectionRect) return;
        
            e.preventDefault();
        
            if (zoomMode && selectionRect) {
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

                endPoint = {x: svgP.x, y: svgP.y};
                // Get the selection rectangle dimensions
                let selWidth = Math.abs(endPoint.x - startPoint.x);
                let selHeight = Math.abs(endPoint.y - startPoint.y);

                // Minimum selection size check
                if (selWidth > 10 && selHeight > 10) {
                    // Get the top-left corner of the selection
                    const minX = Math.min(startPoint.x, endPoint.x);
                    const minY = Math.min(startPoint.y, endPoint.y);
                    // The coordinates are already in SVG space, so we can use them directly
                    viewBox = updateViewBox({
                        x: minX,
                        y: minY,
                        w: selWidth,
                        h: selHeight
                    });

                    // Animate final zoom with GSAP
                    gsap.to(svgElement, {
                        duration: 0.3,
                        attr: {
                            viewBox: `${minX} ${minY} ${selWidth} ${selHeight}`
                        },
                        ease: "power2.out"
                    });
                }

                // Remove the selection rectangle with GSAP
                gsap.to(selectionRect, {
                    duration: 0.2,
                    opacity: 0,
                    onComplete: function () {
                        if (selectionRect && selectionRect.parentNode) {
                            selectionRect.parentNode.removeChild(selectionRect);
                        }
                        selectionRect = null;
                    }
                });
            }

            isPanning = false;
        };

        // Handle mouse leaving the SVG area
        svgElement.onmouseleave = function (e) {
            isPanning = false;

            if (selectionRect && selectionRect.parentNode) {
                gsap.to(selectionRect, {
                    duration: 0.2,
                    opacity: 0,
                    onComplete: function () {
                        selectionRect.parentNode.removeChild(selectionRect);
                        selectionRect = null;
                    }
                });
            }
        };

        // Set up a MutationObserver to watch for changes in the SVG
        // This helps when elements are added or modified dynamically
        const observer = new MutationObserver(() => {
            initTooltips();
        });

        observer.observe(svgElement, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['data-tooltip']
        });
    }

    // Enhanced function to highlight a specific element in the SVG
    function highlightElement(elementId) {
        const svg = document.getElementById("floor-plan-svg").querySelector("svg");
        if (!svg) return;

        let element = svg.getElementById(elementId) || svg.querySelector(`[data-id="${elementId}"]`);
        if (!element) {
            console.log(`Could not find element: ${elementId}`);
            return;
        }

        console.log(`Found element to highlight: ${elementId}`);

        const bbox = element.getBBox();
        console.log("Element BBox:", bbox);

        const originalViewBox = svg.dataset.originalViewBox;
        console.log("Original ViewBox:", originalViewBox);

        if (originalViewBox) {
            const [origX, origY, origW, origH] = originalViewBox.split(' ').map(Number);

            // Ensure origW and origH are valid
            const safeOrigW = isNaN(origW) || origW <= 0 ? 15046 : origW;
            const safeOrigH = isNaN(origH) || origH <= 0 ? 15046 : origH;

            // Ensure bbox values are valid
            const bboxX = isNaN(bbox.x) ? 0 : Number(bbox.x);
            const bboxY = isNaN(bbox.y) ? 0 : Number(bbox.y);
            const bboxW = isNaN(bbox.width) ? 10 : Number(bbox.width);
            const bboxH = isNaN(bbox.height) ? 10 : Number(bbox.height);

            console.log(`BBox Values: x=${bboxX}, y=${bboxY}, width=${bboxW}, height=${bboxH}`);

            // Dynamically adjust padding factor based on floor plan size
            const paddingFactor = Math.max(1, Math.min(10, (bboxW + bboxH) / 100)); // Dynamically adjust padding factor
            let startX = bboxX - bboxW * paddingFactor;
            let startY = bboxY - bboxH * paddingFactor;
            let endX = bboxX + bboxW * (1 + paddingFactor);
            let endY = bboxY + bboxH * (1 + paddingFactor);

            // Compute width and height safely
            let computedW = isNaN(endX - startX) ? 100 : Math.max(10, endX - startX);
            let computedH = isNaN(endY - startY) ? 100 : Math.max(10, endY - startY);

            let newW = Math.min(safeOrigW, computedW);
            let newH = Math.min(safeOrigH, computedH);

            console.log(`Final Computed ViewBox: ${startX} ${startY} ${newW} ${newH}`)

            // Disable zoom and pan during highlight operation
            disableZoomAndPan();
            // Apply zoom with animation
            if (!isNaN(startX) && !isNaN(startY) && !isNaN(newW) && !isNaN(newH)) {
                gsap.to(svg, {
                    duration: 1,
                    attr: { viewBox: `${startX} ${startY} ${newW} ${newH}` },
                    ease: "power2.inOut"
                });

                // Apply highlight effects
                const effects = createHighlightEffects(element, svg);

                // Restore original view after 5s
                setTimeout(() => {
                    console.log("Resetting viewBox using resetZoom() function.");
                    resetZoom(); // Call the existing reset function
                    // Re-enable zoom and pan after highlight is complete
                    enableZoomAndPan();
                }, 5000);

                // Clean up effects after 20s
                setTimeout(() => {
                    console.log("Cleanup triggered after 20 seconds");
                    completeCleanup(element, effects.elements, effects.animations);
                }, 20000);
            } else {
                console.error("Invalid viewBox values. Skipping update.");
            }
            // Scroll to the SVG container after zooming
            const anchorElement = document.getElementById("zoom-anchor");
            if (anchorElement) {
                // Ensure scroll happens after zoom animation
                gsap.delayedCall(1.1, () => {  // Delay to ensure zoom is complete
                    anchorElement.scrollIntoView({ behavior: "smooth", block: "start" });
                });
            }
        }
    }
    // Disable zoom and pan interactions
    function disableZoomAndPan() {
        // Temporarily remove mouse listeners for zoom and pan
        document.querySelector("#floor-plan-svg").style.pointerEvents = "none"; // Disable pointer events
    }

    // Enable zoom and pan interactions
    function enableZoomAndPan() {
        // Restore mouse listeners for zoom and pan
        document.querySelector("#floor-plan-svg").style.pointerEvents = "auto"; // Re-enable pointer events
    }
    // Function for complete cleanup of all highlighting effects
    function completeCleanup(element, effectElements, animations) {
        console.log("Performing complete cleanup of highlighting");

        // Stop all animations
        animations.forEach(anim => {
            if (anim && typeof anim.cancel === 'function') {
                anim.cancel();
            }
        });

        // Remove all visual effect elements
        effectElements.forEach(el => {
            if (el && el.parentNode) {
                el.parentNode.removeChild(el);
            }
        });

        console.log("Cleanup complete");
    }

    // Create all visual highlight effects and return references to animations and elements
    function createHighlightEffects(element, svg) {
        const effectElements = [];
        const effectAnimations = [];

        try {
            // Get element's bounding box
            const bbox = element.getBBox();
            const centerX = bbox.x + bbox.width / 2;
            const centerY = bbox.y + bbox.height / 2;

            // Create a spotlight circle
            const spotlight = document.createElementNS("http://www.w3.org/2000/svg", "circle");
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
                const spotlightAnim = spotlight.animate([
                    { opacity: 0.5 },
                    { opacity: 0.3 },
                    { opacity: 0.1 },
                    { opacity: 0.3 },
                    { opacity: 0.5 },
                    { opacity: 0.1 },
                ], {
                    delay: 300,
                    duration: 3000,
                    iterations: Infinity
                });
                effectAnimations.push(spotlightAnim);
            } catch (animError) {
                console.log("Spotlight animation not supported:", animError);
            }

            // Create animated border
            const border = document.createElementNS("http://www.w3.org/2000/svg", "rect");
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
                const borderAnim = border.animate([
                    { strokeWidth: "2px", strokeOpacity: 1 },
                    { strokeWidth: "6px", strokeOpacity: 0.7 },
                    { strokeWidth: "2px", strokeOpacity: 1 }
                ], {
                    duration: 2000,
                    iterations: Infinity
                });
                effectAnimations.push(borderAnim);
            } catch (animError) {
                console.log("Border animation not supported:", animError);
            }

            // Add a pulsing arrow pointing down toward the element
            const arrowY = bbox.y - 30;

            const arrow = document.createElementNS("http://www.w3.org/2000/svg", "path");
            arrow.setAttribute("d", `M${centerX},${arrowY + 20} L${centerX - 10},${arrowY} L${centerX + 10},${arrowY} Z`);
            arrow.classList.add("indicator-arrow");
            arrow.setAttribute("data-highlight-effect", "true");

            svg.appendChild(arrow);
            effectElements.push(arrow);

            // Animate the arrow
            try {
                const arrowAnim = arrow.animate([
                    { transform: 'translateY(0px)' },
                    { transform: 'translateY(10px)' },
                    { transform: 'translateY(0px)' }
                ], {
                    duration: 1500,
                    iterations: Infinity
                });
                effectAnimations.push(arrowAnim);
            } catch (animError) {
                console.log("Arrow animation not supported:", animError);
            }

            return {
                elements: effectElements,
                animations: effectAnimations
            };
        } catch (error) {
            console.error("Error creating highlight effects:", error);
            return {
                elements: [],
                animations: []
            };
        }
    }
    // Function to check for and highlight elements from URL parameters
    function highlightElementFromURL() {
        // Get query parameters from URL
        const urlParams = new URLSearchParams(window.location.search);

        // Check for various highlight parameters
        const rackId = urlParams.get('highlight_rack');
        const deviceId = urlParams.get('highlight_device');
        const powerPanelId = urlParams.get('highlight_powerpanel');
        const powerFeedId = urlParams.get('highlight_powerfeed');

        // Find and highlight the SVG element based on these IDs
        if (rackId) {
            highlightElement(`rack-${rackId}`, 'rack');
        } else if (deviceId) {
            highlightElement(`device-${deviceId}`, 'device');
        } else if (powerPanelId) {
            highlightElement(`powerpanel-${powerPanelId}`, 'powerpanel');
        } else if (powerFeedId) {
            highlightElement(`powerfeed-${powerFeedId}`, 'powerfeed');
        }
    }

    // Call the function when the page loads
    highlightElementFromURL();

    // Add function to check the current theme
    function getCurrentTheme() {
        // First check localStorage for user preference
        const currentTheme = localStorage.getItem('theme');
        if (currentTheme && currentTheme !== "system") {
            return currentTheme;
        }

        // If system theme, check system preference
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return "dark";
        }

        // Default to light
        return "light";
    }

    // Add this function to update the SVG's CSS
    function updateSvgTheme() {
        const isDarkMode = getCurrentTheme() === "dark";
        const svgElement = document.querySelector('#floor-plan-svg');
        if (svgElement) {
            // Find the style element within the SVG
            const styleElement = svgElement.querySelector('style');
            if (styleElement) {
                // Fetch the appropriate CSS file
                const cssFile = isDarkMode ? 'dark_svg.css' : 'svg.css';
                fetch(`/static/nautobot_floor_plan/css/${cssFile}`)
                    .then(response => response.text())
                    .then(css => {
                        styleElement.textContent = css;
                });
            }
        }
    }

    // Call this when the page loads
    updateSvgTheme();

    // Also update when theme changes
    const htmlEl = document.getElementsByTagName('html')[0];
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.attributeName === 'data-theme') {
                updateSvgTheme();
            }
        });
    });

    observer.observe(htmlEl, {
        attributes: true,
        attributeFilter: ['data-theme']
    });
});