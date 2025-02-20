import requests
import json

def test_exact_format():
    result = requests.post(
        "http://localhost:8000/v1/badger/process/",
        json={
            "repository_name": "badger-test",
            "username": "allegheny-college-sandbox",
            "workflow_run_id": "12873358453",
            "commit_hash": "b57e3b627482c39ae9c3d3c74f31a4c0d91c769d",
            "grading_output": [
                {
                    "name": "Committed",
                    "step": 1
                },
                {
                    "name": "Overly committed",
                    "step": 1
                }
            ]
        },
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    )

    print(f"Status Code: {result.status_code}")
    try:
        print(f"Response: {json.dumps(result.json(), indent=2)}")
    except:
        print(f"Response: {result.content.decode()}")

if __name__ == "__main__":
    test_exact_format()