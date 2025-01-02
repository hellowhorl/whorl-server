from functools import wraps
from django.http import HttpResponse
import json
import hmac
import hashlib
import os

def verify_github_signature(request):
    """Verify GitHub webhook signature."""
    github_secret = os.getenv('GITHUB_WEBHOOK_SECRET', '')
    if not github_secret:
        return False

    signature = request.headers.get('X-Hub-Signature-256', '')
    if not signature:
        return False

    expected_signature = 'sha256=' + hmac.new(
        github_secret.encode(),
        request.body,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected_signature)

def require_github_auth(view_func):
    """Decorator to require GitHub webhook authentication."""
    @wraps(view_func)
    def wrapped_view(view_instance, request, *args, **kwargs):
        if not verify_github_signature(request):
            return HttpResponse(
                json.dumps({'error': 'Invalid GitHub signature'}),
                status=401,
                content_type='application/json'
            )
        return view_func(view_instance, request, *args, **kwargs)
    return wrapped_view