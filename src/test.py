import requests
results = requests.post(
 "http://localhost:8000/v1/badger/submit/",
 json = {
     "repository_name": "test-repo",
     "student_username": "Danniyb",
     "workflow_run_id": "12345",
     "commit_hash": "abc123",
     "grading_output": [
        {
             "status": True,
             "badges": [
                 {"name": "Git Master", "step": 1}
                 ],
            "category": "git"
        }
        ]
    }
)

print(results.content)