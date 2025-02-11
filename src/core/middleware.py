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
        http_user = headers.get("HTTP_USER")

        if token and api_version and http_user:
            headers = {
                "Authorization": f"{token}",
                "X-GitHub-Api-Version": f"{api_version}",
            }

            # Fetch the authenticated user's details
            user_response = requests.get("https://api.github.com/user", headers=headers)
            if user_response.status_code == 200:
                user_data = user_response.json()
                if user_data.get("login") == http_user:
                    # User is authenticated
                    return JsonResponse(user_data, status=200)
                else:
                    # User is not authenticated
                    return JsonResponse({"error": "User does not match token"}, status=401)
            else:
                return JsonResponse(user_response.json(), status=user_response.status_code)
        
        response = self.get_response(request)
        return response
