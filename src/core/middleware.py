"""Authentication Middleware for API Endpoints."""

import requests
from django.http import JsonResponse


class GitHubTokenAuthenticationMiddleware:
    """Middleware to authenticate requests using a GitHub token."""

    def __init__(self, get_response):
        """Initialize the middleware with the given response handler."""
        self.get_response = get_response

    def __call__(self, request):
        """Process the incoming request and authenticate the GitHub token."""
        headers = request.META
        token = headers.get("HTTP_AUTHORIZATION")
        http_user = headers.get("HTTP_USER")

        headers = {
            "Authorization": f"{token}",
        }

        # Fetch the authenticated user's details
        user_response = requests.get("https://api.github.com/user", headers=headers)
        if user_response.status_code == 200:
            user_data = user_response.json()
            if user_data.get("login") == http_user:
                # User is authenticated
                response = self.get_response(request)
                return response
            else:
                # User is not authenticated
                return user_response
        else:
            return user_response
