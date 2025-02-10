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
        headers = {'Authorization': token}
        return True
        # response = requests.get('https://api.github.com/user', headers=headers)
        # return response.status_code == 200

        # figure out how to authentificate token here __> github rest api
        # https://docs.github.com/en/rest/authentication/authenticating-to-the-rest-api?apiVersion=2022-11-28

