"""Middleware for nautobot_floor_plan."""

import logging

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import resolve, reverse
from nautobot.dcim.models import Rack

from nautobot_floor_plan.models import FloorPlanTile

logger = logging.getLogger(__name__)


class RackLocationValidationMiddleware:
    """
    Middleware to validate location changes for Rack objects in Nautobot.

    This middleware intercepts POST requests to the Rack edit view. If the Rack's location
    is being changed and the Rack is associated with a FloorPlanTile, it prevents the change
    and redirects the user back to the edit page with an error message.

    Attributes:
        get_response (callable): The next middleware or view in the request/response cycle.
    """

    def __init__(self, get_response):
        """
        Initialize the middleware.

        Args:
            get_response (callable): The next middleware or view to call.
        """
        self.get_response = get_response

    def __call__(self, request):
        """
        Process an incoming HTTP request.

        Args:
            request (HttpRequest): The HTTP request to process.

        Returns:
            HttpResponse: The HTTP response.
        """
        if request.method == "POST":
            # Resolve the view name and check if it's the Rack edit view
            match = resolve(request.path)
            if match.view_name == "dcim:rack_edit":
                logger.debug("RackLocationValidationMiddleware triggered for view: %s", match.view_name)

                # Extract Rack ID from the resolved URL
                rack_id = match.kwargs.get("pk")
                if not rack_id:
                    logger.error("Rack ID not found in URL.")
                    return self.get_response(request)

                try:
                    rack = Rack.objects.get(pk=rack_id)

                    # Check for location change
                    new_location = request.POST.get("location")
                    if new_location and new_location != str(rack.location_id):
                        # Validate against FloorPlanTile
                        if FloorPlanTile.objects.filter(rack=rack).exists():
                            logger.debug("Validation failed: Rack is installed in a FloorPlan.")
                            messages.error(request, "Cannot move Rack as it is currently installed in a FloorPlan.")
                            return redirect(reverse("dcim:rack_edit", args=[rack_id]))

                except Rack.DoesNotExist:
                    logger.error("Rack with ID %s does not exist.", rack_id)

        # Process the request normally
        return self.get_response(request)
