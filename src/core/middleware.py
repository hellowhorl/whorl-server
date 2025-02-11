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
        api_version = headers.get("HTTP_X_GITHUB_API_VERSION")
        
        if token and api_version:
            headers = {
                "Authorization": f"{token}",
                "X-GitHub-Api-Version": f"{api_version}",
            }

            response = requests.get("https://api.github.com/", headers=headers)
            return JsonResponse(response.json(), status=response.status_code)
        
        response = self.get_response(request)
        return response

# what else do we need to authenticate a user other than a token?
