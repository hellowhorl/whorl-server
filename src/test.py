import requests

result = requests.post(
    "http://localhost:8000/v1/badger/process/",
    json={
        "repository_name": "test-repo",
        "student_username": "Danniyb",
        "workflow_run_id": "12345",
        "commit_hash": "abc123",
        "grading_output": [
            {
                "description": "Make at least one commit",
                "category": "git",
                "badges": [
                    {"name": "Git Master", "step": 1}
                ],
                "status": True
            }
        ]
    },
    headers={"Content-Type": "application/json"}
)

print(result.content)
