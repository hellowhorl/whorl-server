import requests

# base config
BASE_URL = "http://localhost:8000/v1/persona"


def create_persona_example():
    """Create a new persona for an AI assistant."""
    url = f"{BASE_URL}/create/MathTutor"

    # sample persona creation data
    data = {
        "persona_creator": "professor_ai",
        "persona_prompt": "You are a patient math tutor assistant...",
        "persona_file_name": "math_guide.pdf"
    }

    # simulate a file upload (this is not required though)
    files = {
        "file_binary": open("sample_math.pdf", "rb")
    }

    response = requests.post(url, data=data, files=files)
    print(response)
    return response.json().get('assistant_id')


def create_thread_example(assistant_id):
    """Create a thread for a specific assistant."""
    url = f"{BASE_URL}/thread/create"

    data = {
        "thread_owner": "user_12345",
        "assistant_id": assistant_id,
        "initial_message": "Help me solve some math equations"
    }

    response = requests.post(url, data=data)
    print(response)
    return response.json().get('thread_id')


def cancel_thread_example(thread_id):
    """Cancel an existing thread."""
    url = f"{BASE_URL}/cancel/{thread_id}"

    response = requests.get(url)
    print(response)
