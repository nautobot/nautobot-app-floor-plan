"""Middleware for floor plan functionality."""

import logging

logger = logging.getLogger(__name__)


class FloorPlanReturnURLMiddleware:
    """Middleware to capture and store floor plan return URLs in session."""

    def __init__(self, get_response):
        """Initialize the middleware."""
        self.get_response = get_response

    def __call__(self, request):
        """Process the request."""
        # Check if this is a bulk edit POST request with a floor plan return URL
        if request.method == "POST" and "/edit/" in request.path:
            return_url = request.POST.get("return_url", "")
            if return_url and ("floor-plan" in return_url or "floor_plan" in return_url):
                # Store in session so we can retrieve it on the job result page
                request.session["floor_plan_return_url"] = return_url
                logger.debug("Stored floor plan return URL in session: %s", return_url)

        response = self.get_response(request)
        return response
