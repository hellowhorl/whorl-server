# whorl-server/src/test_signature.py
import hmac
import hashlib
import json
import os

def generate_signature(payload, secret):
    """Generate GitHub-style HMAC signature."""
    return 'sha256=' + hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

# Test payload
payload = json.dumps({
    "repository_name": "dumb-badger",
    "student_username": "Danniyb",
    "workflow_run_id": "1182515504",
    "commit_hash": "1e2c5f6",
    "course_id": "CS200",
    "course_name": "Computer Science II",
    "assignment_name": "lab01",
    "grading_output": {
      "checks": [
        {"name": "cd works!", "passed": True},
        {"name": "pwd works!", "passed": True}
      ]
    }
}, sort_keys=True)

# Get secret from environment
secret = os.getenv('GITHUB_WEBHOOK_SECRET')

# Generate signature
signature = generate_signature(payload, secret)

print(f"Payload: {payload}")
print(f"Secret: {secret}")
print(f"Generated signature: {signature}")

print("\nCurl command:")
print(f'''
curl -X POST http://localhost:8000/v1/badger/add/ \\
  -H "Content-Type: application/json" \\
  -H "X-Hub-Signature-256: {signature}" \\
  -d '{payload}'
''')