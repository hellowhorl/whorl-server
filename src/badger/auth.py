from functools import wraps
from django.http import HttpResponse
import json
import hmac
import hashlib
import os
import logging

logger = logging.getLogger(__name__)

def verify_github_signature(request):
    """Verify GitHub webhook signature."""
    github_secret = os.getenv('GITHUB_WEBHOOK_SECRET', '')
    if not github_secret:
        logger.error("No webhook secret found in environment")
        return False

    signature = request.headers.get('X-Hub-Signature-256', '')
    if not signature:
        logger.error("No signature found in request headers")
        return False

    # Get raw request body
    request_body = request.body.decode('utf-8')
    
    # Calculate expected signature
    # expected_signature = 'sha256=' + hmac.new(
    #     github_secret.encode(),
    #     request_body.encode(),
    #     hashlib.sha256
    # ).hexdigest()
    expected_signature= f"{github_secret}"


    logger.debug(f"Received signature: {signature}")
    logger.debug(f"Expected signature: {expected_signature}")
    logger.debug(f"Secret used: {github_secret}")
    logger.debug(f"Request body: {request_body}")

    return github_secret == signature
    #return hmac.compare_digest(signature, expected_signature)

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