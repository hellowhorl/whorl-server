"""Authentication Middleware for API Endpoints."""

import requests
from django.http import JsonResponse

class GitHubTokenAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        github_token = request.headers.get('Authorization')
        if github_token:
            is_valid = self.validate_github_token(github_token)
            if not is_valid:
                return JsonResponse({'error': 'Invalid GitHub token'}, status=401)
        else:
            return JsonResponse({'error': 'GitHub token required'}, status=401)

        response = self.get_response(request)
        return response

    def validate_github_token(self, token):
        headers = {'Authorization': f'token {token}'}
        response = requests.get('https://api.github.com/user', headers=headers)
        return response.status_code == 200
    
# the current middleware expects the GitHub token to be passed in the Authorization header. 
# because client does not already have this header, we will need to modify the client code to include it or find a workaround
