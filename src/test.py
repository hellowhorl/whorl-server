import requests

result = requests.post(
    "http://localhost:8000/v1/badger/process/",
    json={
        "repository_name": "test-repo",
        "student_username": "Danniyb",
        "workflow_run_id": "11112",
        "commit_hash": "abc123",
        "grading_output": [
            {
                "description": "Make at least one commit",
                "category": "git",
                "badges": [
                    {
                        "name": "Git Master",
                        "step": 1
                    }
                ],
                "status": True
            }
        ]
    },
    headers={
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
)

result = requests.get(
    "http://localhost:8000/v1/badger/collection/Danniyb/",
    headers={"Accept": "application/json"}
)

print("\nBadge Collection:")
print(f"Status Code: {result.status_code}")
print(f"Response: {result.content.decode()}")