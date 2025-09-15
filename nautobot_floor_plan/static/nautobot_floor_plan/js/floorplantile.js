document.addEventListener('DOMContentLoaded', function() {
    // Function to set the active tab based on form errors or selected object
    function setActiveTab() {
        // Get the container element
        const container = document.getElementById('object-tabs-container');

        // If container doesn't exist, exit early
        if (!container) return;

        // Get all tab elements
            const tabLinks = {
                'rack': document.querySelector('a[href="#rack"]'),
                'device': document.querySelector('a[href="#device"]'),
                'power-panel': document.querySelector('a[href="#power-panel"]'),
                'power-feed': document.querySelector('a[href="#power-feed"]')
            };

        // Get all tab panes
        const tabPanes = {
            'rack': document.getElementById('rack'),
            'device': document.getElementById('device'),
            'power-panel': document.getElementById('power-panel'),
            'power-feed': document.getElementById('power-feed')
        };

        // Check for form errors (these are added as data attributes in the template)
        const hasErrors = {
            'rack': container.getAttribute('data-rack-errors') === 'true',
            'device': container.getAttribute('data-device-errors') === 'true',
            'power-panel': container.getAttribute('data-power-panel-errors') === 'true',
            'power-feed': container.getAttribute('data-power-feed-errors') === 'true'
        };

        // Check for selected objects (these are added as data attributes in the template)
        const hasObject = {
            'rack': container.getAttribute('data-has-rack') === 'true',
            'device': container.getAttribute('data-has-device') === 'true',
            'power-panel': container.getAttribute('data-has-power-panel') === 'true',
            'power-feed': container.getAttribute('data-has-power-feed') === 'true'
        };

        // Determine which tab should be active
        let activeTab = 'rack'; // Default to rack tab

        // First priority: tabs with errors
        for (const [tab, hasError] of Object.entries(hasErrors)) {
            if (hasError) {
                activeTab = tab;
                break;
            }
        }

        // Second priority: tabs with selected objects (if no errors)
        if (!Object.values(hasErrors).some(Boolean)) {
            for (const [tab, hasObj] of Object.entries(hasObject)) {
                if (hasObj) {
                    activeTab = tab;
                    break;
                }
            }
        }

            // Set the active tab link and pane for Bootstrap 5
            for (const [tab, link] of Object.entries(tabLinks)) {
                if (link) {
                    if (tab === activeTab) {
                        link.classList.add('active');
                    } else {
                        link.classList.remove('active');
                    }
                }
            }
            for (const [tab, pane] of Object.entries(tabPanes)) {
                if (pane) {
                    if (tab === activeTab) {
                        pane.classList.add('active', 'show');
                    } else {
                        pane.classList.remove('active', 'show');
                    }
                }
            }
    }

    // Run the function on page load
    setActiveTab();

        // Add event listeners to tab links (Bootstrap 5)
        const tabLinksAll = document.querySelectorAll('.nav-tabs a[data-bs-toggle="tab"]');
        tabLinksAll.forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                // Remove active class from all tab links
                tabLinksAll.forEach(l => l.classList.remove('active'));
                // Remove active and show from all panes
                document.querySelectorAll('.tab-pane').forEach(pane => {
                    pane.classList.remove('active', 'show');
                });
                // Add active to clicked tab link
                this.classList.add('active');
                // Add active and show to corresponding pane
                const target = this.getAttribute('href').substring(1);
                const pane = document.getElementById(target);
                if (pane) {
                    pane.classList.add('active', 'show');
                }
            });
        });
});